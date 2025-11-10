#!/bin/bash
#
# ARK Production Startup Script
#
# Starts all required services in correct order:
# 1. Validates production configuration
# 2. Starts metrics server
# 3. Starts Watchdog monitoring
# 4. Starts agent processes
# 5. Runs health checks
# 6. Executes synthetic validation loop
#
# Usage:
#   ./start_production.sh [--skip-validation] [--canary]
#
# Author: ARK System
# Created: 2025-11-10

set -euo pipefail

# === CONFIGURATION ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBAPP_DIR="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="/var/log/ark"
PIDS_DIR="/var/run/ark"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
SKIP_VALIDATION=false
CANARY_MODE=false

for arg in "$@"; do
    case $arg in
        --skip-validation)
            SKIP_VALIDATION=true
            ;;
        --canary)
            CANARY_MODE=true
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

check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Check Redis
    if ! command -v redis-cli &> /dev/null; then
        log_warning "redis-cli not found - will check Redis programmatically"
    fi
    
    # Check required Python packages
    python3 -c "import redis" 2>/dev/null || missing_deps+=("python-redis")
    python3 -c "import aiohttp" 2>/dev/null || missing_deps+=("python-aiohttp")
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_error "Install with: pip install redis aiohttp"
        exit 1
    fi
    
    log_success "All dependencies satisfied"
}

create_directories() {
    log_info "Creating required directories..."
    
    sudo mkdir -p "$LOGS_DIR" "$PIDS_DIR" /var/lib/ark /var/backups/ark
    sudo chown -R "$USER:$USER" "$LOGS_DIR" "$PIDS_DIR" /var/lib/ark /var/backups/ark
    
    log_success "Directories created"
}

load_environment() {
    log_info "Loading production environment..."
    
    if [ ! -f "$WEBAPP_DIR/.env.production" ]; then
        log_error "Production environment file not found: $WEBAPP_DIR/.env.production"
        exit 1
    fi
    
    # Source environment
    set -a
    source "$WEBAPP_DIR/.env.production"
    set +a
    
    # Validate required variables
    local required_vars=(
        "ARK_ENV"
        "ARK_STATE_DB"
        "REDIS_URL"
        "METRICS_PORT"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            log_error "Required environment variable not set: $var"
            exit 1
        fi
    done
    
    log_success "Environment loaded (ARK_ENV=$ARK_ENV)"
}

validate_configuration() {
    if [ "$SKIP_VALIDATION" = true ]; then
        log_warning "Skipping configuration validation (--skip-validation)"
        return 0
    fi
    
    log_info "Validating production configuration..."
    
    cd "$WEBAPP_DIR"
    python3 -m deployment.config_prod validate
    
    if [ $? -ne 0 ]; then
        log_error "Configuration validation failed"
        exit 1
    fi
    
    log_success "Configuration validated"
}

start_metrics_server() {
    log_info "Starting metrics server on port $METRICS_PORT..."
    
    cd "$WEBAPP_DIR"
    
    # Start metrics server in background
    nohup python3 -m monitoring.metrics_server \
        > "$LOGS_DIR/metrics_server.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PIDS_DIR/metrics_server.pid"
    
    # Wait for startup
    sleep 2
    
    # Check if running
    if ! kill -0 $pid 2>/dev/null; then
        log_error "Metrics server failed to start"
        cat "$LOGS_DIR/metrics_server.log"
        exit 1
    fi
    
    # Health check
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "http://localhost:$METRICS_PORT/healthz" > /dev/null 2>&1; then
            log_success "Metrics server started (PID: $pid)"
            return 0
        fi
        
        log_info "Waiting for metrics server... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_error "Metrics server health check timeout"
    exit 1
}

start_watchdog() {
    log_info "Starting Watchdog monitoring..."
    
    cd "$WEBAPP_DIR"
    
    # Start Watchdog in background
    nohup python3 -c "
import asyncio
import logging
from monitoring.watchdog import Watchdog

logging.basicConfig(level=logging.INFO)

async def main():
    watchdog = Watchdog()
    await watchdog.start()

asyncio.run(main())
" > "$LOGS_DIR/watchdog.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PIDS_DIR/watchdog.pid"
    
    sleep 1
    
    if ! kill -0 $pid 2>/dev/null; then
        log_error "Watchdog failed to start"
        cat "$LOGS_DIR/watchdog.log"
        exit 1
    fi
    
    log_success "Watchdog started (PID: $pid)"
}

run_health_checks() {
    log_info "Running pre-flight health checks..."
    
    # Check metrics server
    if ! curl -sf "http://localhost:$METRICS_PORT/healthz" > /dev/null; then
        log_error "Metrics server health check failed"
        return 1
    fi
    
    # Check metrics readiness
    if ! curl -sf "http://localhost:$METRICS_PORT/readyz" > /dev/null; then
        log_warning "Metrics server not ready yet"
    fi
    
    # Check SLOs
    local slo_status=$(curl -sf "http://localhost:$METRICS_PORT/slos")
    log_info "Initial SLO status: $slo_status"
    
    log_success "Health checks passed"
}

run_synthetic_validation() {
    log_info "Running synthetic validation loop (300s)..."
    
    cd "$WEBAPP_DIR"
    
    # Run validation loop
    python3 -m deployment.run_synthetic_loop \
        --duration 300 \
        --redis-url "$REDIS_URL" \
        --api-url "http://localhost:8000"
    
    if [ $? -eq 0 ]; then
        log_success "Synthetic validation PASSED"
        return 0
    else
        log_error "Synthetic validation FAILED"
        return 1
    fi
}

display_status() {
    log_info "=== ARK Production Status ==="
    echo
    
    # Metrics server
    if [ -f "$PIDS_DIR/metrics_server.pid" ]; then
        local pid=$(cat "$PIDS_DIR/metrics_server.pid")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Metrics Server (PID: $pid) - http://localhost:$METRICS_PORT"
        else
            echo -e "${RED}✗${NC} Metrics Server (not running)"
        fi
    fi
    
    # Watchdog
    if [ -f "$PIDS_DIR/watchdog.pid" ]; then
        local pid=$(cat "$PIDS_DIR/watchdog.pid")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Watchdog (PID: $pid)"
        else
            echo -e "${RED}✗${NC} Watchdog (not running)"
        fi
    fi
    
    echo
    echo "Logs:"
    echo "  Metrics: $LOGS_DIR/metrics_server.log"
    echo "  Watchdog: $LOGS_DIR/watchdog.log"
    echo
    echo "Endpoints:"
    echo "  Metrics: http://localhost:$METRICS_PORT/metrics"
    echo "  SLOs: http://localhost:$METRICS_PORT/slos"
    echo "  Health: http://localhost:$METRICS_PORT/healthz"
    echo
}

stop_services() {
    log_info "Stopping ARK services..."
    
    # Stop metrics server
    if [ -f "$PIDS_DIR/metrics_server.pid" ]; then
        local pid=$(cat "$PIDS_DIR/metrics_server.pid")
        if kill -0 $pid 2>/dev/null; then
            kill -TERM $pid
            log_success "Stopped metrics server (PID: $pid)"
        fi
        rm -f "$PIDS_DIR/metrics_server.pid"
    fi
    
    # Stop Watchdog
    if [ -f "$PIDS_DIR/watchdog.pid" ]; then
        local pid=$(cat "$PIDS_DIR/watchdog.pid")
        if kill -0 $pid 2>/dev/null; then
            kill -TERM $pid
            log_success "Stopped Watchdog (PID: $pid)"
        fi
        rm -f "$PIDS_DIR/watchdog.pid"
    fi
}

# === MAIN EXECUTION ===

main() {
    log_info "=== ARK Production Startup ==="
    echo
    
    # Trap exit to cleanup
    trap stop_services EXIT INT TERM
    
    # Pre-flight checks
    check_dependencies
    create_directories
    load_environment
    validate_configuration
    
    echo
    log_info "=== Starting Services ==="
    
    # Start infrastructure
    start_metrics_server
    start_watchdog
    
    echo
    log_info "=== Validation Phase ==="
    
    # Health checks
    run_health_checks
    
    # Synthetic validation
    if run_synthetic_validation; then
        echo
        log_success "=== Production startup complete ==="
        display_status
        
        if [ "$CANARY_MODE" = true ]; then
            log_info "Canary deployment mode - monitoring for 10 minutes..."
            log_info "Press Ctrl+C to stop"
            sleep 600
        else
            log_info "Press Ctrl+C to stop services"
            
            # Keep running
            while true; do
                sleep 60
                
                # Periodic health check
                if ! curl -sf "http://localhost:$METRICS_PORT/healthz" > /dev/null; then
                    log_error "Metrics server health check failed"
                    exit 1
                fi
            done
        fi
    else
        log_error "Synthetic validation failed - aborting startup"
        exit 1
    fi
}

# Run main function
main
