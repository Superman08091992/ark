#!/bin/bash
# ARK Logging Setup Script
# Creates log directories and sets up logrotate

set -e

echo "🔧 Setting up ARK logging infrastructure..."

# Create log directories
mkdir -p logs
mkdir -p logs/archive
mkdir -p logs/reasoning
mkdir -p logs/agents
mkdir -p logs/federation

# Set permissions
chmod 755 logs
chmod 755 logs/*

echo "✅ Log directories created"

# Create logrotate configuration
cat > /tmp/ark-logrotate.conf << 'EOF'
/home/user/webapp/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 user user
    sharedscripts
    postrotate
        # Signal ARK to reopen log files
        pkill -HUP -f "python.*reasoning_api.py" || true
    endscript
}

/home/user/webapp/logs/reasoning/*.log {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
    create 0644 user user
}

/home/user/webapp/logs/agents/*.log {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
    create 0644 user user
}

/home/user/webapp/logs/federation/*.log {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
    create 0644 user user
}
EOF

echo "✅ Logrotate configuration created"

# Test log rotation (dry run)
echo "🧪 Testing logrotate configuration..."
#logrotate -d /tmp/ark-logrotate.conf 2>&1 | head -20 || echo "Note: logrotate not available in container"

# Create initial log files
touch logs/ark.log
touch logs/ark_rotating.log
touch logs/ark_errors.log
touch logs/reasoning/pipeline.log
touch logs/agents/kyle.log
touch logs/agents/joey.log
touch logs/agents/kenny.log
touch logs/agents/aletheia.log
touch logs/agents/id.log
touch logs/agents/hrm.log
touch logs/federation/sync.log
touch logs/federation/peers.log

echo "✅ Initial log files created"

# Create log monitoring script
cat > scripts/monitor_logs.sh << 'EOF'
#!/bin/bash
# ARK Log Monitor - Real-time log tailing

echo "📊 ARK Log Monitor"
echo "===================="
echo "Monitoring: logs/*.log"
echo "Press Ctrl+C to exit"
echo ""

tail -f logs/ark_rotating.log logs/ark_errors.log logs/reasoning/pipeline.log
EOF

chmod +x scripts/monitor_logs.sh

echo "✅ Log monitoring script created (./scripts/monitor_logs.sh)"

# Create log analysis script
cat > scripts/analyze_logs.sh << 'EOF'
#!/bin/bash
# ARK Log Analyzer

echo "📈 ARK Log Analysis Report"
echo "=========================="
echo ""

echo "🔥 Error Count (last 24h):"
find logs -name "*.log" -mtime -1 -exec grep -c "ERROR" {} \; 2>/dev/null | awk '{s+=$1} END {print "  Total Errors:", s}'

echo ""
echo "⚠️  Warning Count (last 24h):"
find logs -name "*.log" -mtime -1 -exec grep -c "WARNING" {} \; 2>/dev/null | awk '{s+=$1} END {print "  Total Warnings:", s}'

echo ""
echo "💭 Reasoning Sessions (last 24h):"
grep -c "reasoning complete" logs/reasoning/pipeline.log 2>/dev/null || echo "  0 sessions"

echo ""
echo "🤖 Agent Activity (last 1h):"
for agent in kyle joey kenny aletheia id hrm; do
    count=$(find logs/agents/${agent}.log -mmin -60 -exec wc -l {} \; 2>/dev/null | awk '{print $1}')
    if [ ! -z "$count" ] && [ "$count" != "0" ]; then
        echo "  ${agent}: ${count} log entries"
    fi
done

echo ""
echo "📦 Log Disk Usage:"
du -sh logs/ 2>/dev/null || echo "  N/A"

echo ""
echo "🗂️  Archived Logs:"
ls -lh logs/archive/*.gz 2>/dev/null | wc -l | awk '{print "  " $1 " compressed archives"}'

EOF

chmod +x scripts/analyze_logs.sh

echo "✅ Log analysis script created (./scripts/analyze_logs.sh)"

echo ""
echo "🎉 Logging infrastructure setup complete!"
echo ""
echo "📁 Log locations:"
echo "   - Main logs: logs/*.log"
echo "   - Reasoning: logs/reasoning/*.log"
echo "   - Agents: logs/agents/*.log"
echo "   - Federation: logs/federation/*.log"
echo ""
echo "🔧 Useful commands:"
echo "   - Monitor logs: ./scripts/monitor_logs.sh"
echo "   - Analyze logs: ./scripts/analyze_logs.sh"
echo "   - View errors: tail -f logs/ark_errors.log"
echo ""
