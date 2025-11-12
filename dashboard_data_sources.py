#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Dashboard Production Data Sources

Connects real ARK system data to dashboard WebSocket feeds:
- Federation: Query ark-federation-service.py Redis peer data
- Memory: Query reasoning_logs.db and ark.db for consolidation metrics

This module replaces mock data generation with production data sources.

Author: ARK Development Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
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

logger = logging.getLogger(__name__)


class FederationDataSource:
    """
    Real-time federation mesh data from Redis and ark-federation-service
    
    Queries:
    - Active peers from Redis (peer:* keys)
    - Network health from peer heartbeats
    - Sync traffic from recent activity
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize federation data source
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client: Optional[aioredis.Redis] = None
        self.last_sync_events: List[Dict] = []
        self._connected = False
        logger.info(f"FederationDataSource initialized with Redis: {redis_url}")
    
    async def connect(self):
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - federation data will be unavailable")
            return False
        
        try:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            self._connected = True
            logger.info("✅ Connected to Redis for federation data")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Failed to connect to Redis: {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    async def get_peers(self) -> List[Dict]:
        """
        Get active peers from Redis
        
        Returns:
            List of peer info dictionaries
        """
        if not self._connected or not self.redis_client:
            return []
        
        try:
            peers = []
            async for key in self.redis_client.scan_iter(match="peer:*"):
                peer_data = await self.redis_client.hgetall(key)
                if peer_data:
                    # Convert to standard format
                    peer_id = key.replace("peer:", "")
                    peers.append({
                        "id": peer_id,
                        "hostname": peer_data.get("hostname", peer_id),
                        "trust_tier": peer_data.get("trust_tier", "verified"),
                        "status": "online" if peer_data.get("last_seen") else "offline",
                        "latency": int(peer_data.get("latency", 0)),
                        "last_seen": int(peer_data.get("last_seen", 0)) * 1000  # Convert to ms
                    })
            
            return peers
        except Exception as e:
            logger.error(f"Error fetching peers from Redis: {e}")
            return []
    
    async def get_sync_traffic(self) -> List[Dict]:
        """
        Get recent sync traffic events
        
        Returns:
            List of sync event dictionaries
        """
        if not self._connected or not self.redis_client:
            return self.last_sync_events[-10:]  # Return cached events
        
        try:
            # Query recent sync events from Redis list
            events = await self.redis_client.lrange("sync_events", 0, 9)
            sync_traffic = []
            
            for event_json in events:
                try:
                    event = json.loads(event_json)
                    sync_traffic.append({
                        "timestamp": event.get("timestamp", int(time.time() * 1000)),
                        "source": event.get("source", "unknown"),
                        "target": event.get("target", "unknown"),
                        "event_type": event.get("event_type", "sync"),
                        "bytes": event.get("bytes", 0),
                        "success": event.get("success", True)
                    })
                except json.JSONDecodeError:
                    continue
            
            # Cache for offline mode
            self.last_sync_events = sync_traffic
            return sync_traffic
        except Exception as e:
            logger.error(f"Error fetching sync traffic: {e}")
            return self.last_sync_events[-10:]
    
    async def get_network_metrics(self, peers: List[Dict]) -> Dict[str, float]:
        """
        Calculate network health metrics from peer data
        
        Args:
            peers: List of peer dictionaries
            
        Returns:
            Dictionary with health, integrity, and latency metrics
        """
        if not peers:
            return {
                "network_health": 0.0,
                "data_integrity": 0.0,
                "avg_latency": 0.0
            }
        
        # Calculate health: percentage of online peers
        online_peers = sum(1 for p in peers if p.get("status") == "online")
        network_health = (online_peers / len(peers)) * 100 if peers else 0.0
        
        # Data integrity: based on trust tiers
        core_peers = sum(1 for p in peers if p.get("trust_tier") == "core")
        trusted_peers = sum(1 for p in peers if p.get("trust_tier") == "trusted")
        data_integrity = ((core_peers * 1.0 + trusted_peers * 0.95) / len(peers)) * 100 if peers else 0.0
        
        # Average latency
        latencies = [p.get("latency", 0) for p in peers if p.get("status") == "online"]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        
        return {
            "network_health": round(network_health, 1),
            "data_integrity": round(data_integrity, 1),
            "avg_latency": round(avg_latency, 1)
        }


class MemoryDataSource:
    """
    Real-time memory consolidation data from ARK databases
    
    Queries:
    - Reasoning sessions from reasoning_logs.db
    - Code index and patterns from ark.db
    - Sandbox executions for quarantine tracking
    """
    
    def __init__(
        self,
        reasoning_db_path: str = "data/reasoning_logs.db",
        ark_db_path: str = "data/ark.db"
    ):
        """
        Initialize memory data source
        
        Args:
            reasoning_db_path: Path to reasoning logs database
            ark_db_path: Path to ARK main database
        """
        self.reasoning_db_path = Path(reasoning_db_path)
        self.ark_db_path = Path(ark_db_path)
        self._last_query_time = 0
        self._cache: Dict[str, Any] = {}
        logger.info(f"MemoryDataSource initialized with DBs: {reasoning_db_path}, {ark_db_path}")
    
    def _get_reasoning_conn(self) -> Optional[sqlite3.Connection]:
        """Get connection to reasoning logs database"""
        try:
            if self.reasoning_db_path.exists():
                return sqlite3.connect(str(self.reasoning_db_path))
        except Exception as e:
            logger.error(f"Error connecting to reasoning DB: {e}")
        return None
    
    def _get_ark_conn(self) -> Optional[sqlite3.Connection]:
        """Get connection to ARK database"""
        try:
            if self.ark_db_path.exists():
                return sqlite3.connect(str(self.ark_db_path))
        except Exception as e:
            logger.error(f"Error connecting to ARK DB: {e}")
        return None
    
    async def get_consolidation_rates(self) -> Dict[str, float]:
        """
        Calculate memory ingestion and consolidation rates
        
        Returns:
            Dictionary with ingestion_rate and consolidation_rate
        """
        conn = self._get_reasoning_conn()
        if not conn:
            return {"ingestion_rate": 0.0, "consolidation_rate": 0.0}
        
        try:
            cursor = conn.cursor()
            
            # Count sessions in last minute (ingestion rate)
            one_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM reasoning_sessions 
                WHERE created_at > ?
            """, (one_min_ago,))
            recent_sessions = cursor.fetchone()[0]
            
            # Count completed stages (consolidation rate)
            cursor.execute("""
                SELECT COUNT(*) FROM reasoning_stages 
                WHERE created_at > ? AND confidence >= 0.7
            """, (one_min_ago,))
            consolidated_stages = cursor.fetchone()[0]
            
            # Calculate rates per second
            ingestion_rate = recent_sessions / 60.0
            consolidation_rate = consolidated_stages / 60.0
            
            conn.close()
            return {
                "ingestion_rate": round(ingestion_rate, 1),
                "consolidation_rate": round(consolidation_rate, 1)
            }
        except Exception as e:
            logger.error(f"Error calculating consolidation rates: {e}")
            conn.close()
            return {"ingestion_rate": 0.0, "consolidation_rate": 0.0}
    
    async def get_deduplication_efficiency(self) -> float:
        """
        Calculate deduplication efficiency from code patterns
        
        Returns:
            Deduplication percentage
        """
        conn = self._get_ark_conn()
        if not conn:
            return 0.0
        
        try:
            cursor = conn.cursor()
            
            # Get total patterns vs unique code snippets
            cursor.execute("SELECT COUNT(DISTINCT code_snippet) FROM code_patterns")
            unique_snippets = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(usage_count) FROM code_patterns")
            total_usage = cursor.fetchone()[0] or 0
            
            # Efficiency = (reused code / total code) * 100
            if total_usage > 0:
                efficiency = ((total_usage - unique_snippets) / total_usage) * 100
            else:
                efficiency = 0.0
            
            conn.close()
            return round(max(0.0, min(100.0, efficiency)), 1)
        except Exception as e:
            logger.error(f"Error calculating dedup efficiency: {e}")
            if conn:
                conn.close()
            return 0.0
    
    async def get_quarantine_count(self) -> int:
        """
        Get count of items in quarantine (failed sandbox executions)
        
        Returns:
            Number of quarantined items
        """
        conn = self._get_ark_conn()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM sandbox_executions 
                WHERE status = 'error' OR security_violations IS NOT NULL
            """)
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting quarantine count: {e}")
            if conn:
                conn.close()
            return 0
    
    async def get_trust_distribution(self) -> Dict[str, int]:
        """
        Get distribution of items by trust tier
        
        Returns:
            Dictionary mapping trust tier to count
        """
        conn = self._get_ark_conn()
        if not conn:
            return {"core": 0, "trusted": 0, "sandbox": 0, "external": 0}
        
        try:
            cursor = conn.cursor()
            
            # Count by trust tier in code_index
            cursor.execute("""
                SELECT trust_tier, COUNT(*) 
                FROM code_index 
                GROUP BY trust_tier
            """)
            
            distribution = {"core": 0, "trusted": 0, "sandbox": 0, "external": 0}
            for tier, count in cursor.fetchall():
                if tier in distribution:
                    distribution[tier] = count
            
            conn.close()
            return distribution
        except Exception as e:
            logger.error(f"Error getting trust distribution: {e}")
            if conn:
                conn.close()
            return {"core": 0, "trusted": 0, "sandbox": 0, "external": 0}
    
    async def get_confidence_deltas(self, count: int = 50) -> List[float]:
        """
        Get recent confidence delta values from reasoning stages
        
        Args:
            count: Number of deltas to return
            
        Returns:
            List of confidence delta values
        """
        conn = self._get_reasoning_conn()
        if not conn:
            return [0.0] * count
        
        try:
            cursor = conn.cursor()
            
            # Get recent confidence values
            cursor.execute("""
                SELECT confidence FROM reasoning_stages 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (count * 2,))  # Get 2x to calculate deltas
            
            confidences = [row[0] for row in cursor.fetchall() if row[0] is not None]
            
            # Calculate deltas
            deltas = []
            for i in range(len(confidences) - 1):
                delta = confidences[i] - confidences[i + 1]
                deltas.append(round(delta, 3))
            
            # Pad with zeros if not enough data
            while len(deltas) < count:
                deltas.append(0.0)
            
            conn.close()
            return deltas[:count]
        except Exception as e:
            logger.error(f"Error getting confidence deltas: {e}")
            if conn:
                conn.close()
            return [0.0] * count
    
    async def get_recent_logs(self, limit: int = 10) -> List[Dict]:
        """
        Get recent memory consolidation events
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of log dictionaries
        """
        conn = self._get_reasoning_conn()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Get recent reasoning sessions
            cursor.execute("""
                SELECT agent_name, query, overall_confidence, timestamp, created_at
                FROM reasoning_sessions 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            logs = []
            for row in cursor.fetchall():
                agent_name, query, confidence, timestamp, created_at = row
                
                # Determine log type and message
                if confidence and confidence >= 0.8:
                    log_type = "consolidation"
                    message = f"High-confidence reasoning by {agent_name}"
                elif confidence and confidence < 0.5:
                    log_type = "warning"
                    message = f"Low-confidence reasoning by {agent_name}: {query[:50]}..."
                else:
                    log_type = "info"
                    message = f"{agent_name} processed: {query[:50]}..."
                
                logs.append({
                    "timestamp": created_at or timestamp,
                    "type": log_type,
                    "message": message,
                    "severity": "warning" if log_type == "warning" else "info"
                })
            
            conn.close()
            return logs
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            if conn:
                conn.close()
            return []


# Global instances
federation_source: Optional[FederationDataSource] = None
memory_source: Optional[MemoryDataSource] = None


async def init_data_sources(redis_url: str = "redis://localhost:6379/0"):
    """
    Initialize production data sources
    
    Args:
        redis_url: Redis connection URL
    """
    global federation_source, memory_source
    
    # Initialize federation data source
    federation_source = FederationDataSource(redis_url)
    await federation_source.connect()
    
    # Initialize memory data source
    memory_source = MemoryDataSource()
    
    logger.info("✅ Production data sources initialized")


async def cleanup_data_sources():
    """Cleanup data sources on shutdown"""
    global federation_source, memory_source
    
    if federation_source:
        await federation_source.disconnect()
    
    logger.info("✅ Data sources cleaned up")


def get_federation_source() -> Optional[FederationDataSource]:
    """Get federation data source instance"""
    return federation_source


def get_memory_source() -> Optional[MemoryDataSource]:
    """Get memory data source instance"""
    return memory_source
