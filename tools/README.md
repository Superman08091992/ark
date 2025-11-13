# ARK Tools Suite

Comprehensive command-line tools for managing, monitoring, and developing ARK systems.

## 📁 Directory Structure

```
tools/
├── admin/          - System administration and health checks
├── backup/         - Backup and restore utilities
├── database/       - Database management and queries
├── dev/            - Development workflow tools
├── federation/     - P2P network management
├── monitoring/     - Real-time system monitoring
└── README.md       - This file
```

---

## 🛠️ Tools Overview

### 1. **ARK Admin** - `tools/admin/ark-admin.py`
**Purpose**: System administration, health checks, and management

**Features**:
- Comprehensive system health checks
- Database integrity verification
- Process monitoring
- Disk space analysis
- Redis connection testing
- Log analysis and rotation
- Federation peer management

**Usage**:
```bash
# System health check
./tools/admin/ark-admin.py health

# List databases and statistics
./tools/admin/ark-admin.py db-list

# Vacuum databases to reclaim space
./tools/admin/ark-admin.py db-vacuum

# Analyze and optimize databases
./tools/admin/ark-admin.py db-analyze

# List federation peers
./tools/admin/ark-admin.py peers

# Analyze logs from last 7 days
./tools/admin/ark-admin.py logs --days 7

# Rotate logs older than 30 days
./tools/admin/ark-admin.py rotate-logs --days 30

# Clear Redis keys by pattern
./tools/admin/ark-admin.py redis-clear "peer:*"
```

**Output Example**:
```json
{
  "timestamp": "2025-11-12T10:30:00",
  "status": "healthy",
  "checks": {
    "directories": {"status": "ok"},
    "databases": {
      "status": "ok",
      "databases": {
        "ark": {"tables": 12, "size_mb": 45.2, "readable": true},
        "reasoning": {"tables": 8, "size_mb": 23.1, "readable": true}
      }
    },
    "redis": {"status": "ok", "connected": true},
    "processes": {"status": "ok", "processes": [...]},
    "disk_space": {"status": "ok", "percent_used": "45%"}
  }
}
```

---

### 2. **ARK Backup** - `tools/backup/ark-backup.sh`
**Purpose**: Complete system backup and restore with multiple backup types

**Features**:
- Full system backups (databases, config, data, logs)
- Data-only backups (databases and files)
- Config-only backups (settings and keys)
- Incremental backup support
- Backup verification
- One-command restore
- Compression and archiving

**Usage**:
```bash
# Full backup (everything)
./tools/backup/ark-backup.sh full

# Data-only backup (databases + files)
./tools/backup/ark-backup.sh data-only

# Config-only backup (settings + keys)
./tools/backup/ark-backup.sh config-only

# List available backups
./tools/backup/ark-backup.sh list

# Restore from backup
./tools/backup/ark-backup.sh restore backups/ark_backup_20251112_103000.tar.gz
```

**Backup Contents**:

**Full Backup**:
- SQLite databases (ark.db, reasoning_logs.db)
- Configuration files (.env, docker-compose.yml)
- Cryptographic keys (keys/)
- Data files (files/, agent_logs/)
- System logs (last 7 days)
- Redis dump (if available)

**Data-Only Backup**:
- Databases only
- Data files only
- Redis dump

**Config-Only Backup**:
- Environment files
- Keys
- Docker configs

**Output**:
```
🔄 Full Backup
===========================================================

✅ Backing Up Databases
  ✅ ark.db backed up (45.2 MB)
  ✅ reasoning_logs.db backed up (23.1 MB)

✅ Backing Up Configuration
  ✅ Backed up .env.production
  ✅ Backed up cryptographic keys

✅ Backing Up Data Files
  ✅ Backed up files directory (120 MB)
  ✅ Backed up agent logs (15 MB)

✅ Backup Complete
  Archive: /home/user/webapp/backups/ark_backup_20251112_103000.tar.gz
  Size: 215 MB
```

---

### 3. **ARK Monitor** - `tools/monitoring/ark-monitor.py`
**Purpose**: Real-time system monitoring with live dashboard

**Features**:
- Real-time CPU, memory, disk usage
- Process monitoring for ARK services
- Database statistics
- Redis connection monitoring
- Sparkline graphs for trends
- Color-coded status indicators
- Automatic refresh (configurable interval)

**Usage**:
```bash
# Start monitoring (2s interval)
./tools/monitoring/ark-monitor.py

# Custom interval (5s)
./tools/monitoring/ark-monitor.py --interval 5

# Monitor specific ARK installation
./tools/monitoring/ark-monitor.py --base-path /opt/ark
```

**Dashboard Display**:
```
╔═══════════════════════════════════════════════════════════════════╗
║        ARK SYSTEM MONITOR - 2025-11-12 10:30:45                  ║
╚═══════════════════════════════════════════════════════════════════╝

🖥️  SYSTEM RESOURCES
  CPU:    ████████████████░░░░░░░░░░░░░░  54.2%  (8 cores)
  Memory: ██████████████████░░░░░░░░░░░░  62.5%  (10.0/16.0 GB)
  Disk:   █████████████░░░░░░░░░░░░░░░░░  45.3%  (90.6/200.0 GB)

📊 TRENDS (60s)
  CPU:    ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇█
  Memory: ▃▃▄▄▄▅▅▅▆▆▆▆▆▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇

⚙️  ARK PROCESSES (3)
  ✅ [12345] reasoning_api.py    CPU:  2.5% MEM:  1.8%
  ✅ [12346] uvicorn             CPU:  1.2% MEM:  1.5%
  ✅ [12347] redis-server        CPU:  0.5% MEM:  0.8%

💾 DATABASES
  ark         : ✅  12 tables, ~45,230 rows,   45.2 MB
  reasoning   : ✅   8 tables, ~12,450 rows,   23.1 MB

🔴 REDIS
  Status:  ✅ Connected
  Keys:    1,234
  Memory:  15.2 MB
  Clients: 3
  Uptime:  5 days

Press Ctrl+C to stop monitoring
```

---

### 4. **ARK Database** - `tools/database/ark-db.py`
**Purpose**: Database management, queries, and analysis

**Features**:
- List tables with row counts
- Execute SQL queries
- View table schemas
- Database statistics
- Export data (JSON, CSV, SQL)
- Search tables
- View recent entries
- Interactive queries

**Usage**:
```bash
# List all tables in ark.db
./tools/database/ark-db.py list ark

# Show database statistics
./tools/database/ark-db.py stats reasoning

# Show table schema
./tools/database/ark-db.py schema ark code_patterns

# Execute SQL query
./tools/database/ark-db.py query ark "SELECT * FROM code_patterns LIMIT 10"

# Search for data
./tools/database/ark-db.py search reasoning reasoning_sessions "keyword"

# View recent entries
./tools/database/ark-db.py recent ark code_patterns 20

# Export table to JSON
./tools/database/ark-db.py export ark code_patterns patterns.json --format json

# Export to CSV
./tools/database/ark-db.py export ark code_patterns patterns.csv --format csv
```

**Example Output - List Tables**:
```
📊 Tables in ark.db
================================================================================

🔹 code_patterns (1,234 rows)
Column              Type        Key    Null       Default
------------------  ----------  -----  ---------  -------
id                  INTEGER     PK     NOT NULL
pattern_hash        TEXT               NOT NULL
pattern             TEXT               NOT NULL
trust_tier          TEXT               NOT NULL
reuse_count         INTEGER            NOT NULL   0
created_at          TEXT               NOT NULL

🔹 code_index (5,678 rows)
...
```

---

### 5. **ARK Federation** - `tools/federation/ark-federation.py`
**Purpose**: P2P federation network management

**Features**:
- List federation peers
- Add/remove peers
- Update peer trust tiers
- Network statistics
- Sync status monitoring
- Generate Ed25519 key pairs
- View federation keys

**Usage**:
```bash
# List all peers
./tools/federation/ark-federation.py peers

# Add new peer
./tools/federation/ark-federation.py add <peer_id> <host> <port>

# Generate federation keys
./tools/federation/ark-federation.py genkeys

# Show current keys
./tools/federation/ark-federation.py keys
```

**Example Output - Peers List**:
```
🌐 Federation Peers
====================================================================================================
Peer ID             Host              Port   Status    Last Seen             Trust
------------------  ----------------  -----  --------  -------------------  ----------
abc123def456...     192.168.1.100     8104   active    2025-11-12 10:25:30  trusted
def456ghi789...     192.168.1.101     8104   active    2025-11-12 10:24:15  verified
ghi789jkl012...     10.0.0.50         8104   active    2025-11-12 10:20:00  unverified

📊 Total Peers: 3
```

---

### 6. **ARK Dev** - `tools/dev/ark-dev.sh`
**Purpose**: Development workflow automation

**Features**:
- Start/stop development servers
- Server status monitoring
- Live log tailing
- Code linting (flake8, pylint, eslint)
- Code formatting (black, prettier)
- Test execution (pytest, jest)
- Clean cache and old files
- Production builds
- Python REPL with ARK imports
- Database shell access
- Git workflow helpers

**Usage**:
```bash
# Server Management
./tools/dev/ark-dev.sh start       # Start backend + frontend
./tools/dev/ark-dev.sh stop        # Stop all servers
./tools/dev/ark-dev.sh restart     # Restart servers
./tools/dev/ark-dev.sh status      # Show server status
./tools/dev/ark-dev.sh logs backend # Tail backend logs

# Code Quality
./tools/dev/ark-dev.sh lint        # Run all linters
./tools/dev/ark-dev.sh format      # Format all code
./tools/dev/ark-dev.sh test        # Run tests
./tools/dev/ark-dev.sh clean       # Clean cache files

# Development
./tools/dev/ark-dev.sh shell       # Python REPL
./tools/dev/ark-dev.sh db ark      # SQLite shell
./tools/dev/ark-dev.sh commit      # Interactive commit

# Build
./tools/dev/ark-dev.sh build       # Build production assets
```

**Example Output - Status**:
```
===========================================================
Development Server Status
===========================================================

✅ Backend: Running (PID: 12345)
   URL: http://localhost:8101
   Logs: tail -f logs/dev_backend.log

✅ Frontend: Running (PID: 12346)
   URL: http://localhost:5173
   Logs: tail -f logs/dev_frontend.log

✅ Redis: Running
```

---

## 🚀 Quick Start

### Installation
All tools are ready to use immediately after cloning the ARK repository:

```bash
cd /path/to/ark
ls -la tools/
```

### Make All Tools Executable
```bash
chmod +x tools/**/*.py tools/**/*.sh
```

### Add to PATH (Optional)
```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$PATH:/path/to/ark/tools/admin"
export PATH="$PATH:/path/to/ark/tools/backup"
export PATH="$PATH:/path/to/ark/tools/monitoring"
export PATH="$PATH:/path/to/ark/tools/database"
export PATH="$PATH:/path/to/ark/tools/federation"
export PATH="$PATH:/path/to/ark/tools/dev"

# Then use tools directly
ark-admin.py health
ark-backup.sh full
ark-monitor.py
```

---

## 📋 Common Workflows

### Daily Health Check
```bash
# Check system health
./tools/admin/ark-admin.py health

# Monitor for 30 seconds
timeout 30 ./tools/monitoring/ark-monitor.py

# Check recent logs
./tools/admin/ark-admin.py logs --days 1
```

### Weekly Maintenance
```bash
# Full backup
./tools/backup/ark-backup.sh full

# Vacuum databases
./tools/admin/ark-admin.py db-vacuum

# Analyze databases
./tools/admin/ark-admin.py db-analyze

# Rotate old logs
./tools/admin/ark-admin.py rotate-logs --days 30

# Clean development cache
./tools/dev/ark-dev.sh clean
```

### Development Session
```bash
# Start development servers
./tools/dev/ark-dev.sh start

# Watch logs
./tools/dev/ark-dev.sh logs all

# Run tests before commit
./tools/dev/ark-dev.sh test
./tools/dev/ark-dev.sh lint

# Commit changes
./tools/dev/ark-dev.sh commit
```

### Database Operations
```bash
# View database stats
./tools/database/ark-db.py stats ark

# Search for patterns
./tools/database/ark-db.py search ark code_patterns "function"

# Export data for analysis
./tools/database/ark-db.py export ark code_patterns /tmp/patterns.json

# Recent activity
./tools/database/ark-db.py recent reasoning reasoning_sessions 50
```

### Federation Management
```bash
# Check network status
./tools/federation/ark-federation.py stats

# List all peers
./tools/federation/ark-federation.py peers

# Add trusted peer
./tools/federation/ark-federation.py add peer123 192.168.1.100 8104
./tools/federation/ark-federation.py trust peer123 trusted
```

---

## 🔧 Prerequisites

### Python Tools
- **Python**: 3.10+
- **Required packages**: redis, psutil, tabulate, cryptography
- **Install**: `pip install redis psutil tabulate cryptography`

### Shell Tools
- **Bash**: 4.0+
- **System tools**: tar, gzip, sqlite3, find, ps, df
- **Optional**: flake8, pylint, black, prettier

### Services
- **Redis**: For federation features
- **SQLite**: For database operations
- **Git**: For development tools

---

## 📊 Tool Dependencies

```
ark-admin.py        → redis, psutil, sqlite3
ark-backup.sh       → tar, gzip, sqlite3, redis-cli (optional)
ark-monitor.py      → psutil, redis, sqlite3
ark-db.py           → sqlite3, tabulate
ark-federation.py   → redis, cryptography
ark-dev.sh          → bash, git, python3, node (optional)
```

---

## 🐛 Troubleshooting

### Tool Won't Execute
```bash
# Make executable
chmod +x tools/path/to/tool.py

# Check shebang
head -1 tools/path/to/tool.py
# Should be: #!/usr/bin/env python3
```

### Import Errors
```bash
# Activate virtual environment
source venv/bin/activate

# Install missing packages
pip install redis psutil tabulate cryptography
```

### Permission Denied
```bash
# Run with sudo (admin tools only)
sudo ./tools/admin/ark-admin.py health

# Fix ownership
sudo chown -R $USER:$USER /path/to/ark
```

### Redis Connection Failed
```bash
# Check Redis is running
redis-cli ping

# Start Redis
redis-server --daemonize yes

# Check Redis URL
echo $REDIS_URL
export REDIS_URL="redis://localhost:6379/0"
```

### Database Not Found
```bash
# Check database path
ls -la data/*.db

# Set ARK_BASE_PATH
export ARK_BASE_PATH=/path/to/ark
./tools/database/ark-db.py stats ark
```

---

## 🔐 Security Notes

### Backup Security
- Backups contain sensitive data (keys, databases)
- Store backups in secure locations
- Encrypt backups for production: `gpg -c backup.tar.gz`
- Limit backup file permissions: `chmod 600 backup.tar.gz`

### Key Management
- Private keys stored in `keys/` with 600 permissions
- Never commit keys to version control
- Regenerate keys if compromised
- Use different keys for different environments

### Tool Access
- Admin tools require appropriate permissions
- Database tools have read/write access
- Federation tools manage network connections
- Use separate user accounts for production

---

## 📚 Additional Resources

- **ARK Documentation**: `README.md`, `QUICKSTART.md`
- **Docker Deployment**: `DOCKER.md` (if available)
- **Setup Guide**: `SETUP_EXPLAINED.md`
- **Production Data**: `PRODUCTION_DATA_INTEGRATION.md`

---

## 🤝 Contributing

### Adding New Tools

1. **Create tool file** in appropriate directory
2. **Add executable permission**: `chmod +x tool.py`
3. **Add shebang**: `#!/usr/bin/env python3` or `#!/bin/bash`
4. **Document in this README**
5. **Add usage examples**
6. **Test thoroughly**

### Tool Template (Python)
```python
#!/usr/bin/env python3
"""
Tool Name - Brief description
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def main():
    parser = argparse.ArgumentParser(description="Tool description")
    parser.add_argument('command', help='Command to execute')
    args = parser.parse_args()
    
    # Tool logic here

if __name__ == "__main__":
    main()
```

### Tool Template (Bash)
```bash
#!/bin/bash
# Tool Name - Brief description
set -e

show_usage() {
    cat << EOF
Usage: $0 <command>
  command1 - Description
  command2 - Description
EOF
}

case "${1:-help}" in
    command1) echo "Execute command1" ;;
    command2) echo "Execute command2" ;;
    help|*)   show_usage ;;
esac
```

---

## 📝 Version History

- **v1.0** (2025-11-12): Initial tools suite
  - Admin tool for system management
  - Backup tool with full/data/config modes
  - Monitor tool with real-time dashboard
  - Database tool for queries and exports
  - Federation tool for P2P management
  - Dev tool for workflow automation

---

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review tool help: `./tool.py --help`
3. Check ARK documentation
4. Review logs: `./tools/admin/ark-admin.py logs`

---

**Made with ❤️ for the ARK Project**
