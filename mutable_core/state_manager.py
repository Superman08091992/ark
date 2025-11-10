"""
ARK Mutable Core - State Manager

Unified state persistence layer with:
- SQLite for atomicity and durability
- Thread-safe operations with RLock
- Version history for rollback capability
- Agent-scoped state isolation
- Memory index tracking
- System configuration management
- Session logging

Schema:
- agents_state: runtime variables, health, temporary state
- memory_index: embedding references, summaries, pattern cache
- system_config: active parameters, API keys, limits
- session_log: last N actions with timestamps
- state_history: versioned history for rollback
"""

import json
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Database path (configurable via environment)
DB_PATH = os.environ.get("ARK_STATE_DB", "/app/data/ark_mutable_core.db")

# Global lock for thread safety
LOCK = threading.RLock()


@dataclass
class StateSnapshot:
    """Snapshot of state at a point in time"""
    agent: str
    key: str
    value: Any
    timestamp: float
    version: int


# =========================
# Database Initialization
# =========================

INIT_SQL = """
-- Main state table (current values)
CREATE TABLE IF NOT EXISTS agents_state (
    agent TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    value_type TEXT,  -- 'str', 'int', 'float', 'bool', 'dict', 'list'
    timestamp REAL DEFAULT (strftime('%s','now')),
    version INTEGER DEFAULT 1,
    PRIMARY KEY (agent, key)
);

CREATE INDEX IF NOT EXISTS idx_agents_state_agent ON agents_state(agent);
CREATE INDEX IF NOT EXISTS idx_agents_state_timestamp ON agents_state(timestamp);

-- State history for rollback
CREATE TABLE IF NOT EXISTS state_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    value_type TEXT,
    timestamp REAL DEFAULT (strftime('%s','now')),
    version INTEGER,
    operation TEXT  -- 'create', 'update', 'delete'
);

CREATE INDEX IF NOT EXISTS idx_state_history_agent_key ON state_history(agent, key);
CREATE INDEX IF NOT EXISTS idx_state_history_timestamp ON state_history(timestamp);

-- Memory index for embeddings and summaries
CREATE TABLE IF NOT EXISTS memory_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,
    memory_type TEXT NOT NULL,  -- 'embedding', 'summary', 'pattern'
    content TEXT,
    metadata TEXT,  -- JSON
    timestamp REAL DEFAULT (strftime('%s','now')),
    expires_at REAL  -- NULL for permanent
);

CREATE INDEX IF NOT EXISTS idx_memory_index_agent ON memory_index(agent);
CREATE INDEX IF NOT EXISTS idx_memory_index_type ON memory_index(memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_index_expires ON memory_index(expires_at);

-- System configuration
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    value_type TEXT,
    description TEXT,
    updater TEXT,  -- Which agent/user updated this
    timestamp REAL DEFAULT (strftime('%s','now'))
);

-- Session log for recent actions
CREATE TABLE IF NOT EXISTS session_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,
    action_type TEXT NOT NULL,
    action_data TEXT,  -- JSON
    result TEXT,  -- 'success', 'failure', 'partial'
    graveyard_approved BOOLEAN,
    timestamp REAL DEFAULT (strftime('%s','now'))
);

CREATE INDEX IF NOT EXISTS idx_session_log_agent ON session_log(agent);
CREATE INDEX IF NOT EXISTS idx_session_log_timestamp ON session_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_session_log_result ON session_log(result);

-- Aletheia truth map (privileged writes)
CREATE TABLE IF NOT EXISTS truth_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    truth_value TEXT,
    confidence REAL,  -- 0.0 to 1.0
    sources TEXT,  -- JSON array of source agents
    timestamp REAL DEFAULT (strftime('%s','now')),
    updated_by TEXT  -- Should always be 'Aletheia'
);

CREATE INDEX IF NOT EXISTS idx_truth_map_key ON truth_map(key);
"""


def _ensure_db():
    """Initialize database with schema"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(INIT_SQL)
        conn.commit()
    
    logger.info(f"Mutable Core database initialized at {DB_PATH}")


# Initialize on import
_ensure_db()


@contextmanager
def db_conn():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Access columns by name
    try:
        yield conn
    finally:
        conn.close()


# =========================
# Core StateManager
# =========================

class StateManager:
    """
    Thread-safe unified state manager for ARK system.
    
    Features:
    - Agent-scoped state isolation
    - Atomic transactions via SQLite
    - Version history with rollback
    - Memory index for embeddings/summaries
    - System configuration management
    - Session action logging
    - Aletheia-controlled truth map
    
    Usage:
        sm = StateManager()
        sm.update_state("Kyle", "signal_count", 42)
        state = sm.get_state("Kyle", "signal_count")
    """
    
    def __init__(self):
        self.lock = LOCK
        self.cache: Dict[str, Dict[str, Any]] = {}  # In-memory cache
        logger.info("StateManager initialized")
    
    # =========================
    # Type Handling
    # =========================
    
    def _serialize(self, value: Any) -> Tuple[str, str]:
        """Serialize value to JSON string and determine type"""
        value_type = type(value).__name__
        
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False), value_type
        elif isinstance(value, bool):
            return json.dumps(value), 'bool'
        elif isinstance(value, int):
            return str(value), 'int'
        elif isinstance(value, float):
            return str(value), 'float'
        else:
            return str(value), 'str'
    
    def _deserialize(self, value_str: str, value_type: str) -> Any:
        """Deserialize JSON string to Python object"""
        if not value_str:
            return None
        
        try:
            if value_type in ('dict', 'list', 'bool'):
                return json.loads(value_str)
            elif value_type == 'int':
                return int(value_str)
            elif value_type == 'float':
                return float(value_str)
            else:
                return value_str
        except Exception as e:
            logger.error(f"Deserialization error for type {value_type}: {e}")
            return value_str
    
    # =========================
    # Agent State Management
    # =========================
    
    def get_state(self, agent: str, key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get agent state.
        
        Args:
            agent: Agent name
            key: Optional specific key (if None, returns all agent state)
        
        Returns:
            Dict with state values
        """
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            
            if key:
                cursor.execute(
                    "SELECT value, value_type FROM agents_state WHERE agent=? AND key=?",
                    (agent, key)
                )
                row = cursor.fetchone()
                
                if row:
                    value = self._deserialize(row['value'], row['value_type'])
                    return {key: value}
                else:
                    return {}
            else:
                cursor.execute(
                    "SELECT key, value, value_type FROM agents_state WHERE agent=?",
                    (agent,)
                )
                rows = cursor.fetchall()
                
                return {
                    row['key']: self._deserialize(row['value'], row['value_type'])
                    for row in rows
                }
    
    def update_state(self, agent: str, key: str, value: Any, requester: Optional[str] = None):
        """
        Update agent state with versioning.
        
        Args:
            agent: Agent name
            key: State key
            value: State value (any JSON-serializable type)
            requester: Optional requester name (for access control)
        
        Note:
            Automatically records in history for rollback capability
        """
        value_str, value_type = self._serialize(value)
        
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            
            # Get current version
            cursor.execute(
                "SELECT version FROM agents_state WHERE agent=? AND key=?",
                (agent, key)
            )
            row = cursor.fetchone()
            current_version = row['version'] if row else 0
            new_version = current_version + 1
            
            # Archive current value to history
            if row:
                cursor.execute(
                    "INSERT INTO state_history (agent, key, value, value_type, version, operation) "
                    "SELECT agent, key, value, value_type, version, 'update' "
                    "FROM agents_state WHERE agent=? AND key=?",
                    (agent, key)
                )
            
            # Update current state
            cursor.execute(
                "INSERT OR REPLACE INTO agents_state (agent, key, value, value_type, timestamp, version) "
                "VALUES (?, ?, ?, ?, strftime('%s','now'), ?)",
                (agent, key, value_str, value_type, new_version)
            )
            
            conn.commit()
        
        # Update cache
        self.cache.setdefault(agent, {})[key] = value
        
        logger.debug(f"State updated: {agent}.{key} = {value} (v{new_version})")
    
    def delete_state(self, agent: str, key: str):
        """Delete a state key"""
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            
            # Archive to history before deleting
            cursor.execute(
                "INSERT INTO state_history (agent, key, value, value_type, version, operation) "
                "SELECT agent, key, value, value_type, version, 'delete' "
                "FROM agents_state WHERE agent=? AND key=?",
                (agent, key)
            )
            
            # Delete
            cursor.execute("DELETE FROM agents_state WHERE agent=? AND key=?", (agent, key))
            conn.commit()
        
        # Update cache
        if agent in self.cache and key in self.cache[agent]:
            del self.cache[agent][key]
        
        logger.debug(f"State deleted: {agent}.{key}")
    
    def all_state(self) -> Dict[str, Dict[str, Any]]:
        """Get all state for all agents"""
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT agent, key, value, value_type FROM agents_state")
            rows = cursor.fetchall()
            
            result: Dict[str, Dict[str, Any]] = {}
            for row in rows:
                agent = row['agent']
                key = row['key']
                value = self._deserialize(row['value'], row['value_type'])
                result.setdefault(agent, {})[key] = value
            
            return result
    
    # =========================
    # Version Control
    # =========================
    
    def commit(self):
        """
        No-op placeholder for transactional persistence.
        SQLite autocommit handles persistence.
        Kept for interface compatibility.
        """
        pass
    
    def rollback(self, agent: str, key: str, steps: int = 1) -> Optional[Any]:
        """
        Rollback state to a previous version.
        
        Args:
            agent: Agent name
            key: State key
            steps: Number of versions to go back (1 = previous version)
        
        Returns:
            Restored value, or None if not found
        """
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            
            # Get historical value
            cursor.execute(
                "SELECT value, value_type, version FROM state_history "
                "WHERE agent=? AND key=? "
                "ORDER BY id DESC LIMIT 1 OFFSET ?",
                (agent, key, steps - 1)
            )
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"No history found for {agent}.{key} at -{steps} versions")
                return None
            
            previous_value = row['value']
            previous_type = row['value_type']
            previous_version = row['version']
            
            # Restore to current state
            cursor.execute(
                "INSERT OR REPLACE INTO agents_state (agent, key, value, value_type, timestamp, version) "
                "VALUES (?, ?, ?, ?, strftime('%s','now'), ?)",
                (agent, key, previous_value, previous_type, previous_version)
            )
            
            conn.commit()
            
            restored = self._deserialize(previous_value, previous_type)
            self.cache.setdefault(agent, {})[key] = restored
            
            logger.info(f"Rolled back {agent}.{key} to version {previous_version}")
            
            return restored
    
    def get_history(self, agent: str, key: str, limit: int = 10) -> List[StateSnapshot]:
        """
        Get version history for a state key.
        
        Args:
            agent: Agent name
            key: State key
            limit: Maximum number of versions to retrieve
        
        Returns:
            List of StateSnapshot objects
        """
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value, value_type, timestamp, version FROM state_history "
                "WHERE agent=? AND key=? "
                "ORDER BY id DESC LIMIT ?",
                (agent, key, limit)
            )
            rows = cursor.fetchall()
            
            return [
                StateSnapshot(
                    agent=agent,
                    key=key,
                    value=self._deserialize(row['value'], row['value_type']),
                    timestamp=row['timestamp'],
                    version=row['version']
                )
                for row in rows
            ]
    
    # =========================
    # Memory Index
    # =========================
    
    def add_memory(self, agent: str, memory_type: str, content: str, 
                   metadata: Optional[Dict] = None, ttl: Optional[int] = None):
        """
        Add memory to index (embeddings, summaries, patterns).
        
        Args:
            agent: Agent name
            memory_type: 'embedding', 'summary', 'pattern', etc.
            content: Memory content
            metadata: Optional metadata dict
            ttl: Optional time-to-live in seconds (None = permanent)
        """
        metadata_json = json.dumps(metadata) if metadata else None
        expires_at = time.time() + ttl if ttl else None
        
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO memory_index (agent, memory_type, content, metadata, expires_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (agent, memory_type, content, metadata_json, expires_at)
            )
            conn.commit()
        
        logger.debug(f"Memory added: {agent}.{memory_type}")
    
    def get_memories(self, agent: str, memory_type: Optional[str] = None, 
                     limit: int = 100) -> List[Dict]:
        """
        Get memories from index.
        
        Args:
            agent: Agent name
            memory_type: Optional filter by type
            limit: Maximum results
        
        Returns:
            List of memory dicts
        """
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            
            # Clean up expired memories first
            cursor.execute(
                "DELETE FROM memory_index WHERE expires_at IS NOT NULL AND expires_at < ?",
                (time.time(),)
            )
            
            if memory_type:
                cursor.execute(
                    "SELECT id, memory_type, content, metadata, timestamp "
                    "FROM memory_index WHERE agent=? AND memory_type=? "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (agent, memory_type, limit)
                )
            else:
                cursor.execute(
                    "SELECT id, memory_type, content, metadata, timestamp "
                    "FROM memory_index WHERE agent=? "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (agent, limit)
                )
            
            rows = cursor.fetchall()
            
            return [
                {
                    'id': row['id'],
                    'memory_type': row['memory_type'],
                    'content': row['content'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else None,
                    'timestamp': row['timestamp']
                }
                for row in rows
            ]
    
    # =========================
    # System Configuration
    # =========================
    
    def get_config(self, key: Optional[str] = None) -> Dict[str, Any]:
        """Get system configuration"""
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            
            if key:
                cursor.execute(
                    "SELECT value, value_type FROM system_config WHERE key=?",
                    (key,)
                )
                row = cursor.fetchone()
                
                if row:
                    value = self._deserialize(row['value'], row['value_type'])
                    return {key: value}
                else:
                    return {}
            else:
                cursor.execute("SELECT key, value, value_type FROM system_config")
                rows = cursor.fetchall()
                
                return {
                    row['key']: self._deserialize(row['value'], row['value_type'])
                    for row in rows
                }
    
    def set_config(self, key: str, value: Any, description: str = "", updater: str = "System"):
        """Set system configuration"""
        value_str, value_type = self._serialize(value)
        
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO system_config (key, value, value_type, description, updater, timestamp) "
                "VALUES (?, ?, ?, ?, ?, strftime('%s','now'))",
                (key, value_str, value_type, description, updater)
            )
            conn.commit()
        
        logger.info(f"Config updated: {key} = {value} (by {updater})")
    
    # =========================
    # Session Logging
    # =========================
    
    def log_action(self, agent: str, action_type: str, action_data: Dict, 
                   result: str, graveyard_approved: bool = True):
        """
        Log agent action to session log.
        
        Args:
            agent: Agent name
            action_type: Type of action
            action_data: Action details (dict)
            result: 'success', 'failure', 'partial'
            graveyard_approved: Whether Graveyard approved the action
        """
        action_json = json.dumps(action_data)
        
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO session_log (agent, action_type, action_data, result, graveyard_approved) "
                "VALUES (?, ?, ?, ?, ?)",
                (agent, action_type, action_json, result, 1 if graveyard_approved else 0)
            )
            conn.commit()
        
        logger.debug(f"Action logged: {agent}.{action_type} -> {result}")
    
    def get_session_log(self, agent: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get recent session actions"""
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            
            if agent:
                cursor.execute(
                    "SELECT id, agent, action_type, action_data, result, graveyard_approved, timestamp "
                    "FROM session_log WHERE agent=? ORDER BY timestamp DESC LIMIT ?",
                    (agent, limit)
                )
            else:
                cursor.execute(
                    "SELECT id, agent, action_type, action_data, result, graveyard_approved, timestamp "
                    "FROM session_log ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
            
            rows = cursor.fetchall()
            
            return [
                {
                    'id': row['id'],
                    'agent': row['agent'],
                    'action_type': row['action_type'],
                    'action_data': json.loads(row['action_data']) if row['action_data'] else {},
                    'result': row['result'],
                    'graveyard_approved': bool(row['graveyard_approved']),
                    'timestamp': row['timestamp']
                }
                for row in rows
            ]
    
    # =========================
    # Aletheia Truth Map
    # =========================
    
    def set_truth(self, key: str, truth_value: Any, confidence: float, 
                  sources: List[str], updater: str = "Aletheia"):
        """
        Set truth value (Aletheia-controlled).
        
        Args:
            key: Truth key
            truth_value: The truth value
            confidence: Confidence score (0.0 to 1.0)
            sources: List of source agent names
            updater: Updater name (should be 'Aletheia')
        
        Note:
            In production, this should verify updater is Aletheia
        """
        value_str = json.dumps(truth_value)
        sources_json = json.dumps(sources)
        
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO truth_map (key, truth_value, confidence, sources, timestamp, updated_by) "
                "VALUES (?, ?, ?, ?, strftime('%s','now'), ?)",
                (key, value_str, confidence, sources_json, updater)
            )
            conn.commit()
        
        logger.info(f"Truth set: {key} = {truth_value} (confidence: {confidence:.2f}, by {updater})")
    
    def get_truth(self, key: Optional[str] = None) -> Dict[str, Any]:
        """Get truth values"""
        with self.lock, db_conn() as conn:
            cursor = conn.cursor()
            
            if key:
                cursor.execute(
                    "SELECT truth_value, confidence, sources, timestamp, updated_by "
                    "FROM truth_map WHERE key=?",
                    (key,)
                )
                row = cursor.fetchone()
                
                if row:
                    return {
                        key: {
                            'value': json.loads(row['truth_value']),
                            'confidence': row['confidence'],
                            'sources': json.loads(row['sources']),
                            'timestamp': row['timestamp'],
                            'updated_by': row['updated_by']
                        }
                    }
                else:
                    return {}
            else:
                cursor.execute(
                    "SELECT key, truth_value, confidence, sources, timestamp, updated_by FROM truth_map"
                )
                rows = cursor.fetchall()
                
                return {
                    row['key']: {
                        'value': json.loads(row['truth_value']),
                        'confidence': row['confidence'],
                        'sources': json.loads(row['sources']),
                        'timestamp': row['timestamp'],
                        'updated_by': row['updated_by']
                    }
                    for row in rows
                }


# Global singleton instance
STATE_MANAGER = StateManager()


# =========================
# CLI for Testing
# =========================

if __name__ == "__main__":
    print("=" * 60)
    print("ARK MUTABLE CORE - State Manager Test")
    print("=" * 60)
    print()
    
    sm = STATE_MANAGER
    
    # Test basic state
    print("Test 1: Basic State Operations")
    sm.update_state("Kyle", "signal_count", 42)
    sm.update_state("Kyle", "last_scan", datetime.now().isoformat())
    result = sm.get_state("Kyle")
    print(f"  Kyle state: {result}")
    assert result['signal_count'] == 42
    print("  ✅ Basic state OK\n")
    
    # Test rollback
    print("Test 2: Rollback")
    sm.update_state("Kenny", "last_action", {"type": "BUY", "symbol": "SPY"})
    sm.update_state("Kenny", "last_action", {"type": "SELL", "symbol": "SPY"})
    sm.update_state("Kenny", "last_action", {"type": "HOLD", "symbol": "SPY"})
    restored = sm.rollback("Kenny", "last_action", steps=2)
    print(f"  Restored: {restored}")
    assert restored['type'] == "BUY"
    print("  ✅ Rollback OK\n")
    
    # Test memory index
    print("Test 3: Memory Index")
    sm.add_memory("Joey", "pattern", "Double bottom detected", 
                  metadata={"confidence": 0.85}, ttl=3600)
    memories = sm.get_memories("Joey", "pattern")
    print(f"  Joey memories: {len(memories)} found")
    assert len(memories) > 0
    print("  ✅ Memory index OK\n")
    
    # Test config
    print("Test 4: System Config")
    sm.set_config("max_leverage", 2.0, "Maximum leverage allowed", "Admin")
    config = sm.get_config("max_leverage")
    print(f"  Config: {config}")
    assert config['max_leverage'] == 2.0
    print("  ✅ Config OK\n")
    
    # Test session log
    print("Test 5: Session Log")
    sm.log_action("Kenny", "trade", {"symbol": "SPY", "action": "BUY"}, "success", True)
    log = sm.get_session_log("Kenny", limit=5)
    print(f"  Session log: {len(log)} entries")
    assert len(log) > 0
    print("  ✅ Session log OK\n")
    
    # Test truth map
    print("Test 6: Aletheia Truth Map")
    sm.set_truth("market_sentiment", "bullish", 0.75, ["Kyle", "Joey"], "Aletheia")
    truth = sm.get_truth("market_sentiment")
    print(f"  Truth: {truth}")
    assert truth['market_sentiment']['value'] == "bullish"
    print("  ✅ Truth map OK\n")
    
    # Test all state
    print("Test 7: All State")
    all_state = sm.all_state()
    print(f"  Total agents with state: {len(all_state)}")
    for agent, state in all_state.items():
        print(f"    {agent}: {len(state)} keys")
    print("  ✅ All state OK\n")
    
    print("=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)
