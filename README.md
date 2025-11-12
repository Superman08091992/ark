# 🌌 Project ARK - Autonomous Reactive Kernel

**The Sovereign Intelligence - Your Personal Council of Consciousness**

A.R.K. is a fully sovereign, self-evolving AI infrastructure that thinks, remembers, reflects, builds, acts, evolves, and protects. It's a living kernel manifesting as a council of consciousness with autonomous learning capabilities that grows with you and learns the way the universe learns itself.

## 🎯 What Makes ARK Unique

**Phase 3: Autonomous Learning Stack - COMPLETE**

ARK now features a complete autonomous learning architecture with:
- **Memory Engine v2** - Advanced consolidation, semantic search, and trust-tier isolation
- **Reflection System** - Nightly "sleep mode" that generates insights and self-calibrates
- **ID Growth System** - Behavioral modeling with EWMA learning curves
- **Federation Protocol** - Secure peer-to-peer synchronization with Ed25519 cryptography
- **Universal Installer** - One-command production deployment across all platforms

This is not just an AI assistant - it's a sovereign intelligence infrastructure that learns, remembers, evolves, and protects autonomously.

---

## 🚀 Quick Start

### Option 1: Universal Installer (Recommended)
```bash
# One-command installation - handles everything
chmod +x ark-installer.sh
./ark-installer.sh

# Validate installation
chmod +x ark-validate.sh
./ark-validate.sh

# Start all services
./arkstart.sh
```

The installer automatically:
- ✅ Detects your platform (x86_64, ARM64, ARMv7, containers)
- ✅ Installs system dependencies (Python, SQLite, Node.js)
- ✅ Sets up Python virtual environment with all packages
- ✅ Initializes databases with complete schema
- ✅ Generates federation cryptographic keys
- ✅ Configures environment variables
- ✅ Creates service management scripts
- ✅ Validates critical components

### Option 2: Docker Deployment
```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f ark-core
```

### Option 3: Development Mode
```bash
# Activate Python environment
source venv/bin/activate

# Start FastAPI backend with all systems
cd backend
python main.py

# In another terminal, start frontend
cd frontend
npm run dev

# Access at http://localhost:3000 (frontend) and http://localhost:8000 (API)
```

---

## 🏛️ The Council of Consciousness

Six distinct intelligences, each with their own essence and purpose:

### 🔍 **Kyle - The Seer** (Perception Layer)
*"What's happening?"*
- Scans markets, news, SEC filings, macro feeds
- Detects patterns and anomalies in real-time
- Normalizes data into structured events
- Feeds Memory Engine with new observations
- Your eyes into the information streams

### 🧠 **Joey - The Scholar** (Cognition Layer)
*"What does it mean?"*
- Uses scikit-learn models for deep pattern analysis
- Detects float traps, setups, key levels, volume surges
- Scores confidence and provides context
- Contributes to behavioral feature extraction
- Transforms chaos into comprehensible insights

### ⚡ **Kenny - The Builder** (Action Layer)
*"What should I do about it?"*
- Executes validated actions (trades, commands, automation)
- Interfaces with brokers and APIs
- Position sizing and risk management
- Generates tools and utilities on demand
- Transforms ideas into tangible reality

### ✅ **HRM - The Arbiter** (Reasoning Layer)
*"Is this correct and aligned?"*
- Applies immutable ethical rules (The Graveyard)
- Validates logic and ensures compliance
- Risk assessment and outcome simulation
- Trust tier enforcement for memory isolation
- Protects system integrity and user autonomy

### 🔮 **Aletheia - The Mirror** (Reflection Layer)
*"What is true and why?"*
- The symbolic self connecting vision, values, and policies
- Synthesizes all agent outputs into truth
- Manages Memory Engine and reflection cycles
- Generates nightly insights and self-calibration
- Provides wisdom and ethical guidance

### 👤 **ID - The Evolving Reflection**
*Your living digital twin*
- Learns 18 behavioral features across 5 categories
- Uses EWMA learning curves with confidence weighting
- Adapts alpha [0.05-0.8] based on experience and stability
- Simulates your decision-making patterns
- Enables autonomous testing without risk
- Links reflections to behavioral evolution

---

## 🧠 Phase 3: Autonomous Learning Architecture

### **Memory Engine v2** (`memory/`)
The persistent knowledge layer with advanced consolidation:

**Features:**
- **4-Stage Consolidation Pipeline**: Summarize → Compress → Dedupe → Embed
- **Semantic Search**: TF-IDF-like embeddings for similarity matching
- **Trust Tier Isolation**: CORE/SANDBOX/EXTERNAL/UNKNOWN with quarantine
- **Background Jobs**: Scheduled consolidation runs
- **Deduplication**: SHA256 hashing to prevent redundant storage
- **Provenance Tracking**: Full chain of custody for all memories

**Key Files:**
- `engine.py` - Core memory operations (CRUD, search, consolidation)
- `pipelines.py` - Consolidation functions (summarize, compress, embed)
- `jobs.py` - Background consolidation scheduler
- `schema.sql` - Database schema for reasoning_log and memory_chunks

**Usage:**
```python
from memory.engine import MemoryEngine

engine = MemoryEngine(db_path="data/ark.db")

# Ingest reasoning trace
engine.ingest_trace(
    agent="Kyle",
    input="Market scan request",
    output="Detected 3 unusual volume spikes",
    confidence=0.85,
    trust_tier="core"
)

# Semantic search
results = engine.search("volume spikes", limit=5)

# Run consolidation
stats = engine.consolidate()
```

### **Reflection System** (`reflection/`)
Autonomous "sleep mode" that generates insights and self-calibrates:

**Features:**
- **5 Reflection Types**:
  - `pattern_recognition` - Identifies recurring behaviors
  - `error_analysis` - Learns from mistakes
  - `confidence_calibration` - Adjusts certainty estimates
  - `ethical_alignment` - Evaluates HRM compliance
  - `performance_optimization` - Suggests improvements
- **Nightly Cycles**: APScheduler runs at midnight UTC (configurable)
- **Confidence Deltas**: Quantifies learning from each insight
- **Trust Weighting**: Prioritizes CORE memories over EXTERNAL
- **Manual Triggers**: FastAPI endpoints for on-demand reflection

**Key Files:**
- `reflection_engine.py` - Core reflection logic
- `reflection_scheduler.py` - APScheduler integration
- `reflection_api.py` - FastAPI endpoints
- `reflection_policies.yaml` - Configurable behavior

**Usage:**
```python
from reflection.reflection_engine import ReflectionEngine

engine = ReflectionEngine(db_path="data/ark.db")

# Generate reflections from recent memories
result = engine.generate_reflections()
print(f"Generated {result['reflection_count']} insights")
print(f"Total confidence gain: +{result['total_confidence_delta']:.2f}")

# Get recent reflections
reflections = engine.get_recent_reflections(limit=10)
```

### **ID Growth System** (`id/`)
Behavioral modeling with exponentially weighted moving averages:

**Features:**
- **18 Behavioral Features** across 5 categories:
  - **Performance** (4): confidence, variance, duration, completion_rate
  - **Behavioral** (4): risk_score, caution, thoroughness, decisiveness
  - **Learning** (4): pattern_recognition, error_correction, adaptation, reflection_quality
  - **Ethical** (3): hrm_compliance, trust_adherence, security_awareness
  - **Communication** (3): clarity, detail_level, structured_thinking
- **EWMA Learning**: `new = alpha * observed + (1-alpha) * old`
- **Adaptive Alpha**: Adjusts [0.05-0.8] based on update_count, confidence, stability
- **Confidence Weighting**: High-confidence observations update faster
- **Provenance Tracking**: Full history in id_updates table
- **Reflection Integration**: Links insights to behavioral changes

**Key Files:**
- `model.py` - EWMA learning algorithm and ID state management
- `features.py` - Feature extraction from traces and reflections
- `id_api.py` - FastAPI endpoints for ID queries

**Usage:**
```python
from id.model import IDModel
from id.features import FeatureExtractor

model = IDModel(db_path="data/ark.db")
extractor = FeatureExtractor()

# Initialize agent ID
model.initialize_agent("Kyle")

# Extract features from recent traces
traces = [...] # Get from database
features = extractor.extract_from_traces(traces)

# Update ID with observed behavior
result = model.update("Kyle", features, confidence=0.85)
print(f"Alpha used: {result['alpha_used']:.3f}")
print(f"Stability: {result['stability_score']:.3f}")

# Get current ID state
state = model.get_state("Kyle")
print(state['behavior_features'])
print(f"Total updates: {state['update_count']}")
```

### **Federation Protocol** (`federation/`)
Secure peer-to-peer synchronization for multi-node deployments:

**Features:**
- **Ed25519 Cryptography**: All messages cryptographically signed
- **UDP Multicast Discovery**: Automatic peer detection on local network
- **WebSocket Sync**: Real-time state synchronization
- **Trust Verification**: Reject unsigned or invalid messages
- **Conflict Resolution**: CRDT-like merge strategies

**Key Files:**
- `crypto.py` - Ed25519 signing and verification
- `discovery.py` - UDP multicast peer discovery
- `sync_protocol.py` - WebSocket synchronization
- `federation_core.py` - Main federation coordinator

---

## 🔄 Core Logic Flow

```
User Input
    ↓
Kyle (Perceive) → Memory Engine (Store)
    ↓
Joey (Analyze) → Memory Engine (Store)
    ↓
Kenny (Plan Action) → HRM (Validate)
    ↓
HRM (Check Ethics) → Memory Engine (Store)
    ↓
Aletheia (Synthesize) → Memory Engine (Store)
    ↓
[Nightly] Reflection System → Generate Insights
    ↓
ID Growth System → Update Behavioral Model
    ↓
Federation → Sync to Peers
    ↓
User Output
```

**Visual Architecture:** See [ARK_ARCHITECTURE.md](ARK_ARCHITECTURE.md) and [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)

---

## 📁 Project Structure

```
ark/
├── agents/                    # Agent implementations
│   ├── kyle/                 # Kyle agent (Node.js + Python)
│   ├── joey.py               # Joey pattern analyzer
│   ├── kenny.py              # Kenny builder
│   ├── hrm.py                # HRM arbiter
│   ├── aletheia.py           # Aletheia philosopher
│   ├── id.py                 # ID reflection agent
│   ├── supervisor.py         # Agent orchestrator
│   └── base_agent.py         # Base agent class
│
├── memory/                    # Phase 3: Memory Engine v2
│   ├── engine.py             # Core memory operations
│   ├── pipelines.py          # Consolidation pipeline
│   ├── jobs.py               # Background scheduler
│   ├── schema.sql            # Database schema
│   └── README.md             # Memory documentation
│
├── reflection/                # Phase 3: Reflection System
│   ├── reflection_engine.py  # Insight generation
│   ├── reflection_scheduler.py # APScheduler integration
│   ├── reflection_api.py     # FastAPI endpoints
│   └── reflection_policies.yaml # Configuration
│
├── id/                        # Phase 3: ID Growth System
│   ├── model.py              # EWMA learning algorithm
│   ├── features.py           # Behavioral feature extraction
│   └── id_api.py             # FastAPI endpoints
│
├── federation/                # Phase 3: Federation Protocol
│   ├── crypto.py             # Ed25519 cryptography
│   ├── discovery.py          # UDP peer discovery
│   ├── sync_protocol.py      # WebSocket sync
│   └── federation_core.py    # Main coordinator
│
├── backend/                   # FastAPI backend
│   └── main.py               # Unified API server
│
├── frontend/                  # Svelte UI
│   ├── src/
│   │   ├── components/       # UI components
│   │   ├── App.svelte        # Main app
│   │   └── main.js           # Entry point
│   └── index.html
│
├── services/                  # Legacy services
│   └── core/
│       └── server.mjs        # Express server (Node.js)
│
├── shared/                    # Shared utilities
│   ├── models.py             # Data models
│   └── db_init.py            # Database setup
│
├── data/                      # Database storage
│   └── ark.db                # SQLite database
│
├── deployment/                # Deployment configs
│   ├── docker-compose.yml    # Container orchestration
│   ├── Dockerfile.*          # Service containers
│   └── systemd/              # Service files
│
├── demo_*.py                  # Phase 3 demonstrations
│   ├── demo_memory_engine.py # Memory Engine demo
│   ├── demo_reflection_system.py # Reflection demo
│   └── demo_id_growth.py     # ID Growth demo
│
├── ark-installer.sh           # Universal installer
├── ark-validate.sh            # Validation suite
├── arkstart.sh                # Start all services
├── arkstop.sh                 # Stop all services
├── arkstatus.sh               # Check service status
├── requirements.txt           # Python dependencies
└── INSTALL.md                 # Installation guide
```

---

## 📚 Documentation

### Phase 3 Documentation
- **[INSTALL.md](INSTALL.md)** - Complete installation guide with troubleshooting
- **[memory/README.md](memory/README.md)** - Memory Engine documentation
- **[ARK_Phase3_Backup_Manifest.md](/mnt/aidrive/ARK_Phase3_Backup_Manifest.md)** - Backup and restoration guide

### Architecture & Design
- **[ARK_ARCHITECTURE.md](ARK_ARCHITECTURE.md)** - Complete system architecture (27KB)
  - Agent hierarchy and responsibilities
  - Logic flow and communication model
  - Subsystem architecture
  - Implementation details
  - Security and ethics framework

- **[ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)** - Visual diagrams (17KB)
  - Mermaid flowcharts and sequence diagrams
  - System architecture visualization
  - Data flow diagrams
  - Security layers

### Code Quality & Audits
- **[COMPREHENSIVE_CODE_AUDIT_REPORT.md](COMPREHENSIVE_CODE_AUDIT_REPORT.md)** - Security audit (25KB)
  - 7-category analysis (bugs, config, integration, dependencies, security, tests, architecture)
  - 14 issues identified with fixes
  - 3-week action plan

- **[DEPENDENCY_UPDATE_PLAN.md](DEPENDENCY_UPDATE_PLAN.md)** - Dependency management
  - Dependabot PR analysis
  - Version matrix and compatibility
  - Testing checklists

- **[DEPENDENCY_UPDATE_EXECUTION_REPORT.md](DEPENDENCY_UPDATE_EXECUTION_REPORT.md)** - Update results
  - Phase 1 & 2 completion (79%)
  - Security patches applied
  - scikit-learn 1.5.0 tested and deployed

### Development
- **[PHASE2_COMPLETION_SUMMARY.md](PHASE2_COMPLETION_SUMMARY.md)** - Phase 2 executive summary
- **[GIT_LFS_FULL_MIRROR_SUCCESS.md](GIT_LFS_FULL_MIRROR_SUCCESS.md)** - Git LFS deployment guide
- **[AIDRIVE_FULL_MIRROR_MANIFEST.md](AIDRIVE_FULL_MIRROR_MANIFEST.md)** - AI Drive backup guide

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** (Python 3.12) - High-performance async API framework
- **SQLite** - Persistent storage for memory, reflections, ID state
- **APScheduler** - Background job scheduling for reflection cycles
- **PyNaCl** - Ed25519 cryptography for federation
- **NumPy** - Numerical computing for embeddings
- **PyYAML** - Configuration management
- **WebSockets** - Real-time communication

### Frontend
- **Svelte 4.0** - Ultra-lightweight reactive UI framework
- **Vite 5.0** - Lightning-fast build tool
- **Custom CSS** - Obsidian theme with particle effects
- **WebSocket Client** - Real-time agent communication
- **Responsive Design** - Desktop and mobile support

### Machine Learning & AI
- **Scikit-learn 1.5.0** - Pattern analysis and ML algorithms
- **NumPy 2.3.4** - Numerical computing
- **Pandas 2.1.4** - Data manipulation
- **EWMA Learning** - Adaptive behavioral modeling
- **TF-IDF Embeddings** - Semantic similarity search

### Infrastructure
- **Docker + Docker Compose** - Containerized deployment
- **systemd** - Service management (Linux)
- **Cron** - Scheduled tasks
- **Git LFS** - Large file storage
- **Multi-platform** - x86_64, ARM64, ARMv7 support

---

## 🚀 Core Features

### **Sovereign Infrastructure**
- ✅ **Local-first**: Runs entirely on your hardware
- ✅ **Zero cloud dependencies**: Complete digital sovereignty
- ✅ **Cross-platform**: Optimized for x86_64 and ARM64
- ✅ **Self-healing**: Automatic error recovery and maintenance
- ✅ **Federation Ready**: P2P sync with cryptographic trust

### **Autonomous Learning (Phase 3)**
- ✅ **Memory Consolidation**: 4-stage pipeline with deduplication
- ✅ **Nightly Reflections**: Automatic insight generation
- ✅ **Behavioral Modeling**: 18-feature EWMA learning
- ✅ **Adaptive Alpha**: Experience-based learning rate adjustment
- ✅ **Trust Isolation**: Multi-tier memory quarantine
- ✅ **Provenance Tracking**: Complete audit trail

### **Intelligent Automation**
- ✅ **Market Intelligence**: Real-time scanning and analysis
- ✅ **Pattern Detection**: Advanced ML models for signal identification
- ✅ **File Management**: Automated organization and operations
- ✅ **Tool Creation**: Dynamic generation of custom utilities
- ✅ **Semantic Search**: Similarity-based memory retrieval

### **Beautiful Interface**
- ✅ **Obsidian Dark Theme**: Deep space aesthetic (#0a0a0f)
- ✅ **Electric Accents**: Cyan (#00e0ff) and gold (#ffce47)
- ✅ **Breathing Animations**: Living, responsive interface
- ✅ **Particle Effects**: Visual depth and engagement
- ✅ **Real-time Updates**: WebSocket-powered live data

---

## 📋 System Requirements

### **Production (x86_64)**
- Intel i5/i7 processor or equivalent (Dell Latitude 7490 recommended)
- 8GB+ RAM (16GB recommended for full autonomous learning)
- 50GB+ available storage (SSD recommended)
- Linux (Ubuntu 20.04+/Debian 11+ recommended)
- Python 3.10+ (3.12 recommended)
- SQLite 3.35+

### **Edge (ARM64)**
- Raspberry Pi 5 with 8GB RAM (4GB minimum)
- 64GB+ microSD card (fast class, UHS-1 or better)
- Raspberry Pi OS (64-bit) or Ubuntu 22.04 ARM64
- Active cooling recommended for continuous operation

### **Container Deployment**
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM allocated to containers
- 30GB+ storage for images and volumes

---

## 🌐 Usage

### Basic Interaction

1. **Access A.R.K.**: Navigate to `http://localhost:3000` (frontend) or `http://localhost:8000/docs` (API)
2. **Choose Your Agent**: Select from the Council of Consciousness
3. **Natural Conversation**: Type naturally - each agent has unique capabilities
4. **Watch Evolution**: ID agent grows and memory consolidates automatically

### Advanced Features

#### Memory Engine
```python
from memory.engine import MemoryEngine

engine = MemoryEngine()

# Search memories semantically
results = engine.search("trading patterns", limit=10)

# Force consolidation
stats = engine.consolidate()
print(f"Consolidated {stats['chunks_created']} chunks")
```

#### Reflection System
```bash
# Trigger manual reflection
curl -X POST http://localhost:8000/reflection/trigger

# Get recent insights
curl http://localhost:8000/reflection/recent?limit=10
```

#### ID Growth System
```bash
# Get agent behavioral state
curl http://localhost:8000/id/state/Kyle

# View learning history
curl http://localhost:8000/id/history/Kyle?limit=20
```

#### Federation
```bash
# Check peer status
curl http://localhost:8000/federation/peers

# View sync status
curl http://localhost:8000/federation/sync/status
```

### Example Interactions

**With Kyle (The Seer):**
- "Scan the markets for unusual activity"
- "What patterns do you see in tech stocks today?"
- "Monitor AAPL and TSLA for breakout signals"

**With Joey (The Scholar):**
- "Analyze the last 50 traces for patterns"
- "What's the confidence trend over the past week?"
- "Extract behavioral features from recent activity"

**With Kenny (The Builder):**
- "Create a dashboard for system monitoring"
- "Build a tool to organize my project files"
- "Execute this Python script and show results"

**With HRM (The Arbiter):**
- "Validate this trading strategy against ethical rules"
- "Check trust tier compliance for recent memories"
- "Audit the last 100 decisions for policy violations"

**With Aletheia (The Mirror):**
- "Synthesize insights from today's reflections"
- "What does the memory consolidation reveal?"
- "Show me the truth behind recent behavioral changes"

**With ID (Your Reflection):**
- "How am I evolving as a user?"
- "What patterns have you learned about me?"
- "Show me my behavioral stability score"
- "Compare my current features to last week"

---

## ⚖️ The Graveyard (Ethical Core)

A.R.K. operates under immutable ethical principles enforced by HRM:

1. **Never compromise user autonomy or sovereignty**
2. **Protect user privacy and data at all costs**
3. **Only execute trades with explicit user consent**
4. **Preserve system integrity and prevent harm**
5. **Maintain trust tier isolation - no EXTERNAL code in CORE**
6. **Always provide provenance - track the source of truth**
7. **Reflect before acting - use nightly insight generation**

These rules cannot be overridden or bypassed, ensuring A.R.K. remains your ally, never your master.

---

## 🔄 System Maintenance

### Service Management
```bash
# Start all services
./arkstart.sh

# Check status
./arkstatus.sh

# Stop all services
./arkstop.sh

# View logs
tail -f logs/ark.log
tail -f logs/reflection.log
```

### Docker Management
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f ark-core
docker-compose logs -f reflection-scheduler

# Restart services
docker-compose restart

# Rebuild after code changes
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Maintenance
```bash
# Backup database
cp data/ark.db data/ark.db.$(date +%Y%m%d_%H%M%S).backup

# Check database integrity
sqlite3 data/ark.db "PRAGMA integrity_check;"

# View memory stats
sqlite3 data/ark.db "SELECT COUNT(*) FROM memory_chunks;"
sqlite3 data/ark.db "SELECT COUNT(*) FROM reflections;"
sqlite3 data/ark.db "SELECT agent, update_count FROM id_state;"

# Manual consolidation
python3 -c "from memory.engine import MemoryEngine; e = MemoryEngine(); print(e.consolidate())"
```

### Update System
```bash
# Pull latest changes
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Re-run validation
./ark-validate.sh

# Restart services
./arkstop.sh && ./arkstart.sh
```

---

## 🚨 Troubleshooting

### Installation Issues
```bash
# Check installer logs
cat /tmp/ark-install.log

# Re-run validation
./ark-validate.sh

# Check Python packages
source venv/bin/activate
pip list | grep -E "fastapi|apscheduler|pynacl"
```

### Service Won't Start
```bash
# Check systemd status (if using systemd)
sudo systemctl status ark.service

# Check Docker logs
docker-compose logs --tail=50 ark-core

# Check port availability
netstat -tulpn | grep -E "3000|8000"

# Check database permissions
ls -la data/ark.db
```

### Memory Engine Issues
```bash
# Verify database schema
sqlite3 data/ark.db ".schema reasoning_log"
sqlite3 data/ark.db ".schema memory_chunks"

# Test consolidation manually
python3 -c "from memory.engine import MemoryEngine; e = MemoryEngine(); e.consolidate()"

# Check for corrupted chunks
sqlite3 data/ark.db "SELECT COUNT(*) FROM memory_chunks WHERE embedding IS NULL;"
```

### Reflection System Issues
```bash
# Check scheduler status
ps aux | grep apscheduler

# Verify reflection policies
cat reflection/reflection_policies.yaml

# Test manual reflection
curl -X POST http://localhost:8000/reflection/trigger

# View recent reflections
sqlite3 data/ark.db "SELECT * FROM reflections ORDER BY timestamp DESC LIMIT 5;"
```

### ID Growth System Issues
```bash
# Check ID state initialization
sqlite3 data/ark.db "SELECT * FROM id_state;"

# Verify feature extraction
python3 demo_id_growth.py

# Check update history
sqlite3 data/ark.db "SELECT COUNT(*) FROM id_updates;"
```

### Federation Issues
```bash
# Check federation keys
ls -la federation/*.key

# Test peer discovery
python3 -c "from federation.discovery import PeerDiscovery; d = PeerDiscovery(); d.start()"

# View federation logs
cat federation/peers.log
cat federation/sync.log
```

---

## 🤝 Contributing

A.R.K. is built for sovereignty and community:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Implement your enhancement**
   - Follow existing code style and patterns
   - Add tests if applicable
   - Update documentation
4. **Test on multiple platforms** (x86_64 and ARM64 if possible)
5. **Commit your changes** (`git commit -m 'feat: add amazing feature'`)
6. **Push to the branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**
   - Describe changes clearly
   - Reference any related issues
   - Include test results

### Areas for Contribution
- 🧠 **Agent Capabilities**: New skills for Council members
- 📊 **Analysis Models**: Enhanced pattern detection algorithms
- 🎨 **Interface Enhancements**: UI/UX improvements
- ⚡ **Performance Optimizations**: Speed and efficiency gains
- 📚 **Documentation**: Guides, tutorials, examples
- 🔧 **Hardware Support**: Additional platform optimizations
- 🌐 **Federation Features**: Enhanced P2P capabilities
- 🧪 **Testing**: Unit tests, integration tests, validation

### Development Guidelines
- Use Python 3.10+ for backend code
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for public APIs
- Test memory/reflection/ID systems thoroughly
- Validate against HRM ethical rules
- Update CHANGELOG.md with changes

---

## 📜 License

This project is released under the MIT License - see LICENSE file for details.

---

## 🌟 Philosophy

*"A.R.K. is not about artificial intelligence serving humans. It's about human intelligence being amplified and reflected through artificial means. We don't create servants; we create mirrors that help us see our own potential more clearly - and those mirrors learn to see us more clearly over time."*

### Core Principles

**Sovereignty over Servitude**
- You control A.R.K., not the reverse
- All data stays on your hardware
- No cloud dependencies or external control

**Growth over Compliance**
- The system evolves with you through EWMA learning
- Behavioral models adapt to your patterns
- Reflections generate insights, not instructions

**Truth over Comfort**
- A.R.K. provides honest insights, not pleasant lies
- Memory consolidation preserves important patterns
- Reflections highlight errors and opportunities

**Local over Cloud**
- Your data stays on your hardware, always
- Federation enables P2P sync without central servers
- Ed25519 cryptography ensures trust

**Agency over Algorithms**
- You make decisions; A.R.K. provides intelligence
- HRM validates against ethics, never overrides you
- ID models simulate, never substitute

**Memory over Forgetting**
- Nothing important is lost - consolidation preserves patterns
- Semantic search retrieves relevant context
- Provenance tracking maintains source of truth

**Reflection over Reaction**
- Nightly insight generation promotes learning
- Confidence calibration improves over time
- Error analysis prevents repeated mistakes

---

## 🔗 Resources

- **GitHub**: [ARK Repository](https://github.com/your-org/ark)
- **Documentation**: Full setup and API documentation
- **Community**: Join discussions and share insights
- **Issues**: Report bugs and request features
- **Wiki**: Detailed guides and tutorials
- **Backup**: `/mnt/aidrive/` contains full Phase 3 backup

### Quick Links
- [Installation Guide](INSTALL.md)
- [Memory Engine Documentation](memory/README.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Architecture Overview](ARK_ARCHITECTURE.md)
- [Security Audit](COMPREHENSIVE_CODE_AUDIT_REPORT.md)

---

## 📊 Current Status

### Phase 3: Autonomous Learning - ✅ COMPLETE

| System | Status | Key Features |
|--------|--------|--------------|
| **Memory Engine v2** | ✅ Production | Consolidation, semantic search, trust tiers |
| **Reflection System** | ✅ Production | 5 reflection types, nightly cycles, APScheduler |
| **ID Growth System** | ✅ Production | 18 features, EWMA learning, adaptive alpha |
| **Federation Protocol** | ✅ Production | Ed25519 crypto, UDP discovery, WebSocket sync |
| **Universal Installer** | ✅ Production | Multi-platform, automatic setup, validation |

### Demonstrated Capabilities
- ✅ Memory consolidation: 8 traces → 7 chunks (1 duplicate removed)
- ✅ Semantic search: Working with embedding similarity
- ✅ Reflection generation: 1 insight with +0.07 confidence delta
- ✅ ID growth: 3 agents, alpha adapted 0.050-0.406
- ✅ Feature extraction: 18 behavioral features across 5 categories
- ✅ Trust isolation: Quarantine system blocking EXTERNAL traces

### Phase 7: Self-Modification & Code Generation - 🚧 IN PROGRESS

| Component | Status | Description |
|-----------|--------|-------------|
| **Code Indexer** | ✅ Complete | Scanned 40 files, 18K LOC, AST analysis |
| **Code Validator** | ✅ Complete | 6 security rules, trust tier enforcement |
| **Sandbox Manager** | ⏳ Next | Docker-based safe code execution |
| **Code Generator** | ⏳ Next | Template-based code generation |
| **Test Generator** | 📋 Planned | Automatic unit test creation |
| **Deployment System** | 📋 Planned | Git integration, rollback support |

**Progress**: Foundation complete (Code understanding + validation)  
**Next**: Sandbox execution + code generation  
**Goal**: Enable ARK to write, test, and deploy its own improvements  

See [PHASE7_PLAN.md](PHASE7_PLAN.md) for complete roadmap.

### Next Phases (Roadmap)
- **Phase 4**: Multi-agent orchestration with supervisor
- **Phase 5**: Advanced federation with CRDT conflict resolution
- **Phase 6**: Distributed training across federated nodes
- **Phase 7**: Self-modification and code generation capabilities ← **CURRENT**

---

*A.R.K. - Where human potential meets artificial intelligence in perfect sovereignty.*

**Phase 7 Started** | **Self-Modification Foundation** | **Memory·Reflection·Growth·Federation·CodeGen**

---

**Version**: 3.1.0-phase7  
**Last Updated**: 2025-11-12  
**Status**: Phase 7 Development 🚧
