#!/usr/bin/env bash
#
# ARK Rollback Orchestration Script
#
# Provides simple CLI for triggering automated rollback with comprehensive
# logging and status reporting.
#
# Usage:
#   ./deployment/rollback.sh [--reason REASON] [--snapshot SNAPSHOT_ID] [--no-health-check]
#
# Examples:
#   ./deployment/rollback.sh --reason "Canary tripwire triggered"
#   ./deployment/rollback.sh --snapshot "20240110_153000"
#   ./deployment/rollback.sh --no-health-check --reason "Emergency"

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Logging
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/rollback_$(date +%Y%m%d_%H%M%S).log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Log function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" | tee -a "$LOG_FILE" >&2
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $*" | tee -a "$LOG_FILE"
}

# Banner
log "=========================================="
log "    ARK Rollback Automation"
log "=========================================="
log ""

# Parse arguments
REASON="Manual rollback via script"
SNAPSHOT_ID=""
NO_HEALTH_CHECK=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --reason)
            REASON="$2"
            shift 2
            ;;
        --snapshot)
            SNAPSHOT_ID="$2"
            shift 2
            ;;
        --no-health-check)
            NO_HEALTH_CHECK="--no-health-check"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --reason REASON           Reason for rollback (required for audit)"
            echo "  --snapshot SNAPSHOT_ID    Specific DB snapshot to restore (default: latest)"
            echo "  --no-health-check         Skip health check validation (DANGEROUS)"
            echo "  --help, -h                Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --reason \"Canary tripwire triggered\""
            echo "  $0 --snapshot \"20240110_153000\" --reason \"Manual rollback\""
            echo "  $0 --no-health-check --reason \"Emergency\""
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Display rollback configuration
log_info "Rollback Configuration:"
log_info "  Reason: $REASON"
log_info "  Snapshot: ${SNAPSHOT_ID:-latest stable}"
log_info "  Health Check: ${NO_HEALTH_CHECK:-enabled}"
log_info "  Log File: $LOG_FILE"
log ""

# Confirmation prompt
log_warn "⚠️  This will rollback the production deployment!"
log_warn "⚠️  Current canary will be stopped"
log_warn "⚠️  Database will be restored from snapshot"
log_warn "⚠️  Docker container will use stable image"
log ""
read -p "Continue with rollback? (yes/no): " -r CONFIRM
echo ""

if [[ ! "$CONFIRM" =~ ^[Yy][Ee][Ss]$ ]]; then
    log "Rollback cancelled by user"
    exit 0
fi

log "🔄 Starting rollback process..."
log ""

# Check prerequisites
log_info "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "python3 not found"
    exit 1
fi
log "  ✓ Python 3 available"

# Check Docker
if ! command -v docker &> /dev/null; then
    log_error "docker not found"
    exit 1
fi
log "  ✓ Docker available"

# Check docker-compose
if ! command -v docker-compose &> /dev/null; then
    log_error "docker-compose not found"
    exit 1
fi
log "  ✓ docker-compose available"

# Check rollback script
ROLLBACK_SCRIPT="$SCRIPT_DIR/rollback_automation.py"
if [[ ! -f "$ROLLBACK_SCRIPT" ]]; then
    log_error "Rollback script not found: $ROLLBACK_SCRIPT"
    exit 1
fi
log "  ✓ Rollback automation script available"

log ""
log_info "Prerequisites check passed"
log ""

# Build Python command
PYTHON_CMD="python3 $ROLLBACK_SCRIPT --reason \"$REASON\""

if [[ -n "$SNAPSHOT_ID" ]]; then
    PYTHON_CMD="$PYTHON_CMD --snapshot \"$SNAPSHOT_ID\""
fi

if [[ -n "$NO_HEALTH_CHECK" ]]; then
    PYTHON_CMD="$PYTHON_CMD $NO_HEALTH_CHECK"
fi

# Execute rollback
log "Executing rollback automation..."
log "Command: $PYTHON_CMD"
log ""

START_TIME=$(date +%s)

if eval "$PYTHON_CMD"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    log ""
    log "=========================================="
    log "✅ Rollback completed successfully!"
    log "=========================================="
    log ""
    log_info "Duration: ${DURATION}s"
    log_info "Log file: $LOG_FILE"
    log ""
    log_info "Next steps:"
    log_info "  1. Monitor system metrics for stability"
    log_info "  2. Check logs: tail -f $LOG_DIR/rollback.log"
    log_info "  3. Verify SLOs: curl http://localhost:9090/slos"
    log_info "  4. Review rollback history: cat $LOG_DIR/rollback_history.json"
    log ""
    
    exit 0
else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    log ""
    log "=========================================="
    log_error "❌ Rollback FAILED"
    log "=========================================="
    log ""
    log_error "Duration: ${DURATION}s"
    log_error "Log file: $LOG_FILE"
    log ""
    log_error "Action required:"
    log_error "  1. Review error logs: tail -100 $LOG_FILE"
    log_error "  2. Check container status: docker ps -a"
    log_error "  3. Inspect rollback history: cat $LOG_DIR/rollback_history.json"
    log_error "  4. Manual intervention may be required!"
    log ""
    
    exit 1
fi
