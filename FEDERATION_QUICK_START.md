# ARK Federation - Quick Start Guide

**⚡ 5-Minute Setup for Distributed ARK Instances**

---

## 🎯 What You'll Achieve

After following this guide, you'll have multiple ARK instances (local, cloud, Pi) sharing Code Lattice nodes automatically.

---

## 📋 Prerequisites

- ARK system installed on 2+ machines
- Network connectivity between machines
- Port 9000 accessible (or custom port)

---

## 🚀 Setup Steps

### Step 1: Start Federation on First Instance (Hub)

**On your cloud server or main machine:**

```bash
# Navigate to ARK directory
cd /home/user/webapp

# Set instance type (optional - auto-detected)
export ARK_INSTANCE_TYPE=cloud

# Start federation server
./bin/ark-lattice federation start
```

**Output:**
```
✅ Federation server started
   Instance: ARK-cloud-abc123
   Port: 9000
   Instance ID: abc123...
```

**Note the port and hostname** - you'll need these for other instances.

---

### Step 2: Start Federation on Second Instance

**On your local development machine:**

```bash
cd /home/user/webapp

# Optional: Set instance type
export ARK_INSTANCE_TYPE=local

# Start federation server
./bin/ark-lattice federation start

# Add the hub as a peer (use actual hostname/IP)
./bin/ark-lattice federation add-peer http://your-cloud-server:9000

# Enable automatic sync
./bin/ark-lattice federation auto-sync --start
```

**Output:**
```
✅ Federation server started
   Instance: ARK-local-xyz789
   Port: 9000

✅ Peer added: http://your-cloud-server:9000
   Total peers: 1

✅ Auto-sync started
   Interval: 60s
```

---

### Step 3: Start Federation on Raspberry Pi (Optional)

**On your Raspberry Pi:**

```bash
cd /home/user/webapp

# Pi instance type auto-detected if hostname contains "pi" or "raspberry"
./bin/ark-lattice federation start

# Add cloud hub as peer
./bin/ark-lattice federation add-peer http://your-cloud-server:9000

# Enable auto-sync
./bin/ark-lattice federation auto-sync --start
```

---

### Step 4: Verify Federation Status

**On any instance:**

```bash
./bin/ark-lattice federation status
```

**Expected Output:**
```
🌐 Federation Status:

   Status: ok
   Running: ✅ Yes
   Instance ID: abc123...
   Instance Name: ARK-local-xyz789
   Instance Type: local
   Mode: p2p
   Port: 9000
   Auto-sync: ✅ Enabled
   Sync Interval: 60s

📊 Statistics:
   Total Syncs: 1
   Nodes Sent: 150
   Nodes Received: 200
   Conflicts Resolved: 0

🔗 Peers:
   Total: 1
   Active: 1

   Configured Peers:
   ✅ http://your-cloud-server:9000
```

**✨ Success!** Your instances are now synchronized.

---

## 🧪 Test the Federation

### Test 1: Add a Node on Local Machine

```bash
# Add a test node
./bin/ark-lattice add \
  --id "test_federation_node" \
  --type "template_node" \
  --value "Test federation node" \
  --content "console.log('Federation works!');"
```

### Test 2: Wait for Sync (60 seconds)

```bash
# Check sync status
./bin/ark-lattice federation status
# Look for "Total Syncs" incrementing
```

### Test 3: Verify on Remote Machine

**On cloud server or Pi:**

```bash
# Query for the node
./bin/ark-lattice query --capability federation

# Or list recent nodes
./bin/ark-lattice list --limit 10
```

**✅ If you see `test_federation_node`, federation is working!**

---

## 🎛️ Common Commands

### Federation Management

```bash
# Start federation server
./bin/ark-lattice federation start

# Stop federation server
./bin/ark-lattice federation stop

# Check status
./bin/ark-lattice federation status

# Manual sync (all peers)
./bin/ark-lattice federation sync

# Manual sync (specific peer)
./bin/ark-lattice federation sync --peer http://cloud:9000
```

### Peer Management

```bash
# Add peer
./bin/ark-lattice federation add-peer http://peer:9000

# Remove peer
./bin/ark-lattice federation remove-peer http://peer:9000

# List all peers
./bin/ark-lattice federation list-peers

# Discover peers on local network
./bin/ark-lattice federation discover
```

### Auto-Sync Control

```bash
# Enable auto-sync
./bin/ark-lattice federation auto-sync --start

# Disable auto-sync
./bin/ark-lattice federation auto-sync --stop
```

---

## 🔧 Configuration

### Environment Variables

Set these before starting federation:

```bash
# Instance type (local|cloud|pi)
export ARK_INSTANCE_TYPE=cloud

# Federation mode (p2p|hub)
export FEDERATION_MODE=p2p

# Federation port (default: 9000)
export FEDERATION_PORT=9000

# Hub URL (for hub-spoke mode)
export FEDERATION_HUB_URL=http://hub.example.com:9000

# Auto-sync interval in milliseconds (default: 60000 = 60s)
export FEDERATION_SYNC_INTERVAL=30000

# Enable/disable auto-sync (default: true)
export FEDERATION_AUTO_SYNC=true

# Backend URL (for CLI commands)
export ARK_BACKEND_URL=http://localhost:8000
```

### Configuration Files

Federation automatically creates:

- `code-lattice/federation-config.json` - Persistent configuration
- `code-lattice/federation-state.json` - Sync state and statistics

**Location:** `/home/user/webapp/code-lattice/`

---

## 📊 Monitoring

### Check Statistics

```bash
./bin/ark-lattice federation status
```

**Key Metrics:**
- **Total Syncs** - Number of sync operations
- **Nodes Sent** - Nodes shared with peers
- **Nodes Received** - Nodes received from peers
- **Conflicts Resolved** - Conflicts during merge

### Check Peers

```bash
./bin/ark-lattice federation list-peers
```

**Output:**
```
🔗 Configured Peers (2):

   1. ✅ http://cloud-server:9000
   2. ⚪ http://pi-device:9000
```

**Legend:**
- ✅ = Active (recently synced)
- ⚪ = Inactive (not synced yet or offline)

---

## 🐛 Troubleshooting

### Issue: Peer shows as inactive (⚪)

**Check connectivity:**
```bash
curl http://peer-url:9000/federation/info
```

**Expected:** JSON response with instance info

**If fails:**
1. Check firewall: `sudo ufw allow 9000/tcp`
2. Check peer is running: `./bin/ark-lattice federation status` on peer
3. Check network: `ping peer-hostname`

### Issue: Port already in use

**Solution:**
```bash
export FEDERATION_PORT=9001
./bin/ark-lattice federation start
```

Federation will auto-increment port if busy.

### Issue: Nodes not syncing

**Check auto-sync:**
```bash
./bin/ark-lattice federation status
# Look for "Auto-sync: ✅ Enabled"
```

**If disabled:**
```bash
./bin/ark-lattice federation auto-sync --start
```

**Manual sync:**
```bash
./bin/ark-lattice federation sync
```

### Issue: Too many conflicts

**Reduce sync interval:**
```bash
export FEDERATION_SYNC_INTERVAL=120000  # 2 minutes
# Restart federation server
```

Or coordinate changes (have one instance make changes at a time).

---

## 🎓 Usage Scenarios

### Scenario 1: Local + Cloud Backup

**Setup:**
```bash
# On local machine
./bin/ark-lattice federation start
./bin/ark-lattice federation add-peer http://cloud:9000
./bin/ark-lattice federation auto-sync --start

# On cloud server
./bin/ark-lattice federation start
./bin/ark-lattice federation add-peer http://local:9000
./bin/ark-lattice federation auto-sync --start
```

**Benefit:** Automatic backup of all Code Lattice nodes to cloud.

### Scenario 2: Team Collaboration (P2P)

**Setup:**
```bash
# On each team member's machine
./bin/ark-lattice federation start
./bin/ark-lattice federation discover  # Auto-find team members
./bin/ark-lattice federation auto-sync --start
```

**Benefit:** Shared knowledge base across team.

### Scenario 3: Multi-Site Deployment

**Setup:**
```bash
# On cloud hub
export FEDERATION_MODE=hub
./bin/ark-lattice federation start

# On each site (local + Pi devices)
./bin/ark-lattice federation start
./bin/ark-lattice federation add-peer http://cloud-hub:9000
./bin/ark-lattice federation auto-sync --start
```

**Benefit:** Centralized coordination with edge intelligence.

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Federation server running on all instances
- [ ] Peers configured correctly
- [ ] Auto-sync enabled
- [ ] Peers showing as active (✅)
- [ ] Statistics incrementing
- [ ] Test node syncs successfully

---

## 📚 Next Steps

- Read full guide: [LATTICE_FEDERATION_GUIDE.md](LATTICE_FEDERATION_GUIDE.md)
- Check implementation: [PHASE_3_COMPLETION_REPORT.md](PHASE_3_COMPLETION_REPORT.md)
- Explore API: See backend endpoints in guide

---

## 🎉 Success!

You now have a **distributed ARK system** with automatic node synchronization!

**What this means:**
- ✅ Add nodes on any instance → available everywhere
- ✅ Work offline → sync when connected
- ✅ Automatic backups to cloud
- ✅ Team collaboration enabled
- ✅ Edge computing ready

**Enjoy distributed autonomous development! 🚀**
