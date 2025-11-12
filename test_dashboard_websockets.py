#!/usr/bin/env python3
"""
Test script for dashboard WebSocket endpoints
"""

import asyncio
import json
import websockets

async def test_federation_websocket():
    """Test federation mesh WebSocket"""
    uri = "ws://localhost:8101/ws/federation"
    print(f"🔌 Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to Federation Mesh WebSocket")
            
            # Receive initial state
            message = await websocket.recv()
            data = json.loads(message)
            print(f"\n📊 Federation Mesh Data:")
            print(f"   - Peers: {len(data.get('peers', []))}")
            print(f"   - Network Health: {data.get('network_health', 0)}%")
            print(f"   - Data Integrity: {data.get('data_integrity', 0)}%")
            print(f"   - Sync Events: {len(data.get('sync_traffic', []))}")
            
            # Send ping
            await websocket.send("ping")
            pong = await websocket.recv()
            pong_data = json.loads(pong)
            print(f"\n✅ Ping/Pong successful: {pong_data.get('type')}")
            
            return True
    except Exception as e:
        print(f"❌ Federation WebSocket error: {e}")
        return False

async def test_memory_websocket():
    """Test memory engine WebSocket"""
    uri = "ws://localhost:8101/ws/memory"
    print(f"\n🔌 Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to Memory Engine WebSocket")
            
            # Receive initial state
            message = await websocket.recv()
            data = json.loads(message)
            print(f"\n📊 Memory Engine Data:")
            print(f"   - Ingestion Rate: {data.get('ingestion_rate', 0)} mem/s")
            print(f"   - Consolidation Rate: {data.get('consolidation_rate', 0)} mem/s")
            print(f"   - Dedup Efficiency: {data.get('dedup_rate', 0)}%")
            print(f"   - Quarantine Count: {data.get('quarantine_count', 0)}")
            print(f"   - Memory Logs: {len(data.get('logs', []))}")
            
            # Send refresh request
            await websocket.send("refresh")
            refresh_data = await websocket.recv()
            print(f"\n✅ Refresh successful: received {len(refresh_data)} bytes")
            
            return True
    except Exception as e:
        print(f"❌ Memory WebSocket error: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Testing ARK Dashboard WebSocket Endpoints")
    print("=" * 60)
    
    federation_ok = await test_federation_websocket()
    memory_ok = await test_memory_websocket()
    
    print("\n" + "=" * 60)
    print("📝 Test Results:")
    print("=" * 60)
    print(f"   Federation Mesh: {'✅ PASS' if federation_ok else '❌ FAIL'}")
    print(f"   Memory Engine:   {'✅ PASS' if memory_ok else '❌ FAIL'}")
    print("=" * 60)
    
    if federation_ok and memory_ok:
        print("\n🎉 All dashboard WebSocket endpoints working correctly!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
