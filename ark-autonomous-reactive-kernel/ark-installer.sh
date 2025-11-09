#!/bin/bash
set -e

# A.R.K. (Autonomous Reactive Kernel) Installer
# One-click installation with hardware detection

echo "🌌 A.R.K. - Autonomous Reactive Kernel"
echo "    Installing your sovereign intelligence..."
echo ""

# Detect architecture
ARCH=$(uname -m)
if [[ "$ARCH" == "x86_64" ]]; then
    HARDWARE="dell"
    MODEL_SIZE="heavy"
elif [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
    HARDWARE="pi"
    MODEL_SIZE="light"
else
    echo "❌ Unsupported architecture: $ARCH"
    exit 1
fi

echo "🔍 Detected: $HARDWARE ($ARCH) - $MODEL_SIZE models"

# Create ARK directory
ARK_DIR="$HOME/ark"
mkdir -p "$ARK_DIR"
cd "$ARK_DIR"

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo "🚀 Starting A.R.K. services..."
docker-compose up -d

echo "⚡ Creating systemd service..."
sudo tee /etc/systemd/system/ark.service > /dev/null <<EOF
[Unit]
Description=A.R.K. Autonomous Reactive Kernel
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=$ARK_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable ark.service
sudo systemctl start ark.service

echo ""
echo "✨ A.R.K. is now awakening..."
echo "🌐 Access your council at: http://localhost:3000"
echo "📱 Telegram bot will be available once configured"
echo ""
echo "🔥 The Council of Consciousness awaits..."