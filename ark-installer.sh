#!/bin/bash
set -e

# ============================================================================
# A.R.K. — Autonomous Reactive Kernel Universal Installer
# ============================================================================
# 
# Installs complete ARK system with:
# - Multi-agent framework (Kyle, Joey, Kenny, HRM, Aletheia, ID)
# - Distributed mesh federation
# - Autonomous learning pipeline (Memory → Reflection → ID Growth)
# - Portable sovereign node capability
#
# Supports: x86_64, ARM64 (Raspberry Pi), containerized environments
# ============================================================================

echo "🌌 A.R.K. — Autonomous Reactive Kernel Universal Installer"
echo "=========================================================="
echo ""
echo "This installer will provision:"
echo "  • Multi-agent cognitive framework"
echo "  • Federation mesh networking"
echo "  • Autonomous learning systems"
echo "  • Memory, Reflection, and ID Growth"
echo ""
sleep 2

# ============================================================================
# 1. ENVIRONMENT DETECTION
# ============================================================================

echo "🔍 Detecting system environment..."

# Detect architecture
ARCH=$(uname -m)
case "$ARCH" in
    x86_64)
        PLATFORM="x86_64"
        ;;
    aarch64|arm64)
        PLATFORM="ARM64"
        ;;
    armv7l)
        PLATFORM="ARMv7"
        ;;
    *)
        echo "⚠️  Unsupported architecture: $ARCH"
        echo "Supported: x86_64, ARM64, ARMv7"
        exit 1
        ;;
esac

# Detect OS
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    OS_NAME=$NAME
    OS_VERSION=$VERSION_ID
else
    OS_NAME=$(uname -s)
    OS_VERSION="unknown"
fi

# Check if running in container
if [[ -f /.dockerenv ]] || grep -q docker /proc/1/cgroup 2>/dev/null; then
    IN_CONTAINER=true
else
    IN_CONTAINER=false
fi

echo "✓ Platform: $PLATFORM"
echo "✓ OS: $OS_NAME $OS_VERSION"
echo "✓ Container: $IN_CONTAINER"
echo ""

# ============================================================================
# 2. DIRECTORY STRUCTURE
# ============================================================================

echo "📁 Creating directory structure..."

# Core directories
mkdir -p agents backend frontend data files logs shared
mkdir -p memory reflection id federation services tests

# Data subdirectories
mkdir -p data/db data/reflection_archive data/federation data/backups

# Log subdirectories  
mkdir -p logs/agents logs/federation logs/reflection logs/id

# Secure permissions
chmod 700 logs data/db data/federation
chmod 755 agents backend frontend services

echo "✓ Directory structure created"
echo ""

# ============================================================================
# 3. SYSTEM DEPENDENCIES
# ============================================================================

echo "📦 Checking system dependencies..."

# Check for required commands
REQUIRED_COMMANDS="python3 sqlite3 curl git"
MISSING_COMMANDS=""

for cmd in $REQUIRED_COMMANDS; do
    if ! command -v $cmd &> /dev/null; then
        MISSING_COMMANDS="$MISSING_COMMANDS $cmd"
    fi
done

if [[ -n "$MISSING_COMMANDS" ]]; then
    echo "⚠️  Missing required commands:$MISSING_COMMANDS"
    echo ""
    echo "Please install them first:"
    
    if [[ "$OS_NAME" == *"Ubuntu"* ]] || [[ "$OS_NAME" == *"Debian"* ]]; then
        echo "  sudo apt-get update"
        echo "  sudo apt-get install -y python3 python3-pip python3-venv sqlite3 curl git"
    elif [[ "$OS_NAME" == *"CentOS"* ]] || [[ "$OS_NAME" == *"Red Hat"* ]]; then
        echo "  sudo yum install -y python3 python3-pip sqlite curl git"
    elif [[ "$OS_NAME" == "Darwin" ]]; then
        echo "  brew install python3 sqlite curl git"
    fi
    
    exit 1
fi

echo "✓ System dependencies satisfied"
echo ""

# ============================================================================
# 4. PYTHON ENVIRONMENT
# ============================================================================

echo "🐍 Setting up Python environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 8 ]]; then
    echo "⚠️  Python 3.8+ required, found $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"

# Create virtual environment
if [[ ! -d venv ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip wheel setuptools -q

echo "✓ Python environment ready"
echo ""

# ============================================================================
# 5. PYTHON DEPENDENCIES
# ============================================================================

echo "📚 Installing Python dependencies..."

# Core dependencies
echo "Installing core packages..."
pip install -q \
    fastapi uvicorn websockets \
    sqlalchemy sqlite-utils \
    pyyaml python-dotenv \
    pydantic \
    httpx aiohttp

# Autonomous learning dependencies
echo "Installing autonomous learning packages..."
pip install -q \
    numpy scipy pandas \
    scikit-learn \
    apscheduler

# Cryptography and security
echo "Installing cryptography packages..."
pip install -q \
    PyNaCl cryptography

# Optional dependencies (with fallbacks)
echo "Installing optional packages..."
pip install -q duckdb 2>/dev/null || echo "  ⚠️  DuckDB not available (optional)"
pip install -q redis 2>/dev/null || echo "  ⚠️  Redis not available (optional)"

echo "✓ Python dependencies installed"
echo ""

# ============================================================================
# 6. NODE.JS ENVIRONMENT (OPTIONAL)
# ============================================================================

echo "🪐 Checking Node.js environment..."

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Node.js $NODE_VERSION detected"
    
    # Install PM2 if not present
    if ! command -v pm2 &> /dev/null; then
        echo "Installing PM2 process manager..."
        npm install -g pm2 2>/dev/null || echo "  ⚠️  PM2 installation failed (optional)"
    fi
else
    echo "⚠️  Node.js not found (optional for process management)"
    echo "   Install from: https://nodejs.org/"
fi

echo ""

# ============================================================================
# 7. DATABASE INITIALIZATION
# ============================================================================

echo "🗄️  Initializing databases..."

# SQLite database
if [[ -f memory/schema.sql ]]; then
    echo "Creating memory database..."
    sqlite3 data/demo_memory.db < memory/schema.sql
    echo "✓ Memory database initialized"
else
    echo "⚠️  memory/schema.sql not found, creating empty database"
    sqlite3 data/demo_memory.db "SELECT 1;"
fi

# DuckDB analytics database (optional)
if command -v duckdb &> /dev/null; then
    echo "Creating analytics database..."
    duckdb data/analytics.duckdb "CREATE TABLE IF NOT EXISTS metrics (id VARCHAR, timestamp TIMESTAMP, data JSON);"
    echo "✓ Analytics database initialized"
fi

echo ""

# ============================================================================
# 8. REDIS CACHE (OPTIONAL)
# ============================================================================

echo "🔴 Checking Redis cache..."

if command -v redis-server &> /dev/null; then
    # Check if Redis is already running
    if redis-cli ping &> /dev/null; then
        echo "✓ Redis already running"
    else
        echo "Starting Redis server..."
        redis-server --daemonize yes --port 6379 2>/dev/null || echo "  ⚠️  Redis startup failed (optional)"
    fi
elif command -v redis-cli &> /dev/null; then
    echo "✓ Redis client available"
else
    echo "⚠️  Redis not found (optional for caching)"
fi

echo ""

# ============================================================================
# 9. ENVIRONMENT CONFIGURATION
# ============================================================================

echo "⚙️  Creating environment configuration..."

cat > .env << 'EOF'
# ============================================================================
# A.R.K. Environment Configuration
# ============================================================================

# === System Settings ===
ARK_ENV=production
ARK_LOG_LEVEL=INFO
ARK_TIMEZONE=UTC
ARK_DEBUG=false

# === Database Paths ===
ARK_DB_PATH=data/demo_memory.db
ARK_ANALYTICS_PATH=data/analytics.duckdb

# === Reflection System ===
ARK_REFLECTION_MODE=sleep
ARK_SLEEP_SCHEDULE=0 0 * * *
ARK_REFLECTION_RETENTION_DAYS=90
ARK_REFLECTION_AUDIT_LOG=logs/reflection_audit.log

# === ID Growth System ===
ARK_ID_MODEL_PATH=data/id_state.db
ARK_ID_BASE_ALPHA=0.3
ARK_ID_MIN_ALPHA=0.05
ARK_ID_MAX_ALPHA=0.8

# === Federation Settings ===
ARK_FEDERATION_PORT=8104
ARK_DISCOVERY_PORT=8103
ARK_DISCOVERY_ADDRESS=239.255.0.1
ARK_FEDERATION_KEYS_PATH=data/federation/keys
ARK_TRUST_TIER=CORE

# === HTTP Services ===
ARK_HTTP_PORT=8000
ARK_BACKEND_URL=http://localhost:8000
ARK_ENABLE_CORS=true
ARK_MAX_UPLOAD_SIZE=10485760

# === Cache Settings ===
ARK_REDIS_URL=redis://localhost:6379
ARK_REDIS_ENABLED=true
ARK_CACHE_TTL=3600

# === External Services (Optional) ===
ARK_SUPABASE_URL=https://aqbibheiykdrehjpsjjw.supabase.co
ARK_SUPABASE_KEY=
ARK_OPENAI_API_KEY=
ARK_ANTHROPIC_API_KEY=

# === Agent Settings ===
ARK_AGENT_TIMEOUT=300
ARK_MAX_REASONING_DEPTH=5
ARK_DEFAULT_CONFIDENCE=0.5

# === Security ===
ARK_REQUIRE_SIGNATURES=true
ARK_QUARANTINE_VIOLATIONS=true
ARK_HRM_GATE_ENABLED=true

EOF

echo "✓ Environment configuration created (.env)"
echo ""

# ============================================================================
# 10. FEDERATION INITIALIZATION
# ============================================================================

echo "🔐 Initializing federation cryptography..."

# Create federation keys directory
mkdir -p data/federation/keys

# Generate Ed25519 keypair for federation
python3 - << 'PYCODE'
import os
import json
from pathlib import Path

try:
    from nacl.signing import SigningKey
    from nacl.encoding import HexEncoder
    
    keys_dir = Path("data/federation/keys")
    keys_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate signing key
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key
    
    # Save keys
    with open(keys_dir / "signing.key", "wb") as f:
        f.write(signing_key.encode(encoder=HexEncoder))
    
    with open(keys_dir / "verify.key", "wb") as f:
        f.write(verify_key.encode(encoder=HexEncoder))
    
    # Set secure permissions
    os.chmod(keys_dir / "signing.key", 0o600)
    os.chmod(keys_dir / "verify.key", 0o644)
    
    # Create peer ID
    peer_id = verify_key.encode(encoder=HexEncoder).decode()[:16]
    
    with open(keys_dir / "peer_id.txt", "w") as f:
        f.write(peer_id)
    
    print(f"✓ Federation keypair generated (Peer ID: {peer_id})")

except ImportError:
    print("⚠️  PyNaCl not available - federation crypto skipped")
    print("   Install with: pip install PyNaCl")

PYCODE

echo ""

# ============================================================================
# 11. AUTONOMOUS LEARNING INITIALIZATION
# ============================================================================

echo "🧠 Initializing autonomous learning systems..."

# Initialize Reflection System
python3 - << 'PYCODE'
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

try:
    # Check if reflection system exists
    if Path("reflection/reflection_engine.py").exists():
        from reflection.reflection_engine import ReflectionEngine
        
        engine = ReflectionEngine(
            db_path='data/demo_memory.db',
            policy_path='reflection/reflection_policies.yaml'
        )
        
        print("✓ Reflection engine initialized")
        engine.close()
    else:
        print("⚠️  Reflection system not found - skipping initialization")

except Exception as e:
    print(f"⚠️  Reflection initialization failed: {e}")

PYCODE

# Initialize ID Growth System
python3 - << 'PYCODE'
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

try:
    # Check if ID system exists
    if Path("id/model.py").exists():
        from id.model import IDModel
        
        model = IDModel(db_path='data/demo_memory.db')
        
        # Initialize core agents
        core_agents = ['Kyle', 'Joey', 'Kenny', 'HRM', 'Aletheia', 'ID']
        
        for agent in core_agents:
            state = model.get_state(agent)
            if not state:
                model.initialize_agent(agent)
        
        print(f"✓ ID system initialized ({len(core_agents)} core agents)")
        model.close()
    else:
        print("⚠️  ID system not found - skipping initialization")

except Exception as e:
    print(f"⚠️  ID initialization failed: {e}")

PYCODE

echo ""

# ============================================================================
# 12. SERVICE MANAGEMENT SCRIPTS
# ============================================================================

echo "🚀 Creating service management scripts..."

# Main startup script
cat > arkstart.sh << 'EOF'
#!/bin/bash
set -e

echo "🌌 Starting A.R.K. Autonomous Reactive Kernel"
echo "=============================================="

# Activate environment
source venv/bin/activate

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Start services based on availability
echo ""
echo "Starting services..."

# Check for PM2
if command -v pm2 &> /dev/null; then
    echo "Using PM2 process manager..."
    
    # Backend
    if [[ -f backend/main.py ]]; then
        pm2 start backend/main.py --name ark-backend --interpreter python3 --watch
        echo "✓ Backend started (PM2)"
    fi
    
    # Agents
    for agent in agents/*.py; do
        if [[ -f "$agent" ]]; then
            agent_name=$(basename "$agent" .py)
            pm2 start "$agent" --name "ark-$agent_name" --interpreter python3
            echo "✓ Agent $agent_name started (PM2)"
        fi
    done
    
    echo ""
    echo "View logs with: pm2 logs"
    echo "Stop all with: pm2 stop all"
    
else
    echo "Starting services directly (PM2 not available)..."
    
    # Backend
    if [[ -f backend/main.py ]]; then
        python3 backend/main.py &
        echo "✓ Backend started"
    fi
    
    echo ""
    echo "Services running in background"
    echo "View logs in: logs/"
fi

echo ""
echo "🎉 A.R.K. systems online!"
echo ""
echo "Access at: http://localhost:${ARK_HTTP_PORT:-8000}"

EOF

chmod +x arkstart.sh

# Stop script
cat > arkstop.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping A.R.K. systems..."

if command -v pm2 &> /dev/null; then
    pm2 stop all
    pm2 delete all
    echo "✓ All PM2 processes stopped"
else
    # Kill by process name
    pkill -f "python3.*backend" || true
    pkill -f "python3.*agents" || true
    echo "✓ Services stopped"
fi

echo "✓ A.R.K. systems offline"

EOF

chmod +x arkstop.sh

# Status script
cat > arkstatus.sh << 'EOF'
#!/bin/bash

echo "📊 A.R.K. System Status"
echo "======================="
echo ""

# Database check
if [[ -f data/demo_memory.db ]]; then
    echo "✓ Memory database: OK"
    db_size=$(du -h data/demo_memory.db | cut -f1)
    echo "  Size: $db_size"
else
    echo "✗ Memory database: Not found"
fi

# Environment check
if [[ -f .env ]]; then
    echo "✓ Environment configuration: OK"
else
    echo "✗ Environment configuration: Missing"
fi

# Virtual environment check
if [[ -d venv ]]; then
    echo "✓ Python environment: OK"
else
    echo "✗ Python environment: Not initialized"
fi

# Process check
echo ""
echo "Running processes:"
if command -v pm2 &> /dev/null; then
    pm2 list
else
    ps aux | grep -E "python3.*(backend|agents)" | grep -v grep || echo "  No processes found"
fi

echo ""
echo "Federation:"
if [[ -f data/federation/keys/peer_id.txt ]]; then
    peer_id=$(cat data/federation/keys/peer_id.txt)
    echo "  Peer ID: $peer_id"
else
    echo "  Not initialized"
fi

echo ""
echo "Recent logs:"
if [[ -f logs/reflection_audit.log ]]; then
    echo "  Reflection: $(tail -1 logs/reflection_audit.log)"
fi

EOF

chmod +x arkstatus.sh

echo "✓ Service scripts created"
echo "  - arkstart.sh: Start all services"
echo "  - arkstop.sh: Stop all services"  
echo "  - arkstatus.sh: Check system status"
echo ""

# ============================================================================
# 13. DOCKER SUPPORT
# ============================================================================

echo "🐋 Creating Docker configuration..."

cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements*.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt || true

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data logs data/federation

# Expose ports
EXPOSE 8000 8103/udp 8104

# Set environment
ENV ARK_ENV=production
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python3", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

EOF

cat > docker-compose.yml << 'EOF'
version: "3.9"

services:
  ark-backend:
    build: .
    container_name: ark-backend
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - ARK_ENV=production
      - ARK_DB_PATH=data/demo_memory.db
      - ARK_REDIS_URL=redis://redis:6379
    ports:
      - "8000:8000"
      - "8103:8103/udp"
      - "8104:8104"
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: ark-redis
    restart: unless-stopped
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"

  ark-agents:
    build: .
    container_name: ark-agents
    command: bash -c "python3 agents/supervisor.py || sleep infinity"
    depends_on:
      - ark-backend
      - redis
    environment:
      - ARK_BACKEND_URL=http://ark-backend:8000
      - ARK_REDIS_URL=redis://redis:6379
    volumes:
      - ./agents:/app/agents
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped

volumes:
  redis-data:

EOF

cat > .dockerignore << 'EOF'
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.git/
.env
node_modules/
*.log
.DS_Store

EOF

echo "✓ Docker configuration created"
echo ""

# ============================================================================
# 14. VALIDATION
# ============================================================================

echo "🧪 Validating installation..."

VALIDATION_PASSED=true

# Check critical files
CRITICAL_FILES=(
    "data/demo_memory.db"
    ".env"
    "arkstart.sh"
    "arkstop.sh"
    "arkstatus.sh"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✓ $file"
    else
        echo "✗ $file (missing)"
        VALIDATION_PASSED=false
    fi
done

# Check directories
CRITICAL_DIRS=(
    "data"
    "logs"
    "venv"
)

for dir in "${CRITICAL_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        echo "✓ $dir/"
    else
        echo "✗ $dir/ (missing)"
        VALIDATION_PASSED=false
    fi
done

echo ""

if [[ "$VALIDATION_PASSED" == true ]]; then
    echo "✅ Installation validation successful"
else
    echo "⚠️  Some components missing - check errors above"
fi

echo ""

# ============================================================================
# 15. FINAL SUMMARY
# ============================================================================

echo "============================================================================"
echo "🎉 A.R.K. Installation Complete!"
echo "============================================================================"
echo ""
echo "System Configuration:"
echo "  Platform: $PLATFORM"
echo "  OS: $OS_NAME"
echo "  Python: $PYTHON_VERSION"
echo "  Database: data/demo_memory.db"
echo "  Environment: .env"
echo ""
echo "Next Steps:"
echo ""
echo "  1. Review configuration:"
echo "     cat .env"
echo ""
echo "  2. Start all services:"
echo "     ./arkstart.sh"
echo ""
echo "  3. Check system status:"
echo "     ./arkstatus.sh"
echo ""
echo "  4. Run demonstrations:"
echo "     source venv/bin/activate"
echo "     python3 demo_memory_engine.py"
echo "     python3 demo_reflection_system.py"
echo "     python3 demo_id_growth.py"
echo ""
echo "  5. Access API:"
echo "     curl http://localhost:8000/health"
echo ""
echo "Docker Alternative:"
echo "  docker-compose up -d"
echo ""
echo "Documentation:"
echo "  • Memory Engine: memory/README.md"
echo "  • Reflection System: reflection/reflection_policies.yaml"
echo "  • ID Growth: id/__init__.py"
echo "  • Federation: federation/README.md"
echo ""
echo "============================================================================"
echo "🌌 Welcome to the A.R.K. Autonomous Reactive Kernel"
echo "============================================================================"
echo ""
