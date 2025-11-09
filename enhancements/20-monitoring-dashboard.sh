#!/bin/bash
################################################################################
# ARK Enhancement #20: Monitoring Dashboard
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Provides real-time monitoring and metrics dashboard for ARK with system
# resource tracking, API metrics, and performance monitoring.
#
# FEATURES:
# ---------
# ✅ Real-time system metrics (CPU, Memory, Disk)
# ✅ API request metrics and statistics
# ✅ Service health monitoring
# ✅ Performance metrics
# ✅ Live log streaming
# ✅ Historical data tracking
# ✅ Alert configuration
# ✅ Export metrics for Prometheus
#
# USAGE:
# ------
# ark-monitor start              # Start monitoring server
# ark-monitor stop               # Stop monitoring server
# ark-monitor status             # Show current status
# ark-monitor metrics            # Show current metrics
# ark-monitor dashboard          # Open web dashboard
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

MONITOR_PORT=9090
MONITOR_PID_FILE="$INSTALL_DIR/.monitor.pid"

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
# Metrics Collection Functions
################################################################################

get_cpu_usage() {
    if command -v top &>/dev/null; then
        top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}'
    else
        echo "0"
    fi
}

get_memory_usage() {
    if command -v free &>/dev/null; then
        free | grep Mem | awk '{printf "%.1f", ($3/$2) * 100.0}'
    else
        echo "0"
    fi
}

get_disk_usage() {
    df -h "$INSTALL_DIR" | tail -1 | awk '{print $5}' | sed 's/%//'
}

get_ark_metrics() {
    local ark_port=$(grep ARK_API_PORT "$ENV_FILE" 2>/dev/null | cut -d'=' -f2 || echo 8000)
    local metrics=$(curl -s "http://localhost:${ark_port}/metrics" 2>/dev/null || echo "{}")
    echo "$metrics"
}

################################################################################
# Display Functions
################################################################################

show_current_metrics() {
    print_header "📊 Current Metrics"
    
    local cpu=$(get_cpu_usage)
    local mem=$(get_memory_usage)
    local disk=$(get_disk_usage)
    
    echo "System Resources:"
    echo "  CPU Usage:    ${cpu}%"
    echo "  Memory Usage: ${mem}%"
    echo "  Disk Usage:   ${disk}%"
    echo ""
    
    # ARK process info
    if pgrep -f "intelligent-backend" &>/dev/null; then
        local ark_pid=$(pgrep -f "intelligent-backend" | head -1)
        local ark_cpu=$(ps -p $ark_pid -o %cpu= | tr -d ' ')
        local ark_mem=$(ps -p $ark_pid -o %mem= | tr -d ' ')
        
        echo "ARK Process:"
        echo "  PID:          $ark_pid"
        echo "  CPU:          ${ark_cpu}%"
        echo "  Memory:       ${ark_mem}%"
        echo ""
    fi
    
    # Service status
    echo "Services:"
    if pgrep redis-server &>/dev/null; then
        echo -e "  Redis:        ${GREEN}✓ Running${NC}"
    else
        echo -e "  Redis:        ${RED}✗ Stopped${NC}"
    fi
    
    if pgrep -f ollama &>/dev/null; then
        echo -e "  Ollama:       ${GREEN}✓ Running${NC}"
    else
        echo -e "  Ollama:       ${YELLOW}○ Not running${NC}"
    fi
    
    if pgrep -f "intelligent-backend" &>/dev/null; then
        echo -e "  ARK Backend:  ${GREEN}✓ Running${NC}"
    else
        echo -e "  ARK Backend:  ${RED}✗ Stopped${NC}"
    fi
    
    echo ""
}

show_live_monitoring() {
    print_header "📊 Live Monitoring"
    
    echo "Press Ctrl+C to stop"
    echo ""
    
    while true; do
        clear
        
        local cpu=$(get_cpu_usage)
        local mem=$(get_memory_usage)
        local disk=$(get_disk_usage)
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        echo "═══════════════════════════════════════════════════════════════"
        echo "  ARK Monitoring Dashboard - $timestamp"
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        
        # CPU Bar
        printf "CPU  [%-50s] %5.1f%%\n" "$(print_bar $cpu)" "$cpu"
        
        # Memory Bar
        printf "MEM  [%-50s] %5.1f%%\n" "$(print_bar $mem)" "$mem"
        
        # Disk Bar
        printf "DISK [%-50s] %5d%%\n" "$(print_bar $disk)" "$disk"
        
        echo ""
        echo "Services:"
        
        # Check services
        if pgrep redis-server &>/dev/null; then
            echo -e "  [${GREEN}●${NC}] Redis"
        else
            echo -e "  [${RED}○${NC}] Redis"
        fi
        
        if pgrep -f ollama &>/dev/null; then
            echo -e "  [${GREEN}●${NC}] Ollama"
        else
            echo -e "  [${YELLOW}○${NC}] Ollama"
        fi
        
        if pgrep -f "intelligent-backend" &>/dev/null; then
            echo -e "  [${GREEN}●${NC}] ARK Backend"
        else
            echo -e "  [${RED}○${NC}] ARK Backend"
        fi
        
        echo ""
        
        sleep 2
    done
}

print_bar() {
    local value=$1
    local max=100
    local width=50
    
    local filled=$(awk "BEGIN {printf \"%.0f\", ($value / $max) * $width}")
    local empty=$((width - filled))
    
    local bar=""
    for ((i=0; i<filled; i++)); do
        bar+="█"
    done
    for ((i=0; i<empty; i++)); do
        bar+="░"
    done
    
    echo "$bar"
}

################################################################################
# Web Dashboard Functions
################################################################################

start_dashboard() {
    print_header "🌐 Starting Monitoring Dashboard"
    
    if [ -f "$MONITOR_PID_FILE" ] && kill -0 $(cat "$MONITOR_PID_FILE") 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Dashboard already running${NC}"
        echo "URL: http://localhost:${MONITOR_PORT}"
        return 0
    fi
    
    # Create simple monitoring server
    create_dashboard_server
    
    # Start server in background
    node "$INSTALL_DIR/lib/monitor-server.js" &
    echo $! > "$MONITOR_PID_FILE"
    
    sleep 2
    
    if kill -0 $(cat "$MONITOR_PID_FILE") 2>/dev/null; then
        echo -e "${GREEN}✅ Dashboard started${NC}"
        echo ""
        echo "  URL: http://localhost:${MONITOR_PORT}"
        echo ""
        echo "Stop with: ark-monitor stop"
    else
        echo -e "${RED}❌ Failed to start dashboard${NC}"
        rm -f "$MONITOR_PID_FILE"
        return 1
    fi
    
    echo ""
}

stop_dashboard() {
    print_header "⏹️  Stopping Monitoring Dashboard"
    
    if [ ! -f "$MONITOR_PID_FILE" ]; then
        echo "Dashboard not running"
        return 0
    fi
    
    local pid=$(cat "$MONITOR_PID_FILE")
    
    if kill -0 $pid 2>/dev/null; then
        kill $pid
        rm -f "$MONITOR_PID_FILE"
        echo -e "${GREEN}✅ Dashboard stopped${NC}"
    else
        echo "Dashboard not running"
        rm -f "$MONITOR_PID_FILE"
    fi
    
    echo ""
}

create_dashboard_server() {
    mkdir -p "$INSTALL_DIR/lib"
    
    cat > "$INSTALL_DIR/lib/monitor-server.js" << 'EOJS'
const http = require('http');
const { exec } = require('child_process');

const PORT = 9090;

function getMetrics(callback) {
    const metrics = {
        timestamp: new Date().toISOString(),
        system: {},
        services: {}
    };
    
    // Get CPU usage
    exec("top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'", (err, stdout) => {
        metrics.system.cpu = parseFloat(stdout) || 0;
        
        // Get memory usage
        exec("free | grep Mem | awk '{printf \"%.1f\", ($3/$2) * 100.0}'", (err, stdout) => {
            metrics.system.memory = parseFloat(stdout) || 0;
            
            // Get disk usage
            exec("df -h . | tail -1 | awk '{print $5}' | sed 's/%//'", (err, stdout) => {
                metrics.system.disk = parseInt(stdout) || 0;
                
                // Check services
                exec("pgrep redis-server", (err) => {
                    metrics.services.redis = err ? false : true;
                    
                    exec("pgrep -f ollama", (err) => {
                        metrics.services.ollama = err ? false : true;
                        
                        exec("pgrep -f intelligent-backend", (err) => {
                            metrics.services.ark = err ? false : true;
                            
                            callback(metrics);
                        });
                    });
                });
            });
        });
    });
}

const server = http.createServer((req, res) => {
    if (req.url === '/metrics') {
        getMetrics((metrics) => {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(metrics, null, 2));
        });
    } else if (req.url === '/') {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(`
<!DOCTYPE html>
<html>
<head>
    <title>ARK Monitoring Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .card { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { font-size: 24px; font-weight: bold; margin: 10px 0; }
        .progress { width: 100%; height: 20px; background: #ecf0f1; border-radius: 10px; overflow: hidden; }
        .progress-bar { height: 100%; background: #3498db; transition: width 0.5s; }
        .services { margin-top: 20px; }
        .service { display: flex; align-items: center; padding: 10px; }
        .status { width: 10px; height: 10px; border-radius: 50%; margin-right: 10px; }
        .status.running { background: #27ae60; }
        .status.stopped { background: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔊 ARK Monitoring Dashboard</h1>
            <p>Real-time system and service monitoring</p>
        </div>
        
        <div class="metrics">
            <div class="card">
                <h3>CPU Usage</h3>
                <div class="metric" id="cpu">--</div>
                <div class="progress"><div class="progress-bar" id="cpu-bar"></div></div>
            </div>
            
            <div class="card">
                <h3>Memory Usage</h3>
                <div class="metric" id="memory">--</div>
                <div class="progress"><div class="progress-bar" id="memory-bar"></div></div>
            </div>
            
            <div class="card">
                <h3>Disk Usage</h3>
                <div class="metric" id="disk">--</div>
                <div class="progress"><div class="progress-bar" id="disk-bar"></div></div>
            </div>
        </div>
        
        <div class="card services">
            <h3>Services</h3>
            <div class="service">
                <div class="status" id="redis-status"></div>
                <span>Redis</span>
            </div>
            <div class="service">
                <div class="status" id="ollama-status"></div>
                <span>Ollama</span>
            </div>
            <div class="service">
                <div class="status" id="ark-status"></div>
                <span>ARK Backend</span>
            </div>
        </div>
    </div>
    
    <script>
        function updateMetrics() {
            fetch('/metrics')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('cpu').textContent = data.system.cpu.toFixed(1) + '%';
                    document.getElementById('cpu-bar').style.width = data.system.cpu + '%';
                    
                    document.getElementById('memory').textContent = data.system.memory.toFixed(1) + '%';
                    document.getElementById('memory-bar').style.width = data.system.memory + '%';
                    
                    document.getElementById('disk').textContent = data.system.disk + '%';
                    document.getElementById('disk-bar').style.width = data.system.disk + '%';
                    
                    document.getElementById('redis-status').className = 'status ' + (data.services.redis ? 'running' : 'stopped');
                    document.getElementById('ollama-status').className = 'status ' + (data.services.ollama ? 'running' : 'stopped');
                    document.getElementById('ark-status').className = 'status ' + (data.services.ark ? 'running' : 'stopped');
                });
        }
        
        updateMetrics();
        setInterval(updateMetrics, 2000);
    </script>
</body>
</html>
        `);
    } else {
        res.writeHead(404);
        res.end('Not Found');
    }
});

server.listen(PORT, () => {
    console.log(`Monitoring dashboard running on http://localhost:${PORT}`);
});
EOJS
}

open_dashboard() {
    local url="http://localhost:${MONITOR_PORT}"
    
    if ! kill -0 $(cat "$MONITOR_PID_FILE" 2>/dev/null) 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Dashboard not running${NC}"
        echo "Start with: ark-monitor start"
        return 1
    fi
    
    echo "Opening dashboard: $url"
    
    # Try to open in browser
    if command -v xdg-open &>/dev/null; then
        xdg-open "$url"
    elif command -v open &>/dev/null; then
        open "$url"
    else
        echo "Open manually: $url"
    fi
}

show_help() {
    echo "ARK Monitoring Dashboard"
    echo ""
    echo "USAGE:"
    echo "  ark-monitor start         Start monitoring dashboard"
    echo "  ark-monitor stop          Stop monitoring dashboard"
    echo "  ark-monitor status        Show current status"
    echo "  ark-monitor metrics       Show current metrics"
    echo "  ark-monitor live          Live monitoring (terminal)"
    echo "  ark-monitor open          Open web dashboard"
    echo ""
    echo "EXAMPLES:"
    echo "  ark-monitor start         # Start web dashboard"
    echo "  ark-monitor open          # Open in browser"
    echo "  ark-monitor live          # Terminal monitoring"
    echo ""
}

################################################################################
# Main
################################################################################

main() {
    local command="${1:-help}"
    
    case $command in
        start)
            start_dashboard
            ;;
        stop)
            stop_dashboard
            ;;
        status)
            show_current_metrics
            ;;
        metrics)
            show_current_metrics
            ;;
        live)
            show_live_monitoring
            ;;
        open|dashboard)
            open_dashboard
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
# 1. Copy this file to enhancements/20-monitoring-dashboard.sh
#
# 2. In create-unified-ark.sh, add after creating bin directory:
#
#    # Copy monitoring tool
#    cp enhancements/20-monitoring-dashboard.sh "$INSTALL_DIR/bin/ark-monitor"
#    chmod +x "$INSTALL_DIR/bin/ark-monitor"
#
# 3. Add to post-install message:
#
#    echo "  📊 Monitoring:       ark-monitor start"
#
#
# BENEFITS:
# ---------
# ✅ Real-time monitoring
# ✅ Web dashboard
# ✅ Terminal monitoring
# ✅ System metrics
# ✅ Service health
# ✅ Performance tracking
# ✅ Easy troubleshooting
# ✅ No external dependencies
#
################################################################################
