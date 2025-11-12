# 🚀 ARK Quick Start Guide

## Complete Setup and Installation Commands

This guide provides step-by-step instructions to get ARK up and running with the Sovereign Intelligence Console dashboard.

---

## 📋 Prerequisites

### System Requirements
- **OS**: Linux, macOS, or WSL2
- **Python**: 3.8+ (3.12 recommended)
- **Node.js**: 18+ (for frontend)
- **RAM**: 2GB minimum (4GB recommended)
- **Disk**: 1GB free space

### Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv \
    nodejs npm sqlite3 curl git redis-server
```

#### macOS
```bash
brew install python3 node sqlite curl git redis
```

#### CentOS/RHEL
```bash
sudo yum install -y python3 python3-pip \
    nodejs npm sqlite curl git redis
```

---

## 🎯 Quick Installation (Recommended)

### Method 1: Universal Installer

```bash
# 1. Clone the repository
git clone https://github.com/Superman08091992/ark.git
cd ark

# 2. Run universal installer
chmod +x ark-installer.sh
./ark-installer.sh

# 3. Validate installation
chmod +x ark-validate.sh
./ark-validate.sh

# 4. Start all services
./arkstart.sh
```

**What the installer does:**
- ✅ Detects platform (x86_64, ARM64, ARMv7)
- ✅ Creates directory structure
- ✅ Sets up Python virtual environment
- ✅ Installs all dependencies
- ✅ Initializes SQLite databases
- ✅ Generates cryptographic keys
- ✅ Configures services

---

## 🔧 Manual Installation

If you prefer manual setup or the installer fails:

### Step 1: Clone Repository
```bash
git clone https://github.com/Superman08091992/ark.git
cd ark
```

### Step 2: Setup Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/macOS
# OR
.\venv\Scripts\activate   # On Windows

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Setup Frontend
```bash
cd frontend

# Install Node dependencies
npm install

# Build frontend (production)
npm run build

# OR run in development mode
npm run dev

cd ..
```

### Step 4: Initialize Databases
```bash
# Create data directory
mkdir -p data

# Initialize reasoning logs database
sqlite3 data/reasoning_logs.db < reasoning/memory_sync.py

# Initialize ARK database
sqlite3 data/ark.db < codegen/schema.sql
```

### Step 5: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

**Key environment variables:**
```bash
# Redis URL for federation data
REDIS_URL=redis://localhost:6379/0

# Base path for ARK
ARK_BASE_PATH=/path/to/ark

# Server ports
ARK_HTTP_PORT=8000
ARK_REASONING_PORT=8101
ARK_FRONTEND_PORT=4173
```

---

## 🚀 Starting ARK

### Method 1: All Services at Once
```bash
# Start all services
./arkstart.sh
```

### Method 2: Individual Services

#### Backend API Server
```bash
# Activate Python environment
source venv/bin/activate

# Start reasoning API (WebSocket backend)
python3 reasoning_api.py

# The server starts on port 8101
# WebSocket endpoints:
# - ws://localhost:8101/ws/federation
# - ws://localhost:8101/ws/memory
# - ws://localhost:8101/ws/reasoning/{agent_name}
```

#### Frontend Dashboard
```bash
# In a new terminal
cd frontend

# Development mode (hot reload)
npm run dev
# Access at: http://localhost:5173

# OR Production preview
npm run preview
# Access at: http://localhost:4173
```

#### Redis (Optional - for production federation data)
```bash
# Start Redis server
redis-server --daemonize yes

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

---

## 🎨 Accessing the Dashboard

### Option 1: Direct Access (Production Build)
After running `npm run preview` in the frontend directory:

**Dashboard URL:**
```
http://localhost:4173/dashboard-demo.html
```

### Option 2: Development Mode
After running `npm run dev`:

**Dashboard URL:**
```
http://localhost:5173/dashboard-demo.html
```

### Option 3: Public URL (Current Live Instance)
If you're using the sandbox deployment:

**Dashboard:**
```
https://4173-iqvk5326f1xsbwmwb3rnw-cc2fbc16.sandbox.novita.ai/dashboard-demo.html
```

**Backend API:**
```
https://8101-iqvk5326f1xsbwmwb3rnw-cc2fbc16.sandbox.novita.ai
```

---

## 📊 Dashboard Features

Once you access the dashboard, you'll see:

### Top Stats Bar
- **Total Peers**: Number of connected federation nodes
- **Network Health**: Percentage of online peers
- **Consolidation**: Memory processing rate
- **Efficiency**: Deduplication percentage

### Left Panel: 🌐 Federation Mesh
- Network health with progress bar
- Data integrity tracking
- Active peer count
- Average latency
- Live peer list with trust tiers:
  - **Core** (cyan): Highest trust
  - **Trusted** (gold): Verified nodes
  - **Verified** (red): Standard peers

### Right Panel: 🧠 Memory Engine
- Ingestion rate (memories/second)
- Consolidation rate (processing speed)
- Deduplication efficiency
- Quarantine count
- Real-time event logs

---

## 🔍 Verifying Installation

### Check Backend Status
```bash
# Test reasoning API health
curl http://localhost:8101/health

# Check if WebSocket endpoints exist
curl -I http://localhost:8101/ws/federation
```

### Check Frontend Status
```bash
# Test frontend server
curl http://localhost:4173

# Test dashboard page
curl http://localhost:4173/dashboard-demo.html
```

### Check WebSocket Connections
```bash
# Run WebSocket test script
python3 test_dashboard_websockets.py
```

Expected output:
```
✅ Federation Mesh WebSocket: PASS
✅ Memory Engine WebSocket: PASS
🎉 All dashboard WebSocket endpoints working correctly!
```

### Check Data Sources
```bash
# Check if databases exist
ls -lh data/reasoning_logs.db data/ark.db

# Check Redis connection (if running)
redis-cli ping
```

---

## 🛠️ Common Commands

### Service Management
```bash
# Start all services
./arkstart.sh

# Stop all services
./arkstop.sh

# Check service status
./arkstatus.sh

# View logs
tail -f logs/*.log
```

### Python Environment
```bash
# Activate environment
source venv/bin/activate

# Deactivate environment
deactivate

# Update dependencies
pip install -r requirements.txt --upgrade
```

### Frontend Development
```bash
cd frontend

# Install/update dependencies
npm install

# Development server (hot reload)
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Database Management
```bash
# View reasoning logs
sqlite3 data/reasoning_logs.db "SELECT * FROM reasoning_sessions LIMIT 5;"

# View ARK database
sqlite3 data/ark.db "SELECT * FROM code_index LIMIT 5;"

# Backup databases
cp data/reasoning_logs.db data/reasoning_logs.backup.db
cp data/ark.db data/ark.backup.db
```

### Redis Management
```bash
# Start Redis
redis-server --daemonize yes

# Stop Redis
redis-cli shutdown

# View Redis data
redis-cli keys "*"

# Monitor Redis commands
redis-cli monitor
```

---

## 🐛 Troubleshooting

### Issue: Backend won't start
```bash
# Check if port 8101 is in use
lsof -i :8101

# Kill existing process
kill -9 <PID>

# Try starting again
python3 reasoning_api.py
```

### Issue: Frontend won't start
```bash
# Check if port 4173 or 5173 is in use
lsof -i :4173
lsof -i :5173

# Kill existing process
kill -9 <PID>

# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run preview
```

### Issue: WebSocket connection failed
```bash
# 1. Verify backend is running
curl http://localhost:8101/health

# 2. Check WebSocket endpoints
python3 test_dashboard_websockets.py

# 3. Check browser console for errors
# Open dashboard, press F12, check Console tab
```

### Issue: No data in dashboard
```bash
# Check if data sources are initialized
ls -lh data/reasoning_logs.db data/ark.db

# Check if Redis is running (optional)
redis-cli ping

# Restart backend to reload data sources
pkill -f reasoning_api.py
python3 reasoning_api.py
```

### Issue: Dashboard shows 404
```bash
# Verify file exists
ls -lh frontend/public/dashboard-demo.html

# If missing, you may need to pull latest changes
git pull origin master

# Restart frontend server
cd frontend
npm run preview
```

---

## 📦 Port Reference

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Backend API | 8000 | HTTP | Main FastAPI server |
| Reasoning API | 8101 | HTTP/WS | WebSocket endpoints |
| Frontend Dev | 5173 | HTTP | Vite development server |
| Frontend Preview | 4173 | HTTP | Vite production preview |
| Redis | 6379 | TCP | Cache and federation data |
| Federation | 8104 | UDP/TCP | P2P mesh communication |

---

## 🔐 Security Notes

### For Production Deployment

1. **Change default ports**
   ```bash
   # Edit .env
   ARK_REASONING_PORT=9001
   ARK_FRONTEND_PORT=3000
   ```

2. **Use HTTPS**
   - Set up reverse proxy (nginx/caddy)
   - Install SSL certificate
   - Update WebSocket URLs to wss://

3. **Enable authentication**
   - Add API keys
   - Configure JWT tokens
   - Restrict CORS origins

4. **Secure Redis**
   ```bash
   # Edit redis.conf
   requirepass your-secure-password
   bind 127.0.0.1
   ```

5. **Database encryption**
   - Use SQLCipher for encrypted databases
   - Secure backup storage

---

## 📚 Next Steps

After installation, explore:

1. **Documentation**
   - `README.md` - Main documentation
   - `BACKEND_INTEGRATION_COMPLETE.md` - WebSocket backend
   - `PRODUCTION_DATA_INTEGRATION.md` - Data sources
   - `MERGE_COMPLETE.md` - Latest changes

2. **Demos**
   ```bash
   source venv/bin/activate
   python3 demo_memory_engine.py
   python3 demo_reflection_system.py
   python3 demo_id_growth.py
   ```

3. **API Documentation**
   - Open: http://localhost:8101/docs
   - Interactive API explorer with FastAPI

4. **Agent Testing**
   ```bash
   # Test individual agents
   python3 -c "from agents.kyle import KyleAgent; agent = KyleAgent(); print(agent.name)"
   ```

---

## 💡 Quick Reference

### Essential Commands
```bash
# One-line start
source venv/bin/activate && python3 reasoning_api.py &
cd frontend && npm run preview &

# Access dashboard
open http://localhost:4173/dashboard-demo.html

# View logs
tail -f logs/*.log

# Stop everything
pkill -f reasoning_api.py
pkill -f "node.*vite"
```

### File Locations
- **Backend**: `reasoning_api.py`
- **Dashboard**: `frontend/public/dashboard-demo.html`
- **Data Sources**: `dashboard_data_sources.py`
- **WebSocket**: `dashboard_websockets.py`
- **Databases**: `data/reasoning_logs.db`, `data/ark.db`
- **Logs**: `logs/`

---

## 🎉 Success Indicators

You'll know everything is working when:

1. ✅ Backend responds: `curl http://localhost:8101/health`
2. ✅ Frontend loads: `curl http://localhost:4173`
3. ✅ Dashboard accessible in browser
4. ✅ WebSocket status indicators are **green**
5. ✅ Real-time data updates visible
6. ✅ Animations smooth and responsive

---

## 🆘 Getting Help

If you encounter issues:

1. **Check logs**: `tail -f logs/*.log`
2. **Run validation**: `./ark-validate.sh`
3. **Test WebSockets**: `python3 test_dashboard_websockets.py`
4. **View documentation**: All `.md` files in project root
5. **Check GitHub issues**: Report bugs or ask questions

---

## 🌟 Welcome to ARK!

You now have a complete sovereign intelligence infrastructure with:
- ✅ Multi-agent reasoning system
- ✅ Real-time WebSocket dashboards
- ✅ Production data integration
- ✅ Beautiful cyberpunk UI
- ✅ Autonomous learning capabilities

**Your neural mesh awaits!** 🚀
