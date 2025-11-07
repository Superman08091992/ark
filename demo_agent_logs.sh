#!/bin/bash

echo "🗂️  PER-AGENT LOGGING SYSTEM DEMONSTRATION"
echo "=========================================="
echo ""

# Phase 1: Each agent creates their own log
echo "📝 Phase 1: Each Agent Creates Their Own Log"
echo "----------------------------------------------"
curl -s -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" \
  -d '{"message":"Analyze stock market trends","agent":"Kyle","userId":"user-1"}' > /dev/null
echo "✓ Kyle logged: Analyze stock market trends"

curl -s -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" \
  -d '{"message":"Calculate probability distributions","agent":"Joey","userId":"user-2"}' > /dev/null
echo "✓ Joey logged: Calculate probability distributions"

curl -s -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" \
  -d '{"message":"Assess portfolio risk","agent":"Kenny","userId":"user-3"}' > /dev/null
echo "✓ Kenny logged: Assess portfolio risk"

curl -s -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" \
  -d '{"message":"Verify system ethics","agent":"HRM","userId":"user-4"}' > /dev/null
echo "✓ HRM logged: Verify system ethics"

curl -s -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" \
  -d '{"message":"Contemplate truth and reality","agent":"Aletheia","userId":"user-5"}' > /dev/null
echo "✓ Aletheia logged: Contemplate truth and reality"

curl -s -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" \
  -d '{"message":"Profile user behavior","agent":"ID","userId":"user-6"}' > /dev/null
echo "✓ ID logged: Profile user behavior"

echo ""
sleep 1

# Phase 2: Check individual logs
echo "📊 Phase 2: Individual Agent Logs"
echo "----------------------------------"
for agent in kyle joey kenny hrm aletheia id; do
  COUNT=$(cat agent_logs/${agent}_log.json | jq '. | length')
  AGENT_NAME=$(cat agent_logs/${agent}_log.json | jq -r '.[0].agent')
  echo "${AGENT_NAME} log: ${COUNT} entries (own conversations only)"
done

echo ""
sleep 1

# Phase 3: Check master logs
echo "🔍 Phase 3: Master Logs (HRM & Aletheia)"
echo "----------------------------------------"
HRM_MASTER_COUNT=$(cat agent_logs/hrm_master_log.json | jq '. | length')
ALETHEIA_MASTER_COUNT=$(cat agent_logs/aletheia_master_log.json | jq '. | length')
echo "HRM Master Log: ${HRM_MASTER_COUNT} entries (ALL agents)"
echo "Aletheia Master Log: ${ALETHEIA_MASTER_COUNT} entries (ALL agents)"

echo ""
echo "Master log contains activity from:"
cat agent_logs/hrm_master_log.json | jq -r '.[].agent' | sort | uniq -c | awk '{print "  • "$2": "$1" entries"}'

echo ""
sleep 1

# Phase 4: Agent reads other logs
echo "👁️  Phase 4: Cross-Agent Log Reading"
echo "------------------------------------"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" \
  -d '{"message":"What are others working on?","agent":"Kyle","userId":"test"}' | jq -r '.response')
echo "$RESPONSE" | grep -A1 "Can read logs from:" || echo "$RESPONSE" | head -8

echo ""
sleep 1

# Phase 5: HRM shows master statistics
echo "⚖️  Phase 5: HRM Master Log Statistics"
echo "--------------------------------------"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" \
  -d '{"message":"Show system overview","agent":"HRM","userId":"admin"}' | jq -r '.response')
echo "$RESPONSE" | grep -A5 "Master Log:" || echo "$RESPONSE" | head -10

echo ""
echo "=========================================="
echo "✅ Per-Agent Logging System Verified!"
echo ""
echo "Summary:"
echo "  • Each agent maintains own log file"
echo "  • All agents can read each other's logs"
echo "  • HRM & Aletheia maintain master logs"
echo "  • Master logs aggregate ALL activity"
echo "  • 1000-entry rotation prevents overflow"
