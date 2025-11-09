# ARK Docker Container

Complete Docker containerization of ARK for easy deployment and portability.

## 🎯 Features

- **Multi-stage build** for optimized image size
- **All-in-one container** with Redis and Ollama
- **Non-root user** for security
- **Health checks** built-in
- **Persistent volumes** for data
- **Docker Compose** support
- **Easy configuration** via environment variables

## 📦 Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# 1. Create configuration file
cp ark.env.example ark.env
# Edit ark.env with your settings

# 2. Start ARK
docker-compose up -d

# 3. Check status
docker-compose ps
docker-compose logs -f ark

# 4. Access ARK
curl http://localhost:8000/health
```

### Option 2: Using Docker Directly

```bash
# 1. Build image
docker build -t ark:latest -f enhancements/15-docker-container/Dockerfile .

# 2. Run container
docker run -d \
  --name ark \
  -p 8000:8000 \
  -v ark-data:/home/ark/ark/data \
  -e ARK_API_PORT=8000 \
  -e ARK_DEBUG=false \
  ark:latest

# 3. Check logs
docker logs -f ark

# 4. Access ARK
curl http://localhost:8000/health
```

## 🔧 Configuration

### Environment Variables

Create `ark.env` file:

```bash
# API Configuration
ARK_API_PORT=8000
ARK_API_HOST=0.0.0.0
ARK_DEBUG=false

# Redis Configuration
ARK_REDIS_HOST=127.0.0.1
ARK_REDIS_PORT=6379

# Ollama Configuration
ARK_OLLAMA_HOST=http://127.0.0.1:11434
ARK_OLLAMA_MODEL=llama3.2:1b
ARK_OLLAMA_ENABLED=true

# Advanced
ARK_WORKERS=4
ARK_TIMEOUT=30
ARK_LOG_LEVEL=INFO
```

### Ports

- **8000** - ARK API (HTTP)
- **6379** - Redis (internal, optional expose)
- **11434** - Ollama (internal, optional expose)

### Volumes

```yaml
volumes:
  # Data directory (Redis, Ollama models, etc.)
  - ark-data:/home/ark/ark/data
  
  # Configuration file (optional)
  - ./ark.env:/home/ark/ark/.env:ro
```

## 📋 Docker Compose Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f ark

# Check status
docker-compose ps

# Execute commands in container
docker-compose exec ark ark-health

# Update and restart
docker-compose pull
docker-compose up -d
```

## 🏗️ Building from Source

```bash
# Build with custom tag
docker build -t myusername/ark:v1.0 \
  -f enhancements/15-docker-container/Dockerfile .

# Build with build args
docker build \
  --build-arg NODE_VERSION=20 \
  -t ark:latest \
  -f enhancements/15-docker-container/Dockerfile .

# Push to registry
docker push myusername/ark:v1.0
```

## 🔍 Troubleshooting

### Check container status
```bash
docker ps -a | grep ark
```

### View logs
```bash
docker logs ark
docker logs --tail 100 -f ark
```

### Enter container
```bash
docker exec -it ark bash
```

### Check health
```bash
docker inspect --format='{{.State.Health.Status}}' ark
```

### Restart services inside container
```bash
docker exec ark ark-services restart
```

## 🧪 Testing

```bash
# Build test image
docker build -t ark:test -f enhancements/15-docker-container/Dockerfile .

# Run test container
docker run --rm -it ark:test bash

# Test ARK installation
docker run --rm ark:test ark --version
docker run --rm ark:test ark-health
```

## 🚀 Production Deployment

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml ark

# Check services
docker service ls
docker service logs ark_ark
```

### Using Kubernetes

```yaml
# See kubernetes-deployment.yml (coming soon)
```

### Resource Limits

Add to docker-compose.yml:

```yaml
services:
  ark:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## 🔐 Security

### Non-root User

Container runs as `ark` user (not root) for security.

### Read-only Filesystem

Add to docker-compose.yml:

```yaml
services:
  ark:
    read_only: true
    tmpfs:
      - /tmp
      - /home/ark/ark/data
```

### Network Isolation

```yaml
services:
  ark:
    networks:
      - ark-internal
    ports:
      - "127.0.0.1:8000:8000"  # Only localhost
```

## 📊 Monitoring

### Health Check

Built-in health check at `/health` endpoint.

### Resource Usage

```bash
# Container stats
docker stats ark

# Detailed inspection
docker inspect ark
```

## 🔄 Updates

```bash
# Pull latest changes
git pull

# Rebuild image
docker-compose build --no-cache

# Restart with new image
docker-compose up -d
```

## 🗑️ Cleanup

```bash
# Stop and remove container
docker-compose down

# Remove volumes (⚠️ deletes data!)
docker-compose down -v

# Remove image
docker rmi ark:latest

# Clean all Docker artifacts
docker system prune -a
```

## 📝 Notes

- Container includes Redis and Ollama internally
- Data persists in named volumes
- Configuration via environment variables or .env file
- Automatic service startup on container start
- Health checks ensure services are running

## 🐛 Common Issues

### Port already in use
```bash
# Change port mapping in docker-compose.yml
ports:
  - "8080:8000"  # Use different host port
```

### Permission issues
```bash
# Fix volume permissions
docker-compose down
docker volume rm ark_ark-data
docker-compose up -d
```

### Out of memory
```bash
# Increase memory limit
docker update --memory 2g ark
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [ARK Documentation](../../README.md)

---

**Built with ❤️ for easy ARK deployment**
