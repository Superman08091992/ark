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

case $OS in
    arch)
        pacman -Sy --needed --noconfirm nodejs redis ollama
        ;;
    debian)
        apt update
        apt install -y nodejs npm redis-server
        # Ollama
        curl -fsSL https://ollama.ai/install.sh | sh
        ;;
    macos)
        brew install node redis
        brew install ollama
        ;;
    *)
        echo "❌ Package installation not implemented for $OS"
        exit 1
        ;;
esac

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
echo "6️⃣  Downloading Ollama model (this may take a while)..."
# Wait for ollama to start
sleep 5
ollama pull llama2 || echo "⚠️  Model download failed, will retry later"

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
