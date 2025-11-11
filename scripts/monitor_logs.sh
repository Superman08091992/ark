#!/bin/bash
# ARK Log Monitor - Real-time log tailing

echo "📊 ARK Log Monitor"
echo "===================="
echo "Monitoring: logs/*.log"
echo "Press Ctrl+C to exit"
echo ""

tail -f logs/ark_rotating.log logs/ark_errors.log logs/reasoning/pipeline.log
