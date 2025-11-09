# ARK Code Lattice Federation Guide

## 🌐 Overview

The ARK Code Lattice Federation system enables **distributed autonomous development** across multiple ARK instances running on:
- **Local machines** (development workstations)
- **Cloud servers** (AWS, Azure, GCP)
- **Edge devices** (Raspberry Pi, IoT devices)

This guide covers **two federation implementations**:

1. **Node.js Federation** - Simple P2P with HTTP sync (built-in)
2. **Python/FastAPI Federation** - Advanced with Redis, cryptographic signatures, and delta sync

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Node.js Federation (Built-in)](#nodejs-federation-built-in)
3. [Python Federation Service (Advanced)](#python-federation-service-advanced)
4. [Setup Instructions](#setup-instructions)
5. [CLI Commands](#cli-commands)
6. [API Reference](#api-reference)
7. [Multi-Instance Scenarios](#multi-instance-scenarios)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Federation Topologies

**1. Pure Peer-to-Peer (P2P)**
```
┌──────────┐         ┌──────────┐
│  Local   │◄───────►│  Cloud   │
│  ARK-1   │         │  ARK-2   │
└────┬─────┘         └────┬─────┘
     │                    │
     └──────────┬─────────┘
                ▼
          ┌──────────┐
          │   Pi     │
          │  ARK-3   │
          └──────────┘
```

**2. Hub-and-Spoke**
```
       ┌──────────────┐
       │  Cloud Hub   │
       │    ARK-H     │
       └──────┬───────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│Local-1│ │Local-2│ │  Pi   │
│ ARK-1 │ │ ARK-2 │ │ ARK-3 │
└───────┘ └───────┘ └───────┘
```

**3. Hybrid (Recommended)**
```
       ┌──────────────┐
       │  Cloud Hub   │◄──── Optional central registry
       │    ARK-H     │
       └──────┬───────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│Local-1│◄┼►│Local-2│◄┼►│  Pi   │
│ ARK-1 │ │ │ ARK-2 │ │ │ ARK-3 │
└───────┘ │ └───────┘ │ └───────┘
          └───────────┘
      Direct P2P connections
```

### Key Concepts

**Node**: A single ARK instance with its own Code Lattice database

**Peer**: Another ARK instance that this node can sync with

**Sync**: Bidirectional exchange of Code Lattice nodes

**Conflict Resolution**: Last-Write-Wins with deterministic tiebreaker

**Discovery**: Automatic detection of peers on local network

---

## Node.js Federation (Built-in)

### Features

✅ **Zero Dependencies** - Built into ARK backend  
✅ **HTTP-based** - Simple REST API  
✅ **Auto-sync** - Configurable periodic synchronization  
✅ **Peer Discovery** - Automatic local network scanning  
✅ **Conflict Resolution** - Timestamp-based with instance ID tiebreaker  
✅ **State Persistence** - JSON-based configuration storage  

### How It Works

1. **Instance Identification**
   ```javascript
   instanceId = SHA256(hostname + timestamp)
   instanceType = 'local' | 'cloud' | 'pi'
   instanceName = 'ARK-{type}-{id}'
   ```

2. **Synchronization Protocol**
   ```
   Node A                           Node B
      │                                │
      ├──► GET /federation/nodes ─────►│
      │                                │
      │◄─── {nodes: [...]} ────────────┤
      │                                │
      ├──► POST /federation/sync ─────►│
      │     {nodes: [...]}             │
      │                                │
      │◄─── {received: N} ─────────────┤
   ```

3. **Conflict Resolution**
   ```javascript
   if (incoming.timestamp > existing.timestamp) {
     accept_incoming()
   } else if (incoming.timestamp < existing.timestamp) {
     keep_existing()
   } else {
     // Timestamps equal - use instance ID
     if (sourceInstanceId > localInstanceId) {
       accept_incoming()
     } else {
       keep_existing()
     }
   }
   ```

### Environment Variables

```bash
# Instance configuration
export ARK_INSTANCE_TYPE=local          # local, cloud, or pi
export FEDERATION_PORT=9000             # Federation server port
export FEDERATION_MODE=p2p              # p2p or hub

# Hub configuration (hub mode only)
export FEDERATION_HUB_URL=http://hub.example.com:9000

# Sync configuration
export FEDERATION_AUTO_SYNC=true        # Enable auto-sync
export FEDERATION_SYNC_INTERVAL=60000   # Sync every 60 seconds
```

### Backend Integration

The Node.js federation is automatically available when the ARK backend starts. It initializes on first API call and uses the backend's configuration.

---

## Python Federation Service (Advanced)

### Features

✅ **Redis-backed** - Fast distributed state  
✅ **Cryptographic Signatures** - Ed25519 verification  
✅ **Delta Sync** - Only transfer changed nodes  
✅ **TTL-based Discovery** - Automatic peer expiration  
✅ **Manifest Hashing** - Content-based change detection  
✅ **Production-ready** - FastAPI + Uvicorn  

### Architecture

```
┌──────────────────────────────────────────┐
│       Python Federation Service          │
│  ┌────────────┐      ┌────────────┐     │
│  │  FastAPI   │─────►│   Redis    │     │
│  │  Uvicorn   │      │  Key-Value │     │
│  └────────────┘      └────────────┘     │
│         │                    │           │
│    ┌────▼────────────────────▼────┐     │
│    │   Lattice Data Directory     │     │
│    │   • manifest.json            │     │
│    │   • node-123.json            │     │
│    │   • node-456.json            │     │
│    └──────────────────────────────┘     │
└──────────────────────────────────────────┘
```

### Setup

1. **Install Dependencies**
   ```bash
   cd /home/user/webapp
   pip3 install -r federation-requirements.txt
   ```

2. **Start Redis**
   ```bash
   # Using Docker (recommended)
   docker run -d -p 6379:6379 redis:alpine
   
   # Or install locally
   sudo apt install redis-server
   redis-server
   ```

3. **Generate Ed25519 Keys**
   ```python
   from nacl.signing import SigningKey
   import base64
   
   # Generate keypair
   signing_key = SigningKey.generate()
   verify_key = signing_key.verify_key
   
   print("Private Key:", base64.b64encode(bytes(signing_key)).decode())
   print("Public Key:", base64.b64encode(bytes(verify_key)).decode())
   ```

4. **Configure Environment**
   ```bash
   export ARK_NODE_ID=ark-node-local
   export ARK_FED_PUBKEY=<base64-encoded-public-key>
   export REDIS_URL=redis://localhost:6379/0
   export LATTICE_PATH=./lattice_data
   export FEDERATION_PORT=9001
   ```

5. **Start Service**
   ```bash
   python3 ark-federation-service.py
   # Or with uvicorn directly:
   uvicorn ark-federation-service:app --host 0.0.0.0 --port 9001
   ```

### API Endpoints

**GET /discover**
```bash
curl http://localhost:9001/discover
# Response: {"peers": [...], "count": N}
```

**POST /manifest**
```bash
curl -X POST http://localhost:9001/manifest \
  -H "Content-Type: application/json" \
  -d '{
    "manifest": {"node_id": "ark-1", "nodes": [...]},
    "signature": "...",
    "pubkey": "..."
  }'
# Response: {"status": "registered", "node_id": "ark-1"}
```

**POST /sync**
```bash
curl -X POST http://localhost:9001/sync \
  -H "Content-Type: application/json" \
  -d '{
    "manifest_hash": "abc123",
    "nodes": [
      {"id": "node-1", "hash": "def456"},
      {"id": "node-2", "hash": "ghi789"}
    ]
  }'
# Response: {"delta_count": 3, "nodes": [...]}
```

### Manifest Structure

```json
{
  "node_id": "ark-node-local",
  "instance_type": "local",
  "version": "1.0.0",
  "last_updated": 1699564800,
  "nodes": [
    {
      "id": "python_flask_basic",
      "type": "framework_node",
      "hash": "sha256:abc123...",
      "updated_at": 1699564700
    },
    {
      "id": "react_component_form",
      "type": "component_node",
      "hash": "sha256:def456...",
      "updated_at": 1699564750
    }
  ]
}
```

### Signature Generation

```python
import json, base64
from nacl.signing import SigningKey

# Load or generate signing key
signing_key = SigningKey.from_seed(base64.b64decode(private_key_b64))

# Create manifest
manifest = {
    "node_id": "ark-1",
    "nodes": [...]
}

# Sign manifest
payload = json.dumps(manifest, sort_keys=True).encode()
signed = signing_key.sign(payload)
signature = base64.b64encode(signed.signature).decode()

# Send to federation
data = {
    "manifest": manifest,
    "signature": signature,
    "pubkey": base64.b64encode(bytes(signing_key.verify_key)).decode()
}
```

---

## Setup Instructions

### Quick Start: Local Development

1. **Start ARK Backend** (includes Node.js federation)
   ```bash
   cd /home/user/webapp
   node intelligent-backend.cjs
   ```

2. **Start Federation Server**
   ```bash
   ./bin/ark-lattice federation start
   ```

3. **Check Status**
   ```bash
   ./bin/ark-lattice federation status
   ```

### Multi-Instance Setup

#### Scenario 1: Local + Cloud

**Local Machine:**
```bash
# Terminal 1 - Backend
export ARK_INSTANCE_TYPE=local
export FEDERATION_PORT=9000
node intelligent-backend.cjs

# Terminal 2 - Start federation
./bin/ark-lattice federation start
```

**Cloud Server:**
```bash
# Terminal 1 - Backend
export ARK_INSTANCE_TYPE=cloud
export FEDERATION_PORT=9000
node intelligent-backend.cjs

# Terminal 2 - Start federation & add local peer
./bin/ark-lattice federation start
./bin/ark-lattice federation add-peer http://your-local-ip:9000
```

**Back on Local:**
```bash
# Add cloud peer
./bin/ark-lattice federation add-peer http://cloud-server-ip:9000

# Sync
./bin/ark-lattice federation sync
```

#### Scenario 2: Hub with Multiple Spokes

**Cloud Hub:**
```bash
export ARK_INSTANCE_TYPE=cloud
export FEDERATION_MODE=hub
export FEDERATION_PORT=9000
node intelligent-backend.cjs
./bin/ark-lattice federation start
```

**Local Spoke 1:**
```bash
export ARK_INSTANCE_TYPE=local
export FEDERATION_MODE=hub
export FEDERATION_HUB_URL=http://hub-ip:9000
node intelligent-backend.cjs
./bin/ark-lattice federation start
```

**Raspberry Pi Spoke 2:**
```bash
export ARK_INSTANCE_TYPE=pi
export FEDERATION_MODE=hub
export FEDERATION_HUB_URL=http://hub-ip:9000
node intelligent-backend.cjs
./bin/ark-lattice federation start
```

#### Scenario 3: Hybrid P2P + Hub

```bash
# Each node configures both hub and direct peers
export FEDERATION_MODE=p2p
export FEDERATION_HUB_URL=http://hub-ip:9000  # Optional registry

# Add direct P2P connections
./bin/ark-lattice federation add-peer http://peer1:9000
./bin/ark-lattice federation add-peer http://peer2:9000
```

---

## CLI Commands

### Federation Management

**Start Federation Server**
```bash
./bin/ark-lattice federation start
# Output: Federation server started on port 9000
```

**Stop Federation Server**
```bash
./bin/ark-lattice federation stop
```

**Check Status**
```bash
./bin/ark-lattice federation status
# Shows: instance info, peers, stats, sync status
```

### Peer Management

**Add Peer**
```bash
./bin/ark-lattice federation add-peer http://192.168.1.100:9000
```

**Remove Peer**
```bash
./bin/ark-lattice federation remove-peer http://192.168.1.100:9000
```

**List Peers**
```bash
./bin/ark-lattice federation list-peers
# Shows: all configured peers with active status
```

**Discover Peers**
```bash
./bin/ark-lattice federation discover
# Scans local network for ARK instances
```

### Synchronization

**Manual Sync (All Peers)**
```bash
./bin/ark-lattice federation sync
```

**Sync with Specific Peer**
```bash
./bin/ark-lattice federation sync --peer http://192.168.1.100:9000
```

**Enable Auto-Sync**
```bash
./bin/ark-lattice federation auto-sync --start
```

**Disable Auto-Sync**
```bash
./bin/ark-lattice federation auto-sync --stop
```

---

## API Reference

### Backend API Endpoints

All endpoints are available at `http://localhost:8000/api/federation/`

#### GET /api/federation/status

Get federation status and statistics.

**Response:**
```json
{
  "status": "ok",
  "info": {
    "instanceId": "abc123...",
    "instanceName": "ARK-local-abc123",
    "instanceType": "local",
    "federationMode": "p2p",
    "listenPort": 9000,
    "autoSync": true,
    "syncInterval": 60000,
    "peers": ["http://192.168.1.100:9000"]
  },
  "isRunning": true,
  "activePeers": ["http://192.168.1.100:9000"],
  "stats": {
    "totalSyncs": 42,
    "nodesSent": 150,
    "nodesReceived": 203,
    "conflictsResolved": 5
  }
}
```

#### POST /api/federation/start

Start the federation server.

**Response:**
```json
{
  "status": "started",
  "port": 9000,
  "instanceId": "abc123...",
  "instanceName": "ARK-local-abc123"
}
```

#### POST /api/federation/stop

Stop the federation server.

#### POST /api/federation/peers/add

Add a peer.

**Request:**
```json
{
  "peerUrl": "http://192.168.1.100:9000"
}
```

**Response:**
```json
{
  "status": "added",
  "peerUrl": "http://192.168.1.100:9000",
  "totalPeers": 3
}
```

#### DELETE /api/federation/peers/:url

Remove a peer (URL-encoded).

#### GET /api/federation/peers

List all configured peers.

#### POST /api/federation/sync

Trigger manual synchronization.

**Request (optional):**
```json
{
  "peerUrl": "http://192.168.1.100:9000"
}
```

**Response:**
```json
{
  "status": "synced",
  "result": [
    {
      "peer": "http://192.168.1.100:9000",
      "success": true,
      "nodesSent": 15,
      "nodesReceived": 23
    }
  ]
}
```

#### POST /api/federation/discover

Discover peers on local network.

#### POST /api/federation/auto-sync/start

Enable automatic synchronization.

#### POST /api/federation/auto-sync/stop

Disable automatic synchronization.

---

## Multi-Instance Scenarios

### Scenario 1: Developer Laptop + Cloud Server

**Use Case:** Develop locally, test/deploy on cloud

**Setup:**
1. Local machine runs ARK with federation on port 9000
2. Cloud server runs ARK with federation on port 9000
3. Add each other as peers
4. Enable auto-sync (60s interval)

**Workflow:**
```bash
# Local: Add new security nodes
./bin/ark-lattice import security-pentesting-nodes.json

# Auto-sync will push to cloud within 60s
# OR manually sync:
./bin/ark-lattice federation sync

# Cloud now has security nodes available
# Cloud Kenny can generate pentesting code
```

### Scenario 2: Office Network with Multiple Developers

**Use Case:** Team shares node library improvements

**Setup:**
1. Each developer's machine runs ARK
2. Use peer discovery to find team members
3. Enable auto-sync
4. Optional: Cloud hub for remote workers

**Workflow:**
```bash
# Developer A discovers team
./bin/ark-lattice federation discover
# Finds: Developer B (192.168.1.50:9000), Developer C (192.168.1.51:9000)

# Auto-add discovered peers
./bin/ark-lattice federation add-peer http://192.168.1.50:9000
./bin/ark-lattice federation add-peer http://192.168.1.51:9000

# Enable auto-sync
./bin/ark-lattice federation auto-sync --start

# Developer A adds new React hooks
# Automatically syncs to B and C
```

### Scenario 3: Edge Computing with Raspberry Pi

**Use Case:** Deploy to edge devices with limited connectivity

**Setup:**
1. Cloud hub maintains master node library
2. Raspberry Pi devices connect when online
3. Sync on connection, work offline
4. Periodic sync back to hub

**Workflow:**
```bash
# Raspberry Pi (home automation project)
export ARK_INSTANCE_TYPE=pi
export FEDERATION_HUB_URL=http://cloud-hub:9000

# Start ARK
node intelligent-backend.cjs &
./bin/ark-lattice federation start

# Initial sync from hub
./bin/ark-lattice federation sync

# Work offline with local nodes
# Kenny generates Python IoT code using local lattice

# Later: Sync improvements back to hub
./bin/ark-lattice federation sync
```

### Scenario 4: Multi-Region Deployment

**Use Case:** Global team with regional hubs

**Architecture:**
```
        ┌─────────┐
        │ US Hub  │
        └────┬────┘
             │
    ┌────────┼────────┐
    │        │        │
┌───▼───┐ ┌──▼──┐ ┌──▼───┐
│ EU Hub│ │ AP  │ │ Local│
└───┬───┘ │ Hub │ │ Devs │
    │     └──┬──┘ └──────┘
┌───▼───┐ ┌──▼──┐
│ Local │ │Local│
│ Devs  │ │Devs │
└───────┘ └─────┘
```

**Setup:**
```bash
# US Hub (Primary)
export FEDERATION_MODE=hub
export FEDERATION_PORT=9000

# EU Hub (Secondary)
export FEDERATION_MODE=p2p
export FEDERATION_HUB_URL=http://us-hub:9000
./bin/ark-lattice federation add-peer http://us-hub:9000
./bin/ark-lattice federation add-peer http://ap-hub:9000

# Regional developers point to nearest hub
export FEDERATION_HUB_URL=http://eu-hub:9000
```

---

## Security Considerations

### Node.js Federation (Built-in)

**Security Level:** Basic (suitable for trusted networks)

**Risks:**
- ❌ No authentication
- ❌ No encryption (HTTP only)
- ❌ No signature verification
- ⚠️ Vulnerable to MITM attacks

**Mitigations:**
1. Use VPN or private networks
2. Implement firewall rules
3. Use HTTPS reverse proxy (nginx/caddy)
4. Restrict peers to known IP addresses

**Example: HTTPS Proxy with Nginx**
```nginx
server {
    listen 443 ssl;
    server_name ark-federation.local;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:9000;
        proxy_set_header Host $host;
    }
}
```

### Python Federation Service (Advanced)

**Security Level:** Production-ready

**Features:**
- ✅ Ed25519 cryptographic signatures
- ✅ Manifest integrity verification
- ✅ Peer authentication via public keys
- ✅ Redis ACL support
- ✅ TTL-based peer expiration

**Best Practices:**

1. **Key Management**
   ```bash
   # Generate keys on each node
   python3 -c "
   from nacl.signing import SigningKey
   import base64
   sk = SigningKey.generate()
   print('Private:', base64.b64encode(bytes(sk)).decode())
   print('Public:', base64.b64encode(bytes(sk.verify_key)).decode())
   "
   
   # Store private key securely
   export ARK_FED_PRIVKEY="<private-key>"
   chmod 600 ~/.ark_federation_key
   ```

2. **Redis Security**
   ```bash
   # Use password authentication
   redis-cli CONFIG SET requirepass "strong-password"
   export REDIS_URL="redis://:strong-password@localhost:6379/0"
   
   # Or use Redis ACL
   redis-cli ACL SETUSER arkfed on >password ~peer:* +get +set +hset +hgetall
   ```

3. **Network Isolation**
   ```bash
   # Bind Redis to localhost only
   redis-server --bind 127.0.0.1
   
   # Use SSH tunnels for remote access
   ssh -L 6379:localhost:6379 user@remote-server
   ```

4. **HTTPS/TLS**
   ```bash
   # Use uvicorn with SSL
   uvicorn ark-federation-service:app \
     --host 0.0.0.0 \
     --port 9001 \
     --ssl-keyfile /path/to/key.pem \
     --ssl-certfile /path/to/cert.pem
   ```

---

## Troubleshooting

### Common Issues

**1. Federation server won't start**

```bash
# Check if port is already in use
lsof -i :9000

# Use different port
export FEDERATION_PORT=9001
./bin/ark-lattice federation start
```

**2. Peers not syncing**

```bash
# Check connectivity
curl http://peer-ip:9000/federation/info

# Check firewall
sudo ufw allow 9000/tcp

# Verify peer is added
./bin/ark-lattice federation list-peers

# Try manual sync with verbose output
./bin/ark-lattice federation sync --peer http://peer-ip:9000
```

**3. "Cannot read property of undefined" errors**

```bash
# Backend not running
node intelligent-backend.cjs &

# Wait for backend to start
sleep 2

# Then start federation
./bin/ark-lattice federation start
```

**4. Redis connection errors (Python service)**

```bash
# Check Redis is running
redis-cli ping
# Should respond: PONG

# Check Redis URL
echo $REDIS_URL

# Test connection
redis-cli -u $REDIS_URL ping
```

**5. Signature verification failures**

```bash
# Ensure public key matches private key
python3 -c "
from nacl.signing import SigningKey
import base64
sk = SigningKey(base64.b64decode('$ARK_FED_PRIVKEY'))
print('Public key:', base64.b64encode(bytes(sk.verify_key)).decode())
"

# Compare with ARK_FED_PUBKEY
echo $ARK_FED_PUBKEY
```

### Debug Mode

**Node.js Federation:**
```bash
# Enable debug logging
export DEBUG=ark:federation
node intelligent-backend.cjs
```

**Python Federation:**
```bash
# Uvicorn debug mode
uvicorn ark-federation-service:app --reload --log-level debug
```

### Health Checks

**Node.js:**
```bash
# Check server health
curl http://localhost:9000/federation/info

# Expected: {"instanceId": "...", "instanceName": "...", ...}
```

**Python:**
```bash
# Check FastAPI docs
curl http://localhost:9001/docs

# Check Redis connection
curl http://localhost:9001/discover
```

---

## Performance Considerations

### Node.js Federation

**Scalability:**
- ✅ Handles 10-50 peers easily
- ⚠️ Degrades with 100+ peers (full mesh)
- 💡 Use hub-and-spoke for large deployments

**Optimization:**
```javascript
// Adjust sync interval based on network
export FEDERATION_SYNC_INTERVAL=300000  // 5 minutes for slow networks
export FEDERATION_SYNC_INTERVAL=30000   // 30 seconds for fast networks
```

### Python Federation

**Scalability:**
- ✅ Handles 100s of peers with Redis
- ✅ Delta sync reduces bandwidth
- ✅ Manifest hashing avoids redundant transfers

**Redis Tuning:**
```bash
# Increase max memory
redis-cli CONFIG SET maxmemory 512mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Adjust TTL based on network reliability
# In ark-federation-service.py, line 87:
r.expire(f"peer:{node_id}", 300)  # 5 minutes for unstable networks
```

---

## Monitoring and Metrics

### Node.js Federation Stats

```bash
# View detailed statistics
./bin/ark-lattice federation status

# Outputs:
# - Total syncs performed
# - Nodes sent/received
# - Conflicts resolved
# - Active peers count
# - Last sync timestamps
```

### Python Federation Metrics

**Redis Monitoring:**
```bash
# Monitor Redis commands
redis-cli MONITOR

# Get stats
redis-cli INFO stats

# Check peer count
redis-cli KEYS "peer:*" | wc -l
```

**Application Metrics:**
```python
# Add to ark-federation-service.py
from fastapi import FastAPI
import time

app = FastAPI()

@app.get("/metrics")
def metrics():
    return {
        "uptime": time.time() - app.state.start_time,
        "peers": r.dbsize(),
        "sync_count": r.get("sync_counter") or 0
    }
```

---

## Advanced Topics

### Custom Sync Strategies

**Selective Sync:** Only sync specific node types
```javascript
// In lattice-federation.cjs
async syncWithPeer(peerUrl, options = {}) {
  const { nodeTypes = null } = options;
  
  let nodes = await this.getNodesSince(lastSync);
  
  if (nodeTypes) {
    nodes = nodes.filter(n => nodeTypes.includes(n.type));
  }
  
  // ... rest of sync logic
}
```

**Priority Sync:** Sync important nodes first
```javascript
nodes.sort((a, b) => {
  const priorityA = a.priority || 0;
  const priorityB = b.priority || 0;
  return priorityB - priorityA;
});
```

### Event Hooks

```javascript
// Subscribe to federation events
const federation = getFederation();

federation.on('peer-added', (peer) => {
  console.log(`New peer: ${peer}`);
});

federation.on('sync-complete', (stats) => {
  console.log(`Synced: ${stats.nodesReceived} received, ${stats.nodesSent} sent`);
});

federation.on('conflict-resolved', (conflict) => {
  console.log(`Resolved conflict for node: ${conflict.nodeId}`);
});
```

---

## Roadmap

### Planned Features

**Phase 4 (Q1 2024):**
- [ ] WebSocket-based real-time sync
- [ ] Merkle tree for efficient delta detection
- [ ] Distributed hash table (DHT) for peer discovery
- [ ] Built-in NAT traversal (STUN/TURN)

**Phase 5 (Q2 2024):**
- [ ] Blockchain-based node provenance
- [ ] Multi-signature node approval workflows
- [ ] Federated machine learning for node recommendations
- [ ] GraphQL API for federation

**Phase 6 (Q3 2024):**
- [ ] Mobile app for federation management
- [ ] Browser extension for node sharing
- [ ] Integration with IPFS for content-addressed storage
- [ ] Zero-knowledge proofs for private node sharing

---

## Contributing

To contribute to ARK Federation:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

**Areas for contribution:**
- Additional conflict resolution strategies
- Performance optimizations
- Security enhancements
- Documentation improvements
- Multi-language federation clients

---

## License

ARK Code Lattice Federation is part of the ARK project.

---

## Support

**Issues:** Report bugs on GitHub  
**Discussions:** Join ARK Discord  
**Documentation:** https://github.com/ark-project/docs  

---

**Last Updated:** 2024-11-09  
**Version:** 1.0.0  
**Author:** Jimmy <jimmy@ark-project.local>
