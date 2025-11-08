#!/bin/bash
##############################################################################
# ARK Host Service Installer
# Installs ARK host service for USB node connections
##############################################################################

set -e

VERSION="1.0.0"

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║            ARK HOST SERVICE INSTALLER v${VERSION}                    ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Detect OS
if [ -f /etc/arch-release ]; then
    OS="arch"
    PKG_MANAGER="pacman"
elif [ -f /etc/debian_version ]; then
    OS="debian"
    PKG_MANAGER="apt"
elif [ -f /etc/redhat-release ]; then
    OS="redhat"
    PKG_MANAGER="yum"
elif [ "$(uname)" == "Darwin" ]; then
    OS="macos"
    PKG_MANAGER="brew"
else
    echo "❌ Unsupported OS"
    exit 1
fi

echo "📋 Detected OS: $OS"
echo ""

# Check root/sudo
if [ "$EUID" -ne 0 ] && [ "$OS" != "macos" ]; then
    echo "⚠️  This script needs sudo privileges for system installation"
    echo "   Re-running with sudo..."
    exec sudo bash "$0" "$@"
fi

echo "1️⃣  Installing dependencies..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for bundled Node.js
if [ -d "$SCRIPT_DIR/deps/node/nodejs" ]; then
    echo "✅ Found bundled Node.js v20.10.0"
    export PATH="$SCRIPT_DIR/deps/node/nodejs/bin:$PATH"
    NODE_BUNDLED=true
else
    echo "⬇️  Node.js not bundled, will install from package manager..."
    NODE_BUNDLED=false
fi

# Check for bundled Redis
if [ -f "$SCRIPT_DIR/deps/redis/bin/redis-server" ]; then
    echo "✅ Found bundled Redis v7.2.4"
    REDIS_BUNDLED=true
else
    echo "⬇️  Redis not bundled, will install from package manager..."
    REDIS_BUNDLED=false
fi

# Install missing dependencies
case $OS in
    arch)
        [ "$NODE_BUNDLED" = false ] && pacman -Sy --needed --noconfirm nodejs
        [ "$REDIS_BUNDLED" = false ] && pacman -Sy --needed --noconfirm redis
        pacman -Sy --needed --noconfirm ollama || echo "⚠️  Ollama not in repos, will download manually"
        ;;
    debian)
        [ "$NODE_BUNDLED" = false ] && (apt update && apt install -y nodejs npm)
        [ "$REDIS_BUNDLED" = false ] && (apt update && apt install -y redis-server)
        # Ollama (always download, not bundled)
        echo "⬇️  Installing Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
        ;;
    macos)
        [ "$NODE_BUNDLED" = false ] && brew install node
        [ "$REDIS_BUNDLED" = false ] && brew install redis
        brew install ollama
        ;;
    *)
        echo "❌ Package installation not implemented for $OS"
        exit 1
        ;;
esac

# Copy bundled Redis to system if present
if [ "$REDIS_BUNDLED" = true ]; then
    echo "📦 Installing bundled Redis binaries..."
    cp "$SCRIPT_DIR/deps/redis/bin/"* /usr/local/bin/
    chmod +x /usr/local/bin/redis-*
fi

echo ""
echo "2️⃣  Creating ARK host directory..."
mkdir -p /opt/ark-host/{bin,models,db,logs,skills,redis}
mkdir -p /opt/ark-host/skills/{system_ops,devops,data_ai,productivity,trading,media_docs,hardware}

echo ""
echo "3️⃣  Creating host configuration..."
cat > /opt/ark-host/config.yaml << 'EOF'
host:
  id: "host_$(hostname)_$(openssl rand -hex 4)"
  name: "$(hostname)"
  
services:
  arkd:
    enabled: true
    workers: 4
    
  redis:
    enabled: true
    maxmemory: 2GB
    bind: 127.0.0.1
    port: 6379
    
  ollama:
    enabled: true
    gpu: auto
    models:
      - llama2
  
api:
  bind: 127.0.0.1
  port: 8000
  tls: false  # Set to true for production
  
resources:
  cpu_limit: 8
  ram_limit: 16GB
  gpu_enabled: true
  
session:
  max_concurrent: 3
  idle_timeout_minutes: 120
  temp_dir: /tmp/ark-sessions/
  
security:
  require_mutual_tls: false  # Set to true for production
  allowed_usb_fingerprints: []
EOF

echo ""
echo "4️⃣  Creating systemd services..."

# Redis service
cat > /etc/systemd/system/ark-redis.service << 'EOF'
[Unit]
Description=ARK Redis Cache
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/redis-server --bind 127.0.0.1 --port 6379 --maxmemory 2gb --maxmemory-policy allkeys-lru
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Ollama service
cat > /etc/systemd/system/ark-ollama.service << 'EOF'
[Unit]
Description=ARK Ollama LLM Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/ollama serve
Environment="OLLAMA_HOST=127.0.0.1:11434"
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# ARK host service
cat > /etc/systemd/system/ark-host.service << 'EOF'
[Unit]
Description=ARK Host Service
After=network.target ark-redis.service ark-ollama.service
Requires=ark-redis.service ark-ollama.service

[Service]
Type=simple
WorkingDirectory=/opt/ark-host
ExecStart=/usr/bin/node /opt/ark-host/bin/intelligent-backend.cjs
Restart=always
Environment="PORT=8000"
Environment="REDIS_URL=redis://127.0.0.1:6379"
Environment="OLLAMA_HOST=http://127.0.0.1:11434"

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "5️⃣  Enabling and starting services..."
systemctl daemon-reload
systemctl enable ark-redis ark-ollama
systemctl start ark-redis ark-ollama

echo ""
echo "6️⃣  Setting up AI models..."
# Wait for ollama to start
sleep 5

# Ask user which model to download
echo ""
echo "📦 Choose an AI model for ARK:"
echo ""
echo "  1) llama3.2:1b     - Fastest, smallest (1.3GB) [RECOMMENDED for testing]"
echo "  2) llama3.2:3b     - Balanced (2GB)"
echo "  3) qwen2.5:3b      - Better reasoning (2.5GB)"
echo "  4) phi3:mini       - Microsoft, fast (2.4GB)"
echo "  5) llama3.1:8b     - High quality (4.7GB)"
echo "  6) mistral:7b      - Very capable (4.1GB)"
echo "  7) codellama:7b    - Best for coding (3.8GB)"
echo "  8) Skip            - Download manually later"
echo ""

# If running non-interactively, default to smallest
if [ -t 0 ]; then
    read -p "Enter choice [1-8] (default: 1): " model_choice
    model_choice=${model_choice:-1}
else
    model_choice=1
    echo "Non-interactive mode: Selecting option 1 (llama3.2:1b)"
fi

case $model_choice in
    1)
        MODEL="llama3.2:1b"
        echo "⬇️  Downloading llama3.2:1b (1.3GB) - Fast and efficient..."
        ;;
    2)
        MODEL="llama3.2:3b"
        echo "⬇️  Downloading llama3.2:3b (2GB) - Balanced performance..."
        ;;
    3)
        MODEL="qwen2.5:3b"
        echo "⬇️  Downloading qwen2.5:3b (2.5GB) - Enhanced reasoning..."
        ;;
    4)
        MODEL="phi3:mini"
        echo "⬇️  Downloading phi3:mini (2.4GB) - Microsoft's efficient model..."
        ;;
    5)
        MODEL="llama3.1:8b"
        echo "⬇️  Downloading llama3.1:8b (4.7GB) - High quality responses..."
        ;;
    6)
        MODEL="mistral:7b"
        echo "⬇️  Downloading mistral:7b (4.1GB) - Very capable model..."
        ;;
    7)
        MODEL="codellama:7b"
        echo "⬇️  Downloading codellama:7b (3.8GB) - Optimized for code..."
        ;;
    8)
        echo "⏭️  Skipping model download. Install later with:"
        echo "   ollama pull llama3.2:1b"
        MODEL=""
        ;;
    *)
        echo "⚠️  Invalid choice, defaulting to llama3.2:1b..."
        MODEL="llama3.2:1b"
        ;;
esac

if [ -n "$MODEL" ]; then
    echo ""
    echo "📥 Downloading $MODEL..."
    echo "   This may take a few minutes depending on your connection..."
    echo ""
    
    if ollama pull "$MODEL"; then
        echo "✅ Model $MODEL downloaded successfully!"
        
        # Update config to use this model
        sed -i "s/- llama2/- $MODEL/" /opt/ark-host/config.yaml
        
        # Test the model
        echo ""
        echo "🧪 Testing model..."
        if echo "Hello, test message" | ollama run "$MODEL" --verbose 2>/dev/null | head -1; then
            echo "✅ Model is working!"
        else
            echo "⚠️  Model test inconclusive, but should work when needed"
        fi
    else
        echo "⚠️  Model download failed. You can download it later with:"
        echo "   ollama pull $MODEL"
    fi
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║            ✅ ARK HOST SERVICE INSTALLED! ✅                         ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Services Status:"
systemctl status ark-redis --no-pager | head -3
systemctl status ark-ollama --no-pager | head -3
echo ""
echo "🎯 Host is ready for ARK USB connections!"
echo ""
echo "🚀 Next Steps:"
echo "   1. Plug in your ARK USB drive"
echo "   2. Run: /media/ark/client/bin/ark-client"
echo "   3. Access UI: http://localhost:3000"
echo ""
echo "📖 Configuration: /opt/ark-host/config.yaml"
echo "📊 Logs: /opt/ark-host/logs/"
echo ""
echo "🔧 Manage Services:"
echo "   systemctl status ark-redis"
echo "   systemctl status ark-ollama"
echo "   systemctl status ark-host"
echo ""
