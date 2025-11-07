#!/bin/bash

echo "🧪 Testing Enhanced Learning System"
echo "===================================="
echo ""

# Test 1: Multiple topics to build knowledge graph
echo "1️⃣  Building knowledge with varied topics..."
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I am interested in machine learning for trading algorithms", "agent": "Joey", "userId": "investor-123"}' > /dev/null

curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How does deep learning improve financial forecasting?", "agent": "Aletheia", "userId": "investor-123"}' > /dev/null

curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the risks of algorithmic trading?", "agent": "Kyle", "userId": "investor-123"}' > /dev/null

echo "✅ Sent 3 messages"
sleep 1

# Test 2: Check knowledge accumulation
echo ""
echo "2️⃣  Checking knowledge accumulation..."
KNOWLEDGE=$(curl -s http://localhost:8000/api/knowledge?topic=ai)
STRENGTH=$(echo $KNOWLEDGE | jq -r '.knowledge.strength')
RELATED=$(echo $KNOWLEDGE | jq -r '.knowledge.related | length')
echo "   AI topic strength: $STRENGTH"
echo "   Related topics: $RELATED"

# Test 3: Test memory recall
echo ""
echo "3️⃣  Testing memory recall..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What topics have we discussed?", "agent": "Kenny", "userId": "investor-123"}' | jq -r '.response')
echo "$RESPONSE" | head -10

# Test 4: Check cross-agent learning
echo ""
echo "4️⃣  Testing cross-agent learning..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Based on what others discussed, what should I know about AI trading?", "agent": "HRM", "userId": "investor-123"}' | jq -r '.response')
echo "$RESPONSE" | head -10

# Test 5: Check knowledge persistence
echo ""
echo "5️⃣  Checking knowledge persistence..."
if [ -f "knowledge_base/knowledge_graph.json" ]; then
  NODES=$(cat knowledge_base/knowledge_graph.json | jq '.nodes | length')
  echo "   ✅ Knowledge file exists with $NODES nodes"
else
  echo "   ❌ Knowledge file not found"
fi

echo ""
echo "===================================="
echo "✅ Learning system test complete!"
