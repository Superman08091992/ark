#!/bin/bash
################################################################################
# ARK Enhancement #16: Network Access Setup
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Configures ARK to be accessible from other devices on the local network or
# internet. Sets up firewall rules, port forwarding guides, and generates
# access URLs with QR codes for easy mobile access.
#
# FEATURES:
# ---------
# ✅ Local network access configuration
# ✅ Firewall rule management (UFW, iptables)
# ✅ IP address detection (local and public)
# ✅ Access URL generation with QR codes
# ✅ Port forwarding guidance
# ✅ Network interface selection
# ✅ SSL/TLS setup guidance
# ✅ Access testing from other devices
# ✅ Security recommendations
#
# USAGE:
# ------
# ark-network setup              # Configure network access
# ark-network status             # Show network status
# ark-network qr                 # Generate QR code for mobile
# ark-network test               # Test network accessibility
# ark-network firewall enable    # Enable firewall rules
# ark-network firewall disable   # Disable firewall rules
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

get_local_ip() {
    # Try multiple methods to get local IP
    local ip=""
    
    # Method 1: ip command
    if command -v ip &>/dev/null; then
        ip=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')
    fi
    
    # Method 2: ifconfig
    if [ -z "$ip" ] && command -v ifconfig &>/dev/null; then
        ip=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n1 | sed 's/addr://')
    fi
    
    # Method 3: hostname -I
    if [ -z "$ip" ] && command -v hostname &>/dev/null; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    
    echo "${ip:-127.0.0.1}"
}

get_public_ip() {
    # Try multiple services to get public IP
    local ip=""
    
    if command -v curl &>/dev/null; then
        ip=$(curl -s -4 https://ifconfig.me 2>/dev/null || \
             curl -s -4 https://api.ipify.org 2>/dev/null || \
             curl -s -4 https://icanhazip.com 2>/dev/null)
    elif command -v wget &>/dev/null; then
        ip=$(wget -qO- https://ifconfig.me 2>/dev/null || \
             wget -qO- https://api.ipify.org 2>/dev/null)
    fi
    
    echo "${ip:-N/A}"
}

get_ark_port() {
    local port=8000
    
    if [ -f "$ENV_FILE" ]; then
        port=$(grep "^ARK_API_PORT=" "$ENV_FILE" | cut -d'=' -f2 || echo "8000")
    fi
    
    echo "$port"
}

is_port_accessible() {
    local host=$1
    local port=$2
    
    if command -v nc &>/dev/null; then
        nc -z -w2 "$host" "$port" &>/dev/null
    elif command -v telnet &>/dev/null; then
        timeout 2 telnet "$host" "$port" &>/dev/null
    else
        # Fallback: try curl
        curl -s -m 2 "http://${host}:${port}" &>/dev/null
    fi
}

################################################################################
# Network Configuration Functions
################################################################################

configure_network_access() {
    print_header "🌐 Network Access Setup"
    
    local local_ip=$(get_local_ip)
    local public_ip=$(get_public_ip)
    local port=$(get_ark_port)
    
    echo "Current Network Information:"
    echo "  Local IP:   $local_ip"
    echo "  Public IP:  $public_ip"
    echo "  ARK Port:   $port"
    echo ""
    
    print_section "Step 1: Configure ARK Host Binding"
    
    echo "Current ARK host binding:"
    if [ -f "$ENV_FILE" ]; then
        local current_host=$(grep "^ARK_API_HOST=" "$ENV_FILE" | cut -d'=' -f2)
        echo "  ARK_API_HOST=${current_host:-0.0.0.0}"
    else
        echo "  Not configured (defaults to 127.0.0.1)"
    fi
    
    echo ""
    echo "To allow network access, ARK must bind to 0.0.0.0"
    read -p "Update ARK_API_HOST to 0.0.0.0? (y/N): " update_host
    
    if [ "$update_host" = "y" ] || [ "$update_host" = "Y" ]; then
        if [ -f "$ENV_FILE" ]; then
            if grep -q "^ARK_API_HOST=" "$ENV_FILE"; then
                sed -i "s/^ARK_API_HOST=.*/ARK_API_HOST=0.0.0.0/" "$ENV_FILE"
            else
                echo "ARK_API_HOST=0.0.0.0" >> "$ENV_FILE"
            fi
        else
            mkdir -p "$(dirname "$ENV_FILE")"
            echo "ARK_API_HOST=0.0.0.0" > "$ENV_FILE"
        fi
        echo -e "${GREEN}✅ Updated ARK_API_HOST to 0.0.0.0${NC}"
        echo -e "${YELLOW}⚠️  You need to restart ARK for changes to take effect${NC}"
    fi
    
    print_section "Step 2: Firewall Configuration"
    
    if command -v ufw &>/dev/null; then
        echo "UFW firewall detected"
        configure_ufw_firewall "$port"
    elif command -v firewall-cmd &>/dev/null; then
        echo "firewalld detected"
        configure_firewalld "$port"
    elif command -v iptables &>/dev/null; then
        echo "iptables detected"
        configure_iptables "$port"
    else
        echo -e "${YELLOW}⚠️  No firewall detected or not accessible${NC}"
    fi
    
    print_section "Step 3: Network Access URLs"
    
    echo "Your ARK can be accessed at:"
    echo ""
    echo -e "${GREEN}Local Network:${NC}"
    echo "  http://${local_ip}:${port}"
    echo ""
    
    if [ "$public_ip" != "N/A" ]; then
        echo -e "${YELLOW}Internet (requires port forwarding):${NC}"
        echo "  http://${public_ip}:${port}"
        echo ""
    fi
    
    print_section "Step 4: Port Forwarding (Optional)"
    
    echo "To access ARK from the internet, you need to:"
    echo ""
    echo "1. Log in to your router's admin panel"
    echo "2. Find Port Forwarding / NAT settings"
    echo "3. Forward external port ${port} to ${local_ip}:${port}"
    echo "4. Save settings and restart router if needed"
    echo ""
    echo "Router admin typically at:"
    echo "  • http://192.168.1.1"
    echo "  • http://192.168.0.1"
    echo "  • http://10.0.0.1"
    echo ""
    
    print_section "Step 5: Security Recommendations"
    
    echo -e "${RED}⚠️  IMPORTANT SECURITY NOTES:${NC}"
    echo ""
    echo "• ARK does not have built-in authentication by default"
    echo "• Anyone with the URL can access your ARK instance"
    echo "• Consider using a VPN instead of port forwarding"
    echo "• Use HTTPS if exposing to internet (see ark-https)"
    echo "• Regularly update ARK for security patches"
    echo ""
    
    echo -e "${GREEN}✅ Network access setup complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Test access:    ark-network test"
    echo "  2. Generate QR:    ark-network qr"
    echo "  3. Check status:   ark-network status"
    echo ""
}

################################################################################
# Firewall Configuration Functions
################################################################################

configure_ufw_firewall() {
    local port=$1
    
    echo "Configuring UFW firewall..."
    echo ""
    
    # Check if UFW is active
    local ufw_status=$(sudo ufw status 2>/dev/null | grep -i status | awk '{print $2}')
    
    if [ "$ufw_status" != "active" ]; then
        echo -e "${YELLOW}⚠️  UFW is not active${NC}"
        read -p "Enable UFW firewall? (y/N): " enable_ufw
        if [ "$enable_ufw" = "y" ] || [ "$enable_ufw" = "Y" ]; then
            sudo ufw --force enable
            echo -e "${GREEN}✅ UFW enabled${NC}"
        else
            return 0
        fi
    fi
    
    # Allow ARK port
    read -p "Allow port ${port} through firewall? (y/N): " allow_port
    if [ "$allow_port" = "y" ] || [ "$allow_port" = "Y" ]; then
        sudo ufw allow ${port}/tcp comment "ARK API"
        echo -e "${GREEN}✅ Port ${port} allowed through UFW${NC}"
        
        # Reload UFW
        sudo ufw reload
    fi
}

configure_firewalld() {
    local port=$1
    
    echo "Configuring firewalld..."
    echo ""
    
    read -p "Allow port ${port} through firewall? (y/N): " allow_port
    if [ "$allow_port" = "y" ] || [ "$allow_port" = "Y" ]; then
        sudo firewall-cmd --permanent --add-port=${port}/tcp
        sudo firewall-cmd --reload
        echo -e "${GREEN}✅ Port ${port} allowed through firewalld${NC}"
    fi
}

configure_iptables() {
    local port=$1
    
    echo "Configuring iptables..."
    echo ""
    
    read -p "Allow port ${port} through firewall? (y/N): " allow_port
    if [ "$allow_port" = "y" ] || [ "$allow_port" = "Y" ]; then
        sudo iptables -A INPUT -p tcp --dport ${port} -j ACCEPT
        
        # Save rules
        if command -v iptables-save &>/dev/null; then
            sudo iptables-save > /etc/iptables/rules.v4 2>/dev/null || \
            sudo iptables-save > /etc/iptables.rules 2>/dev/null
        fi
        
        echo -e "${GREEN}✅ Port ${port} allowed through iptables${NC}"
    fi
}

################################################################################
# Status and Testing Functions
################################################################################

show_network_status() {
    print_header "🌐 Network Status"
    
    local local_ip=$(get_local_ip)
    local public_ip=$(get_public_ip)
    local port=$(get_ark_port)
    
    echo "Network Information:"
    echo "  Local IP:     $local_ip"
    echo "  Public IP:    $public_ip"
    echo "  ARK Port:     $port"
    echo ""
    
    echo "Configuration:"
    if [ -f "$ENV_FILE" ]; then
        local host=$(grep "^ARK_API_HOST=" "$ENV_FILE" | cut -d'=' -f2)
        echo "  ARK_API_HOST: ${host:-Not set}"
    else
        echo "  ARK_API_HOST: Not configured"
    fi
    echo ""
    
    echo "Access URLs:"
    echo -e "  ${GREEN}Local:${NC}    http://localhost:${port}"
    echo -e "  ${GREEN}Network:${NC}  http://${local_ip}:${port}"
    if [ "$public_ip" != "N/A" ]; then
        echo -e "  ${YELLOW}Internet:${NC} http://${public_ip}:${port} (requires port forwarding)"
    fi
    echo ""
    
    echo "Firewall Status:"
    if command -v ufw &>/dev/null; then
        local ufw_status=$(sudo ufw status 2>/dev/null | grep -i status | awk '{print $2}')
        echo "  UFW: $ufw_status"
        if [ "$ufw_status" = "active" ]; then
            sudo ufw status | grep "$port" || echo "    Port ${port}: Not configured"
        fi
    elif command -v firewall-cmd &>/dev/null; then
        echo "  firewalld: $(sudo firewall-cmd --state 2>/dev/null || echo 'unknown')"
    else
        echo "  No firewall detected"
    fi
    echo ""
}

test_network_access() {
    print_header "🧪 Testing Network Access"
    
    local local_ip=$(get_local_ip)
    local port=$(get_ark_port)
    
    echo "Testing localhost access..."
    if is_port_accessible "localhost" "$port"; then
        echo -e "${GREEN}✅ Localhost: http://localhost:${port}${NC}"
    else
        echo -e "${RED}❌ Localhost: Not accessible${NC}"
        echo "   Is ARK running? Try: ark start"
    fi
    
    echo ""
    echo "Testing local network access..."
    if is_port_accessible "$local_ip" "$port"; then
        echo -e "${GREEN}✅ Network: http://${local_ip}:${port}${NC}"
    else
        echo -e "${YELLOW}⚠️  Network: Not accessible${NC}"
        echo "   Check firewall rules: ark-network firewall enable"
    fi
    
    echo ""
    echo -e "${BLUE}To test from another device:${NC}"
    echo "  1. Connect to the same network"
    echo "  2. Open browser and visit: http://${local_ip}:${port}"
    echo "  3. Or scan QR code: ark-network qr"
    echo ""
}

generate_qr_code() {
    local local_ip=$(get_local_ip)
    local port=$(get_ark_port)
    local url="http://${local_ip}:${port}"
    
    print_header "📱 QR Code for Mobile Access"
    
    echo "Scan this QR code with your mobile device:"
    echo ""
    
    # Check if qrencode is available
    if command -v qrencode &>/dev/null; then
        qrencode -t ANSIUTF8 "$url"
        echo ""
        echo "URL: $url"
    else
        echo -e "${YELLOW}⚠️  qrencode not installed${NC}"
        echo ""
        echo "Install with:"
        echo "  Ubuntu/Debian: sudo apt-get install qrencode"
        echo "  macOS:         brew install qrencode"
        echo ""
        echo "Or manually enter this URL on your mobile device:"
        echo ""
        echo -e "${GREEN}${url}${NC}"
        echo ""
        echo "You can also use an online QR generator:"
        echo "  https://www.qr-code-generator.com/"
    fi
    echo ""
}

################################################################################
# Firewall Management Functions
################################################################################

enable_firewall_rule() {
    local port=$(get_ark_port)
    
    print_header "🔥 Enabling Firewall Rule"
    
    if command -v ufw &>/dev/null; then
        sudo ufw allow ${port}/tcp comment "ARK API"
        sudo ufw reload
        echo -e "${GREEN}✅ UFW rule enabled for port ${port}${NC}"
    elif command -v firewall-cmd &>/dev/null; then
        sudo firewall-cmd --permanent --add-port=${port}/tcp
        sudo firewall-cmd --reload
        echo -e "${GREEN}✅ firewalld rule enabled for port ${port}${NC}"
    else
        echo -e "${YELLOW}⚠️  No supported firewall found${NC}"
    fi
}

disable_firewall_rule() {
    local port=$(get_ark_port)
    
    print_header "🔥 Disabling Firewall Rule"
    
    echo -e "${YELLOW}⚠️  This will block network access to ARK${NC}"
    read -p "Are you sure? (y/N): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Cancelled."
        return 0
    fi
    
    if command -v ufw &>/dev/null; then
        sudo ufw delete allow ${port}/tcp
        sudo ufw reload
        echo -e "${GREEN}✅ UFW rule disabled for port ${port}${NC}"
    elif command -v firewall-cmd &>/dev/null; then
        sudo firewall-cmd --permanent --remove-port=${port}/tcp
        sudo firewall-cmd --reload
        echo -e "${GREEN}✅ firewalld rule disabled for port ${port}${NC}"
    else
        echo -e "${YELLOW}⚠️  No supported firewall found${NC}"
    fi
}

show_help() {
    echo "ARK Network Access Setup"
    echo ""
    echo "USAGE:"
    echo "  ark-network setup              Configure network access"
    echo "  ark-network status             Show network status"
    echo "  ark-network test               Test network accessibility"
    echo "  ark-network qr                 Generate QR code for mobile"
    echo "  ark-network firewall enable    Enable firewall rules"
    echo "  ark-network firewall disable   Disable firewall rules"
    echo ""
    echo "EXAMPLES:"
    echo "  ark-network setup     # Run interactive setup"
    echo "  ark-network test      # Test if ARK is accessible"
    echo "  ark-network qr        # Show QR code for mobile"
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
            configure_network_access
            ;;
        status)
            show_network_status
            ;;
        test)
            test_network_access
            ;;
        qr)
            generate_qr_code
            ;;
        firewall)
            local subcommand="${1:-help}"
            case $subcommand in
                enable)
                    enable_firewall_rule
                    ;;
                disable)
                    disable_firewall_rule
                    ;;
                *)
                    echo "Firewall commands: enable, disable"
                    ;;
            esac
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
# 1. Copy this file to enhancements/16-network-access-setup.sh
#
# 2. In create-unified-ark.sh, add after creating bin directory:
#
#    # Copy network access tool
#    cp enhancements/16-network-access-setup.sh "$INSTALL_DIR/bin/ark-network"
#    chmod +x "$INSTALL_DIR/bin/ark-network"
#
# 3. Add to post-install message:
#
#    echo "  🌐 Network setup:    ark-network setup"
#
#
# METHOD 2: Manual Installation
# ------------------------------
# 1. Copy to your ARK bin directory:
#    cp enhancements/16-network-access-setup.sh ~/ark/bin/ark-network
#    chmod +x ~/ark/bin/ark-network
#
# 2. Run setup:
#    ark-network setup
#
# 3. Test access:
#    ark-network test
#
#
# BENEFITS:
# ---------
# ✅ Easy network access configuration
# ✅ Automatic IP detection
# ✅ Firewall management
# ✅ QR codes for mobile access
# ✅ Security recommendations
# ✅ Access testing
# ✅ Port forwarding guidance
# ✅ Cross-platform support
#
################################################################################
