# ARK Docker Container
# Multi-stage build for optimized image size

################################################################################
# Stage 1: Base Image with Dependencies
################################################################################
FROM node:20-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Create ark user
RUN useradd -m -s /bin/bash ark

WORKDIR /home/ark

################################################################################
# Stage 2: ARK Installation
################################################################################
FROM base AS ark-install

# Copy ARK source files
COPY --chown=ark:ark . /home/ark/ark-source

# Switch to ark user
USER ark

# Install ARK
RUN cd /home/ark && \
    bash /home/ark/ark-source/create-unified-ark.sh --docker && \
    tar xzf ark-complete-*.tar.gz && \
    cd ark-complete-*/ && \
    bash install.sh --non-interactive --prefix /home/ark/ark

################################################################################
# Stage 3: Final Runtime Image
################################################################################
FROM node:20-slim AS runtime

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    redis-server \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create ark user
RUN useradd -m -s /bin/bash ark

# Copy installed ARK from build stage
COPY --from=ark-install --chown=ark:ark /home/ark/ark /home/ark/ark

# Set working directory
WORKDIR /home/ark/ark

# Switch to ark user
USER ark

# Expose ports
EXPOSE 8000 6379 11434

# Environment variables
ENV ARK_HOME=/home/ark/ark
ENV PATH="${ARK_HOME}/bin:${PATH}"
ENV NODE_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Volume for persistent data
VOLUME ["/home/ark/ark/data", "/home/ark/ark/.env"]

# Start script
COPY --chown=ark:ark docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["ark", "start"]
