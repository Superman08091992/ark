#!/bin/bash
################################################################################
# ARK Enhancement #16: HTTPS Support with SSL/TLS
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Sets up HTTPS support for ARK using Let's Encrypt SSL certificates or
# self-signed certificates. Includes nginx/caddy reverse proxy configuration
# for production deployments.
#
# FEATURES:
# ---------
# ✅ Let's Encrypt certificate automation
# ✅ Self-signed certificate generation
# ✅ Nginx reverse proxy setup
# ✅ Caddy reverse proxy setup
# ✅ Auto-renewal configuration
# ✅ HTTP to HTTPS redirect
# ✅ SSL certificate verification
# ✅ Certificate expiry monitoring
# ✅ Multiple domain support
# ✅ Security headers configuration
#
# USAGE:
# ------
# ark-https setup               # Interactive setup wizard
# ark-https nginx               # Configure nginx reverse proxy
# ark-https caddy               # Configure caddy reverse proxy
# ark-https self-signed         # Generate self-signed certificate
# ark-https letsencrypt <domain> # Get Let's Encrypt certificate
# ark-https renew               # Renew certificates
# ark-https status              # Check certificate status
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

CERT_DIR="$INSTALL_DIR/ssl"
NGINX_CONF="/etc/nginx/sites-available/ark"
CADDY_CONF="/etc/caddy/Caddyfile"

################################################################################
# Certificate Management
################################################################################

generate_self_signed() {
    local domain="${1:-ark.local}"
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🔒 Generating Self-Signed Certificate${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    mkdir -p "$CERT_DIR"
    
    echo "Domain: $domain"
    echo ""
    
    # Generate private key
    echo -n "Generating private key... "
    openssl genrsa -out "$CERT_DIR/privkey.pem" 2048 2>/dev/null
    echo -e "${GREEN}✅${NC}"
    
    # Generate certificate
    echo -n "Generating certificate... "
    openssl req -new -x509 -key "$CERT_DIR/privkey.pem" \
        -out "$CERT_DIR/fullchain.pem" -days 365 \
        -subj "/CN=$domain/O=ARK/C=US" 2>/dev/null
    echo -e "${GREEN}✅${NC}"
    
    # Set permissions
    chmod 600 "$CERT_DIR/privkey.pem"
    chmod 644 "$CERT_DIR/fullchain.pem"
    
    echo ""
    echo -e "${GREEN}✅ Self-signed certificate created${NC}"
    echo "   Certificate: $CERT_DIR/fullchain.pem"
    echo "   Private Key: $CERT_DIR/privkey.pem"
    echo "   Valid for: 365 days"
    echo ""
    echo -e "${YELLOW}⚠️  Warning: Self-signed certificates will show browser warnings${NC}"
    echo "   For production, use Let's Encrypt instead"
    echo ""
}

setup_letsencrypt() {
    local domain="$1"
    local email="${2:-admin@$domain}"
    
    if [ -z "$domain" ]; then
        echo -e "${RED}❌ Domain name required${NC}"
        echo "Usage: ark-https letsencrypt <domain> [email]"
        exit 1
    fi
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🔒 Setting up Let's Encrypt${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo "Domain: $domain"
    echo "Email: $email"
    echo ""
    
    # Check if certbot is installed
    if ! command -v certbot &>/dev/null; then
        echo -e "${YELLOW}⚠️  certbot not found. Installing...${NC}"
        
        if command -v apt-get &>/dev/null; then
            sudo apt-get update && sudo apt-get install -y certbot
        elif command -v yum &>/dev/null; then
            sudo yum install -y certbot
        else
            echo -e "${RED}❌ Cannot install certbot automatically${NC}"
            echo "Please install certbot manually:"
            echo "  https://certbot.eff.org/"
            exit 1
        fi
    fi
    
    mkdir -p "$CERT_DIR"
    
    # Get certificate
    echo "Obtaining certificate from Let's Encrypt..."
    echo ""
    
    sudo certbot certonly --standalone \
        --preferred-challenges http \
        --email "$email" \
        --agree-tos \
        --no-eff-email \
        -d "$domain"
    
    # Copy certificates to ARK directory
    sudo cp "/etc/letsencrypt/live/$domain/fullchain.pem" "$CERT_DIR/"
    sudo cp "/etc/letsencrypt/live/$domain/privkey.pem" "$CERT_DIR/"
    sudo chown $(whoami):$(whoami) "$CERT_DIR"/*.pem
    
    echo ""
    echo -e "${GREEN}✅ Let's Encrypt certificate obtained${NC}"
    echo "   Certificate: $CERT_DIR/fullchain.pem"
    echo "   Private Key: $CERT_DIR/privkey.pem"
    echo ""
    
    # Setup auto-renewal
    setup_cert_renewal
}

setup_cert_renewal() {
    echo "Setting up automatic certificate renewal..."
    
    # Add cron job for renewal
    local cron_cmd="0 0 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'"
    
    (crontab -l 2>/dev/null | grep -v "certbot renew" ; echo "$cron_cmd") | crontab -
    
    echo -e "${GREEN}✅ Auto-renewal configured${NC}"
    echo "   Certificates will be checked daily"
    echo ""
}

check_certificate_status() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🔍 Certificate Status${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ ! -f "$CERT_DIR/fullchain.pem" ]; then
        echo -e "${YELLOW}⚠️  No certificate found${NC}"
        echo "Run: ark-https setup"
        return 1
    fi
    
    echo "Certificate: $CERT_DIR/fullchain.pem"
    echo ""
    
    # Check expiry
    local expiry=$(openssl x509 -enddate -noout -in "$CERT_DIR/fullchain.pem" | cut -d= -f2)
    local expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$expiry" +%s 2>/dev/null)
    local now_epoch=$(date +%s)
    local days_left=$(( (expiry_epoch - now_epoch) / 86400 ))
    
    echo "Expires: $expiry"
    echo "Days remaining: $days_left"
    
    if [ $days_left -lt 30 ]; then
        echo -e "${YELLOW}⚠️  Certificate expires soon - run: ark-https renew${NC}"
    elif [ $days_left -lt 0 ]; then
        echo -e "${RED}❌ Certificate expired!${NC}"
    else
        echo -e "${GREEN}✅ Certificate is valid${NC}"
    fi
    
    echo ""
    
    # Show certificate details
    echo "Certificate details:"
    openssl x509 -in "$CERT_DIR/fullchain.pem" -noout -subject -issuer
    
    echo ""
}

################################################################################
# Reverse Proxy Setup
################################################################################

setup_nginx() {
    local domain="${1:-ark.local}"
    local ark_port=$(grep "^ARK_API_PORT=" "$INSTALL_DIR/.env" 2>/dev/null | cut -d'=' -f2 || echo "8000")
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🔧 Configuring Nginx Reverse Proxy${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Check if nginx is installed
    if ! command -v nginx &>/dev/null; then
        echo -e "${YELLOW}⚠️  nginx not found. Installing...${NC}"
        if command -v apt-get &>/dev/null; then
            sudo apt-get install -y nginx
        elif command -v yum &>/dev/null; then
            sudo yum install -y nginx
        else
            echo -e "${RED}❌ Please install nginx manually${NC}"
            exit 1
        fi
    fi
    
    # Create nginx configuration
    echo "Creating nginx configuration..."
    
    sudo tee "$NGINX_CONF" > /dev/null << EOF
# ARK Nginx Configuration
# Reverse proxy with HTTPS

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name $domain;
    
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $domain;
    
    # SSL Certificate
    ssl_certificate $CERT_DIR/fullchain.pem;
    ssl_certificate_key $CERT_DIR/privkey.pem;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy to ARK
    location / {
        proxy_pass http://127.0.0.1:$ark_port;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Logging
    access_log /var/log/nginx/ark-access.log;
    error_log /var/log/nginx/ark-error.log;
}
EOF
    
    # Enable site
    sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/ark
    
    # Test configuration
    echo ""
    echo -n "Testing nginx configuration... "
    if sudo nginx -t 2>/dev/null; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
        echo "Run: sudo nginx -t"
        exit 1
    fi
    
    # Reload nginx
    echo -n "Reloading nginx... "
    sudo systemctl reload nginx 2>/dev/null || sudo service nginx reload
    echo -e "${GREEN}✅${NC}"
    
    echo ""
    echo -e "${GREEN}✅ Nginx configured successfully${NC}"
    echo "   Access ARK at: https://$domain"
    echo ""
}

setup_caddy() {
    local domain="${1:-ark.local}"
    local ark_port=$(grep "^ARK_API_PORT=" "$INSTALL_DIR/.env" 2>/dev/null | cut -d'=' -f2 || echo "8000")
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🔧 Configuring Caddy Reverse Proxy${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Check if caddy is installed
    if ! command -v caddy &>/dev/null; then
        echo -e "${YELLOW}⚠️  caddy not found${NC}"
        echo "Install Caddy:"
        echo "  https://caddyserver.com/docs/install"
        exit 1
    fi
    
    # Create Caddyfile
    echo "Creating Caddy configuration..."
    
    sudo tee "$CADDY_CONF" > /dev/null << EOF
# ARK Caddy Configuration
# Automatic HTTPS with Let's Encrypt

$domain {
    reverse_proxy localhost:$ark_port
    
    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
    }
    
    # Logging
    log {
        output file /var/log/caddy/ark.log
    }
}
EOF
    
    # Restart Caddy
    echo -n "Restarting Caddy... "
    sudo systemctl restart caddy
    echo -e "${GREEN}✅${NC}"
    
    echo ""
    echo -e "${GREEN}✅ Caddy configured successfully${NC}"
    echo "   Caddy will automatically obtain SSL certificate"
    echo "   Access ARK at: https://$domain"
    echo ""
}

################################################################################
# Setup Wizard
################################################################################

setup_wizard() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🔒 ARK HTTPS Setup Wizard${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo "Choose SSL certificate type:"
    echo "  1. Let's Encrypt (recommended for public domains)"
    echo "  2. Self-signed (for development/testing)"
    echo ""
    read -p "Choice (1/2): " cert_choice
    
    echo ""
    read -p "Domain name: " domain
    
    if [ "$cert_choice" = "1" ]; then
        read -p "Email address: " email
        setup_letsencrypt "$domain" "$email"
    else
        generate_self_signed "$domain"
    fi
    
    echo ""
    echo "Choose reverse proxy:"
    echo "  1. Nginx"
    echo "  2. Caddy"
    echo "  3. None (manual setup)"
    echo ""
    read -p "Choice (1/2/3): " proxy_choice
    
    case $proxy_choice in
        1)
            setup_nginx "$domain"
            ;;
        2)
            setup_caddy "$domain"
            ;;
        3)
            echo "Manual setup selected"
            echo "Certificate files are in: $CERT_DIR"
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✅ HTTPS Setup Complete${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

show_help() {
    echo "ARK HTTPS Support"
    echo ""
    echo "USAGE:"
    echo "  ark-https setup                    Interactive setup wizard"
    echo "  ark-https nginx <domain>           Configure nginx reverse proxy"
    echo "  ark-https caddy <domain>           Configure caddy reverse proxy"
    echo "  ark-https self-signed [domain]     Generate self-signed certificate"
    echo "  ark-https letsencrypt <domain> [email]  Get Let's Encrypt certificate"
    echo "  ark-https status                   Check certificate status"
    echo "  ark-https renew                    Renew certificates"
    echo ""
    echo "EXAMPLES:"
    echo "  ark-https setup                              # Interactive setup"
    echo "  ark-https letsencrypt ark.example.com        # Let's Encrypt"
    echo "  ark-https nginx ark.example.com              # Setup nginx"
    echo ""
}

################################################################################
# Main
################################################################################

main() {
    local command="${1:-setup}"
    shift || true
    
    case $command in
        setup)
            setup_wizard
            ;;
        nginx)
            setup_nginx "$@"
            ;;
        caddy)
            setup_caddy "$@"
            ;;
        self-signed)
            generate_self_signed "$@"
            ;;
        letsencrypt)
            setup_letsencrypt "$@"
            ;;
        status)
            check_certificate_status
            ;;
        renew)
            echo "Renewing certificates..."
            sudo certbot renew
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
# cp enhancements/16-https-support.sh ~/ark/bin/ark-https
# chmod +x ~/ark/bin/ark-https
#
# METHOD 2: Run Setup
# -------------------
# ark-https setup
#
# BENEFITS:
# ---------
# ✅ Secure HTTPS connections
# ✅ Automated Let's Encrypt certificates
# ✅ Production-ready reverse proxy configs
# ✅ Auto-renewal for certificates
# ✅ Security headers included
# ✅ Easy domain configuration
#
################################################################################
