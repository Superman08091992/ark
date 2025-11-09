#!/bin/bash
##############################################################################
# ARK Health Check Command
# Enhancement #1 - Shows complete system status
##############################################################################

ARK_HOME="${ARK_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export PATH="$ARK_HOME/deps/node/nodejs/bin:$ARK_HOME/deps/redis/bin:$PATH"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║                    ARK Health Check                           ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

HEALTH_OK=true

# Check installation
echo "📁 Installation:"
if [ -d "$ARK_HOME" ]; then
    echo "   ✅ ARK_HOME: $ARK_HOME"
else
    echo "   ❌ ARK_HOME not found"
    HEALTH_OK=false
fi

# Check Node.js
echo ""
echo "🟢 Node.js:"
if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version)
    echo "   ✅ Version: $NODE_VERSION"
    echo "   ✅ Path: $(which node)"
else
    echo "   ❌ Node.js not found in PATH"
    HEALTH_OK=false
fi

# Check Redis
echo ""
echo "🔴 Redis:"
if command -v redis-server &>/dev/null; then
    REDIS_VERSION=$(redis-server --version | head -n1)
    echo "   ✅ Version: $REDIS_VERSION"
    
    # Check if running
    if redis-cli ping &>/dev/null; then
        echo "   ✅ Running and responding"
    else
        echo "   ⚠️  Not running (start with: ark-redis)"
    fi
else
    echo "   ❌ Redis not found in PATH"
    HEALTH_OK=false
fi

# Check Ollama
echo ""
echo "🤖 Ollama:"
if command -v ollama &>/dev/null; then
    echo "   ✅ Installed"
    
    # Try to connect
    if ollama list &>/dev/null; then
        echo "   ✅ Running"
        echo "   📦 Installed models:"
        ollama list | tail -n +2 | awk '{print "      - " $1}'
    else
        echo "   ⚠️  Not running (start with: ollama serve)"
    fi
else
    echo "   ⚠️  Not installed (install from: https://ollama.ai)"
fi

# Check backend
echo ""
echo "🧠 Backend:"
if [ -f "$ARK_HOME/lib/intelligent-backend.cjs" ]; then
    echo "   ✅ Backend file present"
    
    # Check if running
    if pgrep -f intelligent-backend &>/dev/null; then
        echo "   ✅ Running"
        PID=$(pgrep -f intelligent-backend)
        echo "      PID: $PID"
    else
        echo "   ⚠️  Not running (start with: ark)"
    fi
else
    echo "   ❌ Backend file missing"
    HEALTH_OK=false
fi

# Check data directories
echo ""
echo "💾 Data Directories:"
for dir in data/knowledge_base data/kyle_infinite_memory logs; do
    if [ -d "$ARK_HOME/$dir" ]; then
        SIZE=$(du -sh "$ARK_HOME/$dir" 2>/dev/null | cut -f1)
        echo "   ✅ $dir ($SIZE)"
    else
        echo "   ⚠️  $dir (not created yet)"
    fi
done

# Check configuration
echo ""
echo "⚙️  Configuration:"
if [ -f "$ARK_HOME/config/ark.conf" ]; then
    echo "   ✅ Config file present"
    API_PORT=$(grep -m1 'port = ' "$ARK_HOME/config/ark.conf" | head -n1 | cut -d= -f2 | tr -d ' ' || echo "8000")
    LLM_MODEL=$(grep 'model = ' "$ARK_HOME/config/ark.conf" | cut -d= -f2 | tr -d ' ' || echo "unknown")
    echo "      API Port: $API_PORT"
    echo "      LLM Model: $LLM_MODEL"
else
    echo "   ❌ Config file missing"
    HEALTH_OK=false
fi

# Check .env file if exists
if [ -f "$ARK_HOME/.env" ]; then
    echo ""
    echo "🔧 Environment:"
    echo "   ✅ .env file present"
fi

# Network check
echo ""
echo "🌐 Network:"
API_PORT=$(grep -m1 'port = ' "$ARK_HOME/config/ark.conf" 2>/dev/null | cut -d= -f2 | tr -d ' ' || echo "8000")
if command -v nc &>/dev/null; then
    if nc -z 127.0.0.1 "$API_PORT" 2>/dev/null; then
        echo "   ✅ API responding on port $API_PORT"
    else
        echo "   ⚠️  API not responding on port $API_PORT"
    fi
else
    echo "   ℹ️  nc not available, skipping port check"
fi

# Overall status
echo ""
if [ "$HEALTH_OK" = true ]; then
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                 ✅ SYSTEM HEALTHY ✅                         ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    exit 0
else
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║              ⚠️  ISSUES DETECTED ⚠️                         ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   1. Check installation: cd \$ARK_HOME"
    echo "   2. View logs: tail -f \$ARK_HOME/logs/*.log"
    echo "   3. Restart services: ark-redis & ark"
    exit 1
fi
