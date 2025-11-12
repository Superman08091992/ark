# ARK Sovereign Intelligence - Multi-arch Docker Image
# Supports: linux/amd64, linux/arm64, linux/arm/v7

FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    sqlite3 \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt requirements.prod.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.prod.txt && \
    pip install gunicorn uvicorn[standard]

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs keys agent_logs && \
    chmod 755 data logs keys agent_logs

# Expose ports
EXPOSE 8000 8101 8104

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8101/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["python3", "reasoning_api.py"]
