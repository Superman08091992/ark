"""
ARK Agent Instrumentation

Decorator-based instrumentation for automatic metrics collection and trace ID propagation.

Usage:
    from monitoring.instrumentation import instrument_agent_method, with_trace_id
    
    class Kyle(BaseAgent):
        @instrument_agent_method(latency_metric="kyle_ingest_latency_ms")
        async def process_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
            # Method automatically tracked with metrics
            pass
        
        @with_trace_id
        async def handle_event(self, event: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
            # trace_id automatically injected and tracked
            pass

Author: ARK System
Created: 2025-11-10
"""

import time
import functools
import logging
from typing import Callable, Any, Optional, Dict
import asyncio
import uuid

from monitoring.metrics import (
    record_latency,
    increment_counter,
    set_gauge,
    record_trace
)

logger = logging.getLogger(__name__)


def instrument_agent_method(
    latency_metric: Optional[str] = None,
    counter_metric: Optional[str] = None,
    track_errors: bool = True
):
    """
    Decorator to automatically instrument agent methods with metrics.
    
    Args:
        latency_metric: Name of histogram metric for latency tracking
        counter_metric: Name of counter metric to increment on each call
        track_errors: If True, increment error counter on exceptions
    
    Example:
        @instrument_agent_method(
            latency_metric="kyle_process_latency_ms",
            counter_metric="kyle_signals_processed_total"
        )
        async def process_signal(self, signal):
            # Processing logic
            return result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            start_time = time.time()
            agent_name = getattr(self, "name", self.__class__.__name__)
            
            # Increment call counter
            if counter_metric:
                increment_counter(counter_metric, labels={"agent": agent_name})
            
            try:
                # Execute method
                result = await func(self, *args, **kwargs)
                
                # Record latency
                if latency_metric:
                    latency_ms = (time.time() - start_time) * 1000
                    record_latency(latency_metric, latency_ms, labels={"agent": agent_name})
                
                return result
            
            except Exception as e:
                # Track errors
                if track_errors:
                    increment_counter(
                        "agent_method_errors_total",
                        labels={
                            "agent": agent_name,
                            "method": func.__name__,
                            "error_type": type(e).__name__
                        }
                    )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            start_time = time.time()
            agent_name = getattr(self, "name", self.__class__.__name__)
            
            # Increment call counter
            if counter_metric:
                increment_counter(counter_metric, labels={"agent": agent_name})
            
            try:
                # Execute method
                result = func(self, *args, **kwargs)
                
                # Record latency
                if latency_metric:
                    latency_ms = (time.time() - start_time) * 1000
                    record_latency(latency_metric, latency_ms, labels={"agent": agent_name})
                
                return result
            
            except Exception as e:
                # Track errors
                if track_errors:
                    increment_counter(
                        "agent_method_errors_total",
                        labels={
                            "agent": agent_name,
                            "method": func.__name__,
                            "error_type": type(e).__name__
                        }
                    )
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def with_trace_id(func: Callable) -> Callable:
    """
    Decorator to automatically inject and track trace_id across agent pipeline.
    
    The trace_id is:
    1. Extracted from kwargs if present
    2. Extracted from first arg if it's a dict with 'trace_id' key
    3. Generated as new UUID if not found
    
    The trace_id is then:
    - Passed to the wrapped function
    - Recorded in metrics for continuity tracking
    - Logged for correlation
    
    Example:
        @with_trace_id
        async def process_event(self, event: Dict, trace_id: str):
            # trace_id is automatically available
            logger.info(f"Processing {trace_id}")
            return result
    """
    @functools.wraps(func)
    async def async_wrapper(self, *args, **kwargs):
        # Extract or generate trace_id
        trace_id = kwargs.get("trace_id")
        
        if not trace_id and args and isinstance(args[0], dict):
            trace_id = args[0].get("trace_id")
        
        if not trace_id:
            trace_id = str(uuid.uuid4())
            logger.debug(f"Generated new trace_id: {trace_id}")
        
        # Inject trace_id into kwargs
        kwargs["trace_id"] = trace_id
        
        # Record trace span
        agent_name = getattr(self, "name", self.__class__.__name__)
        record_trace(trace_id, agent_name)
        
        # Execute with trace_id
        try:
            result = await func(self, *args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error in {agent_name} for trace {trace_id}: {e}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(self, *args, **kwargs):
        # Extract or generate trace_id
        trace_id = kwargs.get("trace_id")
        
        if not trace_id and args and isinstance(args[0], dict):
            trace_id = args[0].get("trace_id")
        
        if not trace_id:
            trace_id = str(uuid.uuid4())
            logger.debug(f"Generated new trace_id: {trace_id}")
        
        # Inject trace_id into kwargs
        kwargs["trace_id"] = trace_id
        
        # Record trace span
        agent_name = getattr(self, "name", self.__class__.__name__)
        record_trace(trace_id, agent_name)
        
        # Execute with trace_id
        try:
            result = func(self, *args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error in {agent_name} for trace {trace_id}: {e}")
            raise
    
    # Return appropriate wrapper
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def track_agent_state(agent_name: str, state_key: str, state_value: Any):
    """
    Track agent state change as gauge metric.
    
    Args:
        agent_name: Name of agent
        state_key: State key being updated
        state_value: New value (must be numeric)
    
    Example:
        track_agent_state("Joey", "pattern_confidence", 0.85)
    """
    if not isinstance(state_value, (int, float)):
        logger.warning(f"Cannot track non-numeric state: {state_key}={state_value}")
        return
    
    metric_name = f"agent_state_{state_key}"
    set_gauge(metric_name, state_value, labels={"agent": agent_name})


def track_hrm_denial(rule_id: str, agent_name: str, action_type: str):
    """
    Track HRM ethics denial with detailed labels.
    
    Args:
        rule_id: Graveyard rule that was violated
        agent_name: Agent whose action was denied
        action_type: Type of action (e.g., "trade", "leverage")
    
    Example:
        track_hrm_denial("max_position_size", "Kenny", "trade")
    """
    increment_counter(
        "hrm_denials_total",
        labels={
            "rule_id": rule_id,
            "agent": agent_name,
            "action_type": action_type
        }
    )


def track_watchdog_event(event_type: str, agent_name: str, severity: str):
    """
    Track Watchdog monitoring event.
    
    Args:
        event_type: Type of event (e.g., "quarantine", "recovery", "heartbeat_failure")
        agent_name: Agent involved
        severity: Event severity ("info", "warning", "critical")
    
    Example:
        track_watchdog_event("quarantine", "Kenny", "critical")
    """
    increment_counter(
        "watchdog_events_total",
        labels={
            "event_type": event_type,
            "agent": agent_name,
            "severity": severity
        }
    )


def track_state_operation(operation: str, agent_name: str, latency_ms: float):
    """
    Track Mutable Core state operation.
    
    Args:
        operation: Operation type ("read", "write", "rollback")
        agent_name: Agent performing operation
        latency_ms: Operation latency in milliseconds
    
    Example:
        track_state_operation("write", "Kyle", 12.5)
    """
    record_latency(
        "state_operation_latency_ms",
        latency_ms,
        labels={
            "operation": operation,
            "agent": agent_name
        }
    )
    
    increment_counter(
        "state_operations_total",
        labels={
            "operation": operation,
            "agent": agent_name
        }
    )


class MetricsContext:
    """
    Context manager for tracking operation metrics with automatic error handling.
    
    Usage:
        async with MetricsContext(
            "kyle_signal_processing",
            agent_name="Kyle",
            trace_id=trace_id
        ) as ctx:
            # Do work
            result = await process_signal(signal)
            ctx.set_result(result)
        
        # Metrics automatically recorded on exit
    """
    
    def __init__(
        self,
        operation_name: str,
        agent_name: str,
        trace_id: Optional[str] = None,
        track_latency: bool = True,
        track_success: bool = True
    ):
        """
        Initialize metrics context.
        
        Args:
            operation_name: Name of operation for metrics
            agent_name: Agent performing operation
            trace_id: Optional trace ID for correlation
            track_latency: Record latency on exit
            track_success: Record success/failure counter
        """
        self.operation_name = operation_name
        self.agent_name = agent_name
        self.trace_id = trace_id or str(uuid.uuid4())
        self.track_latency = track_latency
        self.track_success = track_success
        
        self.start_time = None
        self.result = None
        self.error = None
    
    
    async def __aenter__(self):
        """Enter async context."""
        self.start_time = time.time()
        
        # Record trace
        record_trace(self.trace_id, self.agent_name)
        
        return self
    
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and record metrics."""
        duration_ms = (time.time() - self.start_time) * 1000
        
        # Track latency
        if self.track_latency:
            record_latency(
                f"{self.operation_name}_latency_ms",
                duration_ms,
                labels={"agent": self.agent_name}
            )
        
        # Track success/failure
        if self.track_success:
            if exc_type is None:
                increment_counter(
                    f"{self.operation_name}_success_total",
                    labels={"agent": self.agent_name}
                )
            else:
                increment_counter(
                    f"{self.operation_name}_failure_total",
                    labels={
                        "agent": self.agent_name,
                        "error_type": exc_type.__name__
                    }
                )
        
        # Don't suppress exceptions
        return False
    
    
    def set_result(self, result: Any):
        """Set operation result for potential tracking."""
        self.result = result


# Convenience decorators for common agent operations

def instrument_kyle_method(**kwargs):
    """Decorator for Kyle agent methods."""
    return instrument_agent_method(
        counter_metric="kyle_operations_total",
        **kwargs
    )


def instrument_joey_method(**kwargs):
    """Decorator for Joey agent methods."""
    return instrument_agent_method(
        counter_metric="joey_operations_total",
        **kwargs
    )


def instrument_kenny_method(**kwargs):
    """Decorator for Kenny agent methods."""
    return instrument_agent_method(
        counter_metric="kenny_operations_total",
        **kwargs
    )


def instrument_hrm_method(**kwargs):
    """Decorator for HRM agent methods."""
    return instrument_agent_method(
        counter_metric="hrm_operations_total",
        **kwargs
    )


def instrument_aletheia_method(**kwargs):
    """Decorator for Aletheia agent methods."""
    return instrument_agent_method(
        counter_metric="aletheia_operations_total",
        **kwargs
    )


if __name__ == "__main__":
    # Demo usage
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    class DemoAgent:
        def __init__(self, name: str):
            self.name = name
        
        @instrument_agent_method(
            latency_metric="demo_process_latency_ms",
            counter_metric="demo_process_total"
        )
        @with_trace_id
        async def process(self, data: Dict, trace_id: str):
            logger.info(f"{self.name} processing with trace {trace_id}")
            await asyncio.sleep(0.1)
            return {"status": "success", "trace_id": trace_id}
    
    async def demo():
        agent = DemoAgent("DemoAgent")
        
        # Process with auto-generated trace_id
        result1 = await agent.process({"value": 1})
        print(f"Result 1: {result1}")
        
        # Process with explicit trace_id
        result2 = await agent.process({"value": 2}, trace_id="custom-trace-123")
        print(f"Result 2: {result2}")
        
        # Show metrics
        from monitoring.metrics import get_all_metrics
        metrics = get_all_metrics()
        print(f"\nMetrics: {json.dumps(metrics, indent=2)}")
    
    asyncio.run(demo())
