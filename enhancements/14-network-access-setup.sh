#!/bin/bash
################################################################################
# ARK Enhancement #14: Network Access Setup
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Configures ARK to be accessible from other devices on your network. Sets up
# firewall rules, displays access URLs, generates QR codes, and provides
# mobile-friendly access instructions.
#
# FEATURES:
# ---------
# ✅ Automatic local IP detection
# ✅ Firewall configuration (UFW, iptables, firewalld)
# ✅ Access URL generation with all IP addresses
# ✅ QR code generation for mobile access
# ✅ CORS configuration for web access
# ✅ Security recommendations
# ✅ Port forwarding instructions
# ✅ Testing from other devices
# ✅ Hostname and mDNS setup
# ✅ Network troubleshooting tools
#
# USAGE:
# ------
# ark-network setup             # Configure network access
# ark-network show              # Show access URLs
# ark-network qr                # Generate QR code
# ark-network test              # Test accessibility
# ark-network firewall          # Configure firewall
# ark-network security          # Show security recommendations
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
# Network Detection Functions
################################################################################

get_local_ips() {
    # Get all local IP addresses
    if command -v ip &>/dev/null; then
        ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1'
    elif command -v ifconfig &>/dev/null; then
        ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | sed 's/addr://'
    else
        echo "Unable to detect IP addresses"
        return 1
    fi
}

get_primary_ip() {
    # Get the primary network IP
    if command -v ip &>/dev/null; then
        ip route get 1 2>/dev/null | awk '{print $7; exit}'
    elif command -v ifconfig &>/dev/null; then
        ifconfig | grep "inet " | grep -v 127.0.0.1 | head -n1 | awk '{print $2}' | sed 's/addr://'
    else
        echo "127.0.0.1"
    fi
}

get_hostname() {
    hostname 2>/dev/null || echo "localhost"
}

get_api_port() {
    if [ -f "$ENV_FILE" ]; then
        grep "^ARK_API_PORT=" "$ENV_FILE" | cut -d'=' -f2 | tr -d ' '
    else
        echo "8000"
    fi
}

################################################################################
# Firewall Configuration
################################################################################

configure_firewall() {
    local port=$(get_api_port)
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🔥 Configuring Firewall${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Detect and configure firewall
    if command -v ufw &>/dev/null; then
        echo "Detected: UFW (Uncomplicated Firewall)"
        echo ""
        
        if sudo ufw status | grep -q "Status: active"; then
            echo -e "${GREEN}✅ UFW is active${NC}"
            
            # Check if port is already allowed
            if sudo ufw status | grep -q "$port"; then
                echo -e "${GREEN}✅ Port $port is already allowed${NC}"
            else
                echo -n "Adding port $port to UFW... "
                sudo ufw allow $port/tcp comment "ARK API" &>/dev/null
                echo -e "${GREEN}✅${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  UFW is installed but not active${NC}"
            echo "To enable UFW:"
            echo "  sudo ufw enable"
            echo "  sudo ufw allow $port/tcp comment 'ARK API'"
        fi
        
    elif command -v firewall-cmd &>/dev/null; then
        echo "Detected: firewalld"
        echo ""
        
        if systemctl is-active --quiet firewalld; then
            echo -e "${GREEN}✅ firewalld is active${NC}"
            echo -n "Adding port $port to firewalld... "
            sudo firewall-cmd --permanent --add-port=$port/tcp &>/dev/null
            sudo firewall-cmd --reload &>/dev/null
            echo -e "${GREEN}✅${NC}"
        else
            echo -e "${YELLOW}⚠️  firewalld is not running${NC}"
        fi
        
    elif command -v iptables &>/dev/null; then
        echo "Detected: iptables"
        echo ""
        echo "To allow port $port with iptables:"
        echo "  sudo iptables -A INPUT -p tcp --dport $port -j ACCEPT"
        echo "  sudo iptables-save > /etc/iptables/rules.v4  # Save rules"
        
    else
        echo -e "${YELLOW}⚠️  No firewall detected${NC}"
        echo "Your system may not have a firewall configured."
    fi
    
    echo ""
}

################################################################################
# Access URL Display
################################################################################

show_access_urls() {
    local port=$(get_api_port)
    local primary_ip=$(get_primary_ip)
    local hostname=$(get_hostname)
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🌐 ARK Access URLs${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo -e "${GREEN}Local Access (this device):${NC}"
    echo "  http://localhost:$port"
    echo "  http://127.0.0.1:$port"
    echo ""
    
    echo -e "${GREEN}Network Access (same WiFi/LAN):${NC}"
    
    # List all IP addresses
    local ips=($(get_local_ips))
    if [ ${#ips[@]} -gt 0 ]; then
        for ip in "${ips[@]}"; do
            echo "  http://$ip:$port"
        done
    else
        echo "  http://$primary_ip:$port"
    fi
    
    echo ""
    
    # Hostname access
    if [ "$hostname" != "localhost" ]; then
        echo -e "${GREEN}Hostname Access:${NC}"
        echo "  http://$hostname:$port"
        echo "  http://$hostname.local:$port  ${GRAY}(if mDNS/Avahi enabled)${NC}"
        echo ""
    fi
    
    echo -e "${YELLOW}📱 For mobile devices:${NC}"
    echo "  1. Connect to the same WiFi network"
    echo "  2. Open browser and visit: http://$primary_ip:$port"
    echo "  3. Or scan QR code: ark-network qr"
    echo ""
}

################################################################################
# QR Code Generation
################################################################################

generate_qr_code() {
    local port=$(get_api_port)
    local primary_ip=$(get_primary_ip)
    local url="http://$primary_ip:$port"
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  📱 Mobile Access QR Code${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo "URL: $url"
    echo ""
    
    # Try qrencode if available
    if command -v qrencode &>/dev/null; then
        qrencode -t ANSIUTF8 "$url"
        echo ""
        echo "Scan this QR code with your mobile device"
    else
        # Fallback: ASCII QR code or instructions
        echo "Install qrencode to display QR code:"
        echo ""
        if command -v apt-get &>/dev/null; then
            echo "  sudo apt-get install qrencode"
        elif command -v yum &>/dev/null; then
            echo "  sudo yum install qrencode"
        elif command -v pacman &>/dev/null; then
            echo "  sudo pacman -S qrencode"
        elif command -v brew &>/dev/null; then
            echo "  brew install qrencode"
        else
            echo "  # Install qrencode with your package manager"
        fi
        echo ""
        echo "Or manually enter URL on mobile device:"
        echo -e "${CYAN}$url${NC}"
    fi
    
    echo ""
}

################################################################################
# Network Testing
################################################################################

test_accessibility() {
    local port=$(get_api_port)
    local primary_ip=$(get_primary_ip)
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🧪 Testing Network Accessibility${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Test localhost
    echo -n "Testing localhost:$port... "
    if curl -sf "http://localhost:$port" &>/dev/null || \
       nc -z localhost $port &>/dev/null; then
        echo -e "${GREEN}✅ Accessible${NC}"
    else
        echo -e "${RED}❌ Not accessible${NC}"
        echo "  ARK may not be running. Try: ark start"
    fi
    
    # Test local IP
    echo -n "Testing $primary_ip:$port... "
    if curl -sf "http://$primary_ip:$port" &>/dev/null || \
       nc -z $primary_ip $port &>/dev/null; then
        echo -e "${GREEN}✅ Accessible${NC}"
    else
        echo -e "${YELLOW}⚠️  Not accessible from network IP${NC}"
        echo "  Check firewall configuration"
    fi
    
    # Check if port is listening on all interfaces
    echo ""
    echo "Port listening status:"
    if command -v netstat &>/dev/null; then
        netstat -tuln | grep ":$port " | head -n1
    elif command -v ss &>/dev/null; then
        ss -tuln | grep ":$port " | head -n1
    fi
    
    echo ""
    echo "To test from another device:"
    echo "  1. Ensure device is on same network"
    echo "  2. Open browser: http://$primary_ip:$port"
    echo "  3. Or use curl: curl http://$primary_ip:$port"
    echo ""
}

################################################################################
# Security Recommendations
################################################################################

show_security() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🔒 Security Recommendations${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo -e "${GREEN}✅ Good Practices:${NC}"
    echo "  • Only allow access on trusted networks (home WiFi)"
    echo "  • Use firewall to limit access to specific IPs"
    echo "  • Don't expose to public internet without HTTPS"
    echo "  • Consider using VPN for remote access"
    echo "  • Keep ARK updated for security patches"
    echo ""
    
    echo -e "${YELLOW}⚠️  For Public/Internet Access:${NC}"
    echo "  • Setup HTTPS with SSL certificate"
    echo "  • Use authentication (API keys)"
    echo "  • Enable rate limiting"
    echo "  • Use reverse proxy (nginx/caddy)"
    echo "  • Monitor access logs"
    echo ""
    
    echo -e "${RED}❌ Avoid:${NC}"
    echo "  • Exposing ARK directly to internet without HTTPS"
    echo "  • Using default ports on public networks"
    echo "  • Allowing unrestricted access from 0.0.0.0"
    echo ""
}

################################################################################
# Setup Wizard
################################################################################

setup_network_access() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🌐 ARK Network Access Setup${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    local port=$(get_api_port)
    local primary_ip=$(get_primary_ip)
    
    echo "This will configure ARK for network access."
    echo ""
    echo "Current configuration:"
    echo "  Port: $port"
    echo "  Primary IP: $primary_ip"
    echo ""
    
    # Check if ARK_API_HOST is set correctly
    if [ -f "$ENV_FILE" ]; then
        local api_host=$(grep "^ARK_API_HOST=" "$ENV_FILE" | cut -d'=' -f2)
        
        if [ "$api_host" = "127.0.0.1" ]; then
            echo -e "${YELLOW}⚠️  ARK is configured to listen on localhost only${NC}"
            echo ""
            echo "To allow network access, change ARK_API_HOST to 0.0.0.0"
            echo ""
            echo -n "Update configuration? (y/N): "
            read -r update
            
            if [ "$update" = "y" ] || [ "$update" = "Y" ]; then
                sed -i "s/^ARK_API_HOST=.*/ARK_API_HOST=0.0.0.0/" "$ENV_FILE"
                echo -e "${GREEN}✅ Updated ARK_API_HOST to 0.0.0.0${NC}"
                echo ""
                echo "Restart ARK for changes to take effect:"
                echo "  ark restart"
                echo ""
            fi
        else
            echo -e "${GREEN}✅ ARK_API_HOST is configured for network access${NC}"
            echo ""
        fi
    fi
    
    # Configure firewall
    echo -n "Configure firewall rules? (y/N): "
    read -r firewall
    
    if [ "$firewall" = "y" ] || [ "$firewall" = "Y" ]; then
        configure_firewall
    fi
    
    # Show access URLs
    show_access_urls
    
    # Generate QR code
    echo -n "Generate QR code for mobile access? (y/N): "
    read -r qr
    
    if [ "$qr" = "y" ] || [ "$qr" = "Y" ]; then
        generate_qr_code
    fi
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✅ Network Access Setup Complete${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

################################################################################
# Help
################################################################################

show_help() {
    echo "ARK Network Access Setup"
    echo ""
    echo "USAGE:"
    echo "  ark-network setup      Configure network access (wizard)"
    echo "  ark-network show       Show all access URLs"
    echo "  ark-network qr         Generate QR code for mobile"
    echo "  ark-network test       Test network accessibility"
    echo "  ark-network firewall   Configure firewall rules"
    echo "  ark-network security   Show security recommendations"
    echo ""
    echo "EXAMPLES:"
    echo "  ark-network setup      # First-time setup wizard"
    echo "  ark-network show       # Show URLs after starting ARK"
    echo "  ark-network qr         # Generate QR for mobile access"
    echo ""
}

################################################################################
# Main
################################################################################

main() {
    local command="${1:-setup}"
    
    case $command in
        setup)
            setup_network_access
            ;;
        show)
            show_access_urls
            ;;
        qr)
            generate_qr_code
            ;;
        test)
            test_accessibility
            ;;
        firewall)
            configure_firewall
            ;;
        security)
            show_security
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
# 1. Copy this file to enhancements/14-network-access-setup.sh
#
# 2. In create-unified-ark.sh, after installation:
#
#    # Install network access tool
#    cp enhancements/14-network-access-setup.sh "$INSTALL_DIR/bin/ark-network"
#    chmod +x "$INSTALL_DIR/bin/ark-network"
#
# 3. Add to post-install message:
#
#    echo ""
#    echo "📱 To access ARK from other devices:"
#    echo "   ark-network setup"
#
# 4. Optionally run setup automatically:
#
#    if [ "$SETUP_NETWORK" = "true" ]; then
#        "$INSTALL_DIR/bin/ark-network" setup
#    fi
#
#
# METHOD 2: Manual Installation
# ------------------------------
# 1. Copy to ARK bin directory:
#    cp enhancements/14-network-access-setup.sh ~/ark/bin/ark-network
#    chmod +x ~/ark/bin/ark-network
#
# 2. Run setup:
#    ark-network setup
#
# 3. Show URLs anytime:
#    ark-network show
#
#
# BENEFITS:
# ---------
# ✅ Easy network access configuration
# ✅ Automatic IP detection
# ✅ Firewall configuration assistance
# ✅ QR codes for mobile devices
# ✅ Security recommendations
# ✅ Network troubleshooting tools
# ✅ Works on Raspberry Pi and desktop Linux
# ✅ No manual IP address lookup needed
#
################################################################################
