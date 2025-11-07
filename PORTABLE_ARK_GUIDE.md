# Portable ARK: Plug-and-Play AI on USB/SD Card

## 🎯 Goal

Create a **fully portable, self-contained ARK system** that:
- Runs entirely from USB flash drive or SD card
- Auto-boots when plugged in
- No installation required on host machine
- Includes Kyle's infinite memory + LLM integration
- Self-building and learning AI system
- All data persists on the portable drive

---

## 📋 Best Options for Portable ARK

### **Option 1: Docker-Based Portable ARK (RECOMMENDED)** ⭐

**Best for:** Cross-platform (Windows, Mac, Linux), easiest setup

**Requirements:**
- USB drive/SD card: 8GB+ (16GB+ recommended)
- Docker installed on host machine (one-time install)

**Advantages:**
- ✅ Works on any OS with Docker
- ✅ Isolated environment
- ✅ Easy to update
- ✅ All data on portable drive
- ✅ Auto-start with single command

**Setup:**
```bash
# 1. Format USB as exFAT (cross-platform compatible)
# 2. Copy ARK to USB
# 3. Run from USB
```

---

### **Option 2: Raspberry Pi Image (TRUE PLUG-AND-PLAY)** 🥧

**Best for:** Complete hardware independence, no host needed

**Requirements:**
- Raspberry Pi 4/5 (4GB+ RAM recommended)
- SD card: 32GB+ (for OS + ARK + Ollama)
- Power supply

**Advantages:**
- ✅ **Truly standalone** - no host computer needed
- ✅ Boot directly from SD card
- ✅ Built-in networking
- ✅ Low power consumption
- ✅ Can run 24/7
- ✅ Access via web browser from any device

**Perfect for:** Portable AI assistant you can carry anywhere

---

### **Option 3: Linux Live USB (BOOTABLE OS)** 💿

**Best for:** Maximum portability, boot any computer

**Requirements:**
- USB drive: 32GB+ (64GB recommended)
- Ventoy or Rufus for creating bootable USB

**Advantages:**
- ✅ Boot any x86 computer from USB
- ✅ Full Linux OS + ARK + Ollama
- ✅ No installation on host
- ✅ Persistent storage
- ✅ Complete isolation

**Perfect for:** Running ARK on any computer without installation

---

## 🚀 Implementation: Option 1 (Docker Portable ARK)

### Step 1: Prepare USB Drive

```bash
# Format USB as exFAT (works on Windows, Mac, Linux)
# On Mac:
diskutil list
diskutil eraseDisk exFAT ARK_AI disk2  # Replace disk2 with your USB

# On Linux:
sudo mkfs.exfat -n ARK_AI /dev/sdb1  # Replace sdb1 with your USB

# On Windows:
# Format via GUI: Right-click drive → Format → exFAT
```

### Step 2: Create Portable ARK Structure

```bash
# Mount USB (example: /Volumes/ARK_AI or D:\ on Windows)
cd /Volumes/ARK_AI  # or your USB mount point

# Copy ARK project
cp -r /home/user/webapp/. ./ark-system/

# Create launcher script
cat > start-ark.sh << 'EOF'
#!/bin/bash
# Portable ARK Launcher

# Get script directory (USB mount point)
USB_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$USB_DIR/ark-system"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    echo "Download: https://www.docker.com/get-started"
    exit 1
fi

# Start ARK
echo "🚀 Starting Portable ARK..."
docker-compose up -d

# Wait for services
sleep 5

# Get URLs
echo ""
echo "✅ ARK is running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "🧠 Ollama: http://localhost:11434"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💾 All data saved to USB drive"
echo "🔌 Safe to unplug after running: docker-compose down"
EOF

chmod +x start-ark.sh

# Windows launcher
cat > start-ark.bat << 'EOF'
@echo off
REM Portable ARK Launcher for Windows

cd /d %~dp0\ark-system

REM Check Docker
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Docker not found. Please install Docker Desktop.
    echo Download: https://www.docker.com/get-started
    pause
    exit /b 1
)

REM Start ARK
echo Starting Portable ARK...
docker-compose up -d

REM Wait
timeout /t 5 /nobreak >nul

echo.
echo ARK is running!
echo ============================================
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo Ollama: http://localhost:11434
echo ============================================
echo.
echo All data saved to USB drive
echo To stop: docker-compose down
pause
EOF
```

### Step 3: Configure Docker Compose for Portable Storage

Create `ark-system/docker-compose-portable.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.core
    ports:
      - "8000:8000"
    volumes:
      - ./kyle_infinite_memory:/app/kyle_infinite_memory
      - ./knowledge_base:/app/knowledge_base
      - ./agent_logs:/app/agent_logs
      - ./data:/app/data
    environment:
      - OLLAMA_HOST=http://ollama:11434
    networks:
      - ark-network
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - ark-network
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ./ollama_data:/root/.ollama
    networks:
      - ark-network
    restart: unless-stopped
    # Pull llama2 on first start
    command: sh -c "ollama serve & sleep 10 && ollama pull llama2 && wait"

networks:
  ark-network:
    driver: bridge

volumes:
  kyle_infinite_memory:
  knowledge_base:
  agent_logs:
  ollama_data:
```

### Step 4: Create Auto-Setup Script

```bash
cat > ark-system/setup-portable.sh << 'EOF'
#!/bin/bash
# Auto-setup for Portable ARK

echo "🔧 Setting up Portable ARK..."

# Create necessary directories
mkdir -p kyle_infinite_memory
mkdir -p knowledge_base
mkdir -p agent_logs
mkdir -p ollama_data
mkdir -p data

# Initialize empty JSON files if not exist
[ ! -f kyle_infinite_memory/catalog.json ] && echo "{}" > kyle_infinite_memory/catalog.json
[ ! -f kyle_infinite_memory/master_index.json ] && echo "{}" > kyle_infinite_memory/master_index.json
[ ! -f knowledge_base/knowledge_graph.json ] && echo '{"nodes":{}, "edges":[]}' > knowledge_base/knowledge_graph.json

echo "✅ Setup complete!"
echo "Run ./start-ark.sh (Mac/Linux) or start-ark.bat (Windows)"
EOF

chmod +x ark-system/setup-portable.sh
```

### Step 5: Test Portable ARK

```bash
# On USB drive
cd /Volumes/ARK_AI  # or your USB mount

# Setup
./ark-system/setup-portable.sh

# Start
./start-ark.sh

# Test
curl http://localhost:8000/api/agents

# Stop
cd ark-system && docker-compose down
```

---

## 🥧 Implementation: Option 2 (Raspberry Pi SD Card Image)

### Step 1: Prepare Raspberry Pi OS

```bash
# Download Raspberry Pi OS Lite (64-bit)
# Use Raspberry Pi Imager: https://www.raspberrypi.com/software/

# Configure:
# - Set hostname: ark-ai
# - Enable SSH
# - Set username/password
# - Configure WiFi (optional)

# Flash to SD card
```

### Step 2: Install Dependencies on Pi

```bash
# SSH into Pi
ssh pi@ark-ai.local

# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Docker (optional, for Ollama)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker pi

# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama2
```

### Step 3: Install ARK on Pi

```bash
# Copy ARK to Pi
scp -r /home/user/webapp pi@ark-ai.local:~/ark-system

# Or clone from GitHub
ssh pi@ark-ai.local
git clone https://github.com/Superman08091992/ark.git ~/ark-system
cd ~/ark-system
git checkout genspark_ai_developer
```

### Step 4: Create Auto-Start Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/ark.service
```

```ini
[Unit]
Description=ARK Intelligent System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ark-system
ExecStart=/usr/bin/node /home/pi/ark-system/intelligent-backend.cjs
Restart=always
RestartSec=10
Environment=OLLAMA_HOST=http://localhost:11434
Environment=OLLAMA_MODEL=llama2

[Install]
WantedBy=multi-user.target
```

```bash
# Enable auto-start
sudo systemctl enable ark.service
sudo systemctl start ark.service

# Check status
sudo systemctl status ark.service

# View logs
sudo journalctl -u ark.service -f
```

### Step 5: Access ARK from Network

```bash
# Find Pi's IP
hostname -I

# Access from any device on same network
# Browser: http://192.168.1.XXX:8000
# API: curl http://192.168.1.XXX:8000/api/agents
```

### Step 6: Create Backup/Restore Scripts

```bash
cat > ~/ark-system/backup-ark.sh << 'EOF'
#!/bin/bash
# Backup ARK data

BACKUP_DIR="$HOME/ark-backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp -r ~/ark-system/kyle_infinite_memory "$BACKUP_DIR/"
cp -r ~/ark-system/knowledge_base "$BACKUP_DIR/"
cp -r ~/ark-system/agent_logs "$BACKUP_DIR/"

echo "✅ Backup saved to: $BACKUP_DIR"
EOF

chmod +x ~/ark-system/backup-ark.sh

# Add to cron for daily backups
crontab -e
# Add: 0 2 * * * /home/pi/ark-system/backup-ark.sh
```

---

## 💿 Implementation: Option 3 (Bootable Linux USB)

### Step 1: Download Ubuntu/Debian Live

```bash
# Download Ubuntu 22.04 LTS (or Debian)
# ISO: https://ubuntu.com/download/desktop
```

### Step 2: Create Persistent USB with Ventoy

```bash
# Install Ventoy on USB
# Download: https://www.ventoy.net/

# Run Ventoy installer
# Select USB drive
# Install with persistence

# Copy Ubuntu ISO to USB
# Ventoy will auto-detect it
```

### Step 3: Boot and Install ARK

```bash
# Boot from USB
# Select "Try Ubuntu" with persistence

# Open terminal
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs git

# Install Ollama
curl https://ollama.ai/install.sh | sh

# Clone ARK
git clone https://github.com/Superman08091992/ark.git ~/ark-system
cd ~/ark-system

# Setup
npm install
```

### Step 4: Create Auto-Start Script

```bash
# Add to ~/.bashrc
echo 'cd ~/ark-system && node intelligent-backend.cjs &' >> ~/.bashrc

# Or create desktop shortcut
cat > ~/Desktop/start-ark.sh << 'EOF'
#!/bin/bash
cd ~/ark-system
node intelligent-backend.cjs
EOF

chmod +x ~/Desktop/start-ark.sh
```

---

## 📊 Comparison of Options

| Feature | Docker Portable | Raspberry Pi | Bootable USB |
|---------|----------------|--------------|--------------|
| **Setup Complexity** | ⭐⭐ Easy | ⭐⭐⭐ Medium | ⭐⭐⭐⭐ Complex |
| **Hardware Cost** | $10 (USB) | $60-120 (Pi+SD) | $20 (USB) |
| **True Standalone** | ❌ (needs host) | ✅ Yes | ❌ (needs host) |
| **Cross-Platform** | ✅ Yes | ✅ Yes | ⚠️ x86 only |
| **Auto-Boot** | ⚠️ Manual | ✅ Yes | ✅ Yes |
| **Network Access** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Storage** | USB size | SD card size | USB size |
| **Performance** | Host CPU | Pi CPU | Host CPU |
| **24/7 Operation** | ❌ No | ✅ Yes | ❌ No |

---

## 🏆 RECOMMENDED: Docker Portable ARK

**Why?**
- Easiest to set up
- Works on any OS
- Good performance
- Easy updates
- Low cost

**Storage Layout:**
```
ARK_AI (USB Drive)
├── start-ark.sh              # Mac/Linux launcher
├── start-ark.bat             # Windows launcher
├── stop-ark.sh               # Shutdown script
├── README.txt                # Quick start guide
└── ark-system/
    ├── docker-compose.yml
    ├── intelligent-backend.cjs
    ├── agent_tools.cjs
    ├── frontend/
    ├── kyle_infinite_memory/  # Persistent storage
    ├── knowledge_base/        # Persistent storage
    ├── agent_logs/            # Persistent storage
    ├── ollama_data/           # Ollama models
    └── data/                  # User data
```

**All data persists on USB drive** - plug and play on any computer with Docker!

---

## 🎯 Next Steps

Choose your option and I'll create the complete setup for you:

1. **Docker Portable ARK** - Ready to run on any computer
2. **Raspberry Pi SD Image** - True standalone AI
3. **Bootable Linux USB** - Boot any x86 computer

Let me know which option you prefer, and I'll create the complete implementation!
