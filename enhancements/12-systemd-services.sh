#!/bin/bash
################################################################################
# ARK Enhancement #12: Systemd Services (Raspberry Pi)
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Creates systemd service files for ARK, Redis, and Ollama to enable automatic
# startup on boot. Designed specifically for Raspberry Pi and Debian-based
# systems with systemd support.
#
# FEATURES:
# ---------
# ✅ Systemd service creation for ARK backend
# ✅ Redis service configuration
# ✅ Ollama service setup (if installed)
# ✅ Auto-start on boot
# ✅ Automatic restart on failure
# ✅ Service dependency management
# ✅ Log management with journald
# ✅ User-level and system-level services
# ✅ Service status monitoring
# ✅ Easy enable/disable commands
#
# USAGE:
# ------
# ark-service install           # Install all service files
# ark-service enable            # Enable services (auto-start on boot)
# ark-service disable           # Disable auto-start
# ark-service start             # Start all services
# ark-service stop              # Stop all services
# ark-service restart           # Restart all services
# ark-service status            # Show service status
# ark-service logs [service]    # Show service logs
# ark-service uninstall         # Remove service files
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ARK home detection
if [ -n "$ARK_HOME" ]; then
    INSTALL_DIR="$ARK_HOME"
elif [ -f "$HOME/.arkrc" ]; then
    INSTALL_DIR=$(grep "ARK_HOME=" "$HOME/.arkrc" | cut -d'=' -f2)
else
    INSTALL_DIR="$HOME/ark"
fi

# Service configuration
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
SYSTEMD_SYSTEM_DIR="/etc/systemd/system"
USE_USER_SERVICES=true

# Check if we should use user or system services
if [ "$EUID" -eq 0 ]; then
    USE_USER_SERVICES=false
fi

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

check_systemd() {
    if ! command -v systemctl &>/dev/null; then
        echo -e "${RED}❌ systemd not found on this system${NC}"
        echo "This enhancement is for systemd-based systems only."
        exit 1
    fi
}

check_platform() {
    # Verify this is a suitable platform (not Termux)
    if [ -d "/data/data/com.termux" ]; then
        echo -e "${YELLOW}⚠️  Termux detected - systemd services not available${NC}"
        echo "On Termux, use: ark start (manual start)"
        exit 1
    fi
}

get_service_dir() {
    if [ "$USE_USER_SERVICES" = true ]; then
        echo "$SYSTEMD_USER_DIR"
    else
        echo "$SYSTEMD_SYSTEM_DIR"
    fi
}

get_systemctl_cmd() {
    if [ "$USE_USER_SERVICES" = true ]; then
        echo "systemctl --user"
    else
        echo "sudo systemctl"
    fi
}

################################################################################
# Service File Generators
################################################################################

create_ark_service() {
    local service_dir=$(get_service_dir)
    local service_file="$service_dir/ark-backend.service"
    
    echo "📝 Creating ARK backend service..."
    
    mkdir -p "$service_dir"
    
    cat > "$service_file" << EOF
[Unit]
Description=ARK Intelligent Backend
Documentation=https://github.com/Superman08091992/ark
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$INSTALL_DIR/lib
Environment="PATH=$INSTALL_DIR/bin:$PATH"
Environment="ARK_HOME=$INSTALL_DIR"
Environment="NODE_ENV=production"

# Load environment variables from .env file
EnvironmentFile=-$INSTALL_DIR/.env

# Start ARK backend
ExecStart=$INSTALL_DIR/deps/node/nodejs/bin/node intelligent-backend.cjs

# Restart configuration
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ark-backend

[Install]
WantedBy=default.target
EOF

    chmod 644 "$service_file"
    echo -e "${GREEN}✅ ARK backend service created${NC}"
}

create_redis_service() {
    local service_dir=$(get_service_dir)
    local service_file="$service_dir/ark-redis.service"
    
    # Check if system Redis service exists
    if systemctl list-unit-files | grep -q "^redis-server.service\|^redis.service"; then
        echo -e "${BLUE}ℹ️  System Redis service already exists, skipping ARK Redis service${NC}"
        return 0
    fi
    
    # Check if bundled Redis exists
    if [ ! -f "$INSTALL_DIR/deps/redis/redis-server" ]; then
        echo -e "${YELLOW}⚠️  Bundled Redis not found, skipping Redis service${NC}"
        return 0
    fi
    
    echo "📝 Creating ARK Redis service..."
    
    mkdir -p "$service_dir"
    
    cat > "$service_file" << EOF
[Unit]
Description=ARK Redis Server
Documentation=https://redis.io/documentation
After=network.target

[Service]
Type=forking
User=$(whoami)
WorkingDirectory=$INSTALL_DIR/data/redis

# Start Redis with bundled binary
ExecStart=$INSTALL_DIR/deps/redis/redis-server $INSTALL_DIR/config/redis.conf --daemonize yes
ExecStop=/bin/kill -s TERM \$MAINPID

# PID file
PIDFile=$INSTALL_DIR/data/redis/redis.pid

# Restart configuration
Restart=always
RestartSec=5
StartLimitInterval=120
StartLimitBurst=3

# Resource limits
LimitNOFILE=65536

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ark-redis

[Install]
WantedBy=default.target
EOF

    chmod 644 "$service_file"
    echo -e "${GREEN}✅ Redis service created${NC}"
}

create_ollama_service() {
    # Check if Ollama is installed
    if ! command -v ollama &>/dev/null; then
        echo -e "${BLUE}ℹ️  Ollama not installed, skipping Ollama service${NC}"
        return 0
    fi
    
    # Check if system Ollama service exists
    if systemctl list-unit-files | grep -q "^ollama.service"; then
        echo -e "${BLUE}ℹ️  System Ollama service already exists, skipping${NC}"
        return 0
    fi
    
    local service_dir=$(get_service_dir)
    local service_file="$service_dir/ark-ollama.service"
    
    echo "📝 Creating ARK Ollama service..."
    
    mkdir -p "$service_dir"
    
    cat > "$service_file" << EOF
[Unit]
Description=ARK Ollama Service
Documentation=https://ollama.ai/
After=network.target

[Service]
Type=simple
User=$(whoami)
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="OLLAMA_HOST=127.0.0.1:11434"

# Start Ollama
ExecStart=$(which ollama) serve

# Restart configuration
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Resource limits
LimitNOFILE=65536

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ark-ollama

[Install]
WantedBy=default.target
EOF

    chmod 644 "$service_file"
    echo -e "${GREEN}✅ Ollama service created${NC}"
}

################################################################################
# Service Management Functions
################################################################################

install_services() {
    print_header "📦 Installing ARK Services"
    
    check_systemd
    check_platform
    
    if [ "$USE_USER_SERVICES" = true ]; then
        echo "Installing user-level services..."
        echo "Services will run as: $(whoami)"
        echo ""
    else
        echo "Installing system-level services..."
        echo "Services will run as: $(whoami)"
        echo ""
    fi
    
    # Create service files
    create_ark_service
    create_redis_service
    create_ollama_service
    
    # Reload systemd
    echo ""
    echo "🔄 Reloading systemd daemon..."
    if [ "$USE_USER_SERVICES" = true ]; then
        systemctl --user daemon-reload
    else
        sudo systemctl daemon-reload
    fi
    
    echo ""
    echo -e "${GREEN}✅ Services installed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Enable services:  ark-service enable"
    echo "  2. Start services:   ark-service start"
    echo "  3. Check status:     ark-service status"
    echo ""
}

enable_services() {
    print_header "🚀 Enabling ARK Services"
    
    local systemctl_cmd=$(get_systemctl_cmd)
    
    echo "Enabling services for auto-start on boot..."
    echo ""
    
    # Enable ARK backend
    if [ -f "$(get_service_dir)/ark-backend.service" ]; then
        echo -n "  ARK Backend... "
        $systemctl_cmd enable ark-backend.service 2>/dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}⚠️${NC}"
    fi
    
    # Enable Redis
    if [ -f "$(get_service_dir)/ark-redis.service" ]; then
        echo -n "  ARK Redis... "
        $systemctl_cmd enable ark-redis.service 2>/dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}⚠️${NC}"
    fi
    
    # Enable Ollama
    if [ -f "$(get_service_dir)/ark-ollama.service" ]; then
        echo -n "  ARK Ollama... "
        $systemctl_cmd enable ark-ollama.service 2>/dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}⚠️${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Services enabled - will start automatically on boot${NC}"
    echo ""
}

disable_services() {
    print_header "🛑 Disabling ARK Services"
    
    local systemctl_cmd=$(get_systemctl_cmd)
    
    echo "Disabling auto-start on boot..."
    echo ""
    
    # Disable services
    for service in ark-backend ark-redis ark-ollama; do
        if [ -f "$(get_service_dir)/${service}.service" ]; then
            echo -n "  $service... "
            $systemctl_cmd disable "${service}.service" 2>/dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}⚠️${NC}"
        fi
    done
    
    echo ""
    echo -e "${GREEN}✅ Services disabled${NC}"
    echo ""
}

start_services() {
    print_header "▶️  Starting ARK Services"
    
    local systemctl_cmd=$(get_systemctl_cmd)
    
    # Start Redis first (dependency)
    if [ -f "$(get_service_dir)/ark-redis.service" ]; then
        echo -n "Starting Redis... "
        $systemctl_cmd start ark-redis.service 2>/dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}⚠️${NC}"
        sleep 2
    fi
    
    # Start Ollama
    if [ -f "$(get_service_dir)/ark-ollama.service" ]; then
        echo -n "Starting Ollama... "
        $systemctl_cmd start ark-ollama.service 2>/dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}⚠️${NC}"
        sleep 2
    fi
    
    # Start ARK backend
    if [ -f "$(get_service_dir)/ark-backend.service" ]; then
        echo -n "Starting ARK Backend... "
        $systemctl_cmd start ark-backend.service 2>/dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}⚠️${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Services started${NC}"
    echo ""
}

stop_services() {
    print_header "⏹️  Stopping ARK Services"
    
    local systemctl_cmd=$(get_systemctl_cmd)
    
    # Stop in reverse order
    for service in ark-backend ark-ollama ark-redis; do
        if [ -f "$(get_service_dir)/${service}.service" ]; then
            echo -n "Stopping $service... "
            $systemctl_cmd stop "${service}.service" 2>/dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}⚠️${NC}"
        fi
    done
    
    echo ""
    echo -e "${GREEN}✅ Services stopped${NC}"
    echo ""
}

restart_services() {
    print_header "🔄 Restarting ARK Services"
    
    stop_services
    sleep 2
    start_services
}

show_status() {
    print_header "📊 ARK Services Status"
    
    local systemctl_cmd=$(get_systemctl_cmd)
    
    for service in ark-backend ark-redis ark-ollama; do
        if [ -f "$(get_service_dir)/${service}.service" ]; then
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "Service: $service"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            $systemctl_cmd status "${service}.service" --no-pager -l || true
            echo ""
        fi
    done
}

show_logs() {
    local service="${1:-ark-backend}"
    
    print_header "📄 Service Logs: $service"
    
    local systemctl_cmd=$(get_systemctl_cmd)
    
    if [ -f "$(get_service_dir)/${service}.service" ]; then
        if [ "$USE_USER_SERVICES" = true ]; then
            journalctl --user -u "${service}.service" -n 50 --no-pager
        else
            sudo journalctl -u "${service}.service" -n 50 --no-pager
        fi
    else
        echo -e "${RED}❌ Service not found: ${service}${NC}"
        echo "Available services: ark-backend, ark-redis, ark-ollama"
    fi
    
    echo ""
}

uninstall_services() {
    print_header "🗑️  Uninstalling ARK Services"
    
    echo -e "${YELLOW}⚠️  This will remove all ARK service files${NC}"
    echo -n "Are you sure? (y/N): "
    read -r confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Cancelled."
        return 0
    fi
    
    # Stop services first
    stop_services
    
    # Disable services
    disable_services
    
    # Remove service files
    echo ""
    echo "Removing service files..."
    for service in ark-backend ark-redis ark-ollama; do
        local service_file="$(get_service_dir)/${service}.service"
        if [ -f "$service_file" ]; then
            rm -f "$service_file"
            echo "  Removed: $service"
        fi
    done
    
    # Reload systemd
    echo ""
    echo "🔄 Reloading systemd daemon..."
    if [ "$USE_USER_SERVICES" = true ]; then
        systemctl --user daemon-reload
    else
        sudo systemctl daemon-reload
    fi
    
    echo ""
    echo -e "${GREEN}✅ Services uninstalled${NC}"
    echo ""
}

show_help() {
    echo "ARK Systemd Service Manager"
    echo ""
    echo "USAGE:"
    echo "  ark-service install     Install systemd service files"
    echo "  ark-service enable      Enable auto-start on boot"
    echo "  ark-service disable     Disable auto-start"
    echo "  ark-service start       Start all services"
    echo "  ark-service stop        Stop all services"
    echo "  ark-service restart     Restart all services"
    echo "  ark-service status      Show service status"
    echo "  ark-service logs [srv]  Show service logs"
    echo "  ark-service uninstall   Remove service files"
    echo ""
    echo "EXAMPLES:"
    echo "  ark-service install                # First-time setup"
    echo "  ark-service enable && ark-service start   # Enable & start"
    echo "  ark-service logs ark-backend       # View backend logs"
    echo "  ark-service status                 # Check all services"
    echo ""
    echo "SERVICES:"
    echo "  • ark-backend  - ARK intelligent backend"
    echo "  • ark-redis    - Redis data store (if bundled)"
    echo "  • ark-ollama   - Ollama LLM service (if installed)"
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
# METHOD 1: Add to create-unified-ark.sh (Raspberry Pi)
# ------------------------------------------------------
# 1. Copy this file to enhancements/12-systemd-services.sh
#
# 2. In create-unified-ark.sh, after installation, add:
#
#    # Install systemd service manager
#    if command -v systemctl &>/dev/null && [ ! -d "/data/data/com.termux" ]; then
#        cp enhancements/12-systemd-services.sh "$INSTALL_DIR/bin/ark-service"
#        chmod +x "$INSTALL_DIR/bin/ark-service"
#        
#        # Optional: Auto-install services
#        if [ "$AUTO_SYSTEMD" = "true" ]; then
#            "$INSTALL_DIR/bin/ark-service" install
#            "$INSTALL_DIR/bin/ark-service" enable
#        fi
#    fi
#
# 3. Add to post-install message:
#
#    echo "  🚀 Setup services:   ark-service install && ark-service enable"
#
#
# METHOD 2: Manual Installation on Raspberry Pi
# ----------------------------------------------
# 1. Copy to ARK bin directory:
#    cp enhancements/12-systemd-services.sh ~/ark/bin/ark-service
#    chmod +x ~/ark/bin/ark-service
#
# 2. Install and enable services:
#    ark-service install
#    ark-service enable
#    ark-service start
#
# 3. Check status:
#    ark-service status
#
#
# BENEFITS:
# ---------
# ✅ Auto-start ARK on boot
# ✅ Automatic restart on failure
# ✅ Proper service dependency management
# ✅ Centralized logging with journald
# ✅ Resource limits protection
# ✅ User or system service support
# ✅ Easy service management
# ✅ Works on Raspberry Pi and Debian/Ubuntu
#
################################################################################
