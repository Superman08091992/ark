#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Synchronization Layer

Provides persistent logging and real-time updates for reasoning traces:
- SQLite/DuckDB for persistent reasoning logs
- Redis pub/sub for live reasoning updates
- Async interfaces for non-blocking operations

This enables the intelligent-backend.cjs to:
1. Query historical reasoning patterns
2. Subscribe to live reasoning traces
3. Analyze agent performance over time
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    try:
        import aioredis
        REDIS_AVAILABLE = True
    except (ImportError, TypeError):
        REDIS_AVAILABLE = False
        logging.warning("Redis not available - pub/sub features disabled")

from reasoning.reasoning_engine import ReasoningResult, StageResult

logger = logging.getLogger(__name__)


class ReasoningMemoryDB:
    """SQLite-based persistent storage for reasoning traces"""
    
    def __init__(self, db_path: str = "reasoning_logs.db"):
        """
        Initialize reasoning memory database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
        logger.info(f"Initialized ReasoningMemoryDB at {db_path}")
    
    def _init_database(self):
        """Create database schema if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main reasoning sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reasoning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                agent_name TEXT NOT NULL,
                query TEXT NOT NULL,
                final_output TEXT,
                overall_confidence REAL,
                total_duration_ms REAL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Reasoning stages table (one-to-many with sessions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reasoning_stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                stage_name TEXT NOT NULL,
                stage_order INTEGER NOT NULL,
                input_data TEXT,
                output_data TEXT,
                confidence REAL,
                duration_ms REAL,
                traces TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES reasoning_sessions(session_id)
            )
        """)
        
        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_agent 
            ON reasoning_sessions(agent_name, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stages_session 
            ON reasoning_stages(session_id, stage_order)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Database schema initialized")
    
    def log_reasoning(self, result: ReasoningResult) -> str:
        """
        Log a complete reasoning result
        
        Args:
            result: ReasoningResult to log
            
        Returns:
            Session ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Generate session ID
            session_id = f"{result.agent_name}_{result.timestamp}_{id(result)}"
            
            # Insert main session
            cursor.execute("""
                INSERT INTO reasoning_sessions 
                (session_id, agent_name, query, final_output, overall_confidence, 
                 total_duration_ms, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                result.agent_name,
                result.query,
                json.dumps(result.final_output),
                result.overall_confidence,
                result.total_duration_ms,
                result.timestamp,
                json.dumps(result.metadata)
            ))
            
            # Insert stages
            for i, stage in enumerate(result.stages):
                cursor.execute("""
                    INSERT INTO reasoning_stages
                    (session_id, stage_name, stage_order, input_data, output_data,
                     confidence, duration_ms, traces, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    stage.stage.value,
                    i + 1,
                    json.dumps(stage.input_data) if stage.input_data else None,
                    json.dumps(stage.output_data) if stage.output_data else None,
                    stage.confidence,
                    stage.duration_ms,
                    json.dumps(stage.traces),
                    json.dumps(stage.metadata)
                ))
            
            conn.commit()
            logger.info(f"Logged reasoning session: {session_id}")
            return session_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to log reasoning: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a reasoning session by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get main session
            cursor.execute("""
                SELECT * FROM reasoning_sessions WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            session = dict(zip(columns, row))
            
            # Get stages
            cursor.execute("""
                SELECT * FROM reasoning_stages 
                WHERE session_id = ? 
                ORDER BY stage_order
            """, (session_id,))
            
            stage_rows = cursor.fetchall()
            stage_columns = [desc[0] for desc in cursor.description]
            stages = [dict(zip(stage_columns, row)) for row in stage_rows]
            
            session['stages'] = stages
            return session
            
        finally:
            conn.close()
    
    def query_sessions(
        self,
        agent_name: Optional[str] = None,
        min_confidence: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query reasoning sessions with filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM reasoning_sessions WHERE 1=1"
            params = []
            
            if agent_name:
                query += " AND agent_name = ?"
                params.append(agent_name)
            
            if min_confidence is not None:
                query += " AND overall_confidence >= ?"
                params.append(min_confidence)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
            
        finally:
            conn.close()
    
    def get_agent_statistics(self, agent_name: str) -> Dict[str, Any]:
        """Get reasoning statistics for an agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sessions,
                    AVG(overall_confidence) as avg_confidence,
                    AVG(total_duration_ms) as avg_duration_ms,
                    MIN(overall_confidence) as min_confidence,
                    MAX(overall_confidence) as max_confidence
                FROM reasoning_sessions
                WHERE agent_name = ?
            """, (agent_name,))
            
            row = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            
            return dict(zip(columns, row))
            
        finally:
            conn.close()


class ReasoningPubSub:
    """Redis-based pub/sub for live reasoning updates"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        channel_prefix: str = "reasoning:"
    ):
        """
        Initialize Redis pub/sub
        
        Args:
            redis_url: Redis connection URL
            channel_prefix: Prefix for pub/sub channels
        """
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.redis = None
        self.pubsub = None
        self.subscriptions: Dict[str, List[Callable]] = {}
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - pub/sub disabled")
            return
        
        logger.info(f"Initialized ReasoningPubSub with URL: {redis_url}")
    
    async def connect(self):
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            return
        
        try:
            self.redis = await aioredis.create_redis_pool(self.redis_url)
            logger.info("Connected to Redis for pub/sub")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            logger.info("Disconnected from Redis")
    
    async def publish_reasoning_start(
        self,
        agent_name: str,
        query: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Publish reasoning start event"""
        if not self.redis:
            return
        
        channel = f"{self.channel_prefix}{agent_name}:start"
        message = {
            'event': 'reasoning_start',
            'agent': agent_name,
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        await self.redis.publish(channel, json.dumps(message))
        logger.debug(f"Published reasoning start: {agent_name}")
    
    async def publish_stage_complete(
        self,
        agent_name: str,
        stage_result: StageResult
    ):
        """Publish stage completion event"""
        if not self.redis:
            return
        
        channel = f"{self.channel_prefix}{agent_name}:stage"
        message = {
            'event': 'stage_complete',
            'agent': agent_name,
            'stage': stage_result.stage.value,
            'confidence': stage_result.confidence,
            'duration_ms': stage_result.duration_ms,
            'traces': stage_result.traces,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.redis.publish(channel, json.dumps(message))
        logger.debug(f"Published stage complete: {agent_name}/{stage_result.stage.value}")
    
    async def publish_reasoning_complete(
        self,
        agent_name: str,
        result: ReasoningResult
    ):
        """Publish reasoning completion event"""
        if not self.redis:
            return
        
        channel = f"{self.channel_prefix}{agent_name}:complete"
        message = {
            'event': 'reasoning_complete',
            'agent': agent_name,
            'confidence': result.overall_confidence,
            'total_duration_ms': result.total_duration_ms,
            'timestamp': result.timestamp,
            'stages_count': len(result.stages)
        }
        
        await self.redis.publish(channel, json.dumps(message))
        logger.info(f"Published reasoning complete: {agent_name}")
    
    async def subscribe_agent(
        self,
        agent_name: str,
        callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Subscribe to all events for an agent
        
        Args:
            agent_name: Agent to subscribe to
            callback: Async callback function for events
        """
        if not self.redis:
            logger.warning("Redis not available for subscription")
            return
        
        channels = [
            f"{self.channel_prefix}{agent_name}:start",
            f"{self.channel_prefix}{agent_name}:stage",
            f"{self.channel_prefix}{agent_name}:complete"
        ]
        
        for channel in channels:
            if channel not in self.subscriptions:
                self.subscriptions[channel] = []
            self.subscriptions[channel].append(callback)
        
        logger.info(f"Subscribed to {agent_name} reasoning events")


class MemorySyncManager:
    """
    Unified interface for memory synchronization
    
    Combines SQLite persistence with Redis pub/sub for complete
    reasoning trace management.
    """
    
    def __init__(
        self,
        db_path: str = "reasoning_logs.db",
        redis_url: str = "redis://localhost:6379",
        enable_pubsub: bool = True
    ):
        """
        Initialize memory sync manager
        
        Args:
            db_path: Path to SQLite database
            redis_url: Redis connection URL
            enable_pubsub: Enable Redis pub/sub features
        """
        self.db = ReasoningMemoryDB(db_path)
        self.pubsub = None
        
        if enable_pubsub and REDIS_AVAILABLE:
            self.pubsub = ReasoningPubSub(redis_url)
        
        logger.info("Initialized MemorySyncManager")
    
    async def start(self):
        """Start memory sync services"""
        if self.pubsub:
            await self.pubsub.connect()
        logger.info("MemorySyncManager started")
    
    async def stop(self):
        """Stop memory sync services"""
        if self.pubsub:
            await self.pubsub.disconnect()
        logger.info("MemorySyncManager stopped")
    
    async def log_reasoning_session(self, result: ReasoningResult) -> str:
        """
        Log complete reasoning session (persistence + pub/sub)
        
        Args:
            result: ReasoningResult to log
            
        Returns:
            Session ID
        """
        # Persist to database
        session_id = self.db.log_reasoning(result)
        
        # Publish completion event
        if self.pubsub:
            await self.pubsub.publish_reasoning_complete(
                result.agent_name,
                result
            )
        
        return session_id
    
    async def publish_reasoning_start(
        self,
        agent_name: str,
        query: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Publish reasoning start event"""
        if self.pubsub:
            await self.pubsub.publish_reasoning_start(agent_name, query, metadata)
    
    async def publish_stage_complete(
        self,
        agent_name: str,
        stage_result: StageResult
    ):
        """Publish stage completion event"""
        if self.pubsub:
            await self.pubsub.publish_stage_complete(agent_name, stage_result)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve reasoning session"""
        return self.db.get_session(session_id)
    
    def query_sessions(
        self,
        agent_name: Optional[str] = None,
        min_confidence: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query reasoning sessions"""
        return self.db.query_sessions(agent_name, min_confidence, limit)
    
    def get_agent_statistics(self, agent_name: str) -> Dict[str, Any]:
        """Get agent reasoning statistics"""
        return self.db.get_agent_statistics(agent_name)
    
    async def subscribe_agent(
        self,
        agent_name: str,
        callback: Callable[[Dict[str, Any]], None]
    ):
        """Subscribe to agent reasoning events"""
        if self.pubsub:
            await self.pubsub.subscribe_agent(agent_name, callback)


# Global memory sync instance
_memory_sync: Optional[MemorySyncManager] = None


def get_memory_sync() -> MemorySyncManager:
    """Get or create global memory sync manager"""
    global _memory_sync
    
    if _memory_sync is None:
        _memory_sync = MemorySyncManager(
            db_path="data/reasoning_logs.db",
            redis_url="redis://localhost:6379",
            enable_pubsub=REDIS_AVAILABLE
        )
    
    return _memory_sync


async def init_memory_sync():
    """Initialize global memory sync manager"""
    memory_sync = get_memory_sync()
    await memory_sync.start()
    return memory_sync


async def cleanup_memory_sync():
    """Cleanup global memory sync manager"""
    global _memory_sync
    if _memory_sync:
        await _memory_sync.stop()
        _memory_sync = None
