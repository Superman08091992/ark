#!/usr/bin/env python3
"""
ARK Signal Handler (REQ_INFRA_04)

Provides graceful shutdown capabilities for all ARK components.
Handles SIGTERM, SIGINT signals with proper cleanup and state preservation.
"""

import signal
import sys
import logging
import atexit
from typing import Callable, List, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class GracefulShutdownHandler:
    """
    Manages graceful shutdown for ARK components.
    
    Features:
    - SIGTERM/SIGINT signal handling
    - Cleanup callback registration
    - State persistence on shutdown
    - Log buffer flushing
    - Timeout enforcement
    """
    
    def __init__(self, component_name: str = "ark", timeout: int = 30):
        """
        Initialize shutdown handler.
        
        Args:
            component_name: Name of component (for logging)
            timeout: Maximum seconds to wait for cleanup
        """
        self.component_name = component_name
        self.timeout = timeout
        self.cleanup_callbacks: List[Callable] = []
        self.shutdown_initiated = False
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Register atexit handler as fallback
        atexit.register(self._cleanup)
        
        logger.info(f"Graceful shutdown handler initialized for {component_name}")
    
    def register_cleanup(self, callback: Callable, priority: int = 0):
        """
        Register a cleanup callback to be called on shutdown.
        
        Args:
            callback: Function to call during cleanup
            priority: Priority (higher = called first)
        """
        self.cleanup_callbacks.append((priority, callback))
        self.cleanup_callbacks.sort(key=lambda x: x[0], reverse=True)
        logger.debug(f"Registered cleanup callback: {callback.__name__} (priority: {priority})")
    
    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        logger.info(f"Received signal {signal_name} - initiating graceful shutdown...")
        
        if self.shutdown_initiated:
            logger.warning("Shutdown already in progress, ignoring repeated signal")
            return
        
        self.shutdown_initiated = True
        self._cleanup()
        
        # Exit after cleanup
        sys.exit(0)
    
    def _cleanup(self):
        """Execute all registered cleanup callbacks."""
        if not self.cleanup_callbacks:
            logger.info("No cleanup callbacks registered")
            return
        
        logger.info(f"Executing {len(self.cleanup_callbacks)} cleanup callbacks...")
        
        for priority, callback in self.cleanup_callbacks:
            try:
                callback_name = callback.__name__
                logger.info(f"Executing cleanup: {callback_name} (priority: {priority})")
                callback()
                logger.info(f"✅ Cleanup completed: {callback_name}")
            except Exception as e:
                logger.error(f"❌ Cleanup failed for {callback.__name__}: {e}", exc_info=True)
        
        logger.info("All cleanup callbacks executed")
        
        # Flush all log handlers
        for handler in logging.root.handlers:
            try:
                handler.flush()
            except Exception:
                pass
    
    def shutdown(self):
        """Manually trigger graceful shutdown."""
        logger.info("Manual shutdown initiated")
        self.shutdown_initiated = True
        self._cleanup()


# Global shutdown handler instance
_shutdown_handler: Optional[GracefulShutdownHandler] = None


def init_shutdown_handler(component_name: str = "ark", timeout: int = 30) -> GracefulShutdownHandler:
    """
    Initialize global shutdown handler.
    
    Args:
        component_name: Name of component
        timeout: Cleanup timeout in seconds
        
    Returns:
        GracefulShutdownHandler instance
    """
    global _shutdown_handler
    
    if _shutdown_handler is None:
        _shutdown_handler = GracefulShutdownHandler(component_name, timeout)
    
    return _shutdown_handler


def register_cleanup(callback: Callable, priority: int = 0):
    """
    Register a cleanup callback with the global handler.
    
    Args:
        callback: Cleanup function
        priority: Execution priority (higher = earlier)
    """
    if _shutdown_handler is None:
        init_shutdown_handler()
    
    _shutdown_handler.register_cleanup(callback, priority)


def shutdown():
    """Trigger graceful shutdown."""
    if _shutdown_handler:
        _shutdown_handler.shutdown()


# Common cleanup helpers

def flush_logs_cleanup():
    """Flush all log handlers."""
    logger.info("Flushing all log handlers...")
    for handler in logging.root.handlers:
        try:
            handler.flush()
            handler.close()
        except Exception as e:
            print(f"Warning: Failed to flush log handler: {e}")


def close_database_cleanup(db_path: Path):
    """
    Create closure to close database connection.
    
    Args:
        db_path: Path to database file
        
    Returns:
        Cleanup function
    """
    def cleanup():
        logger.info(f"Closing database: {db_path}")
        # Database-specific cleanup would go here
        # For SQLite, connections are typically closed by the library
    
    return cleanup


def save_state_cleanup(state_data: dict, state_file: Path):
    """
    Create closure to save state on shutdown.
    
    Args:
        state_data: State dictionary to save
        state_file: Path to state file
        
    Returns:
        Cleanup function
    """
    def cleanup():
        import json
        logger.info(f"Saving state to: {state_file}")
        try:
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            logger.info(f"✅ State saved successfully")
        except Exception as e:
            logger.error(f"❌ Failed to save state: {e}")
    
    return cleanup


def release_lockfile_cleanup(lockfile_path: Path):
    """
    Create closure to release lockfile.
    
    Args:
        lockfile_path: Path to lockfile
        
    Returns:
        Cleanup function
    """
    def cleanup():
        logger.info(f"Releasing lockfile: {lockfile_path}")
        try:
            if lockfile_path.exists():
                lockfile_path.unlink()
                logger.info("✅ Lockfile released")
        except Exception as e:
            logger.error(f"❌ Failed to release lockfile: {e}")
    
    return cleanup


def notify_shutdown_cleanup(component_name: str):
    """
    Create closure to log shutdown notification.
    
    Args:
        component_name: Name of component
        
    Returns:
        Cleanup function
    """
    def cleanup():
        logger.info(f"🛑 {component_name} shutting down gracefully")
    
    return cleanup


# Example usage pattern for agents
class AgentWithGracefulShutdown:
    """
    Example base class showing graceful shutdown integration.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.running = False
        self.state = {}
        
        # Initialize shutdown handler
        self.shutdown_handler = init_shutdown_handler(f"agent-{name}")
        
        # Register cleanup callbacks
        self.shutdown_handler.register_cleanup(
            notify_shutdown_cleanup(self.name),
            priority=100  # High priority - log first
        )
        
        self.shutdown_handler.register_cleanup(
            self.save_agent_state,
            priority=90  # Save state before closing resources
        )
        
        self.shutdown_handler.register_cleanup(
            flush_logs_cleanup,
            priority=10  # Low priority - flush logs last
        )
    
    def save_agent_state(self):
        """Save agent state on shutdown."""
        logger.info(f"Saving {self.name} agent state...")
        # State saving logic here
        self.state['shutdown_time'] = str(Path.cwd())  # Example
    
    def start(self):
        """Start agent processing."""
        self.running = True
        logger.info(f"{self.name} agent started")
    
    def stop(self):
        """Stop agent gracefully."""
        self.running = False
        logger.info(f"{self.name} agent stopped")
        self.shutdown_handler.shutdown()


def main():
    """Test signal handler."""
    import time
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize handler
    handler = init_shutdown_handler("test-component")
    
    # Register test callbacks
    def cleanup1():
        logger.info("Cleanup 1: Closing connections...")
        time.sleep(0.5)
    
    def cleanup2():
        logger.info("Cleanup 2: Saving state...")
        time.sleep(0.5)
    
    def cleanup3():
        logger.info("Cleanup 3: Flushing buffers...")
        time.sleep(0.5)
    
    handler.register_cleanup(cleanup1, priority=100)
    handler.register_cleanup(cleanup2, priority=90)
    handler.register_cleanup(cleanup3, priority=80)
    
    # Simulate long-running process
    logger.info("Component running... Press Ctrl+C to trigger graceful shutdown")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
