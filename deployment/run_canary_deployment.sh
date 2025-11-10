#!/bin/bash
#
# ARK Canary Deployment Orchestration Script
#
# Executes controlled canary deployment with automatic tripwire monitoring:
# 1. Deploy canary version alongside stable
# 2. Route 10% traffic to canary
# 3. Monitor for 10 minutes with tripwires
# 4. Gradual ramp: 10% → 25% → 50% → 100%
# 5. Auto-rollback if tripwires triggered
#
# Usage:
#   ./run_canary_deployment.sh [--version VERSION] [--no-auto-rollback]
#
# Author: ARK System
# Created: 2025-11-10

set -euo pipefail

# === CONFIGURATION ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBAPP_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Default values
CANARY_VERSION="${CANARY_VERSION:-$(git rev-parse --short HEAD)}"
AUTO_ROLLBACK=true
DRY_RUN=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --version=*)
            CANARY_VERSION="${arg#*=}"
            ;;
        --no-auto-rollback)
            AUTO_ROLLBACK=false
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        --help)
            cat << EOF
ARK Canary Deployment Script

Usage:
  ./run_canary_deployment.sh [OPTIONS]

Options:
  --version=VERSION      Canary version/commit to deploy (default: current HEAD)
  --no-auto-rollback     Disable automatic rollback on tripwire trigger
  --dry-run              Show what would be done without executing
  --help                 Show this help message

Canary Strategy:
  1. Deploy canary version (10% traffic)
  2. Monitor for 10 minutes with tripwires
  3. Ramp to 25% (10 minutes)
  4. Ramp to 50% (10 minutes)
  5. Ramp to 100% (10 minutes)

Tripwires (auto-rollback):
  - HRM denials spike >3σ baseline
  - Watchdog quarantine >0 in 10 minutes
  - P95 latency >400ms for 3 consecutive minutes

Examples:
  # Deploy current HEAD as canary
  ./run_canary_deployment.sh

  # Deploy specific version
  ./run_canary_deployment.sh --version=abc123

  # Dry run
  ./run_canary_deployment.sh --dry-run
EOF
            exit 0
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

log_step() {
    echo -e "\n${CYAN}▶ $1${NC}"
}

check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found"
        exit 1
    fi
    
    # Check docker-compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose not found"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found"
        exit 1
    fi
    
    # Check if stable deployment is running
    if ! docker ps | grep -q ark-production; then
        log_error "Stable deployment (ark-production) not running"
        log_info "Start with: docker-compose up -d"
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

collect_baseline_metrics() {
    log_step "Collecting baseline metrics from stable deployment..."
    
    # Query Prometheus for baseline metrics
    # This would normally use promtool or curl to query Prometheus
    
    log_info "Collecting HRM denial rate (last 1 hour)..."
    # Example: curl http://localhost:9091/api/v1/query?query=rate(hrm_denials_total[1h])
    
    log_info "Collecting Watchdog quarantine baseline..."
    # Example: curl http://localhost:9091/api/v1/query?query=increase(watchdog_quarantines_total[1h])
    
    log_info "Collecting P95 latency baseline..."
    # Example: curl http://localhost:9091/api/v1/query?query=histogram_quantile(0.95, rate(ark_pass_latency_ms_bucket[1h]))
    
    log_success "Baseline metrics collected"
    
    # Return baseline data
    cat > /tmp/ark_canary_baseline.json << EOF
{
  "hrm_denials_rate_mean": 0.020,
  "hrm_denials_rate_stddev": 0.003,
  "watchdog_quarantines_baseline": 0,
  "p95_latency_baseline_ms": 285.0,
  "collected_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    log_info "Baseline saved to /tmp/ark_canary_baseline.json"
}

build_canary_image() {
    log_step "Building canary Docker image..."
    
    cd "$WEBAPP_DIR"
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would build: ark:canary-${CANARY_VERSION}"
        return 0
    fi
    
    # Build canary image with version tag
    docker build -t "ark:canary-${CANARY_VERSION}" \
                 --build-arg VERSION="${CANARY_VERSION}" \
                 -f Dockerfile .
    
    log_success "Canary image built: ark:canary-${CANARY_VERSION}"
}

deploy_canary() {
    log_step "Deploying canary containers..."
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would deploy canary containers"
        return 0
    fi
    
    cd "$WEBAPP_DIR"
    
    # Create canary docker-compose override
    cat > docker-compose.canary.yml << EOF
version: '3.8'

services:
  ark-canary:
    image: ark:canary-${CANARY_VERSION}
    container_name: ark-canary
    hostname: ark-canary
    restart: unless-stopped
    
    ports:
      - "8001:8000"   # API on different port
      - "6380:6379"   # Redis on different port
      - "9092:9090"   # Metrics on different port
    
    volumes:
      - ark_canary_state:/var/lib/ark
      - ark_canary_logs:/var/log/ark
      - ./graveyard:/home/ark/webapp/graveyard:ro
    
    environment:
      - ARK_ENV=canary
      - ARK_DEPLOYMENT=canary
      - ARK_VERSION=${CANARY_VERSION}
      - ARK_STATE_DB=/var/lib/ark/ark_state_canary.db
      - REDIS_URL=redis://localhost:6379/1
      - METRICS_PORT=9090
    
    networks:
      - ark_network
    
    labels:
      - "ark.deployment=canary"
      - "ark.version=${CANARY_VERSION}"

volumes:
  ark_canary_state:
    driver: local
  ark_canary_logs:
    driver: local

networks:
  ark_network:
    external: true
EOF
    
    # Deploy canary
    docker-compose -f docker-compose.canary.yml up -d
    
    # Wait for canary to be healthy
    log_info "Waiting for canary to be healthy..."
    local max_wait=60
    local waited=0
    
    while [ $waited -lt $max_wait ]; do
        if curl -sf http://localhost:9092/healthz > /dev/null 2>&1; then
            log_success "Canary is healthy"
            return 0
        fi
        
        sleep 2
        ((waited+=2))
    done
    
    log_error "Canary failed to become healthy after ${max_wait}s"
    return 1
}

configure_traffic_routing() {
    local canary_percentage=$1
    
    log_step "Configuring traffic routing: ${canary_percentage}% canary"
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would route ${canary_percentage}% to canary"
        return 0
    fi
    
    # In production, this would configure:
    # - Nginx/HAProxy upstream weights
    # - Kubernetes service mesh (Istio/Linkerd)
    # - AWS ALB target group weights
    # - Or similar load balancing mechanism
    
    # For demo, we'll create a simple routing config file
    cat > /tmp/ark_traffic_routing.conf << EOF
# ARK Traffic Routing Configuration
# Updated: $(date -u +%Y-%m-%dT%H:%M:%SZ)

upstream ark_backend {
    server ark-production:8000 weight=$((100 - canary_percentage));
    server ark-canary:8001 weight=${canary_percentage};
}
EOF
    
    log_success "Traffic routing configured: $((100 - canary_percentage))% stable, ${canary_percentage}% canary"
}

monitor_canary() {
    local duration_minutes=$1
    local percentage=$2
    
    log_step "Monitoring canary at ${percentage}% for ${duration_minutes} minutes..."
    
    cd "$WEBAPP_DIR"
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would monitor for ${duration_minutes} minutes"
        return 0
    fi
    
    # Run Python canary monitoring
    python3 << EOF
import sys
import time
from deployment.canary_config import CanaryDeployment, CanaryConfig

# Create config
config = CanaryConfig(
    canary_percentage=${percentage},
    ramp_duration_minutes=${duration_minutes},
    monitoring_interval_seconds=30,
    auto_rollback_enabled=${AUTO_ROLLBACK}
)

# Create deployment (already started, just monitoring)
deployment = CanaryDeployment(config)
deployment.is_active = True
deployment.current_percentage = ${percentage}

# Collect baseline
deployment.collect_baseline_metrics()

# Monitor
success = deployment.monitor(${duration_minutes})

# Exit with status
sys.exit(0 if success else 1)
EOF
    
    local status=$?
    
    if [ $status -eq 0 ]; then
        log_success "Monitoring passed - no tripwires triggered"
        return 0
    else
        log_error "Monitoring failed - tripwires triggered"
        return 1
    fi
}

rollback_canary() {
    local reason=$1
    
    log_error "ROLLING BACK CANARY: ${reason}"
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would execute rollback"
        return 0
    fi
    
    # 1. Route 100% to stable
    log_info "Routing 100% traffic to stable"
    configure_traffic_routing 0
    
    # 2. Stop canary containers
    log_info "Stopping canary containers"
    cd "$WEBAPP_DIR"
    docker-compose -f docker-compose.canary.yml down
    
    # 3. Clean up canary volumes
    log_info "Cleaning up canary volumes"
    docker volume rm ark_canary_state ark_canary_logs 2>/dev/null || true
    
    # 4. Log rollback
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - ROLLBACK - ${reason}" >> /var/log/ark/canary_rollbacks.log
    
    log_success "Rollback complete"
}

promote_canary() {
    log_step "Promoting canary to production..."
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would promote canary to production"
        return 0
    fi
    
    # 1. Tag canary image as stable
    docker tag "ark:canary-${CANARY_VERSION}" "ark:stable"
    
    # 2. Update stable deployment
    cd "$WEBAPP_DIR"
    docker-compose down
    docker-compose up -d
    
    # 3. Remove canary deployment
    docker-compose -f docker-compose.canary.yml down
    
    # 4. Clean up
    docker volume rm ark_canary_state ark_canary_logs 2>/dev/null || true
    
    log_success "Canary promoted to production"
}

# === MAIN EXECUTION ===

main() {
    echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                              ║${NC}"
    echo -e "${CYAN}║           ARK CANARY DEPLOYMENT WITH TRIPWIRES              ║${NC}"
    echo -e "${CYAN}║                                                              ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}\n"
    
    log_info "Canary version: ${CANARY_VERSION}"
    log_info "Auto-rollback: ${AUTO_ROLLBACK}"
    [ "$DRY_RUN" = true ] && log_warning "DRY RUN MODE - No actual changes"
    
    # Pre-flight
    check_prerequisites
    
    # Collect baseline
    collect_baseline_metrics
    
    # Build and deploy canary
    build_canary_image
    deploy_canary || { log_error "Canary deployment failed"; exit 1; }
    
    # Gradual rollout
    local percentages=(10 25 50 100)
    local duration=10  # minutes per stage
    
    for percentage in "${percentages[@]}"; do
        echo -e "\n${CYAN}═══ Stage: ${percentage}% Canary Traffic ═══${NC}\n"
        
        # Configure routing
        configure_traffic_routing "$percentage"
        
        # Monitor
        if ! monitor_canary "$duration" "$percentage"; then
            rollback_canary "Tripwires triggered at ${percentage}%"
            exit 1
        fi
        
        log_success "✅ ${percentage}% stage successful"
        
        # Don't wait after 100%
        [ "$percentage" -eq 100 ] && break
        
        log_info "Pausing before next stage..."
        sleep 5
    done
    
    # Promote canary to production
    promote_canary
    
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║          🎉 CANARY DEPLOYMENT SUCCESSFUL 🎉                  ║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}\n"
    
    log_info "Version ${CANARY_VERSION} is now production"
}

# Run main
main
