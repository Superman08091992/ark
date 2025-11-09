#!/bin/bash
################################################################################
# ARK Enhancement #10: Configuration Wizard
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Interactive configuration wizard for ARK installation. Guides users through
# setup with smart defaults, validation, and helpful explanations.
#
# FEATURES:
# ---------
# ✅ Interactive prompts with smart defaults
# ✅ Configuration validation
# ✅ Port availability checking
# ✅ Network interface detection
# ✅ Ollama integration setup
# ✅ Redis configuration
# ✅ Environment file generation
# ✅ Service testing after configuration
# ✅ Reconfiguration support
# ✅ Import existing configuration
#
# USAGE:
# ------
# ark-config                    # Run configuration wizard
# ark-config --reconfigure      # Reconfigure existing installation
# ark-config --import <file>    # Import configuration from file
# ark-config --export <file>    # Export current configuration
# ark-config --show             # Show current configuration
# ark-config --reset            # Reset to defaults
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
CONFIG_BACKUP="$INSTALL_DIR/.env.backup"

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
    echo ""
}

prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local value
    
    echo -ne "${GREEN}${prompt}${NC} ${YELLOW}[${default}]${NC}: "
    read -r value
    
    if [ -z "$value" ]; then
        echo "$default"
    else
        echo "$value"
    fi
}

prompt_yes_no() {
    local prompt="$1"
    local default="$2"
    local value
    
    if [ "$default" = "y" ]; then
        echo -ne "${GREEN}${prompt}${NC} ${YELLOW}[Y/n]${NC}: "
    else
        echo -ne "${GREEN}${prompt}${NC} ${YELLOW}[y/N]${NC}: "
    fi
    
    read -r value
    value=${value:-$default}
    
    case "$value" in
        y|Y|yes|Yes|YES)
            echo "yes"
            ;;
        *)
            echo "no"
            ;;
    esac
}

is_port_available() {
    local port=$1
    ! netstat -tuln 2>/dev/null | grep -q ":${port} " && \
    ! lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1
}

get_local_ip() {
    # Try to get local IP address
    if command -v ip &>/dev/null; then
        ip route get 1 2>/dev/null | awk '{print $7; exit}'
    elif command -v ifconfig &>/dev/null; then
        ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n1
    else
        echo "127.0.0.1"
    fi
}

validate_port() {
    local port=$1
    
    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
        return 1
    fi
    
    if [ "$port" -lt 1024 ] || [ "$port" -gt 65535 ]; then
        return 1
    fi
    
    return 0
}

test_ollama_connection() {
    local host=$1
    curl -sf "${host}/api/tags" &>/dev/null
}

################################################################################
# Configuration Functions
################################################################################

configure_basic() {
    print_section "📦 Basic Configuration"
    
    # API Port
    local default_port=8000
    local api_port
    
    while true; do
        api_port=$(prompt_with_default "API Port" "$default_port")
        
        if validate_port "$api_port"; then
            if is_port_available "$api_port"; then
                ARK_API_PORT="$api_port"
                echo -e "${GREEN}✅ Port $api_port is available${NC}"
                break
            else
                echo -e "${YELLOW}⚠️  Port $api_port is in use. Try another port.${NC}"
            fi
        else
            echo -e "${RED}❌ Invalid port number. Must be between 1024-65535.${NC}"
        fi
    done
    
    # API Host
    local local_ip=$(get_local_ip)
    echo ""
    echo "Network interfaces:"
    echo "  • 0.0.0.0     - Listen on all interfaces (recommended)"
    echo "  • 127.0.0.1   - Listen on localhost only (secure)"
    echo "  • ${local_ip} - Listen on local network"
    
    ARK_API_HOST=$(prompt_with_default "API Host" "0.0.0.0")
    
    # Debug Mode
    echo ""
    local debug=$(prompt_yes_no "Enable debug mode?" "n")
    if [ "$debug" = "yes" ]; then
        ARK_DEBUG="true"
    else
        ARK_DEBUG="false"
    fi
}

configure_redis() {
    print_section "🔴 Redis Configuration"
    
    # Check if Redis is installed
    if command -v redis-server &>/dev/null; then
        echo -e "${GREEN}✅ Redis is installed${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis is not installed${NC}"
    fi
    
    # Redis Port
    local default_redis_port=6379
    local redis_port
    
    while true; do
        redis_port=$(prompt_with_default "Redis Port" "$default_redis_port")
        
        if validate_port "$redis_port"; then
            ARK_REDIS_PORT="$redis_port"
            break
        else
            echo -e "${RED}❌ Invalid port number.${NC}"
        fi
    done
    
    # Redis Host
    ARK_REDIS_HOST=$(prompt_with_default "Redis Host" "127.0.0.1")
    
    # Redis Password (optional)
    echo ""
    local use_password=$(prompt_yes_no "Use Redis password?" "n")
    if [ "$use_password" = "yes" ]; then
        echo -ne "${GREEN}Redis Password${NC}: "
        read -s ARK_REDIS_PASSWORD
        echo ""
    else
        ARK_REDIS_PASSWORD=""
    fi
}

configure_ollama() {
    print_section "🤖 Ollama Configuration"
    
    # Check if Ollama is installed
    if command -v ollama &>/dev/null; then
        echo -e "${GREEN}✅ Ollama is installed${NC}"
        
        # Check if Ollama is running
        if curl -sf http://localhost:11434/api/tags &>/dev/null; then
            echo -e "${GREEN}✅ Ollama service is running${NC}"
            
            # List available models
            echo ""
            echo "Installed models:"
            ollama list 2>/dev/null | tail -n +2 || echo "  (none)"
        else
            echo -e "${YELLOW}⚠️  Ollama service is not running${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Ollama is not installed${NC}"
        echo "   Run: ark-ollama install"
    fi
    
    echo ""
    
    # Ollama Host
    local default_ollama_host="http://127.0.0.1:11434"
    local ollama_host
    
    while true; do
        ollama_host=$(prompt_with_default "Ollama Host URL" "$default_ollama_host")
        
        echo -n "Testing connection... "
        if test_ollama_connection "$ollama_host"; then
            ARK_OLLAMA_HOST="$ollama_host"
            echo -e "${GREEN}✅ Connected!${NC}"
            break
        else
            echo -e "${YELLOW}⚠️  Cannot connect${NC}"
            local retry=$(prompt_yes_no "Use this URL anyway?" "n")
            if [ "$retry" = "yes" ]; then
                ARK_OLLAMA_HOST="$ollama_host"
                break
            fi
        fi
    done
    
    # Ollama Model
    echo ""
    echo "Popular models:"
    echo "  • llama3.2:1b  - Lightweight (1.3GB)"
    echo "  • llama3.2:3b  - Balanced (2GB)"
    echo "  • mistral      - High quality (4.1GB)"
    echo "  • codellama    - Code-focused (3.8GB)"
    
    ARK_OLLAMA_MODEL=$(prompt_with_default "Default Model" "llama3.2:1b")
}

configure_advanced() {
    print_section "⚙️  Advanced Configuration"
    
    local advanced=$(prompt_yes_no "Configure advanced settings?" "n")
    
    if [ "$advanced" = "yes" ]; then
        # Worker threads
        ARK_WORKERS=$(prompt_with_default "Worker Threads" "4")
        
        # Request timeout
        ARK_TIMEOUT=$(prompt_with_default "Request Timeout (seconds)" "30")
        
        # Max request size
        ARK_MAX_REQUEST_SIZE=$(prompt_with_default "Max Request Size (MB)" "10")
        
        # Log level
        echo ""
        echo "Log levels: DEBUG, INFO, WARNING, ERROR"
        ARK_LOG_LEVEL=$(prompt_with_default "Log Level" "INFO")
    else
        # Set defaults
        ARK_WORKERS="4"
        ARK_TIMEOUT="30"
        ARK_MAX_REQUEST_SIZE="10"
        ARK_LOG_LEVEL="INFO"
    fi
}

save_configuration() {
    print_section "💾 Saving Configuration"
    
    # Backup existing config
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$CONFIG_BACKUP"
        echo -e "${BLUE}ℹ️  Backed up existing configuration to .env.backup${NC}"
    fi
    
    # Create .env file
    cat > "$ENV_FILE" << EOF
# ARK Configuration
# Generated by Configuration Wizard on $(date)

# Basic Settings
ARK_API_PORT=${ARK_API_PORT}
ARK_API_HOST=${ARK_API_HOST}
ARK_DEBUG=${ARK_DEBUG}

# Redis Configuration
ARK_REDIS_HOST=${ARK_REDIS_HOST}
ARK_REDIS_PORT=${ARK_REDIS_PORT}
EOF

    # Add Redis password if set
    if [ -n "$ARK_REDIS_PASSWORD" ]; then
        echo "ARK_REDIS_PASSWORD=${ARK_REDIS_PASSWORD}" >> "$ENV_FILE"
    fi

    # Add Ollama configuration
    cat >> "$ENV_FILE" << EOF

# Ollama Configuration
ARK_OLLAMA_HOST=${ARK_OLLAMA_HOST}
ARK_OLLAMA_MODEL=${ARK_OLLAMA_MODEL}

# Advanced Settings
ARK_WORKERS=${ARK_WORKERS}
ARK_TIMEOUT=${ARK_TIMEOUT}
ARK_MAX_REQUEST_SIZE=${ARK_MAX_REQUEST_SIZE}
ARK_LOG_LEVEL=${ARK_LOG_LEVEL}
EOF

    echo -e "${GREEN}✅ Configuration saved to: $ENV_FILE${NC}"
}

show_configuration() {
    print_section "📋 Configuration Summary"
    
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}⚠️  No configuration file found${NC}"
        return 1
    fi
    
    echo "Basic Settings:"
    echo "  API Port:     ${ARK_API_PORT:-$(grep ARK_API_PORT "$ENV_FILE" | cut -d'=' -f2)}"
    echo "  API Host:     ${ARK_API_HOST:-$(grep ARK_API_HOST "$ENV_FILE" | cut -d'=' -f2)}"
    echo "  Debug Mode:   ${ARK_DEBUG:-$(grep ARK_DEBUG "$ENV_FILE" | cut -d'=' -f2)}"
    
    echo ""
    echo "Redis:"
    echo "  Host:         ${ARK_REDIS_HOST:-$(grep ARK_REDIS_HOST "$ENV_FILE" | cut -d'=' -f2)}"
    echo "  Port:         ${ARK_REDIS_PORT:-$(grep ARK_REDIS_PORT "$ENV_FILE" | cut -d'=' -f2)}"
    
    echo ""
    echo "Ollama:"
    echo "  Host:         ${ARK_OLLAMA_HOST:-$(grep ARK_OLLAMA_HOST "$ENV_FILE" | cut -d'=' -f2)}"
    echo "  Model:        ${ARK_OLLAMA_MODEL:-$(grep ARK_OLLAMA_MODEL "$ENV_FILE" | cut -d'=' -f2)}"
    
    echo ""
    echo "Configuration file: $ENV_FILE"
}

test_configuration() {
    print_section "🧪 Testing Configuration"
    
    local all_ok=true
    
    # Test API port
    echo -n "Port ${ARK_API_PORT} availability... "
    if is_port_available "$ARK_API_PORT"; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${YELLOW}⚠️  Port in use${NC}"
        all_ok=false
    fi
    
    # Test Redis connection
    echo -n "Redis connection... "
    if command -v redis-cli &>/dev/null; then
        if redis-cli -h "$ARK_REDIS_HOST" -p "$ARK_REDIS_PORT" ping &>/dev/null; then
            echo -e "${GREEN}✅${NC}"
        else
            echo -e "${YELLOW}⚠️  Cannot connect${NC}"
            all_ok=false
        fi
    else
        echo -e "${YELLOW}⚠️  redis-cli not found${NC}"
        all_ok=false
    fi
    
    # Test Ollama connection
    echo -n "Ollama connection... "
    if test_ollama_connection "$ARK_OLLAMA_HOST"; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${YELLOW}⚠️  Cannot connect${NC}"
        all_ok=false
    fi
    
    echo ""
    if [ "$all_ok" = true ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Some tests failed. Please review configuration.${NC}"
        return 1
    fi
}

################################################################################
# Command Handlers
################################################################################

run_wizard() {
    print_header "🧙 ARK Configuration Wizard"
    
    echo "This wizard will help you configure ARK."
    echo ""
    
    # Run configuration steps
    configure_basic
    configure_redis
    configure_ollama
    configure_advanced
    
    # Save configuration
    save_configuration
    
    # Show summary
    show_configuration
    
    # Test configuration
    echo ""
    local test=$(prompt_yes_no "Test configuration now?" "y")
    if [ "$test" = "yes" ]; then
        test_configuration
    fi
    
    # Final message
    echo ""
    print_header "🎉 Configuration Complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Review config:    cat $ENV_FILE"
    echo "  2. Start services:   ark start"
    echo "  3. Check health:     ark-health"
    echo ""
}

export_config() {
    local output_file="${1:-ark-config-export.env}"
    
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}❌ No configuration file found${NC}"
        exit 1
    fi
    
    cp "$ENV_FILE" "$output_file"
    echo -e "${GREEN}✅ Configuration exported to: $output_file${NC}"
}

import_config() {
    local input_file="$1"
    
    if [ -z "$input_file" ]; then
        echo -e "${RED}❌ Please specify a configuration file${NC}"
        exit 1
    fi
    
    if [ ! -f "$input_file" ]; then
        echo -e "${RED}❌ File not found: $input_file${NC}"
        exit 1
    fi
    
    # Backup current config
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$CONFIG_BACKUP"
    fi
    
    cp "$input_file" "$ENV_FILE"
    echo -e "${GREEN}✅ Configuration imported from: $input_file${NC}"
    echo -e "${BLUE}ℹ️  Previous configuration backed up to: $CONFIG_BACKUP${NC}"
}

reset_config() {
    echo -e "${YELLOW}⚠️  This will reset configuration to defaults${NC}"
    local confirm=$(prompt_yes_no "Are you sure?" "n")
    
    if [ "$confirm" = "yes" ]; then
        if [ -f "$ENV_FILE" ]; then
            cp "$ENV_FILE" "$CONFIG_BACKUP"
        fi
        
        # Set defaults
        ARK_API_PORT=8000
        ARK_API_HOST="0.0.0.0"
        ARK_DEBUG="false"
        ARK_REDIS_HOST="127.0.0.1"
        ARK_REDIS_PORT=6379
        ARK_REDIS_PASSWORD=""
        ARK_OLLAMA_HOST="http://127.0.0.1:11434"
        ARK_OLLAMA_MODEL="llama3.2:1b"
        ARK_WORKERS="4"
        ARK_TIMEOUT="30"
        ARK_MAX_REQUEST_SIZE="10"
        ARK_LOG_LEVEL="INFO"
        
        save_configuration
        echo -e "${GREEN}✅ Configuration reset to defaults${NC}"
    else
        echo "Cancelled."
    fi
}

show_help() {
    echo "ARK Configuration Wizard"
    echo ""
    echo "USAGE:"
    echo "  ark-config                    Run configuration wizard"
    echo "  ark-config --reconfigure      Reconfigure existing installation"
    echo "  ark-config --show             Show current configuration"
    echo "  ark-config --test             Test current configuration"
    echo "  ark-config --export <file>    Export configuration to file"
    echo "  ark-config --import <file>    Import configuration from file"
    echo "  ark-config --reset            Reset to default configuration"
    echo ""
    echo "EXAMPLES:"
    echo "  ark-config                              # Interactive setup"
    echo "  ark-config --export my-config.env       # Save configuration"
    echo "  ark-config --import my-config.env       # Load configuration"
    echo ""
}

################################################################################
# Main
################################################################################

main() {
    local command="${1:-wizard}"
    
    case $command in
        --reconfigure)
            run_wizard
            ;;
            
        --show)
            show_configuration
            ;;
            
        --test)
            if [ -f "$ENV_FILE" ]; then
                # Load configuration
                source "$ENV_FILE"
                test_configuration
            else
                echo -e "${RED}❌ No configuration file found${NC}"
                exit 1
            fi
            ;;
            
        --export)
            export_config "$2"
            ;;
            
        --import)
            import_config "$2"
            ;;
            
        --reset)
            reset_config
            ;;
            
        --help|-h|help)
            show_help
            ;;
            
        wizard|*)
            run_wizard
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
# 1. Copy this file to enhancements/10-configuration-wizard.sh
#
# 2. In create-unified-ark.sh, add after installation:
#
#    # Copy configuration wizard
#    cp enhancements/10-configuration-wizard.sh "$INSTALL_DIR/bin/ark-config"
#    chmod +x "$INSTALL_DIR/bin/ark-config"
#    
#    # Run wizard during installation (optional)
#    if [ "$INTERACTIVE" = "true" ]; then
#        "$INSTALL_DIR/bin/ark-config"
#    fi
#
# 3. Add to post-install message:
#
#    echo "  ⚙️  Configure ARK:    ark-config"
#
#
# METHOD 2: Manual Installation
# ------------------------------
# 1. Copy to your ARK bin directory:
#    cp enhancements/10-configuration-wizard.sh ~/ark/bin/ark-config
#    chmod +x ~/ark/bin/ark-config
#
# 2. Run wizard:
#    ark-config
#
#
# BENEFITS:
# ---------
# ✅ User-friendly interactive setup
# ✅ Smart defaults with validation
# ✅ Port availability checking
# ✅ Service connection testing
# ✅ Configuration import/export
# ✅ Reconfiguration support
# ✅ Network interface detection
# ✅ Comprehensive error checking
#
################################################################################
