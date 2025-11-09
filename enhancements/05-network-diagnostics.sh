#!/bin/bash
##############################################################################
# ARK Network Diagnostics
# Enhancement #5 - Network connectivity and access URL testing
##############################################################################

ARK_HOME="${ARK_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║               ARK Network Diagnostics                         ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Load config
if [ -f "$ARK_HOME/config/ark.conf" ]; then
    API_PORT=$(grep -m1 'port = ' "$ARK_HOME/config/ark.conf" | head -n1 | cut -d= -f2 | tr -d ' ' || echo "8000")
    REDIS_PORT=$(grep 'port = ' "$ARK_HOME/config/ark.conf" | tail -n1 | cut -d= -f2 | tr -d ' ' || echo "6379")
else
    API_PORT=8000
    REDIS_PORT=6379
fi

# Load .env if exists
if [ -f "$ARK_HOME/.env" ]; then
    source "$ARK_HOME/.env"
    API_PORT=${ARK_API_PORT:-$API_PORT}
    REDIS_PORT=${ARK_REDIS_PORT:-$REDIS_PORT}
fi

# Check ports
echo "📡 Port Status:"
echo ""
echo "   API Port $API_PORT:"
if command -v nc &>/dev/null; then
    if nc -z 127.0.0.1 "$API_PORT" 2>/dev/null; then
        echo "      ✅ Open and listening"
        if command -v lsof &>/dev/null; then
            PID=$(lsof -ti:$API_PORT 2>/dev/null || echo "unknown")
            echo "      Process PID: $PID"
        fi
    else
        echo "      ❌ Not listening"
        echo "      Start with: ark"
    fi
else
    echo "      ⚠️  nc not available (install: pkg install netcat)"
fi

echo ""
echo "   Redis Port $REDIS_PORT:"
if command -v nc &>/dev/null; then
    if nc -z 127.0.0.1 "$REDIS_PORT" 2>/dev/null; then
        echo "      ✅ Open and listening"
        if command -v lsof &>/dev/null; then
            PID=$(lsof -ti:$REDIS_PORT 2>/dev/null || echo "unknown")
            echo "      Process PID: $PID"
        fi
        
        # Test Redis response
        if command -v redis-cli &>/dev/null; then
            if redis-cli -p "$REDIS_PORT" ping &>/dev/null; then
                echo "      ✅ Responding to commands"
            fi
        fi
    else
        echo "      ❌ Not listening"
        echo "      Start with: ark-redis"
    fi
else
    echo "      ⚠️  nc not available"
fi

# Network info
echo ""
echo "🖥️  Network Information:"
echo "   Hostname: $(hostname)"
echo "   IP Addresses:"

# Get IP addresses
if command -v ip &>/dev/null; then
    ip addr show | grep "inet " | grep -v "127.0.0.1" | awk '{print "      " $2}' | sed 's|/.*||'
elif command -v ifconfig &>/dev/null; then
    ifconfig | grep "inet " | grep -v "127.0.0.1" | awk '{print "      " $2}'
else
    hostname -I 2>/dev/null | tr ' ' '\n' | grep -v '^$' | sed 's/^/      /'
fi

# Test connectivity
echo ""
echo "🔗 Connectivity Tests:"

echo "   Local Loopback:"
if ping -c 1 127.0.0.1 &>/dev/null; then
    echo "      ✅ localhost reachable"
else
    echo "      ❌ localhost not reachable"
fi

echo ""
echo "   Local API:"
if command -v curl &>/dev/null; then
    if curl -s --connect-timeout 2 "http://127.0.0.1:$API_PORT/health" &>/dev/null; then
        echo "      ✅ Responding"
    else
        echo "      ⚠️  Not responding (may need to start ARK)"
    fi
else
    echo "      ⚠️  curl not available (install: pkg install curl)"
fi

echo ""
echo "   Redis:"
if command -v redis-cli &>/dev/null; then
    if redis-cli -p "$REDIS_PORT" ping &>/dev/null; then
        echo "      ✅ Responding"
        # Get Redis info
        REDIS_CLIENTS=$(redis-cli -p "$REDIS_PORT" info clients 2>/dev/null | grep "connected_clients:" | cut -d: -f2 | tr -d '\r')
        if [ -n "$REDIS_CLIENTS" ]; then
            echo "      Connected clients: $REDIS_CLIENTS"
        fi
    else
        echo "      ⚠️  Not responding"
    fi
else
    echo "      ⚠️  redis-cli not available"
fi

echo ""
echo "   Ollama:"
if command -v curl &>/dev/null; then
    if curl -s --connect-timeout 2 "http://127.0.0.1:11434/api/tags" &>/dev/null; then
        echo "      ✅ Responding"
    else
        echo "      ⚠️  Not responding (may not be running)"
    fi
else
    echo "      ⚠️  curl not available"
fi

# Firewall check (Linux only)
if command -v ufw &>/dev/null; then
    echo ""
    echo "🔥 Firewall Status:"
    if ufw status 2>/dev/null | grep -q "Status: active"; then
        echo "   ⚠️  UFW firewall is active"
        echo "   May need to allow ports:"
        echo "      sudo ufw allow $API_PORT"
        echo "      sudo ufw allow $REDIS_PORT"
    else
        echo "   ✅ UFW firewall inactive"
    fi
fi

# Access URLs
echo ""
echo "💡 Access URLs:"
echo ""
echo "   Local Access:"
echo "      http://127.0.0.1:$API_PORT"
echo "      http://localhost:$API_PORT"
echo ""

# Show network IPs
echo "   Network Access (from other devices):"
if command -v hostname &>/dev/null; then
    for ip in $(hostname -I 2>/dev/null); do
        echo "      http://$ip:$API_PORT"
    done
else
    echo "      (Run 'hostname -I' to see your IP addresses)"
fi

# QR Code for mobile access (if qrencode available)
if command -v qrencode &>/dev/null; then
    FIRST_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    if [ -n "$FIRST_IP" ]; then
        echo ""
        echo "📱 QR Code for mobile access:"
        qrencode -t ANSIUTF8 "http://$FIRST_IP:$API_PORT"
    fi
fi

# Performance test
echo ""
echo "⚡ Performance Test:"
if command -v curl &>/dev/null && nc -z 127.0.0.1 "$API_PORT" 2>/dev/null; then
    RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' "http://127.0.0.1:$API_PORT/health" 2>/dev/null || echo "N/A")
    echo "   Response time: ${RESPONSE_TIME}s"
else
    echo "   ⚠️  API not running, cannot test"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  Diagnostics Complete                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

##############################################################################
# INSTALLATION INSTRUCTIONS
##############################################################################
#
# Add to installer's launcher script creation section:
#
#   cp "$SCRIPT_DIR/enhancements/05-network-diagnostics.sh" \
#      "$INSTALL_DIR/bin/ark-diag"
#   chmod +x "$INSTALL_DIR/bin/ark-diag"
#
##############################################################################
# USAGE
##############################################################################
#
# Run diagnostics:
#   ark-diag
#
# Check specific port:
#   nc -z localhost 8000 && echo "Port open"
#
# Test API:
#   curl http://localhost:8000/health
#
##############################################################################
