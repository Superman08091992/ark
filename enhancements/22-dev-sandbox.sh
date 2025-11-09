#!/bin/bash
################################################################################
# ARK Enhancement #22: Development Sandbox with IDE
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Creates a complete development environment with web-based IDE, full library
# access, root privileges, and integrated development tools. Perfect for
# coding, testing, and debugging directly within ARK.
#
# FEATURES:
# ---------
# ✅ Web-based IDE (Code-Server / VSCode in browser)
# ✅ Full Linux environment with root access
# ✅ Pre-installed development tools (git, docker, compilers)
# ✅ Multiple language support (Node.js, Python, Go, Rust, Java)
# ✅ Integrated terminal with sudo access
# ✅ Extensions marketplace
# ✅ Live code execution and debugging
# ✅ File system access
# ✅ Workspace management
# ✅ Port forwarding for testing
# ✅ Git integration
# ✅ Package manager access (npm, pip, cargo, etc.)
#
# USAGE:
# ------
# ark-dev setup                  # Install dev sandbox
# ark-dev start                  # Start IDE
# ark-dev stop                   # Stop IDE
# ark-dev status                 # Check status
# ark-dev install <tool>         # Install dev tool
# ark-dev code                   # Open IDE in browser
# ark-dev terminal               # Direct terminal access
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# ARK home detection
if [ -n "$ARK_HOME" ]; then
    INSTALL_DIR="$ARK_HOME"
elif [ -f "$HOME/.arkrc" ]; then
    INSTALL_DIR=$(grep "ARK_HOME=" "$HOME/.arkrc" | cut -d'=' -f2)
else
    INSTALL_DIR="$HOME/ark"
fi

ENV_FILE="$INSTALL_DIR/.env"
DEV_DIR="$INSTALL_DIR/dev-sandbox"
WORKSPACE_DIR="$DEV_DIR/workspace"
CODE_SERVER_PORT=8443
CODE_SERVER_PID="$DEV_DIR/.code-server.pid"

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

print_section() {
    echo ""
    echo -e "${CYAN}▶ $1${NC}"
}

################################################################################
# Installation Functions
################################################################################

setup_dev_sandbox() {
    print_header "🛠️  Setting Up Development Sandbox"
    
    echo "This will install:"
    echo "  • Code-Server (VS Code in browser)"
    echo "  • Development tools (git, build-essential, etc.)"
    echo "  • Multiple language runtimes"
    echo "  • Full sudo access"
    echo ""
    
    read -p "Continue? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Cancelled."
        return 0
    fi
    
    # Create directories
    mkdir -p "$DEV_DIR"
    mkdir -p "$WORKSPACE_DIR"
    mkdir -p "$DEV_DIR/bin"
    mkdir -p "$DEV_DIR/config"
    
    # Detect OS
    print_section "Detecting Operating System"
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        echo "OS: $OS"
    else
        OS="unknown"
    fi
    
    # Install Code-Server
    install_code_server
    
    # Install development tools
    install_dev_tools
    
    # Setup sudo access
    setup_sudo_access
    
    # Configure Code-Server
    configure_code_server
    
    # Create launcher scripts
    create_launcher_scripts
    
    # Update .env
    update_env_file
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Development Sandbox Installed!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Start IDE:     ark-dev start"
    echo "  2. Open browser:  ark-dev code"
    echo "  3. Password:      (see above or config file)"
    echo ""
    echo "Workspace: $WORKSPACE_DIR"
    echo ""
}

install_code_server() {
    print_section "Installing Code-Server (VS Code)"
    
    if command -v code-server &>/dev/null; then
        echo -e "${GREEN}✅ Code-Server already installed${NC}"
        return 0
    fi
    
    echo "Downloading Code-Server..."
    
    # Get latest version
    local VERSION=$(curl -s https://api.github.com/repos/coder/code-server/releases/latest | grep '"tag_name"' | cut -d'"' -f4 | sed 's/v//')
    
    # Detect architecture
    local ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            ARCH="amd64"
            ;;
        aarch64)
            ARCH="arm64"
            ;;
        armv7l)
            ARCH="armv7"
            ;;
    esac
    
    local DOWNLOAD_URL="https://github.com/coder/code-server/releases/download/v${VERSION}/code-server-${VERSION}-linux-${ARCH}.tar.gz"
    
    echo "Downloading from: $DOWNLOAD_URL"
    
    cd "$DEV_DIR"
    curl -fL "$DOWNLOAD_URL" -o code-server.tar.gz
    
    echo "Extracting..."
    tar xzf code-server.tar.gz
    
    # Move to bin
    local EXTRACTED_DIR=$(tar tzf code-server.tar.gz | head -1 | cut -f1 -d"/")
    cp "$EXTRACTED_DIR/bin/code-server" "$DEV_DIR/bin/"
    rm -rf "$EXTRACTED_DIR" code-server.tar.gz
    
    chmod +x "$DEV_DIR/bin/code-server"
    
    echo -e "${GREEN}✅ Code-Server installed${NC}"
}

install_dev_tools() {
    print_section "Installing Development Tools"
    
    case $OS in
        ubuntu|debian)
            echo "Installing via apt..."
            
            # Update package list
            sudo apt-get update -qq
            
            # Essential build tools
            sudo apt-get install -y \
                build-essential \
                git \
                curl \
                wget \
                vim \
                nano \
                tmux \
                htop \
                jq \
                sqlite3 \
                ca-certificates \
                gnupg \
                lsb-release
            
            # Python development
            echo "Installing Python tools..."
            sudo apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev
            
            # Node.js (if not already installed)
            if ! command -v node &>/dev/null; then
                echo "Installing Node.js..."
                curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
                sudo apt-get install -y nodejs
            fi
            
            # Go language
            echo "Installing Go..."
            if ! command -v go &>/dev/null; then
                wget -q https://go.dev/dl/go1.21.5.linux-amd64.tar.gz -O /tmp/go.tar.gz
                sudo tar -C /usr/local -xzf /tmp/go.tar.gz
                rm /tmp/go.tar.gz
            fi
            
            # Rust (optional)
            if ! command -v cargo &>/dev/null; then
                echo "Installing Rust..."
                curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
            fi
            
            # Docker (if not installed)
            if ! command -v docker &>/dev/null; then
                echo "Installing Docker..."
                curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
                sudo sh /tmp/get-docker.sh
                sudo usermod -aG docker $USER
                rm /tmp/get-docker.sh
            fi
            
            ;;
            
        fedora|centos|rhel)
            echo "Installing via yum/dnf..."
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y git curl wget vim nano tmux htop jq
            ;;
            
        arch|manjaro)
            echo "Installing via pacman..."
            sudo pacman -S --noconfirm base-devel git curl wget vim nano tmux htop jq
            ;;
            
        *)
            echo -e "${YELLOW}⚠️  Unknown OS. Install tools manually${NC}"
            ;;
    esac
    
    echo -e "${GREEN}✅ Development tools installed${NC}"
}

setup_sudo_access() {
    print_section "Configuring Sudo Access"
    
    # Check if user already has sudo
    if sudo -n true 2>/dev/null; then
        echo -e "${GREEN}✅ User already has sudo access${NC}"
        return 0
    fi
    
    # Add user to sudoers (if we have root)
    if [ "$EUID" -eq 0 ]; then
        echo "$USER ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/ark-dev
        chmod 0440 /etc/sudoers.d/ark-dev
        echo -e "${GREEN}✅ Sudo access configured${NC}"
    else
        echo -e "${YELLOW}⚠️  Run with sudo to enable full root access${NC}"
        echo "   sudo ark-dev setup"
    fi
}

configure_code_server() {
    print_section "Configuring Code-Server"
    
    local CONFIG_DIR="$HOME/.config/code-server"
    mkdir -p "$CONFIG_DIR"
    
    # Generate password if not exists
    local PASSWORD_FILE="$DEV_DIR/config/password.txt"
    if [ ! -f "$PASSWORD_FILE" ]; then
        local PASSWORD=$(openssl rand -base64 16)
        echo "$PASSWORD" > "$PASSWORD_FILE"
        chmod 600 "$PASSWORD_FILE"
    fi
    
    local PASSWORD=$(cat "$PASSWORD_FILE")
    
    # Create config
    cat > "$CONFIG_DIR/config.yaml" << EOF
bind-addr: 0.0.0.0:${CODE_SERVER_PORT}
auth: password
password: ${PASSWORD}
cert: false
user-data-dir: ${DEV_DIR}/user-data
extensions-dir: ${DEV_DIR}/extensions
EOF
    
    echo -e "${GREEN}✅ Code-Server configured${NC}"
    echo ""
    echo -e "${YELLOW}IDE Password: ${PASSWORD}${NC}"
    echo "Saved to: $PASSWORD_FILE"
}

create_launcher_scripts() {
    print_section "Creating Launcher Scripts"
    
    # Create wrapper script
    cat > "$DEV_DIR/bin/ark-code-server" << 'EOF'
#!/bin/bash
# ARK Code-Server Launcher

export PATH="/usr/local/go/bin:$HOME/.cargo/bin:$PATH"
export GOPATH="$HOME/go"

CODE_SERVER_BIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/code-server"

exec "$CODE_SERVER_BIN" "$@"
EOF
    
    chmod +x "$DEV_DIR/bin/ark-code-server"
    
    echo -e "${GREEN}✅ Launcher scripts created${NC}"
}

update_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        mkdir -p "$(dirname "$ENV_FILE")"
        touch "$ENV_FILE"
    fi
    
    if ! grep -q "^ARK_DEV_SANDBOX_ENABLED=" "$ENV_FILE"; then
        cat >> "$ENV_FILE" << EOF

# Development Sandbox
ARK_DEV_SANDBOX_ENABLED=true
ARK_DEV_IDE_PORT=${CODE_SERVER_PORT}
ARK_DEV_WORKSPACE=${WORKSPACE_DIR}
EOF
    fi
}

################################################################################
# Runtime Functions
################################################################################

start_ide() {
    print_header "▶️  Starting Development IDE"
    
    if [ -f "$CODE_SERVER_PID" ] && kill -0 $(cat "$CODE_SERVER_PID") 2>/dev/null; then
        echo -e "${YELLOW}⚠️  IDE already running${NC}"
        local port=$(grep "^ARK_DEV_IDE_PORT=" "$ENV_FILE" | cut -d'=' -f2 || echo "$CODE_SERVER_PORT")
        echo "Access at: http://localhost:${port}"
        return 0
    fi
    
    if [ ! -f "$DEV_DIR/bin/ark-code-server" ]; then
        echo -e "${RED}❌ Code-Server not installed${NC}"
        echo "Run: ark-dev setup"
        return 1
    fi
    
    echo "Starting Code-Server..."
    
    # Start in background
    cd "$WORKSPACE_DIR"
    "$DEV_DIR/bin/ark-code-server" \
        --user-data-dir "$DEV_DIR/user-data" \
        --extensions-dir "$DEV_DIR/extensions" \
        > "$DEV_DIR/code-server.log" 2>&1 &
    
    echo $! > "$CODE_SERVER_PID"
    
    # Wait for startup
    echo -n "Waiting for IDE to start"
    for i in {1..30}; do
        if curl -s http://localhost:${CODE_SERVER_PORT} &>/dev/null; then
            echo ""
            echo -e "${GREEN}✅ IDE started successfully${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    echo ""
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎉 Development IDE Ready!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "  URL:       http://localhost:${CODE_SERVER_PORT}"
    echo "  Password:  $(cat "$DEV_DIR/config/password.txt")"
    echo "  Workspace: $WORKSPACE_DIR"
    echo ""
    echo "Quick commands:"
    echo "  ark-dev code       # Open in browser"
    echo "  ark-dev stop       # Stop IDE"
    echo "  ark-dev terminal   # Direct terminal"
    echo ""
}

stop_ide() {
    print_header "⏹️  Stopping Development IDE"
    
    if [ ! -f "$CODE_SERVER_PID" ]; then
        echo "IDE not running"
        return 0
    fi
    
    local pid=$(cat "$CODE_SERVER_PID")
    
    if kill -0 $pid 2>/dev/null; then
        echo "Stopping Code-Server (PID: $pid)..."
        kill $pid
        rm -f "$CODE_SERVER_PID"
        
        # Wait for clean shutdown
        sleep 2
        
        echo -e "${GREEN}✅ IDE stopped${NC}"
    else
        echo "IDE not running (stale PID file)"
        rm -f "$CODE_SERVER_PID"
    fi
    
    echo ""
}

show_status() {
    print_header "📊 Development Sandbox Status"
    
    # IDE Status
    echo "IDE (Code-Server):"
    if [ -f "$CODE_SERVER_PID" ] && kill -0 $(cat "$CODE_SERVER_PID") 2>/dev/null; then
        echo -e "  ${GREEN}✓ Running${NC}"
        echo "  URL: http://localhost:${CODE_SERVER_PORT}"
        echo "  PID: $(cat "$CODE_SERVER_PID")"
        echo "  Workspace: $WORKSPACE_DIR"
    else
        echo -e "  ${RED}✗ Stopped${NC}"
    fi
    
    echo ""
    
    # Installed Tools
    echo "Development Tools:"
    check_tool "git"
    check_tool "node" "--version"
    check_tool "npm" "--version"
    check_tool "python3" "--version"
    check_tool "pip3" "--version"
    check_tool "go" "version"
    check_tool "cargo" "--version"
    check_tool "docker" "--version"
    
    echo ""
    
    # Sudo Access
    echo "Permissions:"
    if sudo -n true 2>/dev/null; then
        echo -e "  ${GREEN}✓ Sudo access enabled${NC}"
    else
        echo -e "  ${YELLOW}⚠ No sudo access${NC}"
    fi
    
    echo ""
}

check_tool() {
    local cmd=$1
    local arg=${2:---version}
    
    if command -v "$cmd" &>/dev/null; then
        local version=$($cmd $arg 2>/dev/null | head -1)
        echo -e "  ${GREEN}✓${NC} $cmd: $version"
    else
        echo -e "  ${RED}✗${NC} $cmd: not installed"
    fi
}

open_in_browser() {
    local url="http://localhost:${CODE_SERVER_PORT}"
    
    if [ ! -f "$CODE_SERVER_PID" ] || ! kill -0 $(cat "$CODE_SERVER_PID") 2>/dev/null; then
        echo -e "${YELLOW}⚠️  IDE not running${NC}"
        echo "Start with: ark-dev start"
        return 1
    fi
    
    echo "Opening IDE in browser..."
    echo "URL: $url"
    echo ""
    
    # Try to open in browser
    if command -v xdg-open &>/dev/null; then
        xdg-open "$url"
    elif command -v open &>/dev/null; then
        open "$url"
    elif command -v wslview &>/dev/null; then
        wslview "$url"
    else
        echo "Open manually: $url"
        echo "Password: $(cat "$DEV_DIR/config/password.txt")"
    fi
}

open_terminal() {
    print_header "🖥️  Development Terminal"
    
    echo "Starting development shell with full environment..."
    echo ""
    
    # Set up environment
    export PATH="/usr/local/go/bin:$HOME/.cargo/bin:$PATH"
    export GOPATH="$HOME/go"
    export WORKSPACE="$WORKSPACE_DIR"
    
    cd "$WORKSPACE_DIR"
    
    echo "Environment:"
    echo "  WORKSPACE: $WORKSPACE_DIR"
    echo "  PATH: $PATH"
    echo ""
    echo "Available commands:"
    echo "  node, npm, python3, pip3, go, cargo, docker, git"
    echo ""
    
    # Start shell
    exec bash
}

install_tool() {
    local tool="$1"
    
    if [ -z "$tool" ]; then
        echo "Available tools to install:"
        echo "  • python-libs    - Python data science libraries"
        echo "  • node-tools     - Node.js development tools"
        echo "  • rust-tools     - Rust development tools"
        echo "  • go-tools       - Go development tools"
        echo "  • database       - Database tools (PostgreSQL, MongoDB)"
        echo "  • kubernetes     - kubectl, helm, k9s"
        echo "  • cloud          - AWS CLI, Azure CLI, gcloud"
        echo ""
        echo "Usage: ark-dev install <tool>"
        return 0
    fi
    
    print_header "📦 Installing: $tool"
    
    case $tool in
        python-libs)
            echo "Installing Python libraries..."
            pip3 install --user numpy pandas matplotlib scikit-learn jupyter
            ;;
            
        node-tools)
            echo "Installing Node.js tools..."
            npm install -g typescript ts-node eslint prettier nodemon pm2
            ;;
            
        rust-tools)
            echo "Installing Rust tools..."
            cargo install cargo-watch cargo-edit cargo-tree
            ;;
            
        go-tools)
            echo "Installing Go tools..."
            go install golang.org/x/tools/gopls@latest
            go install github.com/go-delve/delve/cmd/dlv@latest
            ;;
            
        database)
            echo "Installing database tools..."
            sudo apt-get install -y postgresql-client mongodb-clients redis-tools
            ;;
            
        kubernetes)
            echo "Installing Kubernetes tools..."
            curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
            sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
            rm kubectl
            ;;
            
        cloud)
            echo "Installing cloud tools..."
            pip3 install --user awscli
            ;;
            
        *)
            echo -e "${RED}❌ Unknown tool: $tool${NC}"
            return 1
            ;;
    esac
    
    echo -e "${GREEN}✅ $tool installed${NC}"
    echo ""
}

show_help() {
    echo "ARK Development Sandbox"
    echo ""
    echo "USAGE:"
    echo "  ark-dev setup                  Install development sandbox"
    echo "  ark-dev start                  Start IDE"
    echo "  ark-dev stop                   Stop IDE"
    echo "  ark-dev restart                Restart IDE"
    echo "  ark-dev status                 Show status"
    echo "  ark-dev code                   Open IDE in browser"
    echo "  ark-dev terminal               Open development terminal"
    echo "  ark-dev install <tool>         Install development tool"
    echo "  ark-dev workspace              Show workspace path"
    echo ""
    echo "FEATURES:"
    echo "  • Full VS Code IDE in browser"
    echo "  • Root/sudo access"
    echo "  • Pre-installed: Node.js, Python, Go, Rust, Docker"
    echo "  • Integrated terminal"
    echo "  • Extensions marketplace"
    echo "  • Git integration"
    echo ""
    echo "EXAMPLES:"
    echo "  ark-dev setup                  # First-time setup"
    echo "  ark-dev start                  # Start IDE"
    echo "  ark-dev code                   # Open in browser"
    echo "  ark-dev install python-libs    # Add Python libraries"
    echo "  ark-dev terminal               # Direct shell access"
    echo ""
}

################################################################################
# Main
################################################################################

main() {
    local command="${1:-help}"
    shift || true
    
    case $command in
        setup)
            setup_dev_sandbox
            ;;
        start)
            start_ide
            ;;
        stop)
            stop_ide
            ;;
        restart)
            stop_ide
            sleep 2
            start_ide
            ;;
        status)
            show_status
            ;;
        code|open)
            open_in_browser
            ;;
        terminal|shell)
            open_terminal
            ;;
        install)
            install_tool "$@"
            ;;
        workspace)
            echo "$WORKSPACE_DIR"
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
# 1. Copy this file to enhancements/22-dev-sandbox.sh
#
# 2. In create-unified-ark.sh, add after creating bin directory:
#
#    # Copy dev sandbox tool
#    cp enhancements/22-dev-sandbox.sh "$INSTALL_DIR/bin/ark-dev"
#    chmod +x "$INSTALL_DIR/bin/ark-dev"
#
# 3. Add to post-install message:
#
#    echo "  🛠️  Dev Sandbox:     ark-dev setup"
#
#
# QUICK START:
# ------------
# 1. Setup:      ark-dev setup
# 2. Start IDE:  ark-dev start
# 3. Open:       ark-dev code
# 4. Password:   (shown during start or in password.txt)
#
#
# BENEFITS:
# ---------
# ✅ Full VS Code IDE in browser
# ✅ Root/sudo access
# ✅ Multiple languages (Node, Python, Go, Rust)
# ✅ Docker integration
# ✅ Git support
# ✅ Extensions marketplace
# ✅ Integrated terminal
# ✅ No desktop required
# ✅ Remote development ready
# ✅ Production-ready environment
#
#
# USE CASES:
# ----------
# • Remote development on Raspberry Pi
# • Cloud server coding
# • Container-based development
# • Testing and debugging
# • Learning and experimentation
# • Full-stack development
# • DevOps workflows
#
################################################################################
