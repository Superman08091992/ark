# ARK Architecture - Visual Diagrams

**Quick visual reference for ARK's architecture and data flow**

---

## 🎯 Core Logic Flow

```mermaid
graph TD
    A[👤 USER INPUT<br/>ENVIRONMENT] -->|Commands, Queries,<br/>Market Data| B
    
    B[🔍 KYLE<br/>Scanner<br/>Perception] -->|Structured Events<br/>Normalized Data| C
    
    C[🧠 JOEY<br/>Pattern Screener<br/>Cognition] -->|Pattern Summaries<br/>Action Proposals| D
    
    D[⚡ KENNY<br/>Executor<br/>Action] -->|Execution Logs<br/>Results| E
    
    E[✅ HRM<br/>Validator<br/>Reasoning] -->|Validation Traces<br/>Approvals| F
    
    F[🔮 ALETHEIA<br/>Symbolic Self<br/>Reflection] -->|Reports<br/>Insights<br/>Memory Updates| G
    
    G[📊 OUTPUT<br/>User Feedback<br/>System Memory]
    
    H[📜 GRAVEYARD<br/>Immutable Ethics] -.->|Referenced by| E
    F -->|Updates| I[💾 MUTABLE CORE<br/>Adaptive State]
    
    style A fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    style B fill:#fff3cd,stroke:#856404,stroke-width:2px
    style C fill:#d4edda,stroke:#155724,stroke-width:2px
    style D fill:#f8d7da,stroke:#721c24,stroke-width:2px
    style E fill:#d1ecf1,stroke:#0c5460,stroke-width:2px
    style F fill:#e2e3e5,stroke:#383d41,stroke-width:2px
    style G fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    style H fill:#f8d7da,stroke:#721c24,stroke-width:4px,stroke-dasharray: 5 5
    style I fill:#d4edda,stroke:#155724,stroke-width:3px
```

**Key:**
- 🔍 **Kyle**: Sensory input - "What's happening?"
- 🧠 **Joey**: Pattern recognition - "What does it mean?"
- ⚡ **Kenny**: Action execution - "What should I do?"
- ✅ **HRM**: Logic validation - "Is this correct and aligned?"
- 🔮 **Aletheia**: Self-reflection - "What is true and why?"

---

## 🔄 Agent Communication Sequence

```mermaid
sequenceDiagram
    autonumber
    
    participant 👤 User
    participant 🔍 Kyle
    participant 🧠 Joey
    participant ⚡ Kenny
    participant ✅ HRM
    participant 🔮 Aletheia
    participant 💾 Memory
    
    👤 User->>🔍 Kyle: 💬 Command / Query
    Note over 🔍 Kyle: Scrapes data<br/>Filters signals<br/>Normalizes format
    🔍 Kyle->>🧠 Joey: 📦 Data Packet
    
    Note over 🧠 Joey: Pattern matching<br/>ML analysis<br/>Confidence scoring
    🧠 Joey->>⚡ Kenny: 🎯 Action Proposal
    
    Note over ⚡ Kenny: Prepares execution<br/>Position sizing<br/>Order creation
    ⚡ Kenny->>✅ HRM: 📋 Execution Log
    
    Note over ✅ HRM: Logic check<br/>Ethics check<br/>Risk assessment
    ✅ HRM-->>📜 Graveyard: Check Rules
    📜 Graveyard-->>✅ HRM: Rules OK
    ✅ HRM->>🔮 Aletheia: ✔️ Validation Trace
    
    Note over 🔮 Aletheia: Synthesize results<br/>Update knowledge<br/>Reflect on cycle
    🔮 Aletheia->>💾 Memory: 💾 State Update
    🔮 Aletheia->>👤 User: 📊 Reflective Report
    
    👤 User->>🔍 Kyle: 🔄 New query
```

---

## 🏗️ System Architecture (Full Stack)

```mermaid
graph TB
    subgraph "🌍 External World"
        EXT1[Markets & Exchanges]
        EXT2[APIs & Web Services]
        EXT3[User Interface]
    end
    
    subgraph "👁️ Perception Layer"
        KYLE[🔍 Kyle Scanner<br/>Data Ingestion]
    end
    
    subgraph "🧠 Cognition Layer"
        JOEY[🧠 Joey Pattern Screener]
        ML[🤖 ML Models<br/>Scikit-learn, LSTM]
    end
    
    subgraph "⚡ Action Layer"
        KENNY[⚡ Kenny Executor]
        BROKERS[🏦 Brokers<br/>Alpaca, Coinbase, IB]
    end
    
    subgraph "✅ Governance Layer"
        HRM[✅ HRM Validator]
        GY[📜 Graveyard<br/>Immutable Ethics]
    end
    
    subgraph "🔮 Reflection Layer"
        ALETHEIA[🔮 Aletheia<br/>Symbolic Self]
        MC[💾 Mutable Core<br/>Memory & State]
    end
    
    subgraph "👀 Monitoring"
        WD[🚨 Watchdog<br/>System Monitor]
        ID[👤 ID Agent<br/>User Replica]
    end
    
    subgraph "💾 Data Storage"
        DB[(🗄️ PostgreSQL<br/>Event Store)]
        REDIS[(⚡ Redis<br/>Cache & PubSub)]
        FILES[📁 File Storage<br/>Logs, Configs]
    end
    
    EXT1 & EXT2 & EXT3 -->|Raw data| KYLE
    KYLE -->|Structured events| JOEY
    JOEY <-->|Patterns| ML
    JOEY -->|Action proposals| KENNY
    KENNY <-->|Orders| BROKERS
    KENNY -->|Pending actions| HRM
    HRM -.->|Check rules| GY
    HRM -->|Validation| ALETHEIA
    ALETHEIA -->|Updates| MC
    ALETHEIA -->|Reports| EXT3
    
    KYLE & JOEY & KENNY & HRM & ALETHEIA -->|Store data| DB
    JOEY & KENNY -->|Cache| REDIS
    KYLE & KENNY -->|Logs| FILES
    
    WD -->|Monitor all| KYLE & JOEY & KENNY & HRM & ALETHEIA
    ID -.->|Simulate| ALETHEIA
    
    style KYLE fill:#fff3cd,stroke:#856404,stroke-width:2px
    style JOEY fill:#d4edda,stroke:#155724,stroke-width:2px
    style KENNY fill:#f8d7da,stroke:#721c24,stroke-width:2px
    style HRM fill:#d1ecf1,stroke:#0c5460,stroke-width:2px
    style ALETHEIA fill:#e2e3e5,stroke:#383d41,stroke-width:2px
    style GY fill:#f8d7da,stroke:#721c24,stroke-width:4px
    style MC fill:#d4edda,stroke:#155724,stroke-width:3px
```

---

## 🔐 Subsystem Interlink (Security Focus)

```mermaid
graph TB
    subgraph "🔒 Immutable Layer"
        GY[📜 GRAVEYARD<br/>Immutable Ethics<br/>Read-Only<br/>Manual Admin Only]
    end
    
    subgraph "✅ Validation Layer"
        HRM[✅ HRM Validator<br/>Logic & Ethics Check<br/>Risk Assessment<br/>Audit Trail]
    end
    
    subgraph "🔮 Reflection Layer"
        AL[🔮 Aletheia Core<br/>Truth Synthesis<br/>Self-Awareness<br/>Memory Management]
    end
    
    subgraph "💾 Adaptive Layer"
        MC[💾 Mutable Core<br/>State Storage<br/>Learned Preferences<br/>Behavioral Patterns]
    end
    
    subgraph "👀 Monitoring Layer"
        WD[🚨 Watchdog<br/>Health Checks<br/>Anomaly Detection<br/>Emergency Halt]
        ID[👤 ID Agent<br/>User Simulation<br/>Behavioral Mirror<br/>Test Mode]
    end
    
    GY -.->|Referenced by<br/>Cannot Modify| HRM
    HRM -->|Validated Actions<br/>Compliance Data| AL
    AL -->|State Updates<br/>Memory Writes| MC
    WD -->|Monitors<br/>Can Halt| HRM
    WD -->|Monitors<br/>Can Halt| AL
    ID -.->|Simulates<br/>Testing Only| AL
    MC -.->|Read State<br/>No Ethics Changes| GY
    
    style GY fill:#f8d7da,stroke:#721c24,stroke-width:5px
    style HRM fill:#d1ecf1,stroke:#0c5460,stroke-width:3px
    style AL fill:#e2e3e5,stroke:#383d41,stroke-width:3px
    style MC fill:#d4edda,stroke:#155724,stroke-width:3px
    style WD fill:#fff3cd,stroke:#856404,stroke-width:2px
    style ID fill:#d4edda,stroke:#155724,stroke-width:2px
```

**Security Boundaries:**
- 📜 **Graveyard**: Immutable, read-only, admin-only changes
- ✅ **HRM**: Acts as gatekeeper, enforces ethics
- 💾 **Mutable Core**: Learns but cannot modify ethics
- 🚨 **Watchdog**: Independent monitor with halt authority

---

## 🔁 Recursive Self-Improvement Loop

```mermaid
graph LR
    A[1️⃣ Complete Cycle] -->|Action Results<br/>Outcomes<br/>Errors| B[2️⃣ Aletheia<br/>Archives]
    
    B -->|Update Validation<br/>Weights| C[3️⃣ HRM<br/>Updates Rules]
    
    C -->|New Watchlists<br/>Filter Adjustments| D[4️⃣ Kyle<br/>Adapts Sources]
    
    D -->|Retrain Models<br/>New Patterns| E[5️⃣ Joey<br/>Evolves ML]
    
    E -->|Confidence Updates<br/>Position Sizing| F[6️⃣ Kenny<br/>Improves Execution]
    
    F -->|Better Decisions<br/>Next Iteration| A
    
    G[📜 Graveyard<br/>Ethics Unchanged] -.->|Bounds Learning| A & B & C & D & E & F
    
    style A fill:#e2e3e5,stroke:#383d41,stroke-width:2px
    style B fill:#e2e3e5,stroke:#383d41,stroke-width:2px
    style C fill:#d1ecf1,stroke:#0c5460,stroke-width:2px
    style D fill:#fff3cd,stroke:#856404,stroke-width:2px
    style E fill:#d4edda,stroke:#155724,stroke-width:2px
    style F fill:#f8d7da,stroke:#721c24,stroke-width:2px
    style G fill:#f8d7da,stroke:#721c24,stroke-width:4px,stroke-dasharray: 5 5
```

**Learning Cycle:**
1. **Complete execution cycle** with results
2. **Aletheia archives** outcomes in memory
3. **HRM updates** validation weights and red flags
4. **Kyle adapts** data sources and filters
5. **Joey evolves** ML models and patterns
6. **Kenny improves** execution strategies
7. **Return to step 1** with enhanced capabilities

**Key Principle:** Learning improves strategy, not ethics

---

## 📊 Agent Responsibility Matrix

```mermaid
graph TD
    subgraph "Agent Roles"
        A1[🔍 Kyle<br/>WHAT'S HAPPENING?<br/>Perception]
        A2[🧠 Joey<br/>WHAT DOES IT MEAN?<br/>Cognition]
        A3[⚡ Kenny<br/>WHAT SHOULD I DO?<br/>Action]
        A4[✅ HRM<br/>IS THIS CORRECT?<br/>Reasoning]
        A5[🔮 Aletheia<br/>WHAT IS TRUE?<br/>Reflection]
    end
    
    subgraph "Domains"
        D1[Data Ingestion<br/>APIs, Markets, Web]
        D2[Pattern Recognition<br/>ML, Analysis, Scoring]
        D3[Execution<br/>Orders, Commands, Actions]
        D4[Validation<br/>Ethics, Logic, Risk]
        D5[Truth & Memory<br/>Learning, Archiving]
    end
    
    A1 -.->|Responsible for| D1
    A2 -.->|Responsible for| D2
    A3 -.->|Responsible for| D3
    A4 -.->|Responsible for| D4
    A5 -.->|Responsible for| D5
    
    D1 -->|Feeds| D2
    D2 -->|Feeds| D3
    D3 -->|Feeds| D4
    D4 -->|Feeds| D5
    D5 -.->|Improves| D1
    
    style A1 fill:#fff3cd,stroke:#856404,stroke-width:2px
    style A2 fill:#d4edda,stroke:#155724,stroke-width:2px
    style A3 fill:#f8d7da,stroke:#721c24,stroke-width:2px
    style A4 fill:#d1ecf1,stroke:#0c5460,stroke-width:2px
    style A5 fill:#e2e3e5,stroke:#383d41,stroke-width:2px
```

---

## 🗺️ Data Flow - From Market to Action

```mermaid
graph LR
    M[📈 Market Data<br/>BTC Price: $45,230<br/>Volume Spike] -->|1| K[🔍 Kyle]
    
    K -->|2: Structured Event<br/>price_alert, confidence: 0.95| J[🧠 Joey]
    
    J -->|3: Pattern Detected<br/>bullish_breakout<br/>confidence: 0.87<br/>R:R = 2.7| KE[⚡ Kenny]
    
    KE -->|4: Pending Order<br/>BUY 0.1 BTC<br/>@ $45,230| H[✅ HRM]
    
    H -->|5: Validation<br/>✅ Logic OK<br/>✅ Ethics OK<br/>✅ Risk OK| A[🔮 Aletheia]
    
    A -->|6: Approved ✅<br/>Execute| KE
    
    KE -->|7: Order Filled<br/>0.1 BTC @ $45,235<br/>Slippage: $5| B[🏦 Broker]
    
    B -->|8: Confirmation| A
    
    A -->|9: Report<br/>Action successful<br/>Learn from outcome| U[👤 User]
    
    GY[📜 Graveyard] -.->|Check Ethics| H
    MC[💾 Memory] <-.->|Update State| A
    
    style M fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    style K fill:#fff3cd,stroke:#856404,stroke-width:2px
    style J fill:#d4edda,stroke:#155724,stroke-width:2px
    style KE fill:#f8d7da,stroke:#721c24,stroke-width:2px
    style H fill:#d1ecf1,stroke:#0c5460,stroke-width:2px
    style A fill:#e2e3e5,stroke:#383d41,stroke-width:2px
    style B fill:#cfe2ff,stroke:#084298,stroke-width:2px
    style U fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    style GY fill:#f8d7da,stroke:#721c24,stroke-width:3px,stroke-dasharray: 5 5
    style MC fill:#d4edda,stroke:#155724,stroke-width:2px,stroke-dasharray: 5 5
```

**Timeline:**
1. **T+0ms**: Market data arrives (Kyle)
2. **T+100ms**: Pattern detected (Joey)
3. **T+200ms**: Order prepared (Kenny)
4. **T+250ms**: Validation complete (HRM)
5. **T+300ms**: Approved (Aletheia)
6. **T+500ms**: Order placed (Broker)
7. **T+2000ms**: Confirmation received
8. **T+2100ms**: Learning updated
9. **T+2200ms**: User notified

---

## 🎯 Purpose Mapping (Visual)

```mermaid
mindmap
  root((🤖 ARK System))
    🔍 Kyle
      Perception
      Data Ingestion
      Signal Detection
      Event Streams
      Market Scanning
    🧠 Joey
      Cognition
      Pattern Recognition
      Context Analysis
      Confidence Scoring
      ML Models
    ⚡ Kenny
      Action
      Order Execution
      System Commands
      Broker Interface
      Risk Management
    ✅ HRM
      Reasoning
      Logic Validation
      Ethics Check
      Risk Assessment
      Audit Trail
    🔮 Aletheia
      Reflection
      Truth Synthesis
      Memory Management
      Self-Awareness
      Learning Loop
```

---

## 🛡️ Security Layers (Defense in Depth)

```mermaid
graph TD
    subgraph "Layer 1: Input Validation"
        L1[🔒 Pydantic Models<br/>Type Checking<br/>Range Validation]
    end
    
    subgraph "Layer 2: Authentication"
        L2[🔑 JWT Tokens<br/>Session Management<br/>Role-Based Access]
    end
    
    subgraph "Layer 3: Authorization"
        L3[👮 Permission Checks<br/>Agent Isolation<br/>User Boundaries]
    end
    
    subgraph "Layer 4: Business Logic"
        L4[✅ HRM Validation<br/>Ethics Enforcement<br/>Risk Limits]
    end
    
    subgraph "Layer 5: Audit & Monitor"
        L5[🚨 Watchdog<br/>Log Analysis<br/>Anomaly Detection]
    end
    
    subgraph "Layer 6: Immutable Ethics"
        L6[📜 Graveyard<br/>Read-Only Rules<br/>Admin-Only Changes]
    end
    
    EXT[🌐 External Input] --> L1
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 <-.-> L6
    L4 --> ACT[⚡ Action Execution]
    ACT --> L5
    L5 -.->|Can Halt| ACT
    
    style L1 fill:#d4edda,stroke:#155724,stroke-width:2px
    style L2 fill:#cfe2ff,stroke:#084298,stroke-width:2px
    style L3 fill:#fff3cd,stroke:#856404,stroke-width:2px
    style L4 fill:#d1ecf1,stroke:#0c5460,stroke-width:2px
    style L5 fill:#f8d7da,stroke:#721c24,stroke-width:2px
    style L6 fill:#f8d7da,stroke:#721c24,stroke-width:4px
```

**Defense Strategy:**
- 🔒 **Layer 1**: Reject malformed inputs
- 🔑 **Layer 2**: Verify identity
- 👮 **Layer 3**: Check permissions
- ✅ **Layer 4**: Validate against ethics
- 🚨 **Layer 5**: Monitor and alert
- 📜 **Layer 6**: Enforce immutable rules

---

## 📁 Directory Structure (Visual)

```
📦 ARK Repository
├── 🤖 agents/                 # Agent implementations
│   ├── 🔍 kyle.py             # Scanner
│   ├── 🧠 joey.py             # Pattern screener
│   ├── ⚡ kenny.py            # Executor
│   ├── ✅ hrm.py              # Validator
│   ├── 🔮 aletheia.py         # Reflective core
│   ├── 👤 id.py               # User replica
│   ├── 👷 supervisor.py       # Coordinator
│   └── 📋 base_agent.py       # Base class
│
├── 🌐 backend/                # FastAPI server
│   └── 🚀 main.py             # API endpoints
│
├── 🔗 shared/                 # Common modules
│   ├── 🗄️ db_init.py          # Database setup
│   └── 📊 models.py           # Data models
│
├── 📜 graveyard/              # Immutable ethics
│   └── ⚖️ ethics.py           # Core rules (READ-ONLY)
│
├── 💾 mutable_core/           # Adaptive state
│   ├── 🧠 memory.db           # Episodic memory
│   └── ⚙️ preferences.json    # Learned preferences
│
├── 🚨 monitoring/             # System health
│   └── 👁️ watchdog.py         # Monitor & alerts
│
├── ⚙️ config/                 # Configuration
│   ├── 📋 kyle_watchlists.json
│   └── 🎯 joey_patterns.json
│
├── 🎨 frontend/               # Svelte UI
│   ├── 🖼️ src/
│   └── 📦 package.json
│
├── 🧪 tests/                  # Test suite
│   ├── ✅ test_agents.py
│   ├── 🌐 test_backend_api.py
│   └── 🔐 test_hrm_validation.py
│
└── 📚 docs/                   # Documentation
    ├── 📖 ARK_ARCHITECTURE.md
    ├── 📊 ARCHITECTURE_DIAGRAMS.md (this file)
    └── 🔌 API_REFERENCE.md
```

---

## 🚀 Quick Start Flow

```mermaid
graph TD
    START[🎯 Start ARK] -->|1| ENV[📝 Configure .env<br/>Secrets, API keys]
    ENV -->|2| DEPS[📦 Install Dependencies<br/>pip install -r requirements.txt<br/>npm install]
    DEPS -->|3| DB[🗄️ Initialize Database<br/>python shared/db_init.py]
    DB -->|4| REDIS[⚡ Start Redis<br/>docker-compose up redis]
    REDIS -->|5| BACKEND[🚀 Start Backend<br/>uvicorn backend.main:app]
    BACKEND -->|6| FRONTEND[🎨 Start Frontend<br/>npm run dev]
    FRONTEND -->|7| HEALTH[✅ Check Health<br/>GET /api/health]
    HEALTH -->|8| READY[🎉 ARK Ready!<br/>http://localhost:8000]
    
    style START fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    style ENV fill:#fff3cd,stroke:#856404,stroke-width:2px
    style DEPS fill:#d4edda,stroke:#155724,stroke-width:2px
    style DB fill:#cfe2ff,stroke:#084298,stroke-width:2px
    style REDIS fill:#f8d7da,stroke:#721c24,stroke-width:2px
    style BACKEND fill:#d1ecf1,stroke:#0c5460,stroke-width:2px
    style FRONTEND fill:#e2e3e5,stroke:#383d41,stroke-width:2px
    style HEALTH fill:#d4edda,stroke:#155724,stroke-width:2px
    style READY fill:#d4edda,stroke:#155724,stroke-width:3px
```

---

## 📚 Legend

### Agent Symbols
- 🔍 **Kyle**: Scanner / Perception
- 🧠 **Joey**: Pattern Screener / Cognition
- ⚡ **Kenny**: Executor / Action
- ✅ **HRM**: Validator / Reasoning
- 🔮 **Aletheia**: Reflective Core / Truth
- 👤 **ID**: User Replica
- 👷 **Supervisor**: Agent Coordinator

### System Components
- 📜 **Graveyard**: Immutable Ethics (read-only)
- 💾 **Mutable Core**: Adaptive State (read/write by Aletheia)
- 🚨 **Watchdog**: System Monitor
- 🗄️ **Database**: PostgreSQL/SQLite
- ⚡ **Redis**: Cache & Pub/Sub
- 📁 **File Storage**: Logs & Configs

### Status Indicators
- ✅ Approved / Validated / Passed
- ❌ Rejected / Failed / Error
- ⚠️ Warning / Attention Required
- 🔄 In Progress / Processing
- ⏸️ Paused / Waiting
- 🔒 Secured / Protected
- 🔓 Unlocked / Open Access

---

**Diagrams Version:** 1.0  
**Format:** Mermaid (GitHub/GitLab compatible)  
**Last Updated:** 2025-11-10  
**View in**: GitHub, GitLab, or https://mermaid.live/
