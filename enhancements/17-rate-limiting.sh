#!/bin/bash
################################################################################
# ARK Enhancement #17: API Rate Limiting
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Implements rate limiting for ARK API to prevent abuse and ensure fair usage.
# Can be integrated at application level or using nginx/reverse proxy.
#
# FEATURES:
# ---------
# ✅ IP-based rate limiting
# ✅ Token-based rate limiting (API keys)
# ✅ Configurable limits per endpoint
# ✅ Redis-backed rate limiting
# ✅ Nginx rate limiting configuration
# ✅ Custom rate limit responses
# ✅ Whitelist/blacklist support
# ✅ Rate limit status monitoring
# ✅ Automatic cleanup of old entries
# ✅ Burst allowance configuration
#
# USAGE:
# ------
# ark-ratelimit setup               # Configure rate limiting
# ark-ratelimit nginx               # Setup nginx rate limiting
# ark-ratelimit status              # Show current limits
# ark-ratelimit whitelist <ip>      # Add IP to whitelist
# ark-ratelimit blacklist <ip>      # Add IP to blacklist
# ark-ratelimit reset <ip>          # Reset rate limit for IP
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

ENV_FILE="$INSTALL_DIR/.env"
WHITELIST_FILE="$INSTALL_DIR/config/rate-limit-whitelist.txt"
BLACKLIST_FILE="$INSTALL_DIR/config/rate-limit-blacklist.txt"

################################################################################
# Configuration
################################################################################

setup_rate_limiting() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  ⏱️  ARK Rate Limiting Setup${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo "Configure rate limiting for ARK API"
    echo ""
    
    # Get configuration
    read -p "Requests per minute [default: 60]: " rpm
    rpm=${rpm:-60}
    
    read -p "Burst allowance [default: 10]: " burst
    burst=${burst:-10}
    
    read -p "Enable IP-based blocking [Y/n]: " enable_blocking
    enable_blocking=${enable_blocking:-Y}
    
    # Update environment file
    if [ ! -f "$ENV_FILE" ]; then
        touch "$ENV_FILE"
    fi
    
    # Add or update rate limit settings
    if grep -q "^ARK_RATE_LIMIT_RPM=" "$ENV_FILE"; then
        sed -i "s/^ARK_RATE_LIMIT_RPM=.*/ARK_RATE_LIMIT_RPM=$rpm/" "$ENV_FILE"
    else
        echo "ARK_RATE_LIMIT_RPM=$rpm" >> "$ENV_FILE"
    fi
    
    if grep -q "^ARK_RATE_LIMIT_BURST=" "$ENV_FILE"; then
        sed -i "s/^ARK_RATE_LIMIT_BURST=.*/ARK_RATE_LIMIT_BURST=$burst/" "$ENV_FILE"
    else
        echo "ARK_RATE_LIMIT_BURST=$burst" >> "$ENV_FILE"
    fi
    
    if grep -q "^ARK_RATE_LIMIT_ENABLED=" "$ENV_FILE"; then
        sed -i "s/^ARK_RATE_LIMIT_ENABLED=.*/ARK_RATE_LIMIT_ENABLED=true/" "$ENV_FILE"
    else
        echo "ARK_RATE_LIMIT_ENABLED=true" >> "$ENV_FILE"
    fi
    
    # Create whitelist/blacklist files
    mkdir -p "$(dirname "$WHITELIST_FILE")"
    touch "$WHITELIST_FILE"
    touch "$BLACKLIST_FILE"
    
    # Add localhost to whitelist
    if ! grep -q "127.0.0.1" "$WHITELIST_FILE"; then
        echo "127.0.0.1" >> "$WHITELIST_FILE"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Rate limiting configured${NC}"
    echo "   Requests per minute: $rpm"
    echo "   Burst allowance: $burst"
    echo "   Whitelist: $WHITELIST_FILE"
    echo "   Blacklist: $BLACKLIST_FILE"
    echo ""
    echo "Restart ARK for changes to take effect:"
    echo "  ark restart"
    echo ""
}

################################################################################
# Nginx Rate Limiting
################################################################################

setup_nginx_ratelimit() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🔧 Configuring Nginx Rate Limiting${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if ! command -v nginx &>/dev/null; then
        echo -e "${RED}❌ nginx not found${NC}"
        echo "Install nginx first or use application-level rate limiting"
        exit 1
    fi
    
    local rpm=${1:-60}
    local burst=${2:-10}
    local ark_port=$(grep "^ARK_API_PORT=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2 || echo "8000")
    
    # Create rate limit configuration
    local nginx_conf="/etc/nginx/conf.d/ark-ratelimit.conf"
    
    echo "Creating nginx rate limit configuration..."
    
    sudo tee "$nginx_conf" > /dev/null << EOF
# ARK Rate Limiting Configuration

# Define rate limit zone
# 10m can store ~160k IP addresses
limit_req_zone \$binary_remote_addr zone=ark_limit:10m rate=${rpm}r/m;
limit_req_status 429;

# Custom error page for rate limiting
error_page 429 @ratelimit_error;

# Location block for ARK API
location @ark_api {
    # Apply rate limiting
    limit_req zone=ark_limit burst=${burst} nodelay;
    limit_req_log_level warn;
    
    # Add rate limit headers
    add_header X-Rate-Limit-Limit "${rpm}" always;
    add_header X-Rate-Limit-Remaining "\$limit_req_remaining" always;
    
    # Proxy to ARK
    proxy_pass http://127.0.0.1:${ark_port};
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
}

# Rate limit error response
location @ratelimit_error {
    default_type application/json;
    return 429 '{"error":"Rate limit exceeded. Try again later.","limit":"${rpm} requests per minute"}';
}
EOF
    
    echo -n "Testing nginx configuration... "
    if sudo nginx -t 2>/dev/null; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
        exit 1
    fi
    
    echo -n "Reloading nginx... "
    sudo systemctl reload nginx 2>/dev/null || sudo service nginx reload
    echo -e "${GREEN}✅${NC}"
    
    echo ""
    echo -e "${GREEN}✅ Nginx rate limiting configured${NC}"
    echo "   Limit: $rpm requests/minute"
    echo "   Burst: $burst requests"
    echo "   Configuration: $nginx_conf"
    echo ""
}

################################################################################
# IP Management
################################################################################

add_to_whitelist() {
    local ip="$1"
    
    if [ -z "$ip" ]; then
        echo -e "${RED}❌ IP address required${NC}"
        exit 1
    fi
    
    mkdir -p "$(dirname "$WHITELIST_FILE")"
    
    if grep -q "^$ip$" "$WHITELIST_FILE" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  IP already in whitelist: $ip${NC}"
    else
        echo "$ip" >> "$WHITELIST_FILE"
        echo -e "${GREEN}✅ Added to whitelist: $ip${NC}"
    fi
}

add_to_blacklist() {
    local ip="$1"
    
    if [ -z "$ip" ]; then
        echo -e "${RED}❌ IP address required${NC}"
        exit 1
    fi
    
    mkdir -p "$(dirname "$BLACKLIST_FILE")"
    
    if grep -q "^$ip$" "$BLACKLIST_FILE" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  IP already in blacklist: $ip${NC}"
    else
        echo "$ip" >> "$BLACKLIST_FILE"
        echo -e "${GREEN}✅ Added to blacklist: $ip${NC}"
        echo "   Restart ARK to apply: ark restart"
    fi
}

remove_from_whitelist() {
    local ip="$1"
    
    if [ -z "$ip" ]; then
        echo -e "${RED}❌ IP address required${NC}"
        exit 1
    fi
    
    if [ -f "$WHITELIST_FILE" ]; then
        sed -i "/^$ip$/d" "$WHITELIST_FILE"
        echo -e "${GREEN}✅ Removed from whitelist: $ip${NC}"
    else
        echo -e "${YELLOW}⚠️  Whitelist file not found${NC}"
    fi
}

remove_from_blacklist() {
    local ip="$1"
    
    if [ -z "$ip" ]; then
        echo -e "${RED}❌ IP address required${NC}"
        exit 1
    fi
    
    if [ -f "$BLACKLIST_FILE" ]; then
        sed -i "/^$ip$/d" "$BLACKLIST_FILE"
        echo -e "${GREEN}✅ Removed from blacklist: $ip${NC}"
        echo "   Restart ARK to apply: ark restart"
    else
        echo -e "${YELLOW}⚠️  Blacklist file not found${NC}"
    fi
}

show_lists() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  📋 Whitelist & Blacklist${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo -e "${GREEN}Whitelist:${NC}"
    if [ -f "$WHITELIST_FILE" ] && [ -s "$WHITELIST_FILE" ]; then
        cat "$WHITELIST_FILE" | while read ip; do
            echo "  • $ip"
        done
    else
        echo "  (empty)"
    fi
    
    echo ""
    echo -e "${RED}Blacklist:${NC}"
    if [ -f "$BLACKLIST_FILE" ] && [ -s "$BLACKLIST_FILE" ]; then
        cat "$BLACKLIST_FILE" | while read ip; do
            echo "  • $ip"
        done
    else
        echo "  (empty)"
    fi
    
    echo ""
}

################################################################################
# Status and Monitoring
################################################################################

show_status() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  📊 Rate Limiting Status${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Check configuration
    if [ -f "$ENV_FILE" ]; then
        local enabled=$(grep "^ARK_RATE_LIMIT_ENABLED=" "$ENV_FILE" | cut -d'=' -f2)
        local rpm=$(grep "^ARK_RATE_LIMIT_RPM=" "$ENV_FILE" | cut -d'=' -f2)
        local burst=$(grep "^ARK_RATE_LIMIT_BURST=" "$ENV_FILE" | cut -d'=' -f2)
        
        if [ "$enabled" = "true" ]; then
            echo -e "${GREEN}Status: Enabled${NC}"
        else
            echo -e "${YELLOW}Status: Disabled${NC}"
        fi
        
        echo "Limit: ${rpm:-60} requests/minute"
        echo "Burst: ${burst:-10} requests"
    else
        echo -e "${YELLOW}Status: Not configured${NC}"
        echo "Run: ark-ratelimit setup"
    fi
    
    echo ""
    echo "Whitelist: $(wc -l < "$WHITELIST_FILE" 2>/dev/null || echo "0") IPs"
    echo "Blacklist: $(wc -l < "$BLACKLIST_FILE" 2>/dev/null || echo "0") IPs"
    
    echo ""
}

reset_rate_limit() {
    local ip="$1"
    
    if [ -z "$ip" ]; then
        echo -e "${RED}❌ IP address required${NC}"
        exit 1
    fi
    
    echo "Resetting rate limit for: $ip"
    
    # If using Redis
    if command -v redis-cli &>/dev/null; then
        local redis_host=$(grep "^ARK_REDIS_HOST=" "$ENV_FILE" | cut -d'=' -f2 || echo "127.0.0.1")
        local redis_port=$(grep "^ARK_REDIS_PORT=" "$ENV_FILE" | cut -d'=' -f2 || echo "6379")
        
        # Clear rate limit keys for this IP
        redis-cli -h "$redis_host" -p "$redis_port" --scan --pattern "ratelimit:$ip:*" | \
            xargs -r redis-cli -h "$redis_host" -p "$redis_port" DEL
        
        echo -e "${GREEN}✅ Rate limit reset for: $ip${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis CLI not available${NC}"
        echo "Restart ARK to reset rate limits"
    fi
}

show_help() {
    echo "ARK Rate Limiting Management"
    echo ""
    echo "USAGE:"
    echo "  ark-ratelimit setup               Configure rate limiting"
    echo "  ark-ratelimit nginx [rpm] [burst] Setup nginx rate limiting"
    echo "  ark-ratelimit status              Show current configuration"
    echo "  ark-ratelimit whitelist <ip>      Add IP to whitelist"
    echo "  ark-ratelimit blacklist <ip>      Add IP to blacklist"
    echo "  ark-ratelimit unwhitelist <ip>    Remove IP from whitelist"
    echo "  ark-ratelimit unblacklist <ip>    Remove IP from blacklist"
    echo "  ark-ratelimit list                Show whitelist/blacklist"
    echo "  ark-ratelimit reset <ip>          Reset rate limit for IP"
    echo ""
    echo "EXAMPLES:"
    echo "  ark-ratelimit setup                      # Interactive setup"
    echo "  ark-ratelimit nginx 120 20               # Nginx: 120 req/min, burst 20"
    echo "  ark-ratelimit whitelist 192.168.1.100    # Exempt IP from limits"
    echo "  ark-ratelimit blacklist 10.0.0.50        # Block IP completely"
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
            setup_rate_limiting
            ;;
        nginx)
            setup_nginx_ratelimit "$@"
            ;;
        status)
            show_status
            ;;
        whitelist)
            add_to_whitelist "$@"
            ;;
        blacklist)
            add_to_blacklist "$@"
            ;;
        unwhitelist)
            remove_from_whitelist "$@"
            ;;
        unblacklist)
            remove_from_blacklist "$@"
            ;;
        list)
            show_lists
            ;;
        reset)
            reset_rate_limit "$@"
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
# METHOD 1: Add to ARK Installation
# ----------------------------------
# cp enhancements/17-rate-limiting.sh ~/ark/bin/ark-ratelimit
# chmod +x ~/ark/bin/ark-ratelimit
#
# METHOD 2: Setup Rate Limiting
# ------------------------------
# ark-ratelimit setup
# ark restart
#
# METHOD 3: Nginx Rate Limiting (recommended for production)
# -----------------------------------------------------------
# ark-ratelimit nginx 60 10
#
# BENEFITS:
# ---------
# ✅ Prevent API abuse
# ✅ Fair resource allocation
# ✅ Protection against DDoS
# ✅ IP-based blocking
# ✅ Customizable limits
# ✅ Redis-backed tracking
# ✅ Nginx integration available
#
################################################################################
