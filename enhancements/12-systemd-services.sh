#!/bin/bash
################################################################################
# ARK Enhancement #12: Systemd Services (Raspberry Pi / Linux)
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Creates and manages systemd service units for ARK components (Redis, Ollama,
# ARK backend) to enable auto-start on boot and proper service management on
# Raspberry Pi and other Linux systems.
#
# FEATURES:
# ---------
# ✅ Systemd service unit creation for all ARK components
# ✅ Auto-start on boot configuration
# ✅ Service dependency management
# ✅ Automatic restart on failure
# ✅ Proper log management with journald
# ✅ User-mode services (no root required for ARK)
# ✅ Service enable/disable commands
# ✅ Status monitoring
# ✅ Log viewing integration
# ✅ Uninstall capability
#
# USAGE:
# ------
# ark-services install           # Install all systemd services
# ark-services enable            # Enable auto-start on boot
# ark-services disable           # Disable auto-start
# ark-services start             # Start all services
# ark-services stop              # Stop all services
# ark-services restart           # Restart all services
# ark-services status            # Show status of all services
# ark-services logs [service]    # View service logs
# ark-services uninstall         # Remove systemd services
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ARK home detection
if [ -n "$ARK_HOME" ]; then
    INSTALL_DIR="$ARK_HOME"
elif [ -f "$HOME/.arkrc" ]; then
    INSTALL_DIR=$(grep "ARK_HOME=" "$HOME/.arkrc" | cut -d'=' -f2)
else
    INSTALL_DIR="$HOME/ark"
fi

# Systemd directories
USER_SYSTEMD_DIR="$HOME/.config/systemd/user"
SYSTEM_SYSTEMD_DIR="/etc/systemd/system"

# Use user services by default (no root required)
USE_USER_SERVICES=true

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

check_systemd() {
    if ! command -v systemctl &>/dev/null; then
        echo -e "${RED}❌ systemd is not available on this system${NC}"
        echo "This enhancement is for Linux systems with systemd (Raspberry Pi, Ubuntu, Debian, etc.)"
        exit 1
    fi
}

get_systemctl_cmd() {
    if [ "$USE_USER_SERVICES" = true ]; then
        echo "systemctl --user"
    else
        echo "sudo systemctl"
    fi
}

get_service_dir() {
    if [ "$USE_USER_SERVICES" = true ]; then
        echo "$USER_SYSTEMD_DIR"
    else
        echo "$SYSTEM_SYSTEMD_DIR"
    fi
}

################################################################################
# Service Creation Functions
################################################################################

create_redis_service() {
    local service_dir=$(get_service_dir)
    local service_file="$service_dir/ark-redis.service"
    
    print_section "Creating Redis service"
    
    mkdir -p "$service_dir"
    
    cat > "$service_file" << EOF
[Unit]
Description=ARK Redis Server
Documentation=https://redis.io/documentation
After=network.target

[Service]
Type=simple
ExecStart=$INSTALL_DIR/bin/ark-redis --port 6379 --bind 127.0.0.1
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=default.target
EOF

    echo -e "${GREEN}✅ Created: $service_file${NC}"
}

create_ollama_service() {
    local service_dir=$(get_service_dir)
    local service_file="$service_dir/ark-ollama.service"
    
    print_section "Creating Ollama service"
    
    # Check if Ollama is installed
    if ! command -v ollama &>/dev/null; then
        echo -e "${YELLOW}⚠️  Ollama not installed - skipping service creation${NC}"
        echo "   Install Ollama with: ark-ollama install"
        return 0
    fi
    
    mkdir -p "$service_dir"
    
    cat > "$service_file" << EOF
[Unit]
Description=ARK Ollama Service
Documentation=https://ollama.ai/
After=network.target

[Service]
Type=simple
ExecStart=$(which ollama) serve
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal
Environment="OLLAMA_HOST=127.0.0.1:11434"

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=default.target
EOF

    echo -e "${GREEN}✅ Created: $service_file${NC}"
}

create_ark_backend_service() {
    local service_dir=$(get_service_dir)
    local service_file="$service_dir/ark-backend.service"
    
    print_section "Creating ARK Backend service"
    
    mkdir -p "$service_dir"
    
    # Detect Node.js path
    local node_path="node"
    if [ -f "$INSTALL_DIR/deps/node/nodejs/bin/node" ]; then
        node_path="$INSTALL_DIR/deps/node/nodejs/bin/node"
    fi
    
    cat > "$service_file" << EOF
[Unit]
Description=ARK Intelligent Backend
Documentation=https://github.com/Superman08091992/ark
After=network.target ark-redis.service
Wants=ark-redis.service

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR/lib
ExecStart=$node_path $INSTALL_DIR/lib/intelligent-backend.cjs
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal

# Environment
Environment="ARK_HOME=$INSTALL_DIR"
Environment="NODE_ENV=production"
EnvironmentFile=-$INSTALL_DIR/.env

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=default.target
EOF

    echo -e "${GREEN}✅ Created: $service_file${NC}"
}

################################################################################
# Service Management Functions
################################################################################

install_services() {
    print_header "🔧 Installing ARK Systemd Services"
    
    check_systemd
    
    # Ask if user wants system or user services
    if [ "$(id -u)" = "0" ]; then
        echo "Running as root - using system services"
        USE_USER_SERVICES=false
    else
        echo "User service mode (recommended - no root required)"
        USE_USER_SERVICES=true
    fi
    
    # Create services
    create_redis_service
    create_ollama_service
    create_ark_backend_service
    
    # Reload systemd
    print_section "Reloading systemd"
    if [ "$USE_USER_SERVICES" = true ]; then
        systemctl --user daemon-reload
        echo -e "${GREEN}✅ User services reloaded${NC}"
    else
        sudo systemctl daemon-reload
        echo -e "${GREEN}✅ System services reloaded${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Services installed successfully!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Enable auto-start:  ark-services enable"
    echo "  2. Start services:     ark-services start"
    echo "  3. Check status:       ark-services status"
    echo ""
}

enable_services() {
    print_header "🚀 Enabling Auto-Start on Boot"
    
    check_systemd
    local systemctl_cmd=$(get_systemctl_cmd)
    
    # Enable lingering for user services (allows services to run without login)
    if [ "$USE_USER_SERVICES" = true ]; then
        if command -v loginctl &>/dev/null; then
            loginctl enable-linger "$USER" 2>/dev/null || true
        fi
    fi
    
    # Enable each service
    for service in ark-redis ark-ollama ark-backend; do
        local service_file="$(get_service_dir)/${service}.service"
        if [ -f "$service_file" ]; then
            echo -n "Enabling ${service}... "
            if $systemctl_cmd enable "${service}.service" &>/dev/null; then
                echo -e "${GREEN}✅${NC}"
            else
                echo -e "${YELLOW}⚠️${NC}"
            fi
        fi
    done
    
    echo ""
    echo -e "${GREEN}✅ Services enabled - will start automatically on boot${NC}"
}

disable_services() {
    print_header "🛑 Disabling Auto-Start on Boot"
    
    check_systemd
    local systemctl_cmd=$(get_systemctl_cmd)
    
    for service in ark-redis ark-ollama ark-backend; do
        local service_file="$(get_service_dir)/${service}.service"
        if [ -f "$service_file" ]; then
            echo -n "Disabling ${service}... "
            if $systemctl_cmd disable "${service}.service" &>/dev/null; then
                echo -e "${GREEN}✅${NC}"
            else
                echo -e "${YELLOW}⚠️${NC}"
            fi
        fi
    done
    
    echo ""
    echo -e "${GREEN}✅ Services disabled - will not start automatically${NC}"
}

start_services() {
    print_header "▶️  Starting ARK Services"
    
    check_systemd
    local systemctl_cmd=$(get_systemctl_cmd)
    
    # Start in dependency order
    for service in ark-redis ark-ollama ark-backend; do
        local service_file="$(get_service_dir)/${service}.service"
        if [ -f "$service_file" ]; then
            echo -n "Starting ${service}... "
            if $systemctl_cmd start "${service}.service" &>/dev/null; then
                echo -e "${GREEN}✅${NC}"
            else
                echo -e "${RED}❌${NC}"
            fi
        fi
    done
    
    echo ""
    echo "Run 'ark-services status' to check service status"
}

stop_services() {
    print_header "⏹️  Stopping ARK Services"
    
    check_systemd
    local systemctl_cmd=$(get_systemctl_cmd)
    
    # Stop in reverse dependency order
    for service in ark-backend ark-ollama ark-redis; do
        local service_file="$(get_service_dir)/${service}.service"
        if [ -f "$service_file" ]; then
            echo -n "Stopping ${service}... "
            if $systemctl_cmd stop "${service}.service" &>/dev/null; then
                echo -e "${GREEN}✅${NC}"
            else
                echo -e "${YELLOW}⚠️${NC}"
            fi
        fi
    done
    
    echo ""
    echo -e "${GREEN}✅ Services stopped${NC}"
}

restart_services() {
    print_header "🔄 Restarting ARK Services"
    
    stop_services
    sleep 2
    start_services
}

show_status() {
    print_header "📊 ARK Services Status"
    
    check_systemd
    local systemctl_cmd=$(get_systemctl_cmd)
    
    for service in ark-redis ark-ollama ark-backend; do
        local service_file="$(get_service_dir)/${service}.service"
        if [ -f "$service_file" ]; then
            echo -e "${CYAN}${service}:${NC}"
            $systemctl_cmd status "${service}.service" --no-pager -l 2>/dev/null | head -n 10 || \
                echo -e "${YELLOW}  Status unavailable${NC}"
            echo ""
        fi
    done
}

show_logs() {
    local service="${1:-ark-backend}"
    
    check_systemd
    local systemctl_cmd=$(get_systemctl_cmd)
    
    print_header "📄 Logs for ${service}"
    
    local service_file="$(get_service_dir)/${service}.service"
    if [ ! -f "$service_file" ]; then
        echo -e "${RED}❌ Service not found: ${service}${NC}"
        echo "Available services: ark-redis, ark-ollama, ark-backend"
        return 1
    fi
    
    if [ "$USE_USER_SERVICES" = true ]; then
        journalctl --user -u "${service}.service" -n 50 --no-pager
    else
        sudo journalctl -u "${service}.service" -n 50 --no-pager
    fi
}

uninstall_services() {
    print_header "🗑️  Uninstalling ARK Services"
    
    check_systemd
    
    echo -e "${YELLOW}⚠️  This will remove all ARK systemd services${NC}"
    read -p "Are you sure? (y/N): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Cancelled."
        return 0
    fi
    
    # Stop and disable services
    stop_services
    disable_services
    
    # Remove service files
    print_section "Removing service files"
    for service in ark-redis ark-ollama ark-backend; do
        local service_file="$(get_service_dir)/${service}.service"
        if [ -f "$service_file" ]; then
            echo -n "Removing ${service}... "
            rm -f "$service_file"
            echo -e "${GREEN}✅${NC}"
        fi
    done
    
    # Reload systemd
    local systemctl_cmd=$(get_systemctl_cmd)
    $systemctl_cmd daemon-reload
    
    echo ""
    echo -e "${GREEN}✅ Services uninstalled${NC}"
}

show_help() {
    echo "ARK Systemd Services Manager"
    echo ""
    echo "USAGE:"
    echo "  ark-services install           Install systemd services"
    echo "  ark-services enable            Enable auto-start on boot"
    echo "  ark-services disable           Disable auto-start"
    echo "  ark-services start             Start all services"
    echo "  ark-services stop              Stop all services"
    echo "  ark-services restart           Restart all services"
    echo "  ark-services status            Show status of all services"
    echo "  ark-services logs [service]    View service logs"
    echo "  ark-services uninstall         Remove systemd services"
    echo ""
    echo "SERVICES:"
    echo "  • ark-redis      - Redis database service"
    echo "  • ark-ollama     - Ollama LLM service"
    echo "  • ark-backend    - ARK intelligent backend"
    echo ""
    echo "EXAMPLES:"
    echo "  ark-services install          # Set up all services"
    echo "  ark-services enable           # Enable auto-start"
    echo "  ark-services start            # Start everything"
    echo "  ark-services logs ark-backend # View backend logs"
    echo ""
}

################################################################################
# Main
################################################################################

main() {
    local command="${1:-help}"
    shift || true
    
    case $command in
        install)
            install_services
            ;;
        enable)
            enable_services
            ;;
        disable)
            disable_services
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$@"
            ;;
        uninstall)
            uninstall_services
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
# 1. Copy this file to enhancements/12-systemd-services.sh
#
# 2. In create-unified-ark.sh, add after creating bin directory:
#
#    # Copy systemd services manager
#    cp enhancements/12-systemd-services.sh "$INSTALL_DIR/bin/ark-services"
#    chmod +x "$INSTALL_DIR/bin/ark-services"
#
# 3. Add to post-install section (for Linux systems):
#
#    if command -v systemctl &>/dev/null; then
#        echo ""
#        echo "🔧 Systemd Services (Optional):"
#        echo ""
#        read -p "Install systemd services for auto-start? (y/N): " install_services
#        if [ "$install_services" = "y" ] || [ "$install_services" = "Y" ]; then
#            "$INSTALL_DIR/bin/ark-services" install
#            "$INSTALL_DIR/bin/ark-services" enable
#        fi
#    fi
#
# 4. Add to post-install message:
#
#    if command -v systemctl &>/dev/null; then
#        echo "  🔧 Setup services:   ark-services install"
#    fi
#
#
# METHOD 2: Manual Installation
# ------------------------------
# 1. Copy to your ARK bin directory:
#    cp enhancements/12-systemd-services.sh ~/ark/bin/ark-services
#    chmod +x ~/ark/bin/ark-services
#
# 2. Install services:
#    ark-services install
#    ark-services enable
#    ark-services start
#
# 3. Test:
#    ark-services status
#
#
# BENEFITS:
# ---------
# ✅ Auto-start on boot (perfect for Raspberry Pi)
# ✅ Automatic restart on failure
# ✅ Proper dependency management
# ✅ Integrated logging with journald
# ✅ User-mode services (no root required)
# ✅ Easy service management commands
# ✅ Production-ready service configuration
# ✅ Security hardening built-in
#
# IDEAL FOR:
# ----------
# • Raspberry Pi installations
# • Home server deployments
# • Always-on ARK instances
# • Production Linux systems
# • Debian/Ubuntu/Fedora/etc.
#
################################################################################
