# ARK Tools Documentation

Comprehensive toolkit for managing, monitoring, and developing the ARK system.

## 📁 Tool Categories

### 🔧 [Administration](admin/) - System Management
**Purpose**: Complete system administration, health checks, and management

**Tool**: `ark-admin.py`

**Features**:
- System health monitoring
- Database management (list, vacuum, analyze)
- Federation peer management
- Log analysis and rotation
- Redis management

**Usage**:
```bash
# System health check
./tools/admin/ark-admin.py health

# List databases and tables
./tools/admin/ark-admin.py db-list

# Vacuum databases (reclaim space)
./tools/admin/ark-admin.py db-vacuum

# Analyze and optimize databases
./tools/admin/ark-admin.py db-analyze

# List federation peers
./tools/admin/ark-admin.py peers

# Analyze logs (last 7 days)
./tools/admin/ark-admin.py logs --days 7

# Rotate old logs (older than 30 days)
./tools/admin/ark-admin.py rotate-logs --days 30

# Clear Redis keys
./tools/admin/ark-admin.py redis-clear "peer:*"
```

**Output Example**:
```json
{
  "timestamp": "2025-11-12T10:30:00",
  "status": "healthy",
  "checks": {
    "directories": {"status": "ok", ...},
    "databases": {"status": "ok", ...},
    "redis": {"status": "ok", "connected": true},
    "processes": {"status": "ok", ...},
    "disk_space": {"status": "ok", ...}
  }
}
```

---

### 💾 [Backup](backup/) - Data Backup & Restore
**Purpose**: Complete system backup with incremental and full backup support

**Tool**: `ark-backup.sh`

**Features**:
- Full system backup (databases, config, data, logs)
- Data-only backup (databases and files)
- Config-only backup (keys and settings)
- Restore from backup
- Automatic compression
- Backup manifest generation

**Usage**:
```bash
# Full system backup
./tools/backup/ark-backup.sh full

# Data-only backup (faster)
./tools/backup/ark-backup.sh data-only

# Config-only backup (keys and settings)
./tools/backup/ark-backup.sh config-only

# List available backups
./tools/backup/ark-backup.sh list

# Restore from backup
./tools/backup/ark-backup.sh restore backups/ark_backup_20251112_120000.tar.gz
```

**Backup Contents**:
- **Full**: Databases, configuration, data files, logs, Redis dump
- **Data-only**: Databases, data files, Redis dump
- **Config-only**: Environment files, keys, Docker configs

**Backup Location**: `backups/` directory (configurable via `BACKUP_DIR`)

---

### 📊 [Monitoring](monitoring/) - Real-Time System Monitor
**Purpose**: Live system metrics, performance tracking, and alerts

**Tool**: `ark-monitor.py`

**Features**:
- Real-time CPU, memory, and disk monitoring
- ARK process tracking
- Database statistics
- Redis connection monitoring
- Sparkline charts (60-second history)
- Color-coded status indicators
- Auto-refreshing dashboard

**Usage**:
```bash
# Start monitoring (2-second updates)
./tools/monitoring/ark-monitor.py

# Custom update interval (5 seconds)
./tools/monitoring/ark-monitor.py --interval 5

# Monitor specific ARK installation
./tools/monitoring/ark-monitor.py --base-path /opt/ark
```

**Dashboard Features**:
- 🖥️  System resources (CPU, Memory, Disk)
- 📊 Performance trends (sparkline charts)
- ⚙️  ARK process list with PID, CPU, Memory
- 💾 Database health and size
- 🔴 Redis connection status and metrics

**Requirements**:
- `psutil` (CPU/memory monitoring)
- `redis` (Redis monitoring)

---

### 🗄️ [Database](database/) - Database Management
**Purpose**: Query, analyze, and manage ARK databases

**Tool**: `ark-db.py`

**Features**:
- List tables and schemas
- Execute SQL queries
- Search tables
- Export data (JSON, CSV, SQL)
- Show recent entries
- Database statistics

**Usage**:
```bash
# List tables in ark.db
./tools/database/ark-db.py list ark

# Show database statistics
./tools/database/ark-db.py stats reasoning

# Show table schema
./tools/database/ark-db.py schema ark code_patterns

# Execute SQL query
./tools/database/ark-db.py query ark "SELECT * FROM code_patterns WHERE trust_tier='core' LIMIT 10"

# Search for data
./tools/database/ark-db.py search reasoning reasoning_sessions "keyword"

# Show recent entries (last 20)
./tools/database/ark-db.py recent ark code_patterns 20

# Export table to JSON
./tools/database/ark-db.py export ark code_patterns patterns.json --format json

# Export to CSV
./tools/database/ark-db.py export ark code_patterns patterns.csv --format csv
```

**Databases**:
- `ark` - Main ARK database (code patterns, memory, agents)
- `reasoning` - Reasoning logs and sessions

**Requirements**:
- `tabulate` (pretty table output)

---

### 🌐 [Federation](federation/) - P2P Network Management
**Purpose**: Manage P2P federation network, peers, and synchronization

**Tool**: `ark-federation.py`

**Features**:
- List federation peers
- Add/remove peers
- Update trust tiers
- Network statistics
- Synchronization status
- Generate cryptographic keys
- View public keys

**Usage**:
```bash
# List all federation peers
./tools/federation/ark-federation.py peers

# Show peer details
./tools/federation/ark-federation.py info <peer_id>

# Add new peer
./tools/federation/ark-federation.py add <peer_id> <host> <port> [trust_tier]

# Remove peer
./tools/federation/ark-federation.py remove <peer_id>

# Update peer trust tier
./tools/federation/ark-federation.py trust <peer_id> verified

# Show network statistics
./tools/federation/ark-federation.py stats

# Show synchronization status
./tools/federation/ark-federation.py sync

# Generate new key pair
./tools/federation/ark-federation.py genkeys

# Show current keys
./tools/federation/ark-federation.py keys
```

**Trust Tiers**:
- `core` - Core network nodes (highest trust)
- `trusted` - Trusted peers
- `verified` - Verified peers
- `unverified` - New/unverified peers

**Requirements**:
- `redis` (peer storage)
- `cryptography` (key generation)
- `tabulate` (pretty output)

---

### 🛠️ [Development](dev/) - Developer Tools
**Purpose**: Utilities for developers working on ARK

**Tool**: `ark-dev.sh`

**Features**:
- Development environment setup
- Code linting and formatting
- Test execution with coverage
- Database reset and seeding
- Development server management
- Log tailing
- Docker build/run

**Usage**:
```bash
# Set up development environment
./tools/dev/ark-dev.sh setup

# Show development info
./tools/dev/ark-dev.sh info

# Run linters (Black, Flake8, MyPy)
./tools/dev/ark-dev.sh lint

# Format code with Black
./tools/dev/ark-dev.sh format

# Run tests with coverage
./tools/dev/ark-dev.sh test

# Run specific tests
./tools/dev/ark-dev.sh test tests/test_agents.py

# Reset databases (with backup)
./tools/dev/ark-dev.sh reset-db

# Seed test data
./tools/dev/ark-dev.sh seed

# Start development servers (backend + frontend)
./tools/dev/ark-dev.sh dev

# Tail logs
./tools/dev/ark-dev.sh logs reasoning_api.log

# Build Docker image
./tools/dev/ark-dev.sh docker-build

# Run Docker container
./tools/dev/ark-dev.sh docker-run
```

**Development Dependencies**:
- `pytest`, `pytest-cov`, `pytest-asyncio` (testing)
- `black` (code formatting)
- `flake8` (linting)
- `mypy` (type checking)
- `pylint` (code analysis)
- `ipython`, `ipdb` (debugging)

---

## 🚀 Quick Start Guide

### First-Time Setup
```bash
# 1. Set up development environment
./tools/dev/ark-dev.sh setup

# 2. Check system health
./tools/admin/ark-admin.py health

# 3. Create initial backup
./tools/backup/ark-backup.sh full

# 4. Generate federation keys
./tools/federation/ark-federation.py genkeys
```

### Daily Development Workflow
```bash
# 1. Check system status
./tools/admin/ark-admin.py health

# 2. Start monitoring (in separate terminal)
./tools/monitoring/ark-monitor.py

# 3. Start development servers
./tools/dev/ark-dev.sh dev

# 4. Run tests before committing
./tools/dev/ark-dev.sh test

# 5. Format code
./tools/dev/ark-dev.sh format

# 6. Run linters
./tools/dev/ark-dev.sh lint
```

### Maintenance Tasks
```bash
# Weekly: Vacuum databases
./tools/admin/ark-admin.py db-vacuum

# Weekly: Analyze logs
./tools/admin/ark-admin.py logs --days 7

# Monthly: Rotate old logs
./tools/admin/ark-admin.py rotate-logs --days 30

# Monthly: Full backup
./tools/backup/ark-backup.sh full
```

---

## 📦 Installation Requirements

### Core Requirements (All Tools)
```bash
# Python 3.8+
python3 --version

# Virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
```

### Tool-Specific Requirements

**Admin Tool**:
```bash
pip install redis
```

**Monitoring Tool**:
```bash
pip install psutil redis
```

**Database Tool**:
```bash
pip install tabulate
```

**Federation Tool**:
```bash
pip install redis cryptography tabulate
```

**Development Tool**:
```bash
pip install pytest pytest-cov pytest-asyncio black flake8 mypy pylint
```

### Install All Requirements
```bash
# From ARK base directory
pip install -r requirements.txt
pip install psutil tabulate cryptography pytest pytest-cov pytest-asyncio black flake8 mypy pylint
```

---

## 🎯 Common Use Cases

### System Administration
```bash
# Complete health check
./tools/admin/ark-admin.py health

# Optimize databases
./tools/admin/ark-admin.py db-vacuum
./tools/admin/ark-admin.py db-analyze

# View database contents
./tools/database/ark-db.py list ark
./tools/database/ark-db.py stats ark
```

### Backup & Recovery
```bash
# Daily backup (automated via cron)
0 2 * * * cd /path/to/ark && ./tools/backup/ark-backup.sh data-only

# Full weekly backup
0 3 * * 0 cd /path/to/ark && ./tools/backup/ark-backup.sh full

# Restore after failure
./tools/backup/ark-backup.sh restore backups/ark_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Monitoring & Debugging
```bash
# Real-time monitoring
./tools/monitoring/ark-monitor.py

# Check specific process
ps aux | grep reasoning_api

# Tail logs
./tools/dev/ark-dev.sh logs reasoning_api.log

# Database queries
./tools/database/ark-db.py query reasoning "SELECT * FROM reasoning_sessions ORDER BY timestamp DESC LIMIT 10"
```

### Federation Management
```bash
# View network status
./tools/federation/ark-federation.py stats

# Add new peer
./tools/federation/ark-federation.py add peer_abc123 192.168.1.100 8104 trusted

# Monitor synchronization
./tools/federation/ark-federation.py sync
```

### Development Workflow
```bash
# Set up environment
./tools/dev/ark-dev.sh setup

# Write code...

# Test changes
./tools/dev/ark-dev.sh test

# Format and lint
./tools/dev/ark-dev.sh format
./tools/dev/ark-dev.sh lint

# Commit changes
git add .
git commit -m "feat: description"
```

---

## 🔧 Configuration

### Environment Variables

All tools respect these environment variables:

```bash
# ARK base path
export ARK_BASE_PATH=/opt/ark

# Redis connection
export REDIS_URL=redis://localhost:6379/0

# Backup directory
export BACKUP_DIR=/mnt/backups/ark
```

### Tool-Specific Configuration

**Admin Tool**:
- Database paths: `ARK_BASE_PATH/data/*.db`
- Log directory: `ARK_BASE_PATH/logs/`
- Keys directory: `ARK_BASE_PATH/keys/`

**Backup Tool**:
- Backup directory: `BACKUP_DIR` or `ARK_BASE_PATH/backups/`
- Compression: gzip (automatic)

**Monitoring Tool**:
- Update interval: `--interval` flag (default: 2 seconds)
- History length: 60 samples (fixed)

---

## 🐛 Troubleshooting

### Common Issues

**1. "Database not found"**
```bash
# Check if databases exist
ls -lh data/*.db

# Initialize if missing
python3 reasoning_api.py  # Will create on startup
```

**2. "Redis connection failed"**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
redis-server --daemonize yes

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

**3. "Permission denied"**
```bash
# Make tools executable
chmod +x tools/**/*.py tools/**/*.sh

# Or specific tool
chmod +x tools/admin/ark-admin.py
```

**4. "Module not found"**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 📚 Additional Resources

- **[QUICKSTART.md](../QUICKSTART.md)** - Installation and setup guide
- **[README.md](../README.md)** - Project overview
- **[DOCKER.md](../DOCKER.md)** - Docker deployment guide

---

## 🤝 Contributing

To add new tools:

1. Create tool in appropriate category directory
2. Follow existing tool patterns
3. Add usage examples to this README
4. Make executable: `chmod +x your-tool`
5. Test thoroughly before committing

---

## 📄 License

Part of the ARK project. See main project LICENSE for details.
