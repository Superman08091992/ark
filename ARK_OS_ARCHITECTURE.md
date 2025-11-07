# ARK OS - Complete Architecture Specification

## 🎯 Product Objective

**Single USB boots a full OS that you operate entirely via AI chat.**

- Everything a normal desktop can do → natural-language tasks
- Offline by default, self-contained, portable
- Online capabilities:
  - Commands via @ARK_GATEKEEPER_bot (Telegram)
  - Public web UI on 1true.org (tool-limited demo)
  - Signed updates and telemetry sync

---

## 🔐 Access Tiers

| Tier | Interface | Permissions | Use Case |
|------|-----------|-------------|----------|
| **Operator (Local)** | USB, local machine | Full control (per policy) | Primary user |
| **Verified Remote** | Telegram Gatekeeper | Scoped control (via policies) | Remote management |
| **Public Web** | 1true.org | Read-only dashboard + demos | Showcase, marketing |

---

## 🏗️ High-Level Architecture

### Configuration (Your Specs)
- **Mode:** Hybrid
- **Web UI:** Yes (Svelte)
- **Redis:** Yes (caching + queues)
- **Priority:** Portability

### Base Layer: Arch Linux Persistent Live USB

**Why Arch?**
- Rolling release (always current)
- Minimal base (full control)
- Excellent AUR (all packages)
- pacstrap for custom builds

### Core Services Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    ARK OS Service Layer                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   arkd       │  │   Redis      │  │   SQLite     │    │
│  │ Orchestrator │  │ Message Bus  │  │  Persistence │    │
│  │ (Policy)     │  │ Job Queues   │  │  Audit Log   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Ollama     │  │   FastAPI    │  │  Svelte UI   │    │
│  │ llama.cpp    │  │  Chat API    │  │  Dashboard   │    │
│  │ Local LLM    │  │  System APIs │  │  (localhost) │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Telegram    │    │  1true.org   │    │   Local      │
│  Gateway     │    │  Web Backend │    │   Chat UI    │
│  (Remote)    │    │  (Public)    │    │  (Primary)   │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 🔄 Conversation → Action Pipeline

```
1. User Input
   │
   ├─ Local UI (Svelte chat)
   ├─ Telegram (@ARK_GATEKEEPER_bot)
   └─ 1true.org (limited public)
   │
   ▼
2. NL Task Parser
   │ Maps natural language → Skill (capability plugin)
   │ Example: "Install Obsidian" → skill.pkg.install
   │
   ▼
3. Policy Engine
   │ Validates: scope, user, risk, resources
   │ Checks: allowlists, namespaces, rate limits
   │
   ▼
4. Planner
   │ Generates execution steps
   │ Enqueues jobs in Redis: queue:exec
   │
   ▼
5. arkd Executors
   │ Consume jobs from Redis
   │ Run in sandboxed environments:
   │  - run.local.sandbox (unprivileged, no net)
   │  - run.container.build (Podman with RO rootfs)
   │  - run.host.admin (MFA required, logged)
   │
   ▼
6. Result Streaming
   │ Stream back to UI/Telegram
   │ Store artifacts in SQLite
   │ Audit log everything
   └─ Emit events to stream:events
```

---

## 🔒 Security and Governance

### Policy-First Architecture

**Namespaces:**
```yaml
namespaces:
  run.local.sandbox:
    user: unprivileged
    network: false
    cpu_limit: 2
    ram_limit: 512MB
    
  run.container.build:
    engine: podman
    rootfs: readonly
    network: true
    cpu_limit: 4
    
  run.host.admin:
    mfa_required: true
    audit_level: full
    rate_limit: 5/hour
```

**Policy Model:**
```yaml
policies:
  - subject: operator_local
    resource: run.local.sandbox.*
    action: execute
    effect: allow
    
  - subject: operator_remote_verified
    resource: run.host.admin.*
    action: execute
    effect: deny
    reason: "Remote users cannot perform admin operations"
    
  - subject: public_web
    resource: read.dashboard
    action: read
    effect: allow
```

### Secrets Management

```
/ark/secrets/
  ├── vault.key (sealed)
  ├── telegram_bot_token
  ├── 1true_org_api_key
  └── operator_passphrase_hash

Unsealed at runtime → environment variables
Operations reference via ${SECRET_NAME}
```

### Network Posture

```
Firewall: Deny-by-default
Local UI: 127.0.0.1:3000 (localhost only)
FastAPI: 127.0.0.1:8000 (localhost only)

When online:
  - Telegram: Outbound HTTPS only
  - Updates: Signature-verified HTTPS
  - 1true.org: Reverse proxy (optional)
```

---

## 💾 Data and Storage

### Redis (Volatile, Fast)

```
# Job Queues
queue:exec          → {task_id, skill, args, limits, actor}
queue:result        → {task_id, status, stdout, stderr, artifacts}

# Event Stream
stream:events       → XADD * type=task.start actor=local task_id=123

# Session Context
session:{user_id}   → {messages[], context, last_active}

# Cache
cache:embeddings    → {text_hash: vector}
cache:summaries     → {doc_hash: summary}

# Rate Limiting
ratelimit:{actor}:{skill} → INCRBY with TTL
```

### SQLite (Durable, Local)

```sql
-- Audit trail
CREATE TABLE audit_log (
    ts INTEGER NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT,
    hash TEXT,
    status TEXT,
    duration_ms INTEGER,
    risk_level TEXT,
    PRIMARY KEY (ts, actor)
);

-- Artifacts produced by tasks
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

-- Policy definitions
CREATE TABLE policies (
    id INTEGER PRIMARY KEY,
    version INTEGER NOT NULL,
    rule TEXT NOT NULL,
    effect TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

-- Installed packages/capabilities
CREATE TABLE inventory (
    pk TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    source TEXT NOT NULL,
    trusted BOOLEAN NOT NULL
);

-- Knowledge base
CREATE TABLE knowledge (
    id INTEGER PRIMARY KEY,
    topic TEXT NOT NULL,
    embedding_ref TEXT,
    summary TEXT,
    raw_ref TEXT,
    trust_score REAL,
    created_at INTEGER NOT NULL
);
```

### Filesystem Layout (USB Persistent Partition)

```
/ark/
├── bin/              # Launchers, wrappers, CLI tools
├── core/             # arkd orchestrator, policy engine, skills
│   ├── arkd
│   ├── policy_engine.py
│   └── skills/
│       ├── system_ops/
│       ├── devops/
│       ├── data_ai/
│       ├── productivity/
│       ├── trading/
│       ├── media_docs/
│       └── hardware/
├── ui/               # Svelte web app
├── api/              # FastAPI application
├── models/           # Ollama/gguf LLM models
├── data/             # User datasets, artifacts
├── logs/             # All logs (rotated)
├── db/               # SQLite database files
├── secrets/          # Sealed secrets vault
└── updates/          # Staged signed updates
```

---

## 🧩 Skills Catalog (Initial Set)

### 1. System Operations
```yaml
skill: system_ops.pkg_install
inputs:
  - package_name: string
  - repository: string (default: core)
outputs:
  - installed: boolean
  - version: string
risks: [disk_write, network_required]
sandbox: run.local.sandbox
```

**Available:**
- `list_packages` - Query installed packages
- `install_package` - Install via pacman
- `manage_service` - Start/stop systemd units
- `mount_device` - Mount USB/external drives
- `network_config` - Configure network interfaces
- `sensor_read` - Read hardware sensors

### 2. DevOps
```yaml
skill: devops.container_build
inputs:
  - dockerfile_path: string
  - tag: string
outputs:
  - image_id: string
  - size_mb: int
risks: [container_runtime, cpu_intensive]
sandbox: run.container.build
```

**Available:**
- `build_container` - Build Docker/Podman images
- `run_tests` - Execute test suites
- `compile_code` - Compile C/C++/Rust/Go
- `manage_repos` - Git operations
- `deploy_service` - Deploy to systemd

### 3. Data/AI
```yaml
skill: data_ai.llm_inference
inputs:
  - prompt: string
  - model: string (default: llama2)
  - max_tokens: int
outputs:
  - response: string
  - tokens_used: int
risks: [gpu_usage, cpu_intensive]
sandbox: run.local.sandbox
```

**Available:**
- `run_llm` - Ollama inference
- `embed_text` - Generate embeddings
- `summarize` - Document summarization
- `index_files` - Vector search indexing
- `query_knowledge` - RAG queries

### 4. Productivity
```yaml
skill: productivity.file_create
inputs:
  - path: string
  - content: string
outputs:
  - created: boolean
  - sha256: string
risks: [disk_write]
sandbox: run.local.sandbox
```

**Available:**
- `create_file` - Create/edit files
- `project_scaffold` - Generate project templates
- `note_capture` - Quick note taking
- `task_track` - TODO management

### 5. Trading/Market (Kyle)
```yaml
skill: trading.kyle_scan
inputs:
  - symbols: list[string]
  - analysis_type: string
outputs:
  - report_path: string
  - alerts: list[string]
risks: [network_required, cpu_intensive]
sandbox: run.local.sandbox
```

**Available:**
- `kyle_scan` - Market analysis
- `parse_filings` - SEC filing analysis
- `publish_alerts` - Alert generation
- `backtest` - Strategy backtesting

### 6. Media/Docs
```yaml
skill: media_docs.convert_md_pdf
inputs:
  - input_path: string
  - output_path: string
outputs:
  - pdf_path: string
  - pages: int
risks: [disk_write]
sandbox: run.local.sandbox
```

**Available:**
- `convert_markdown` - MD ↔ PDF
- `ocr_image` - OCR processing
- `image_ops` - Basic image manipulation
- `video_transcode` - Video conversion

### 7. Hardware
```yaml
skill: hardware.serial_interface
inputs:
  - port: string
  - baud_rate: int
  - command: string
outputs:
  - response: string
risks: [hardware_access]
sandbox: run.host.admin
```

**Available:**
- `serial_comm` - Serial/USB device communication
- `gpio_control` - GPIO pin control (Pi)
- `cnc_control` - CNC machine interface (optional)
- `3d_printer` - 3D printer interface (optional)

---

## 📋 Policy Examples

```yaml
# Public web users
- subject: public_web
  resources:
    - read.dashboard
    - read.docs
    - read.demos
  actions: [read]
  effect: allow
  conditions:
    rate_limit: 100/hour

# Telegram gatekeeper users
- subject: operator_remote_verified
  resources:
    - run.local.sandbox.*
  actions: [execute]
  effect: allow
  conditions:
    cpu_limit: 2
    ram_limit: 512MB
    no_host_admin: true
    rate_limit: 20/hour

# Local operator
- subject: operator_local
  resources:
    - run.local.sandbox.*
    - run.container.build.*
  actions: [execute, read, write]
  effect: allow

- subject: operator_local
  resources:
    - run.host.admin.*
  actions: [execute]
  effect: allow_with_mfa
  conditions:
    mfa_required: true
    audit_level: full
    rate_limit: 5/hour
```

---

## 🔑 Identity and AuthN/AuthZ

### Local Authentication
```
1. Passphrase + device bind
2. Optional WebAuthn (YubiKey)
3. Generates local JWT (24h expiry)
```

### Telegram Authentication
```
1. User → @ARK_GATEKEEPER_bot
2. Bot verifies Telegram user_id against allowlist
3. Issues short-lived JWT (1h expiry)
4. JWT includes: actor_id, role, scope
```

### Web Authentication (1true.org)
```
1. OAuth2/OIDC login
2. Role-scoped JWT issued
3. Proxied to node with actor context
```

### Every Action
```
Headers:
  X-Actor-ID: local_operator
  X-Actor-Role: operator_local
  X-Actor-Token: JWT...
  
Audit:
  actor, action, target, timestamp, result
```

---

## 📡 Offline-First Operations

```
Boot Sequence:
  1. GRUB/Syslinux
  2. Arch Linux kernel
  3. systemd-boot
  4. Mount /ark partition (persistent)
  5. Start services:
     - redis.service
     - ollama.service
     - arkd.service (orchestrator)
     - api.service (FastAPI)
     - ui.service (Svelte)
  6. Display chat UI (localhost:3000)

Offline Mode:
  ✓ All models resident on USB
  ✓ No external dependencies
  ✓ No-net policies apply
  ✓ Full functionality except:
    - Telegram gateway
    - 1true.org sync
    - Updates
    
Online Mode:
  ✓ Detect network link
  ✓ Enable online policies
  ✓ Start sync manager
  ✓ Connect Telegram bridge
```

---

## 🌐 Online Bridge Architecture

### Telegram Integration

```
User ──► @ARK_GATEKEEPER_bot
         │
         ▼
    Bot Service (Python)
         │ Verify user_id
         │ Issue JWT
         │
         ▼
    1true.org Gateway
         │ Rate limit
         │ Log request
         │
         ▼
    Node API: POST /api/chat
         │
         ▼
    arkd Execution
         │
         ▼
    Result ──► Bot ──► User
```

### 1true.org Public Website

```
Features:
  - Public demo UI (tool-less)
  - System documentation
  - Live metrics (anonymized)
  - "Connect Your Node" flow
  - Verified user portal

Endpoints:
  GET  /                    → Landing page
  GET  /demo                → Tool-less chat demo
  GET  /docs                → Documentation
  GET  /metrics             → Public metrics
  POST /auth/login          → OAuth2 login
  GET  /dashboard           → User dashboard
  POST /api/proxy/:node_id  → Proxy to user's node (verified)
```

### Update Service

```
Manifest:
  {
    "version": "2.1.0",
    "channel": "stable",
    "signature": "SHA256:...",
    "files": [
      {"path": "arkd", "sha256": "...", "size": 1024000},
      {"path": "models/llama2.gguf", "sha256": "...", "delta": true}
    ]
  }

Process:
  1. Fetch manifest from 1true.org/updates/stable.json
  2. Verify signature against trusted public key
  3. Download files to /ark/updates/
  4. Verify checksums
  5. Run pre-update health check
  6. Atomic swap (symlink switch)
  7. Restart services
  8. Post-update health check
  9. Rollback on failure
```

---

## 🔌 API Endpoints

### Chat API
```
POST /api/chat
Body: {
  actor: "operator_local",
  text: "Install Obsidian",
  context_ref: "session_123"
}
Response: {
  message_id: "msg_456",
  stream_url: "/api/stream/msg_456",
  status: "processing"
}
```

### Task API
```
POST /api/task
Body: {
  actor: "operator_remote_verified",
  skill: "trading.kyle_scan",
  args: {
    symbols: ["AAPL", "TSLA"],
    analysis_type: "momentum"
  }
}
Response: {
  task_id: "task_789",
  status: "queued",
  eta_seconds: 30
}
```

### System APIs
```
GET  /api/health          → System health status
GET  /api/capabilities    → Available skills
GET  /api/policies        → Active policies (filtered by actor)
POST /api/files           → Upload file
GET  /api/files/:id       → Download file (scoped)
POST /api/updates/apply   → Apply staged update (local + MFA)
```

---

## 📊 Redis Contracts

### Job Queue
```redis
# Enqueue task
LPUSH queue:exec '{"task_id":"t1","skill":"pkg.install","args":{"package":"obsidian"},"actor":"local"}'

# Worker consume
BRPOP queue:exec 0

# Result
LPUSH queue:result '{"task_id":"t1","status":"success","stdout":"...","artifacts":[]}'
```

### Event Stream
```redis
# Add event
XADD stream:events * type=task.start actor=local task_id=t1 skill=pkg.install

# Consume
XREAD BLOCK 1000 STREAMS stream:events $
```

### Rate Limiting
```redis
# Increment counter
INCR ratelimit:remote:trading.kyle_scan
EXPIRE ratelimit:remote:trading.kyle_scan 3600

# Check
GET ratelimit:remote:trading.kyle_scan
# If > threshold: deny
```

---

## 🎛️ arkd Orchestrator Responsibilities

```python
class Orchestrator:
    def __init__(self):
        self.redis = Redis()
        self.policy_engine = PolicyEngine()
        self.skill_registry = SkillRegistry()
        self.audit_log = AuditLog(db='audit.db')
    
    async def process_queue(self):
        while True:
            # Pop task
            task = await self.redis.brpop('queue:exec')
            
            # Validate policy
            if not self.policy_engine.authorize(
                actor=task['actor'],
                resource=f"run.{task['skill']}",
                action='execute'
            ):
                await self.publish_result(task['task_id'], 'denied')
                continue
            
            # Resolve skill
            skill = self.skill_registry.get(task['skill'])
            
            # Execute in sandbox
            result = await self.execute_sandboxed(
                skill=skill,
                args=task['args'],
                limits=skill.limits,
                actor=task['actor']
            )
            
            # Audit
            self.audit_log.record(
                actor=task['actor'],
                action=task['skill'],
                target=task['args'],
                status=result.status,
                duration=result.duration_ms
            )
            
            # Publish result
            await self.publish_result(task['task_id'], result)
```

---

## 🚀 Boot Sequence and UX

### Boot Process
```
1. GRUB menu
   ├─ ARK OS (Persistent)
   └─ ARK OS (Recovery)

2. Kernel load + initramfs
   └─ Arch Linux base

3. systemd targets
   ├─ redis.service
   ├─ ollama.service
   ├─ arkd.service
   ├─ api.service (FastAPI)
   └─ ui.service (Svelte)

4. First screen: Chat UI (localhost:3000)
```

### Example Chat Interactions

```
User: Create a project folder with Python venv and install FastAPI

arkd:
  ✓ Created /ark/data/my_project/
  ✓ Created Python venv
  ✓ Installed FastAPI, uvicorn
  📁 Project ready at /ark/data/my_project/
```

```
User: Start tinyllama and summarize /ark/docs/*.md

arkd:
  ⏳ Loading tinyllama...
  ✓ Model loaded
  📄 Processing 15 files...
  ✓ Summary saved to /ark/data/summaries/docs_20250107.txt
```

```
User: Build Docker image from /ark/data/my_project and run tests

arkd:
  🔨 Building image (tag: my_project:latest)
  ✓ Build complete (image_id: sha256:abc123...)
  🧪 Running tests...
  ✓ All tests passed (15/15)
```

```
User: Pair with @ARK_GATEKEEPER_bot

arkd:
  📱 Open Telegram and message @ARK_GATEKEEPER_bot
  🔑 Use pairing code: XYZ123
  ⏳ Waiting for confirmation...
  ✓ Paired! Remote access enabled with scope: limited
```

```
User: Apply update channel 'stable'

arkd:
  🔍 Checking for updates...
  📦 Update available: v2.1.0 → v2.2.0
  ⚠️  MFA required for system update
  🔐 Enter passphrase: ****
  ✓ Verified
  ⏳ Downloading update (124 MB)...
  ✓ Download complete, verifying signatures...
  ✓ Signatures valid
  ⚡ Applying update...
  ✓ Update complete! Restarting services...
  ✅ ARK OS v2.2.0 ready
```

---

## 📈 Telemetry and Observability

### Structured Logging
```json
{
  "ts": "2025-01-07T12:34:56Z",
  "level": "info",
  "component": "arkd",
  "actor": "operator_local",
  "action": "skill.pkg.install",
  "target": "obsidian",
  "status": "success",
  "duration_ms": 1234,
  "risk_level": "low"
}
```

### Local Dashboard
```
┌─────────────────────────────────────────────────────────┐
│ ARK OS Dashboard                                        │
├─────────────────────────────────────────────────────────┤
│ System:                                                 │
│   CPU: 45% (4 cores)                                    │
│   RAM: 2.1 / 8.0 GB                                     │
│   Disk: 45 / 128 GB (/ark)                              │
│   GPU: NVIDIA RTX 3060 (12GB) - 20% utilized            │
│                                                          │
│ Services:                                                │
│   ✓ arkd        (running, 3 workers)                    │
│   ✓ redis       (running, 127 keys)                     │
│   ✓ ollama      (running, llama2 loaded)                │
│   ✓ api         (running, 45 req/min)                   │
│   ✓ ui          (running, 1 session)                    │
│                                                          │
│ Job Queue:                                               │
│   Pending: 0                                             │
│   Running: 1 (skill.data_ai.embed_text)                 │
│   Completed today: 47                                    │
│                                                          │
│ Network:                                                 │
│   Status: Online (192.168.1.100)                         │
│   Telegram: Connected                                    │
│   Updates: Stable channel, up-to-date (v2.2.0)          │
└─────────────────────────────────────────────────────────┘
```

### Anonymized Metrics (When Online)
```
Opt-in telemetry (by policy):
  - OS version
  - Hardware specs (anonymized)
  - Skill usage (counts, not content)
  - Error rates
  - Performance metrics

Never collected:
  - User data
  - Chat content
  - File paths
  - Personal identifiers
```

---

## ⚡ Performance and Limits

### Resource Management
```yaml
redis:
  maxmemory: 512MB
  eviction: allkeys-lru

ollama:
  gpu_layers: auto
  context_size: 4096
  threads: 4

arkd:
  worker_count: 3
  max_concurrent_jobs: 5

api:
  workers: 4
  timeout: 300s
  max_request_size: 100MB
```

### Sandbox Limits (Per Actor)
```yaml
run.local.sandbox:
  cpu: 2 cores
  ram: 512MB
  disk: 1GB /tmp
  network: false
  devices: []

run.container.build:
  cpu: 4 cores
  ram: 2GB
  disk: 10GB
  network: true
  devices: []

run.host.admin:
  cpu: unlimited
  ram: unlimited
  disk: unlimited
  network: true
  devices: all
  mfa_required: true
```

### Constrained Hardware Degradation
```
If RAM < 4GB:
  - Use smaller models (tinyllama)
  - Reduce worker count
  - Disable GPU features

If Disk < 32GB:
  - Compress logs more aggressively
  - Limit artifact retention
  - Warn user

If No GPU:
  - CPU-only inference (slower)
  - Batch operations
  - Lower context limits
```

---

## 🔥 Failure Modes and Recovery

### Network Loss
```
Detection: ping gateway every 30s
Action:
  - Queue jobs locally
  - Schedule retries
  - Disable online-only skills
  - Continue offline operations
Recovery:
  - Resume sync
  - Flush queued jobs
```

### Model Load Failure
```
Detection: Ollama health check fail
Action:
  - Fallback to smallest model
  - Log error
  - Notify user
Recovery:
  - Retry model load
  - Download model if missing
```

### Policy Denial
```
Detection: Policy engine returns deny
Action:
  - Explain denial reason
  - Show required permissions
  - Suggest allowed alternatives
Example:
  "❌ Denied: run.host.admin requires MFA
   💡 Tip: Use 'mfa enable' to set up authentication
   📝 Or use run.local.sandbox for non-admin tasks"
```

### Update Failure
```
Detection: Post-update health check fail
Action:
  - Automatic rollback to last snapshot
  - Log failure details
  - Notify user
Recovery:
  - Restore previous version
  - Mark update as failed
  - Report to update server
```

### Database Corruption
```
Detection: SQLite integrity check fail
Action:
  - Use nightly backup
  - Restore from last good state
  - Log corruption details
Prevention:
  - WAL mode
  - Integrity checks on boot
  - Hourly backups to /ark/db/backups/
```

---

## 🛡️ Content Boundaries and Safety

### High-Risk Operations
```yaml
blocked_by_default:
  - rm -rf / (destructive filesystem ops)
  - dd if=/dev/zero of=/dev/sda (disk wiping)
  - iptables -F (firewall disable)
  - systemctl stop arkd (self-termination)

require_confirmation:
  - Package removal
  - File deletion (> 100MB)
  - Network config changes
  - Firewall rule changes

require_mfa:
  - System updates
  - Policy modifications
  - Secret changes
  - Admin namespace access
```

### Policy Self-Modification Protection
```
Rules:
  - Policy updates require signed source
  - Policy version must increment
  - Rollback capability preserved
  - Audit trail immutable
```

### Destructive Operation Safeguards
```
Before execution:
  1. Show preview of changes
  2. Require explicit confirmation
  3. Create snapshot (if possible)
  4. Log with high audit level
  5. Rate limit (max 5/hour)
```

---

## 🌍 Public Website Mode (1true.org)

### Tool-less Demo
```
Features:
  - Chat with canned prompts
  - Example: "Show me system capabilities"
  - Example: "What skills are available?"
  - No actual execution
  - Responses from static knowledge base

Limitations:
  - Cannot execute skills
  - Cannot access files
  - Cannot modify system
```

### Documentation Hub
```
Sections:
  - Getting Started
  - Skill Catalog
  - Policy Examples
  - API Reference
  - Troubleshooting
  - Community Forum
```

### "Connect Your Node" Flow
```
1. User registers on 1true.org
2. Receives pairing code
3. On USB: arkd pair <code>
4. Verified connection established
5. User can send commands via web portal
```

### No-USB Mode
```
If user has no USB:
  - Can interact via Telegram only
  - Restricted sandbox environment
  - Shared compute resources
  - Limited to non-destructive skills
  - Rate limited more aggressively
```

---

## 📦 Upgrade Channels

### Channels
```
stable:
  - Tested releases
  - Security updates
  - Recommended for production

candidate:
  - Release candidates
  - Pre-release testing
  - May have bugs

edge:
  - Daily builds
  - Experimental features
  - Not recommended for critical use
```

### Update Process
```
1. Node checks channel periodically
2. Fetches manifest.json
3. Compares versions
4. Shows changelog to user
5. User approves (or auto if policy)
6. Download diff-based patches
7. Verify signatures (GPG)
8. Apply atomically
9. Health check
10. Rollback on failure
```

### Diff-Based Updates
```
Instead of full downloads:
  - Binary diff (bsdiff/xdelta)
  - Only changed files
  - Compressed patches
  - Example: 2GB → 50MB patch

Signature enforcement:
  - Manifest signed by ARK maintainers
  - Public key embedded in OS
  - Verify before extraction
```

---

## 🎬 Concrete Example Flows

### A. Local Operator Installs Obsidian

```
User: Install Obsidian

arkd:
  1. Parse intent → skill.pkg.install
  2. Check policy:
     - Subject: operator_local
     - Resource: run.local.sandbox.pkg.install
     - Action: execute
     - Effect: ✓ allow
  3. Plan steps:
     - Update package database
     - Install obsidian
     - Create desktop entry
  4. Enqueue job in Redis queue:exec
  5. Worker picks up job
  6. Execute in sandbox with network:
     $ pacman -S --needed obsidian
  7. Success!
  8. Store artifact (desktop entry) in SQLite
  9. Audit log: actor=local, action=pkg.install, status=success
  10. Return result to UI:
      "✓ Installed Obsidian v1.5.3
       📱 Desktop shortcut created
       🚀 Launch with: obsidian"
```

### B. Telegram Remote Asks for Kyle Scan

```
Telegram User: @ARK_GATEKEEPER_bot run Kyle scan on AAPL,TSLA

Bot:
  1. Verify user_id against allowlist
  2. Issue JWT with scope: operator_remote_verified
  3. POST to Node API /api/task:
     {
       "actor": "remote_user123",
       "skill": "trading.kyle_scan",
       "args": {
         "symbols": ["AAPL", "TSLA"],
         "analysis_type": "momentum"
       }
     }

arkd:
  4. Check policy:
     - Subject: operator_remote_verified
     - Resource: run.local.sandbox.trading.kyle_scan
     - Action: execute
     - Conditions: cpu=2, ram=512MB, no file write outside /ark/data/market
     - Effect: ✓ allow
  5. Execute Kyle scan in sandbox
  6. Generate report, save to /ark/data/market/scan_20250107.csv
  7. Extract summary
  8. Return to API → Bot → User:
     "📊 Kyle Scan Complete
      
      AAPL: Momentum ↗️ Strong (RSI: 72)
      TSLA: Momentum ↘️ Weak (RSI: 38)
      
      📁 Full report: scan_20250107.csv
      ⏱️ Executed in 12.3s"
```

### C. Public User on 1true.org

```
Public User: (on 1true.org/demo)
  "What skills are available?"

Demo Backend:
  1. No execution, canned response
  2. Fetch from static knowledge base
  3. Return formatted list:
     "🔧 Available Skills:
      
      System Ops: Install packages, manage services
      DevOps: Build containers, run tests
      Data/AI: Run LLMs, embeddings, summaries
      Productivity: File ops, project scaffolds
      Trading: Kyle scans, market analysis
      Media: Convert docs, OCR, image ops
      
      🎯 To use these skills, connect your ARK USB or
         chat via @ARK_GATEKEEPER_bot"

Limitations:
  - Cannot execute any actual skills
  - Cannot access files
  - Cannot modify system
  - Rate limited: 100 requests/hour
```

---

## 📂 File Structure (Complete)

```
/ark/
├── bin/
│   ├── ark                    # Main CLI
│   ├── arkd                   # Orchestrator daemon
│   ├── ark-pair               # Pairing helper
│   ├── ark-update             # Update manager
│   └── ark-backup             # Backup utility
│
├── core/
│   ├── arkd.py                # Main orchestrator
│   ├── policy_engine.py       # Policy validator
│   ├── skill_registry.py      # Skill loader
│   ├── sandbox.py             # Execution sandbox
│   ├── sync_manager.py        # Online sync
│   └── skills/
│       ├── __init__.py
│       ├── system_ops/
│       │   ├── pkg_install.py
│       │   ├── service_manage.py
│       │   └── ...
│       ├── devops/
│       ├── data_ai/
│       ├── productivity/
│       ├── trading/
│       ├── media_docs/
│       └── hardware/
│
├── ui/
│   ├── src/
│   │   ├── App.svelte
│   │   ├── Chat.svelte
│   │   ├── Dashboard.svelte
│   │   └── ...
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── api/
│   ├── main.py                # FastAPI app
│   ├── routes/
│   │   ├── chat.py
│   │   ├── tasks.py
│   │   ├── files.py
│   │   └── system.py
│   ├── models.py
│   └── dependencies.py
│
├── models/
│   ├── llama2.gguf            # Default model
│   ├── tinyllama.gguf         # Fallback
│   └── embeddings.gguf        # Embedding model
│
├── data/
│   ├── market/                # Kyle data
│   ├── projects/              # User projects
│   ├── notes/                 # Notes
│   └── artifacts/             # Generated files
│
├── logs/
│   ├── arkd.log
│   ├── api.log
│   ├── ui.log
│   ├── audit.log
│   └── system.log
│
├── db/
│   ├── audit.db               # Audit log
│   ├── artifacts.db           # Artifacts
│   ├── policies.db            # Policies
│   ├── inventory.db           # Packages
│   ├── knowledge.db           # KB
│   └── backups/               # Nightly backups
│
├── secrets/
│   ├── vault.key              # Master key (sealed)
│   ├── telegram_bot_token
│   ├── 1true_org_api_key
│   └── operator_passphrase_hash
│
└── updates/
    ├── manifest.json
    ├── staged/
    └── rollback/
```

---

## 🎯 Implementation Roadmap

### Phase 1: Core Infrastructure (Weeks 1-4)
- [ ] Arch Linux persistent USB build
- [ ] Redis + SQLite setup
- [ ] arkd orchestrator (basic)
- [ ] Policy engine (basic)
- [ ] FastAPI skeleton
- [ ] Svelte UI (chat only)

### Phase 2: Skills Foundation (Weeks 5-8)
- [ ] Skill plugin system
- [ ] Sandboxing (run.local.sandbox)
- [ ] System ops skills (5 core)
- [ ] DevOps skills (3 core)
- [ ] Testing framework

### Phase 3: LLM Integration (Weeks 9-12)
- [ ] Ollama integration
- [ ] Data/AI skills
- [ ] Embeddings + vector search
- [ ] Kyle trading skills (port existing)

### Phase 4: Online Bridge (Weeks 13-16)
- [ ] Telegram bot gateway
- [ ] 1true.org public site
- [ ] Update service
- [ ] Sync manager

### Phase 5: Security Hardening (Weeks 17-20)
- [ ] MFA implementation
- [ ] Secrets vault
- [ ] Audit trail
- [ ] Policy testing
- [ ] Penetration testing

### Phase 6: Polish & Launch (Weeks 21-24)
- [ ] Documentation
- [ ] Tutorials
- [ ] Performance optimization
- [ ] Beta testing
- [ ] Public release

---

## 🚧 Next Immediate Steps

Based on your requirements, here's what I should build **right now**:

1. **Create Arch Linux persistent USB builder script**
   - Automated USB creation
   - Pre-configured with all services
   - Ready to boot and chat

2. **Build arkd orchestrator core**
   - Job queue processing
   - Policy engine integration
   - Skill execution framework

3. **Implement basic skills**
   - System ops (pkg install)
   - File operations
   - LLM inference (Ollama)

4. **Create policy system**
   - YAML policy definitions
   - Validation engine
   - Runtime enforcement

5. **Build FastAPI + Svelte chat UI**
   - Chat interface
   - Task management
   - Dashboard

**Should I start building these components now?** 🚀
