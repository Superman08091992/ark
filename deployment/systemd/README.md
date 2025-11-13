# ARK Systemd Service Files (REQ_INFRA_01)

This directory contains systemd service files for production deployment of ARK with automatic restart and process supervision.

---

## 📋 Available Services

### 1. **ark-backend.service**
- **Purpose**: ARK reasoning API backend (FastAPI)
- **Port**: 8101
- **Features**: Auto-restart, resource limits, security hardening
- **Dependencies**: network.target, redis.service (optional)

### 2. **ark.service**
- **Purpose**: Complete ARK system (wrapper for all components)
- **Components**: Backend, Frontend, Agents
- **Features**: Uses arkstart.sh/arkstop.sh for orchestration
- **Dependencies**: ark-backend.service

---

## 🚀 Installation

### Quick Install (All Services)

```bash
# Copy service files
sudo cp deployment/systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable ARK to start on boot
sudo systemctl enable ark

# Start ARK
sudo systemctl start ark

# Check status
sudo systemctl status ark
```

### Individual Service Install

```bash
# Install backend only
sudo cp deployment/systemd/ark-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ark-backend
sudo systemctl start ark-backend
```

---

## 🎛️ Service Management

### Start/Stop/Restart

```bash
# Start ARK
sudo systemctl start ark

# Stop ARK (graceful shutdown)
sudo systemctl stop ark

# Restart ARK
sudo systemctl restart ark

# Reload configuration
sudo systemctl reload ark
```

### Check Status

```bash
# ARK system status
sudo systemctl status ark

# Backend status
sudo systemctl status ark-backend

# View recent logs
sudo journalctl -u ark -n 50

# Follow live logs
sudo journalctl -u ark -f

# Logs with timestamps
sudo journalctl -u ark -f --since "10 minutes ago"
```

### Enable/Disable Auto-Start

```bash
# Enable auto-start on boot
sudo systemctl enable ark

# Disable auto-start
sudo systemctl disable ark

# Check if enabled
sudo systemctl is-enabled ark
```

---

## 📊 Monitoring

### View Logs

```bash
# All ARK logs
sudo journalctl -u ark -u ark-backend -f

# Errors only
sudo journalctl -u ark --priority=err -f

# Last 100 lines
sudo journalctl -u ark -n 100

# Logs since boot
sudo journalctl -u ark -b

# Export logs to file
sudo journalctl -u ark > ark_logs.txt
```

### Resource Usage

```bash
# CPU and memory usage
sudo systemctl status ark

# Detailed resource stats
sudo systemd-cgtop

# Process tree
sudo systemctl status ark --no-pager -l
```

---

## 🔧 Configuration

### Environment Variables

Service files load environment from `/home/user/webapp/.env`

Create `.env` file:
```bash
cd /home/user/webapp
cp .env.example .env
nano .env
```

After changing `.env`:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ark
```

### Resource Limits

Edit service file to adjust limits:
```bash
sudo nano /etc/systemd/system/ark-backend.service
```

Available limits:
- `MemoryMax=4G` - Maximum memory
- `CPUQuota=200%` - Maximum CPU (200% = 2 cores)
- `LimitNOFILE=65536` - Max open files
- `LimitNPROC=4096` - Max processes

After editing:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ark-backend
```

---

## 🚨 Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status ark -l

# View full error logs
sudo journalctl -u ark -xe

# Verify files exist
ls -la /home/user/webapp/arkstart.sh
ls -la /home/user/webapp/reasoning_api.py

# Check permissions
sudo systemctl cat ark

# Test script manually
cd /home/user/webapp
./arkstart.sh
```

### Service Restarts Continuously

```bash
# Check restart count
sudo systemctl status ark

# View crash logs
sudo journalctl -u ark --since "1 hour ago"

# Disable auto-restart temporarily
sudo systemctl edit ark
# Add: [Service]
# Add: Restart=no

# Check for port conflicts
sudo netstat -tulpn | grep 8101
```

### Permission Errors

```bash
# Fix ownership
sudo chown -R user:user /home/user/webapp

# Fix permissions
chmod +x /home/user/webapp/arkstart.sh
chmod +x /home/user/webapp/arkstop.sh

# Check systemd service user
sudo systemctl cat ark | grep User=
```

### Memory Issues

```bash
# Check memory usage
sudo systemctl status ark

# Increase memory limit
sudo systemctl edit ark-backend
# Add: [Service]
# Add: MemoryMax=8G

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart ark-backend
```

---

## 🔐 Security Hardening

Service files include security features:

- **NoNewPrivileges**: Prevents privilege escalation
- **PrivateTmp**: Isolated /tmp directory
- **ProtectSystem**: Read-only system directories
- **ProtectHome**: Limited home directory access
- **ReadWritePaths**: Explicit write permissions

To further harden:

```bash
# Edit service file
sudo systemctl edit ark-backend

# Add additional restrictions:
[Service]
PrivateNetwork=yes        # Isolate network (if applicable)
ProtectKernelTunables=yes # Protect kernel parameters
ProtectControlGroups=yes  # Protect cgroups
```

---

## 📦 Uninstallation

```bash
# Stop and disable services
sudo systemctl stop ark
sudo systemctl disable ark

# Remove service files
sudo rm /etc/systemd/system/ark*.service

# Reload systemd
sudo systemctl daemon-reload

# Reset failed units
sudo systemctl reset-failed
```

---

## 🔄 Updates

After updating ARK code:

```bash
# Restart services to load new code
sudo systemctl restart ark

# Or reload without full restart (if supported)
sudo systemctl reload ark
```

---

## 📝 Custom Services

To create custom ARK services:

1. Copy existing service file
2. Modify ExecStart, Description, etc.
3. Install and enable

Example:
```bash
cp deployment/systemd/ark-backend.service deployment/systemd/ark-custom.service
nano deployment/systemd/ark-custom.service
sudo cp deployment/systemd/ark-custom.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start ark-custom
```

---

## 🆘 Support

- **Systemd Docs**: `man systemd.service`
- **Journal Docs**: `man journalctl`
- **ARK Issues**: https://github.com/Superman08091992/ark/issues

---

**Last Updated**: 2025-11-13  
**ARK Version**: v3.1.0-phase7
