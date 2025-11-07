# Portable USB Node + External Host Setup

## 🎯 Architecture Overview

This setup separates concerns for optimal performance and portability:

**USB Node (Portable, Lightweight):**
- Identity/secrets vault
- Local policies
- Data persistence (memories, knowledge)
- Client interface (chat UI)
- Sync agent

**External Host (Powerful, Stationary):**
- Heavy computation (LLM inference, arkd orchestrator)
- Redis cache
- SQLite databases
- Service layer (FastAPI, Ollama)
- Network gateway (Telegram, 1true.org)

---

## 🔌 Why This Architecture?

### Problems with All-on-USB:
- ❌ USB I/O is **slow** (especially random reads/writes)
- ❌ Large models (4GB+) take **forever** to load from USB
- ❌ Limited by USB bandwidth (~40-150 MB/s USB 3.0)
- ❌ Wear on USB flash memory
- ❌ Can't leverage host GPU effectively
- ❌ Performance varies wildly between hosts

### Benefits of USB + Host Split:
- ✅ **Fast operations** (host SSD/NVMe)
- ✅ **GPU acceleration** (use host GPU)
- ✅ **Better caching** (host RAM)
- ✅ **Portable identity** (USB carries who you are)
- ✅ **Stateless host** (can run on any machine)
- ✅ **Optimal resource use** (leverage host power)

---

## 📦 What Goes Where?

### USB Node (Portable, ~8GB)

```
/ark/ (on USB)
├── identity/
│   ├── operator_id              # Your unique identity
│   ├── private_key              # Encrypted keypair
│   ├── policies.yaml            # Your personal policies
│   └── trusted_hosts.json       # Whitelist of hosts
│
├── data/ (Persistent)
│   ├── kyle_infinite_memory/    # Your memories
│   ├── knowledge_base/          # Your knowledge graph
│   ├── agent_logs/              # Conversation history
│   ├── artifacts/               # Generated files
│   └── notes/                   # Personal notes
│
├── config/
│   ├── preferences.yaml         # UI preferences
│   ├── telegram_config.yaml    # Bot pairing
│   └── sync_config.yaml         # Sync settings
│
├── client/
│   ├── ark-client               # Lightweight client binary
│   ├── ui/                      # Web UI files
│   └── sync-agent               # Background sync
│
└── cache/ (Optional)
    └── model_index.json         # Track which models you use
```

**Total Size:** ~500MB-2GB (without models)

---

### External Host (Stationary, RAM/SSD)

```
/opt/ark-host/ (on host machine)
├── bin/
│   ├── arkd                     # Orchestrator daemon
│   ├── ark-host-service         # Host service manager
│   └── ollama                   # LLM runtime
│
├── models/
│   ├── llama2.gguf              # 4GB (loaded to RAM)
│   ├── tinyllama.gguf           # 600MB (fallback)
│   └── embeddings.gguf          # 200MB
│
├── redis/
│   └── data/                    # Volatile cache
│
├── db/ (Temporary)
│   ├── session.db               # Active sessions
│   └── job_queue.db             # Job state
│
├── skills/
│   ├── system_ops/
│   ├── devops/
│   ├── data_ai/
│   └── ...                      # Skill plugins
│
└── logs/
    └── host.log                 # Host-specific logs
```

**Total Size:** ~8-20GB (with models)

---

## 🔄 Connection Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USB Node (Portable)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                │
│  │ Identity     │         │ Data         │                │
│  │ Vault        │         │ Persistence  │                │
│  │ (Encrypted)  │         │ (Memories)   │                │
│  └──────────────┘         └──────────────┘                │
│         │                        │                          │
│         └────────────┬───────────┘                          │
│                      │                                      │
│              ┌───────▼────────┐                            │
│              │  ark-client    │                            │
│              │  (Lightweight) │                            │
│              └───────┬────────┘                            │
│                      │                                      │
└──────────────────────┼──────────────────────────────────────┘
                       │
                       │ Secure Connection (TLS + mutual auth)
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 External Host (Powerful)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   arkd       │  │   Redis      │  │   Ollama     │    │
│  │ Orchestrator │  │ Cache + Queue│  │  LLM Engine  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│         │                 │                  │             │
│         └─────────────────┼──────────────────┘             │
│                           │                                │
│                  ┌────────▼────────┐                       │
│                  │    FastAPI      │                       │
│                  │  (API Server)   │                       │
│                  └────────┬────────┘                       │
│                           │                                │
└───────────────────────────┼────────────────────────────────┘
                            │
                    ┌───────┴────────┐
                    │                │
            ┌───────▼───────┐  ┌────▼──────┐
            │   Telegram    │  │ 1true.org │
            │   Gateway     │  │  Bridge   │
            └───────────────┘  └───────────┘
```

---

## 🔐 Security Model

### Identity on USB (Who You Are)
```yaml
identity:
  operator_id: "op_abc123def456"
  public_key: "ssh-ed25519 AAAA..."
  private_key: "encrypted with USB passphrase"
  
policies:
  - name: "default"
    trusted_hosts:
      - host_fingerprint: "SHA256:xyz..."
        allow_scopes: [read, write, execute]
    
  - name: "public_machine"
    trusted_hosts:
      - host_fingerprint: "SHA256:public..."
        allow_scopes: [read]  # Read-only on untrusted hosts
```

### Host Authorization (Where You Run)
```
1. USB plugged in
2. ark-client reads identity
3. Connects to host via localhost
4. Mutual TLS handshake:
   - USB proves identity with private key
   - Host proves it's trusted (fingerprint match)
5. Session established
6. All operations signed by USB identity
```

### Trust Levels
```yaml
trust_levels:
  fully_trusted_host:
    # Your home machine
    scopes: [read, write, execute, admin]
    data_sync: bidirectional
    cache_enabled: true
    
  work_machine:
    # Office computer
    scopes: [read, write, execute]
    data_sync: push_only  # Don't pull work data to USB
    cache_enabled: true
    
  public_machine:
    # Library computer
    scopes: [read]
    data_sync: none
    cache_enabled: false
    session_timeout: 30min
    clear_on_disconnect: true
```

---

## 🚀 Boot Sequence

### 1. Host Preparation (One-time per machine)
```bash
# Install ARK host service
curl -sSL https://ark.1true.org/install-host.sh | bash

# Or manual:
sudo pacman -S ark-host-service redis ollama

# Start services
sudo systemctl enable --now ark-host
sudo systemctl enable --now redis
sudo systemctl enable --now ollama

# Download models (optional, can auto-download)
ollama pull llama2
```

**Status:** Host is now ready for any ARK USB

---

### 2. USB Connection
```bash
# Plug in USB
# Automount to /media/ark or /run/media/$USER/ARK

# Launch client (auto-starts if configured)
/media/ark/client/ark-client

# First time: pair with host
ark-client pair-host
# Output:
#   🔑 Host Fingerprint: SHA256:abc123...
#   ✓ Trust this host? (y/N): y
#   ✓ Host added to trusted_hosts.json
#   ✓ Connection established
```

---

### 3. Session Start
```
1. ark-client reads identity from USB
2. Connects to localhost:8000 (ark-host-service)
3. Mutual TLS auth
4. Host loads your policies
5. Host syncs data from USB to /tmp/ark-session-{operator_id}/
6. Services start (if not already running)
7. Chat UI opens in browser (localhost:3000)
8. Ready to use!
```

**Time:** ~10 seconds (fast!)

---

### 4. During Session
```
You → Chat UI → FastAPI → arkd → Skills → Results → You
         ↓
    Background sync:
      - Memories saved to USB
      - Artifacts synced
      - Logs updated
      - Knowledge graph synced
```

---

### 5. Disconnect
```bash
# Graceful disconnect
ark-client disconnect

# Or just unplug (safe if sync is complete)
# USB signals cleanup:
#   1. Flush all pending writes
#   2. Sync data back to USB
#   3. Clear session cache (if policy requires)
#   4. Stop client
#   5. Safe to unplug ✓
```

---

## 📊 Data Flow Examples

### Example 1: "Install Obsidian"

```
1. You (USB UI) → "Install Obsidian"
   │
2. ark-client → POST localhost:8000/api/chat
   Headers:
     X-Ark-Identity: op_abc123
     X-Ark-Signature: signed_by_usb_key
   Body:
     {text: "Install Obsidian"}
   │
3. Host FastAPI → Verify signature
   ✓ Identity valid
   ✓ Policy allows: skill.pkg.install
   │
4. arkd → Execute skill.pkg.install
   $ pacman -S obsidian
   │
5. Result → FastAPI → ark-client → UI
   "✓ Installed Obsidian v1.5.3"
   │
6. Background: Log synced to USB at /ark/data/agent_logs/
```

---

### Example 2: Kyle Memory Storage

```
1. You ask Kyle about quantum mechanics
   │
2. Kyle researches (on host)
   - LLM inference (fast on host GPU)
   - Web search
   - Source compilation
   │
3. Memory stored:
   - Immediate: Redis cache (host)
   - Background: Synced to USB /ark/data/kyle_infinite_memory/
   - Backup: Host keeps copy in session DB
   │
4. Next time you plug USB into DIFFERENT host:
   - Your memories come with you
   - New host loads them
   - Kyle remembers everything
```

---

### Example 3: Multi-Host Workflow

```
Home Machine (Morning):
  - Create project with Kyle
  - Generate code
  - Run tests
  - Sync to USB
  - Unplug

Work Machine (Afternoon):
  - Plug in USB
  - Continue project (data synced)
  - Make changes
  - Sync to USB
  - Unplug

Home Machine (Evening):
  - Plug in USB
  - All work machine changes synced
  - Continue where you left off
```

---

## 🔧 Configuration Options

### USB Node Config (`/ark/config/preferences.yaml`)

```yaml
identity:
  operator_id: "op_abc123def456"
  display_name: "Superman"
  
sync:
  mode: auto              # auto | manual | on-disconnect
  interval_seconds: 30    # Background sync frequency
  conflict_resolution: usb_wins  # usb_wins | host_wins | prompt
  
ui:
  theme: dark
  port: 3000
  auto_open_browser: true
  
security:
  session_timeout_minutes: 60
  require_passphrase_on_connect: true
  clear_host_cache_on_disconnect: true
  
hosts:
  default_trust_level: untrusted
  auto_trust_localhost: false
```

---

### Host Service Config (`/etc/ark-host/config.yaml`)

```yaml
host:
  id: "host_home_desktop"
  name: "Home Desktop"
  
services:
  arkd:
    enabled: true
    workers: 4
    
  redis:
    enabled: true
    maxmemory: 2GB
    
  ollama:
    enabled: true
    gpu: auto
    models:
      - llama2
      - tinyllama
  
api:
  bind: 127.0.0.1
  port: 8000
  tls: true
  
resources:
  cpu_limit: 8
  ram_limit: 16GB
  gpu_enabled: true
  
session:
  max_concurrent: 3
  idle_timeout_minutes: 120
  temp_dir: /tmp/ark-sessions/
  
security:
  require_mutual_tls: true
  allowed_usb_fingerprints:
    - "SHA256:abc123..."  # Your USB
```

---

## 🎛️ Advanced Features

### 1. **Distributed Mode** (USB + Multiple Hosts)

```yaml
# /ark/config/distributed.yaml
distributed:
  enabled: true
  
  home_host:
    address: 192.168.1.100:8000
    role: primary
    capabilities: [gpu, storage, admin]
    
  work_host:
    address: 10.0.0.50:8000
    role: secondary
    capabilities: [cpu, storage]
    restricted_skills: [admin, hardware]
    
  cloud_host:
    address: cloud.1true.org:8000
    role: backup
    capabilities: [cpu]
    restricted_skills: [admin, hardware, filesystem]
```

**Use case:** Route heavy GPU tasks to home, CPU tasks to work, backups to cloud

---

### 2. **Offline Cache** (USB carries recent data)

```yaml
cache:
  enabled: true
  size_limit: 2GB  # On USB
  
  cache_items:
    - type: llm_responses
      ttl_days: 7
      
    - type: embeddings
      ttl_days: 30
      
    - type: model_weights
      enabled: false  # Too large for USB
```

**Benefit:** Work offline with cached responses

---

### 3. **Multi-USB Support** (Share across team)

```yaml
# Each team member has USB
team:
  member_1:
    usb_id: "op_alice"
    trust_level: admin
    
  member_2:
    usb_id: "op_bob"
    trust_level: developer
    
  member_3:
    usb_id: "op_charlie"
    trust_level: read_only

# Host accepts any team USB
# Policies enforced per USB
```

---

## 📈 Performance Comparison

### All-on-USB vs USB+Host

| Operation | All-on-USB | USB+Host | Speedup |
|-----------|------------|----------|---------|
| **Boot to ready** | 60-90s | 10-15s | **6x faster** |
| **Load LLM model** | 30-45s | 2-5s | **10x faster** |
| **LLM inference** | 5-10 tok/s | 30-100 tok/s | **10x faster** |
| **File operations** | Slow (USB I/O) | Fast (SSD) | **50x faster** |
| **Redis cache** | Slow | Native RAM | **100x faster** |
| **GPU acceleration** | Limited | Full | **Unlimited** |

---

## 🚧 Implementation Steps

### Phase 1: USB Node (Week 1-2)
```bash
1. Create USB structure
2. Build ark-client (Go/Rust for portability)
3. Implement identity/secrets
4. Create sync agent
5. Package UI files
```

### Phase 2: Host Service (Week 3-4)
```bash
1. Build ark-host-service
2. Implement mutual TLS auth
3. Create session manager
4. Integrate Redis, Ollama
5. Package installer script
```

### Phase 3: Integration (Week 5)
```bash
1. Test USB ↔ Host communication
2. Verify data sync
3. Test disconnect/reconnect
4. Multi-host testing
5. Security audit
```

---

## 🎯 Recommendation

**USE THIS ARCHITECTURE!**

**Why:**
- ✅ **Best performance** (10x faster)
- ✅ **True portability** (identity + data on USB)
- ✅ **Leverage host power** (GPU, RAM, SSD)
- ✅ **Scalable** (can add hosts easily)
- ✅ **Secure** (mutual auth, encrypted)
- ✅ **Future-proof** (distributed ready)

**vs. All-on-USB:**
- ❌ 10x slower
- ❌ Limited by USB I/O
- ❌ Can't use GPU effectively
- ❌ Wears out USB
- ❌ Not scalable

---

## 🚀 Quick Start (When Built)

```bash
# One-time: Install host service
curl -sSL https://ark.1true.org/install-host.sh | bash

# Plug in USB
# auto-mounts to /media/ark

# Start client
/media/ark/client/ark-client

# First time: pair with host
# After that: auto-connect

# Chat UI opens: localhost:3000
# Start chatting with Kyle!

# When done: unplug (auto-syncs and disconnects)
```

---

## 📞 Next Steps

**Should I build:**

1. **USB Node Structure**
   - Client binary
   - Sync agent
   - Identity management

2. **Host Service**
   - ark-host-service
   - Session manager
   - Mutual TLS auth

3. **Both** (full implementation)

**This architecture is MUCH better than all-on-USB!** 🚀
