"""
ARK Watchdog - System Monitoring and Emergency Controls

Monitors:
- Agent health (response times, errors, availability)
- Graveyard compliance (rule violations, ethics breaches)
- System resources (memory, CPU, queue depth)
- Redis communication (message latency, failures)

Emergency Controls:
- Emergency halt: Stop all agent task processing
- Agent isolation: Quarantine misbehaving agents
- Circuit breaker: Prevent cascade failures
"""

import asyncio
import time
import redis
import json
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import deque
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AgentHealth:
    """Health metrics for an agent"""
    name: str
    status: str  # 'healthy', 'degraded', 'unhealthy', 'offline'
    last_heartbeat: float
    response_time_avg_ms: float
    response_time_p95_ms: float
    error_count: int
    error_rate: float
    task_count: int
    success_rate: float
    violations_count: int
    last_violation: Optional[str]
    uptime_seconds: float
    

@dataclass
class SystemHealth:
    """Overall system health"""
    status: str  # 'healthy', 'degraded', 'critical', 'emergency'
    timestamp: str
    uptime_seconds: float
    agents_healthy: int
    agents_degraded: int
    agents_unhealthy: int
    agents_offline: int
    total_agents: int
    redis_connected: bool
    redis_latency_ms: float
    queue_depth: int
    memory_usage_pct: float
    cpu_usage_pct: float
    graveyard_violations_total: int
    graveyard_violations_critical: int
    emergency_halt_active: bool


class Watchdog:
    """
    System monitoring and emergency control service.
    
    Runs as an async background service monitoring all agents and system health.
    Can trigger emergency halt if critical violations detected.
    """
    
    def __init__(self, redis_host: str = 'redis', redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client: Optional[redis.Redis] = None
        
        # Watchdog state
        self.running = False
        self.start_time = time.time()
        self.emergency_halt = False
        self.isolated_agents = set()
        
        # Health tracking
        self.agent_health: Dict[str, AgentHealth] = {}
        self.system_health: Optional[SystemHealth] = None
        
        # Metrics history (last 100 datapoints)
        self.response_times: Dict[str, deque] = {}
        self.error_counts: Dict[str, deque] = {}
        self.violation_history: deque = deque(maxlen=100)
        
        # Initialize metrics
        self.system_metrics = {
            'redis_connected': False,
            'redis_latency_ms': 0,
            'queue_depth': 0,
            'memory_usage_pct': 0,
            'cpu_usage_pct': 0
        }
        self.graveyard_metrics = {
            'total_violations': 0,
            'critical_violations': 0
        }
        
        # Configuration
        self.config = {
            'check_interval_seconds': 5,
            'heartbeat_timeout_seconds': 30,
            'response_time_threshold_ms': 5000,  # 5 second threshold
            'error_rate_threshold': 0.20,  # 20% error rate
            'violation_rate_threshold': 0.10,  # 10% violation rate
            'critical_violations_threshold': 3,  # 3 critical violations triggers halt
            'queue_depth_threshold': 100,
            'memory_threshold_pct': 90.0,
            'cpu_threshold_pct': 90.0
        }
        
        logger.info("Watchdog initialized")
    
    async def start(self):
        """Start Watchdog monitoring"""
        if self.running:
            logger.warning("Watchdog already running")
            return
        
        logger.info("Starting Watchdog monitoring service...")
        
        # Connect to Redis
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            logger.info("Watchdog connected to Redis")
        except Exception as e:
            logger.error(f"Watchdog failed to connect to Redis: {e}")
            self.redis_client = None
        
        self.running = True
        self.start_time = time.time()
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
        
        logger.info("✅ Watchdog monitoring active")
    
    async def stop(self):
        """Stop Watchdog monitoring"""
        logger.info("Stopping Watchdog...")
        self.running = False
        
        if self.redis_client:
            self.redis_client.close()
        
        logger.info("✅ Watchdog stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect health metrics
                await self._collect_agent_health()
                await self._collect_system_metrics()
                
                # Check for violations
                await self._check_graveyard_compliance()
                
                # Evaluate system health
                await self._evaluate_system_health()
                
                # Check for emergency conditions
                await self._check_emergency_conditions()
                
                # Publish health status to Redis
                await self._publish_health_status()
                
            except Exception as e:
                logger.error(f"Watchdog monitoring error: {e}")
            
            # Sleep until next check
            await asyncio.sleep(self.config['check_interval_seconds'])
    
    async def _collect_agent_health(self):
        """Collect health metrics for all agents"""
        if not self.redis_client:
            return
        
        agents = ['Kyle', 'Joey', 'Kenny', 'HRM', 'Aletheia', 'ID']
        
        for agent_name in agents:
            try:
                # Get agent heartbeat from Redis
                heartbeat_key = f"agent_heartbeat:{agent_name}"
                heartbeat = self.redis_client.get(heartbeat_key)
                
                if heartbeat:
                    heartbeat_time = float(heartbeat)
                    time_since_heartbeat = time.time() - heartbeat_time
                    
                    # Get agent metrics
                    metrics_key = f"agent_metrics:{agent_name}"
                    metrics = self.redis_client.get(metrics_key)
                    
                    if metrics:
                        metrics_data = json.loads(metrics)
                        
                        # Determine agent status
                        if time_since_heartbeat > self.config['heartbeat_timeout_seconds']:
                            status = 'offline'
                        elif metrics_data.get('error_rate', 0) > self.config['error_rate_threshold']:
                            status = 'unhealthy'
                        elif metrics_data.get('response_time_avg_ms', 0) > self.config['response_time_threshold_ms']:
                            status = 'degraded'
                        else:
                            status = 'healthy'
                        
                        # Update agent health
                        self.agent_health[agent_name] = AgentHealth(
                            name=agent_name,
                            status=status,
                            last_heartbeat=heartbeat_time,
                            response_time_avg_ms=metrics_data.get('response_time_avg_ms', 0),
                            response_time_p95_ms=metrics_data.get('response_time_p95_ms', 0),
                            error_count=metrics_data.get('error_count', 0),
                            error_rate=metrics_data.get('error_rate', 0),
                            task_count=metrics_data.get('task_count', 0),
                            success_rate=metrics_data.get('success_rate', 1.0),
                            violations_count=metrics_data.get('violations_count', 0),
                            last_violation=metrics_data.get('last_violation'),
                            uptime_seconds=time.time() - self.start_time
                        )
                else:
                    # No heartbeat - agent is offline
                    self.agent_health[agent_name] = AgentHealth(
                        name=agent_name,
                        status='offline',
                        last_heartbeat=0,
                        response_time_avg_ms=0,
                        response_time_p95_ms=0,
                        error_count=0,
                        error_rate=0,
                        task_count=0,
                        success_rate=0,
                        violations_count=0,
                        last_violation=None,
                        uptime_seconds=0
                    )
            
            except Exception as e:
                logger.error(f"Error collecting health for {agent_name}: {e}")
    
    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        if not self.redis_client:
            return
        
        try:
            # Redis latency check
            start = time.time()
            self.redis_client.ping()
            redis_latency_ms = (time.time() - start) * 1000
            
            # Queue depth
            queue_depth = self.redis_client.llen('agent_tasks')
            
            # System resources
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.1)
            
            # Store metrics
            self.system_metrics = {
                'redis_connected': True,
                'redis_latency_ms': redis_latency_ms,
                'queue_depth': queue_depth,
                'memory_usage_pct': memory.percent,
                'cpu_usage_pct': cpu
            }
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            self.system_metrics = {
                'redis_connected': False,
                'redis_latency_ms': 0,
                'queue_depth': 0,
                'memory_usage_pct': 0,
                'cpu_usage_pct': 0
            }
    
    async def _check_graveyard_compliance(self):
        """Check for Graveyard rule violations"""
        if not self.redis_client:
            return
        
        try:
            # Get violation count from Redis
            violation_key = "graveyard_violations:total"
            total_violations = int(self.redis_client.get(violation_key) or 0)
            
            critical_key = "graveyard_violations:critical"
            critical_violations = int(self.redis_client.get(critical_key) or 0)
            
            self.graveyard_metrics = {
                'total_violations': total_violations,
                'critical_violations': critical_violations
            }
            
            # Record violation history
            self.violation_history.append({
                'timestamp': time.time(),
                'total': total_violations,
                'critical': critical_violations
            })
            
        except Exception as e:
            logger.error(f"Error checking Graveyard compliance: {e}")
            self.graveyard_metrics = {
                'total_violations': 0,
                'critical_violations': 0
            }
    
    async def _evaluate_system_health(self):
        """Evaluate overall system health"""
        
        # Count agent statuses
        agents_healthy = sum(1 for h in self.agent_health.values() if h.status == 'healthy')
        agents_degraded = sum(1 for h in self.agent_health.values() if h.status == 'degraded')
        agents_unhealthy = sum(1 for h in self.agent_health.values() if h.status == 'unhealthy')
        agents_offline = sum(1 for h in self.agent_health.values() if h.status == 'offline')
        total_agents = len(self.agent_health)
        
        # Determine overall system status
        if self.emergency_halt:
            status = 'emergency'
        elif agents_unhealthy > 0 or agents_offline > 2:
            status = 'critical'
        elif agents_degraded > 1 or agents_offline > 0:
            status = 'degraded'
        else:
            status = 'healthy'
        
        # Check system metrics
        if hasattr(self, 'system_metrics'):
            if self.system_metrics.get('memory_usage_pct', 0) > self.config['memory_threshold_pct']:
                status = 'critical' if status == 'healthy' else status
            if self.system_metrics.get('cpu_usage_pct', 0) > self.config['cpu_threshold_pct']:
                status = 'degraded' if status == 'healthy' else status
        
        # Build system health
        self.system_health = SystemHealth(
            status=status,
            timestamp=datetime.now().isoformat(),
            uptime_seconds=time.time() - self.start_time,
            agents_healthy=agents_healthy,
            agents_degraded=agents_degraded,
            agents_unhealthy=agents_unhealthy,
            agents_offline=agents_offline,
            total_agents=total_agents,
            redis_connected=self.system_metrics.get('redis_connected', False),
            redis_latency_ms=self.system_metrics.get('redis_latency_ms', 0),
            queue_depth=self.system_metrics.get('queue_depth', 0),
            memory_usage_pct=self.system_metrics.get('memory_usage_pct', 0),
            cpu_usage_pct=self.system_metrics.get('cpu_usage_pct', 0),
            graveyard_violations_total=self.graveyard_metrics.get('total_violations', 0),
            graveyard_violations_critical=self.graveyard_metrics.get('critical_violations', 0),
            emergency_halt_active=self.emergency_halt
        )
    
    async def _check_emergency_conditions(self):
        """Check for conditions requiring emergency halt"""
        
        # Check critical violations threshold
        if hasattr(self, 'graveyard_metrics'):
            critical_violations = self.graveyard_metrics.get('critical_violations', 0)
            
            if critical_violations >= self.config['critical_violations_threshold']:
                logger.critical(f"🚨 EMERGENCY: {critical_violations} critical violations detected!")
                await self.trigger_emergency_halt("Critical Graveyard violations threshold exceeded")
        
        # Check for catastrophic system failures
        if self.system_health:
            if self.system_health.agents_offline >= 4:  # More than half agents offline
                logger.critical("🚨 EMERGENCY: Majority of agents offline!")
                await self.trigger_emergency_halt("Catastrophic agent failure")
    
    async def trigger_emergency_halt(self, reason: str):
        """Trigger emergency halt of all agent processing"""
        if self.emergency_halt:
            return  # Already halted
        
        logger.critical(f"🚨🚨🚨 EMERGENCY HALT TRIGGERED: {reason} 🚨🚨🚨")
        
        self.emergency_halt = True
        
        # Publish emergency halt to Redis
        if self.redis_client:
            self.redis_client.set('system_emergency_halt', 'true')
            self.redis_client.set('emergency_halt_reason', reason)
            self.redis_client.set('emergency_halt_timestamp', time.time())
            
            # Publish to emergency channel
            self.redis_client.publish('emergency_halt', json.dumps({
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
                'watchdog': 'active'
            }))
        
        logger.critical("All agent task processing halted")
    
    async def clear_emergency_halt(self):
        """Clear emergency halt (manual intervention)"""
        logger.warning("Clearing emergency halt...")
        
        self.emergency_halt = False
        
        if self.redis_client:
            self.redis_client.delete('system_emergency_halt')
            self.redis_client.delete('emergency_halt_reason')
            
            # Publish clear message
            self.redis_client.publish('emergency_clear', json.dumps({
                'timestamp': datetime.now().isoformat(),
                'watchdog': 'active'
            }))
        
        logger.info("✅ Emergency halt cleared")
    
    async def isolate_agent(self, agent_name: str, reason: str):
        """Isolate a misbehaving agent"""
        logger.warning(f"Isolating agent {agent_name}: {reason}")
        
        self.isolated_agents.add(agent_name)
        
        if self.redis_client:
            isolation_key = f"agent_isolated:{agent_name}"
            self.redis_client.set(isolation_key, json.dumps({
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }))
        
        logger.info(f"✅ Agent {agent_name} isolated")
    
    async def restore_agent(self, agent_name: str):
        """Restore an isolated agent"""
        logger.info(f"Restoring agent {agent_name}...")
        
        self.isolated_agents.discard(agent_name)
        
        if self.redis_client:
            isolation_key = f"agent_isolated:{agent_name}"
            self.redis_client.delete(isolation_key)
        
        logger.info(f"✅ Agent {agent_name} restored")
    
    async def _publish_health_status(self):
        """Publish health status to Redis"""
        if not self.redis_client:
            return
        
        try:
            # Publish system health
            if self.system_health:
                self.redis_client.set(
                    'watchdog_system_health',
                    json.dumps(asdict(self.system_health)),
                    ex=60  # 60 second TTL
                )
            
            # Publish agent health
            for agent_name, health in self.agent_health.items():
                self.redis_client.set(
                    f'watchdog_agent_health:{agent_name}',
                    json.dumps(asdict(health)),
                    ex=60
                )
        
        except Exception as e:
            logger.error(f"Error publishing health status: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current Watchdog status"""
        return {
            'running': self.running,
            'uptime_seconds': time.time() - self.start_time if self.running else 0,
            'emergency_halt': self.emergency_halt,
            'isolated_agents': list(self.isolated_agents),
            'system_health': asdict(self.system_health) if self.system_health else None,
            'agent_health': {name: asdict(health) for name, health in self.agent_health.items()},
            'config': self.config
        }


# Global Watchdog instance
_watchdog_instance: Optional[Watchdog] = None


async def start_watchdog(redis_host: str = 'redis', redis_port: int = 6379) -> Watchdog:
    """Start the global Watchdog instance"""
    global _watchdog_instance
    
    if _watchdog_instance is None:
        _watchdog_instance = Watchdog(redis_host, redis_port)
    
    await _watchdog_instance.start()
    return _watchdog_instance


async def stop_watchdog():
    """Stop the global Watchdog instance"""
    global _watchdog_instance
    
    if _watchdog_instance:
        await _watchdog_instance.stop()


def get_watchdog_status() -> Dict[str, Any]:
    """Get status of global Watchdog instance"""
    global _watchdog_instance
    
    if _watchdog_instance:
        return _watchdog_instance.get_status()
    else:
        return {'running': False, 'error': 'Watchdog not initialized'}
