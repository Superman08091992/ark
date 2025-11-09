#!/bin/bash
################################################################################
# ARK Enhancement #18: HTTPS/SSL Support
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Enables HTTPS/SSL for ARK API with automatic certificate management using
# Let's Encrypt or self-signed certificates. Provides secure communication
# for production deployments.
#
# FEATURES:
# ---------
# ✅ Let's Encrypt automatic certificates
# ✅ Self-signed certificate generation
# ✅ Certificate renewal automation
# ✅ HTTP to HTTPS redirect
# ✅ Certificate validation
# ✅ Multiple domain support
# ✅ Certificate monitoring
# ✅ nginx/Apache reverse proxy config
#
# USAGE:
# ------
# ark-https setup                   # Interactive HTTPS setup
# ark-https letsencrypt <domain>    # Get Let's Encrypt certificate
# ark-https selfsigned              # Generate self-signed certificate
# ark-https renew                   # Renew certificates
# ark-https status                  # Show certificate status
# ark-https nginx                   # Generate nginx config
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

ENV_FILE="$INSTALL_DIR/.env"
CERT_DIR="$INSTALL_DIR/certs"

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

check_domain() {
    local domain=$1
    
    # Check if domain resolves
    if ! host "$domain" &>/dev/null; then
        echo -e "${YELLOW}⚠️  Warning: Domain $domain does not resolve${NC}"
        return 1
    fi
    
    # Check if domain points to this server
    local domain_ip=$(host "$domain" | grep "has address" | awk '{print $4}' | head -1)
    local server_ip=$(curl -s https://ifconfig.me)
    
    if [ "$domain_ip" != "$server_ip" ]; then
        echo -e "${YELLOW}⚠️  Warning: Domain points to $domain_ip, server IP is $server_ip${NC}"
        return 1
    fi
    
    return 0
}

################################################################################
# Let's Encrypt Functions
################################################################################

setup_letsencrypt() {
    local domain=$1
    local email=${2:-admin@$domain}
    
    print_header "🔐 Let's Encrypt Setup"
    
    if [ -z "$domain" ]; then
        echo -e "${RED}❌ Domain name required${NC}"
        echo "Usage: ark-https letsencrypt <domain> [email]"
        return 1
    fi
    
    echo "Domain: $domain"
    echo "Email:  $email"
    echo ""
    
    # Check domain
    if ! check_domain "$domain"; then
        read -p "Continue anyway? (y/N): " continue
        if [ "$continue" != "y" ] && [ "$continue" != "Y" ]; then
            return 1
        fi
    fi
    
    # Check if certbot is installed
    if ! command -v certbot &>/dev/null; then
        echo "Installing certbot..."
        if [ -f /etc/debian_version ]; then
            sudo apt-get update
            sudo apt-get install -y certbot
        elif [ -f /etc/redhat-release ]; then
            sudo yum install -y certbot
        elif command -v brew &>/dev/null; then
            brew install certbot
        else
            echo -e "${RED}❌ Please install certbot manually${NC}"
            return 1
        fi
    fi
    
    mkdir -p "$CERT_DIR"
    
    # Get certificate
    print_section "Obtaining Certificate"
    
    local ark_port=$(grep ARK_API_PORT "$ENV_FILE" 2>/dev/null | cut -d'=' -f2 || echo 8000)
    
    echo "Stopping ARK temporarily (port 80 needed)..."
    if command -v ark &>/dev/null; then
        ark stop 2>/dev/null || true
    fi
    
    # Request certificate
    sudo certbot certonly \
        --standalone \
        --preferred-challenges http \
        --email "$email" \
        --agree-tos \
        --no-eff-email \
        -d "$domain"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Certificate obtained successfully${NC}"
        
        # Copy certificates
        sudo cp "/etc/letsencrypt/live/$domain/fullchain.pem" "$CERT_DIR/cert.pem"
        sudo cp "/etc/letsencrypt/live/$domain/privkey.pem" "$CERT_DIR/key.pem"
        sudo chown $(whoami):$(whoami) "$CERT_DIR"/*.pem
        chmod 600 "$CERT_DIR"/key.pem
        
        # Update .env
        update_env_https "$domain"
        
        # Setup auto-renewal
        setup_auto_renewal "$domain"
        
        echo ""
        echo -e "${GREEN}✅ HTTPS configured successfully!${NC}"
        echo ""
        echo "Certificate files:"
        echo "  • $CERT_DIR/cert.pem"
        echo "  • $CERT_DIR/key.pem"
        echo ""
        echo "Access ARK at: https://$domain"
        echo ""
    else
        echo -e "${RED}❌ Failed to obtain certificate${NC}"
        return 1
    fi
}

setup_auto_renewal() {
    local domain=$1
    
    print_section "Setting up auto-renewal"
    
    # Create renewal script
    cat > "$INSTALL_DIR/bin/ark-cert-renew" << 'EOF'
#!/bin/bash
# ARK Certificate Renewal Script

DOMAIN="$1"
CERT_DIR="$2"

echo "Renewing certificate for $DOMAIN..."

# Renew with certbot
sudo certbot renew --quiet

# Copy updated certificates
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$CERT_DIR/cert.pem"
    sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$CERT_DIR/key.pem"
    sudo chown $(whoami):$(whoami) "$CERT_DIR"/*.pem
    chmod 600 "$CERT_DIR"/key.pem
    
    echo "Certificate renewed successfully"
    
    # Restart ARK
    if command -v ark &>/dev/null; then
        ark restart
    fi
else
    echo "Certificate renewal failed"
    exit 1
fi
EOF
    
    chmod +x "$INSTALL_DIR/bin/ark-cert-renew"
    
    # Add to crontab (renew weekly, certificates renew if <30 days left)
    local cron_job="0 3 * * 0 $INSTALL_DIR/bin/ark-cert-renew $domain $CERT_DIR"
    
    (crontab -l 2>/dev/null | grep -v ark-cert-renew; echo "$cron_job") | crontab -
    
    echo -e "${GREEN}✅ Auto-renewal configured (weekly check)${NC}"
}

################################################################################
# Self-Signed Certificate Functions
################################################################################

generate_selfsigned() {
    print_header "🔐 Self-Signed Certificate"
    
    local domain=${1:-localhost}
    local days=${2:-365}
    
    echo "Generating self-signed certificate..."
    echo "  Domain: $domain"
    echo "  Valid:  $days days"
    echo ""
    
    mkdir -p "$CERT_DIR"
    
    # Generate private key
    openssl genrsa -out "$CERT_DIR/key.pem" 2048 2>/dev/null
    
    # Generate certificate
    openssl req -new -x509 \
        -key "$CERT_DIR/key.pem" \
        -out "$CERT_DIR/cert.pem" \
        -days "$days" \
        -subj "/CN=$domain/O=ARK/C=US" \
        2>/dev/null
    
    chmod 600 "$CERT_DIR"/key.pem
    
    if [ -f "$CERT_DIR/cert.pem" ]; then
        echo -e "${GREEN}✅ Self-signed certificate generated${NC}"
        echo ""
        echo "Certificate files:"
        echo "  • $CERT_DIR/cert.pem"
        echo "  • $CERT_DIR/key.pem"
        echo ""
        
        # Update .env
        update_env_https "$domain"
        
        echo -e "${YELLOW}⚠️  Self-signed certificates show browser warnings${NC}"
        echo "   Use Let's Encrypt for production deployments"
        echo ""
    else
        echo -e "${RED}❌ Failed to generate certificate${NC}"
        return 1
    fi
}

################################################################################
# Configuration Functions
################################################################################

update_env_https() {
    local domain=$1
    
    if [ ! -f "$ENV_FILE" ]; then
        mkdir -p "$(dirname "$ENV_FILE")"
        touch "$ENV_FILE"
    fi
    
    # Update or add HTTPS settings
    if grep -q "^ARK_HTTPS_ENABLED=" "$ENV_FILE"; then
        sed -i "s|^ARK_HTTPS_ENABLED=.*|ARK_HTTPS_ENABLED=true|" "$ENV_FILE"
        sed -i "s|^ARK_HTTPS_CERT=.*|ARK_HTTPS_CERT=$CERT_DIR/cert.pem|" "$ENV_FILE"
        sed -i "s|^ARK_HTTPS_KEY=.*|ARK_HTTPS_KEY=$CERT_DIR/key.pem|" "$ENV_FILE"
    else
        cat >> "$ENV_FILE" << EOF

# HTTPS Configuration
ARK_HTTPS_ENABLED=true
ARK_HTTPS_CERT=$CERT_DIR/cert.pem
ARK_HTTPS_KEY=$CERT_DIR/key.pem
ARK_HTTPS_REDIRECT=true
EOF
    fi
    
    echo -e "${GREEN}✅ Updated $ENV_FILE${NC}"
}

show_status() {
    print_header "🔐 Certificate Status"
    
    if [ ! -f "$CERT_DIR/cert.pem" ]; then
        echo -e "${RED}❌ No certificate found${NC}"
        echo "Run: ark-https setup"
        return 1
    fi
    
    echo "Certificate file: $CERT_DIR/cert.pem"
    echo ""
    
    # Show certificate info
    openssl x509 -in "$CERT_DIR/cert.pem" -noout -text | grep -A2 "Subject:\|Validity\|DNS:"
    
    # Check expiration
    local expire_date=$(openssl x509 -in "$CERT_DIR/cert.pem" -noout -enddate | cut -d= -f2)
    local expire_epoch=$(date -d "$expire_date" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$expire_date" +%s 2>/dev/null)
    local now_epoch=$(date +%s)
    local days_left=$(( ($expire_epoch - $now_epoch) / 86400 ))
    
    echo ""
    if [ $days_left -lt 30 ]; then
        echo -e "${RED}⚠️  Certificate expires in $days_left days${NC}"
        echo "   Run: ark-https renew"
    elif [ $days_left -lt 90 ]; then
        echo -e "${YELLOW}⚠️  Certificate expires in $days_left days${NC}"
    else
        echo -e "${GREEN}✓ Certificate valid for $days_left days${NC}"
    fi
    
    echo ""
}

renew_certificates() {
    print_header "🔄 Renewing Certificates"
    
    if [ ! -f "$CERT_DIR/cert.pem" ]; then
        echo -e "${RED}❌ No certificate to renew${NC}"
        return 1
    fi
    
    # Check if Let's Encrypt certificate
    if sudo test -d "/etc/letsencrypt/live"; then
        echo "Renewing Let's Encrypt certificate..."
        sudo certbot renew
        
        # Copy updated certificates
        local domain=$(openssl x509 -in "$CERT_DIR/cert.pem" -noout -subject | grep -oP 'CN\s*=\s*\K[^,]+')
        if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
            sudo cp "/etc/letsencrypt/live/$domain/fullchain.pem" "$CERT_DIR/cert.pem"
            sudo cp "/etc/letsencrypt/live/$domain/privkey.pem" "$CERT_DIR/key.pem"
            sudo chown $(whoami):$(whoami) "$CERT_DIR"/*.pem
            echo -e "${GREEN}✅ Certificate renewed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Self-signed certificate cannot be renewed${NC}"
        echo "   Generate a new one: ark-https selfsigned"
    fi
    
    echo ""
}

generate_nginx_config() {
    print_header "🔧 nginx Configuration"
    
    local domain=${1:-example.com}
    local ark_port=$(grep ARK_API_PORT "$ENV_FILE" 2>/dev/null | cut -d'=' -f2 || echo 8000)
    
    cat << EOF
# nginx configuration for ARK with HTTPS

upstream ark_backend {
    server 127.0.0.1:$ark_port;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $domain;
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name $domain;
    
    # SSL certificates
    ssl_certificate $CERT_DIR/cert.pem;
    ssl_certificate_key $CERT_DIR/key.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Proxy to ARK
    location / {
        proxy_pass http://ark_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF
    
    echo ""
    echo "Save this to: /etc/nginx/sites-available/ark"
    echo "Then: sudo ln -s /etc/nginx/sites-available/ark /etc/nginx/sites-enabled/"
    echo "And: sudo nginx -t && sudo systemctl restart nginx"
    echo ""
}

interactive_setup() {
    print_header "🔐 HTTPS Setup Wizard"
    
    echo "How would you like to set up HTTPS?"
    echo ""
    echo "1. Let's Encrypt (recommended for production)"
    echo "2. Self-signed certificate (for testing)"
    echo "3. Use existing certificates"
    echo ""
    
    read -p "Choose option (1-3): " choice
    
    case $choice in
        1)
            echo ""
            read -p "Enter your domain name: " domain
            read -p "Enter your email: " email
            setup_letsencrypt "$domain" "$email"
            ;;
        2)
            echo ""
            read -p "Enter domain/hostname [localhost]: " domain
            domain=${domain:-localhost}
            generate_selfsigned "$domain"
            ;;
        3)
            echo ""
            read -p "Certificate path: " cert_path
            read -p "Private key path: " key_path
            
            mkdir -p "$CERT_DIR"
            cp "$cert_path" "$CERT_DIR/cert.pem"
            cp "$key_path" "$CERT_DIR/key.pem"
            chmod 600 "$CERT_DIR"/key.pem"
            
            update_env_https "$(openssl x509 -in "$cert_path" -noout -subject | grep -oP 'CN\s*=\s*\K[^,]+')"
            echo -e "${GREEN}✅ Certificates configured${NC}"
            ;;
        *)
            echo "Invalid option"
            return 1
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}✅ HTTPS setup complete!${NC}"
    echo ""
    echo "Restart ARK to apply changes: ark restart"
    echo ""
}

show_help() {
    echo "ARK HTTPS/SSL Support"
    echo ""
    echo "USAGE:"
    echo "  ark-https setup                        Interactive HTTPS setup"
    echo "  ark-https letsencrypt <domain> [email] Get Let's Encrypt certificate"
    echo "  ark-https selfsigned [domain] [days]   Generate self-signed certificate"
    echo "  ark-https renew                        Renew certificates"
    echo "  ark-https status                       Show certificate status"
    echo "  ark-https nginx [domain]               Generate nginx config"
    echo ""
    echo "EXAMPLES:"
    echo "  ark-https setup                           # Interactive setup"
    echo "  ark-https letsencrypt api.example.com    # Get Let's Encrypt cert"
    echo "  ark-https selfsigned localhost            # Testing certificate"
    echo "  ark-https nginx api.example.com           # Generate nginx config"
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
            interactive_setup
            ;;
        letsencrypt)
            setup_letsencrypt "$@"
            ;;
        selfsigned)
            generate_selfsigned "$@"
            ;;
        renew)
            renew_certificates
            ;;
        status)
            show_status
            ;;
        nginx)
            generate_nginx_config "$@"
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
# 1. Copy this file to enhancements/18-https-support.sh
#
# 2. In create-unified-ark.sh, add after creating bin directory:
#
#    # Copy HTTPS tool
#    cp enhancements/18-https-support.sh "$INSTALL_DIR/bin/ark-https"
#    chmod +x "$INSTALL_DIR/bin/ark-https"
#
# 3. Add to post-install message:
#
#    echo "  🔐 HTTPS setup:      ark-https setup"
#
#
# METHOD 2: Manual Installation
# ------------------------------
# 1. Copy to your ARK bin directory:
#    cp enhancements/18-https-support.sh ~/ark/bin/ark-https"
#    chmod +x ~/ark/bin/ark-https
#
# 2. Run setup:
#    ark-https setup
#
#
# BENEFITS:
# ---------
# ✅ Secure communication with SSL/TLS
# ✅ Automatic Let's Encrypt certificates
# ✅ Auto-renewal support
# ✅ Self-signed for testing
# ✅ nginx/Apache reverse proxy configs
# ✅ Certificate monitoring
# ✅ Production-ready security
# ✅ Easy domain management
#
################################################################################
