#!/bin/bash
#
# ARK Development Tool
# Quick commands for development workflow
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

ARK_BASE_PATH="${ARK_BASE_PATH:-$(pwd)}"

print_header() {
    echo -e "\n${CYAN}===========================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}===========================================================${NC}\n"
}

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Development server management
dev_start() {
    print_header "Starting Development Servers"
    
    # Check if already running
    if pgrep -f "reasoning_api.py" > /dev/null; then
        print_info "Backend already running"
    else
        print_info "Starting backend..."
        cd "$ARK_BASE_PATH"
        source venv/bin/activate 2>/dev/null || true
        nohup python3 reasoning_api.py > logs/dev_backend.log 2>&1 &
        echo $! > /tmp/ark_backend.pid
        print_success "Backend started (PID: $(cat /tmp/ark_backend.pid))"
    fi
    
    # Start frontend if exists
    if [ -d "$ARK_BASE_PATH/frontend" ]; then
        if pgrep -f "vite" > /dev/null; then
            print_info "Frontend already running"
        else
            print_info "Starting frontend..."
            cd "$ARK_BASE_PATH/frontend"
            nohup npm run dev > ../logs/dev_frontend.log 2>&1 &
            echo $! > /tmp/ark_frontend.pid
            print_success "Frontend started (PID: $(cat /tmp/ark_frontend.pid))"
        fi
    fi
    
    sleep 2
    dev_status
}

dev_stop() {
    print_header "Stopping Development Servers"
    
    # Stop backend
    if [ -f /tmp/ark_backend.pid ]; then
        pid=$(cat /tmp/ark_backend.pid)
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            print_success "Backend stopped (PID: $pid)"
        fi
        rm -f /tmp/ark_backend.pid
    fi
    
    # Stop frontend
    if [ -f /tmp/ark_frontend.pid ]; then
        pid=$(cat /tmp/ark_frontend.pid)
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            print_success "Frontend stopped (PID: $pid)"
        fi
        rm -f /tmp/ark_frontend.pid
    fi
    
    # Fallback: kill by name
    pkill -f "reasoning_api.py" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
}

dev_restart() {
    print_header "Restarting Development Servers"
    dev_stop
    sleep 1
    dev_start
}

dev_status() {
    print_header "Development Server Status"
    
    # Backend status
    if pgrep -f "reasoning_api.py" > /dev/null; then
        pid=$(pgrep -f "reasoning_api.py")
        print_success "Backend: Running (PID: $pid)"
        print_info "   URL: http://localhost:8101"
        print_info "   Logs: tail -f logs/dev_backend.log"
    else
        print_error "Backend: Not running"
    fi
    
    # Frontend status
    if pgrep -f "vite" > /dev/null; then
        pid=$(pgrep -f "vite")
        print_success "Frontend: Running (PID: $pid)"
        print_info "   URL: http://localhost:5173"
        print_info "   Logs: tail -f logs/dev_frontend.log"
    else
        print_info "Frontend: Not running"
    fi
    
    # Redis status
    if pgrep redis-server > /dev/null; then
        print_success "Redis: Running"
    else
        print_info "Redis: Not running"
    fi
}

dev_logs() {
    local service="${1:-backend}"
    
    case "$service" in
        backend)
            tail -f "$ARK_BASE_PATH/logs/dev_backend.log"
            ;;
        frontend)
            tail -f "$ARK_BASE_PATH/logs/dev_frontend.log"
            ;;
        all)
            tail -f "$ARK_BASE_PATH/logs/dev_backend.log" "$ARK_BASE_PATH/logs/dev_frontend.log"
            ;;
        *)
            print_error "Unknown service: $service"
            echo "Available: backend, frontend, all"
            ;;
    esac
}

# Code quality checks
dev_lint() {
    print_header "Running Linters"
    
    cd "$ARK_BASE_PATH"
    
    # Python linting
    if command -v flake8 &> /dev/null; then
        print_info "Running flake8..."
        flake8 . --exclude=venv,deps,node_modules --max-line-length=120 || true
    fi
    
    if command -v pylint &> /dev/null; then
        print_info "Running pylint..."
        pylint *.py --disable=all --enable=E,F || true
    fi
    
    # JavaScript linting
    if [ -d "$ARK_BASE_PATH/frontend" ]; then
        cd "$ARK_BASE_PATH/frontend"
        if [ -f "package.json" ]; then
            print_info "Running ESLint..."
            npm run lint 2>/dev/null || true
        fi
    fi
}

dev_format() {
    print_header "Formatting Code"
    
    cd "$ARK_BASE_PATH"
    
    # Python formatting
    if command -v black &> /dev/null; then
        print_info "Running black..."
        black . --exclude="venv|deps|node_modules" || true
        print_success "Python code formatted"
    fi
    
    # JavaScript formatting
    if [ -d "$ARK_BASE_PATH/frontend" ]; then
        cd "$ARK_BASE_PATH/frontend"
        if command -v prettier &> /dev/null; then
            print_info "Running prettier..."
            prettier --write "src/**/*.{js,jsx,ts,tsx,json,css}" 2>/dev/null || true
            print_success "JavaScript code formatted"
        fi
    fi
}

dev_test() {
    print_header "Running Tests"
    
    cd "$ARK_BASE_PATH"
    
    # Python tests
    if [ -d "tests" ]; then
        print_info "Running pytest..."
        source venv/bin/activate 2>/dev/null || true
        pytest tests/ -v || true
    fi
    
    # JavaScript tests
    if [ -d "$ARK_BASE_PATH/frontend" ]; then
        cd "$ARK_BASE_PATH/frontend"
        if [ -f "package.json" ]; then
            print_info "Running frontend tests..."
            npm test 2>/dev/null || true
        fi
    fi
}

dev_clean() {
    print_header "Cleaning Development Files"
    
    cd "$ARK_BASE_PATH"
    
    # Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    print_success "Python cache cleaned"
    
    # Node modules (optional - prompts user)
    if [ -d "$ARK_BASE_PATH/frontend/node_modules" ]; then
        read -p "Remove node_modules? (y/n): " response
        if [ "$response" = "y" ]; then
            rm -rf "$ARK_BASE_PATH/frontend/node_modules"
            print_success "node_modules removed"
        fi
    fi
    
    # Log files (keep last 7 days)
    find "$ARK_BASE_PATH/logs" -name "*.log" -mtime +7 -delete 2>/dev/null || true
    print_success "Old log files cleaned"
}

dev_build() {
    print_header "Building Production Assets"
    
    # Build frontend
    if [ -d "$ARK_BASE_PATH/frontend" ]; then
        cd "$ARK_BASE_PATH/frontend"
        print_info "Building frontend..."
        npm run build
        print_success "Frontend built to dist/"
    fi
}

dev_shell() {
    print_header "Opening Python Shell"
    
    cd "$ARK_BASE_PATH"
    source venv/bin/activate 2>/dev/null || true
    
    print_info "ARK Python Shell"
    print_info "Available imports:"
    print_info "  from agents.base_agent import BaseAgent"
    print_info "  from reasoning.memory_engine import MemoryEngine"
    print_info "  from dashboard_data_sources import *"
    echo ""
    
    python3 -i << 'EOF'
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("ARK development environment loaded")
print("Type 'help()' for Python help or 'exit()' to quit")
EOF
}

# Quick database access
dev_db() {
    local db="${1:-ark}"
    
    if [ "$db" = "ark" ]; then
        sqlite3 "$ARK_BASE_PATH/data/ark.db"
    elif [ "$db" = "reasoning" ]; then
        sqlite3 "$ARK_BASE_PATH/data/reasoning_logs.db"
    else
        print_error "Unknown database: $db"
        echo "Available: ark, reasoning"
    fi
}

# Git workflow helpers
dev_commit() {
    print_header "Git Commit Helper"
    
    cd "$ARK_BASE_PATH"
    
    # Show status
    git status
    
    echo ""
    read -p "Commit message: " message
    
    if [ -z "$message" ]; then
        print_error "Commit message required"
        exit 1
    fi
    
    git add .
    git commit -m "$message"
    print_success "Committed: $message"
    
    read -p "Push to remote? (y/n): " push
    if [ "$push" = "y" ]; then
        git push
        print_success "Pushed to remote"
    fi
}

# Usage
show_usage() {
    cat << EOF
ARK Development Tool - Quick commands for development workflow

Usage: $0 <command>

Server Management:
  start       - Start development servers (backend + frontend)
  stop        - Stop development servers
  restart     - Restart development servers
  status      - Show server status
  logs [svc]  - Tail logs (backend|frontend|all)

Code Quality:
  lint        - Run linters (flake8, pylint, eslint)
  format      - Format code (black, prettier)
  test        - Run tests (pytest, jest)
  clean       - Clean cache and old files

Build & Deploy:
  build       - Build production assets

Development:
  shell       - Open Python REPL with ARK imports
  db [name]   - Open database shell (ark|reasoning)
  commit      - Interactive git commit helper

Examples:
  $0 start           # Start all dev servers
  $0 logs backend    # Watch backend logs
  $0 lint            # Run all linters
  $0 shell           # Open Python shell

EOF
}

# Main command router
case "${1:-help}" in
    start)      dev_start ;;
    stop)       dev_stop ;;
    restart)    dev_restart ;;
    status)     dev_status ;;
    logs)       dev_logs "$2" ;;
    lint)       dev_lint ;;
    format)     dev_format ;;
    test)       dev_test ;;
    clean)      dev_clean ;;
    build)      dev_build ;;
    shell)      dev_shell ;;
    db)         dev_db "$2" ;;
    commit)     dev_commit ;;
    help|*)     show_usage ;;
esac
