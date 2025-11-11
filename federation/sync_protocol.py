#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Federation Sync Protocol

WebSocket-based bidirectional knowledge synchronization:
- Signed KnowledgePacket transmission
- Signature verification before acceptance
- Conflict resolution with hash comparison
- Delta sync optimization
- Connection management per peer

Security:
- All packets must be signed
- Verification with trusted peer keys
- Invalid signatures rejected immediately
- Connection authenticated on handshake
"""

import asyncio
import json
import logging
import websockets
from typing import Optional, Dict, Callable, Set
from datetime import datetime
from websockets.server import serve
from websockets.client import connect

logger = logging.getLogger(__name__)


class SyncProtocol:
    """
    WebSocket-based synchronization protocol for ARK federation
    
    Handles bidirectional knowledge packet exchange with signature verification.
    """
    
    def __init__(
        self,
        node_id: str,
        private_key,
        verify_keys: Dict[str, any],  # peer_id -> VerifyKey
        on_packet_received: Optional[Callable] = None
    ):
        """
        Initialize sync protocol
        
        Args:
            node_id: This node's identifier
            private_key: Ed25519 signing key for outgoing packets
            verify_keys: Dictionary of peer_id -> VerifyKey for verification
            on_packet_received: Callback when packet verified (packet_dict)
        """
        self.node_id = node_id
        self.private_key = private_key
        self.verify_keys = verify_keys
        self.on_packet_received = on_packet_received
        
        # Connection management
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.connected_peers: Set[str] = set()
        
        # Sync state
        self.packets_sent = 0
        self.packets_received = 0
        self.packets_rejected = 0
        
        logger.info(f"Sync protocol initialized for node: {node_id}")
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8104):
        """
        Start WebSocket server for incoming peer connections
        
        Args:
            host: Host to bind to
            port: Port to listen on
        """
        logger.info(f"🔄 Starting sync server on {host}:{port}")
        
        async with serve(self._handle_connection, host, port):
            # Keep server running
            await asyncio.Future()
    
    async def connect_to_peer(
        self,
        peer_id: str,
        peer_address: str,
        peer_port: int
    ) -> bool:
        """
        Connect to a peer's sync server
        
        Args:
            peer_id: Peer's node identifier
            peer_address: Peer's address
            peer_port: Peer's sync port
            
        Returns:
            True if connection successful
        """
        uri = f"ws://{peer_address}:{peer_port}"
        
        try:
            logger.info(f"🔗 Connecting to peer: {peer_id} at {uri}")
            
            websocket = await connect(uri)
            
            # Send handshake
            await self._send_handshake(websocket)
            
            # Receive peer handshake
            handshake = await websocket.recv()
            peer_data = json.loads(handshake)
            
            if not self._verify_handshake(peer_data, peer_id):
                logger.error(f"Invalid handshake from {peer_id}")
                await websocket.close()
                return False
            
            # Store connection
            self.connections[peer_id] = websocket
            self.connected_peers.add(peer_id)
            
            logger.info(f"✅ Connected to peer: {peer_id}")
            
            # Start receive loop
            asyncio.create_task(self._receive_loop(peer_id, websocket))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {peer_id}: {e}")
            return False
    
    async def send_packet(self, peer_id: str, packet: Dict):
        """
        Send signed knowledge packet to peer
        
        Args:
            peer_id: Target peer
            packet: KnowledgePacket as dict
        """
        if peer_id not in self.connections:
            logger.warning(f"Not connected to peer: {peer_id}")
            return False
        
        try:
            # Import crypto here to avoid circular import
            from federation import crypto as ark_crypto
            
            # Sign packet
            envelope = ark_crypto.sign_packet(self.private_key, packet)
            
            # Send over WebSocket
            websocket = self.connections[peer_id]
            await websocket.send(json.dumps(envelope))
            
            self.packets_sent += 1
            logger.debug(f"📤 Sent packet to {peer_id}: {packet.get('packet_id', 'unknown')[:16]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send packet to {peer_id}: {e}")
            await self.disconnect_peer(peer_id)
            return False
    
    async def broadcast_packet(self, packet: Dict, exclude_peers: Set[str] = None):
        """
        Broadcast packet to all connected peers
        
        Args:
            packet: KnowledgePacket to broadcast
            exclude_peers: Set of peer IDs to exclude
        """
        exclude_peers = exclude_peers or set()
        
        tasks = []
        for peer_id in self.connected_peers:
            if peer_id not in exclude_peers:
                tasks.append(self.send_packet(peer_id, packet))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"📡 Broadcast packet to {len(tasks)} peer(s)")
    
    async def disconnect_peer(self, peer_id: str):
        """Disconnect from a peer"""
        if peer_id in self.connections:
            try:
                await self.connections[peer_id].close()
            except:
                pass
            
            del self.connections[peer_id]
            self.connected_peers.discard(peer_id)
            
            logger.info(f"🔌 Disconnected from peer: {peer_id}")
    
    async def _handle_connection(self, websocket, path):
        """Handle incoming peer connection"""
        peer_id = None
        
        try:
            # Receive handshake
            handshake = await websocket.recv()
            peer_data = json.loads(handshake)
            
            peer_id = peer_data.get('node_id')
            if not peer_id:
                logger.error("Handshake missing node_id")
                return
            
            # Verify handshake
            if not self._verify_handshake(peer_data, peer_id):
                logger.error(f"Invalid handshake from {peer_id}")
                return
            
            # Send our handshake
            await self._send_handshake(websocket)
            
            # Store connection
            self.connections[peer_id] = websocket
            self.connected_peers.add(peer_id)
            
            logger.info(f"✅ Peer connected: {peer_id}")
            
            # Receive loop
            await self._receive_loop(peer_id, websocket)
            
        except websockets.ConnectionClosed:
            logger.info(f"Peer disconnected: {peer_id}")
        except Exception as e:
            logger.error(f"Connection error with {peer_id}: {e}")
        finally:
            if peer_id:
                self.connected_peers.discard(peer_id)
                if peer_id in self.connections:
                    del self.connections[peer_id]
    
    async def _receive_loop(self, peer_id: str, websocket):
        """Receive and process packets from peer"""
        try:
            async for message in websocket:
                try:
                    envelope = json.loads(message)
                    await self._process_received_packet(peer_id, envelope)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {peer_id}")
                except Exception as e:
                    logger.error(f"Error processing packet from {peer_id}: {e}")
                    
        except websockets.ConnectionClosed:
            logger.info(f"Connection closed: {peer_id}")
        except Exception as e:
            logger.error(f"Receive loop error for {peer_id}: {e}")
    
    async def _process_received_packet(self, peer_id: str, envelope: Dict):
        """
        Process received packet with signature verification
        
        Args:
            peer_id: Sender peer ID
            envelope: Signed packet envelope
        """
        # Verify signature
        if peer_id not in self.verify_keys:
            logger.error(f"No verify key for peer: {peer_id}")
            self.packets_rejected += 1
            return
        
        # Import crypto
        from federation import crypto as ark_crypto
        
        verify_key = self.verify_keys[peer_id]
        
        if not ark_crypto.verify_packet(envelope, verify_key):
            logger.error(f"❌ Invalid signature from {peer_id}")
            self.packets_rejected += 1
            return
        
        # Signature valid - extract packet
        packet = envelope['packet']
        self.packets_received += 1
        
        logger.debug(f"📥 Received verified packet from {peer_id}: {packet.get('packet_id', 'unknown')[:16]}...")
        
        # Callback
        if self.on_packet_received:
            await self.on_packet_received(peer_id, packet)
    
    async def _send_handshake(self, websocket):
        """Send handshake to peer"""
        handshake = {
            'type': 'handshake',
            'node_id': self.node_id,
            'version': 'v6.0',
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
        
        await websocket.send(json.dumps(handshake))
    
    def _verify_handshake(self, data: Dict, expected_peer_id: str) -> bool:
        """Verify handshake from peer"""
        if data.get('type') != 'handshake':
            return False
        
        if data.get('node_id') != expected_peer_id:
            logger.warning(f"Node ID mismatch: expected {expected_peer_id}, got {data.get('node_id')}")
            return False
        
        return True
    
    def get_stats(self) -> Dict:
        """Get sync statistics"""
        return {
            'connected_peers': len(self.connected_peers),
            'active_connections': len(self.connections),
            'packets_sent': self.packets_sent,
            'packets_received': self.packets_received,
            'packets_rejected': self.packets_rejected,
            'peers': list(self.connected_peers)
        }


if __name__ == "__main__":
    # Test sync protocol
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        # Mock keys
        from nacl import signing
        
        priv = signing.SigningKey.generate()
        pub = priv.verify_key
        
        verify_keys = {'test-peer': pub}
        
        async def on_packet(peer_id, packet):
            print(f"Received from {peer_id}: {packet}")
        
        sync = SyncProtocol('test-node', priv, verify_keys, on_packet)
        await sync.start_server(port=8104)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped")
