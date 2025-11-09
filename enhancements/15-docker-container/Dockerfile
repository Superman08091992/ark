# ARK Intelligent Backend - Docker Image
# Multi-stage build for optimized image size

################################################################################
# Stage 1: Base image with dependencies
################################################################################
FROM node:20-alpine AS base

# Install system dependencies
RUN apk add --no-cache \
    bash \
    curl \
    redis \
    supervisor \
    tzdata

# Set working directory
WORKDIR /ark

################################################################################
# Stage 2: Dependencies installation
################################################################################
FROM base AS dependencies

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm ci --only=production && \
    npm cache clean --force

################################################################################
# Stage 3: Final image
################################################################################
FROM base AS final

# Set environment variables
ENV NODE_ENV=production \
    ARK_HOME=/ark \
    ARK_API_PORT=8000 \
    ARK_API_HOST=0.0.0.0 \
    ARK_REDIS_HOST=127.0.0.1 \
    ARK_REDIS_PORT=6379 \
    ARK_OLLAMA_HOST=http://127.0.0.1:11434 \
    ARK_OLLAMA_MODEL=llama3.2:1b \
    ARK_DEBUG=false

# Copy dependencies from dependencies stage
COPY --from=dependencies /ark/node_modules ./node_modules

# Copy application files
COPY lib ./lib
COPY bin ./bin
COPY config ./config

# Create necessary directories
RUN mkdir -p /ark/data/redis \
             /ark/data/logs \
             /ark/data/uploads && \
    chmod +x /ark/bin/*

# Copy supervisor configuration
COPY docker/supervisord.conf /etc/supervisord.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${ARK_API_PORT}/health || exit 1

# Expose ports
# 8000: ARK API
# 6379: Redis (if using internal Redis)
EXPOSE 8000 6379

# Volume for persistent data
VOLUME ["/ark/data"]

# Start supervisor (manages Redis + ARK backend)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]

################################################################################
# Build and Run Instructions
################################################################################
#
# Build image:
#   docker build -t ark-backend:latest -f enhancements/15-docker-container/Dockerfile .
#
# Run container:
#   docker run -d \
#     --name ark-backend \
#     -p 8000:8000 \
#     -v ark-data:/ark/data \
#     -e ARK_OLLAMA_HOST=http://host.docker.internal:11434 \
#     ark-backend:latest
#
# Run with external Redis:
#   docker run -d \
#     --name ark-backend \
#     -p 8000:8000 \
#     -e ARK_REDIS_HOST=redis \
#     --link redis:redis \
#     ark-backend:latest
#
# Run with environment file:
#   docker run -d \
#     --name ark-backend \
#     -p 8000:8000 \
#     --env-file .env \
#     ark-backend:latest
#
################################################################################

# Labels
LABEL maintainer="ARK Project" \
      description="ARK Intelligent Backend - AI-powered personal assistant" \
      version="1.0.0"
