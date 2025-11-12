#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Dashboard WebSocket Endpoints

Real-time data feeds for the Sovereign Intelligence Console dashboards:
- Federation Mesh: P2P network topology and sync traffic
- Memory Engine: Memory consolidation and confidence tracking

Architecture:
- FastAPI WebSocket endpoints
- Async background tasks for periodic updates
- SQLite for state persistence
- Mock data generation for development

Author: ARK Development Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set, Optional
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ============================================================================
# Data Models
# ============================================================================

class PeerInfo(BaseModel):
    """P2P peer information"""
    id: str
    name: str
    trust_tier: str  # 'core', 'trusted', 'verified', 'unverified'
    status: str  # 'active', 'syncing', 'idle'
    latency: float  # milliseconds
    data_shared: int  # bytes

class SyncEvent(BaseModel):
    """Network sync event"""
    timestamp: int  # milliseconds since epoch
    peer: str
    action: str  # 'memory_sync', 'reflection_sync', 'identity_sync', 'knowledge_sync'
    status: str  # 'active', 'complete', 'error'
    bytes: int

class MemoryLog(BaseModel):
    """Memory system event log"""
    timestamp: str  # ISO 8601
    message: str

# ============================================================================
# WebSocket Connection Manager
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections for multiple dashboards"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            'federation': set(),
            'memory': set(),
        }
    
    async def connect(self, websocket: WebSocket, dashboard: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[dashboard].add(websocket)
        logger.info(f"✅ Client connected to {dashboard} dashboard (total: {len(self.active_connections[dashboard])})")
    
    def disconnect(self, websocket: WebSocket, dashboard: str):
        """Remove WebSocket connection"""
        self.active_connections[dashboard].discard(websocket)
        logger.info(f"❌ Client disconnected from {dashboard} dashboard (remaining: {len(self.active_connections[dashboard])})")
    
    async def broadcast(self, message: dict, dashboard: str):
        """Broadcast message to all connected clients for a dashboard"""
        disconnected = set()
        for connection in self.active_connections[dashboard]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections[dashboard].discard(connection)
    
    def has_connections(self, dashboard: str) -> bool:
        """Check if dashboard has active connections"""
        return len(self.active_connections[dashboard]) > 0

# Global connection manager
manager = ConnectionManager()

# ============================================================================
# Federation Mesh State
# ============================================================================

class FederationState:
    """Manages federation mesh state and metrics"""
    
    def __init__(self):
        self.peers: List[PeerInfo] = []
        self.sync_traffic: List[SyncEvent] = []
        self.network_health: float = 94.0
        self.data_integrity: float = 99.7
        
        # Initialize with mock peers
        self._init_mock_peers()
    
    def _init_mock_peers(self):
        """Initialize with mock peer data"""
        self.peers = [
            PeerInfo(
                id='peer-1',
                name='ARK-Node-Alpha',
                trust_tier='core',
                status='active',
                latency=12.5,
                data_shared=1247 * 1024
            ),
            PeerInfo(
                id='peer-2',
                name='ARK-Node-Beta',
                trust_tier='trusted',
                status='active',
                latency=45.2,
                data_shared=892 * 1024
            ),
            PeerInfo(
                id='peer-3',
                name='ARK-Node-Gamma',
                trust_tier='trusted',
                status='syncing',
                latency=78.1,
                data_shared=534 * 1024
            ),
            PeerInfo(
                id='peer-4',
                name='ARK-Node-Delta',
                trust_tier='verified',
                status='active',
                latency=23.7,
                data_shared=445 * 1024
            ),
            PeerInfo(
                id='peer-5',
                name='ARK-Node-Epsilon',
                trust_tier='verified',
                status='idle',
                latency=156.3,
                data_shared=198 * 1024
            ),
        ]
        
        # Initialize with some recent sync events
        now = int(time.time() * 1000)
        self.sync_traffic = [
            SyncEvent(
                timestamp=now - 5000,
                peer='ARK-Node-Beta',
                action='memory_sync',
                status='complete',
                bytes=1024
            ),
            SyncEvent(
                timestamp=now - 3000,
                peer='ARK-Node-Gamma',
                action='reflection_sync',
                status='active',
                bytes=2048
            ),
            SyncEvent(
                timestamp=now - 1000,
                peer='ARK-Node-Alpha',
                action='identity_sync',
                status='complete',
                bytes=512
            ),
        ]
    
    def update_metrics(self):
        """Update network metrics with simulated changes"""
        # Update health metrics
        self.network_health = max(85, min(100, self.network_health + random.uniform(-1.5, 1.5)))
        self.data_integrity = max(95, min(100, self.data_integrity + random.uniform(-0.25, 0.25)))
        
        # Update peer latencies
        for peer in self.peers:
            peer.latency = max(10, peer.latency + random.uniform(-10, 10))
        
        # Randomly generate sync events
        if random.random() < 0.3:
            peer = random.choice(self.peers)
            actions = ['memory_sync', 'reflection_sync', 'identity_sync', 'knowledge_sync']
            event = SyncEvent(
                timestamp=int(time.time() * 1000),
                peer=peer.name,
                action=random.choice(actions),
                status='complete' if random.random() < 0.7 else 'active',
                bytes=random.randint(500, 3000)
            )
            self.sync_traffic.append(event)
            # Keep only last 50 events
            self.sync_traffic = self.sync_traffic[-50:]
    
    def to_dict(self) -> dict:
        """Convert state to dictionary for JSON serialization"""
        return {
            'type': 'federation_update',
            'timestamp': int(time.time() * 1000),
            'peers': [peer.model_dump() for peer in self.peers],
            'sync_traffic': [event.model_dump() for event in self.sync_traffic],
            'network_health': round(self.network_health, 2),
            'data_integrity': round(self.data_integrity, 2),
            'total_peers': len(self.peers),
            'active_syncs': sum(1 for e in self.sync_traffic if e.status == 'active')
        }

# Global federation state
federation_state = FederationState()

# ============================================================================
# Memory Engine State
# ============================================================================

class MemoryState:
    """Manages memory engine state and metrics"""
    
    def __init__(self):
        self.ingestion_rate: float = 8.0  # memories per second
        self.consolidation_rate: float = 7.0  # memories per second
        self.dedup_rate: float = 92.5  # percentage
        self.quarantine_count: int = 1
        self.trust_distribution: Dict[str, int] = {
            'core': 10,
            'sandbox': 3,
            'external': 1
        }
        self.confidence_deltas: List[float] = []
        self.logs: List[MemoryLog] = []
        
        # Initialize with mock data
        self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize with mock memory data"""
        # Generate 50 random confidence deltas
        self.confidence_deltas = [
            random.uniform(-0.2, 0.2) for _ in range(50)
        ]
        
        # Initialize logs
        now = datetime.now(timezone.utc)
        self.logs = [
            MemoryLog(
                timestamp=(now - timedelta(seconds=120)).isoformat(),
                message='Consolidated 5 new traces'
            ),
            MemoryLog(
                timestamp=(now - timedelta(seconds=60)).isoformat(),
                message='Deduplicated 2 redundant items'
            ),
            MemoryLog(
                timestamp=now.isoformat(),
                message='Memory sync complete'
            ),
        ]
    
    def update_metrics(self):
        """Update memory metrics with simulated changes"""
        from datetime import timedelta
        
        # Update rates
        self.ingestion_rate = max(0, self.ingestion_rate + random.uniform(-1, 1))
        self.consolidation_rate = max(0, self.consolidation_rate + random.uniform(-0.75, 0.75))
        
        # Update dedup rate
        self.dedup_rate = max(85, min(99, self.dedup_rate + random.uniform(-0.25, 0.25)))
        
        # Update quarantine count
        if random.random() < 0.1:
            self.quarantine_count = max(0, self.quarantine_count + random.choice([-1, 0, 1]))
        
        # Add new confidence delta occasionally
        if random.random() < 0.3:
            new_delta = random.uniform(-0.3, 0.3)
            self.confidence_deltas.append(new_delta)
            self.confidence_deltas = self.confidence_deltas[-50:]  # Keep last 50
        
        # Update trust distribution occasionally
        if random.random() < 0.2:
            self.trust_distribution['core'] += random.choice([-1, 0, 0, 1])
            self.trust_distribution['sandbox'] += random.choice([-1, 0, 1])
            self.trust_distribution['external'] += random.choice([0, 0, 1])
            
            # Ensure non-negative
            for key in self.trust_distribution:
                self.trust_distribution[key] = max(0, self.trust_distribution[key])
        
        # Add new log entry occasionally
        if random.random() < 0.2:
            messages = [
                'Consolidated memory batch',
                'Deduplicated redundant traces',
                'Quarantined suspicious entry',
                'Updated confidence scores',
                'Cross-referenced with peer data',
                'Reflection cycle complete',
                'Memory integrity verified',
                'Trust tier updated'
            ]
            new_log = MemoryLog(
                timestamp=datetime.now(timezone.utc).isoformat(),
                message=random.choice(messages)
            )
            self.logs.append(new_log)
            self.logs = self.logs[-20:]  # Keep last 20
    
    def to_dict(self) -> dict:
        """Convert state to dictionary for JSON serialization"""
        return {
            'type': 'memory_update',
            'timestamp': int(time.time() * 1000),
            'ingestion_rate': round(self.ingestion_rate, 2),
            'consolidation_rate': round(self.consolidation_rate, 2),
            'dedup_rate': round(self.dedup_rate, 2),
            'quarantine_count': self.quarantine_count,
            'trust_distribution': self.trust_distribution,
            'confidence_deltas': [round(d, 3) for d in self.confidence_deltas],
            'logs': [log.model_dump() for log in self.logs]
        }

# Global memory state
memory_state = MemoryState()

# ============================================================================
# Background Update Tasks
# ============================================================================

async def federation_broadcast_task():
    """Background task to broadcast federation updates"""
    logger.info("🚀 Federation broadcast task started")
    
    while True:
        try:
            # Only update if there are connected clients
            if manager.has_connections('federation'):
                # Update metrics
                federation_state.update_metrics()
                
                # Broadcast to all connected clients
                await manager.broadcast(federation_state.to_dict(), 'federation')
            
            # Wait 2-3 seconds before next update
            await asyncio.sleep(random.uniform(2.0, 3.0))
        
        except Exception as e:
            logger.error(f"Federation broadcast error: {e}", exc_info=True)
            await asyncio.sleep(5.0)

async def memory_broadcast_task():
    """Background task to broadcast memory engine updates"""
    logger.info("🚀 Memory broadcast task started")
    
    while True:
        try:
            # Only update if there are connected clients
            if manager.has_connections('memory'):
                # Update metrics
                memory_state.update_metrics()
                
                # Broadcast to all connected clients
                await manager.broadcast(memory_state.to_dict(), 'memory')
            
            # Wait 2-3 seconds before next update
            await asyncio.sleep(random.uniform(2.0, 3.0))
        
        except Exception as e:
            logger.error(f"Memory broadcast error: {e}", exc_info=True)
            await asyncio.sleep(5.0)

# ============================================================================
# WebSocket Endpoints
# ============================================================================

async def websocket_federation(websocket: WebSocket):
    """
    WebSocket endpoint for federation mesh dashboard
    
    Provides real-time updates about:
    - Peer network topology
    - Sync traffic events
    - Network health metrics
    - Data integrity scores
    """
    await manager.connect(websocket, 'federation')
    
    try:
        # Send initial state
        await websocket.send_json(federation_state.to_dict())
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (ping/pong, etc.)
                data = await websocket.receive_text()
                
                # Handle client requests
                if data == 'ping':
                    await websocket.send_json({'type': 'pong', 'timestamp': int(time.time() * 1000)})
                elif data == 'refresh':
                    # Send current state on demand
                    await websocket.send_json(federation_state.to_dict())
            
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                break
    
    except WebSocketDisconnect:
        logger.info("Federation WebSocket disconnected")
    except Exception as e:
        logger.error(f"Federation WebSocket error: {e}", exc_info=True)
    finally:
        manager.disconnect(websocket, 'federation')

async def websocket_memory(websocket: WebSocket):
    """
    WebSocket endpoint for memory engine dashboard
    
    Provides real-time updates about:
    - Memory ingestion and consolidation rates
    - Deduplication efficiency
    - Confidence delta evolution
    - Quarantine zone status
    - Trust tier distribution
    - Recent memory events
    """
    await manager.connect(websocket, 'memory')
    
    try:
        # Send initial state
        await websocket.send_json(memory_state.to_dict())
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (ping/pong, etc.)
                data = await websocket.receive_text()
                
                # Handle client requests
                if data == 'ping':
                    await websocket.send_json({'type': 'pong', 'timestamp': int(time.time() * 1000)})
                elif data == 'refresh':
                    # Send current state on demand
                    await websocket.send_json(memory_state.to_dict())
            
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                break
    
    except WebSocketDisconnect:
        logger.info("Memory WebSocket disconnected")
    except Exception as e:
        logger.error(f"Memory WebSocket error: {e}", exc_info=True)
    finally:
        manager.disconnect(websocket, 'memory')

# ============================================================================
# Startup Function
# ============================================================================

async def start_dashboard_tasks():
    """Start background tasks for dashboard updates"""
    asyncio.create_task(federation_broadcast_task())
    asyncio.create_task(memory_broadcast_task())
    logger.info("✅ Dashboard broadcast tasks started")


async def stop_dashboard_tasks():
    """Stop dashboard background tasks (cleanup on shutdown)"""
    # Broadcast tasks will stop naturally when no connections exist
    # Close all WebSocket connections
    for dashboard in ['federation', 'memory']:
        connections = list(manager.active_connections.get(dashboard, set()))
        for ws in connections:
            try:
                await ws.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
    logger.info("✅ Dashboard tasks stopped")
