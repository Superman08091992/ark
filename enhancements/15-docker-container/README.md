# ARK Docker Container

Complete Docker deployment for ARK Intelligent Backend.

## 📦 What's Included

- **Dockerfile**: Multi-stage build for optimized image
- **docker-compose.yml**: Complete stack with Redis and Ollama
- **supervisord.conf**: Process manager for Redis + ARK
- **.dockerignore**: Optimized build context
- **Scripts**: Management utilities

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# 1. Navigate to project root
cd /path/to/ark

# 2. Create environment file
cat > .env << EOF
ARK_API_PORT=8000
ARK_REDIS_PASSWORD=secure_password_here
ARK_OLLAMA_HOST=http://host.docker.internal:11434
ARK_OLLAMA_MODEL=llama3.2:1b
EOF

# 3. Start services
docker-compose -f enhancements/15-docker-container/docker-compose.yml up -d

# 4. Check status
docker-compose -f enhancements/15-docker-container/docker-compose.yml ps

# 5. View logs
docker-compose -f enhancements/15-docker-container/docker-compose.yml logs -f ark
```

### Option 2: Docker CLI

```bash
# 1. Build image
docker build -t ark-backend:latest \
  -f enhancements/15-docker-container/Dockerfile .

# 2. Run container
docker run -d \
  --name ark-backend \
  -p 8000:8000 \
  -v ark-data:/ark/data \
  -e ARK_OLLAMA_HOST=http://host.docker.internal:11434 \
  ark-backend:latest

# 3. Check logs
docker logs -f ark-backend
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ARK_API_PORT` | `8000` | API server port |
| `ARK_API_HOST` | `0.0.0.0` | Listen address |
| `ARK_REDIS_HOST` | `127.0.0.1` | Redis hostname |
| `ARK_REDIS_PORT` | `6379` | Redis port |
| `ARK_REDIS_PASSWORD` | _(empty)_ | Redis password |
| `ARK_OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama URL |
| `ARK_OLLAMA_MODEL` | `llama3.2:1b` | Default LLM model |
| `ARK_DEBUG` | `false` | Debug mode |
| `ARK_WORKERS` | `4` | Worker threads |
| `ARK_LOG_LEVEL` | `INFO` | Log verbosity |

### Using Host Ollama

If Ollama is running on your host machine:

```yaml
environment:
  ARK_OLLAMA_HOST: http://host.docker.internal:11434
```

### Using Docker Ollama

Uncomment the `ollama` service in `docker-compose.yml`:

```yaml
ollama:
  image: ollama/ollama:latest
  # ... (see docker-compose.yml)
```

Then pull a model:

```bash
docker-compose exec ollama ollama pull llama3.2:1b
```

## 📊 Service Management

### Docker Compose Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart ARK
docker-compose restart ark

# View logs
docker-compose logs -f ark
docker-compose logs -f redis

# Execute commands
docker-compose exec ark /bin/bash

# Check status
docker-compose ps
```

### Docker CLI Commands

```bash
# Start
docker start ark-backend

# Stop
docker stop ark-backend

# Restart
docker restart ark-backend

# Logs
docker logs -f ark-backend

# Shell access
docker exec -it ark-backend /bin/bash

# Health check
docker inspect --format='{{.State.Health.Status}}' ark-backend
```

## 💾 Data Persistence

### Volumes

- `ark-data`: Application data, logs, uploads
- `ark-redis-data`: Redis persistence
- `ark-ollama-data`: Ollama models (if using Docker Ollama)

### Backup

```bash
# Backup all data
docker run --rm \
  -v ark-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/ark-backup-$(date +%Y%m%d).tar.gz -C /data .

# Backup Redis only
docker run --rm \
  -v ark-redis-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/redis-backup-$(date +%Y%m%d).tar.gz -C /data .
```

### Restore

```bash
# Restore data
docker run --rm \
  -v ark-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/ark-backup-YYYYMMDD.tar.gz -C /data
```

## 🔍 Troubleshooting

### Container won't start

```bash
# Check logs
docker logs ark-backend

# Check configuration
docker inspect ark-backend

# Verify environment
docker exec ark-backend env
```

### Cannot connect to Ollama

```bash
# Test from container
docker exec ark-backend curl http://host.docker.internal:11434/api/tags

# Verify host Ollama is running
ollama list

# Check Ollama is listening on all interfaces
# In Ollama config, set OLLAMA_HOST=0.0.0.0
```

### Redis connection failed

```bash
# Check Redis container
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis
```

## 🌐 Networking

### Accessing from Other Devices

```bash
# Get your host IP
ip addr show | grep "inet " | grep -v 127.0.0.1

# Access ARK from another device
http://YOUR_HOST_IP:8000
```

### Port Mapping

Default ports:
- `8000`: ARK API
- `6379`: Redis (internal)
- `11434`: Ollama (if using Docker Ollama)

Change ports in `.env`:
```
ARK_API_PORT=8080
```

## 🔒 Security

### Production Deployment

1. **Use HTTPS**: Put ARK behind reverse proxy (nginx/caddy)
2. **Set Redis Password**: Use `ARK_REDIS_PASSWORD`
3. **Limit Exposure**: Use firewall rules
4. **Update Regularly**: Pull latest images
5. **Monitor Logs**: Enable log aggregation

### Example with Traefik

```yaml
services:
  ark:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.ark.rule=Host(`ark.yourdomain.com`)"
      - "traefik.http.routers.ark.tls=true"
      - "traefik.http.routers.ark.tls.certresolver=letsencrypt"
```

## 📈 Performance Tuning

### Resource Limits

```yaml
services:
  ark:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 512M
```

### Scaling

```bash
# Scale ARK (requires load balancer)
docker-compose up -d --scale ark=3
```

## 🛠️ Development

### Build Development Image

```bash
# With hot reload
docker build -t ark-backend:dev \
  --target development \
  -f Dockerfile.dev .

# Mount source code
docker run -d \
  --name ark-dev \
  -p 8000:8000 \
  -v $(pwd)/lib:/ark/lib \
  ark-backend:dev
```

## 📝 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Ollama Docker](https://hub.docker.com/r/ollama/ollama)
- [Redis Docker](https://hub.docker.com/_/redis)

## ❓ Support

For issues or questions:
1. Check container logs: `docker logs ark-backend`
2. Verify configuration: `docker inspect ark-backend`
3. Test connectivity: `docker exec ark-backend curl localhost:8000`
4. Review GitHub issues

---

**Built with ❤️ for the ARK Project**
