# ARK Launch Guide

Complete guide to starting, stopping, and managing ARK services.

## 🚀 Quick Start

### Option 1: Simple Launch (Recommended)
```bash
./arkstart.sh
```

This will:
- ✅ Activate virtual environment
- ✅ Check/start Redis (if installed)
- ✅ Start backend API (port 8101)
- ✅ Start frontend (port 5173, if available)
- ✅ Perform health check
- ✅ Display access URLs

### Option 2: Using Tools
```bash
./ark-tools dev start
```

For development workflow management.

### Option 3: Docker
```bash
docker-compose up -d
```

For containerized deployment.

---

## 📋 System Requirements

### Required
- **Python**: 3.10 or higher
- **Virtual Environment**: `venv/` (auto-activated by arkstart.sh)
- **Dependencies**: Listed in `requirements.txt`

### Optional
- **Redis**: For federation and caching features
- **Node.js**: For frontend (if using)
- **Docker**: For containerized deployment

---

## 🔧 Installation & Setup

### First Time Setup

1. **Clone Repository**
```bash
git clone https://github.com/Superman08091992/ark.git
cd ark
```

2. **Create Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

Or for production:
```bash
pip install -r requirements.prod.txt
```

4. **Install Optional Tools Dependencies**
```bash
# For development tools
pip install flake8 pylint black pytest

# System tools (if needed)
sudo apt install redis-server sqlite3
```

5. **Initialize Databases** (auto-created on first run)
```bash
mkdir -p data logs keys agent_logs files
```

6. **Start ARK**
```bash
./arkstart.sh
```

---

## 🎮 Control Commands

### Start Services
```bash
./arkstart.sh
```

**What it does**:
- Activates Python virtual environment
- Checks Redis availability (starts if needed)
- Starts backend API (reasoning_api.py)
- Starts frontend (if available)
- Runs health check
- Shows access URLs and status

**Output**:
```
╔════════════════════════════════════════════════════════════════════╗
║  🌌 ARK - Autonomous Reactive Kernel                               ║
╚════════════════════════════════════════════════════════════════════╝

Starting ARK System...

✅ Virtual environment active: /path/to/ark/venv
✅ Redis is running
✅ Backend started (PID: 12345)
   API: http://localhost:8101
   Docs: http://localhost:8101/docs
✅ Frontend started (PID: 12346)
   URL: http://localhost:5173

✨ ARK System Started Successfully! ✨
```

### Stop Services
```bash
./arkstop.sh
```

**What it does**:
- Gracefully stops backend API
- Gracefully stops frontend
- Optionally stops Redis (prompts user)
- Cleans up PID files

### Check Status
```bash
./arkstatus.sh
```

**What it does**:
- Shows all running services with PIDs
- Displays database information
- Shows disk space usage
- Shows recent log entries
- Provides quick status overview

**Output**:
```
╔════════════════════════════════════════════════════════════════════╗
║  📊 ARK - System Status                                            ║
╚════════════════════════════════════════════════════════════════════╝

Services:
✅ Backend (reasoning_api.py) - PID: 12345
         http://localhost:8101
✅ Frontend (vite) - PID: 12346
         http://localhost:5173
✅ Redis - PID: 1234

Databases:
✅ ark.db (45 MB)
✅ reasoning_logs.db (23 MB)

Disk Space:
  Used: 90.6G / 200.0G (46%)
```

---

## 🛠️ Advanced Control

### Using ARK Tools

The tools suite provides additional control options:

```bash
# Development workflow
./ark-tools dev start        # Start dev servers
./ark-tools dev stop         # Stop dev servers
./ark-tools dev restart      # Restart servers
./ark-tools dev status       # Show status
./ark-tools dev logs backend # Watch logs

# System administration
./ark-tools admin health     # Health check
./ark-tools status           # Quick status

# Real-time monitoring
./ark-tools monitor          # Dashboard
```

### Manual Service Control

#### Backend API
```bash
# Start
source venv/bin/activate
python3 reasoning_api.py

# Or in background
nohup python3 reasoning_api.py > logs/backend.log 2>&1 &

# Stop
pkill -f reasoning_api.py
```

#### Frontend
```bash
# Start
cd frontend
npm run dev

# Or in background
nohup npm run dev > ../logs/frontend.log 2>&1 &

# Stop
pkill -f vite
```

#### Redis
```bash
# Start
redis-server --daemonize yes

# Stop
redis-cli shutdown

# Check
redis-cli ping
```

---

## 🌐 Access URLs

### After Starting ARK

**Backend API**:
- URL: http://localhost:8101
- API Docs: http://localhost:8101/docs
- OpenAPI: http://localhost:8101/openapi.json
- Dashboard: http://localhost:8101/dashboard-demo.html

**Frontend** (if available):
- URL: http://localhost:5173

**WebSocket Endpoints**:
- Federation: ws://localhost:8101/ws/federation
- Memory: ws://localhost:8101/ws/memory

---

## 📊 Monitoring & Logs

### Real-Time Monitoring
```bash
# Interactive dashboard
./ark-tools monitor

# Or watch specific logs
tail -f logs/backend.log
tail -f logs/frontend.log
```

### Log Locations
```
logs/
├── backend.log          # Backend API logs
├── frontend.log         # Frontend logs (if applicable)
├── dev_backend.log      # Development backend logs
└── dev_frontend.log     # Development frontend logs
```

### Health Checks
```bash
# Quick health check
./ark-tools health

# Detailed health check
./ark-tools admin health

# System status
./arkstatus.sh
```

---

## 🐳 Docker Deployment

### Quick Start
```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Using Deploy Script
```bash
# Automated deployment
./docker-deploy.sh
```

### Docker Services
```
Services:
├── ark-backend   (ports 8101, 8104)
├── ark-frontend  (port 4173)
└── redis         (port 6379)
```

See `DOCKER.md` for complete Docker documentation.

---

## 🔧 Troubleshooting

### Backend Won't Start

**Check Python version**:
```bash
python3 --version  # Should be 3.10+
```

**Check dependencies**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Check port availability**:
```bash
lsof -i :8101  # Check if port in use
```

**Check logs**:
```bash
tail -50 logs/backend.log
```

### Redis Connection Issues

**Check Redis is running**:
```bash
redis-cli ping  # Should return PONG
```

**Start Redis**:
```bash
redis-server --daemonize yes
```

**Check Redis URL**:
```bash
echo $REDIS_URL  # Should be redis://localhost:6379/0
```

### Frontend Won't Start

**Check Node.js**:
```bash
node --version   # Should be 16+
npm --version
```

**Install dependencies**:
```bash
cd frontend
npm install
```

**Clear cache**:
```bash
rm -rf frontend/node_modules
cd frontend && npm install
```

### Database Issues

**Check databases exist**:
```bash
ls -lh data/*.db
```

**Recreate databases** (if needed):
```bash
rm data/*.db
./arkstart.sh  # Will recreate on start
```

### Permission Denied

**Make scripts executable**:
```bash
chmod +x arkstart.sh arkstop.sh arkstatus.sh ark-tools
chmod +x tools/*/*.py tools/*/*.sh
```

**Fix ownership**:
```bash
sudo chown -R $USER:$USER /path/to/ark
```

---

## 📚 Related Documentation

- **README.md** - Project overview and features
- **QUICKSTART.md** - Quick installation guide
- **TOOLS_QUICKSTART.md** - Tools suite quick start
- **tools/README.md** - Complete tools documentation
- **DOCKER.md** - Docker deployment guide
- **SETUP_EXPLAINED.md** - Detailed setup explanations

---

## 🎯 Common Workflows

### Daily Development

```bash
# Morning - Start everything
./arkstart.sh

# Check status
./arkstatus.sh

# Monitor in real-time
./ark-tools monitor

# Evening - Stop everything
./arkstop.sh
```

### Testing Changes

```bash
# Restart backend to test changes
./ark-tools dev restart

# Watch logs for errors
./ark-tools dev logs backend

# Run tests
./ark-tools dev test
```

### Production Deployment

```bash
# Using Docker (recommended)
./docker-deploy.sh

# Or manual
source venv/bin/activate
pip install -r requirements.prod.txt
./arkstart.sh
```

### Backup Before Restart

```bash
# Create backup
./ark-tools backup full

# Then restart
./arkstop.sh
./arkstart.sh
```

---

## 🚨 Emergency Commands

### Force Stop All
```bash
pkill -f reasoning_api.py
pkill -f vite
pkill -f redis-server
```

### Clean Restart
```bash
./arkstop.sh
rm -f /tmp/ark_*.pid
./arkstart.sh
```

### Reset Everything
```bash
./arkstop.sh
rm -f logs/*.log
rm -f /tmp/ark_*.pid
./arkstart.sh
```

---

## 🔐 Environment Variables

### Required
```bash
ARK_BASE_PATH=/path/to/ark     # Auto-detected by scripts
```

### Optional
```bash
REDIS_URL=redis://localhost:6379/0
ARK_HTTP_PORT=8000
ARK_REASONING_PORT=8101
ARK_FEDERATION_PORT=8104
```

### Set in .env file
```bash
cp .env.example .env
# Edit .env with your values
```

---

## ✅ Pre-Flight Checklist

Before launching ARK, verify:

- [ ] Python 3.10+ installed
- [ ] Virtual environment created (`venv/`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Directories exist (`data/`, `logs/`, `keys/`)
- [ ] Redis running (optional, but recommended)
- [ ] Ports 8101, 5173 available
- [ ] Enough disk space (> 1 GB free)

---

## 📞 Getting Help

### Check Status First
```bash
./arkstatus.sh
./ark-tools health
```

### View Logs
```bash
tail -50 logs/backend.log
./ark-tools admin logs --days 1
```

### Run Diagnostics
```bash
./ark-tools admin health
./ark-tools db stats ark
```

---

**Made with ❤️ for the ARK Project**

**Version**: 1.0  
**Last Updated**: 2025-11-13  
**Status**: Production Ready ✅
