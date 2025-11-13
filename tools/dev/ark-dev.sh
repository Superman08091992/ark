#!/bin/bash
#
# ARK Development Tool
# Utilities for developers working on ARK
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

ARK_BASE_PATH="${ARK_BASE_PATH:-$(pwd)}"

print_header() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}\n"
}

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# ==================== ENVIRONMENT ====================

setup_dev_env() {
    print_header "🔧 Setting Up Development Environment"
    
    cd "$ARK_BASE_PATH"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        exit 1
    fi
    print_success "Python 3 found: $(python3 --version)"
    
    # Create/activate virtual environment
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Install/upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    # Install dependencies
    print_info "Installing dependencies..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt --quiet
        print_success "Production dependencies installed"
    fi
    
    if [ -f "requirements.dev.txt" ]; then
        pip install -r requirements.dev.txt --quiet
        print_success "Development dependencies installed"
    fi
    
    # Install development tools
    print_info "Installing development tools..."
    pip install --quiet \
        pytest pytest-cov pytest-asyncio \
        black flake8 mypy pylint \
        ipython ipdb
    print_success "Development tools installed"
    
    print_success "Development environment ready!"
    print_info "Activate with: source venv/bin/activate"
}

# ==================== CODE QUALITY ====================

run_linters() {
    print_header "🔍 Running Linters"
    
    cd "$ARK_BASE_PATH"
    source venv/bin/activate
    
    # Black (code formatter check)
    print_info "Running Black..."
    if black --check --diff . 2>/dev/null; then
        print_success "Black: Code is properly formatted"
    else
        print_warning "Black: Code formatting issues found"
        echo "  Run 'black .' to fix"
    fi
    
    # Flake8 (style guide enforcement)
    print_info "Running Flake8..."
    if flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics 2>/dev/null; then
        print_success "Flake8: No critical issues"
    else
        print_warning "Flake8: Issues found"
    fi
    
    # MyPy (type checking)
    print_info "Running MyPy..."
    if mypy --ignore-missing-imports reasoning_api.py 2>/dev/null; then
        print_success "MyPy: Type checking passed"
    else
        print_warning "MyPy: Type issues found"
    fi
}

format_code() {
    print_header "🎨 Formatting Code"
    
    cd "$ARK_BASE_PATH"
    source venv/bin/activate
    
    print_info "Running Black formatter..."
    black .
    
    print_success "Code formatted!"
}

# ==================== TESTING ====================

run_tests() {
    print_header "🧪 Running Tests"
    
    cd "$ARK_BASE_PATH"
    source venv/bin/activate
    
    local test_path="${1:-.}"
    
    print_info "Running pytest on: $test_path"
    
    pytest "$test_path" \
        --verbose \
        --cov=. \
        --cov-report=term-missing \
        --cov-report=html:htmlcov
    
    print_success "Tests complete!"
    print_info "Coverage report: htmlcov/index.html"
}

# ==================== DATABASE ====================

reset_databases() {
    print_header "🗄️  Resetting Databases"
    
    print_warning "This will DELETE all data in databases!"
    read -p "Continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "Cancelled"
        return
    fi
    
    cd "$ARK_BASE_PATH/data"
    
    # Backup existing databases
    if [ -f "ark.db" ]; then
        mv ark.db "ark.db.backup.$(date +%Y%m%d_%H%M%S)"
        print_info "Backed up ark.db"
    fi
    
    if [ -f "reasoning_logs.db" ]; then
        mv reasoning_logs.db "reasoning_logs.db.backup.$(date +%Y%m%d_%H%M%S)"
        print_info "Backed up reasoning_logs.db"
    fi
    
    # Initialize new databases
    cd "$ARK_BASE_PATH"
    source venv/bin/activate
    
    print_info "Initializing databases..."
    python3 -c "
from agents.base_agent import BaseAgent
from reasoning.memory_engine import MemoryEngine
print('Databases initialized')
"
    
    print_success "Databases reset!"
}

seed_test_data() {
    print_header "🌱 Seeding Test Data"
    
    cd "$ARK_BASE_PATH"
    source venv/bin/activate
    
    python3 << 'EOF'
import sqlite3
from datetime import datetime, timedelta
import random

# Seed ARK database
conn = sqlite3.connect('data/ark.db')
cursor = conn.cursor()

# Add sample code patterns
patterns = [
    ("authentication_flow", "async def login(user, pass)", "core"),
    ("error_handler", "try: ... except Exception", "trusted"),
    ("api_endpoint", "@app.post('/api/...)", "verified"),
]

for pattern_name, code_snippet, trust in patterns:
    cursor.execute("""
        INSERT OR IGNORE INTO code_patterns (pattern_name, code_snippet, trust_tier, usage_count)
        VALUES (?, ?, ?, ?)
    """, (pattern_name, code_snippet, trust, random.randint(5, 50)))

conn.commit()
conn.close()

print("✅ Test data seeded successfully")
EOF
    
    print_success "Test data added!"
}

# ==================== DEVELOPMENT SERVER ====================

start_dev() {
    print_header "🚀 Starting Development Servers"
    
    cd "$ARK_BASE_PATH"
    source venv/bin/activate
    
    # Start Redis
    if ! pgrep redis-server > /dev/null; then
        print_info "Starting Redis..."
        redis-server --daemonize yes --port 6379
        sleep 1
    fi
    print_success "Redis running"
    
    # Start backend in background
    print_info "Starting backend (port 8101)..."
    python3 reasoning_api.py &
    BACKEND_PID=$!
    sleep 3
    
    # Start frontend in background
    if [ -d "frontend" ]; then
        print_info "Starting frontend (port 4173)..."
        cd frontend
        npm run dev &
        FRONTEND_PID=$!
        cd ..
    fi
    
    print_success "Development servers started!"
    print_info "Backend:  http://localhost:8101"
    print_info "Frontend: http://localhost:4173"
    print_info "Dashboard: http://localhost:4173/dashboard-demo.html"
    
    echo ""
    print_warning "Press Ctrl+C to stop servers"
    
    # Wait for Ctrl+C
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
    wait
}

# ==================== LOGS ====================

tail_logs() {
    print_header "📋 Tailing Logs"
    
    cd "$ARK_BASE_PATH/logs"
    
    local log_file="${1:-reasoning_api.log}"
    
    if [ ! -f "$log_file" ]; then
        print_error "Log file not found: $log_file"
        exit 1
    fi
    
    print_info "Tailing: $log_file"
    tail -f "$log_file"
}

# ==================== DOCKER ====================

docker_build() {
    print_header "🐳 Building Docker Image"
    
    cd "$ARK_BASE_PATH"
    
    print_info "Building ARK Docker image..."
    docker build -t ark:dev .
    
    print_success "Docker image built: ark:dev"
}

docker_run() {
    print_header "🐳 Running Docker Container"
    
    cd "$ARK_BASE_PATH"
    
    print_info "Starting ARK container..."
    docker run -d \
        --name ark-dev \
        -p 8101:8101 \
        -p 8104:8104 \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/logs:/app/logs" \
        ark:dev
    
    print_success "Container started: ark-dev"
    print_info "Logs: docker logs -f ark-dev"
}

# ==================== UTILITIES ====================

show_info() {
    print_header "ℹ️  ARK Development Info"
    
    echo "Base Path:     $ARK_BASE_PATH"
    echo "Python:        $(python3 --version 2>&1)"
    echo "Venv Active:   ${VIRTUAL_ENV:-No}"
    echo ""
    
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            echo "Redis:         ✅ Running"
        else
            echo "Redis:         ❌ Not running"
        fi
    else
        echo "Redis:         ❌ Not installed"
    fi
    
    echo ""
    echo "Databases:"
    [ -f "$ARK_BASE_PATH/data/ark.db" ] && echo "  ark.db:          ✅ $(du -h $ARK_BASE_PATH/data/ark.db | cut -f1)" || echo "  ark.db:          ❌"
    [ -f "$ARK_BASE_PATH/data/reasoning_logs.db" ] && echo "  reasoning_logs:  ✅ $(du -h $ARK_BASE_PATH/data/reasoning_logs.db | cut -f1)" || echo "  reasoning_logs:  ❌"
}

# ==================== MAIN ====================

case "${1:-help}" in
    setup)
        setup_dev_env
        ;;
    lint)
        run_linters
        ;;
    format)
        format_code
        ;;
    test)
        run_tests "${2:-.}"
        ;;
    reset-db)
        reset_databases
        ;;
    seed)
        seed_test_data
        ;;
    dev)
        start_dev
        ;;
    logs)
        tail_logs "$2"
        ;;
    docker-build)
        docker_build
        ;;
    docker-run)
        docker_run
        ;;
    info)
        show_info
        ;;
    help|*)
        print_header "🛠️  ARK Development Tool"
        echo "Usage: $0 <command>"
        echo ""
        echo "Environment:"
        echo "  setup            - Set up development environment"
        echo "  info             - Show development environment info"
        echo ""
        echo "Code Quality:"
        echo "  lint             - Run all linters"
        echo "  format           - Format code with Black"
        echo "  test [path]      - Run tests (optional: specific path)"
        echo ""
        echo "Database:"
        echo "  reset-db         - Reset databases (with backup)"
        echo "  seed             - Seed databases with test data"
        echo ""
        echo "Development:"
        echo "  dev              - Start development servers"
        echo "  logs [file]      - Tail log file"
        echo ""
        echo "Docker:"
        echo "  docker-build     - Build Docker image"
        echo "  docker-run       - Run Docker container"
        echo ""
        echo "Examples:"
        echo "  $0 setup"
        echo "  $0 lint"
        echo "  $0 test tests/"
        echo "  $0 dev"
        ;;
esac
