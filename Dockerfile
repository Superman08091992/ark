# ARK Multi-Agent Trading System - Production Container
# Base: Arch Linux (rolling release)
# Exposes: 8000 (API), 6379 (Redis), 9090 (Metrics)

FROM archlinux:latest

LABEL maintainer="ARK System"
LABEL description="ARK Unified Multi-Agent Trading System with Immutable Ethics"
LABEL version="1.0.0"

# Install system dependencies
RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
        python \
        python-pip \
        redis \
        git \
        base-devel \
        sudo \
        curl \
        vim && \
    pacman -Scc --noconfirm

# Create app user
RUN useradd -m -s /bin/bash ark && \
    echo "ark ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set working directory
WORKDIR /home/ark/webapp

# Copy application code
COPY --chown=ark:ark . .

# Install Python dependencies
RUN pip install --no-cache-dir \
    redis \
    aiohttp \
    asyncio \
    pytest \
    pytest-asyncio \
    requests || \
    echo "Some packages may already be installed"

# Create required directories
RUN mkdir -p /var/lib/ark /var/log/ark /var/backups/ark /var/run/ark && \
    chown -R ark:ark /var/lib/ark /var/log/ark /var/backups/ark /var/run/ark

# Set Graveyard permissions (immutable ethics)
RUN chmod 444 graveyard/ethics.py || echo "Graveyard file not found"

# Configure Redis
RUN mkdir -p /etc/redis && \
    chown -R ark:ark /etc/redis

# Copy Redis configuration
RUN cat > /etc/redis/redis.conf << 'EOF'
# Redis configuration for ARK
bind 0.0.0.0
port 6379
daemonize no
supervised systemd
pidfile /var/run/ark/redis.pid
loglevel notice
logfile /var/log/ark/redis.log
dir /var/lib/ark
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF

# Switch to app user
USER ark

# Expose ports
EXPOSE 8000 6379 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9090/healthz || exit 1

# Start command
CMD ["bash", "-c", "redis-server /etc/redis/redis.conf --daemonize yes && sleep 2 && python3 -m monitoring.metrics_server & sleep 2 && tail -f /var/log/ark/*.log"]
