#!/bin/bash
#
# ARK System Status Script
# Shows comprehensive system status using ark-tools
#

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

ARK_BASE_PATH="${ARK_BASE_PATH:-$(cd "$(dirname "$0")" && pwd)}"

print_header() {
    echo -e "\n${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  📊 ${BLUE}ARK - System Status${NC}                                       ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Check services
check_services() {
    echo -e "${CYAN}Services:${NC}"
    
    # Backend
    if pgrep -f "reasoning_api.py" > /dev/null; then
        pid=$(pgrep -f "reasoning_api.py")
        print_success "Backend (reasoning_api.py) - PID: $pid"
        echo -e "         ${BLUE}http://localhost:8101${NC}"
    else
        print_error "Backend (reasoning_api.py) - Not running"
    fi
    
    # Frontend
    if pgrep -f "vite" > /dev/null; then
        pid=$(pgrep -f "vite")
        print_success "Frontend (vite) - PID: $pid"
        echo -e "         ${BLUE}http://localhost:5173${NC}"
    else
        print_info "Frontend - Not running"
    fi
    
    # Redis
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null 2>&1; then
            pid=$(pgrep redis-server)
            print_success "Redis - PID: $pid"
        else
            print_warning "Redis - Not running"
        fi
    else
        print_info "Redis - Not installed"
    fi
    
    echo ""
}

# Check databases
check_databases() {
    echo -e "${CYAN}Databases:${NC}"
    
    if [ -f "$ARK_BASE_PATH/data/ark.db" ]; then
        size=$(du -h "$ARK_BASE_PATH/data/ark.db" | cut -f1)
        print_success "ark.db ($size)"
    else
        print_error "ark.db - Not found"
    fi
    
    if [ -f "$ARK_BASE_PATH/data/reasoning_logs.db" ]; then
        size=$(du -h "$ARK_BASE_PATH/data/reasoning_logs.db" | cut -f1)
        print_success "reasoning_logs.db ($size)"
    else
        print_error "reasoning_logs.db - Not found"
    fi
    
    echo ""
}

# Check disk space
check_disk() {
    echo -e "${CYAN}Disk Space:${NC}"
    df -h "$ARK_BASE_PATH" | tail -1 | awk '{
        used=$3; total=$2; percent=$5;
        printf "  Used: %s / %s (%s)\n", used, total, percent
    }'
    echo ""
}

# Show recent logs
show_logs() {
    echo -e "${CYAN}Recent Logs (last 5 lines):${NC}"
    
    if [ -f "$ARK_BASE_PATH/logs/backend.log" ]; then
        echo -e "${BLUE}Backend:${NC}"
        tail -5 "$ARK_BASE_PATH/logs/backend.log" 2>/dev/null | sed 's/^/  /'
    fi
    
    if [ -f "$ARK_BASE_PATH/logs/frontend.log" ]; then
        echo -e "\n${BLUE}Frontend:${NC}"
        tail -5 "$ARK_BASE_PATH/logs/frontend.log" 2>/dev/null | sed 's/^/  /'
    fi
    
    echo ""
}

# Use ark-tools if available
use_tools() {
    if [ -x "$ARK_BASE_PATH/ark-tools" ]; then
        echo -e "${CYAN}Running comprehensive health check...${NC}\n"
        "$ARK_BASE_PATH/ark-tools" status
        return 0
    fi
    return 1
}

# Main status check
main() {
    print_header
    
    # Try using ark-tools first
    if use_tools; then
        echo ""
        echo -e "${CYAN}For detailed monitoring:${NC}"
        echo -e "  ${GREEN}./ark-tools monitor${NC}     - Real-time dashboard"
        echo -e "  ${GREEN}./ark-tools admin health${NC} - Detailed health check"
        echo -e "  ${GREEN}./ark-tools db stats ark${NC} - Database statistics"
        echo ""
    else
        # Fallback to manual checks
        check_services
        check_databases
        check_disk
        show_logs
        
        echo -e "${CYAN}Available Commands:${NC}"
        echo -e "  ${GREEN}./arkstart.sh${NC}      - Start services"
        echo -e "  ${GREEN}./arkstop.sh${NC}       - Stop services"
        echo -e "  ${GREEN}tail -f logs/backend.log${NC}  - Watch backend logs"
        echo ""
    fi
}

# Run main
main
