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

