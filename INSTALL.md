# A.R.K. Installation Guide

## Autonomous Reactive Kernel - Universal Installer

This guide covers installation and deployment of the complete ARK system with all autonomous learning components.

---

## 🎯 Quick Start

### One-Command Installation

```bash
./ark-installer.sh
```

The installer automatically:
- Detects your platform (x86_64, ARM64, ARMv7)
- Creates directory structure
- Sets up Python virtual environment
- Installs all dependencies
- Initializes databases
- Configures federation cryptography
- Creates service management scripts

---

## 📋 Prerequisites

### Minimum Requirements

- **OS**: Linux, macOS, or WSL2
- **Python**: 3.8 or higher
- **Disk Space**: 500MB minimum
- **RAM**: 2GB minimum (4GB recommended)
- **Architecture**: x86_64, ARM64, or ARMv7

### Recommended

- **Node.js**: 18+ (for PM2 process management)
- **Redis**: 6+ (for caching)
- **Docker**: 20+ (for containerized deployment)

### Install Prerequisites

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv \
    sqlite3 curl git
```

#### CentOS/RHEL
```bash
sudo yum install -y \
    python3 python3-pip \
    sqlite curl git
```

#### macOS
```bash
brew install python3 sqlite curl git
```

---

## 🚀 Installation Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd webapp
```

### 2. Run Installer

```bash
chmod +x ark-installer.sh
./ark-installer.sh
```

The installer will:
- ✅ Detect system architecture and OS
- ✅ Create directory structure
- ✅ Set up Python virtual environment
- ✅ Install Python dependencies
- ✅ Initialize SQLite databases
- ✅ Generate federation cryptography keys
- ✅ Initialize autonomous learning systems
- ✅ Create service management scripts
- ✅ Generate Docker configuration

### 3. Validate Installation

```bash
./ark-validate.sh
```

Expected output:
```
✅ All validation tests passed!

Your ARK system is ready to use.
Start with: ./arkstart.sh
```

### 4. Start Services

```bash
./arkstart.sh
```

---

## 🐋 Docker Deployment

### Using Docker Compose

```bash
docker-compose up -d
```

This starts:
- **ark-backend**: Main API server (port 8000)
- **redis**: Cache server (port 6379)
- **ark-agents**: Multi-agent framework

### Build and Run Manually

```bash
docker build -t ark:latest .
docker run -d -p 8000:8000 ark:latest
```

### View Logs

```bash
docker-compose logs -f
```

### Stop Services

```bash
docker-compose down
```

---

## ⚙️ Configuration

### Environment Variables

Edit `.env` to customize:

```bash
# System
ARK_ENV=production
ARK_LOG_LEVEL=INFO
ARK_TIMEZONE=UTC

# Database
ARK_DB_PATH=data/demo_memory.db

# Reflection System
ARK_REFLECTION_MODE=sleep
ARK_SLEEP_SCHEDULE=0 0 * * *

# ID Growth System
ARK_ID_BASE_ALPHA=0.3
ARK_ID_MIN_ALPHA=0.05
ARK_ID_MAX_ALPHA=0.8

# Federation
ARK_FEDERATION_PORT=8104
ARK_TRUST_TIER=CORE

# Services
ARK_HTTP_PORT=8000
```

### Reflection Policies

Edit `reflection/reflection_policies.yaml`:

```yaml
reflection:
  mode: "sleep"
  schedule: "0 0 * * *"
  max_chunks_per_cycle: 50
  min_confidence_delta: 0.05
```

---

## 🎮 Service Management

### Start Services

```bash
./arkstart.sh
```

With PM2 (if available):
- Starts backend API
- Starts all agents
- Monitors processes
- Auto-restarts on failure

Without PM2:
- Starts services in background
- Logs to `logs/` directory

### Stop Services

```bash
./arkstop.sh
```

### Check Status

```bash
./arkstatus.sh
```

Output shows:
- Database status and size
- Running processes
- Federation peer ID
- Recent log entries

---

## 🧪 Testing Installation

### 1. Run Demonstrations

```bash
source venv/bin/activate

# Memory Engine demonstration
python3 demo_memory_engine.py

# Reflection System demonstration
python3 demo_reflection_system.py

# ID Growth demonstration
python3 demo_id_growth.py
```

### 2. Test API

```bash
# Health check
curl http://localhost:8000/health

# Memory stats
curl http://localhost:8000/api/memory/stats

# Reflection stats
curl http://localhost:8000/api/reflection/stats

# ID stats
curl http://localhost:8000/api/id/stats
```

### 3. Test Federation

```bash
# Check peer ID
cat data/federation/keys/peer_id.txt

# Test discovery (requires network)
# Check logs/federation.log
```

---

## 📦 What Gets Installed

### Directory Structure

```
ark/
├── agents/              # Multi-agent cognitive framework
├── backend/             # FastAPI backend
├── data/
│   ├── demo_memory.db   # Main SQLite database
│   ├── federation/      # Federation keys and state
│   └── backups/         # Database backups
├── logs/
│   ├── agents/          # Agent logs
│   ├── reflection/      # Reflection audit logs
│   └── federation/      # Federation logs
├── memory/              # Memory Engine v2
├── reflection/          # Reflection System
├── id/                  # ID Growth System
├── federation/          # Federation mesh
├── services/            # API services
├── venv/                # Python virtual environment
├── .env                 # Environment configuration
├── arkstart.sh          # Start script
├── arkstop.sh           # Stop script
└── arkstatus.sh         # Status script
```

### Database Tables

The installer creates:
- `reasoning_log`: Reasoning traces from agents
- `memory_chunks`: Consolidated memory
- `reflections`: Sleep mode insights
- `id_state`: Agent behavioral models
- `id_updates`: Learning history
- `quarantine`: Suspicious traces

### Core Systems

1. **Memory Engine v2**
   - CRUD operations
   - Consolidation pipeline
   - Semantic search
   - Trust tier enforcement

2. **Reflection System**
   - Nightly sleep cycle
   - Pattern recognition
   - Confidence calibration
   - Ethical validation

3. **ID Growth System**
   - EWMA learning
   - 18 behavioral features
   - Confidence-weighted adaptation
   - Provenance tracking

4. **Federation**
   - Ed25519 cryptography
   - UDP multicast discovery
   - WebSocket synchronization
   - Trust tier isolation

---

## 🔧 Troubleshooting

### Python Version Issues

```bash
# Check Python version
python3 --version

# Must be 3.8 or higher
# If not, install newer Python:
sudo apt-get install python3.10
```

### Virtual Environment Issues

```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database Issues

```bash
# Reinitialize database
rm data/demo_memory.db
sqlite3 data/demo_memory.db < memory/schema.sql
```

### Permission Issues

```bash
# Fix permissions
chmod 700 logs data
chmod 755 agents backend
chmod +x ark*.sh
```

### Port Conflicts

Edit `.env`:
```bash
ARK_HTTP_PORT=8001  # Change from 8000
```

### Redis Not Available

Redis is optional. Disable in `.env`:
```bash
ARK_REDIS_ENABLED=false
```

---

## 🚀 Platform-Specific Notes

### Raspberry Pi (ARM64)

- Installer automatically detects ARM64
- NumPy may take longer to install
- Reduce reflection batch size:
  ```yaml
  max_chunks_per_cycle: 25
  ```

### macOS

- Use Homebrew for system dependencies
- Some packages may require Xcode Command Line Tools:
  ```bash
  xcode-select --install
  ```

### Docker on ARM

Use platform flag:
```bash
docker build --platform linux/arm64 -t ark:latest .
```

### WSL2 (Windows)

- Install WSL2 with Ubuntu
- Follow Ubuntu/Debian instructions
- Access via: http://localhost:8000

---

## 📊 System Requirements by Deployment

### Development (Local)

- RAM: 2GB
- Disk: 500MB
- CPU: 1 core

### Production (Server)

- RAM: 4GB
- Disk: 2GB
- CPU: 2+ cores
- Network: 100Mbps+

### Edge (Raspberry Pi)

- RAM: 2GB (Pi 4)
- Disk: 8GB SD card
- CPU: ARM Cortex-A72
- Network: Ethernet recommended

### Container (Docker)

- RAM: 2GB allocated
- Disk: 1GB for images
- CPU: 2 cores
- Network: Bridge or host mode

---

## 🔐 Security Considerations

### Production Deployment

1. **Change default credentials**
   ```bash
   # Generate secure keys
   openssl rand -hex 32
   ```

2. **Enable HTTPS**
   - Use reverse proxy (nginx/caddy)
   - Install SSL certificate

3. **Firewall rules**
   ```bash
   # Allow only necessary ports
   ufw allow 8000/tcp
   ufw allow 8104/tcp
   ufw enable
   ```

4. **Database encryption**
   - Enable SQLite encryption extensions
   - Encrypt backups

5. **Federation security**
   - Verify peer signatures
   - Use trust tier isolation
   - Monitor quarantine rates

---

## 📚 Additional Resources

- **Memory Engine**: `memory/README.md`
- **Reflection System**: `reflection/reflection_policies.yaml`
- **ID Growth**: `id/__init__.py`
- **Federation**: `federation/README.md`
- **API Documentation**: http://localhost:8000/docs

---

## 🆘 Getting Help

### Check Logs

```bash
# All logs
tail -f logs/*.log

# Specific system
tail -f logs/reflection_audit.log
```

### Run Diagnostics

```bash
./ark-validate.sh
./arkstatus.sh
```

### Common Issues

1. **Port already in use**
   - Change `ARK_HTTP_PORT` in `.env`

2. **Database locked**
   - Stop all services: `./arkstop.sh`
   - Check for stale processes: `ps aux | grep python3`

3. **Federation keys missing**
   - Re-run installer
   - Or manually generate:
     ```bash
     python3 -c "from nacl.signing import SigningKey; print(SigningKey.generate())"
     ```

---

## 🎉 Success!

If you see this after validation:

```
✅ All validation tests passed!
Your ARK system is ready to use.
```

You're all set! Start exploring:

```bash
./arkstart.sh
curl http://localhost:8000/health
```

Welcome to the A.R.K. Autonomous Reactive Kernel! 🌌
