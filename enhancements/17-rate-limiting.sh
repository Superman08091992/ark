#!/bin/bash
################################################################################
# ARK Enhancement #17: API Rate Limiting
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Implements rate limiting for ARK API to prevent abuse, ensure fair usage,
# and protect against DDoS attacks. Provides both Redis-based and in-memory
# rate limiting with configurable limits and windows.
#
# FEATURES:
# ---------
# ✅ Request rate limiting per IP address
# ✅ Multiple rate limit strategies (fixed window, sliding window)
# ✅ Redis-based distributed rate limiting
# ✅ In-memory rate limiting (fallback)
# ✅ Configurable limits and time windows
# ✅ Whitelist/blacklist support
# ✅ Rate limit headers (X-RateLimit-*)
# ✅ Custom error responses
# ✅ Monitoring and metrics
#
# This file provides the rate limiting middleware implementation for Node.js
################################################################################

# This is a bash wrapper that provides configuration management
# The actual rate limiting is implemented in JavaScript (see companion file)

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

ENV_FILE="$INSTALL_DIR/.env"
RATE_LIMIT_CONFIG="$INSTALL_DIR/config/rate-limit.json"

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

################################################################################
# Configuration Functions
################################################################################

create_default_config() {
    mkdir -p "$(dirname "$RATE_LIMIT_CONFIG")"
    
    cat > "$RATE_LIMIT_CONFIG" << 'EOF'
{
  "enabled": true,
  "strategy": "sliding-window",
  "storage": "redis",
  "limits": {
    "default": {
      "requests": 100,
      "window": 60,
      "message": "Too many requests, please try again later"
    },
    "auth": {
      "requests": 10,
      "window": 60,
      "message": "Too many authentication attempts"
    },
    "api": {
      "requests": 100,
      "window": 60,
      "message": "API rate limit exceeded"
    }
  },
  "whitelist": [
    "127.0.0.1",
    "::1"
  ],
  "blacklist": [],
  "headers": {
    "total": "X-RateLimit-Limit",
    "remaining": "X-RateLimit-Remaining",
    "reset": "X-RateLimit-Reset"
  },
  "skipFailedRequests": false,
  "skipSuccessfulRequests": false
}
EOF
}

show_config() {
    print_header "⚙️  Rate Limiting Configuration"
    
    if [ ! -f "$RATE_LIMIT_CONFIG" ]; then
        echo -e "${YELLOW}⚠️  No configuration file found${NC}"
        echo "Run: ark-ratelimit init"
        return 1
    fi
    
    echo "Configuration file: $RATE_LIMIT_CONFIG"
    echo ""
    
    if command -v jq &>/dev/null; then
        cat "$RATE_LIMIT_CONFIG" | jq .
    else
        cat "$RATE_LIMIT_CONFIG"
    fi
    
    echo ""
}

init_rate_limiting() {
    print_header "🔧 Initialize Rate Limiting"
    
    if [ -f "$RATE_LIMIT_CONFIG" ]; then
        echo -e "${YELLOW}⚠️  Configuration already exists${NC}"
        read -p "Overwrite? (y/N): " overwrite
        if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
            echo "Cancelled."
            return 0
        fi
    fi
    
    create_default_config
    
    echo -e "${GREEN}✅ Rate limiting configuration created${NC}"
    echo "Configuration file: $RATE_LIMIT_CONFIG"
    echo ""
    
    # Update .env file
    if [ -f "$ENV_FILE" ]; then
        if ! grep -q "^ARK_RATE_LIMIT_ENABLED=" "$ENV_FILE"; then
            cat >> "$ENV_FILE" << 'EOF'

# Rate Limiting
ARK_RATE_LIMIT_ENABLED=true
ARK_RATE_LIMIT_STRATEGY=sliding-window
ARK_RATE_LIMIT_STORAGE=redis
ARK_RATE_LIMIT_DEFAULT_REQUESTS=100
ARK_RATE_LIMIT_DEFAULT_WINDOW=60
EOF
            echo -e "${GREEN}✅ Added rate limiting to .env${NC}"
        fi
    fi
    
    echo ""
    echo "Next steps:"
    echo "  1. Review config:  ark-ratelimit show"
    echo "  2. Enable:         ark-ratelimit enable"
    echo "  3. Test:           ark-ratelimit test"
    echo ""
}

enable_rate_limiting() {
    print_header "✅ Enabling Rate Limiting"
    
    if [ ! -f "$RATE_LIMIT_CONFIG" ]; then
        echo -e "${YELLOW}⚠️  No configuration found${NC}"
        echo "Run: ark-ratelimit init"
        return 1
    fi
    
    # Update config
    if command -v jq &>/dev/null; then
        local tmp=$(mktemp)
        jq '.enabled = true' "$RATE_LIMIT_CONFIG" > "$tmp" && mv "$tmp" "$RATE_LIMIT_CONFIG"
    fi
    
    # Update .env
    if [ -f "$ENV_FILE" ]; then
        if grep -q "^ARK_RATE_LIMIT_ENABLED=" "$ENV_FILE"; then
            sed -i 's/^ARK_RATE_LIMIT_ENABLED=.*/ARK_RATE_LIMIT_ENABLED=true/' "$ENV_FILE"
        else
            echo "ARK_RATE_LIMIT_ENABLED=true" >> "$ENV_FILE"
        fi
    fi
    
    echo -e "${GREEN}✅ Rate limiting enabled${NC}"
    echo -e "${YELLOW}⚠️  Restart ARK for changes to take effect${NC}"
    echo ""
}

disable_rate_limiting() {
    print_header "🛑 Disabling Rate Limiting"
    
    # Update config
    if [ -f "$RATE_LIMIT_CONFIG" ] && command -v jq &>/dev/null; then
        local tmp=$(mktemp)
        jq '.enabled = false' "$RATE_LIMIT_CONFIG" > "$tmp" && mv "$tmp" "$RATE_LIMIT_CONFIG"
    fi
    
    # Update .env
    if [ -f "$ENV_FILE" ]; then
        if grep -q "^ARK_RATE_LIMIT_ENABLED=" "$ENV_FILE"; then
            sed -i 's/^ARK_RATE_LIMIT_ENABLED=.*/ARK_RATE_LIMIT_ENABLED=false/' "$ENV_FILE"
        fi
    fi
    
    echo -e "${GREEN}✅ Rate limiting disabled${NC}"
    echo -e "${YELLOW}⚠️  Restart ARK for changes to take effect${NC}"
    echo ""
}

add_to_whitelist() {
    local ip="$1"
    
    if [ -z "$ip" ]; then
        echo -e "${RED}❌ Please specify an IP address${NC}"
        return 1
    fi
    
    print_header "➕ Adding to Whitelist"
    
    if [ ! -f "$RATE_LIMIT_CONFIG" ]; then
        echo -e "${YELLOW}⚠️  No configuration found${NC}"
        echo "Run: ark-ratelimit init"
        return 1
    fi
    
    if command -v jq &>/dev/null; then
        local tmp=$(mktemp)
        jq --arg ip "$ip" '.whitelist += [$ip] | .whitelist |= unique' "$RATE_LIMIT_CONFIG" > "$tmp" && mv "$tmp" "$RATE_LIMIT_CONFIG"
        echo -e "${GREEN}✅ Added $ip to whitelist${NC}"
    else
        echo -e "${YELLOW}⚠️  jq required for this operation${NC}"
        echo "Manually add to $RATE_LIMIT_CONFIG"
    fi
    
    echo ""
}

remove_from_whitelist() {
    local ip="$1"
    
    if [ -z "$ip" ]; then
        echo -e "${RED}❌ Please specify an IP address${NC}"
        return 1
    fi
    
    print_header "➖ Removing from Whitelist"
    
    if command -v jq &>/dev/null; then
        local tmp=$(mktemp)
        jq --arg ip "$ip" '.whitelist -= [$ip]' "$RATE_LIMIT_CONFIG" > "$tmp" && mv "$tmp" "$RATE_LIMIT_CONFIG"
        echo -e "${GREEN}✅ Removed $ip from whitelist${NC}"
    else
        echo -e "${YELLOW}⚠️  jq required for this operation${NC}"
    fi
    
    echo ""
}

show_status() {
    print_header "📊 Rate Limiting Status"
    
    if [ ! -f "$RATE_LIMIT_CONFIG" ]; then
        echo -e "${RED}❌ Not configured${NC}"
        echo "Run: ark-ratelimit init"
        return 1
    fi
    
    echo "Configuration:"
    if command -v jq &>/dev/null; then
        local enabled=$(jq -r '.enabled' "$RATE_LIMIT_CONFIG")
        local strategy=$(jq -r '.strategy' "$RATE_LIMIT_CONFIG")
        local storage=$(jq -r '.storage' "$RATE_LIMIT_CONFIG")
        local requests=$(jq -r '.limits.default.requests' "$RATE_LIMIT_CONFIG")
        local window=$(jq -r '.limits.default.window' "$RATE_LIMIT_CONFIG")
        
        echo "  Enabled:   $enabled"
        echo "  Strategy:  $strategy"
        echo "  Storage:   $storage"
        echo "  Limit:     $requests requests per ${window}s"
        echo ""
        
        local whitelist_count=$(jq '.whitelist | length' "$RATE_LIMIT_CONFIG")
        echo "  Whitelist: $whitelist_count IPs"
        
        if [ "$whitelist_count" -gt 0 ]; then
            jq -r '.whitelist[]' "$RATE_LIMIT_CONFIG" | while read ip; do
                echo "    • $ip"
            done
        fi
    else
        echo "  (Install jq for detailed status)"
    fi
    
    echo ""
}

test_rate_limiting() {
    print_header "🧪 Testing Rate Limiting"
    
    local ark_host="http://localhost:$(grep ARK_API_PORT "$ENV_FILE" 2>/dev/null | cut -d'=' -f2 || echo 8000)"
    
    echo "Sending test requests to: $ark_host"
    echo ""
    
    local success=0
    local limited=0
    
    for i in {1..15}; do
        echo -n "Request $i: "
        
        local response=$(curl -s -w "%{http_code}" -o /dev/null "$ark_host/health" 2>/dev/null || echo "000")
        
        if [ "$response" = "200" ]; then
            echo -e "${GREEN}✓${NC} Success"
            ((success++))
        elif [ "$response" = "429" ]; then
            echo -e "${YELLOW}⚠${NC} Rate limited"
            ((limited++))
        else
            echo -e "${RED}✗${NC} Error ($response)"
        fi
        
        sleep 0.5
    done
    
    echo ""
    echo "Results:"
    echo "  Successful:   $success"
    echo "  Rate limited: $limited"
    echo ""
    
    if [ $limited -gt 0 ]; then
        echo -e "${GREEN}✅ Rate limiting is working!${NC}"
    else
        echo -e "${YELLOW}⚠️  No rate limiting detected${NC}"
        echo "Check if rate limiting is enabled and ARK is running"
    fi
    
    echo ""
}

show_help() {
    echo "ARK Rate Limiting Management"
    echo ""
    echo "USAGE:"
    echo "  ark-ratelimit init                    Initialize rate limiting"
    echo "  ark-ratelimit enable                  Enable rate limiting"
    echo "  ark-ratelimit disable                 Disable rate limiting"
    echo "  ark-ratelimit status                  Show current status"
    echo "  ark-ratelimit show                    Show configuration"
    echo "  ark-ratelimit test                    Test rate limiting"
    echo "  ark-ratelimit whitelist add <ip>      Add IP to whitelist"
    echo "  ark-ratelimit whitelist remove <ip>   Remove IP from whitelist"
    echo ""
    echo "EXAMPLES:"
    echo "  ark-ratelimit init                        # Set up rate limiting"
    echo "  ark-ratelimit whitelist add 192.168.1.5   # Allow unlimited access"
    echo "  ark-ratelimit test                        # Test if it works"
    echo ""
}

################################################################################
# Main
################################################################################

main() {
    local command="${1:-help}"
    shift || true
    
    case $command in
        init)
            init_rate_limiting
            ;;
        enable)
            enable_rate_limiting
            ;;
        disable)
            disable_rate_limiting
            ;;
        status)
            show_status
            ;;
        show|config)
            show_config
            ;;
        test)
            test_rate_limiting
            ;;
        whitelist)
            local action="${1:-help}"
            case $action in
                add)
                    add_to_whitelist "$2"
                    ;;
                remove)
                    remove_from_whitelist "$2"
                    ;;
                *)
                    echo "Whitelist commands: add <ip>, remove <ip>"
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
# 1. Copy this file to enhancements/17-rate-limiting.sh
#
# 2. Copy the companion file (rate-limit-middleware.js) to lib/
#
# 3. In create-unified-ark.sh, add after creating bin directory:
#
#    # Copy rate limiting tool
#    cp enhancements/17-rate-limiting.sh "$INSTALL_DIR/bin/ark-ratelimit"
#    chmod +x "$INSTALL_DIR/bin/ark-ratelimit"
#    
#    # Copy rate limiting middleware
#    cp enhancements/rate-limit-middleware.js "$INSTALL_DIR/lib/"
#
# 4. In intelligent-backend.cjs, add the middleware:
#
#    const rateLimiter = require('./rate-limit-middleware');
#    app.use(rateLimiter);
#
# 5. Add to post-install message:
#
#    echo "  🚦 Rate limiting:    ark-ratelimit init"
#
#
# METHOD 2: Manual Installation
# ------------------------------
# 1. Copy to your ARK bin directory:
#    cp enhancements/17-rate-limiting.sh ~/ark/bin/ark-ratelimit
#    chmod +x ~/ark/bin/ark-ratelimit
#
# 2. Initialize:
#    ark-ratelimit init
#
# 3. Enable:
#    ark-ratelimit enable
#
#
# BENEFITS:
# ---------
# ✅ Protects against API abuse
# ✅ Prevents DDoS attacks
# ✅ Ensures fair usage
# ✅ Configurable limits
# ✅ Redis-based (distributed)
# ✅ IP whitelist support
# ✅ Standard rate limit headers
# ✅ Easy monitoring
#
################################################################################
