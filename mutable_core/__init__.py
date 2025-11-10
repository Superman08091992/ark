"""
ARK Mutable Core - Unified State Management

Centralized persistent state for all agents with:
- Thread-safe operations
- SQLite-based atomic transactions
- Version history and rollback
- Aletheia-controlled writes for critical state
- Read access for all agents
"""

from mutable_core.state_manager import StateManager, STATE_MANAGER

__all__ = ['StateManager', 'STATE_MANAGER']
