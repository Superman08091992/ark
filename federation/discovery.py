#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Federation Discovery Service

Implements UDP multicast beacon for peer discovery:
- Broadcasts presence every 60s with node ID, trust tier, key fingerprint
- Listens for other nodes on the same subnet
- Auto-registers discovered peers
- Validates manifests before registration

Security:
- Fingerprint included for manual verification
- Trust tier starts as UNKNOWN
- Requires manual elevation to CORE/SANDBOX after key exchange
"""

import asyncio
import json
import logging
import socket
import struct
from typing import Optional, Dict, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

# Multicast configuration
MCAST_GROUP = '239.255.0.1'  # Local admin multicast
MCAST_PORT = 8103
BEACON_INTERVAL = 60  # Seconds between broadcasts


class DiscoveryService:
    """
    UDP multicast discovery service for ARK nodes
    
    Broadcasts node presence and listens for peers on local network.
    """
    
    def __init__(
        self,
        node_manifest: Dict,
        on_peer_discovered: Optional[Callable] = None
    ):
        """
        Initialize discovery service
        
        Args:
            node_manifest: This node's PeerManifest as dict
            on_peer_discovered: Callback when peer found (peer_manifest)
        """
        self.node_manifest = node_manifest
        self.on_peer_discovered = on_peer_discovered
        
        self.running = False
        self.sock = None
        
        # Track discovered peers to avoid duplicates
        self.discovered_peers: Dict[str, float] = {}  # peer_id -> last_seen
        
        logger.info(f"Discovery service initialized for {node_manifest['peer_name']}")
    
    async def start(self):
        """Start discovery service"""
        self.running = True
        logger.info(f"🔍 Starting discovery service on {MCAST_GROUP}:{MCAST_PORT}")
        
        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to multicast port
        self.sock.bind(('', MCAST_PORT))
        
        # Join multicast group
        mreq = struct.pack('4sl', socket.inet_aton(MCAST_GROUP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        # Set non-blocking
        self.sock.setblocking(False)
        
        # Start tasks
        await asyncio.gather(
            self._broadcast_loop(),
            self._listen_loop(),
            self._cleanup_loop()
        )
    
    async def stop(self):
        """Stop discovery service"""
        self.running = False
        if self.sock:
            self.sock.close()
        logger.info("Discovery service stopped")
    
    async def _broadcast_loop(self):
        """Broadcast beacon every BEACON_INTERVAL seconds"""
        logger.info(f"📡 Broadcasting beacon every {BEACON_INTERVAL}s")
        
        while self.running:
            try:
                # Create beacon message
                beacon = {
                    'type': 'beacon',
                    'peer_id': self.node_manifest['peer_id'],
                    'peer_name': self.node_manifest['peer_name'],
                    'address': self.node_manifest['address'],
                    'port': self.node_manifest['port'],
                    'trust_tier': self.node_manifest.get('trust_tier', 'unknown'),
                    'key_fingerprint': self._get_fingerprint(),
                    'capabilities': self.node_manifest.get('capabilities', []),
                    'version': self.node_manifest.get('version', 'v6.0'),
                    'timestamp': int(datetime.now().timestamp() * 1000)
                }
                
                # Serialize and send
                data = json.dumps(beacon).encode('utf-8')
                self.sock.sendto(data, (MCAST_GROUP, MCAST_PORT))
                
                logger.debug(f"📤 Beacon broadcast: {self.node_manifest['peer_name']}")
                
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
            
            await asyncio.sleep(BEACON_INTERVAL)
    
    async def _listen_loop(self):
        """Listen for beacons from other nodes"""
        logger.info("👂 Listening for peer beacons...")
        
        while self.running:
            try:
                # Non-blocking receive with timeout
                await asyncio.sleep(0.1)  # Small sleep to prevent busy loop
                
                try:
                    data, addr = self.sock.recvfrom(4096)
                except BlockingIOError:
                    continue  # No data available
                
                # Parse beacon
                try:
                    beacon = json.loads(data.decode('utf-8'))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid beacon from {addr}")
                    continue
                
                # Validate beacon
                if not self._validate_beacon(beacon):
                    logger.warning(f"Invalid beacon structure from {addr}")
                    continue
                
                # Ignore own beacons
                if beacon['peer_id'] == self.node_manifest['peer_id']:
                    continue
                
                # Process discovered peer
                await self._process_discovered_peer(beacon, addr)
                
            except Exception as e:
                logger.error(f"Listen error: {e}")
    
    async def _cleanup_loop(self):
        """Clean up stale peer entries"""
        while self.running:
            await asyncio.sleep(300)  # Every 5 minutes
            
            now = datetime.now().timestamp()
            stale_threshold = 300  # 5 minutes
            
            stale_peers = [
                peer_id for peer_id, last_seen in self.discovered_peers.items()
                if (now - last_seen) > stale_threshold
            ]
            
            for peer_id in stale_peers:
                logger.info(f"🧹 Removing stale peer: {peer_id}")
                del self.discovered_peers[peer_id]
    
    def _get_fingerprint(self) -> str:
        """Get public key fingerprint if available"""
        pub_key = self.node_manifest.get('public_key')
        if pub_key:
            return pub_key[:16] + "..."
        return "no-key"
    
    def _validate_beacon(self, beacon: Dict) -> bool:
        """Validate beacon structure"""
        required_fields = ['type', 'peer_id', 'peer_name', 'address', 'port']
        return all(field in beacon for field in required_fields)
    
    async def _process_discovered_peer(self, beacon: Dict, addr: tuple):
        """Process a discovered peer"""
        peer_id = beacon['peer_id']
        peer_name = beacon['peer_name']
        
        # Check if already discovered recently
        now = datetime.now().timestamp()
        if peer_id in self.discovered_peers:
            # Update last seen
            self.discovered_peers[peer_id] = now
            return
        
        # New peer discovered
        logger.info(f"🔍 Discovered peer: {peer_name} ({beacon['address']}:{beacon['port']})")
        logger.info(f"   Fingerprint: {beacon.get('key_fingerprint', 'none')}")
        logger.info(f"   Capabilities: {', '.join(beacon.get('capabilities', []))}")
        
        # Mark as discovered
        self.discovered_peers[peer_id] = now
        
        # Create peer manifest
        peer_manifest = {
            'peer_id': peer_id,
            'peer_name': peer_name,
            'address': beacon['address'],
            'port': beacon['port'],
            'public_key': None,  # Not shared via beacon (security)
            'capabilities': beacon.get('capabilities', []),
            'trust_tier': 'unknown',  # Always starts as unknown
            'version': beacon.get('version', 'unknown'),
            'timestamp': beacon.get('timestamp'),
        }
        
        # Callback to federation node
        if self.on_peer_discovered:
            await self.on_peer_discovered(peer_manifest)


async def discover_peers_once(node_manifest: Dict, timeout: int = 10) -> list:
    """
    One-shot discovery scan (non-blocking)
    
    Args:
        node_manifest: This node's manifest
        timeout: Seconds to listen for peers
        
    Returns:
        List of discovered peer manifests
    """
    discovered = []
    
    def on_discovered(peer_manifest):
        discovered.append(peer_manifest)
    
    service = DiscoveryService(node_manifest, on_discovered)
    
    try:
        # Run for timeout seconds
        await asyncio.wait_for(service.start(), timeout=timeout)
    except asyncio.TimeoutError:
        pass
    finally:
        await service.stop()
    
    return discovered


if __name__ == "__main__":
    # Test discovery service
    logging.basicConfig(level=logging.INFO)
    
    test_manifest = {
        'peer_id': 'test-node-123',
        'peer_name': 'Test ARK Node',
        'address': '127.0.0.1',
        'port': 8102,
        'public_key': 'abcd1234' * 8,  # Fake key
        'capabilities': ['test'],
        'trust_tier': 'core',
        'version': 'v6.0'
    }
    
    async def main():
        service = DiscoveryService(test_manifest)
        await service.start()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped")
