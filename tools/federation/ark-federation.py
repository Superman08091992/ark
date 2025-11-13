#!/usr/bin/env python3
"""
ARK Federation Tool
Manage P2P federation network, peers, and synchronization
"""

import os
import sys
import json
import argparse
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("❌ Redis not available - install with: pip install redis")
    sys.exit(1)

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class ARKFederation:
    """ARK Federation Management Tool"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getenv('ARK_BASE_PATH', os.getcwd()))
        self.keys_dir = self.base_path / "keys"
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = None
    
    async def connect(self) -> bool:
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            return False
    
    async def list_peers(self):
        """List all federation peers"""
        if not await self.connect():
            return
        
        print("\n🌐 Federation Peers\n" + "="*100)
        
        peers = []
        peer_count = 0
        
        async for key in self.redis.scan_iter(match="peer:*"):
            peer_count += 1
            peer_data = await self.redis.hgetall(key)
            
            peer_id = key.replace("peer:", "")
            print(f"Peer {peer_count}: {peer_id[:16]}... - {peer_data.get('host', 'N/A')}")
        
        print(f"\n📊 Total Peers: {peer_count}")
    
    async def add_peer(self, peer_id: str, host: str, port: int, trust_tier: str = "unverified"):
        """Add a new peer"""
        if not await self.connect():
            return
        
        peer_key = f"peer:{peer_id}"
        
        peer_data = {
            "peer_id": peer_id,
            "host": host,
            "port": str(port),
            "status": "active",
            "trust_tier": trust_tier,
            "added_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
        }
        
        await self.redis.hset(peer_key, mapping=peer_data)
        
        print(f"✅ Peer added: {peer_id}")
        print(f"   Host: {host}:{port}")
        print(f"   Trust: {trust_tier}")
    
    def generate_keys(self):
        """Generate new federation key pair"""
        if not CRYPTO_AVAILABLE:
            print("❌ Cryptography library not available")
            return
        
        print("\n🔑 Generating Federation Keys\n" + "="*80)
        
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        
        private_key_path = self.keys_dir / "federation_private.pem"
        public_key_path = self.keys_dir / "federation_public.pem"
        
        private_key_path.write_bytes(private_pem)
        public_key_path.write_bytes(public_pem)
        
        private_key_path.chmod(0o600)
        public_key_path.chmod(0o644)
        
        print(f"✅ Keys generated successfully")
        print(f"   Private: {private_key_path}")
        print(f"   Public:  {public_key_path}")


async def main():
    parser = argparse.ArgumentParser(description="ARK Federation Management Tool")
    parser.add_argument('command', choices=['peers', 'add', 'genkeys'])
    parser.add_argument('args', nargs='*')
    parser.add_argument('--base-path', type=str)
    
    args = parser.parse_args()
    fed = ARKFederation(base_path=args.base_path)
    
    if args.command == 'peers':
        await fed.list_peers()
    elif args.command == 'add':
        if len(args.args) < 3:
            print("Usage: add <peer_id> <host> <port>")
            sys.exit(1)
        await fed.add_peer(args.args[0], args.args[1], int(args.args[2]))
    elif args.command == 'genkeys':
        fed.generate_keys()


if __name__ == "__main__":
    asyncio.run(main())
