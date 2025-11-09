#!/bin/bash
################################################################################
# ARK Docker Entrypoint Script
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🐳 ARK Docker Container Starting${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Set ARK_HOME
export ARK_HOME="${ARK_HOME:-/home/ark/ark}"
export PATH="$ARK_HOME/bin:$PATH"

# Load environment variables from .env if exists
if [ -f "$ARK_HOME/.env" ]; then
    echo -e "${GREEN}✓${NC} Loading configuration from .env"
    set -a
    source "$ARK_HOME/.env"
    set +a
fi

# Start Redis in background
echo -e "${CYAN}▶${NC} Starting Redis..."
redis-server --daemonize yes --port ${ARK_REDIS_PORT:-6379} --bind ${ARK_REDIS_HOST:-127.0.0.1}

# Wait for Redis to be ready
echo -n "  Waiting for Redis..."
for i in {1..30}; do
    if redis-cli -h ${ARK_REDIS_HOST:-127.0.0.1} -p ${ARK_REDIS_PORT:-6379} ping &>/dev/null; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    sleep 1
done

# Start Ollama if installed and enabled
if command -v ollama &>/dev/null && [ "${ARK_OLLAMA_ENABLED:-true}" = "true" ]; then
    echo -e "${CYAN}▶${NC} Starting Ollama..."
    ollama serve &>/dev/null &
    
    # Wait for Ollama to be ready
    echo -n "  Waiting for Ollama..."
    for i in {1..30}; do
        if curl -sf ${ARK_OLLAMA_HOST:-http://127.0.0.1:11434}/api/tags &>/dev/null; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        sleep 1
    done
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ ARK Container Ready${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  API Port:    ${ARK_API_PORT:-8000}"
echo "  Redis Port:  ${ARK_REDIS_PORT:-6379}"
echo "  Ollama Port: 11434"
echo ""

# Execute the command
exec "$@"
