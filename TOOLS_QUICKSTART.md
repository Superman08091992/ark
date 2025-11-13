# ARK Tools - Quick Start Guide

Get started with ARK's comprehensive tools suite in 5 minutes.

## 📋 Prerequisites

### Required
- **Python**: 3.10 or higher
- **Bash**: 4.0 or higher (standard on Linux/Mac)
- **Git**: For version control operations
- **SQLite**: For database operations
- **Redis**: For federation features (optional)

### Check Your System
```bash
python3 --version  # Should be 3.10+
bash --version     # Should be 4.0+
git --version
sqlite3 --version
redis-cli ping     # Optional: PONG if Redis running
```

---

## 🚀 Installation

### 1. Activate Virtual Environment
```bash
cd /path/to/ark
source venv/bin/activate
```

### 2. Install Python Dependencies
```bash
pip install redis psutil tabulate cryptography
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 3. Verify Tools
```bash
ls -la ark-tools tools/*/
```

All tools should be executable (marked with `x` in permissions).

### 4. Test Installation
```bash
./ark-tools help
```

You should see the colorful tools menu.

---

## 🎯 First Steps

### Health Check
```bash
# Quick health check
./ark-tools health

# or detailed check
./ark-tools admin health
```

**Example Output**:
```json
{
  "timestamp": "2025-11-13T06:00:00",
  "status": "healthy",
  "checks": {
    "directories": {"status": "ok"},
    "databases": {"status": "ok"},
    "redis": {"status": "ok"},
    "processes": {"status": "ok"}
  }
}
```

### System Status
```bash
./ark-tools status
```

Shows running services, databases, and disk space.

### Real-Time Monitoring
```bash
./ark-tools monitor
```

Press `Ctrl+C` to stop.

---

## 📦 Common Tasks

### Backup Operations

**Create Full Backup**:
```bash
./ark-tools backup full
```

**List Backups**:
```bash
./ark-tools backup list
```

**Restore from Backup**:
```bash
./ark-tools backup restore backups/ark_backup_20251113_060000.tar.gz
```

### Database Operations

**List Tables**:
```bash
./ark-tools db list ark
```

**Run Query**:
```bash
./ark-tools db query ark "SELECT * FROM code_patterns LIMIT 10"
```

**Export Data**:
```bash
./ark-tools db export ark code_patterns /tmp/patterns.json
```

### Development Workflow

**Start Development Servers**:
```bash
./ark-tools dev start
```

**Check Server Status**:
```bash
./ark-tools dev status
```

**Watch Logs**:
```bash
./ark-tools dev logs backend
```

**Stop Servers**:
```bash
./ark-tools dev stop
```

### Federation Management

**List Peers**:
```bash
./ark-tools federation peers
```

**Generate Keys**:
```bash
./ark-tools federation genkeys
```

---

## 🛠️ Individual Tools

All tools can be used directly or through the unified launcher.

### Via Unified Launcher (Recommended)
```bash
./ark-tools <tool> [command]
```

### Direct Tool Access
```bash
./tools/admin/ark-admin.py <command>
./tools/backup/ark-backup.sh <mode>
./tools/monitoring/ark-monitor.py
./tools/database/ark-db.py <command>
./tools/federation/ark-federation.py <command>
./tools/dev/ark-dev.sh <command>
```

---

## 📊 Tool Reference

### ARK Admin
```bash
./ark-tools admin health          # System health check
./ark-tools admin db-list         # List databases
./ark-tools admin db-vacuum       # Optimize databases
./ark-tools admin peers           # List federation peers
./ark-tools admin logs --days 7   # Analyze logs
```

### ARK Backup
```bash
./ark-tools backup full         # Full system backup
./ark-tools backup data-only    # Databases + files
./ark-tools backup config-only  # Configuration only
./ark-tools backup list         # List backups
./ark-tools backup restore <file>
```

### ARK Monitor
```bash
./ark-tools monitor              # Start monitoring
./ark-tools monitor --interval 5 # 5-second refresh
```

### ARK Database
```bash
./ark-tools db list <database>           # List tables
./ark-tools db stats <database>          # Statistics
./ark-tools db schema <db> <table>       # Show schema
./ark-tools db query <db> "SQL"          # Run query
./ark-tools db recent <db> <table> 20    # Recent rows
./ark-tools db export <db> <table> <file>
```

### ARK Federation
```bash
./ark-tools federation peers     # List all peers
./ark-tools federation genkeys   # Generate key pair
./ark-tools federation add <id> <host> <port>
```

### ARK Dev
```bash
./ark-tools dev start     # Start dev servers
./ark-tools dev stop      # Stop servers
./ark-tools dev status    # Show status
./ark-tools dev logs      # Watch logs
./ark-tools dev lint      # Run linters
./ark-tools dev format    # Format code
./ark-tools dev test      # Run tests
./ark-tools dev shell     # Python REPL
./ark-tools dev commit    # Git commit helper
```

---

## 🔧 Troubleshooting

### Tool Won't Execute
```bash
# Make executable
chmod +x ark-tools
chmod +x tools/*/*.py tools/*/*.sh
```

### Import Errors
```bash
# Activate venv first
source venv/bin/activate

# Install missing packages
pip install redis psutil tabulate cryptography
```

### Redis Connection Failed
```bash
# Start Redis
redis-server --daemonize yes

# Check Redis
redis-cli ping

# Set Redis URL
export REDIS_URL="redis://localhost:6379/0"
```

### Database Not Found
```bash
# Check databases exist
ls -la data/*.db

# Set base path
export ARK_BASE_PATH=/path/to/ark
```

### Permission Denied
```bash
# Fix ownership
sudo chown -R $USER:$USER /path/to/ark

# Or run with sudo (admin tools only)
sudo ./ark-tools admin health
```

---

## 🎓 Learning Path

### Day 1: Basics
1. ✅ Install tools and dependencies
2. ✅ Run health check
3. ✅ Explore unified launcher
4. ✅ Create your first backup

### Day 2: Monitoring
1. ✅ Start real-time monitor
2. ✅ Check system status
3. ✅ Analyze logs
4. ✅ View database statistics

### Day 3: Development
1. ✅ Start dev servers
2. ✅ Run code quality checks
3. ✅ Use Python REPL
4. ✅ Database queries

### Day 4: Advanced
1. ✅ Federation network setup
2. ✅ Automated backups (cron)
3. ✅ Custom queries and exports
4. ✅ Integration with CI/CD

---

## 📚 Documentation

- **This Guide**: Quick start (you are here)
- **tools/README.md**: Comprehensive 17 KB guide
- **TOOLS_COMPLETE.md**: Implementation details
- **Tool Help**: Every tool has `--help` flag

### Getting More Help
```bash
# Show tool menu
./ark-tools help

# Show specific tool help
./ark-tools admin --help
./ark-tools db --help
./ark-tools federation --help
```

---

## 💡 Pro Tips

### 1. Add to PATH
```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$PATH:/path/to/ark"

# Then use from anywhere
ark-tools health
```

### 2. Create Aliases
```bash
alias arkt="./ark-tools"
alias arkh="./ark-tools health"
alias arkm="./ark-tools monitor"
alias arkb="./ark-tools backup full"
```

### 3. Scheduled Backups
```bash
# Add to crontab (crontab -e)
0 2 * * * cd /path/to/ark && ./tools/backup/ark-backup.sh full
```

### 4. Monitor in Background
```bash
# Using tmux
tmux new -s ark-monitor
./ark-tools monitor
# Ctrl+B, D to detach

# Reattach later
tmux attach -t ark-monitor
```

### 5. Quick Status Dashboard
```bash
# Create wrapper script
cat > ~/ark-status.sh << 'EOF'
#!/bin/bash
cd /path/to/ark
./ark-tools health | jq .
./ark-tools status
EOF
chmod +x ~/ark-status.sh

# Run anytime
~/ark-status.sh
```

---

## 🔄 Daily Workflow

### Morning Routine
```bash
cd /path/to/ark
source venv/bin/activate

# Check system health
./ark-tools health

# Start development
./ark-tools dev start

# Open monitoring dashboard
./ark-tools monitor
```

### Development Cycle
```bash
# Make changes to code

# Run tests
./ark-tools dev test

# Lint code
./ark-tools dev lint

# Format code
./ark-tools dev format

# Commit
./ark-tools dev commit
```

### End of Day
```bash
# Create backup
./ark-tools backup full

# Stop servers
./ark-tools dev stop

# Check final status
./ark-tools status
```

---

## 🎯 Next Steps

1. **Read Full Documentation**: `tools/README.md`
2. **Explore Each Tool**: Try all commands with `--help`
3. **Set Up Automation**: Scheduled backups, monitoring
4. **Integrate with Workflow**: CI/CD, development process
5. **Customize**: Add aliases, create wrapper scripts

---

## 📞 Support

### Common Issues
1. Check troubleshooting section above
2. Verify all prerequisites installed
3. Ensure virtual environment activated
4. Check tool permissions (should be executable)

### Getting Help
```bash
# Tool-specific help
./ark-tools <tool> --help

# Show tool capabilities
./tools/admin/ark-admin.py --help
./tools/backup/ark-backup.sh
./tools/database/ark-db.py --help
```

### Documentation
- **Tools README**: Comprehensive guide with examples
- **TOOLS_COMPLETE**: Full implementation details
- **ARK Documentation**: Main README and guides

---

## ✅ Quick Checklist

Before using tools, verify:
- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Tools are executable (`chmod +x`)
- [ ] Redis running (optional, for federation)
- [ ] Databases exist (`ls data/*.db`)

After setup:
- [ ] Health check passes
- [ ] Unified launcher works
- [ ] At least one backup created
- [ ] Monitoring dashboard accessible

---

**Made with ❤️ for the ARK Project**

**Quick Start Version**: 1.0  
**Last Updated**: 2025-11-13  
**Status**: Ready to Use ✅
