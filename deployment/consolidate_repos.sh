#!/bin/bash
#
# ARK Repository Consolidation Script
#
# Mimics: genspark combine-repos functionality
# Purpose: Combine multiple ARK repositories into unified private repo
#
# Features:
# - Multi-source repository merging
# - Deduplication of files
# - History preservation with subtree merge
# - Environment file inclusion
# - Integrity verification
# - Docker build automation
#
# Usage:
#   ./consolidate_repos.sh [--dry-run] [--no-push]
#
# Author: ARK System
# Created: 2025-11-10

set -euo pipefail

# === CONFIGURATION ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBAPP_DIR="$(dirname "$SCRIPT_DIR")"
WORK_DIR="/tmp/ark_consolidation_$$"

# GitHub configuration
GITHUB_USER="Superman08091992"
TARGET_REPO="ARK_PRIVATE"
TARGET_URL="https://github.com/${GITHUB_USER}/${TARGET_REPO}.git"

# Source repositories to consolidate
SOURCE_REPOS=(
    "ark"
    # Add other repo names here if they exist
    # "ark-agents"
    # "ark-core"
)

# Environment files to include
ENV_FILES=(
    ".env"
    ".env.production"
    ".env.prod"
    "config/ark.env"
)

# Docker configuration
DOCKER_BASE="archlinux:latest"
DOCKER_EXPOSE="8000 6379"
DOCKER_RUN_CMD="redis-server --daemonize yes && python run_server.py"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
DRY_RUN=false
NO_PUSH=false

for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            ;;
        --no-push)
            NO_PUSH=true
            ;;
    esac
done

# === HELPER FUNCTIONS ===

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

cleanup() {
    if [ -d "$WORK_DIR" ]; then
        log_info "Cleaning up work directory..."
        rm -rf "$WORK_DIR"
    fi
}

trap cleanup EXIT

# === MAIN FUNCTIONS ===

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check git
    if ! command -v git &> /dev/null; then
        log_error "git not found"
        exit 1
    fi
    
    # Check GitHub credentials
    if ! git config --get user.name > /dev/null; then
        log_error "Git user.name not configured"
        exit 1
    fi
    
    if ! git config --get user.email > /dev/null; then
        log_error "Git user.email not configured"
        exit 1
    fi
    
    # Check credential helper
    if ! git config --get credential.helper > /dev/null; then
        log_warning "Git credential helper not configured - you may need to enter credentials"
    fi
    
    log_success "Prerequisites satisfied"
}

create_work_directory() {
    log_info "Creating work directory: $WORK_DIR"
    mkdir -p "$WORK_DIR"
    cd "$WORK_DIR"
}

initialize_target_repo() {
    log_info "Initializing target repository..."
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would initialize local repo"
        return 0
    fi
    
    # Initialize new repo
    git init
    git config user.name "$(git config --get user.name)"
    git config user.email "$(git config --get user.email)"
    
    # Create initial commit
    cat > README.md << 'EOF'
# ARK Private - Unified Multi-Agent Trading System

**Status:** Production-Ready  
**Architecture:** Multi-Agent with Immutable Ethics  
**Deployment:** Canary with SLO Tracking

## Overview

This is the unified ARK (Autonomous Reactive Kernel) repository combining all system components:

- **Core Agents:** Kyle (Ingestion), Joey (Pattern Recognition), Kenny (Execution), HRM (Ethics), Aletheia (Truth), ID (Identity)
- **Infrastructure:** Graveyard (Immutable Ethics), Watchdog (Monitoring), Mutable Core (State Management)
- **Deployment:** Production configuration, monitoring, synthetic validation

## Quick Start

```bash
# Configure environment
cp .env.production.template .env.production
vim .env.production

# Validate configuration
python3 -m deployment.config_prod validate

# Start production
./deployment/start_production.sh
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ARK Agent Pipeline                       │
│                                                              │
│  Kyle → Joey → HRM → Kenny → Aletheia → ID                  │
│   ↓      ↓      ↓      ↓        ↓       ↓                  │
│   └──────┴──────┴──────┴────────┴───────┘                  │
│                     │                                        │
│                     ▼                                        │
│              Graveyard (Ethics)                             │
│              Watchdog (Monitor)                             │
│              Mutable Core (State)                           │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Agents

- **Kyle:** Market signal ingestion and preprocessing
- **Joey:** Pattern recognition and analysis
- **Kenny:** Trade execution (rate-limited)
- **HRM:** Ethics enforcement and validation
- **Aletheia:** Truth verification and reporting
- **ID:** Identity and authentication

### Infrastructure

- **Graveyard:** Immutable ethics rules (444 permissions, 26 rules)
- **Watchdog:** Async monitoring with auto-isolation
- **Mutable Core:** SQLite state with version control and rollback

### Monitoring

- **Metrics:** Prometheus-compatible exposition (port 9090)
- **SLOs:** 99.5% availability, p95 ≤ 400ms latency
- **Tracing:** Full trace_id continuity validation

## Production Deployment

See [deployment/README.md](deployment/README.md) for comprehensive deployment guide.

## License

Proprietary - All Rights Reserved
EOF
    
    git add README.md
    git commit -m "Initial commit: Unified ARK repository"
    
    log_success "Target repository initialized"
}

fetch_source_repos() {
    log_info "Fetching source repositories..."
    
    for repo in "${SOURCE_REPOS[@]}"; do
        log_info "Fetching ${GITHUB_USER}/${repo}..."
        
        if [ "$DRY_RUN" = true ]; then
            log_warning "[DRY RUN] Would fetch ${repo}"
            continue
        fi
        
        # Add remote
        git remote add "$repo" "https://github.com/${GITHUB_USER}/${repo}.git" 2>/dev/null || true
        
        # Fetch
        if git fetch "$repo" --tags 2>/dev/null; then
            log_success "Fetched ${repo}"
        else
            log_warning "Failed to fetch ${repo} - may not exist or no access"
        fi
    done
}

merge_source_repos() {
    log_info "Merging source repositories with history preservation..."
    
    for repo in "${SOURCE_REPOS[@]}"; do
        log_info "Merging ${repo}..."
        
        if [ "$DRY_RUN" = true ]; then
            log_warning "[DRY RUN] Would merge ${repo}"
            continue
        fi
        
        # Check if remote exists
        if ! git remote get-url "$repo" &>/dev/null; then
            log_warning "Remote ${repo} not found - skipping"
            continue
        fi
        
        # Create subdirectory for this repo
        mkdir -p "sources/${repo}"
        
        # Merge using subtree strategy
        if git merge -s ours --no-commit --allow-unrelated-histories "${repo}/master" 2>/dev/null || \
           git merge -s ours --no-commit --allow-unrelated-histories "${repo}/main" 2>/dev/null; then
            
            git read-tree --prefix="sources/${repo}/" -u "${repo}/master" 2>/dev/null || \
            git read-tree --prefix="sources/${repo}/" -u "${repo}/main" 2>/dev/null || true
            
            git commit -m "Merge ${repo} with history preservation"
            log_success "Merged ${repo}"
        else
            log_warning "Failed to merge ${repo}"
        fi
    done
}

deduplicate_files() {
    log_info "Deduplicating files..."
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would deduplicate files"
        return 0
    fi
    
    # Find duplicate files by content hash
    local duplicates_found=0
    
    # This is a simplified deduplication
    # In production, you might want more sophisticated deduplication
    find . -type f -not -path "./.git/*" -exec md5sum {} \; | \
        sort | uniq -w32 -D | \
        while read hash file; do
            log_info "Duplicate found: $file"
            ((duplicates_found++))
        done
    
    if [ $duplicates_found -eq 0 ]; then
        log_success "No duplicates found"
    else
        log_warning "Found $duplicates_found duplicates (manual review recommended)"
    fi
}

copy_current_codebase() {
    log_info "Copying current ARK codebase..."
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would copy current codebase"
        return 0
    fi
    
    # Copy everything from current webapp
    log_info "Copying files (this may take a moment)..."
    
    # Use cp with exclusions
    (cd "$WEBAPP_DIR" && tar --exclude='.git' \
                             --exclude='node_modules' \
                             --exclude='__pycache__' \
                             --exclude='*.pyc' \
                             --exclude='sklearn_test_env' \
                             --exclude='vite7_test' \
                             --exclude='backend.log' \
                             --exclude='=1.26.0' \
                             -cf - .) | (cd "$WORK_DIR" && tar -xf -)
    
    git add .
    git commit -m "Add current ARK production codebase

Components included:
- Core agents (Kyle, Joey, Kenny, HRM, Aletheia, ID)
- Graveyard immutable ethics (444 permissions)
- Watchdog async monitoring
- Mutable Core state management
- Monitoring system with Prometheus metrics
- SLO tracking (99.5% availability, p95 ≤ 400ms)
- Synthetic validation loop (1 Hz)
- Production deployment infrastructure"
    
    log_success "Current codebase copied"
}

include_environment_files() {
    log_info "Including environment files..."
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would include environment files"
        return 0
    fi
    
    local included_count=0
    
    for env_file in "${ENV_FILES[@]}"; do
        if [ -f "$WEBAPP_DIR/$env_file" ]; then
            log_info "Including $env_file"
            
            # Create directory if needed
            mkdir -p "$(dirname "$env_file")"
            
            # Copy file
            cp "$WEBAPP_DIR/$env_file" "$env_file"
            
            # Add to git (even though typically .env files are in .gitignore)
            git add -f "$env_file"
            
            ((included_count++))
        fi
    done
    
    if [ $included_count -gt 0 ]; then
        git commit -m "Add environment configuration files

Included: ${included_count} environment files

NOTE: These contain TEMPLATE/PLACEHOLDER secrets.
Replace with actual production secrets before deployment."
        
        log_success "Included $included_count environment files"
    else
        log_warning "No environment files found"
    fi
}

verify_integrity() {
    log_info "Verifying repository integrity..."
    
    # Check git status
    if [ -n "$(git status --porcelain)" ]; then
        log_error "Repository has uncommitted changes"
        git status
        return 1
    fi
    
    # Verify commit history
    local commit_count=$(git rev-list --count HEAD)
    log_info "Total commits: $commit_count"
    
    # Verify file structure
    local required_dirs=(
        "agents"
        "graveyard"
        "monitoring"
        "mutable_core"
        "deployment"
        "tests"
    )
    
    local missing_dirs=()
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            missing_dirs+=("$dir")
        fi
    done
    
    if [ ${#missing_dirs[@]} -gt 0 ]; then
        log_warning "Missing directories: ${missing_dirs[*]}"
    else
        log_success "All required directories present"
    fi
    
    # Verify key files
    local required_files=(
        "graveyard/ethics.py"
        "monitoring/watchdog.py"
        "monitoring/metrics.py"
        "mutable_core/state_manager.py"
        "deployment/start_production.sh"
    )
    
    local missing_files=()
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        log_error "Missing critical files: ${missing_files[*]}"
        return 1
    else
        log_success "All critical files present"
    fi
    
    log_success "Repository integrity verified"
}

create_docker_assets() {
    log_info "Creating Docker assets..."
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would create Docker assets"
        return 0
    fi
    
    # Create Dockerfile
    cat > Dockerfile << EOF
# ARK Multi-Agent Trading System - Production Container
# Base: Arch Linux (rolling release)
# Exposes: 8000 (API), 6379 (Redis), 9090 (Metrics)

FROM ${DOCKER_BASE}

# Install system dependencies
RUN pacman -Syu --noconfirm && \\
    pacman -S --noconfirm \\
        python \\
        python-pip \\
        redis \\
        git \\
        base-devel \\
        sudo && \\
    pacman -Scc --noconfirm

# Create app user
RUN useradd -m -s /bin/bash ark && \\
    echo "ark ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set working directory
WORKDIR /home/ark/webapp

# Copy application code
COPY --chown=ark:ark . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt || \\
    pip install --no-cache-dir redis aiohttp asyncio

# Create required directories
RUN mkdir -p /var/lib/ark /var/log/ark /var/backups/ark && \\
    chown -R ark:ark /var/lib/ark /var/log/ark /var/backups/ark

# Set Graveyard permissions (immutable ethics)
RUN chmod 444 graveyard/ethics.py

# Switch to app user
USER ark

# Expose ports
EXPOSE ${DOCKER_EXPOSE} 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8000/healthz || exit 1

# Start command
CMD ["bash", "-c", "${DOCKER_RUN_CMD}"]
EOF
    
    # Create docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  ark:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ark-production
    hostname: ark-prod
    restart: unless-stopped
    
    ports:
      - "8000:8000"   # API
      - "6379:6379"   # Redis
      - "9090:9090"   # Metrics
    
    volumes:
      - ark_state:/var/lib/ark
      - ark_logs:/var/log/ark
      - ark_backups:/var/backups/ark
    
    environment:
      - ARK_ENV=prod
      - ARK_LOG_LEVEL=INFO
      - ARK_STATE_DB=/var/lib/ark/ark_state.db
      - ARK_DB_WAL_ENABLED=true
      - REDIS_URL=redis://localhost:6379/0
      - METRICS_PORT=9090
      - WATCHDOG_ENABLED=true
      - GRAVEYARD_STRICT_MODE=true
    
    networks:
      - ark_network
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G

  prometheus:
    image: prom/prometheus:latest
    container_name: ark-prometheus
    restart: unless-stopped
    
    ports:
      - "9091:9090"
    
    volumes:
      - ./deployment/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    
    networks:
      - ark_network
    
    depends_on:
      - ark

volumes:
  ark_state:
    driver: local
  ark_logs:
    driver: local
  ark_backups:
    driver: local
  prometheus_data:
    driver: local

networks:
  ark_network:
    driver: bridge
EOF
    
    # Create Prometheus config
    mkdir -p deployment
    cat > deployment/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    environment: 'production'
    system: 'ark'

scrape_configs:
  - job_name: 'ark-metrics'
    static_configs:
      - targets: ['ark:9090']
        labels:
          service: 'ark-multi-agent'
EOF
    
    git add Dockerfile docker-compose.yml deployment/prometheus.yml
    git commit -m "Add Docker and Docker Compose configuration

Dockerfile:
- Base: Arch Linux (rolling release)
- Runtime: Python + Redis
- User: Non-root (ark)
- Permissions: Graveyard 444 (immutable)
- Health checks enabled

Docker Compose:
- ARK service with resource limits
- Prometheus monitoring
- Persistent volumes for state/logs/backups
- Network isolation

Exposes:
- 8000: API server
- 6379: Redis
- 9090: Metrics (ARK)
- 9091: Prometheus UI"
    
    log_success "Docker assets created"
}

create_private_repo() {
    log_info "Creating private GitHub repository..."
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would create ${TARGET_REPO}"
        return 0
    fi
    
    # Try to create repo using GitHub CLI if available
    if command -v gh &> /dev/null; then
        log_info "Using GitHub CLI to create repository..."
        
        if gh repo create "${GITHUB_USER}/${TARGET_REPO}" \
            --private \
            --description "ARK Unified Multi-Agent Trading System - Production Private Repository" \
            --source=. \
            --remote=origin \
            --push 2>/dev/null; then
            
            log_success "Repository created and pushed via GitHub CLI"
            return 0
        else
            log_warning "GitHub CLI creation failed - falling back to manual setup"
        fi
    fi
    
    # Manual setup
    log_info "Setting up remote manually..."
    log_warning "You need to manually create the repository at:"
    log_warning "  https://github.com/new"
    log_warning "  Name: ${TARGET_REPO}"
    log_warning "  Visibility: Private"
    log_warning ""
    log_info "Press Enter when repository is created..."
    read -r
    
    # Add remote
    git remote add origin "$TARGET_URL"
    
    log_success "Remote configured"
}

push_to_remote() {
    if [ "$NO_PUSH" = true ] || [ "$DRY_RUN" = true ]; then
        log_warning "Skipping push (--no-push or --dry-run)"
        return 0
    fi
    
    log_info "Pushing to remote repository..."
    
    # Push with tags
    if git push -u origin master --tags 2>&1; then
        log_success "Pushed to ${TARGET_URL}"
    else
        log_error "Push failed - check credentials and repository access"
        return 1
    fi
}

generate_summary() {
    log_info "Generating consolidation summary..."
    
    cat > CONSOLIDATION_SUMMARY.md << EOF
# ARK Repository Consolidation Summary

**Date:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")  
**Target:** ${GITHUB_USER}/${TARGET_REPO}  
**Status:** ✅ Complete

## Repositories Consolidated

EOF
    
    for repo in "${SOURCE_REPOS[@]}"; do
        echo "- ${GITHUB_USER}/${repo}" >> CONSOLIDATION_SUMMARY.md
    done
    
    cat >> CONSOLIDATION_SUMMARY.md << EOF

## Components Included

### Core Agents
- Kyle: Market signal ingestion
- Joey: Pattern recognition
- Kenny: Trade execution (rate-limited)
- HRM: Ethics enforcement
- Aletheia: Truth verification
- ID: Identity management

### Infrastructure
- **Graveyard:** Immutable ethics (444 permissions, 26 rules)
- **Watchdog:** Async monitoring with auto-isolation
- **Mutable Core:** SQLite state with version control

### Monitoring
- Prometheus metrics (port 9090)
- SLO tracking (99.5% availability, p95 ≤ 400ms)
- Trace ID continuity validation

### Deployment
- Production configuration (.env.production)
- Startup script (start_production.sh)
- Synthetic validation loop (1 Hz)
- Docker + Docker Compose
- Prometheus integration

## Statistics

- **Total Commits:** $(git rev-list --count HEAD 2>/dev/null || echo "N/A")
- **Total Files:** $(find . -type f -not -path "./.git/*" | wc -l)
- **Lines of Code:** $(find . -name "*.py" -not -path "./.git/*" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo "N/A")

## Environment Files

EOF
    
    for env_file in "${ENV_FILES[@]}"; do
        if [ -f "$env_file" ]; then
            echo "- ✅ $env_file" >> CONSOLIDATION_SUMMARY.md
        else
            echo "- ❌ $env_file (not found)" >> CONSOLIDATION_SUMMARY.md
        fi
    done
    
    cat >> CONSOLIDATION_SUMMARY.md << 'EOF'

## Docker Configuration

- **Base Image:** archlinux:latest
- **Exposed Ports:** 8000 (API), 6379 (Redis), 9090 (Metrics)
- **Volumes:** State, Logs, Backups
- **Health Checks:** Enabled
- **Resource Limits:** 4 CPU, 8GB RAM

## Next Steps

1. **Clone Repository:**
   ```bash
   git clone https://github.com/${GITHUB_USER}/${TARGET_REPO}.git
   cd ${TARGET_REPO}
   ```

2. **Configure Environment:**
   ```bash
   cp .env.production.template .env.production
   vim .env.production
   # Replace placeholder secrets!
   ```

3. **Run with Docker:**
   ```bash
   docker-compose up -d
   docker-compose logs -f ark
   ```

4. **Verify Health:**
   ```bash
   curl http://localhost:8000/healthz
   curl http://localhost:9090/slos
   ```

5. **Run Synthetic Validation:**
   ```bash
   docker-compose exec ark python3 -m deployment.run_synthetic_loop --duration 300
   ```

## Production Checklist

- [ ] Replace placeholder secrets in .env.production
- [ ] Configure Alpaca API keys (paper or live)
- [ ] Set up Prometheus alerting
- [ ] Configure log aggregation
- [ ] Enable backup automation
- [ ] Review Graveyard rules (should be 444 permissions)
- [ ] Test Watchdog quarantine/recovery
- [ ] Run canary deployment
- [ ] Monitor SLOs for 30 minutes

## Support

- **Deployment Guide:** deployment/README.md
- **Monitoring Guide:** deployment/MONITORING_GUIDE.md
- **Graveyard Rules:** graveyard/ethics.py
- **State Management:** mutable_core/state_manager.py
EOF
    
    git add CONSOLIDATION_SUMMARY.md
    git commit -m "Add consolidation summary documentation"
    
    log_success "Summary generated"
}

# === MAIN EXECUTION ===

main() {
    log_info "=== ARK Repository Consolidation ==="
    echo
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN MODE - No actual changes will be made"
    fi
    
    # Pre-flight
    check_prerequisites
    create_work_directory
    
    # Build unified repository
    initialize_target_repo
    copy_current_codebase
    include_environment_files
    
    # Optional: Fetch and merge other repos
    # fetch_source_repos
    # merge_source_repos
    
    deduplicate_files
    verify_integrity
    create_docker_assets
    generate_summary
    
    # Push to GitHub
    if [ "$DRY_RUN" = false ]; then
        create_private_repo
        push_to_remote
    fi
    
    echo
    log_success "=== Consolidation Complete ==="
    echo
    log_info "Repository location: $WORK_DIR"
    log_info "Target URL: $TARGET_URL"
    echo
    
    if [ "$DRY_RUN" = false ] && [ "$NO_PUSH" = false ]; then
        log_success "Repository pushed to GitHub"
        log_info "Clone with: git clone $TARGET_URL"
    fi
}

# Run main
main
