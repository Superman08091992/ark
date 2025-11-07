#!/bin/bash
##############################################################################
# Portable ARK Creator
# Creates a plug-and-play ARK system for USB/SD card
##############################################################################

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║           🚀 PORTABLE ARK SYSTEM CREATOR 🚀                      ║"
echo "║                                                                   ║"
echo "║  Creates a self-contained, plug-and-play AI system               ║"
echo "║  that runs from USB flash drive or SD card                       ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if target directory provided
if [ -z "$1" ]; then
    echo "❌ Error: Target directory not specified"
    echo ""
    echo "Usage: $0 /path/to/usb/drive"
    echo ""
    echo "Examples:"
    echo "  macOS:   $0 /Volumes/ARK_AI"
    echo "  Linux:   $0 /media/user/ARK_AI"
    echo "  Windows: $0 /mnt/d  (if using WSL/Git Bash)"
    echo ""
    exit 1
fi

TARGET_DIR="$1"
ARK_DIR="$TARGET_DIR/ark-system"

echo "📂 Target Location: $TARGET_DIR"
echo "🎯 ARK System Directory: $ARK_DIR"
echo ""

# Check if target exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "❌ Error: Target directory does not exist: $TARGET_DIR"
    echo ""
    echo "Please ensure your USB/SD card is mounted first."
    exit 1
fi

# Confirm with user
read -p "⚠️  This will create ARK system in $TARGET_DIR. Continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled by user"
    exit 1
fi

echo ""
echo "🔧 Creating Portable ARK System..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create directory structure
echo "1️⃣  Creating directory structure..."
mkdir -p "$ARK_DIR"
mkdir -p "$ARK_DIR/kyle_infinite_memory"
mkdir -p "$ARK_DIR/knowledge_base"
mkdir -p "$ARK_DIR/agent_logs"
mkdir -p "$ARK_DIR/ollama_data"
mkdir -p "$ARK_DIR/data"
mkdir -p "$ARK_DIR/frontend"

# Copy core files
echo "2️⃣  Copying ARK core files..."
cp intelligent-backend.cjs "$ARK_DIR/"
cp agent_tools.cjs "$ARK_DIR/"
cp package.json "$ARK_DIR/"
cp -r frontend "$ARK_DIR/"

# Copy documentation
echo "3️⃣  Copying documentation..."
cp LLM_INTEGRATION.md "$ARK_DIR/"
cp OLLAMA_SETUP.md "$ARK_DIR/"
cp PORTABLE_ARK_GUIDE.md "$ARK_DIR/"
cp README.md "$ARK_DIR/"

# Initialize data files
echo "4️⃣  Initializing data files..."
cat > "$ARK_DIR/kyle_infinite_memory/catalog.json" << 'EOF'
{}
EOF

cat > "$ARK_DIR/kyle_infinite_memory/master_index.json" << 'EOF'
{}
EOF

cat > "$ARK_DIR/knowledge_base/knowledge_graph.json" << 'EOF'
{"nodes":{}, "edges":[]}
EOF

# Create Docker Compose for portable setup
echo "5️⃣  Creating Docker Compose configuration..."
cat > "$ARK_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  backend:
    image: node:20-alpine
    command: sh -c "npm install && node intelligent-backend.cjs"
    working_dir: /app
    ports:
      - "8000:8000"
    volumes:
      - ./:/app
      - ./kyle_infinite_memory:/app/kyle_infinite_memory
      - ./knowledge_base:/app/knowledge_base
      - ./agent_logs:/app/agent_logs
      - ./data:/app/data
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - OLLAMA_MODEL=llama2
      - PORT=8000
    networks:
      - ark-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8000/api/agents"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ./ollama_data:/root/.ollama
    networks:
      - ark-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  ark-network:
    driver: bridge
EOF

# Create launchers for different OS
echo "6️⃣  Creating launcher scripts..."

# Mac/Linux launcher
cat > "$ARK_DIR/start-ark.sh" << 'EOF'
#!/bin/bash
##############################################################################
# Portable ARK Launcher (Mac/Linux)
##############################################################################

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                 🚀 Starting Portable ARK System 🚀               ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found!"
    echo ""
    echo "Please install Docker Desktop:"
    echo "  macOS: https://docs.docker.com/desktop/install/mac-install/"
    echo "  Linux: https://docs.docker.com/desktop/install/linux-install/"
    echo ""
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon not running!"
    echo ""
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker found and running"
echo ""

# Pull Ollama model if not present
echo "🧠 Checking Ollama model..."
docker-compose up -d ollama
sleep 5
docker-compose exec -T ollama ollama pull llama2 2>&1 | grep -v "pulling\|verifying"
echo "✅ Ollama ready"
echo ""

# Start services
echo "🚀 Starting ARK services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check health
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                   ║"
    echo "║                  ✅ ARK IS NOW RUNNING! ✅                       ║"
    echo "║                                                                   ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🌐 Access ARK at:"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs:    http://localhost:8000/api/agents"
    echo "   Ollama:      http://localhost:11434"
    echo ""
    echo "💬 Chat with Kyle:"
    echo "   curl -X POST http://localhost:8000/api/chat \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"agent_name\":\"Kyle\",\"message\":\"Hello Kyle\"}'"
    echo ""
    echo "💾 All data is saved to this USB drive"
    echo "🔌 To stop: ./stop-ark.sh"
    echo ""
    echo "📖 Documentation: See *.md files in this directory"
    echo ""
else
    echo ""
    echo "⚠️  Some services may not have started correctly"
    echo "Check status: docker-compose ps"
    echo "View logs: docker-compose logs"
fi
EOF

chmod +x "$ARK_DIR/start-ark.sh"

# Windows launcher
cat > "$ARK_DIR/start-ark.bat" << 'EOF'
@echo off
REM ##########################################################################
REM Portable ARK Launcher (Windows)
REM ##########################################################################

cd /d %~dp0

echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║                 Starting Portable ARK System                     ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

REM Check Docker
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Docker not found!
    echo.
    echo Please install Docker Desktop:
    echo https://docs.docker.com/desktop/install/windows-install/
    echo.
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Docker daemon not running!
    echo.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Docker found and running
echo.

REM Start services
echo Starting ARK services...
docker-compose up -d

REM Wait
echo.
echo Waiting for services to start...
timeout /t 10 /nobreak >nul

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║                  ARK IS NOW RUNNING!                             ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.
echo Access ARK at:
echo   Backend API: http://localhost:8000
echo   API Docs:    http://localhost:8000/api/agents
echo   Ollama:      http://localhost:11434
echo.
echo All data is saved to this USB drive
echo To stop: stop-ark.bat
echo.
pause
EOF

# Stop scripts
cat > "$ARK_DIR/stop-ark.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🛑 Stopping ARK..."
docker-compose down
echo "✅ ARK stopped. Safe to unplug USB drive."
EOF

chmod +x "$ARK_DIR/stop-ark.sh"

cat > "$ARK_DIR/stop-ark.bat" << 'EOF'
@echo off
cd /d %~dp0
echo Stopping ARK...
docker-compose down
echo ARK stopped. Safe to unplug USB drive.
pause
EOF

# Create README
echo "7️⃣  Creating quick start guide..."
cat > "$ARK_DIR/README-PORTABLE.txt" << 'EOF'
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                    PORTABLE ARK QUICK START                          ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

WHAT IS THIS?
─────────────────────────────────────────────────────────────────────────
This is a fully portable, self-contained AI system that runs entirely
from this USB drive or SD card. It includes:

  • Kyle: AI agent with infinite memory
  • LLM Integration: Ollama with llama2 model
  • Auto-research: Learns from conversations
  • Source citations: All information is sourced
  • Persistent storage: All data saved to this drive


REQUIREMENTS
─────────────────────────────────────────────────────────────────────────
  • Docker Desktop (one-time install on host machine)
  • 8GB+ USB drive or SD card
  • Windows, macOS, or Linux


QUICK START
─────────────────────────────────────────────────────────────────────────
1. Install Docker Desktop (if not installed):
   https://www.docker.com/get-started

2. Run the launcher:
   - Mac/Linux: ./start-ark.sh
   - Windows:   start-ark.bat

3. Wait ~30 seconds for services to start

4. Access ARK at http://localhost:8000


USAGE
─────────────────────────────────────────────────────────────────────────
Chat with Kyle:
  curl -X POST http://localhost:8000/api/chat \
    -H 'Content-Type: application/json' \
    -d '{"agent_name":"Kyle","message":"Hello Kyle"}'

Check agents:
  curl http://localhost:8000/api/agents

Check Kyle's memory:
  curl http://localhost:8000/api/memory


STOPPING ARK
─────────────────────────────────────────────────────────────────────────
  - Mac/Linux: ./stop-ark.sh
  - Windows:   stop-ark.bat

IMPORTANT: Always stop ARK before unplugging the drive!


DATA STORAGE
─────────────────────────────────────────────────────────────────────────
All data is stored on this USB drive in these directories:

  kyle_infinite_memory/  - Kyle's permanent memories
  knowledge_base/        - Knowledge graph
  agent_logs/           - Conversation logs
  ollama_data/          - LLM models and cache
  data/                 - User data


TROUBLESHOOTING
─────────────────────────────────────────────────────────────────────────
Problem: "Docker not found"
  → Install Docker Desktop from docker.com

Problem: "Docker daemon not running"
  → Start Docker Desktop application

Problem: Services won't start
  → Check Docker has enough resources (4GB+ RAM recommended)
  → Run: docker-compose logs

Problem: Ollama model not loading
  → Run: docker-compose exec ollama ollama pull llama2


DOCUMENTATION
─────────────────────────────────────────────────────────────────────────
  README.md               - Main documentation
  LLM_INTEGRATION.md      - LLM features guide
  OLLAMA_SETUP.md         - Ollama configuration
  PORTABLE_ARK_GUIDE.md   - Full portable setup guide


FEATURES
─────────────────────────────────────────────────────────────────────────
✅ Infinite Memory: Kyle never forgets
✅ LLM Enhancement: Intelligent research with Ollama
✅ Auto-Research: Learns about unknown topics automatically
✅ Source Citations: All information is sourced and verified
✅ Quiet Operation: No status spam, just useful responses
✅ Knowledge Extraction: Filters facts from noise
✅ Portable: Run from any computer with Docker


SUPPORT
─────────────────────────────────────────────────────────────────────────
GitHub: https://github.com/Superman08091992/ark
Issues: https://github.com/Superman08091992/ark/issues


VERSION
─────────────────────────────────────────────────────────────────────────
Portable ARK v1.0
Created: 2025-11-07
EOF

# Create version file
echo "8️⃣  Creating version file..."
cat > "$ARK_DIR/VERSION" << EOF
Portable ARK v1.0
Created: $(date)
Source: /home/user/webapp
Branch: genspark_ai_developer
Commit: $(cd /home/user/webapp && git rev-parse --short HEAD 2>/dev/null || echo "N/A")
EOF

# Create status check script
cat > "$ARK_DIR/status.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                    ARK System Status                             ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

docker-compose ps

echo ""
echo "📊 Storage Usage:"
du -sh kyle_infinite_memory knowledge_base agent_logs ollama_data 2>/dev/null

echo ""
echo "💾 Memory Count:"
echo "  Memories: $(find kyle_infinite_memory -name "*.json" 2>/dev/null | wc -l)"

echo ""
echo "🧠 Ollama Models:"
docker-compose exec -T ollama ollama list 2>/dev/null || echo "  Ollama not running"
EOF

chmod +x "$ARK_DIR/status.sh"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║            ✅ PORTABLE ARK SYSTEM CREATED! ✅                    ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "📂 Location: $ARK_DIR"
echo ""
echo "📋 What's included:"
echo "   ✓ ARK intelligent backend"
echo "   ✓ LLM integration (Ollama)"
echo "   ✓ Kyle's infinite memory system"
echo "   ✓ Auto-research capabilities"
echo "   ✓ Source citation system"
echo "   ✓ All documentation"
echo "   ✓ Launcher scripts"
echo "   ✓ Data persistence"
echo ""
echo "🚀 To start ARK:"
echo "   cd $ARK_DIR"
echo "   ./start-ark.sh  (Mac/Linux)"
echo "   start-ark.bat   (Windows)"
echo ""
echo "📖 Quick start guide:"
echo "   $ARK_DIR/README-PORTABLE.txt"
echo ""
echo "💡 This USB/SD card can now run ARK on any computer with Docker!"
echo ""
