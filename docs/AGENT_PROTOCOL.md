# AGENT COMMUNICATION PROTOCOL

**Version**: 1.0.0  
**Status**: Authoritative  
**Owner**: ARK Enterprise Architecture  
**Last Updated**: 2025-11-13

---

## 1. PURPOSE

This document defines the **authoritative communication contract** for all ARK agents, with specific focus on the **Trading Intelligence Backend** pipeline:

```
Kyle → Joey → Pattern Engine → HRM → Kenny → Telegram
```

All agents MUST conform to this protocol for interoperability, observability, and error handling.

---

## 2. CORE DATA STRUCTURES

### 2.1 TradeSetup Object

The **TradeSetup** is the universal data interchange format for trading intelligence.

```python
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

class TradeSetup(BaseModel):
    """Universal trade setup object for agent communication."""
    
    # Identity
    setup_id: str = Field(..., description="UUID v4 identifier")
    correlation_id: str = Field(..., description="Trace ID for cross-agent logging")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Symbol & Market
    symbol: str = Field(..., description="Ticker symbol (e.g., 'AAPL', 'TSLA')")
    market_type: str = Field(..., description="'equity', 'crypto', 'forex', 'options'")
    
    # Direction & Strategy
    direction: str = Field(..., description="'long', 'short', 'swing'")
    pattern: Optional[str] = Field(None, description="Pattern name (e.g., 'Squeezer', 'Dead Cat')")
    strategy: Optional[str] = Field(None, description="Strategy context (e.g., 'momentum', 'mean_reversion')")
    
    # Fundamental Data
    price: float = Field(..., description="Current price")
    float_: Optional[float] = Field(None, alias="float", description="Float size (millions)")
    market_cap: Optional[float] = Field(None, description="Market cap (millions)")
    volume: Optional[float] = Field(None, description="Current volume")
    avg_volume: Optional[float] = Field(None, description="Average volume")
    
    # Technical Indicators
    indicators: Dict[str, Any] = Field(default_factory=dict, description="Technical indicators (RSI, MACD, etc.)")
    
    # Catalyst & News
    catalyst: Optional[str] = Field(None, description="News catalyst or event")
    sentiment: Optional[str] = Field(None, description="'bullish', 'bearish', 'neutral'")
    
    # Scoring
    scores: Dict[str, float] = Field(default_factory=dict, description="Multi-factor scores (technical, fundamental, catalyst)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall confidence score [0.0-1.0]")
    
    # Execution Plan
    entry: Optional[float] = Field(None, description="Recommended entry price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    target: Optional[float] = Field(None, description="Price target")
    position_size: Optional[float] = Field(None, description="Recommended position size (% of capital)")
    
    # Risk Metrics
    risk_reward_ratio: Optional[float] = Field(None, description="R:R ratio")
    max_loss_percent: Optional[float] = Field(None, description="Max loss %")
    
    # Agent State
    agents_processed: List[str] = Field(default_factory=list, description="List of agent names that processed this setup")
    status: str = Field(default="pending", description="'pending', 'approved', 'rejected', 'sent'")
    
    # Validation & Metadata
    validation_errors: List[str] = Field(default_factory=list, description="HRM validation failures")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    
    @validator('direction')
    def validate_direction(cls, v):
        allowed = ['long', 'short', 'swing']
        if v.lower() not in allowed:
            raise ValueError(f"direction must be one of {allowed}")
        return v.lower()
    
    @validator('status')
    def validate_status(cls, v):
        allowed = ['pending', 'approved', 'rejected', 'sent']
        if v.lower() not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v.lower()
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
```

---

### 2.2 AgentMessage Object

The **AgentMessage** wraps all agent-to-agent communication with observability metadata.

```python
from enum import Enum

class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"

class AgentMessage(BaseModel):
    """Envelope for agent-to-agent communication."""
    
    # Identity & Tracing
    message_id: str = Field(..., description="UUID v4 for this message")
    correlation_id: str = Field(..., description="Shared trace ID across pipeline")
    causation_id: Optional[str] = Field(None, description="Message ID that caused this message")
    
    # Routing
    from_agent: str = Field(..., description="Source agent name (e.g., 'kyle', 'joey', 'hrm')")
    to_agent: Optional[str] = Field(None, description="Target agent name (None = broadcast)")
    
    # Message Type
    message_type: MessageType = Field(..., description="Type of message")
    
    # Payload
    payload: Dict[str, Any] = Field(..., description="Message payload (can contain TradeSetup)")
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ttl_seconds: Optional[int] = Field(None, description="Time-to-live for message")
    
    # Metadata
    priority: int = Field(default=5, ge=1, le=10, description="Message priority (1=highest, 10=lowest)")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if message has exceeded TTL."""
        if self.ttl_seconds is None:
            return False
        age = (datetime.utcnow() - self.timestamp).total_seconds()
        return age > self.ttl_seconds
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
```

---

### 2.3 ErrorEscalation Object

The **ErrorEscalation** defines how agents report and escalate errors.

```python
class ErrorSeverity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorEscalation(BaseModel):
    """Error reporting and escalation structure."""
    
    # Identity
    error_id: str = Field(..., description="UUID v4 for this error")
    correlation_id: str = Field(..., description="Trace ID linking to original request")
    
    # Source
    from_agent: str = Field(..., description="Agent that encountered the error")
    
    # Error Details
    severity: ErrorSeverity = Field(..., description="Error severity level")
    error_code: str = Field(..., description="Machine-readable error code (e.g., 'PATTERN_NOT_FOUND')")
    error_message: str = Field(..., description="Human-readable error description")
    exception_type: Optional[str] = Field(None, description="Python exception class name")
    stack_trace: Optional[str] = Field(None, description="Stack trace for debugging")
    
    # Context
    context: Dict[str, Any] = Field(default_factory=dict, description="Contextual data for debugging")
    affected_trade_setup: Optional[str] = Field(None, description="TradeSetup ID if applicable")
    
    # Actions
    retry_count: int = Field(default=0, description="Number of retries attempted")
    recoverable: bool = Field(default=True, description="Whether error is recoverable")
    suggested_action: Optional[str] = Field(None, description="Recommended remediation")
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
```

---

## 3. AGENT BUS ARCHITECTURE

### 3.1 Message Bus Interface

All agents MUST communicate through the **AgentBus** singleton:

```python
from typing import Callable, Awaitable, Optional
import asyncio
from collections import defaultdict

class AgentBus:
    """Singleton message bus for agent communication."""
    
    def __init__(self):
        self._subscriptions: Dict[str, List[Callable]] = defaultdict(list)
        self._correlation_index: Dict[str, List[str]] = defaultdict(list)
        self._message_history: List[AgentMessage] = []
        self._max_history = 1000
    
    async def publish(self, message: AgentMessage) -> None:
        """Publish message to subscribers."""
        # Track in correlation index
        self._correlation_index[message.correlation_id].append(message.message_id)
        
        # Store in history
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)
        
        # Route to subscribers
        if message.to_agent:
            subscribers = self._subscriptions.get(message.to_agent, [])
        else:
            # Broadcast to all
            subscribers = [s for subs in self._subscriptions.values() for s in subs]
        
        for subscriber in subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(message)
                else:
                    subscriber(message)
            except Exception as e:
                # Log but don't crash bus
                print(f"[ERROR] Subscriber failed: {e}")
    
    def subscribe(self, agent_name: str, handler: Callable[[AgentMessage], Awaitable[None]]) -> None:
        """Subscribe agent to messages."""
        self._subscriptions[agent_name].append(handler)
    
    def get_conversation_history(self, correlation_id: str) -> List[AgentMessage]:
        """Retrieve all messages for a correlation ID."""
        message_ids = self._correlation_index.get(correlation_id, [])
        return [msg for msg in self._message_history if msg.message_id in message_ids]

# Global singleton
agent_bus = AgentBus()
```

---

### 3.2 Error Bus Interface

All agents MUST report errors through the **ErrorBus**:

```python
class ErrorBus:
    """Singleton error escalation bus."""
    
    def __init__(self):
        self._error_handlers: Dict[ErrorSeverity, List[Callable]] = defaultdict(list)
        self._error_history: List[ErrorEscalation] = []
        self._max_history = 500
    
    async def escalate(self, error: ErrorEscalation) -> None:
        """Escalate error to registered handlers."""
        # Store in history
        self._error_history.append(error)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)
        
        # Route to severity-specific handlers
        handlers = self._error_handlers.get(error.severity, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error)
                else:
                    handler(error)
            except Exception as e:
                print(f"[CRITICAL] Error handler failed: {e}")
    
    def register_handler(self, severity: ErrorSeverity, handler: Callable[[ErrorEscalation], Awaitable[None]]) -> None:
        """Register handler for specific error severity."""
        self._error_handlers[severity].append(handler)
    
    def get_errors_by_correlation(self, correlation_id: str) -> List[ErrorEscalation]:
        """Retrieve all errors for a correlation ID."""
        return [err for err in self._error_history if err.correlation_id == correlation_id]

# Global singleton
error_bus = ErrorBus()
```

---

## 4. AGENT IMPLEMENTATION CONTRACT

### 4.1 Base Agent Interface

All agents MUST inherit from **BaseAgent**:

```python
from abc import ABC, abstractmethod
import uuid

class BaseAgent(ABC):
    """Abstract base class for all ARK agents."""
    
    def __init__(self, name: str):
        self.name = name
        agent_bus.subscribe(name, self.handle_message)
    
    @abstractmethod
    async def handle_message(self, message: AgentMessage) -> None:
        """Process incoming message. MUST be implemented by subclass."""
        pass
    
    async def send_message(self, to_agent: str, payload: Dict[str, Any], 
                          message_type: MessageType = MessageType.REQUEST,
                          correlation_id: Optional[str] = None) -> str:
        """Send message to another agent."""
        message_id = str(uuid.uuid4())
        correlation_id = correlation_id or str(uuid.uuid4())
        
        message = AgentMessage(
            message_id=message_id,
            correlation_id=correlation_id,
            from_agent=self.name,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload
        )
        
        await agent_bus.publish(message)
        return message_id
    
    async def send_error(self, error_message: str, severity: ErrorSeverity,
                        error_code: str, correlation_id: str,
                        context: Optional[Dict] = None) -> None:
        """Report error to error bus."""
        error = ErrorEscalation(
            error_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            from_agent=self.name,
            severity=severity,
            error_code=error_code,
            error_message=error_message,
            context=context or {}
        )
        
        await error_bus.escalate(error)
```

---

## 5. TRADING INTELLIGENCE PIPELINE

### 5.1 Signal Flow

```
┌──────┐     ┌──────┐     ┌─────────────┐     ┌─────┐     ┌───────┐     ┌──────────┐
│ Kyle │────▶│ Joey │────▶│   Pattern   │────▶│ HRM │────▶│ Kenny │────▶│ Telegram │
│      │     │      │     │   Engine    │     │     │     │       │     │          │
└──────┘     └──────┘     └─────────────┘     └─────┘     └───────┘     └──────────┘
  Scan      Enrich        Match Pattern      Validate    Execute      Send Signal
  Market    Data         Score Setup         Ethics      Plan         @slavetotradesbot
```

### 5.2 Agent Responsibilities

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| **Kyle** | Market Scanner | External APIs | Raw market data |
| **Joey** | Data Enrichment | Raw data | Enriched TradeSetup |
| **Pattern Engine** | Pattern Matching | TradeSetup | TradeSetup + pattern + scores |
| **HRM** | Risk & Ethics Validation | TradeSetup | Approved/Rejected TradeSetup |
| **Kenny** | Execution Planning | Approved TradeSetup | TradeSetup + execution plan |
| **Telegram Service** | Signal Delivery | TradeSetup | Formatted message to bot |

### 5.3 Message Flow Example

```python
# 1. Kyle scans market
kyle_message = AgentMessage(
    message_id=uuid4(),
    correlation_id=uuid4(),  # START OF TRACE
    from_agent="kyle",
    to_agent="joey",
    message_type=MessageType.REQUEST,
    payload={"symbol": "TSLA", "scan_type": "pre_market_gainer"}
)

# 2. Joey enriches data
joey_message = AgentMessage(
    message_id=uuid4(),
    correlation_id=kyle_message.correlation_id,  # SAME TRACE
    causation_id=kyle_message.message_id,
    from_agent="joey",
    to_agent="pattern_engine",
    message_type=MessageType.REQUEST,
    payload={"trade_setup": trade_setup.dict()}
)

# 3. Pattern Engine analyzes
pattern_message = AgentMessage(
    message_id=uuid4(),
    correlation_id=kyle_message.correlation_id,  # SAME TRACE
    causation_id=joey_message.message_id,
    from_agent="pattern_engine",
    to_agent="hrm",
    message_type=MessageType.REQUEST,
    payload={"trade_setup": enriched_setup.dict()}
)

# ... and so on
```

---

## 6. CORRELATION ID REQUIREMENTS

**CRITICAL**: All agents MUST maintain **correlation_id** throughout the pipeline.

### 6.1 Correlation ID Rules

1. ✅ **Kyle** generates initial `correlation_id` (UUID v4)
2. ✅ **All downstream agents** preserve this `correlation_id`
3. ✅ **Each agent** generates unique `message_id` but keeps same `correlation_id`
4. ✅ **Error reports** include `correlation_id` for trace reconstruction

### 6.2 Logging with Correlation IDs

```python
import logging
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='unknown')

class CorrelationFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id_var.get()
        return True

# Usage in agents
async def handle_message(self, message: AgentMessage):
    correlation_id_var.set(message.correlation_id)
    logger.info(f"Processing trade setup {message.payload['symbol']}")
    # Logs automatically include correlation_id
```

---

## 7. ERROR HANDLING REQUIREMENTS

### 7.1 Retry Logic

Agents SHOULD implement exponential backoff for transient failures:

```python
async def retry_with_backoff(self, func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                await self.send_error(
                    error_message=str(e),
                    severity=ErrorSeverity.ERROR,
                    error_code="MAX_RETRIES_EXCEEDED",
                    correlation_id=correlation_id_var.get()
                )
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 7.2 Circuit Breaker Pattern

Agents calling external APIs SHOULD implement circuit breakers:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    async def call(self, func):
        if self.state == "open":
            if (datetime.utcnow() - self.last_failure_time).seconds > self.timeout:
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func()
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
```

---

## 8. ACCEPTANCE CRITERIA

### For REQ_AGENT_01 (Agent Communication Protocol)

- ✅ `AGENT_PROTOCOL.md` defines TradeSetup, AgentMessage, ErrorEscalation
- ✅ All agents use `AgentBus` for communication
- ✅ BaseAgent interface enforces contract
- ✅ Protocol supports async message passing

### For REQ_AGENT_02 (Error Escalation)

- ✅ `ErrorBus` provides centralized error routing
- ✅ Severity-based handler registration
- ✅ Error history tracking with correlation IDs
- ✅ Retry and circuit breaker patterns documented

### For REQ_AGENT_03 (Correlation IDs)

- ✅ All messages include `correlation_id` and `message_id`
- ✅ Logging filter propagates correlation IDs
- ✅ Error reports include correlation for trace reconstruction
- ✅ AgentBus maintains conversation history by correlation ID

### For REQ_AGENT_04 (HRM Arbitration)

- ✅ Protocol defines validation flow through HRM
- ✅ TradeSetup includes `validation_errors` field
- ✅ Status field tracks approval workflow
- ✅ HRM agent interface specified in pipeline

---

## 9. VERSIONING & COMPATIBILITY

**Protocol Version**: 1.0.0

**Breaking Changes**: Require major version bump  
**New Fields**: Require minor version bump  
**Bug Fixes**: Require patch version bump

Agents MUST declare supported protocol version in initialization.

---

**END OF AGENT_PROTOCOL.md**
