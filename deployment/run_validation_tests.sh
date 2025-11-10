#!/usr/bin/env bash
#
# ARK Post-Deploy Validation Test Runner
#
# Runs comprehensive validation tests after deployment to verify:
# 1. Ethics enforcement via Graveyard
# 2. Agent isolation via Watchdog
# 3. Heartbeat monitoring
# 4. State continuity and version control
#
# Usage:
#   ./deployment/run_validation_tests.sh [--category CATEGORY] [--verbose]
#
# Categories:
#   all              Run all validation tests (default)
#   ethics           Run ethics enforcement tests only
#   isolation        Run agent isolation tests only
#   heartbeat        Run heartbeat monitoring tests only
#   state            Run state continuity tests only
#   integration      Run integration tests only
#
# Examples:
#   ./deployment/run_validation_tests.sh
#   ./deployment/run_validation_tests.sh --category ethics --verbose
#   ./deployment/run_validation_tests.sh --verbose

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
LOG_FILE="$LOG_DIR/validation_$(date +%Y%m%d_%H%M%S).log"

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
log "    ARK Post-Deploy Validation Tests"
log "=========================================="
log ""

# Parse arguments
CATEGORY="all"
VERBOSE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --category)
            CATEGORY="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE="-v"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --category CATEGORY   Test category to run (default: all)"
            echo "                        Categories: all, ethics, isolation, heartbeat, state, integration"
            echo "  --verbose, -v         Verbose output"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 --category ethics --verbose"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Display configuration
log_info "Configuration:"
log_info "  Category: $CATEGORY"
log_info "  Verbose: ${VERBOSE:-disabled}"
log_info "  Log File: $LOG_FILE"
log ""

# Check prerequisites
log_info "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "python3 not found"
    exit 1
fi
log "  ✓ Python 3 available"

# Check pytest
if ! python3 -c "import pytest" 2>/dev/null; then
    log_warn "pytest not installed, installing..."
    pip3 install pytest
fi
log "  ✓ pytest available"

# Check test file
TEST_FILE="$PROJECT_ROOT/tests/test_post_deploy_validation.py"
if [[ ! -f "$TEST_FILE" ]]; then
    log_error "Test file not found: $TEST_FILE"
    exit 1
fi
log "  ✓ Test file available"

log ""
log_info "Prerequisites check passed"
log ""

# Set environment variables for tests
export ARK_API_BASE_URL="${ARK_API_BASE_URL:-http://localhost:8000}"
export ARK_STATE_DB="${ARK_STATE_DB:-/var/lib/ark/ark_state.db}"
export ARK_REDIS_HOST="${ARK_REDIS_HOST:-localhost}"
export ARK_REDIS_PORT="${ARK_REDIS_PORT:-6379}"

log_info "Test Environment:"
log_info "  ARK_API_BASE_URL: $ARK_API_BASE_URL"
log_info "  ARK_STATE_DB: $ARK_STATE_DB"
log_info "  ARK_REDIS_HOST: $ARK_REDIS_HOST"
log_info "  ARK_REDIS_PORT: $ARK_REDIS_PORT"
log ""

# Build pytest command based on category
PYTEST_ARGS=""

case "$CATEGORY" in
    all)
        log "Running all validation tests..."
        PYTEST_ARGS="$TEST_FILE"
        ;;
    ethics)
        log "Running ethics enforcement tests..."
        PYTEST_ARGS="$TEST_FILE::TestEthicsEnforcement"
        ;;
    isolation)
        log "Running agent isolation tests..."
        PYTEST_ARGS="$TEST_FILE::TestAgentIsolation"
        ;;
    heartbeat)
        log "Running heartbeat monitoring tests..."
        PYTEST_ARGS="$TEST_FILE::TestHeartbeatMonitoring"
        ;;
    state)
        log "Running state continuity tests..."
        PYTEST_ARGS="$TEST_FILE::TestStateContinuity"
        ;;
    integration)
        log "Running integration tests..."
        PYTEST_ARGS="$TEST_FILE::TestSystemIntegration"
        ;;
    *)
        log_error "Unknown category: $CATEGORY"
        echo "Valid categories: all, ethics, isolation, heartbeat, state, integration"
        exit 1
        ;;
esac

# Add verbose flag if requested
if [[ -n "$VERBOSE" ]]; then
    PYTEST_ARGS="$PYTEST_ARGS $VERBOSE"
fi

# Add output options
PYTEST_ARGS="$PYTEST_ARGS --tb=short --color=yes"

# Run tests
log ""
log "Executing tests..."
log "Command: pytest $PYTEST_ARGS"
log ""

START_TIME=$(date +%s)

if python3 -m pytest $PYTEST_ARGS 2>&1 | tee -a "$LOG_FILE"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    log ""
    log "=========================================="
    log "✅ Validation tests PASSED"
    log "=========================================="
    log ""
    log_info "Duration: ${DURATION}s"
    log_info "Category: $CATEGORY"
    log_info "Log file: $LOG_FILE"
    log ""
    log_info "Deployment validation successful!"
    log_info "System is ready for production traffic."
    log ""
    
    exit 0
else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    log ""
    log "=========================================="
    log_error "❌ Validation tests FAILED"
    log "=========================================="
    log ""
    log_error "Duration: ${DURATION}s"
    log_error "Category: $CATEGORY"
    log_error "Log file: $LOG_FILE"
    log ""
    log_error "Action required:"
    log_error "  1. Review test failures above"
    log_error "  2. Check system logs: tail -f $PROJECT_ROOT/logs/*.log"
    log_error "  3. Verify service health: curl http://localhost:8000/healthz"
    log_error "  4. Check metrics: curl http://localhost:9090/metrics"
    log_error "  5. Consider rollback if issues persist"
    log ""
    log_error "DO NOT proceed to production until all tests pass!"
    log ""
    
    exit 1
fi
