#!/bin/bash
#
# ARK System Stop Script (REQ_INFRA_04, REQ_REC_01)
# Gracefully stops all ARK services with optional panic mode
#
# Usage:
#   ./arkstop.sh          - Graceful shutdown (SIGTERM)
#   ./arkstop.sh --force  - Panic mode (immediate SIGKILL)
#

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Mode: graceful or panic
MODE="${1:-graceful}"
FORCE_MODE=false

if [[ "$MODE" == "--force" ]] || [[ "$MODE" == "-f" ]] || [[ "$MODE" == "panic" ]]; then
    FORCE_MODE=true
fi

print_header() {
    if [ "$FORCE_MODE" = true ]; then
        echo -e "\n${RED}╔════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║${NC}  🚨 ${RED}ARK - PANIC SHUTDOWN MODE${NC}                               ${RED}║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════════════════╝${NC}\n"
        echo -e "${YELLOW}⚠️  WARNING: Immediate termination without cleanup${NC}\n"
    else
        echo -e "\n${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${CYAN}║${NC}  🛑 ${BLUE}ARK - Graceful Shutdown${NC}                                ${CYAN}║${NC}"
        echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}\n"
    fi
}

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Stop backend
stop_backend() {
    if [ "$FORCE_MODE" = true ]; then
        print_info "🚨 PANIC: Force-killing ARK Backend..."
        # Immediate SIGKILL
        pkill -9 -f "reasoning_api.py" 2>/dev/null && print_success "Backend killed (SIGKILL)" || print_info "Backend not running"
        rm -f /tmp/ark_backend.pid 2>/dev/null
    else
        print_info "Stopping ARK Backend (graceful)..."
        
        if [ -f /tmp/ark_backend.pid ]; then
            pid=$(cat /tmp/ark_backend.pid)
            if kill -0 $pid 2>/dev/null; then
                # Send SIGTERM for graceful shutdown
                kill $pid
                sleep 3  # Wait for graceful shutdown
                if ! kill -0 $pid 2>/dev/null; then
                    print_success "Backend stopped gracefully (PID: $pid)"
                else
                    # Fallback to SIGKILL if graceful failed
                    kill -9 $pid 2>/dev/null
                    print_success "Backend force-stopped (PID: $pid)"
                fi
            else
                print_info "Backend not running (stale PID file)"
            fi
            rm -f /tmp/ark_backend.pid
        else
            # Try killing by process name
            if pkill -15 -f "reasoning_api.py" 2>/dev/null; then
                sleep 2
                print_success "Backend stopped"
            else
                print_info "Backend not running"
            fi
        fi
    fi
}

# Stop frontend
stop_frontend() {
    if [ "$FORCE_MODE" = true ]; then
        print_info "🚨 PANIC: Force-killing ARK Frontend..."
        # Immediate SIGKILL
        pkill -9 -f "vite" 2>/dev/null && print_success "Frontend killed (SIGKILL)" || print_info "Frontend not running"
        rm -f /tmp/ark_frontend.pid 2>/dev/null
    else
        print_info "Stopping ARK Frontend (graceful)..."
        
        if [ -f /tmp/ark_frontend.pid ]; then
            pid=$(cat /tmp/ark_frontend.pid)
            if kill -0 $pid 2>/dev/null; then
                kill $pid
                sleep 2
                if ! kill -0 $pid 2>/dev/null; then
                    print_success "Frontend stopped gracefully (PID: $pid)"
                else
                    kill -9 $pid 2>/dev/null
                    print_success "Frontend force-stopped (PID: $pid)"
                fi
            else
                print_info "Frontend not running (stale PID file)"
            fi
            rm -f /tmp/ark_frontend.pid
        else
            # Try killing by process name
            if pkill -15 -f "vite" 2>/dev/null; then
                sleep 1
                print_success "Frontend stopped"
            else
                print_info "Frontend not running"
            fi
        fi
    fi
}

# Stop Redis (optional)
stop_redis() {
    if [ "$FORCE_MODE" = true ]; then
        # Skip prompt in panic mode
        if command -v redis-cli &> /dev/null && redis-cli ping &> /dev/null 2>&1; then
            print_info "Leaving Redis running (not ARK-managed)"
        fi
    else
        read -p "$(echo -e ${YELLOW}⚠️  Stop Redis? [y/N]: ${NC})" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if command -v redis-cli &> /dev/null; then
                if redis-cli ping &> /dev/null; then
                    redis-cli shutdown 2>/dev/null
                    print_success "Redis stopped"
                else
                    print_info "Redis not running"
                fi
            else
                print_info "Redis not installed"
            fi
        fi
    fi
}

# Release system lock
release_lock() {
    if [ -f "shared/lockfile.py" ] && command -v python3 &> /dev/null; then
        python3 shared/lockfile.py --release --component system 2>/dev/null
    fi
    
    # Clean up any remaining lockfiles
    rm -f /tmp/ark.lock /tmp/ark_*.lock 2>/dev/null
}

# Main stop sequence
main() {
    print_header
    
    stop_backend
    stop_frontend
    
    echo ""
    
    if [ "$FORCE_MODE" != true ]; then
        stop_redis
    fi
    
    # Release system lock
    release_lock
    
    echo ""
    
    if [ "$FORCE_MODE" = true ]; then
        print_success "🚨 PANIC SHUTDOWN COMPLETE"
        echo -e "${YELLOW}⚠️  State may be inconsistent - check logs before restarting${NC}"
    else
        print_success "ARK services stopped gracefully"
    fi
    
    echo ""
    
    echo -e "${CYAN}To restart ARK:${NC}"
    echo -e "  ${GREEN}./arkstart.sh${NC}"
    echo ""
    
    if [ "$FORCE_MODE" = true ]; then
        echo -e "${CYAN}For graceful shutdown next time:${NC}"
        echo -e "  ${GREEN}./arkstop.sh${NC}  (without --force)"
        echo ""
    fi
}

# Run main
main
