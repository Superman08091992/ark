#!/bin/bash
################################################################################
# ARK Enhancement #09: Ollama Auto-Installer
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Automatically installs Ollama and downloads LLM models with a single command.
# Detects platform, installs Ollama, verifies installation, and downloads
# preferred models (llama3.2:1b, mistral, etc.)
#
# FEATURES:
# ---------
# ✅ Cross-platform support (Linux, macOS, Termux/Android)
# ✅ Automatic platform detection
# ✅ Ollama installation with verification
# ✅ Model download with progress tracking
# ✅ Multiple model support
# ✅ Model listing and management
# ✅ Configuration update (.env file)
# ✅ Health checks after installation
# ✅ Service management (start/stop/restart)
#
# USAGE:
# ------
# ark-ollama install              # Install Ollama + default model (llama3.2:1b)
# ark-ollama install mistral      # Install Ollama + specific model
# ark-ollama install llama3.2:1b mistral codellama  # Multiple models
# ark-ollama list                 # List installed models
# ark-ollama pull <model>         # Download additional model
# ark-ollama remove <model>       # Remove a model
# ark-ollama status              # Check Ollama service status
# ark-ollama start               # Start Ollama service
# ark-ollama stop                # Stop Ollama service
# ark-ollama restart             # Restart Ollama service
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ARK home detection
if [ -n "$ARK_HOME" ]; then
    INSTALL_DIR="$ARK_HOME"
elif [ -f "$HOME/.arkrc" ]; then
    INSTALL_DIR=$(grep "ARK_HOME=" "$HOME/.arkrc" | cut -d'=' -f2)
else
    INSTALL_DIR="$HOME/ark"
fi

ENV_FILE="$INSTALL_DIR/.env"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

detect_platform() {
    if [ -d "/data/data/com.termux" ]; then
        echo "termux"
    elif [ "$(uname)" == "Darwin" ]; then
        echo "macos"
    elif [ "$(uname)" == "Linux" ]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            echo "${ID:-linux}"
        else
            echo "linux"
        fi
    else
        echo "unknown"
    fi
}

is_ollama_installed() {
    command -v ollama &>/dev/null
}

is_ollama_running() {
    if ! is_ollama_installed; then
        return 1
    fi
    
    # Try to ping Ollama API
    curl -s http://localhost:11434/api/tags &>/dev/null
}

install_ollama() {
    local platform=$(detect_platform)
    
    print_header "🔧 Installing Ollama"
    
    case $platform in
        termux)
            echo -e "${YELLOW}⚠️  Ollama installation on Termux requires manual steps:${NC}"
            echo ""
            echo "1. Install proot-distro:"
            echo "   pkg install proot-distro"
            echo ""
            echo "2. Install Ubuntu:"
            echo "   proot-distro install ubuntu"
            echo ""
            echo "3. Login to Ubuntu:"
            echo "   proot-distro login ubuntu"
            echo ""
            echo "4. Inside Ubuntu, install Ollama:"
            echo "   curl -fsSL https://ollama.com/install.sh | sh"
            echo ""
            echo "5. Start Ollama:"
            echo "   ollama serve &"
            echo ""
            echo -e "${BLUE}📖 Alternative: Use remote Ollama instance${NC}"
            echo "   Set OLLAMA_HOST in $ENV_FILE:"
            echo "   OLLAMA_HOST=http://your-server:11434"
            return 1
            ;;
            
        macos)
            echo "📥 Installing Ollama for macOS..."
            if ! command -v brew &>/dev/null; then
                echo -e "${YELLOW}⚠️  Homebrew not found. Installing Homebrew first...${NC}"
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install ollama
            ;;
            
        ubuntu|debian)
            echo "📥 Installing Ollama for Linux..."
            curl -fsSL https://ollama.com/install.sh | sh
            ;;
            
        *)
            echo "📥 Installing Ollama (generic Linux)..."
            curl -fsSL https://ollama.com/install.sh | sh
            ;;
    esac
    
    # Verify installation
    if is_ollama_installed; then
        echo -e "${GREEN}✅ Ollama installed successfully!${NC}"
        ollama --version
        return 0
    else
        echo -e "${RED}❌ Ollama installation failed${NC}"
        return 1
    fi
}

start_ollama_service() {
    local platform=$(detect_platform)
    
    echo "🚀 Starting Ollama service..."
    
    if is_ollama_running; then
        echo -e "${GREEN}✅ Ollama is already running${NC}"
        return 0
    fi
    
    case $platform in
        macos)
            # On macOS, Ollama runs as a background service
            ollama serve &>/dev/null &
            ;;
        *)
            # On Linux, check if systemd service exists
            if systemctl list-unit-files | grep -q ollama.service; then
                sudo systemctl start ollama
            else
                # Run in background
                ollama serve &>/dev/null &
            fi
            ;;
    esac
    
    # Wait for service to be ready
    echo -n "⏳ Waiting for Ollama to start"
    for i in {1..30}; do
        if is_ollama_running; then
            echo ""
            echo -e "${GREEN}✅ Ollama service is running${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo ""
    echo -e "${RED}❌ Ollama failed to start${NC}"
    return 1
}

pull_model() {
    local model="$1"
    
    if [ -z "$model" ]; then
        model="llama3.2:1b"
    fi
    
    echo ""
    echo -e "${BLUE}📦 Downloading model: $model${NC}"
    echo -e "${YELLOW}⏳ This may take several minutes depending on model size...${NC}"
    echo ""
    
    if ollama pull "$model"; then
        echo ""
        echo -e "${GREEN}✅ Model '$model' downloaded successfully${NC}"
        
        # Update .env file with model
        update_env_model "$model"
        return 0
    else
        echo ""
        echo -e "${RED}❌ Failed to download model '$model'${NC}"
        return 1
    fi
}

update_env_model() {
    local model="$1"
    
    if [ ! -f "$ENV_FILE" ]; then
        mkdir -p "$(dirname "$ENV_FILE")"
        touch "$ENV_FILE"
    fi
    
    # Update or add OLLAMA_MODEL
    if grep -q "^ARK_OLLAMA_MODEL=" "$ENV_FILE"; then
        sed -i "s|^ARK_OLLAMA_MODEL=.*|ARK_OLLAMA_MODEL=$model|" "$ENV_FILE"
    else
        echo "ARK_OLLAMA_MODEL=$model" >> "$ENV_FILE"
    fi
    
    # Ensure OLLAMA_HOST is set
    if ! grep -q "^ARK_OLLAMA_HOST=" "$ENV_FILE"; then
        echo "ARK_OLLAMA_HOST=http://127.0.0.1:11434" >> "$ENV_FILE"
    fi
}

list_models() {
    print_header "📚 Installed Models"
    
    if ! is_ollama_running; then
        echo -e "${YELLOW}⚠️  Ollama is not running${NC}"
        echo "Run: ark-ollama start"
        return 1
    fi
    
    ollama list
}

remove_model() {
    local model="$1"
    
    if [ -z "$model" ]; then
        echo -e "${RED}❌ Please specify a model to remove${NC}"
        echo "Usage: ark-ollama remove <model>"
        return 1
    fi
    
    echo "🗑️  Removing model: $model"
    
    if ollama rm "$model"; then
        echo -e "${GREEN}✅ Model '$model' removed${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to remove model '$model'${NC}"
        return 1
    fi
}

show_status() {
    print_header "🔍 Ollama Status"
    
    echo "Installation:"
    if is_ollama_installed; then
        echo -e "  ${GREEN}✅ Ollama is installed${NC}"
        echo "     Version: $(ollama --version)"
    else
        echo -e "  ${RED}❌ Ollama is not installed${NC}"
        return 1
    fi
    
    echo ""
    echo "Service:"
    if is_ollama_running; then
        echo -e "  ${GREEN}✅ Ollama service is running${NC}"
        echo "     Endpoint: http://localhost:11434"
    else
        echo -e "  ${YELLOW}⚠️  Ollama service is not running${NC}"
        echo "     Run: ark-ollama start"
    fi
    
    echo ""
    echo "Configuration:"
    if [ -f "$ENV_FILE" ]; then
        local model=$(grep "^ARK_OLLAMA_MODEL=" "$ENV_FILE" | cut -d'=' -f2)
        local host=$(grep "^ARK_OLLAMA_HOST=" "$ENV_FILE" | cut -d'=' -f2)
        
        if [ -n "$model" ]; then
            echo "  Model: $model"
        fi
        if [ -n "$host" ]; then
            echo "  Host: $host"
        fi
    else
        echo -e "  ${YELLOW}⚠️  No configuration file found${NC}"
    fi
}

stop_ollama_service() {
    echo "🛑 Stopping Ollama service..."
    
    local platform=$(detect_platform)
    
    case $platform in
        macos)
            pkill -f "ollama serve" || true
            ;;
        *)
            if systemctl list-unit-files | grep -q ollama.service; then
                sudo systemctl stop ollama
            else
                pkill -f "ollama serve" || true
            fi
            ;;
    esac
    
    sleep 2
    
    if ! is_ollama_running; then
        echo -e "${GREEN}✅ Ollama service stopped${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Ollama may still be running${NC}"
        return 1
    fi
}

show_help() {
    echo "ARK Ollama Auto-Installer"
    echo ""
    echo "USAGE:"
    echo "  ark-ollama install [model...]   Install Ollama and download model(s)"
    echo "  ark-ollama list                 List installed models"
    echo "  ark-ollama pull <model>         Download additional model"
    echo "  ark-ollama remove <model>       Remove a model"
    echo "  ark-ollama status               Show Ollama status"
    echo "  ark-ollama start                Start Ollama service"
    echo "  ark-ollama stop                 Stop Ollama service"
    echo "  ark-ollama restart              Restart Ollama service"
    echo ""
    echo "EXAMPLES:"
    echo "  ark-ollama install                    # Install with llama3.2:1b"
    echo "  ark-ollama install mistral            # Install with mistral"
    echo "  ark-ollama install llama3.2:1b codellama  # Multiple models"
    echo "  ark-ollama pull phi                   # Download phi model"
    echo ""
    echo "POPULAR MODELS:"
    echo "  • llama3.2:1b    - Lightweight (1.3GB) - Good for testing"
    echo "  • llama3.2:3b    - Balanced (2GB) - Good quality"
    echo "  • mistral        - High quality (4.1GB)"
    echo "  • codellama      - Code-focused (3.8GB)"
    echo "  • phi            - Microsoft small model (1.6GB)"
    echo ""
}

################################################################################
# Main Command Handler
################################################################################

main() {
    local command="${1:-help}"
    shift || true
    
    case $command in
        install)
            print_header "🤖 ARK Ollama Auto-Installer"
            
            # Install Ollama if not present
            if ! is_ollama_installed; then
                install_ollama || exit 1
            else
                echo -e "${GREEN}✅ Ollama is already installed${NC}"
            fi
            
            # Start Ollama service
            start_ollama_service || exit 1
            
            # Install models
            if [ $# -eq 0 ]; then
                # Default model
                pull_model "llama3.2:1b"
            else
                # Install specified models
                for model in "$@"; do
                    pull_model "$model"
                done
            fi
            
            # Show final status
            echo ""
            show_status
            
            echo ""
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${GREEN}🎉 Ollama installation complete!${NC}"
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            echo "Next steps:"
            echo "  1. List models:      ark-ollama list"
            echo "  2. Test a model:     ollama run llama3.2:1b"
            echo "  3. Start ARK:        ark start"
            echo ""
            ;;
            
        list)
            list_models
            ;;
            
        pull)
            if ! is_ollama_running; then
                start_ollama_service || exit 1
            fi
            pull_model "$@"
            ;;
            
        remove|rm)
            remove_model "$@"
            ;;
            
        status)
            show_status
            ;;
            
        start)
            start_ollama_service
            ;;
            
        stop)
            stop_ollama_service
            ;;
            
        restart)
            stop_ollama_service
            sleep 2
            start_ollama_service
            ;;
            
        help|--help|-h)
            show_help
            ;;
            
        *)
            echo -e "${RED}❌ Unknown command: $command${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"

################################################################################
# INTEGRATION INSTRUCTIONS
################################################################################
#
# METHOD 1: Add to create-unified-ark.sh
# ----------------------------------------
# 1. Copy this file to enhancements/09-ollama-auto-installer.sh
#
# 2. In create-unified-ark.sh, add after creating bin directory:
#
#    # Copy Ollama installer
#    cp enhancements/09-ollama-auto-installer.sh "$INSTALL_DIR/bin/ark-ollama"
#    chmod +x "$INSTALL_DIR/bin/ark-ollama"
#
# 3. Add to post-install message:
#
#    echo "  📦 Install Ollama:   ark-ollama install"
#
#
# METHOD 2: Manual Installation
# ------------------------------
# 1. Copy to your ARK bin directory:
#    cp enhancements/09-ollama-auto-installer.sh ~/ark/bin/ark-ollama
#    chmod +x ~/ark/bin/ark-ollama
#
# 2. Test:
#    ark-ollama status
#    ark-ollama install
#
#
# BENEFITS:
# ---------
# ✅ One-command Ollama installation
# ✅ Automatic model downloading
# ✅ Multiple model support
# ✅ Service management
# ✅ Cross-platform support
# ✅ Configuration integration
# ✅ Health status checking
# ✅ Easy model management
#
################################################################################
