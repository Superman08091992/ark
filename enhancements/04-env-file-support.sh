#!/bin/bash
##############################################################################
# ARK Environment File Support
# Enhancement #4 - .env file for easy configuration
##############################################################################

##############################################################################
# EXAMPLE .env FILE
##############################################################################
# Create this file at: $ARK_HOME/.env

cat > /dev/null << 'ENV_EXAMPLE'
# ARK Environment Configuration

# Server Settings
ARK_API_PORT=8000
ARK_API_HOST=0.0.0.0

# Redis Settings
ARK_REDIS_PORT=6379
ARK_REDIS_HOST=127.0.0.1

# Ollama Settings
ARK_OLLAMA_HOST=http://127.0.0.1:11434
ARK_OLLAMA_MODEL=llama3.2:1b

# Data Paths
ARK_DATA_DIR=/opt/ark/data
ARK_LOG_DIR=/opt/ark/logs
ARK_CONFIG_DIR=/opt/ark/config

# Features
ARK_DEBUG=false
ARK_AUTO_SAVE=true
ARK_LOG_LEVEL=info

# Web UI
ARK_WEB_PORT=4321
ARK_WEB_HOST=0.0.0.0

# Security
ARK_AUTH_ENABLED=false
ARK_API_KEY=
ARK_RATE_LIMIT=100

# Performance
ARK_MAX_WORKERS=4
ARK_CACHE_SIZE=1000
ENV_EXAMPLE

##############################################################################
# INTEGRATION INTO LAUNCHER SCRIPTS
##############################################################################

# Update ark launcher to load .env:
cat > /dev/null << 'ARK_LAUNCHER'
#!/bin/bash
# ARK Main Launcher with .env support

ARK_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Load environment variables from .env if it exists
if [ -f "$ARK_HOME/.env" ]; then
    export $(grep -v '^#' "$ARK_HOME/.env" | xargs)
fi

# Set defaults if not in .env
export ARK_HOME
export ARK_API_PORT=${ARK_API_PORT:-8000}
export ARK_API_HOST=${ARK_API_HOST:-0.0.0.0}
export ARK_REDIS_PORT=${ARK_REDIS_PORT:-6379}
export ARK_OLLAMA_HOST=${ARK_OLLAMA_HOST:-http://127.0.0.1:11434}
export ARK_DEBUG=${ARK_DEBUG:-false}

# Test bundled Node.js
if [ -f "$ARK_HOME/deps/node/nodejs/bin/node" ]; then
    if "$ARK_HOME/deps/node/nodejs/bin/node" --version &>/dev/null; then
        export PATH="$ARK_HOME/deps/node/nodejs/bin:$PATH"
    fi
fi

# Start ARK backend
cd "$ARK_HOME/lib"
exec node intelligent-backend.cjs "$@"
ARK_LAUNCHER

##############################################################################
# CREATE .env.example TEMPLATE
##############################################################################

# Add to installer after creating config:
cat > /dev/null << 'CREATE_ENV_EXAMPLE'
# Create .env.example template
cat > "$INSTALL_DIR/.env.example" << 'ENV_EOF'
# ARK Environment Configuration
# Copy this file to .env and customize

# Server Settings
ARK_API_PORT=8000
ARK_API_HOST=0.0.0.0

# Redis Settings
ARK_REDIS_PORT=6379
ARK_REDIS_HOST=127.0.0.1

# Ollama Settings
ARK_OLLAMA_HOST=http://127.0.0.1:11434
ARK_OLLAMA_MODEL=llama3.2:1b

# Data Paths  
ARK_DATA_DIR=$INSTALL_DIR/data
ARK_LOG_DIR=$INSTALL_DIR/logs
ARK_CONFIG_DIR=$INSTALL_DIR/config

# Features
ARK_DEBUG=false
ARK_AUTO_SAVE=true
ARK_LOG_LEVEL=info

# Web UI
ARK_WEB_PORT=4321
ARK_WEB_HOST=0.0.0.0

# Security
ARK_AUTH_ENABLED=false
ARK_API_KEY=
ARK_RATE_LIMIT=100
ENV_EOF

echo "📝 Created .env.example template at: $INSTALL_DIR/.env.example"
echo "   Copy to .env and customize: cp .env.example .env"
CREATE_ENV_EXAMPLE

##############################################################################
# USAGE INSTRUCTIONS
##############################################################################
#
# 1. After installation, create .env file:
#    cd $ARK_HOME
#    cp .env.example .env
#    nano .env  # or vi, vim, etc.
#
# 2. Customize values in .env
#
# 3. Restart ARK to load new values:
#    ark-redis &
#    ark
#
# 4. Check loaded values:
#    echo $ARK_API_PORT
#    echo $ARK_OLLAMA_HOST
#
##############################################################################
# BENEFITS
##############################################################################
#
# - Standard configuration format (.env is industry standard)
# - Easy to edit (simple key=value pairs)
# - Version control friendly (.env in .gitignore)
# - No config file parsing needed
# - Environment-specific configs (dev/prod)
# - Override defaults easily
# - Secrets management (API keys, tokens)
#
##############################################################################
# IMPLEMENTATION CHECKLIST
##############################################################################
#
# [ ] Add .env.example creation to installer
# [ ] Update ark launcher to load .env
# [ ] Update ark-redis launcher to load .env
# [ ] Update ark-web launcher to load .env
# [ ] Add .env to .gitignore
# [ ] Document .env variables in README
#
##############################################################################
