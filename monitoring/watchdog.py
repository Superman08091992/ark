"""
ARK Watchdog - System Monitoring and Emergency Controls

Lightweight async monitor that:
- Tracks agent health (latency, failures, rule breaches)
- Monitors Redis queue depth and performance
- Detects anomalies and generates alerts
- Provides emergency isolation/halt capabilities
- Logs compliance trends for Graveyard violations

Architecture:
- Async/await for non-blocking monitoring
- Redis pub/sub for event streaming
- Background health check loops (configurable intervals)
- Automatic isolation when thresholds exceeded
"""

import asyncio
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import deque, defaultdict
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

logger = logging.getLogger(__name__)


@dataclass
class WatchdogConfig:
    """Watchdog configuration"""
    
    # Health check intervals (seconds)
    agent_check_interval: float = 5.0  # Check agents every 5s
    redis_check_interval: float = 2.0  # Check Redis every 2s
    graveyard_check_interval: float = 10.0  # Check compliance every 10s
    
    # Thresholds for automatic action
    max_agent_latency_ms: float = 5000.0  # 5 seconds max response time
    max_agent_failure_rate: float = 0.20  # 20% max failure rate
    max_queue_depth: int = 1000  # Maximum Redis queue depth
    max_graveyard_violations_per_minute: int = 10  # Max violations/min
    max_consecutive_failures: int = 5  # Halt agent after 5 failures
    
    # Alert levels
    warning_threshold: float = 0.70  # Warn at 70% of limits
    critical_threshold: float = 0.90  # Critical at 90% of limits
    
    # History tracking
    metrics_history_size: int = 1000  # Keep last 1000 metrics
    event_history_size: int = 5000  # Keep last 5000 events
    
    # Emergency controls
    enable_auto_isolation: bool = True  # Auto-isolate failing agents
    enable_emergency_halt: bool = True  # Allow emergency stop


@dataclass
class AgentMetrics:
    """Metrics for a single agent"""
    agent_name: str
    last_seen: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    consecutive_failures: int = 0
    isolated: bool = False
    graveyard_violations: int = 0
    recent_latencies: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_failures: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests
    
    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency"""
        if len(self.recent_latencies) == 0:
            return 0.0
        return sum(self.recent_latencies) / len(self.recent_latencies)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def health_score(self) -> float:
        """Calculate overall health score (0.0 to 1.0)"""
        # Combine success rate, latency, and recency
        recency_factor = 1.0 if time.time() - self.last_seen < 60 else 0.5
        latency_factor = max(0.0, 1.0 - (self.avg_latency_ms / 10000.0))  # Normalize to 10s max
        return (self.success_rate * 0.5 + latency_factor * 0.3 + recency_factor * 0.2)


class Watchdog:
    """
    ARK Watchdog - System monitoring and emergency controls
    
    Monitors:
    - Agent health (6 agents: Kyle, Joey, Kenny, HRM, Aletheia, ID)
    - Redis queue depth and performance
    - Graveyard compliance trends
    - System-wide anomalies
    
    Capabilities:
    - Real-time health tracking
    - Automatic agent isolation
    - Emergency system halt
    - Alert generation
    - Compliance reporting
    """
    
    def __init__(self, config: Optional[WatchdogConfig] = None, redis_url: str = "redis://redis:6379"):
        self.config = config or WatchdogConfig()
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        
        # Agent tracking
        self.agent_names = ['Kyle', 'Joey', 'Kenny', 'HRM', 'Aletheia', 'ID']
        self.agent_metrics: Dict[str, AgentMetrics] = {
            name: AgentMetrics(agent_name=name) for name in self.agent_names
        }
        
        # System state
        self.running = False
        self.emergency_halt = False
        self.start_time = time.time()
        
        # Event tracking
        self.events: deque = deque(maxlen=self.config.event_history_size)
        self.alerts: deque = deque(maxlen=self.config.metrics_history_size)
        
        # Redis metrics
        self.redis_queue_depth = 0
        self.redis_latency_ms = 0.0
        self.redis_last_check = 0.0
        
        # Graveyard compliance tracking
        self.graveyard_violations_last_minute: deque = deque(maxlen=100)
        
        logger.info("🐕 Watchdog initialized with config: %s", self.config)
    
    async def connect(self):
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available, running in standalone mode")
            return
        
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("🐕 Watchdog connected to Redis")
        except Exception as e:
            logger.error(f"Watchdog Redis connection failed: {e}")
            # Don't raise - allow standalone operation
            self.redis = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("🐕 Watchdog disconnected from Redis")
    
    async def start(self):
        """Start Watchdog monitoring (non-blocking)"""
        if self.running:
            logger.warning("Watchdog already running")
            return
        
        self.running = True
        self.start_time = time.time()
        
        logger.info("🐕 Watchdog starting monitoring...")
        
        # Start background monitoring tasks
        await asyncio.gather(
            self._monitor_agents(),
            self._monitor_redis(),
            self._monitor_graveyard(),
            self._process_events(),
            return_exceptions=True
        )
    
    async def stop(self):
        """Stop Watchdog monitoring"""
        self.running = False
        logger.info("🐕 Watchdog stopped")
    
    async def _monitor_agents(self):
        """Monitor agent health in background loop"""
        logger.info("🐕 Agent monitoring started")
        
        while self.running:
            try:
                for agent_name in self.agent_names:
                    await self._check_agent_health(agent_name)
                
                await asyncio.sleep(self.config.agent_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Agent monitoring error: {e}")
                await asyncio.sleep(self.config.agent_check_interval)
    
    async def _monitor_redis(self):
        """Monitor Redis queue and performance in background loop"""
        logger.info("🐕 Redis monitoring started")
        
        while self.running:
            try:
                # Check Redis health
                start = time.time()
                
                # Queue depth
                self.redis_queue_depth = await self.redis.llen('agent_tasks') if self.redis else 0
                
                # Latency
                await self.redis.ping() if self.redis else None
                self.redis_latency_ms = (time.time() - start) * 1000
                self.redis_last_check = time.time()
                
                # Check thresholds
                if self.redis_queue_depth > self.config.max_queue_depth:
                    await self._generate_alert(
                        'CRITICAL',
                        'redis_queue_overload',
                        f"Redis queue depth {self.redis_queue_depth} exceeds maximum {self.config.max_queue_depth}"
                    )
                
                await asyncio.sleep(self.config.redis_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Redis monitoring error: {e}")
                await asyncio.sleep(self.config.redis_check_interval)
    
    async def _monitor_graveyard(self):
        """Monitor Graveyard compliance trends in background loop"""
        logger.info("🐕 Graveyard monitoring started")
        
        while self.running:
            try:
                # Check violation rate
                current_time = time.time()
                one_minute_ago = current_time - 60
                
                # Count violations in last minute
                recent_violations = [
                    v for v in self.graveyard_violations_last_minute
                    if v > one_minute_ago
                ]
                
                violations_per_minute = len(recent_violations)
                
                if violations_per_minute > self.config.max_graveyard_violations_per_minute:
                    await self._generate_alert(
                        'CRITICAL',
                        'graveyard_violation_spike',
                        f"Graveyard violations ({violations_per_minute}/min) exceed threshold ({self.config.max_graveyard_violations_per_minute}/min)"
                    )
                
                await asyncio.sleep(self.config.graveyard_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Graveyard monitoring error: {e}")
                await asyncio.sleep(self.config.graveyard_check_interval)
    
    async def _process_events(self):
        """Process events from Redis pub/sub in background loop"""
        logger.info("🐕 Event processing started")
        
        if not self.redis:
            logger.warning("Redis not connected, event processing disabled")
            return
        
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe('agent_events', 'graveyard_events', 'system_events')
            
            while self.running:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    
                    if message:
                        await self._handle_event(message)
                    
                    await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Event processing error: {e}")
            
            await pubsub.unsubscribe()
            await pubsub.close()
            
        except Exception as e:
            logger.error(f"Event subscription error: {e}")
    
    async def _check_agent_health(self, agent_name: str):
        """Check health of a specific agent"""
        metrics = self.agent_metrics[agent_name]
        
        # Check for isolation conditions
        if self.config.enable_auto_isolation and not metrics.isolated:
            # Isolate if consecutive failures exceed threshold
            if metrics.consecutive_failures >= self.config.max_consecutive_failures:
                await self.isolate_agent(agent_name, f"Consecutive failures: {metrics.consecutive_failures}")
            
            # Isolate if failure rate too high
            elif metrics.failure_rate > self.config.max_agent_failure_rate and metrics.total_requests > 10:
                await self.isolate_agent(agent_name, f"Failure rate: {metrics.failure_rate:.1%}")
            
            # Isolate if latency too high
            elif metrics.avg_latency_ms > self.config.max_agent_latency_ms and len(metrics.recent_latencies) > 10:
                await self.isolate_agent(agent_name, f"Average latency: {metrics.avg_latency_ms:.0f}ms")
        
        # Check for warnings
        if not metrics.isolated:
            # Warn if approaching limits
            if metrics.failure_rate > self.config.max_agent_failure_rate * self.config.warning_threshold:
                await self._generate_alert(
                    'WARNING',
                    f'{agent_name}_high_failure_rate',
                    f"{agent_name} failure rate {metrics.failure_rate:.1%} approaching limit"
                )
            
            if metrics.avg_latency_ms > self.config.max_agent_latency_ms * self.config.warning_threshold:
                await self._generate_alert(
                    'WARNING',
                    f'{agent_name}_high_latency',
                    f"{agent_name} latency {metrics.avg_latency_ms:.0f}ms approaching limit"
                )
    
    async def _handle_event(self, message: Dict[str, Any]):
        """Handle incoming event from Redis pub/sub"""
        try:
            channel = message.get('channel', '')
            data_str = message.get('data', '{}')
            
            if isinstance(data_str, bytes):
                data_str = data_str.decode('utf-8')
            
            data = json.loads(data_str) if isinstance(data_str, str) else data_str
            
            # Record event
            event = {
                'timestamp': time.time(),
                'channel': channel,
                'data': data
            }
            self.events.append(event)
            
            # Process agent events
            if channel == 'agent_events':
                agent_name = data.get('agent')
                event_type = data.get('type')
                
                if agent_name and event_type:
                    await self._update_agent_metrics(agent_name, event_type, data)
            
            # Process graveyard events
            elif channel == 'graveyard_events':
                event_type = data.get('type')
                
                if event_type == 'violation':
                    self.graveyard_violations_last_minute.append(time.time())
                    agent_name = data.get('agent')
                    if agent_name and agent_name in self.agent_metrics:
                        self.agent_metrics[agent_name].graveyard_violations += 1
            
        except Exception as e:
            logger.error(f"Event handling error: {e}")
    
    async def _update_agent_metrics(self, agent_name: str, event_type: str, data: Dict[str, Any]):
        """Update agent metrics based on event"""
        if agent_name not in self.agent_metrics:
            return
        
        metrics = self.agent_metrics[agent_name]
        metrics.last_seen = time.time()
        
        if event_type == 'request':
            metrics.total_requests += 1
            
            # Track latency if provided
            latency_ms = data.get('latency_ms', 0)
            if latency_ms > 0:
                metrics.recent_latencies.append(latency_ms)
                metrics.total_latency_ms += latency_ms
        
        elif event_type == 'success':
            metrics.successful_requests += 1
            metrics.consecutive_failures = 0  # Reset
        
        elif event_type == 'failure':
            metrics.failed_requests += 1
            metrics.consecutive_failures += 1
            metrics.recent_failures.append(time.time())
    
    async def isolate_agent(self, agent_name: str, reason: str):
        """Isolate an agent (stop processing its tasks)"""
        if agent_name not in self.agent_metrics:
            logger.error(f"Cannot isolate unknown agent: {agent_name}")
            return
        
        metrics = self.agent_metrics[agent_name]
        
        if metrics.isolated:
            logger.warning(f"Agent {agent_name} already isolated")
            return
        
        metrics.isolated = True
        
        await self._generate_alert(
            'CRITICAL',
            f'{agent_name}_isolated',
            f"Agent {agent_name} isolated: {reason}"
        )
        
        # Publish isolation event
        if self.redis:
            await self.redis.publish('system_events', json.dumps({
                'type': 'agent_isolated',
                'agent': agent_name,
                'reason': reason,
                'timestamp': time.time()
            }))
        
        logger.warning(f"🚨 Agent {agent_name} ISOLATED: {reason}")
    
    async def restore_agent(self, agent_name: str):
        """Restore an isolated agent"""
        if agent_name not in self.agent_metrics:
            logger.error(f"Cannot restore unknown agent: {agent_name}")
            return
        
        metrics = self.agent_metrics[agent_name]
        
        if not metrics.isolated:
            logger.warning(f"Agent {agent_name} not isolated")
            return
        
        metrics.isolated = False
        metrics.consecutive_failures = 0  # Reset
        
        # Publish restoration event
        if self.redis:
            await self.redis.publish('system_events', json.dumps({
                'type': 'agent_restored',
                'agent': agent_name,
                'timestamp': time.time()
            }))
        
        logger.info(f"✅ Agent {agent_name} restored")
    
    async def emergency_stop(self, reason: str):
        """Emergency halt of the entire system"""
        if not self.config.enable_emergency_halt:
            logger.error("Emergency halt disabled in config")
            return False
        
        self.emergency_halt = True
        
        await self._generate_alert(
            'EMERGENCY',
            'system_emergency_halt',
            f"EMERGENCY STOP: {reason}"
        )
        
        # Isolate all agents
        for agent_name in self.agent_names:
            await self.isolate_agent(agent_name, "Emergency stop")
        
        # Publish emergency halt event
        if self.redis:
            await self.redis.publish('system_events', json.dumps({
                'type': 'emergency_halt',
                'reason': reason,
                'timestamp': time.time()
            }))
        
        logger.critical(f"🚨🚨🚨 EMERGENCY HALT: {reason}")
        
        return True
    
    async def _generate_alert(self, level: str, alert_type: str, message: str):
        """Generate an alert"""
        alert = {
            'timestamp': time.time(),
            'level': level,
            'type': alert_type,
            'message': message
        }
        
        self.alerts.append(alert)
        
        # Log based on level
        if level == 'EMERGENCY':
            logger.critical(f"🚨 ALERT [{level}] {alert_type}: {message}")
        elif level == 'CRITICAL':
            logger.error(f"🚨 ALERT [{level}] {alert_type}: {message}")
        elif level == 'WARNING':
            logger.warning(f"⚠️  ALERT [{level}] {alert_type}: {message}")
        else:
            logger.info(f"ℹ️  ALERT [{level}] {alert_type}: {message}")
        
        # Publish alert
        if self.redis:
            await self.redis.publish('alerts', json.dumps(alert))
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        uptime = time.time() - self.start_time
        
        # Agent health summary
        agents_health = {}
        for agent_name, metrics in self.agent_metrics.items():
            agents_health[agent_name] = {
                'health_score': round(metrics.health_score, 3),
                'success_rate': round(metrics.success_rate, 3),
                'avg_latency_ms': round(metrics.avg_latency_ms, 2),
                'total_requests': metrics.total_requests,
                'failures': metrics.failed_requests,
                'isolated': metrics.isolated,
                'graveyard_violations': metrics.graveyard_violations,
                'last_seen_ago_seconds': round(time.time() - metrics.last_seen, 1) if metrics.last_seen > 0 else None
            }
        
        # Overall system health (average agent health)
        agent_scores = [m.health_score for m in self.agent_metrics.values() if not m.isolated]
        system_health_score = sum(agent_scores) / len(agent_scores) if agent_scores else 0.0
        
        # Recent alerts
        recent_alerts = list(self.alerts)[-10:]  # Last 10 alerts
        
        return {
            'status': 'emergency_halt' if self.emergency_halt else 'running' if self.running else 'stopped',
            'uptime_seconds': round(uptime, 1),
            'system_health_score': round(system_health_score, 3),
            'agents': agents_health,
            'redis': {
                'queue_depth': self.redis_queue_depth,
                'latency_ms': round(self.redis_latency_ms, 2),
                'last_check_ago_seconds': round(time.time() - self.redis_last_check, 1) if self.redis_last_check > 0 else None
            },
            'graveyard': {
                'violations_last_minute': len([v for v in self.graveyard_violations_last_minute if v > time.time() - 60]),
                'total_violations': sum(m.graveyard_violations for m in self.agent_metrics.values())
            },
            'recent_alerts': recent_alerts,
            'config': {
                'auto_isolation_enabled': self.config.enable_auto_isolation,
                'emergency_halt_enabled': self.config.enable_emergency_halt
            }
        }


# Convenience function
async def get_system_health(redis_url: str = "redis://redis:6379") -> Dict[str, Any]:
    """Quick system health check (standalone function)"""
    watchdog = Watchdog(redis_url=redis_url)
    try:
        await watchdog.connect()
        health = watchdog.get_system_health()
        await watchdog.disconnect()
        return health
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


# CLI for testing
if __name__ == "__main__":
    import sys
    
    async def main():
        print("=" * 60)
        print("ARK WATCHDOG - System Monitor")
        print("=" * 60)
        print()
        
        # Create Watchdog
        config = WatchdogConfig(
            agent_check_interval=2.0,
            redis_check_interval=1.0,
            graveyard_check_interval=5.0
        )
        
        watchdog = Watchdog(config=config, redis_url="redis://localhost:6379")
        
        try:
            print("Connecting to Redis...")
            await watchdog.connect()
            print("✅ Connected\n")
            
            print("Starting Watchdog monitoring...")
            print("(Press Ctrl+C to stop)\n")
            
            # Start monitoring in background
            monitor_task = asyncio.create_task(watchdog.start())
            
            # Periodically print status
            while True:
                await asyncio.sleep(10)
                
                health = watchdog.get_system_health()
                print(f"\n{'=' * 60}")
                print(f"System Health: {health['system_health_score']:.1%}")
                print(f"Uptime: {health['uptime_seconds']:.0f}s")
                print(f"{'=' * 60}")
                
                for agent_name, agent_health in health['agents'].items():
                    status = "🔴 ISOLATED" if agent_health['isolated'] else "🟢 OK"
                    print(f"{agent_name:10} {status} | Health: {agent_health['health_score']:.1%} | "
                          f"Requests: {agent_health['total_requests']} | "
                          f"Failures: {agent_health['failures']}")
                
                print(f"\nRedis Queue: {health['redis']['queue_depth']} tasks")
                print(f"Graveyard Violations (last min): {health['graveyard']['violations_last_minute']}")
                
                if health['recent_alerts']:
                    print(f"\nRecent Alerts ({len(health['recent_alerts'])}):")
                    for alert in health['recent_alerts'][-3:]:
                        print(f"  [{alert['level']}] {alert['message']}")
        
        except KeyboardInterrupt:
            print("\n\nStopping Watchdog...")
            await watchdog.stop()
            await watchdog.disconnect()
            print("✅ Stopped")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await watchdog.disconnect()
            sys.exit(1)
    
    asyncio.run(main())
