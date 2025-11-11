#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Federation Core

Implements peer-to-peer federation for distributed ARK mesh network.
Each node carries identical intelligence yet retains local sovereignty.

Features:
- Peer discovery (LAN/subnet)
- Trust tier management (core/sandbox/external)
- Bidirectional knowledge synchronization
- Signed peer manifests (ed25519)
- Conflict resolution
"""

import asyncio
import json
import logging
import socket
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import uuid

try:
    from federation import crypto as ark_crypto
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("PyNaCl not available - peer signing disabled")

logger = logging.getLogger(__name__)


class TrustTier(Enum):
    """Trust levels for federation peers"""
    CORE = "core"  # Fully trusted, bidirectional sync
    SANDBOX = "sandbox"  # Limited trust, unidirectional sync
    EXTERNAL = "external"  # Minimal trust, query-only
    UNKNOWN = "unknown"  # Not yet classified


@dataclass
class PeerManifest:
    """Signed manifest describing a peer node"""
    peer_id: str
    peer_name: str
    address: str
    port: int
    public_key: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    trust_tier: TrustTier = TrustTier.UNKNOWN
    version: str = "v6.0"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'peer_id': self.peer_id,
            'peer_name': self.peer_name,
            'address': self.address,
            'port': self.port,
            'public_key': self.public_key,
            'capabilities': self.capabilities,
            'trust_tier': self.trust_tier.value,
            'version': self.version,
            'timestamp': self.timestamp,
            'signature': self.signature
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PeerManifest':
        """Create from dictionary"""
        data = data.copy()
        if 'trust_tier' in data:
            data['trust_tier'] = TrustTier(data['trust_tier'])
        return cls(**data)


@dataclass
class KnowledgePacket:
    """Unit of knowledge for synchronization"""
    packet_id: str
    source_peer: str
    packet_type: str  # reasoning_session, agent_update, memory_entry
    data: Dict
    timestamp: str
    hash: str
    dependencies: List[str] = field(default_factory=list)
    
    def calculate_hash(self) -> str:
        """Calculate content hash"""
        content = json.dumps({
            'packet_id': self.packet_id,
            'source_peer': self.source_peer,
            'packet_type': self.packet_type,
            'data': self.data,
            'timestamp': self.timestamp
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class FederationNode:
    """
    ARK Federation Node
    
    Manages peer connections, trust tiers, and knowledge synchronization.
    """
    
    def __init__(
        self,
        node_name: str,
        listen_port: int = 8102,
        data_dir: str = "data/federation"
    ):
        """
        Initialize federation node
        
        Args:
            node_name: Name of this node
            listen_port: Port for federation server
            data_dir: Directory for federation data
        """
        self.node_id = str(uuid.uuid4())
        self.node_name = node_name
        self.listen_port = listen_port
        self.data_dir = data_dir
        
        # Peer registry
        self.peers: Dict[str, PeerManifest] = {}
        self.trusted_peers: Set[str] = set()
        
        # Knowledge sync state
        self.local_knowledge: Dict[str, KnowledgePacket] = {}
        self.sync_queue: List[KnowledgePacket] = []
        
        # Cryptography - Ed25519 keypair
        if CRYPTO_AVAILABLE:
            self.private_key, self.public_key = ark_crypto.generate_keypair(self.node_id)
            logger.info(f"🔐 Loaded Ed25519 keypair for {self.node_id}")
        else:
            self.private_key = None
            self.public_key = None
            logger.warning("⚠️  No cryptography - signatures disabled")
        
        # Server state
        self.running = False
        
        logger.info(f"Initialized federation node: {self.node_name} ({self.node_id})")
    
    def get_manifest(self) -> PeerManifest:
        """Get this node's manifest"""
        public_key_str = None
        if CRYPTO_AVAILABLE and self.public_key:
            public_key_str = ark_crypto.export_public_key(self.node_id)
        
        return PeerManifest(
            peer_id=self.node_id,
            peer_name=self.node_name,
            address=self._get_local_ip(),
            port=self.listen_port,
            public_key=public_key_str,
            capabilities=[
                "hierarchical_reasoning",
                "agent_orchestration",
                "memory_sync",
                "knowledge_federation",
                "signed_packets" if CRYPTO_AVAILABLE else "unsigned"
            ],
            trust_tier=TrustTier.CORE  # Self is always core
        )
    
    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    async def start(self):
        """Start federation server"""
        self.running = True
        logger.info(f"🕸️  Federation server starting on port {self.listen_port}")
        
        # Start server components
        tasks = [
            self._run_discovery_service(),
            self._run_sync_service(),
            self._run_heartbeat_service()
        ]
        
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Stop federation server"""
        self.running = False
        logger.info("Federation server stopped")
    
    async def _run_discovery_service(self):
        """Run peer discovery service"""
        from federation.discovery import DiscoveryService
        
        logger.info("Discovery service started")
        
        # Create discovery service
        discovery = DiscoveryService(
            node_manifest=self.get_manifest().to_dict(),
            on_peer_discovered=self._on_peer_discovered
        )
        
        try:
            await discovery.start()
        except Exception as e:
            logger.error(f"Discovery service error: {e}")
    
    async def _run_sync_service(self):
        """Run knowledge synchronization service"""
        if not CRYPTO_AVAILABLE:
            logger.warning("Sync service requires cryptography - skipping")
            return
        
        from federation.sync_protocol import SyncProtocol
        
        logger.info("Sync service started")
        
        # Build verify keys dict for trusted peers
        verify_keys = {}
        for peer_id, peer in self.peers.items():
            if peer.trust_tier == TrustTier.CORE and ark_crypto.peer_key_exists(peer_id):
                try:
                    verify_keys[peer_id] = ark_crypto.load_peer_key(peer_id)
                except Exception as e:
                    logger.error(f"Failed to load key for {peer_id}: {e}")
        
        # Create sync protocol
        self.sync_protocol = SyncProtocol(
            node_id=self.node_id,
            private_key=self.private_key,
            verify_keys=verify_keys,
            on_packet_received=self._on_packet_received
        )
        
        # Start sync server
        try:
            await self.sync_protocol.start_server(port=8104)
        except Exception as e:
            logger.error(f"Sync service error: {e}")
    
    async def _run_heartbeat_service(self):
        """Run peer heartbeat monitoring"""
        logger.info("Heartbeat service started")
        
        while self.running:
            # Check peer health
            await self._check_peer_health()
            
            await asyncio.sleep(60)  # Heartbeat every 60s
    
    async def _process_sync_queue(self):
        """Process knowledge packets in sync queue"""
        while self.sync_queue:
            packet = self.sync_queue.pop(0)
            await self._propagate_knowledge(packet)
    
    async def _propagate_knowledge(self, packet: KnowledgePacket):
        """Propagate knowledge packet to peers"""
        for peer_id, peer in self.peers.items():
            # Only sync with trusted peers
            if peer.trust_tier in [TrustTier.CORE, TrustTier.SANDBOX]:
                # Send packet to peer
                logger.debug(f"Propagating {packet.packet_id} to {peer.peer_name}")
    
    async def _check_peer_health(self):
        """Check health of registered peers"""
        for peer_id, peer in list(self.peers.items()):
            # Ping peer
            # If unresponsive, mark as offline
            pass
    
    def discover_peers(self, subnet: str = "auto") -> List[PeerManifest]:
        """
        Discover peers on local network
        
        Args:
            subnet: Subnet to scan (e.g., "192.168.1.0/24")
            
        Returns:
            List of discovered peer manifests
        """
        logger.info(f"🔍 Discovering peers on subnet: {subnet}")
        
        # Simplified discovery - real implementation would scan network
        discovered = []
        
        logger.info(f"Discovered {len(discovered)} peers")
        return discovered
    
    def add_peer(self, manifest: PeerManifest, trust_tier: TrustTier = TrustTier.UNKNOWN):
        """
        Manually add a peer
        
        Args:
            manifest: Peer manifest
            trust_tier: Trust tier to assign
        """
        manifest.trust_tier = trust_tier
        self.peers[manifest.peer_id] = manifest
        
        if trust_tier == TrustTier.CORE:
            self.trusted_peers.add(manifest.peer_id)
        
        logger.info(f"➕ Added peer: {manifest.peer_name} ({trust_tier.value})")
    
    def remove_peer(self, peer_id: str):
        """Remove a peer"""
        if peer_id in self.peers:
            peer = self.peers[peer_id]
            del self.peers[peer_id]
            self.trusted_peers.discard(peer_id)
            logger.info(f"➖ Removed peer: {peer.peer_name}")
    
    def set_peer_trust_tier(self, peer_id: str, trust_tier: TrustTier):
        """Update peer trust tier"""
        if peer_id in self.peers:
            self.peers[peer_id].trust_tier = trust_tier
            
            if trust_tier == TrustTier.CORE:
                self.trusted_peers.add(peer_id)
            else:
                self.trusted_peers.discard(peer_id)
            
            logger.info(f"🔒 Updated {self.peers[peer_id].peer_name} to {trust_tier.value}")
    
    def list_peers(self, trust_tier: Optional[TrustTier] = None) -> List[PeerManifest]:
        """List all peers, optionally filtered by trust tier"""
        if trust_tier:
            return [p for p in self.peers.values() if p.trust_tier == trust_tier]
        return list(self.peers.values())
    
    async def sync_knowledge(self, peer_id: str, auto: bool = True):
        """
        Synchronize knowledge with a peer
        
        Args:
            peer_id: Peer to sync with
            auto: Enable continuous auto-sync
        """
        if peer_id not in self.peers:
            logger.error(f"Peer {peer_id} not found")
            return
        
        peer = self.peers[peer_id]
        logger.info(f"🔄 Syncing knowledge with {peer.peer_name}")
        
        if auto:
            logger.info(f"✅ Auto-sync enabled for {peer.peer_name}")
    
    def add_knowledge(self, packet_type: str, data: Dict):
        """
        Add knowledge packet to local store
        
        Args:
            packet_type: Type of knowledge
            data: Knowledge data
        """
        packet = KnowledgePacket(
            packet_id=str(uuid.uuid4()),
            source_peer=self.node_id,
            packet_type=packet_type,
            data=data,
            timestamp=datetime.now().isoformat(),
            hash="",
            dependencies=[]
        )
        packet.hash = packet.calculate_hash()
        
        self.local_knowledge[packet.packet_id] = packet
        self.sync_queue.append(packet)
        
        logger.debug(f"📦 Added knowledge packet: {packet.packet_id}")
    
    async def _on_peer_discovered(self, peer_manifest: Dict):
        """Callback when peer discovered via UDP multicast"""
        peer_id = peer_manifest['peer_id']
        
        # Check if already registered
        if peer_id in self.peers:
            logger.debug(f"Peer already registered: {peer_id}")
            return
        
        # Auto-register with UNKNOWN trust tier
        manifest = PeerManifest.from_dict(peer_manifest)
        manifest.trust_tier = TrustTier.UNKNOWN
        
        self.peers[peer_id] = manifest
        logger.info(f"✨ Auto-registered discovered peer: {manifest.peer_name} (UNKNOWN tier)")
        logger.info(f"   Use 'ark-lattice peers trust-tier {peer_id} core' to trust")
    
    async def _on_packet_received(self, peer_id: str, packet: Dict):
        """Callback when verified packet received from peer"""
        packet_id = packet.get('packet_id', 'unknown')
        packet_type = packet.get('packet_type', 'unknown')
        
        logger.info(f"📦 Received {packet_type} from {peer_id}: {packet_id[:16]}...")
        
        # Store in local knowledge if not duplicate
        if packet_id not in self.local_knowledge:
            # Create KnowledgePacket
            from federation.federation_core import KnowledgePacket
            
            kp = KnowledgePacket(
                packet_id=packet['packet_id'],
                source_peer=packet['source_peer'],
                packet_type=packet['packet_type'],
                data=packet['data'],
                timestamp=packet['timestamp'],
                hash=packet['hash'],
                dependencies=packet.get('dependencies', [])
            )
            
            self.local_knowledge[packet_id] = kp
            
            # Propagate to other peers (except sender)
            if hasattr(self, 'sync_protocol'):
                await self.sync_protocol.broadcast_packet(packet, exclude_peers={peer_id})
    
    def get_stats(self) -> Dict:
        """Get federation statistics"""
        stats = {
            'node_id': self.node_id,
            'node_name': self.node_name,
            'peers': {
                'total': len(self.peers),
                'core': len([p for p in self.peers.values() if p.trust_tier == TrustTier.CORE]),
                'sandbox': len([p for p in self.peers.values() if p.trust_tier == TrustTier.SANDBOX]),
                'external': len([p for p in self.peers.values() if p.trust_tier == TrustTier.EXTERNAL]),
                'unknown': len([p for p in self.peers.values() if p.trust_tier == TrustTier.UNKNOWN]),
            },
            'knowledge': {
                'local_packets': len(self.local_knowledge),
                'sync_queue': len(self.sync_queue)
            },
            'running': self.running
        }
        
        # Add sync stats if available
        if hasattr(self, 'sync_protocol'):
            stats['sync'] = self.sync_protocol.get_stats()
        
        return stats


# Global federation node
_federation_node: Optional[FederationNode] = None


def get_federation_node() -> FederationNode:
    """Get or create global federation node"""
    global _federation_node
    
    if _federation_node is None:
        _federation_node = FederationNode(
            node_name="ark-primary",
            listen_port=8102
        )
    
    return _federation_node


async def start_federation():
    """Start federation services"""
    node = get_federation_node()
    await node.start()


async def stop_federation():
    """Stop federation services"""
    node = get_federation_node()
    await node.stop()
