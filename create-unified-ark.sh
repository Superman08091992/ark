#!/bin/bash
##############################################################################
# Create Unified ARK Installation Package
# Combines everything into one self-contained program
##############################################################################

set -e

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║          Create Unified ARK Installation Package                     ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/ark-unified"
PACKAGE_NAME="ark-complete-$(date +%Y%m%d).tar.gz"

# Create output directory
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "1️⃣  Collecting all ARK components..."

# Core structure
mkdir -p "$OUTPUT_DIR"/{bin,lib,data,config,docs}

# Copy backend
echo "   📦 Backend..."
cp -r "$SCRIPT_DIR"/*.cjs "$OUTPUT_DIR/lib/" 2>/dev/null || true
cp -r "$SCRIPT_DIR"/intelligent-backend.cjs "$OUTPUT_DIR/lib/" 2>/dev/null || true
cp -r "$SCRIPT_DIR"/agent_tools.cjs "$OUTPUT_DIR/lib/" 2>/dev/null || true

# Copy agents
echo "   🤖 Agents..."
if [ -d "$SCRIPT_DIR/agents" ]; then
    cp -r "$SCRIPT_DIR/agents" "$OUTPUT_DIR/lib/"
fi
if [ -d "$SCRIPT_DIR/joey" ]; then
    cp -r "$SCRIPT_DIR/joey" "$OUTPUT_DIR/lib/agents/"
fi

# Copy frontend (if exists)
echo "   🎨 Frontend..."
if [ -d "$SCRIPT_DIR/src" ]; then
    mkdir -p "$OUTPUT_DIR/lib/web"
    cp -r "$SCRIPT_DIR/src" "$OUTPUT_DIR/lib/web/"
fi
if [ -d "$SCRIPT_DIR/public" ]; then
    cp -r "$SCRIPT_DIR/public" "$OUTPUT_DIR/lib/web/"
fi
if [ -f "$SCRIPT_DIR/astro.config.mjs" ]; then
    cp "$SCRIPT_DIR/astro.config.mjs" "$OUTPUT_DIR/lib/web/"
fi

# Copy data directories
echo "   💾 Data..."
if [ -d "$SCRIPT_DIR/knowledge_base" ]; then
    cp -r "$SCRIPT_DIR/knowledge_base" "$OUTPUT_DIR/data/"
fi
if [ -d "$SCRIPT_DIR/kyle_infinite_memory" ]; then
    cp -r "$SCRIPT_DIR/kyle_infinite_memory" "$OUTPUT_DIR/data/"
fi

# Copy dependencies
echo "   📦 Dependencies..."
if [ -d "$SCRIPT_DIR/deps" ]; then
    cp -r "$SCRIPT_DIR/deps" "$OUTPUT_DIR/"
fi

# Copy docs
echo "   📚 Documentation..."
for doc in "$SCRIPT_DIR"/*.md; do
    if [ -f "$doc" ]; then
        cp "$doc" "$OUTPUT_DIR/docs/"
    fi
done

echo "✅ Components collected"

echo ""
echo "2️⃣  Creating unified installer..."

# Create main install script
cat > "$OUTPUT_DIR/install.sh" << 'INSTALL_EOF'
#!/bin/bash
##############################################################################
# ARK Unified Installer
# Installs complete ARK system anywhere
##############################################################################

set -e

VERSION="1.0.0"
INSTALL_DIR="${1:-/opt/ark}"

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║              ARK Unified Installer v${VERSION}                       ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Detect OS FIRST
if [ -f /etc/arch-release ]; then
    OS="arch"
elif [ -f /etc/debian_version ]; then
    OS="debian"
elif [ -f /etc/redhat-release ]; then
    OS="redhat"
elif [ "$(uname)" == "Darwin" ]; then
    OS="macos"
elif [ "$(uname -o 2>/dev/null)" == "Android" ]; then
    OS="android"
else
    OS="unknown"
fi

echo "📋 Detected OS: $OS"
echo "📁 Installation directory: $INSTALL_DIR"
echo ""

# Check if running as root (skip on Android/Termux)
if [ "$OS" != "android" ]; then
    if [ "$EUID" -ne 0 ] && [ ! -w "$(dirname "$INSTALL_DIR")" ]; then
        if command -v sudo &> /dev/null; then
            echo "⚠️  This script needs sudo privileges for system installation"
            echo "   Re-running with sudo..."
            exec sudo bash "$0" "$@"
        else
            echo "⚠️  No sudo available and cannot write to $INSTALL_DIR"
            echo "   Please either:"
            echo "   1. Run with sudo: sudo $0 $@"
            echo "   2. Install to user directory: $0 ~/ark"
            exit 1
        fi
    fi
fi

# Get script directory (where files are extracted)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "1️⃣  Installing dependencies..."

# Check for bundled Node.js
if [ -d "$SCRIPT_DIR/deps/node/nodejs" ]; then
    echo "✅ Using bundled Node.js"
    NODE_PATH="$SCRIPT_DIR/deps/node/nodejs/bin"
else
    echo "⬇️  Installing Node.js..."
    case $OS in
        debian|android)
            if command -v apt-get &> /dev/null; then
                apt-get update && apt-get install -y nodejs npm
            elif command -v pkg &> /dev/null; then
                pkg install -y nodejs
            fi
            ;;
        arch)
            pacman -Sy --needed --noconfirm nodejs npm
            ;;
        macos)
            brew install node
            ;;
    esac
    NODE_PATH=$(which node | xargs dirname)
fi

# Check for bundled Redis
if [ -d "$SCRIPT_DIR/deps/redis/bin" ]; then
    echo "✅ Using bundled Redis"
    REDIS_PATH="$SCRIPT_DIR/deps/redis/bin"
else
    echo "⬇️  Installing Redis..."
    case $OS in
        debian)
            apt-get update && apt-get install -y redis-server
            ;;
        android)
            pkg install -y redis
            ;;
        arch)
            pacman -Sy --needed --noconfirm redis
            ;;
        macos)
            brew install redis
            ;;
    esac
    REDIS_PATH=$(which redis-server | xargs dirname 2>/dev/null || echo "")
fi

echo ""
echo "2️⃣  Creating installation directory..."
mkdir -p "$INSTALL_DIR"/{bin,lib,data,config,logs,docs}

echo ""
echo "3️⃣  Copying ARK files..."

# Copy lib directory
if [ -d "$SCRIPT_DIR/lib" ] && [ "$(ls -A "$SCRIPT_DIR/lib" 2>/dev/null)" ]; then
    cp -r "$SCRIPT_DIR/lib"/* "$INSTALL_DIR/lib/"
    echo "   ✅ Copied lib/ directory"
else
    echo "   ⚠️  Warning: lib/ directory empty or missing"
    echo "   This may cause ARK to not function properly!"
fi

# Copy data directory
if [ -d "$SCRIPT_DIR/data" ] && [ "$(ls -A "$SCRIPT_DIR/data" 2>/dev/null)" ]; then
    cp -r "$SCRIPT_DIR/data"/* "$INSTALL_DIR/data/"
    echo "   ✅ Copied data/ directory"
else
    echo "   ℹ️  Note: data/ directory empty (will be created on first run)"
fi

# Copy docs directory
if [ -d "$SCRIPT_DIR/docs" ] && [ "$(ls -A "$SCRIPT_DIR/docs" 2>/dev/null)" ]; then
    cp -r "$SCRIPT_DIR/docs"/* "$INSTALL_DIR/docs/"
    echo "   ✅ Copied docs/ directory"
else
    echo "   ℹ️  Note: docs/ directory empty"
fi

# Copy dependencies if bundled
if [ -d "$SCRIPT_DIR/deps" ]; then
    cp -r "$SCRIPT_DIR/deps" "$INSTALL_DIR/"
    echo "   ✅ Copied bundled dependencies"
fi

echo ""
echo "4️⃣  Creating launcher scripts..."

# Create ark command
cat > "$INSTALL_DIR/bin/ark" << 'ARK_EOF'
#!/bin/bash
# ARK Main Launcher

ARK_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Set up environment
export ARK_HOME
export PATH="$ARK_HOME/deps/node/nodejs/bin:$PATH"

# Start ARK backend
cd "$ARK_HOME/lib"
exec node intelligent-backend.cjs "$@"
ARK_EOF

chmod +x "$INSTALL_DIR/bin/ark"

# Create ark-web command (if frontend exists)
if [ -d "$INSTALL_DIR/lib/web" ]; then
    cat > "$INSTALL_DIR/bin/ark-web" << 'WEB_EOF'
#!/bin/bash
# ARK Web Interface

ARK_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$ARK_HOME/deps/node/nodejs/bin:$PATH"

cd "$ARK_HOME/lib/web"
exec npm run dev
WEB_EOF
    chmod +x "$INSTALL_DIR/bin/ark-web"
fi

# Create ark-redis command
cat > "$INSTALL_DIR/bin/ark-redis" << 'REDIS_EOF'
#!/bin/bash
# ARK Redis Server

ARK_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -f "$ARK_HOME/deps/redis/bin/redis-server" ]; then
    exec "$ARK_HOME/deps/redis/bin/redis-server" "$@"
else
    exec redis-server "$@"
fi
REDIS_EOF

chmod +x "$INSTALL_DIR/bin/ark-redis"

# Verify launcher scripts were created
echo ""
echo "🔍 Verifying launcher scripts..."
LAUNCHERS_OK=true
for script in ark ark-redis; do
    if [ -f "$INSTALL_DIR/bin/$script" ] && [ -x "$INSTALL_DIR/bin/$script" ]; then
        echo "   ✅ $script created and executable"
    else
        echo "   ❌ ERROR: $script missing or not executable"
        LAUNCHERS_OK=false
    fi
done

if [ "$LAUNCHERS_OK" = false ]; then
    echo ""
    echo "⚠️  Launcher script creation failed!"
    echo "   Installation cannot continue."
    exit 1
fi

echo ""
echo "5️⃣  Creating configuration..."

cat > "$INSTALL_DIR/config/ark.conf" << 'CONF_EOF'
# ARK Configuration

[server]
host = 0.0.0.0
port = 8000

[redis]
host = 127.0.0.1
port = 6379

[data]
knowledge_base = data/knowledge_base
kyle_memory = data/kyle_infinite_memory
agent_logs = data/agent_logs

[llm]
provider = ollama
model = llama3.2:1b
host = http://127.0.0.1:11434
CONF_EOF

echo ""
echo "6️⃣  Setting up PATH..."

# Add to PATH for current session
export PATH="$INSTALL_DIR/bin:$PATH"

# Detect shell and add to PATH
SHELL_RC=""
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if [ -n "$SHELL_RC" ] && [ -f "$SHELL_RC" ]; then
    if ! grep -q "ARK_HOME" "$SHELL_RC"; then
        # Write directly to shell rc file (avoid /tmp issues on Termux)
        cat >> "$SHELL_RC" << PROFILE_EOF

# ARK Configuration
export PATH="$INSTALL_DIR/bin:\$PATH"
export ARK_HOME="$INSTALL_DIR"
PROFILE_EOF
        echo "✅ Added ARK to $SHELL_RC"
    else
        echo "ℹ️  ARK already in $SHELL_RC"
    fi
else
    echo "⚠️  Could not detect shell RC file. Add manually:"
    echo "   export PATH=\"$INSTALL_DIR/bin:\$PATH\""
    echo "   export ARK_HOME=\"$INSTALL_DIR\""
fi

echo ""
echo "7️⃣  Verifying installation..."

# Check critical files exist
REQUIRED_FILES=(
    "$INSTALL_DIR/bin/ark"
    "$INSTALL_DIR/bin/ark-redis"
    "$INSTALL_DIR/config/ark.conf"
)

INSTALL_OK=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $(basename "$file")"
    else
        echo "   ❌ MISSING: $file"
        INSTALL_OK=false
    fi
done

# Check if bundled Node.js is accessible
if [ -d "$INSTALL_DIR/deps/node/nodejs/bin" ]; then
    if [ -x "$INSTALL_DIR/deps/node/nodejs/bin/node" ]; then
        NODE_VERSION=$("$INSTALL_DIR/deps/node/nodejs/bin/node" --version 2>/dev/null || echo "unknown")
        echo "   ✅ Node.js ($NODE_VERSION)"
    else
        echo "   ⚠️  Node.js binary not executable"
        INSTALL_OK=false
    fi
fi

# Check if bundled Redis is accessible
if [ -d "$INSTALL_DIR/deps/redis/bin" ]; then
    if [ -x "$INSTALL_DIR/deps/redis/bin/redis-server" ]; then
        REDIS_VERSION=$("$INSTALL_DIR/deps/redis/bin/redis-server" --version 2>/dev/null | head -n1 || echo "unknown")
        echo "   ✅ Redis ($REDIS_VERSION)"
    else
        echo "   ⚠️  Redis binary not executable"
        INSTALL_OK=false
    fi
fi

if [ "$INSTALL_OK" = false ]; then
    echo ""
    echo "⚠️  Installation incomplete! Some files are missing or not functional."
    echo "   Please report this issue with the above error messages."
    echo ""
    echo "   Installation directory: $INSTALL_DIR"
    echo "   You may need to:"
    echo "   1. Check file permissions: ls -la $INSTALL_DIR"
    echo "   2. Verify disk space: df -h"
    echo "   3. Re-run installation"
    exit 1
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║              ✅ ARK INSTALLATION COMPLETE! ✅                        ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Installation location: $INSTALL_DIR"
echo ""
echo "🚀 Available commands:"
echo "   ark          - Start ARK backend"
echo "   ark-web      - Start web interface (if installed)"
echo "   ark-redis    - Start Redis server"
echo ""
echo "📝 Configuration: $INSTALL_DIR/config/ark.conf"
echo "💾 Data location: $INSTALL_DIR/data/"
echo "📚 Documentation: $INSTALL_DIR/docs/"
echo ""
echo "🎯 Quick start:"
echo "   1. Start Redis:  ark-redis"
echo "   2. Start ARK:    ark"
echo "   3. Access:       http://localhost:8000"
echo ""
echo "💡 Add to PATH permanently:"
echo "   source ~/.bashrc   # or restart terminal"
echo ""
INSTALL_EOF

chmod +x "$OUTPUT_DIR/install.sh"

echo "✅ Installer created"

echo ""
echo "3️⃣  Creating README..."

cat > "$OUTPUT_DIR/README.md" << 'README_EOF'
# ARK - Unified Installation Package

Complete ARK system in a single package.

## Contents

- **Backend:** Intelligent backend with AI agents
- **Frontend:** Web interface (Astro + React)
- **Agents:** Kyle and other AI agents
- **Dependencies:** Node.js and Redis (bundled)
- **Data:** Knowledge base and agent memories
- **Documentation:** Complete guides

## Installation

### Quick Install (Default location: /opt/ark)

```bash
sudo ./install.sh
```

### Custom Installation Location

```bash
sudo ./install.sh /your/custom/path
```

### Without Sudo (User installation)

```bash
./install.sh ~/ark
```

## Usage

After installation:

```bash
# Start Redis
ark-redis &

# Start ARK backend
ark

# Start web interface (in another terminal)
ark-web
```

Access at: http://localhost:8000

## System Requirements

- **OS:** Linux, macOS, Android (Termux)
- **RAM:** 4GB+ recommended
- **Disk:** 500MB for core, 2GB+ with AI models
- **Ports:** 8000 (API), 6379 (Redis), 4321 (Web)

## What's Included

### Bundled Dependencies (No Download)
- Node.js v20.10.0 (168MB)
- Redis v7.2.4 (13MB)

### Requires Internet
- Ollama (~200MB) - for AI features
- AI Model (~1.3GB+) - your choice of model

## Features

- ✅ Self-contained installation
- ✅ Works offline (after initial setup)
- ✅ Portable - copy to USB and run anywhere
- ✅ No system dependencies
- ✅ Multi-platform support

## Directory Structure

```
/opt/ark/  (or your chosen location)
├── bin/           # Executable commands
├── lib/           # Backend and agents
├── data/          # Knowledge base and memories
├── config/        # Configuration files
├── docs/          # Documentation
├── deps/          # Bundled Node.js and Redis
└── logs/          # Application logs
```

## Configuration

Edit: `/opt/ark/config/ark.conf`

## Uninstallation

```bash
sudo rm -rf /opt/ark
# Remove from PATH in ~/.bashrc or ~/.zshrc
```

## Support

- GitHub: https://github.com/Superman08091992/ark
- Issues: https://github.com/Superman08091992/ark/issues

## Version

1.0.0 - Complete unified installation
README_EOF

echo "✅ README created"

echo ""
echo "4️⃣  Creating package..."

cd "$(dirname "$OUTPUT_DIR")"
tar -czf "$PACKAGE_NAME" "$(basename "$OUTPUT_DIR")"

PACKAGE_SIZE=$(du -h "$PACKAGE_NAME" | cut -f1)

echo "✅ Package created"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║            ✅ UNIFIED ARK PACKAGE CREATED! ✅                        ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Package: $PACKAGE_NAME"
echo "📊 Size: $PACKAGE_SIZE"
echo "📁 Location: $(pwd)/$PACKAGE_NAME"
echo ""
echo "🚀 Distribution:"
echo "   1. Upload to GitHub releases"
echo "   2. Copy to USB drive"
echo "   3. Share the file"
echo ""
echo "💿 To install on any system:"
echo "   tar -xzf $PACKAGE_NAME"
echo "   cd $(basename "$OUTPUT_DIR")"
echo "   sudo ./install.sh"
echo ""
echo "✨ This package can be installed ANYWHERE!"
