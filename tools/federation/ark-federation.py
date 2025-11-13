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
from tabulate import tabulate

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
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
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
            
            peers.append([
                peer_id[:16] + "...",
                peer_data.get('host', 'N/A'),
                peer_data.get('port', 'N/A'),
                peer_data.get('status', 'unknown'),
                peer_data.get('last_seen', 'never'),
                peer_data.get('trust_tier', 'unverified'),
            ])
        
        if not peers:
            print("No peers found in federation network")
            return
        
        print(tabulate(peers,
                      headers=['Peer ID', 'Host', 'Port', 'Status', 'Last Seen', 'Trust'],
                      tablefmt='grid'))
        
        print(f"\n📊 Total Peers: {peer_count}")
    
    async def peer_info(self, peer_id: str):
        """Show detailed peer information"""
        if not await self.connect():
            return
        
        peer_key = f"peer:{peer_id}"
        peer_data = await self.redis.hgetall(peer_key)
        
        if not peer_data:
            print(f"❌ Peer not found: {peer_id}")
            return
        
        print(f"\n🔗 Peer Information: {peer_id}\n" + "="*80)
        
        for field, value in sorted(peer_data.items()):
            print(f"  {field:20s}: {value}")
    
    async def add_peer(self, peer_id: str, host: str, port: int, trust_tier: str = "unverified"):
        """Add a new peer"""
        if not await self.connect():
            return
        
        peer_key = f"peer:{peer_id}"
        
        # Check if peer already exists
        exists = await self.redis.exists(peer_key)
        if exists:
            print(f"⚠️  Peer {peer_id} already exists")
            response = input("Update existing peer? (y/n): ")
            if response.lower() != 'y':
                return
        
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
    
    async def remove_peer(self, peer_id: str):
        """Remove a peer"""
        if not await self.connect():
            return
        
        peer_key = f"peer:{peer_id}"
        
        # Check if peer exists
        exists = await self.redis.exists(peer_key)
        if not exists:
            print(f"❌ Peer not found: {peer_id}")
            return
        
        # Get peer info before deleting
        peer_data = await self.redis.hgetall(peer_key)
        
        print(f"\n⚠️  Removing peer: {peer_id}")
        print(f"   Host: {peer_data.get('host')}:{peer_data.get('port')}")
        
        response = input("Confirm removal? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cancelled")
            return
        
        await self.redis.delete(peer_key)
        print(f"✅ Peer removed: {peer_id}")
    
    async def update_trust(self, peer_id: str, trust_tier: str):
        """Update peer trust tier"""
        if not await self.connect():
            return
        
        valid_tiers = ['core', 'trusted', 'verified', 'unverified']
        if trust_tier not in valid_tiers:
            print(f"❌ Invalid trust tier. Must be one of: {', '.join(valid_tiers)}")
            return
        
        peer_key = f"peer:{peer_id}"
        
        exists = await self.redis.exists(peer_key)
        if not exists:
            print(f"❌ Peer not found: {peer_id}")
            return
        
        await self.redis.hset(peer_key, "trust_tier", trust_tier)
        print(f"✅ Updated trust tier for {peer_id} to: {trust_tier}")
    
    async def network_stats(self):
        """Show network statistics"""
        if not await self.connect():
            return
        
        print("\n📊 Federation Network Statistics\n" + "="*80)
        
        # Count peers
        peer_count = 0
        async for _ in self.redis.scan_iter(match="peer:*"):
            peer_count += 1
        
        # Count sync events
        sync_count = 0
        async for _ in self.redis.scan_iter(match="sync:*"):
            sync_count += 1
        
        # Trust tier distribution
        trust_tiers = {"core": 0, "trusted": 0, "verified": 0, "unverified": 0}
        
        async for key in self.redis.scan_iter(match="peer:*"):
            peer_data = await self.redis.hgetall(key)
            tier = peer_data.get('trust_tier', 'unverified')
            if tier in trust_tiers:
                trust_tiers[tier] += 1
        
        # Redis info
        info = await self.redis.info()
        
        print(f"  Total Peers:          {peer_count}")
        print(f"  Sync Events:          {sync_count}")
        print(f"\n  Trust Distribution:")
        print(f"    Core:               {trust_tiers['core']}")
        print(f"    Trusted:            {trust_tiers['trusted']}")
        print(f"    Verified:           {trust_tiers['verified']}")
        print(f"    Unverified:         {trust_tiers['unverified']}")
        
        print(f"\n  Redis:")
        print(f"    Connected Clients:  {info.get('connected_clients', 0)}")
        print(f"    Total Keys:         {await self.redis.dbsize()}")
        print(f"    Memory Used:        {info.get('used_memory_human', 'N/A')}")
    
    async def sync_status(self):
        """Show synchronization status"""
        if not await self.connect():
            return
        
        print("\n🔄 Synchronization Status\n" + "="*100)
        
        syncs = []
        
        async for key in self.redis.scan_iter(match="sync:*"):
            sync_data = await self.redis.hgetall(key)
            
            sync_id = key.replace("sync:", "")
            
            syncs.append([
                sync_id[:16] + "...",
                sync_data.get('peer_id', 'N/A')[:16] + "...",
                sync_data.get('status', 'unknown'),
                sync_data.get('timestamp', 'N/A'),
                sync_data.get('blocks_synced', '0'),
            ])
        
        if not syncs:
            print("No active synchronizations")
            return
        
        print(tabulate(syncs,
                      headers=['Sync ID', 'Peer ID', 'Status', 'Timestamp', 'Blocks'],
                      tablefmt='grid'))
    
    def generate_keys(self):
        """Generate new federation key pair"""
        if not CRYPTO_AVAILABLE:
            print("❌ Cryptography library not available")
            print("   Install with: pip install cryptography")
            return
        
        print("\n🔑 Generating Federation Keys\n" + "="*80)
        
        # Generate Ed25519 key pair
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Create keys directory
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        
        # Save keys
        private_key_path = self.keys_dir / "federation_private.pem"
        public_key_path = self.keys_dir / "federation_public.pem"
        
        # Check if keys already exist
        if private_key_path.exists() or public_key_path.exists():
            print("⚠️  Keys already exist!")
            response = input("Overwrite existing keys? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cancelled")
                return
        
        private_key_path.write_bytes(private_pem)
        public_key_path.write_bytes(public_pem)
        
        # Set permissions (owner read/write only for private key)
        private_key_path.chmod(0o600)
        public_key_path.chmod(0o644)
        
        print(f"✅ Keys generated successfully")
        print(f"   Private: {private_key_path}")
        print(f"   Public:  {public_key_path}")
        print(f"\n⚠️  Keep your private key secure!")
    
    def show_keys(self):
        """Show current federation keys"""
        print("\n🔑 Federation Keys\n" + "="*80)
        
        private_key_path = self.keys_dir / "federation_private.pem"
        public_key_path = self.keys_dir / "federation_public.pem"
        
        if private_key_path.exists():
            print(f"✅ Private Key: {private_key_path}")
            print(f"   Size: {private_key_path.stat().st_size} bytes")
            print(f"   Permissions: {oct(private_key_path.stat().st_mode)[-3:]}")
        else:
            print(f"❌ Private Key: Not found")
        
        if public_key_path.exists():
            print(f"\n✅ Public Key: {public_key_path}")
            print(f"   Size: {public_key_path.stat().st_size} bytes")
            print(f"\n   Public Key (PEM):")
            print(f"   {'-'*76}")
            print(public_key_path.read_text())
        else:
            print(f"\n❌ Public Key: Not found")


async def main():
    parser = argparse.ArgumentParser(
        description="ARK Federation Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s peers                              - List all peers
  %(prog)s info <peer_id>                     - Show peer details
  %(prog)s add <peer_id> <host> <port>        - Add new peer
  %(prog)s remove <peer_id>                   - Remove peer
  %(prog)s trust <peer_id> <tier>             - Update peer trust
  %(prog)s stats                              - Show network statistics
  %(prog)s sync                               - Show sync status
  %(prog)s genkeys                            - Generate key pair
  %(prog)s keys                               - Show current keys
        """
    )
    
    parser.add_argument('command', choices=[
        'peers', 'info', 'add', 'remove', 'trust', 'stats', 'sync', 'genkeys', 'keys'
    ], help='Command to execute')
    
    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('--base-path', type=str, help='ARK base path')
    
    args = parser.parse_args()
    
    fed = ARKFederation(base_path=args.base_path)
    
    try:
        if args.command == 'peers':
            await fed.list_peers()
        
        elif args.command == 'info':
            if not args.args:
                print("❌ Peer ID required")
                sys.exit(1)
            await fed.peer_info(args.args[0])
        
        elif args.command == 'add':
            if len(args.args) < 3:
                print("❌ Usage: add <peer_id> <host> <port> [trust_tier]")
                sys.exit(1)
            peer_id, host, port = args.args[0], args.args[1], int(args.args[2])
            trust_tier = args.args[3] if len(args.args) > 3 else "unverified"
            await fed.add_peer(peer_id, host, port, trust_tier)
        
        elif args.command == 'remove':
            if not args.args:
                print("❌ Peer ID required")
                sys.exit(1)
            await fed.remove_peer(args.args[0])
        
        elif args.command == 'trust':
            if len(args.args) < 2:
                print("❌ Usage: trust <peer_id> <tier>")
                print("   Valid tiers: core, trusted, verified, unverified")
                sys.exit(1)
            await fed.update_trust(args.args[0], args.args[1])
        
        elif args.command == 'stats':
            await fed.network_stats()
        
        elif args.command == 'sync':
            await fed.sync_status()
        
        elif args.command == 'genkeys':
            fed.generate_keys()
        
        elif args.command == 'keys':
            fed.show_keys()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
