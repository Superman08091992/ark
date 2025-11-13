"""
Agent Message Bus

Central message routing system for agent-to-agent communication with:
- Asynchronous message passing
- Correlation ID tracking for distributed tracing
- Message history and conversation reconstruction
- Subscription-based routing
- TTL (Time-To-Live) support for transient messages

Implements REQ_AGENT_03 (Correlation IDs)

Author: ARK Enterprise Architecture
Version: 1.0.0
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Callable, Awaitable, Optional, Any
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of agent messages."""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"


@dataclass
class AgentMessage:
    """
    Envelope for agent-to-agent communication.
    
    All inter-agent communication MUST use this structure for:
    - Distributed tracing via correlation_id
    - Causality tracking via causation_id
    - Message routing and delivery
    - Priority-based processing
    """
    
    # Identity & Tracing
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    causation_id: Optional[str] = None
    
    # Routing
    from_agent: str = ""
    to_agent: Optional[str] = None  # None = broadcast
    
    # Message Type
    message_type: MessageType = MessageType.REQUEST
    
    # Payload
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: Optional[int] = None
    
    # Metadata
    priority: int = 5  # 1=highest, 10=lowest
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if message has exceeded TTL."""
        if self.ttl_seconds is None:
            return False
        age = (datetime.utcnow() - self.timestamp).total_seconds()
        return age > self.ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "priority": self.priority,
            "metadata": self.metadata
        }


class AgentBus:
    """
    Singleton message bus for agent communication.
    
    Provides:
    - Subscribe agents to receive messages
    - Publish messages to specific agents or broadcast
    - Track message history by correlation ID
    - Route messages based on priority
    - Expire stale messages based on TTL
    """
    
    _instance: Optional['AgentBus'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        """Enforce singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize agent bus (only once due to singleton)."""
        if self._initialized:
            return
        
        self._subscriptions: Dict[str, List[Callable]] = defaultdict(list)
        self._correlation_index: Dict[str, List[str]] = defaultdict(list)
        self._message_history: List[AgentMessage] = []
        self._max_history = 1000
        self._running = False
        
        logger.info("AgentBus initialized")
        self._initialized = True
    
    async def publish(self, message: AgentMessage) -> None:
        """
        Publish message to subscribers.
        
        Routes message to:
        - Specific agent if to_agent is set
        - All agents if to_agent is None (broadcast)
        
        Args:
            message: AgentMessage to publish
        """
        # Check if message is expired
        if message.is_expired():
            logger.warning(
                f"Message {message.message_id} expired (TTL: {message.ttl_seconds}s), "
                f"correlation: {message.correlation_id}"
            )
            return
        
        # Track in correlation index
        self._correlation_index[message.correlation_id].append(message.message_id)
        
        # Store in history
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)
        
        # Determine subscribers
        if message.to_agent:
            # Targeted message
            subscribers = self._subscriptions.get(message.to_agent, [])
            if not subscribers:
                logger.warning(
                    f"No subscribers for agent '{message.to_agent}', "
                    f"message {message.message_id}"
                )
        else:
            # Broadcast to all
            subscribers = [s for subs in self._subscriptions.values() for s in subs]
        
        # Deliver to subscribers
        delivery_count = 0
        for subscriber in subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(message)
                else:
                    # Run sync function in executor to avoid blocking
                    await asyncio.get_event_loop().run_in_executor(None, subscriber, message)
                delivery_count += 1
            except Exception as e:
                logger.error(
                    f"Subscriber failed for message {message.message_id}: {e}",
                    exc_info=True
                )
        
        logger.debug(
            f"Published message {message.message_id} from {message.from_agent} "
            f"to {message.to_agent or 'all'} ({delivery_count} subscribers), "
            f"correlation: {message.correlation_id}"
        )
    
    def subscribe(self, agent_name: str, handler: Callable[[AgentMessage], Awaitable[None]]) -> None:
        """
        Subscribe agent to messages.
        
        Args:
            agent_name: Name of agent subscribing
            handler: Async function to handle messages
        """
        self._subscriptions[agent_name].append(handler)
        logger.info(f"Agent '{agent_name}' subscribed to message bus")
    
    def unsubscribe(self, agent_name: str, handler: Optional[Callable] = None) -> None:
        """
        Unsubscribe agent from messages.
        
        Args:
            agent_name: Name of agent to unsubscribe
            handler: Specific handler to remove (if None, removes all for agent)
        """
        if handler is None:
            # Remove all subscriptions for agent
            if agent_name in self._subscriptions:
                del self._subscriptions[agent_name]
                logger.info(f"Agent '{agent_name}' unsubscribed from message bus")
        else:
            # Remove specific handler
            if agent_name in self._subscriptions:
                try:
                    self._subscriptions[agent_name].remove(handler)
                    logger.info(f"Handler removed for agent '{agent_name}'")
                except ValueError:
                    logger.warning(f"Handler not found for agent '{agent_name}'")
    
    def get_conversation_history(self, correlation_id: str) -> List[AgentMessage]:
        """
        Retrieve all messages for a correlation ID.
        
        Args:
            correlation_id: Correlation ID to search for
            
        Returns:
            List of AgentMessages in chronological order
        """
        message_ids = self._correlation_index.get(correlation_id, [])
        messages = [msg for msg in self._message_history if msg.message_id in message_ids]
        messages.sort(key=lambda x: x.timestamp)
        return messages
    
    def get_message_by_id(self, message_id: str) -> Optional[AgentMessage]:
        """
        Retrieve specific message by ID.
        
        Args:
            message_id: Message ID to find
            
        Returns:
            AgentMessage if found, None otherwise
        """
        for msg in self._message_history:
            if msg.message_id == message_id:
                return msg
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get message bus statistics.
        
        Returns:
            Dictionary with bus statistics
        """
        return {
            "total_subscribers": sum(len(subs) for subs in self._subscriptions.values()),
            "agents_subscribed": list(self._subscriptions.keys()),
            "messages_in_history": len(self._message_history),
            "active_conversations": len(self._correlation_index),
            "max_history_size": self._max_history
        }
    
    def clear_history(self) -> None:
        """Clear message history (for testing or memory management)."""
        self._message_history.clear()
        self._correlation_index.clear()
        logger.info("Message history cleared")
    
    async def cleanup_expired_messages(self) -> int:
        """
        Remove expired messages from history.
        
        Returns:
            Number of messages removed
        """
        initial_count = len(self._message_history)
        self._message_history = [msg for msg in self._message_history if not msg.is_expired()]
        removed = initial_count - len(self._message_history)
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} expired messages")
        
        return removed


# Global singleton instance
agent_bus = AgentBus()


class BaseAgent:
    """
    Abstract base class for all ARK agents.
    
    Provides standard message handling interface and automatic
    subscription to the agent bus.
    """
    
    def __init__(self, name: str, auto_subscribe: bool = True):
        """
        Initialize base agent.
        
        Args:
            name: Agent name (must be unique)
            auto_subscribe: Automatically subscribe to agent bus
        """
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
        
        if auto_subscribe:
            agent_bus.subscribe(name, self.handle_message)
            self.logger.info(f"Agent '{name}' initialized and subscribed to bus")
    
    async def handle_message(self, message: AgentMessage) -> None:
        """
        Handle incoming message. Must be overridden by subclasses.
        
        Args:
            message: Incoming AgentMessage
        """
        raise NotImplementedError(f"Agent {self.name} must implement handle_message()")
    
    async def send_message(self, 
                          to_agent: Optional[str],
                          payload: Dict[str, Any],
                          message_type: MessageType = MessageType.REQUEST,
                          correlation_id: Optional[str] = None,
                          causation_id: Optional[str] = None,
                          ttl_seconds: Optional[int] = None,
                          priority: int = 5) -> str:
        """
        Send message to another agent or broadcast.
        
        Args:
            to_agent: Target agent name (None = broadcast)
            payload: Message payload dictionary
            message_type: Type of message
            correlation_id: Correlation ID (generated if None)
            causation_id: ID of message that caused this message
            ttl_seconds: Time-to-live in seconds
            priority: Message priority (1=highest, 10=lowest)
            
        Returns:
            message_id of sent message
        """
        message = AgentMessage(
            correlation_id=correlation_id or str(uuid.uuid4()),
            causation_id=causation_id,
            from_agent=self.name,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            ttl_seconds=ttl_seconds,
            priority=priority
        )
        
        await agent_bus.publish(message)
        return message.message_id
    
    async def send_request(self, to_agent: str, payload: Dict[str, Any], **kwargs) -> str:
        """Convenience method to send REQUEST message."""
        return await self.send_message(to_agent, payload, MessageType.REQUEST, **kwargs)
    
    async def send_response(self, to_agent: str, payload: Dict[str, Any], **kwargs) -> str:
        """Convenience method to send RESPONSE message."""
        return await self.send_message(to_agent, payload, MessageType.RESPONSE, **kwargs)
    
    async def send_event(self, payload: Dict[str, Any], **kwargs) -> str:
        """Convenience method to broadcast EVENT message."""
        return await self.send_message(None, payload, MessageType.EVENT, **kwargs)


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    # Example agent implementation
    class ExampleAgent(BaseAgent):
        async def handle_message(self, message: AgentMessage):
            self.logger.info(
                f"Received {message.message_type} from {message.from_agent}: "
                f"{message.payload}"
            )
    
    async def demo():
        # Create agents
        kyle = ExampleAgent("kyle")
        joey = ExampleAgent("joey")
        hrm = ExampleAgent("hrm")
        
        print("\n📡 Agent Bus Demo")
        print(f"Stats: {agent_bus.get_stats()}")
        
        # Kyle sends request to Joey
        print("\n🔵 Kyle → Joey (request)")
        msg_id = await kyle.send_request(
            "joey",
            {"symbol": "TSLA", "scan_type": "pre_market_gainer"},
            correlation_id="test-correlation-123"
        )
        
        await asyncio.sleep(0.1)
        
        # Joey responds to Kyle
        print("\n🟢 Joey → Kyle (response)")
        await joey.send_response(
            "kyle",
            {"symbol": "TSLA", "enriched": True},
            correlation_id="test-correlation-123",
            causation_id=msg_id
        )
        
        await asyncio.sleep(0.1)
        
        # Kyle broadcasts event
        print("\n🟡 Kyle → ALL (broadcast event)")
        await kyle.send_event(
            {"event": "market_open", "timestamp": datetime.utcnow().isoformat()},
            correlation_id="test-correlation-123"
        )
        
        await asyncio.sleep(0.1)
        
        # Check conversation history
        print("\n📜 Conversation History:")
        history = agent_bus.get_conversation_history("test-correlation-123")
        for msg in history:
            print(f"   {msg.from_agent} → {msg.to_agent or 'ALL'}: {msg.message_type}")
        
        print(f"\n📊 Final Stats: {agent_bus.get_stats()}")
    
    asyncio.run(demo())
