# Docker Deployment Guide - ARK Trading Intelligence

Complete guide for deploying ARK Trading Intelligence Backend using Docker and Docker Compose.

## 📋 Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 10GB+ disk space

## 🚀 Quick Start (Docker Compose)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/ark-trading.git
cd ark-trading
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit with your values
nano .env
```

**Required Environment Variables**:

```bash
# Telegram (for notifications)
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_id

# Alpaca (for data - paper trading)
ALPACA_API_KEY=your_alpaca_key
ALPACA_API_SECRET=your_alpaca_secret

# Trading settings
ACCOUNT_SIZE=100000.0

# Optional: Other data providers
POLYGON_API_KEY=
ALPHA_VANTAGE_API_KEY=
FINNHUB_API_KEY=
```

### 3. Start Services

```bash
# Start all services
docker-compose -f docker-compose.trading.yml up -d

# View logs
docker-compose -f docker-compose.trading.yml logs -f

# Check status
docker-compose -f docker-compose.trading.yml ps
```

### 4. Verify Deployment

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# View API documentation
open http://localhost:8000/docs
```

## 🏗️ Architecture

Docker Compose deployment includes:

1. **ark-api** - Trading Intelligence API (port 8000)
2. **redis** - Caching and message queue (port 6379)
3. **postgres** - Persistent storage (port 5432)

All services connected via `ark-network` bridge.

## 📦 Service Details

### ARK API Service

**Image**: Custom built from `Dockerfile.api`
**Ports**: 8000:8000
**Volumes**:
- `./logs:/app/logs` - API logs
- `./config:/app/config:ro` - Configuration (read-only)
- `./ark:/app/ark:ro` - Pattern definitions (read-only)
- `./data:/app/data` - Data storage

**Health Check**: `curl http://localhost:8000/api/v1/health` every 30s

### Redis Service

**Image**: redis:7-alpine
**Ports**: 6379:6379
**Volumes**: `redis-data:/data` (persistent)
**Command**: `redis-server --appendonly yes`

### PostgreSQL Service

**Image**: postgres:15-alpine
**Ports**: 5432:5432
**Volumes**: `postgres-data:/var/lib/postgresql/data`
**Database**: `ark_trading`

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes* | - | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Yes* | - | Your Telegram chat ID |
| `ALPACA_API_KEY` | No | - | Alpaca API key (paper) |
| `ALPACA_API_SECRET` | No | - | Alpaca API secret |
| `ACCOUNT_SIZE` | No | 100000.0 | Trading account size |
| `LOG_LEVEL` | No | INFO | Logging level |
| `POSTGRES_USER` | No | arkuser | Postgres username |
| `POSTGRES_PASSWORD` | Yes | changeme | Postgres password |

\* Optional if not using Telegram notifications

### Volume Mounts

Mount local directories for development:

```yaml
services:
  ark-api:
    volumes:
      - ./routes:/app/routes  # Hot reload API routes
      - ./agents:/app/agents  # Hot reload agents
      - ./services:/app/services  # Hot reload services
```

## 🔨 Building Images

### Build API Image

```bash
# Build with Docker
docker build -f Dockerfile.api -t ark-trading-api:v1.0.0 .

# Build with Docker Compose
docker-compose -f docker-compose.trading.yml build
```

### Multi-Platform Build

```bash
# Build for AMD64 and ARM64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f Dockerfile.api \
  -t your-registry/ark-trading-api:v1.0.0 \
  --push \
  .
```

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose -f docker-compose.trading.yml logs -f

# Specific service
docker-compose -f docker-compose.trading.yml logs -f ark-api

# Last 100 lines
docker-compose -f docker-compose.trading.yml logs --tail=100 ark-api
```

### Resource Usage

```bash
# Container stats
docker stats

# Specific container
docker stats ark-trading-api
```

### Health Checks

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' ark-trading-api

# View health log
docker inspect --format='{{json .State.Health}}' ark-trading-api | jq
```

## 🔄 Updates

### Update Services

```bash
# Pull latest images
docker-compose -f docker-compose.trading.yml pull

# Restart services
docker-compose -f docker-compose.trading.yml up -d

# Or rebuild and restart
docker-compose -f docker-compose.trading.yml up -d --build
```

### Rolling Updates

```bash
# Update one service at a time
docker-compose -f docker-compose.trading.yml up -d --no-deps ark-api
```

## 🧪 Testing

### Run Tests in Container

```bash
# Run integration tests
docker-compose -f docker-compose.trading.yml exec ark-api pytest tests/ -v

# Run specific test
docker-compose -f docker-compose.trading.yml exec ark-api pytest tests/test_integration_pipeline.py -v
```

### Interactive Shell

```bash
# Get bash shell
docker-compose -f docker-compose.trading.yml exec ark-api /bin/bash

# Run Python REPL
docker-compose -f docker-compose.trading.yml exec ark-api python

# Execute Python script
docker-compose -f docker-compose.trading.yml exec ark-api python -c "print('Hello')"
```

## 🔐 Security

### Secrets Management

**Option 1: Environment Variables**
```bash
# Set in .env file (gitignored)
TELEGRAM_BOT_TOKEN=abc123...
```

**Option 2: Docker Secrets**
```yaml
services:
  ark-api:
    secrets:
      - telegram_token
      
secrets:
  telegram_token:
    file: ./secrets/telegram_token.txt
```

**Option 3: External Secrets**
```bash
# Use Vault, AWS Secrets Manager, etc.
export TELEGRAM_BOT_TOKEN=$(vault kv get -field=token secret/telegram)
```

### Network Isolation

```yaml
services:
  ark-api:
    networks:
      - public  # External access
      - private  # Internal services

networks:
  public:
    driver: bridge
  private:
    driver: bridge
    internal: true  # No internet access
```

## 📈 Scaling

### Scale Services

```bash
# Run 3 API instances
docker-compose -f docker-compose.trading.yml up -d --scale ark-api=3

# Add load balancer (nginx)
docker-compose -f docker-compose.trading.yml -f docker-compose.lb.yml up -d
```

### Resource Limits

```yaml
services:
  ark-api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## 🗑️ Cleanup

### Stop Services

```bash
# Stop all services
docker-compose -f docker-compose.trading.yml stop

# Stop and remove containers
docker-compose -f docker-compose.trading.yml down
```

### Remove Volumes

```bash
# Remove containers and volumes
docker-compose -f docker-compose.trading.yml down -v

# Remove specific volume
docker volume rm ark-trading_redis-data
```

### Complete Cleanup

```bash
# Remove everything
docker-compose -f docker-compose.trading.yml down -v --rmi all
docker system prune -af
```

## 🆘 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.trading.yml logs ark-api

# Inspect container
docker inspect ark-trading-api

# Check events
docker events --filter container=ark-trading-api
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"
```

### Permission Denied

```bash
# Fix ownership
sudo chown -R $(id -u):$(id -g) ./logs

# Or run as root (not recommended)
docker-compose -f docker-compose.trading.yml exec -u root ark-api bash
```

### Out of Disk Space

```bash
# Check disk usage
docker system df

# Clean unused data
docker system prune -a

# Remove unused volumes
docker volume prune
```

## 🔧 Advanced Configuration

### Custom Network

```yaml
networks:
  ark-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Health Check Customization

```yaml
services:
  ark-api:
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Logging Configuration

```yaml
services:
  ark-api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "app,env"
```

## 📚 Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## 📞 Support

For issues:
1. Check logs: `docker-compose logs -f ark-api`
2. Verify config: `docker-compose config`
3. Check health: `curl http://localhost:8000/api/v1/health`
4. Review documentation: `/docs`
