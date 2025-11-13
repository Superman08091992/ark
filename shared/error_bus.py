"""
Error Escalation Bus

Centralized error reporting and escalation system with:
- Severity-based routing
- Error history tracking
- Correlation ID linking to message traces
- Retry tracking
- Automatic alerting for critical errors

Implements REQ_AGENT_02 (Error Escalation Path)

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


class ErrorSeverity(str, Enum):
    """Error severity levels for routing and alerting."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorEscalation:
    """
    Structured error reporting object.
    
    All agent errors MUST use this structure for:
    - Correlation with message traces
    - Severity-based routing
    - Error analytics and debugging
    """
    
    # Identity
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = ""
    
    # Source
    from_agent: str = ""
    
    # Error Details
    severity: ErrorSeverity = ErrorSeverity.ERROR
    error_code: str = ""
    error_message: str = ""
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    affected_trade_setup: Optional[str] = None
    
    # Actions
    retry_count: int = 0
    recoverable: bool = True
    suggested_action: Optional[str] = None
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_id": self.error_id,
            "correlation_id": self.correlation_id,
            "from_agent": self.from_agent,
            "severity": self.severity.value,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "exception_type": self.exception_type,
            "stack_trace": self.stack_trace,
            "context": self.context,
            "affected_trade_setup": self.affected_trade_setup,
            "retry_count": self.retry_count,
            "recoverable": self.recoverable,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class ErrorBus:
    """
    Singleton error escalation bus.
    
    Provides:
    - Register handlers for specific error severities
    - Escalate errors to appropriate handlers
    - Track error history by correlation ID
    - Automatic critical error alerting
    - Error rate monitoring
    """
    
    _instance: Optional['ErrorBus'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        """Enforce singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize error bus (only once due to singleton)."""
        if self._initialized:
            return
        
        self._error_handlers: Dict[ErrorSeverity, List[Callable]] = defaultdict(list)
        self._error_history: List[ErrorEscalation] = []
        self._max_history = 500
        self._error_counts: Dict[str, int] = defaultdict(int)
        
        # Register default critical error handler
        self.register_handler(ErrorSeverity.CRITICAL, self._default_critical_handler)
        
        logger.info("ErrorBus initialized")
        self._initialized = True
    
    async def escalate(self, error: ErrorEscalation) -> None:
        """
        Escalate error to registered handlers.
        
        Routes error based on severity to all registered handlers for that level.
        Also tracks error in history and updates statistics.
        
        Args:
            error: ErrorEscalation object describing the error
        """
        # Store in history
        self._error_history.append(error)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)
        
        # Update error counts
        self._error_counts[error.severity.value] += 1
        self._error_counts[f"{error.from_agent}:{error.error_code}"] += 1
        
        # Route to severity-specific handlers
        handlers = self._error_handlers.get(error.severity, [])
        
        if not handlers:
            logger.warning(
                f"No handlers registered for {error.severity} errors "
                f"(error_id: {error.error_id})"
            )
        
        # Execute handlers
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error)
                else:
                    # Run sync function in executor
                    await asyncio.get_event_loop().run_in_executor(None, handler, error)
            except Exception as e:
                logger.error(
                    f"Error handler failed for {error.error_id}: {e}",
                    exc_info=True
                )
        
        # Log the error
        log_level = {
            ErrorSeverity.DEBUG: logging.DEBUG,
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error.severity, logging.ERROR)
        
        logger.log(
            log_level,
            f"[{error.severity.value.upper()}] {error.from_agent}: "
            f"{error.error_code} - {error.error_message} "
            f"(error_id: {error.error_id}, correlation: {error.correlation_id})"
        )
    
    def register_handler(self, 
                        severity: ErrorSeverity,
                        handler: Callable[[ErrorEscalation], Awaitable[None]]) -> None:
        """
        Register handler for specific error severity.
        
        Args:
            severity: Error severity level to handle
            handler: Async function to handle errors of this severity
        """
        self._error_handlers[severity].append(handler)
        logger.info(f"Handler registered for {severity.value} errors")
    
    def unregister_handler(self, 
                          severity: ErrorSeverity,
                          handler: Callable) -> None:
        """
        Unregister error handler.
        
        Args:
            severity: Error severity level
            handler: Handler function to remove
        """
        if severity in self._error_handlers:
            try:
                self._error_handlers[severity].remove(handler)
                logger.info(f"Handler removed for {severity.value} errors")
            except ValueError:
                logger.warning(f"Handler not found for {severity.value} errors")
    
    def get_errors_by_correlation(self, correlation_id: str) -> List[ErrorEscalation]:
        """
        Retrieve all errors for a correlation ID.
        
        Args:
            correlation_id: Correlation ID to search for
            
        Returns:
            List of ErrorEscalations in chronological order
        """
        errors = [err for err in self._error_history if err.correlation_id == correlation_id]
        errors.sort(key=lambda x: x.timestamp)
        return errors
    
    def get_errors_by_agent(self, agent_name: str) -> List[ErrorEscalation]:
        """
        Retrieve all errors from specific agent.
        
        Args:
            agent_name: Agent name to filter by
            
        Returns:
            List of ErrorEscalations in chronological order
        """
        errors = [err for err in self._error_history if err.from_agent == agent_name]
        errors.sort(key=lambda x: x.timestamp)
        return errors
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorEscalation]:
        """
        Retrieve all errors of specific severity.
        
        Args:
            severity: Error severity to filter by
            
        Returns:
            List of ErrorEscalations in chronological order
        """
        errors = [err for err in self._error_history if err.severity == severity]
        errors.sort(key=lambda x: x.timestamp)
        return errors
    
    def get_unresolved_errors(self) -> List[ErrorEscalation]:
        """
        Retrieve all unresolved errors.
        
        Returns:
            List of unresolved ErrorEscalations
        """
        return [err for err in self._error_history if not err.resolved]
    
    def mark_resolved(self, error_id: str) -> bool:
        """
        Mark error as resolved.
        
        Args:
            error_id: ID of error to mark resolved
            
        Returns:
            True if error found and marked, False otherwise
        """
        for error in self._error_history:
            if error.error_id == error_id:
                error.resolved = True
                error.resolved_at = datetime.utcnow()
                logger.info(f"Error {error_id} marked as resolved")
                return True
        
        logger.warning(f"Error {error_id} not found")
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get error bus statistics.
        
        Returns:
            Dictionary with error statistics
        """
        total_errors = len(self._error_history)
        unresolved = len(self.get_unresolved_errors())
        
        severity_breakdown = {
            severity.value: len(self.get_errors_by_severity(severity))
            for severity in ErrorSeverity
        }
        
        return {
            "total_errors": total_errors,
            "unresolved_errors": unresolved,
            "resolved_errors": total_errors - unresolved,
            "severity_breakdown": severity_breakdown,
            "error_counts": dict(self._error_counts),
            "max_history_size": self._max_history,
            "handlers_registered": {
                severity.value: len(handlers)
                for severity, handlers in self._error_handlers.items()
            }
        }
    
    def clear_history(self) -> None:
        """Clear error history (for testing or memory management)."""
        self._error_history.clear()
        self._error_counts.clear()
        logger.info("Error history cleared")
    
    async def _default_critical_handler(self, error: ErrorEscalation) -> None:
        """Default handler for critical errors - logs and alerts."""
        logger.critical(
            f"🚨 CRITICAL ERROR from {error.from_agent}: {error.error_message}\n"
            f"   Error ID: {error.error_id}\n"
            f"   Correlation: {error.correlation_id}\n"
            f"   Code: {error.error_code}\n"
            f"   Recoverable: {error.recoverable}\n"
            f"   Suggested Action: {error.suggested_action or 'None'}"
        )
        
        # In production, this would:
        # - Send PagerDuty alert
        # - Post to #alerts Slack channel
        # - Email on-call engineer
        # - Trigger incident response workflow


# Global singleton instance
error_bus = ErrorBus()


class ErrorHandlerMixin:
    """
    Mixin for agents to simplify error reporting.
    
    Provides convenience methods for common error scenarios.
    """
    
    async def report_error(self,
                          error_message: str,
                          severity: ErrorSeverity = ErrorSeverity.ERROR,
                          error_code: str = "UNKNOWN_ERROR",
                          correlation_id: str = "",
                          context: Optional[Dict] = None,
                          exception: Optional[Exception] = None,
                          recoverable: bool = True,
                          suggested_action: Optional[str] = None) -> str:
        """
        Report error to error bus.
        
        Args:
            error_message: Human-readable error description
            severity: Error severity level
            error_code: Machine-readable error code
            correlation_id: Correlation ID from message trace
            context: Additional context dictionary
            exception: Python exception object (if applicable)
            recoverable: Whether error is recoverable
            suggested_action: Recommended remediation
            
        Returns:
            error_id of reported error
        """
        import traceback
        
        error = ErrorEscalation(
            correlation_id=correlation_id,
            from_agent=getattr(self, 'name', 'unknown'),
            severity=severity,
            error_code=error_code,
            error_message=error_message,
            exception_type=type(exception).__name__ if exception else None,
            stack_trace=traceback.format_exc() if exception else None,
            context=context or {},
            recoverable=recoverable,
            suggested_action=suggested_action
        )
        
        await error_bus.escalate(error)
        return error.error_id
    
    async def report_warning(self, message: str, **kwargs) -> str:
        """Convenience method to report WARNING."""
        return await self.report_error(message, ErrorSeverity.WARNING, **kwargs)
    
    async def report_critical(self, message: str, **kwargs) -> str:
        """Convenience method to report CRITICAL error."""
        return await self.report_error(message, ErrorSeverity.CRITICAL, **kwargs)


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    # Example custom error handler
    async def slack_alert_handler(error: ErrorEscalation):
        print(f"📢 SLACK ALERT: {error.severity.value.upper()} from {error.from_agent}")
        print(f"   Message: {error.error_message}")
    
    async def demo():
        # Register custom handlers
        error_bus.register_handler(ErrorSeverity.ERROR, slack_alert_handler)
        error_bus.register_handler(ErrorSeverity.CRITICAL, slack_alert_handler)
        
        print("\n🔴 Error Bus Demo")
        print(f"Stats: {error_bus.get_stats()}")
        
        # Simulate various errors
        print("\n⚠️  Reporting WARNING")
        await error_bus.escalate(ErrorEscalation(
            correlation_id="test-123",
            from_agent="kyle",
            severity=ErrorSeverity.WARNING,
            error_code="API_RATE_LIMIT",
            error_message="Approaching API rate limit (80% used)",
            recoverable=True,
            suggested_action="Throttle API requests"
        ))
        
        await asyncio.sleep(0.1)
        
        print("\n🔴 Reporting ERROR")
        await error_bus.escalate(ErrorEscalation(
            correlation_id="test-123",
            from_agent="joey",
            severity=ErrorSeverity.ERROR,
            error_code="DATA_FETCH_FAILED",
            error_message="Failed to fetch market data for TSLA",
            exception_type="TimeoutError",
            recoverable=True,
            retry_count=2,
            suggested_action="Retry with exponential backoff"
        ))
        
        await asyncio.sleep(0.1)
        
        print("\n🚨 Reporting CRITICAL")
        await error_bus.escalate(ErrorEscalation(
            correlation_id="test-123",
            from_agent="hrm",
            severity=ErrorSeverity.CRITICAL,
            error_code="MEMORY_CORRUPTION",
            error_message="Memory state corrupted - cannot continue",
            recoverable=False,
            suggested_action="Emergency shutdown and restore from snapshot"
        ))
        
        await asyncio.sleep(0.1)
        
        print("\n📊 Error Statistics:")
        stats = error_bus.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("\n📜 Errors by Correlation:")
        errors = error_bus.get_errors_by_correlation("test-123")
        for err in errors:
            print(f"   [{err.severity.value}] {err.from_agent}: {err.error_code}")
    
    asyncio.run(demo())
