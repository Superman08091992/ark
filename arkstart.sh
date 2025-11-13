#!/bin/bash
#
# ARK System Startup Script
# Starts all ARK services and performs health check
#

set -e

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
    echo -e "${CYAN}║${NC}  🌌 ${BLUE}ARK - Autonomous Reactive Kernel${NC}                         ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Check if running in virtual environment
check_venv() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_warning "Virtual environment not activated"
        if [ -d "venv" ]; then
            print_info "Activating venv..."
            source venv/bin/activate
        else
            print_error "Virtual environment not found. Run: python3 -m venv venv"
            exit 1
        fi
    fi
    print_success "Virtual environment active: $VIRTUAL_ENV"
}

# Check Redis
check_redis() {
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            print_success "Redis is running"
            return 0
        else
            print_warning "Redis not running - starting..."
            if command -v redis-server &> /dev/null; then
                redis-server --daemonize yes
                sleep 1
                if redis-cli ping &> /dev/null; then
                    print_success "Redis started"
                    return 0
                fi
            fi
            print_warning "Redis not available (optional for basic operation)"
        fi
    else
        print_warning "Redis not installed (optional for federation features)"
    fi
    return 1
}

# Start backend API
start_backend() {
    print_info "Starting ARK Backend (FastAPI)..."
    
    if pgrep -f "reasoning_api.py" > /dev/null; then
        print_warning "Backend already running"
        return 0
    fi
    
    cd "$ARK_BASE_PATH"
    nohup python3 reasoning_api.py > logs/backend.log 2>&1 &
    echo $! > /tmp/ark_backend.pid
    
    # Wait for startup
    sleep 3
    
    if pgrep -f "reasoning_api.py" > /dev/null; then
        print_success "Backend started (PID: $(cat /tmp/ark_backend.pid))"
        print_info "   API: http://localhost:8101"
        print_info "   Docs: http://localhost:8101/docs"
        return 0
    else
        print_error "Backend failed to start - check logs/backend.log"
        return 1
    fi
}

# Start frontend (if exists)
start_frontend() {
    if [ -d "$ARK_BASE_PATH/frontend" ]; then
        print_info "Starting ARK Frontend..."
        
        if pgrep -f "vite" > /dev/null; then
            print_warning "Frontend already running"
            return 0
        fi
        
        cd "$ARK_BASE_PATH/frontend"
        
        # Check if node_modules exists
        if [ ! -d "node_modules" ]; then
            print_info "Installing frontend dependencies..."
            npm install
        fi
        
        nohup npm run dev > ../logs/frontend.log 2>&1 &
        echo $! > /tmp/ark_frontend.pid
        
        sleep 3
        
        if pgrep -f "vite" > /dev/null; then
            print_success "Frontend started (PID: $(cat /tmp/ark_frontend.pid))"
            print_info "   URL: http://localhost:5173"
            return 0
        else
            print_warning "Frontend failed to start - check logs/frontend.log"
            return 1
        fi
    else
        print_info "Frontend not found - skipping"
        return 0
    fi
}

# Perform health check using tools
health_check() {
    print_info "Running system health check..."
    
    if [ -x "$ARK_BASE_PATH/ark-tools" ]; then
        "$ARK_BASE_PATH/ark-tools" health
    else
        print_warning "ark-tools not found - skipping health check"
        print_info "System status:"
        
        # Manual status check
        if pgrep -f "reasoning_api.py" > /dev/null; then
            print_success "  Backend: Running"
        else
            print_error "  Backend: Not running"
        fi
        
        if redis-cli ping &> /dev/null; then
            print_success "  Redis: Running"
        else
            print_warning "  Redis: Not running"
        fi
    fi
}

# Pre-flight checks (REQ_INFRA_02, REQ_INFRA_03)
preflight_checks() {
    print_info "Running pre-flight checks..."
    
    # Port availability check
    if command -v python3 &> /dev/null; then
        if [ -f "$ARK_BASE_PATH/shared/port_checker.py" ]; then
            if ! python3 "$ARK_BASE_PATH/shared/port_checker.py" --preflight --quiet; then
                print_error "Port conflicts detected. Run: python3 shared/port_checker.py --preflight"
                exit 1
            fi
            print_success "All ports available"
        fi
    fi
    
    # Acquire system lock
    if [ -f "$ARK_BASE_PATH/shared/lockfile.py" ]; then
        if ! python3 "$ARK_BASE_PATH/shared/lockfile.py" --acquire --component system; then
            print_error "Another ARK instance is running. Use --force to terminate or run ./arkstop.sh"
            exit 1
        fi
    fi
}

# Cleanup on exit
cleanup() {
    if [ -f "$ARK_BASE_PATH/shared/lockfile.py" ]; then
        python3 "$ARK_BASE_PATH/shared/lockfile.py" --release --component system 2>/dev/null
    fi
}

trap cleanup EXIT

# Main startup sequence
main() {
    print_header
    
    echo -e "${BLUE}Starting ARK System...${NC}\n"
    
    # Create logs directory
    mkdir -p "$ARK_BASE_PATH/logs"
    
    # Pre-flight checks (locking, ports)
    preflight_checks
    
    # Check environment
    check_venv
    
    # Check/start Redis
    check_redis
    
    # Start services
    start_backend
    start_frontend
    
    # Health check
    echo ""
    health_check
    
    # Final status
    echo ""
    print_header
    echo -e "${GREEN}✨ ARK System Started Successfully! ✨${NC}\n"
    
    echo -e "${CYAN}Available Commands:${NC}"
    echo -e "  ${GREEN}./arkstop.sh${NC}      - Stop all services"
    echo -e "  ${GREEN}./arkstatus.sh${NC}    - Check system status"
    echo -e "  ${GREEN}./ark-tools help${NC}  - Show tools menu"
    echo -e "  ${GREEN}./ark-tools monitor${NC} - Real-time monitoring"
    echo ""
    
    echo -e "${CYAN}Access URLs:${NC}"
    echo -e "  ${BLUE}Backend API:${NC}      http://localhost:8101"
    echo -e "  ${BLUE}API Docs:${NC}         http://localhost:8101/docs"
    echo -e "  ${BLUE}Dashboard:${NC}        http://localhost:8101/dashboard-demo.html"
    if [ -d "$ARK_BASE_PATH/frontend" ]; then
        echo -e "  ${BLUE}Frontend:${NC}         http://localhost:5173"
    fi
    echo ""
    
    echo -e "${CYAN}Logs:${NC}"
    echo -e "  ${BLUE}tail -f logs/backend.log${NC}   - Backend logs"
    if [ -d "$ARK_BASE_PATH/frontend" ]; then
        echo -e "  ${BLUE}tail -f logs/frontend.log${NC}  - Frontend logs"
    fi
    echo ""
}

# Run main
main
