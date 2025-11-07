# 🚀 ARK Deployment Guide

This guide covers all deployment scenarios for Project ARK.

## 📦 Quick Deployment Options

### Option 1: One-Click Installer (Recommended)
```bash
chmod +x ark-installer.sh
./ark-installer.sh
```

The installer automatically:
- Detects hardware architecture (x86_64 or ARM64)
- Installs Docker and dependencies
- Configures systemd services
- Starts all ARK services
- Enables auto-start on boot

### Option 2: Docker Compose
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 3: Complete Deployment Script
```bash
chmod +x deploy-ark.sh
./deploy-ark.sh
```

Creates a complete ARK installation from scratch in a new directory.

### Option 4: Development Mode
```bash
# Terminal 1: Start Kyle agent
node agents/kyle/index.js "Kyle online"

# Terminal 2: Start backend
node services/core/server.mjs

# Access at http://localhost:3000
```

## 🏗️ Deployment Architecture

### Docker Services

**ark-core** (Port 8000)
- FastAPI backend server
- Agent orchestration
- API endpoints
- Database connections

**ark-frontend** (Port 3000)
- Svelte UI application
- Real-time WebSocket connection
- Nginx web server

**ark-agents**
- Python agent processes
- Background task execution
- Inter-agent communication

**redis** (Port 6379)
- Message queue
- Inter-agent communication
- Session storage

**db-init**
- Database initialization
- Schema creation
- Migration execution

## 🔧 Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Database
DATABASE_URL=sqlite:///app/data/ark.db

# Redis
REDIS_URL=redis://redis:6379

# Hardware (dell or pi)
HARDWARE_TYPE=dell

# LLM Configuration
OLLAMA_HOST=http://localhost:11434
MODEL_SIZE=heavy  # or 'light' for Pi

# API
API_URL=http://ark-core:8000
FRONTEND_URL=http://localhost:3000

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/data/ark.log
```

### Hardware-Specific Configuration

**For Dell Latitude 7490 (x86_64):**
```bash
HARDWARE_TYPE=dell
MODEL_SIZE=heavy
# Uses larger, more capable models
```

**For Raspberry Pi 5 (ARM64):**
```bash
HARDWARE_TYPE=pi
MODEL_SIZE=light
# Uses optimized, lighter models
```

## 📊 Service Management

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d ark-core

# Stop all services
docker-compose down

# Restart service
docker-compose restart ark-core

# View logs
docker-compose logs -f ark-core

# Rebuild service
docker-compose build --no-cache ark-core
docker-compose up -d ark-core
```

### Using Systemd (After Installer)

```bash
# Status check
sudo systemctl status ark.service

# Start service
sudo systemctl start ark.service

# Stop service
sudo systemctl stop ark.service

# Restart service
sudo systemctl restart ark.service

# Enable auto-start
sudo systemctl enable ark.service

# Disable auto-start
sudo systemctl disable ark.service

# View logs
sudo journalctl -u ark.service -f
```

## 🔍 Health Checks

### Check Service Health

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# Redis health
docker-compose exec redis redis-cli ping
```

### Validate Database

```bash
# Access database
docker-compose exec ark-core python -c "
from shared.db_init import init_db
init_db()
print('Database OK')
"
```

### Test Agent Communication

```bash
# Check Redis connection
docker-compose exec redis redis-cli
> PING
> KEYS *
> EXIT
```

## 🔄 Updates and Maintenance

### Update ARK System

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

### Database Migration

```bash
# Backup current database
cp data/ark.db data/ark.db.backup

# Run migrations (if needed)
docker-compose exec ark-core python -c "
from shared.db_init import migrate_db
migrate_db()
"

# Verify migration
docker-compose restart ark-core
docker-compose logs ark-core
```

### Clean Reset

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: Deletes all data)
docker-compose down -v

# Clean containers
docker-compose rm -f

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs ark-core

# Check system resources
docker stats

# Verify Docker daemon
sudo systemctl status docker
```

### Port Conflicts

```bash
# Check port usage
netstat -tulpn | grep -E '3000|8000|6379'

# Or with lsof
lsof -i :3000
lsof -i :8000
lsof -i :6379

# Change ports in docker-compose.yml if needed
```

### Database Issues

```bash
# Check database file
ls -lh data/ark.db

# Verify permissions
chmod 644 data/ark.db
chown $USER:$USER data/ark.db

# Reinitialize database
docker-compose exec ark-core python -c "
from shared.db_init import init_db
init_db()
"
```

### Agent Not Responding

```bash
# Check agent logs
docker-compose logs ark-agents

# Restart agents
docker-compose restart ark-agents

# Check Redis communication
docker-compose exec redis redis-cli
> SUBSCRIBE agent_channel
```

### Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs ark-frontend

# Verify API connection
curl http://localhost:8000/health

# Check Nginx config
docker-compose exec ark-frontend cat /etc/nginx/nginx.conf

# Rebuild frontend
docker-compose build --no-cache ark-frontend
docker-compose up -d ark-frontend
```

## 🔐 Security Considerations

### Production Deployment

1. **Change default passwords**
2. **Enable HTTPS with SSL certificates**
3. **Configure firewall rules**
4. **Set up reverse proxy (Nginx/Caddy)**
5. **Enable authentication**
6. **Regular backups**

### SSL/TLS Setup (Example with Caddy)

```bash
# Install Caddy
curl -fsSL https://getcaddy.com | bash

# Create Caddyfile
cat > Caddyfile << EOF
yourdomain.com {
    reverse_proxy localhost:3000
}

api.yourdomain.com {
    reverse_proxy localhost:8000
}
EOF

# Start Caddy
caddy run
```

## 📈 Performance Optimization

### For x86_64 (Dell)

```yaml
# docker-compose.override.yml
services:
  ark-core:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          memory: 2G
```

### For ARM64 (Pi 5)

```yaml
# docker-compose.override.yml
services:
  ark-core:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          memory: 1G
```

## 📊 Monitoring

### Basic Monitoring

```bash
# Watch container stats
docker stats

# Monitor logs in real-time
docker-compose logs -f --tail=100

# Check disk usage
df -h
du -sh data/
```

### Advanced Monitoring (Optional)

Install Prometheus + Grafana for advanced metrics:

```bash
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
```

## 🔄 Backup and Restore

### Backup

```bash
#!/bin/bash
# backup-ark.sh

BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
cp data/ark.db "$BACKUP_DIR/ark_db_$DATE.db"

# Backup files
tar -czf "$BACKUP_DIR/ark_files_$DATE.tar.gz" files/

# Backup config
tar -czf "$BACKUP_DIR/ark_config_$DATE.tar.gz" \
  docker-compose.yml \
  .env \
  requirements.txt

echo "Backup completed: $DATE"
```

### Restore

```bash
#!/bin/bash
# restore-ark.sh

BACKUP_FILE=$1

# Stop services
docker-compose down

# Restore database
cp "$BACKUP_FILE" data/ark.db

# Restore files
tar -xzf ark_files_*.tar.gz -C files/

# Start services
docker-compose up -d

echo "Restore completed"
```

## 📞 Support

For deployment issues:
1. Check logs: `docker-compose logs -f`
2. Verify configuration: `.env` and `docker-compose.yml`
3. Review system requirements
4. Check GitHub issues
5. Contact support

---

*ARK - Autonomous Reactive Kernel | Deployment Guide v1.0*
