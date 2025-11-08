# Create Unified ARK Installation Package

## 🎯 What This Does

Creates a single, self-contained ARK package that you can:
- ✅ Install anywhere (Linux, macOS, Android/Termux)
- ✅ Copy to USB and run on any machine
- ✅ Share as one file
- ✅ No separate dependencies needed

## 📦 What's Included

- **Backend** - Intelligent backend + agents
- **Frontend** - Web UI (Astro + React)
- **Dependencies** - Node.js + Redis (bundled!)
- **Data** - Knowledge base + agent memories
- **Docs** - All documentation
- **Installer** - One-command install script

## 🚀 How to Create the Package

### On Your Computer (Sandbox):

```bash
cd ~/ark  # or wherever your ark repo is

# Run the unified package creator
./create-unified-ark.sh

# Output: ark-complete-YYYYMMDD.tar.gz
# Size: ~200-300MB (includes Node.js + Redis)
```

### On Termux (Android):

```bash
cd ~/ark

# Pull latest code
git pull origin master

# Run the creator
./create-unified-ark.sh

# Package will be created in current directory
```

## 📥 How to Install the Package

### On Any Linux/Mac:

```bash
# Extract the package
tar -xzf ark-complete-20251108.tar.gz

# Go into directory
cd ark-unified

# Install (default location: /opt/ark)
sudo ./install.sh

# Or install to custom location
sudo ./install.sh /your/custom/path

# Or install without sudo (user installation)
./install.sh ~/ark
```

### On Android/Termux:

```bash
# Extract
tar -xzf ark-complete-20251108.tar.gz

# Install (no sudo needed on Android)
cd ark-unified
./install.sh ~/ark

# Add to PATH
echo 'export PATH="$HOME/ark/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## 🎮 Using ARK After Installation

### Start ARK:

```bash
# Start Redis (in background)
ark-redis &

# Start ARK backend
ark

# Start web interface (in another terminal)
ark-web
```

### Access:

- **API:** http://localhost:8000
- **Web:** http://localhost:4321

## 📁 Package Structure

```
ark-complete-20251108.tar.gz
└── ark-unified/
    ├── install.sh          # Installation script
    ├── README.md           # Instructions
    ├── bin/                # Will be created on install
    ├── lib/                # Backend + agents + web
    ├── data/               # Knowledge base + memories
    ├── deps/               # Node.js + Redis (bundled!)
    ├── config/             # Configuration templates
    └── docs/               # Documentation
```

## 🎯 After Installation

```
/opt/ark/  (or your chosen location)
├── bin/
│   ├── ark           # Start backend
│   ├── ark-web       # Start web UI
│   └── ark-redis     # Start Redis
├── lib/
│   ├── intelligent-backend.cjs
│   ├── agent_tools.cjs
│   ├── agents/       # Kyle, Joey, etc.
│   └── web/          # Frontend
├── data/
│   ├── knowledge_base/
│   ├── kyle_infinite_memory/
│   └── agent_logs/
├── deps/
│   ├── node/         # Node.js v20.10.0
│   └── redis/        # Redis v7.2.4
├── config/
│   └── ark.conf      # Configuration
└── docs/
    └── *.md          # All documentation
```

## ✅ Features

- ✅ **Self-contained** - Everything in one package
- ✅ **Portable** - Copy to USB, install anywhere
- ✅ **No system deps** - Node + Redis bundled
- ✅ **Multi-platform** - Linux, Mac, Android
- ✅ **Offline capable** - Works without internet (after setup)
- ✅ **Easy uninstall** - Just delete the directory

## 🔄 Updating ARK

```bash
# On Termux/source machine
cd ~/ark
git pull origin master
./create-unified-ark.sh

# Transfer new package to target machines
# Reinstall:
sudo ./install.sh
```

## 💡 Use Cases

### USB Installation Stick
```bash
# Create package
./create-unified-ark.sh

# Copy to USB
cp ark-complete-*.tar.gz /media/usb/

# On any computer, from USB:
tar -xzf /media/usb/ark-complete-*.tar.gz
cd ark-unified
sudo ./install.sh
```

### Deploy to Multiple Servers
```bash
# Create once
./create-unified-ark.sh

# Upload to all servers
scp ark-complete-*.tar.gz user@server1:/tmp/
scp ark-complete-*.tar.gz user@server2:/tmp/

# Install on each
ssh user@server1 "cd /tmp && tar -xzf ark-*.tar.gz && cd ark-unified && sudo ./install.sh"
```

### Personal Backup
```bash
# Create package
./create-unified-ark.sh

# Upload to cloud/backup
cp ark-complete-*.tar.gz ~/Dropbox/
# or
rclone copy ark-complete-*.tar.gz gdrive:backups/
```

## 🆘 Troubleshooting

### Package too large?

The package includes Node.js (168MB) and Redis (13MB). This is intentional for offline capability.

If you want smaller:
- Edit `create-unified-ark.sh`
- Comment out the deps copying section
- Users will need to install Node/Redis separately

### Installation fails?

```bash
# Check permissions
ls -la install.sh
chmod +x install.sh

# Try without sudo (user install)
./install.sh ~/ark

# Check logs
cat /tmp/ark-install.log
```

### Commands not found after install?

```bash
# Manually add to PATH
export PATH="/opt/ark/bin:$PATH"

# Or add to shell profile
echo 'export PATH="/opt/ark/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## 📊 Size Comparison

| Component | Size |
|-----------|------|
| Core ARK code | ~10MB |
| Node.js (bundled) | 168MB |
| Redis (bundled) | 13MB |
| Documentation | ~5MB |
| Data (optional) | Variable |
| **Total Package** | **~200-300MB** |

**Worth it because:**
- ✅ No download during install
- ✅ Consistent versions
- ✅ Works offline
- ✅ Install anywhere

## 🎉 Summary

1. **Create:** `./create-unified-ark.sh`
2. **Get:** `ark-complete-YYYYMMDD.tar.gz`
3. **Install anywhere:** `tar -xzf ... && cd ark-unified && sudo ./install.sh`
4. **Run:** `ark-redis & ; ark`

**One package, infinite possibilities!** 🚀
