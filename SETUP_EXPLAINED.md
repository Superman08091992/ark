# 📚 ARK Setup and Installation - Detailed Explanation

## Complete Guide to Understanding ARK Installation

This document explains **what happens** during installation, **why** each step is needed, and **how** the system works together.

---

## 🎯 Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Installation Methods Explained](#installation-methods-explained)
3. [What Each Command Does](#what-each-command-does)
4. [Directory Structure Explained](#directory-structure-explained)
5. [Service Startup Process](#service-startup-process)
6. [Data Flow and Communication](#data-flow-and-communication)
7. [Configuration Deep Dive](#configuration-deep-dive)
8. [Troubleshooting Explained](#troubleshooting-explained)

---

## 🏗️ System Architecture Overview

### The Big Picture

ARK is composed of **three main layers**:

```
┌─────────────────────────────────────────────────┐
│         FRONTEND (Dashboard UI)                 │
│  Port 4173 - Svelte/Vite - Browser Interface    │
└─────────────────┬───────────────────────────────┘
                  │ WebSocket (wss://)
                  │ Real-time Data
┌─────────────────▼───────────────────────────────┐
│         BACKEND (Python FastAPI)                │
│  Port 8101 - WebSocket Server - Data Sources    │
└─────────────────┬───────────────────────────────┘
                  │ SQL Queries
                  │ Redis Queries
┌─────────────────▼───────────────────────────────┐
│         DATA LAYER (Storage)                    │
│  SQLite Databases - Redis Cache - File System   │
└─────────────────────────────────────────────────┘
```

### Components

#### 1. Frontend (Browser)
- **Technology**: Svelte + Vite
- **Purpose**: Beautiful cyberpunk UI for monitoring
- **Port**: 4173 (production) or 5173 (dev)
- **Files**: `frontend/public/dashboard-demo.html`

#### 2. Backend (Python Server)
- **Technology**: FastAPI + WebSockets
- **Purpose**: Real-time data streaming, agent coordination
- **Port**: 8101
- **Files**: `reasoning_api.py`, `dashboard_websockets.py`, `dashboard_data_sources.py`

#### 3. Data Layer
- **SQLite**: `data/reasoning_logs.db`, `data/ark.db`
- **Redis**: Cache and federation data (optional)
- **Purpose**: Persistent storage and fast access

---

## 📦 Installation Methods Explained

### Method 1: Universal Installer (Recommended)

```bash
./ark-installer.sh
```

**What it does:**

1. **Platform Detection**
   ```bash
   # Detects your system
   ARCH=$(uname -m)  # x86_64, aarch64, armv7l
   OS=$(uname -s)     # Linux, Darwin (macOS)
   ```
   - **Why**: Different platforms need different packages
   - **Example**: ARM processors (Raspberry Pi) need special NumPy builds

2. **Directory Creation**
   ```bash
   mkdir -p data logs keys frontend/public
   ```
   - **data/**: Stores SQLite databases
   - **logs/**: Stores application logs
   - **keys/**: Stores cryptographic keys for federation
   - **frontend/public/**: Static web files

3. **Python Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   - **Why**: Isolates Python packages from system
   - **Benefit**: No conflicts with other Python projects
   - **Result**: All packages installed in `venv/` directory

4. **Package Installation**
   ```bash
   pip install -r requirements.txt
   ```
   - **Installs**: FastAPI, WebSockets, SQLite drivers, Redis client
   - **Time**: 2-5 minutes depending on internet speed
   - **Size**: ~300MB in venv directory

5. **Database Initialization**
   ```bash
   sqlite3 data/reasoning_logs.db < schema.sql
   ```
   - **Creates tables**: reasoning_sessions, reasoning_stages
   - **Purpose**: Store agent reasoning traces
   - **Size**: Initially ~100KB, grows with usage

6. **Key Generation**
   ```bash
   # Generates Ed25519 cryptographic keys
   python3 -c "from nacl.signing import SigningKey; ..."
   ```
   - **Purpose**: Secure federation between ARK nodes
   - **Files**: `keys/ark-primary_private.key`, `keys/ark-primary_public.key`

7. **Service Scripts**
   ```bash
   # Creates executable scripts
   chmod +x arkstart.sh arkstop.sh arkstatus.sh
   ```
   - **arkstart.sh**: Starts all services
   - **arkstop.sh**: Stops all services
   - **arkstatus.sh**: Shows current status

### Method 2: Manual Installation

**Step-by-step breakdown:**

#### Clone Repository
```bash
git clone https://github.com/Superman08091992/ark.git
cd ark
```
- **Downloads**: All source code (~50MB)
- **Location**: Current directory becomes project root

#### Setup Python
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
- **venv creation**: Takes ~10 seconds
- **pip install**: Takes 2-5 minutes
- **Packages installed**: 50+ Python libraries

#### Setup Frontend
```bash
cd frontend
npm install
```
- **Downloads**: Node packages (~200MB in node_modules)
- **Time**: 1-3 minutes
- **Result**: Ready to build or run dev server

### Method 3: Docker Deployment

```bash
docker-compose up -d
```

**What happens:**

1. **Image Building**
   - Reads `Dockerfile`
   - Installs OS packages (apt-get)
   - Installs Python packages
   - Copies source code
   - **Time**: 5-10 minutes first time
   - **Size**: ~1GB image

2. **Container Creation**
   - Creates isolated environment
   - Mounts volumes for data persistence
   - Sets up networking between containers

3. **Service Startup**
   - Starts Redis container
   - Starts ARK backend container
   - Starts frontend container (if configured)

---

## 🔧 What Each Command Does

### Backend Commands

#### `python3 reasoning_api.py`

**What happens:**

1. **Imports modules** (0.5s)
   ```python
   from fastapi import FastAPI, WebSocket
   from dashboard_websockets import ...
   ```

2. **Initializes agents** (1-2s)
   ```python
   agents['kyle'] = KyleAgent()
   agents['joey'] = JoeyAgent()
   # ... and more
   ```
   - Each agent loads its reasoning engine
   - Connects to database
   - Initializes memory systems

3. **Starts data sources** (0.5s)
   ```python
   await init_data_sources()
   ```
   - Connects to Redis (if available)
   - Opens SQLite database connections
   - Initializes production data sources

4. **Starts WebSocket server** (0.1s)
   ```
   INFO: Uvicorn running on http://0.0.0.0:8101
   ```
   - Opens port 8101
   - Listens for WebSocket connections
   - Starts background broadcast tasks

5. **Background tasks start** (continuous)
   ```python
   # Every 2-3 seconds:
   update_federation_data()
   update_memory_data()
   broadcast_to_clients()
   ```

**Total startup time**: ~3-5 seconds

#### `npm run preview` (Frontend)

**What happens:**

1. **Reads build** (0.1s)
   - Loads pre-built files from `dist/`
   
2. **Starts HTTP server** (0.1s)
   ```
   Local: http://localhost:4173
   ```
   - Serves static files
   - Handles routing

3. **No compilation needed**
   - Files already built
   - Instant serving

**Total startup time**: ~0.2 seconds

#### `npm run dev` (Frontend Development)

**What happens:**

1. **Starts Vite dev server** (1-2s)
   - Hot Module Replacement (HMR) enabled
   - Watches for file changes
   
2. **Pre-bundles dependencies** (first time only, ~5s)
   - Optimizes node_modules
   - Caches for fast reloads

3. **Compiles on-demand** (instant)
   - Compiles files as you request them
   - Live reload on changes

**Total startup time**: ~2-3 seconds (faster on subsequent runs)

---

## 📁 Directory Structure Explained

```
ark/
├── agents/                 # Multi-agent system
│   ├── kyle.py            # Perception agent
│   ├── joey.py            # Cognition agent
│   ├── kenny.py           # Action agent
│   ├── hrm.py             # Reasoning arbiter
│   ├── aletheia.py        # Reflection agent
│   └── id.py              # Identity/learning agent
│
├── reasoning/              # Reasoning engines
│   ├── reasoning_engine.py      # Base reasoning
│   ├── memory_sync.py           # Memory synchronization
│   └── intra_agent_reasoner.py  # Deep reasoning
│
├── dashboard_websockets.py      # WebSocket server
├── dashboard_data_sources.py    # Production data
├── reasoning_api.py             # Main FastAPI server
│
├── frontend/               # Dashboard UI
│   ├── public/
│   │   └── dashboard-demo.html  # Main dashboard
│   ├── src/
│   │   └── components/          # Svelte components
│   ├── package.json
│   └── vite.config.js
│
├── data/                   # Databases
│   ├── reasoning_logs.db       # Reasoning traces
│   └── ark.db                  # Code index, patterns
│
├── logs/                   # Application logs
│   ├── reasoning_api.log
│   └── federation.log
│
├── keys/                   # Cryptographic keys
│   ├── ark-primary_private.key
│   └── ark-primary_public.key
│
├── venv/                   # Python virtual environment
│   ├── bin/                    # Executables
│   ├── lib/                    # Python packages
│   └── pyvenv.cfg
│
├── requirements.txt        # Python dependencies
├── .env                    # Configuration
├── ark-installer.sh        # Universal installer
├── arkstart.sh            # Start all services
├── arkstop.sh             # Stop all services
└── arkstatus.sh           # Check status
```

### Key File Purposes

#### Configuration Files

**`.env`** - Environment variables
```bash
REDIS_URL=redis://localhost:6379/0
ARK_BASE_PATH=/path/to/ark
ARK_HTTP_PORT=8000
ARK_REASONING_PORT=8101
```
- **Purpose**: Centralized configuration
- **Format**: KEY=VALUE pairs
- **Loaded by**: Python (python-dotenv), Node.js (process.env)

**`requirements.txt`** - Python packages
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
...
```
- **Purpose**: Specify exact package versions
- **Usage**: `pip install -r requirements.txt`

**`package.json`** - Node.js project definition
```json
{
  "name": "ark-frontend",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```
- **Purpose**: Define project metadata and scripts
- **Usage**: `npm run <script-name>`

#### Core Application Files

**`reasoning_api.py`** - Main backend server
- **Lines**: ~600
- **Purpose**: FastAPI application with WebSocket support
- **Endpoints**:
  - `/ws/federation` - Federation mesh data
  - `/ws/memory` - Memory engine data
  - `/ws/reasoning/{agent}` - Agent reasoning traces
  - `/health` - Health check

**`dashboard_websockets.py`** - WebSocket infrastructure
- **Lines**: ~700
- **Components**:
  - ConnectionManager - Handles multiple clients
  - FederationState - P2P network state
  - MemoryState - Memory consolidation state
  - Background broadcast tasks

**`dashboard_data_sources.py`** - Production data
- **Lines**: ~600
- **Components**:
  - FederationDataSource - Redis queries
  - MemoryDataSource - SQLite queries
  - Automatic fallback to mock data

**`frontend/public/dashboard-demo.html`** - Dashboard UI
- **Lines**: ~800
- **Size**: ~28KB
- **Features**:
  - Pure HTML/CSS/JavaScript (no build needed)
  - WebSocket client connections
  - Real-time data visualization
  - Responsive design

---

## 🚀 Service Startup Process

### Complete Startup Sequence

#### 1. Backend Startup

```bash
python3 reasoning_api.py
```

**Timeline:**

```
0.0s  | Start
0.1s  | Import Python modules
0.5s  | Initialize FastAPI application
0.8s  | Initialize agents (Kyle, Joey, Kenny, HRM, Aletheia, ID)
1.5s  | Initialize reasoning engines for each agent
2.0s  | Connect to memory sync (SQLite + Redis)
2.2s  | Initialize production data sources
2.5s  | Start dashboard WebSocket tasks
2.8s  | Start background broadcast tasks
3.0s  | ✅ Server ready on port 8101
```

**Detailed breakdown:**

```python
# 1. Application lifespan starts
async def lifespan(app: FastAPI):
    # 2. Initialize memory sync
    memory_sync = await init_memory_sync()
    # - Opens SQLite connection to reasoning_logs.db
    # - Attempts Redis connection
    # - Falls back gracefully if Redis unavailable
    
    # 3. Initialize all agents
    agents['kyle'] = KyleAgent()
    # - Loads agent personality and rules
    # - Initializes intra-agent reasoner
    # - Connects to database for memory
    
    # (Repeat for all 6 agents)
    
    # 4. Initialize reasoning engines
    for agent_name, agent in agents.items():
        reasoning_engines[agent_name] = AgentReasoningEngine(...)
    # - Wraps agent with 5-stage reasoning pipeline
    # - Enables deep reasoning capabilities
    
    # 5. Register agents with HRM
    hrm.register_agent_for_reasoning(...)
    # - Enables hierarchical reasoning coordination
    
    # 6. Initialize data sources
    await init_data_sources(redis_url)
    # - FederationDataSource connects to Redis
    # - MemoryDataSource opens SQLite databases
    # - Sets up automatic fallback
    
    # 7. Start dashboard tasks
    await start_dashboard_tasks()
    # - Starts federation_broadcast_task()
    # - Starts memory_broadcast_task()
    # - Both run in background, update every 2-3s
    
    # 8. Server is ready
    logger.info("🎉 ARK Reasoning API Server ready!")
```

#### 2. Frontend Startup

```bash
cd frontend && npm run preview
```

**Timeline:**

```
0.0s  | Start
0.1s  | Read vite.config.js
0.2s  | Load pre-built files from dist/
0.3s  | Start HTTP server on port 4173
0.4s  | ✅ Frontend ready
```

**What's served:**

```
HTTP Server (port 4173)
├── /                          # Main app (if exists)
├── /dashboard-demo.html       # Dashboard
├── /assets/                   # CSS, JS, images
└── /public/                   # Static files
```

#### 3. Complete Stack Running

```
┌─────────────────────────────────┐
│  Browser                        │
│  http://localhost:4173          │
└────────────┬────────────────────┘
             │ HTTP request
             │ WebSocket upgrade
┌────────────▼────────────────────┐
│  Frontend Server (Vite)         │
│  Port 4173                      │
│  Serves: dashboard-demo.html    │
└────────────┬────────────────────┘
             │ WebSocket connection
             │ wss://localhost:8101/ws/*
┌────────────▼────────────────────┐
│  Backend Server (FastAPI)       │
│  Port 8101                      │
│  - WebSocket endpoints          │
│  - Background broadcast tasks   │
└────────────┬────────────────────┘
             │ SQL queries / Redis queries
┌────────────▼────────────────────┐
│  Data Layer                     │
│  - SQLite: reasoning_logs.db    │
│  - SQLite: ark.db               │
│  - Redis: localhost:6379 (opt)  │
└─────────────────────────────────┘
```

---

## 📡 Data Flow and Communication

### WebSocket Communication Flow

#### 1. Connection Establishment

```javascript
// Frontend (dashboard-demo.html)
const ws = new WebSocket('wss://localhost:8101/ws/federation');

ws.onopen = () => {
    console.log('Connected to Federation Mesh');
};
```

**Backend receives:**
```python
@app.websocket("/ws/federation")
async def federation_endpoint(websocket: WebSocket):
    # 1. Accept connection
    await websocket.accept()
    
    # 2. Register with connection manager
    await manager.connect(websocket, 'federation')
    
    # 3. Send initial state immediately
    await websocket.send_json(federation_state.to_dict())
    
    # 4. Keep connection alive
    while True:
        data = await websocket.receive_text()
        # Handle ping/refresh commands
```

#### 2. Background Data Updates

```python
# Background task runs continuously
async def federation_broadcast_task():
    while True:
        # 1. Check if anyone is listening
        if manager.has_connections('federation'):
            
            # 2. Update metrics from production sources
            await federation_state.update_metrics()
            # - Queries Redis for peer data
            # - Calculates network health
            # - Falls back to mock if needed
            
            # 3. Broadcast to all clients
            await manager.broadcast(
                federation_state.to_dict(), 
                'federation'
            )
        
        # 4. Wait 2-3 seconds
        await asyncio.sleep(random.uniform(2.0, 3.0))
```

#### 3. Frontend Data Reception

```javascript
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // Update UI elements
    document.getElementById('network-health').textContent = 
        `${data.network_health}%`;
    
    document.getElementById('peer-count').textContent = 
        data.total_peers;
    
    // Update peer list
    updatePeerList(data.peers);
    
    // Update charts/visualizations
    updateCharts(data);
};
```

### Data Update Cycle

```
┌─────────────────────────────────────────┐
│  Background Task (every 2-3 seconds)    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  Production Data Sources                 │
│  - Query Redis for peer:* keys           │
│  - Query SQLite for reasoning_sessions   │
│  - Calculate metrics                     │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  Update State Objects                    │
│  - FederationState.peers = [...]         │
│  - MemoryState.ingestion_rate = X        │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  Serialize to JSON                       │
│  state.to_dict() → JSON string           │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  Broadcast to All Connected Clients      │
│  ConnectionManager.broadcast(data)       │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  WebSocket sends to all browsers         │
│  ws.send_json(data)                      │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  Browser receives and updates UI         │
│  document.getElementById(...).update()   │
└──────────────────────────────────────────┘
```

### Production Data Queries

#### Federation Data (from Redis)

```python
async def get_peers(self) -> List[Dict]:
    peers = []
    
    # Scan for all peer keys
    async for key in self.redis_client.scan_iter(match="peer:*"):
        # Get peer data
        peer_data = await self.redis_client.hgetall(key)
        
        # Transform to standard format
        peers.append({
            "id": key.replace("peer:", ""),
            "hostname": peer_data.get("hostname"),
            "trust_tier": peer_data.get("trust_tier", "verified"),
            "status": "online" if peer_data.get("last_seen") else "offline",
            "latency": int(peer_data.get("latency", 0))
        })
    
    return peers
```

**Redis data structure:**
```
Key: peer:ark-node-1
Value (Hash):
  hostname: "ark-node-1.local"
  trust_tier: "core"
  status: "online"
  latency: "15"
  last_seen: "1699800000"
```

#### Memory Data (from SQLite)

```python
async def get_consolidation_rates(self) -> Dict[str, float]:
    conn = sqlite3.connect('data/reasoning_logs.db')
    cursor = conn.cursor()
    
    # Count sessions in last minute
    cursor.execute("""
        SELECT COUNT(*) FROM reasoning_sessions 
        WHERE created_at > datetime('now', '-1 minute')
    """)
    recent_sessions = cursor.fetchone()[0]
    
    # Calculate rate per second
    ingestion_rate = recent_sessions / 60.0
    
    return {
        "ingestion_rate": round(ingestion_rate, 1),
        "consolidation_rate": round(consolidation_rate, 1)
    }
```

---

## ⚙️ Configuration Deep Dive

### Environment Variables Explained

#### Core Settings

**`REDIS_URL`**
```bash
REDIS_URL=redis://localhost:6379/0
```
- **Purpose**: Redis connection string
- **Format**: `redis://host:port/database`
- **Default**: localhost:6379/0
- **Optional**: Falls back to mock data if unavailable

**`ARK_BASE_PATH`**
```bash
ARK_BASE_PATH=/home/user/webapp
```
- **Purpose**: Project root directory
- **Used by**: File path resolution, database locations
- **Default**: Current working directory

#### Port Configuration

**`ARK_REASONING_PORT`**
```bash
ARK_REASONING_PORT=8101
```
- **Purpose**: WebSocket server port
- **Used by**: Backend server binding
- **Change if**: Port conflict with other services

**`ARK_FRONTEND_PORT`**
```bash
ARK_FRONTEND_PORT=4173
```
- **Purpose**: Frontend preview server port
- **Used by**: Vite preview server
- **Note**: Dev server uses 5173 by default

### Vite Configuration

**`frontend/vite.config.js`**
```javascript
export default {
  server: {
    port: 5173,  // Dev server port
    proxy: {
      // Proxy API requests to backend
      '/api': 'http://localhost:8101',
      '/ws': {
        target: 'ws://localhost:8101',
        ws: true
      }
    }
  },
  preview: {
    port: 4173  // Preview server port
  }
}
```

**What this does:**
- **Development mode**: Proxies `/api` and `/ws` to backend
- **Production mode**: Serves pre-built files
- **Benefit**: No CORS issues during development

---

## 🐛 Troubleshooting Explained

### Common Issues and Why They Happen

#### Issue: Port Already in Use

**Error message:**
```
ERROR: [Errno 98] Address already in use
```

**Why this happens:**
- Previous server process still running
- Another application using the same port
- OS hasn't released the port yet

**What's actually happening:**
```python
# Python tries to bind to port 8101
server.bind(('0.0.0.0', 8101))
# OS says: "Sorry, someone else is using that port"
```

**Solution explained:**
1. **Find the process:**
   ```bash
   lsof -i :8101
   # Shows: python3   12345   user
   ```
   - `lsof` = List Open Files
   - `-i :8101` = Show processes using port 8101

2. **Kill the process:**
   ```bash
   kill -9 12345
   ```
   - `-9` = SIGKILL (force terminate)
   - `12345` = Process ID from lsof output

#### Issue: WebSocket Connection Failed

**Error in browser console:**
```
WebSocket connection failed: Error in connection establishment
```

**Why this happens:**
1. Backend server not running
2. Wrong WebSocket URL
3. Firewall blocking connection
4. CORS policy blocking

**Diagnosis steps:**

1. **Check backend is running:**
   ```bash
   curl http://localhost:8101/health
   ```
   - If fails: Backend not started
   - If succeeds: Backend running, WebSocket issue

2. **Check WebSocket endpoint:**
   ```bash
   curl -i http://localhost:8101/ws/federation
   ```
   - Should return: `400 Bad Request` (expected - needs WebSocket upgrade)
   - If `404 Not Found`: Endpoint not registered
   - If connection refused: Backend not running

3. **Test WebSocket programmatically:**
   ```bash
   python3 test_dashboard_websockets.py
   ```
   - Uses Python websockets library
   - Bypasses browser CORS
   - Shows exact error message

#### Issue: No Data in Dashboard

**Symptoms:**
- Dashboard loads
- WebSocket shows connected (green)
- But all metrics show `--` or `0`

**Why this happens:**
- Data sources not initialized
- Databases empty
- Redis not populated
- Mock data generation issue

**Diagnosis:**

1. **Check database files:**
   ```bash
   ls -lh data/reasoning_logs.db data/ark.db
   ```
   - If files don't exist: Not initialized
   - If 0 bytes: Created but empty
   - If several KB: Contains data

2. **Query databases directly:**
   ```bash
   sqlite3 data/reasoning_logs.db "SELECT COUNT(*) FROM reasoning_sessions;"
   ```
   - Returns `0`: No reasoning data yet (expected for new install)
   - Returns `> 0`: Data exists

3. **Check backend logs:**
   ```bash
   tail -f logs/reasoning_api.log
   ```
   - Look for: "Using production data" or "Falling back to mock"
   - Errors in data source queries
   - Connection failures

4. **Check Redis (if using):**
   ```bash
   redis-cli keys "peer:*"
   ```
   - If `(empty list)`: No peers registered
   - If shows keys: Peers exist

#### Issue: Database Locked

**Error message:**
```
sqlite3.OperationalError: database is locked
```

**Why this happens:**
- SQLite is single-writer
- Another process has the database open
- Previous connection didn't close properly
- File permissions issue

**What's happening:**
```
Process A: Opens db for write
Process B: Tries to open db for write
SQLite: "Sorry, Process A has it locked"
Process B: Raises exception
```

**Solution explained:**

1. **Find processes using database:**
   ```bash
   lsof data/reasoning_logs.db
   ```
   - Shows all processes with database open

2. **Stop services cleanly:**
   ```bash
   ./arkstop.sh
   # OR
   pkill -f reasoning_api.py
   ```
   - Allows clean connection closure
   - Database lock released

3. **Check file permissions:**
   ```bash
   ls -l data/reasoning_logs.db
   # Should show: rw-r--r-- (644)
   ```
   - If wrong: `chmod 644 data/reasoning_logs.db`

---

## 🎓 Understanding the Stack

### Python Components

#### FastAPI
```python
app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

**What this does:**
- Creates web server
- Handles HTTP requests
- Supports async operations
- Auto-generates API docs at `/docs`

#### WebSockets
```python
@app.websocket("/ws/federation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_json(response)
```

**What this does:**
- Persistent bidirectional connection
- Real-time data push (not just request/response)
- Lower latency than HTTP polling
- Automatic reconnection handling

#### Async/Await
```python
async def update_data():
    data = await fetch_from_database()
    return data
```

**What this does:**
- Non-blocking operations
- Multiple operations concurrently
- Efficient resource usage
- Better performance

### Frontend Components

#### HTML5
```html
<!DOCTYPE html>
<html>
<head>...</head>
<body>
    <div class="dashboard">...</div>
</body>
</html>
```
- Structure and content
- Semantic markup
- Accessibility

#### CSS3
```css
.panel {
    background: rgba(20, 20, 30, 0.7);
    backdrop-filter: blur(20px);
    animation: fadeIn 0.5s ease;
}
```
- Visual styling
- Animations
- Responsive design
- Glass morphism effects

#### JavaScript
```javascript
const ws = new WebSocket('wss://localhost:8101/ws/federation');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateUI(data);
};
```
- Interactivity
- WebSocket client
- DOM manipulation
- Real-time updates

---

## 🎯 Key Takeaways

### What You Need to Know

1. **ARK is a 3-layer system:**
   - Frontend (Browser UI)
   - Backend (Python Server)
   - Data Layer (SQLite + Redis)

2. **Installation creates:**
   - Virtual environment for Python
   - Database files with schema
   - Configuration files
   - Service management scripts

3. **Services run independently:**
   - Backend: `python3 reasoning_api.py`
   - Frontend: `npm run preview`
   - Can start/stop separately

4. **Communication is WebSocket:**
   - Real-time bidirectional
   - Automatic reconnection
   - Low latency updates

5. **Data has two modes:**
   - Production: Real Redis/SQLite data
   - Mock: Simulated data as fallback
   - Automatic switching

6. **Ports matter:**
   - 8101: Backend WebSocket server
   - 4173: Frontend production preview
   - 5173: Frontend development server
   - 6379: Redis (optional)

---

## 📚 Further Reading

- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **WebSocket Protocol**: https://websockets.spec.whatwg.org
- **Vite Documentation**: https://vitejs.dev
- **SQLite Documentation**: https://sqlite.org/docs.html
- **Redis Documentation**: https://redis.io/documentation

---

**Now you understand how ARK works from the ground up!** 🎉
