#!/bin/bash
#
# ARK System Stop Script
# Gracefully stops all ARK services
#

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "\n${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  🛑 ${BLUE}ARK - Stopping Services${NC}                                  ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Stop backend
stop_backend() {
    print_info "Stopping ARK Backend..."
    
    if [ -f /tmp/ark_backend.pid ]; then
        pid=$(cat /tmp/ark_backend.pid)
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            sleep 2
            if ! kill -0 $pid 2>/dev/null; then
                print_success "Backend stopped (PID: $pid)"
            else
                kill -9 $pid 2>/dev/null
                print_success "Backend force-stopped (PID: $pid)"
            fi
        else
            print_info "Backend not running (stale PID file)"
        fi
        rm -f /tmp/ark_backend.pid
    else
        # Try killing by process name
        if pkill -f "reasoning_api.py" 2>/dev/null; then
            print_success "Backend stopped"
        else
            print_info "Backend not running"
        fi
    fi
}

# Stop frontend
stop_frontend() {
    print_info "Stopping ARK Frontend..."
    
    if [ -f /tmp/ark_frontend.pid ]; then
        pid=$(cat /tmp/ark_frontend.pid)
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            sleep 2
            if ! kill -0 $pid 2>/dev/null; then
                print_success "Frontend stopped (PID: $pid)"
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
        if pkill -f "vite" 2>/dev/null; then
            print_success "Frontend stopped"
        else
            print_info "Frontend not running"
        fi
    fi
}

# Stop Redis (optional)
stop_redis() {
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
}

# Main stop sequence
main() {
    print_header
    
    stop_backend
    stop_frontend
    
    echo ""
    stop_redis
    
    echo ""
    print_success "ARK services stopped"
    echo ""
    
    echo -e "${CYAN}To restart ARK:${NC}"
    echo -e "  ${GREEN}./arkstart.sh${NC}"
    echo ""
}

# Run main
main
