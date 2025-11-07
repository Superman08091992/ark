#!/bin/bash

echo "🎭 INTELLIGENT BACKEND LEARNING DEMONSTRATION"
echo "=============================================="
echo ""
echo "This demo shows how the backend learns and adapts over time."
echo ""

USER_ID="demo-investor-$(date +%s)"

# Phase 1: Initial interaction
echo "📍 Phase 1: First Conversation (No Prior Knowledge)"
echo "---------------------------------------------------"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"I'm interested in AI stocks\", \"agent\": \"Kyle\", \"userId\": \"$USER_ID\"}" | jq -r '.response')
echo "$RESPONSE" | head -8
echo ""
sleep 2

# Phase 2: Build knowledge
echo "📍 Phase 2: Building Knowledge (5 conversations)"
echo "------------------------------------------------"
for i in {1..5}; do
  curl -s -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"Tell me about NVIDIA AI chips, deep learning, and neural networks\", \"agent\": \"Joey\", \"userId\": \"$USER_ID\"}" > /dev/null
  echo "   ✓ Conversation $i processed"
  sleep 0.3
done
echo ""
sleep 1

# Phase 3: Check knowledge growth
echo "📍 Phase 3: Knowledge Graph Status"
echo "-----------------------------------"
AI_KNOWLEDGE=$(curl -s http://localhost:8000/api/knowledge?topic=ai | jq '{strength: .knowledge.strength, related: (.knowledge.related | length)}')
echo "   AI topic knowledge: $AI_KNOWLEDGE"
echo ""
sleep 1

# Phase 4: Different agent, same knowledge
echo "📍 Phase 4: Cross-Agent Learning (Different Agent)"
echo "--------------------------------------------------"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What do we know about AI?\", \"agent\": \"Aletheia\", \"userId\": \"$USER_ID\"}" | jq -r '.response')
echo "$RESPONSE" | head -8
echo ""
sleep 2

# Phase 5: Memory recall
echo "📍 Phase 5: Memory Recall Test"
echo "-------------------------------"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What were my initial interests?\", \"agent\": \"Kyle\", \"userId\": \"$USER_ID\"}" | jq -r '.response')
echo "$RESPONSE" | head -8
echo ""
sleep 2

# Phase 6: Knowledge persistence check
echo "📍 Phase 6: Knowledge Persistence"
echo "---------------------------------"
GRAPH_SIZE=$(cat knowledge_base/knowledge_graph.json | jq '.nodes | length')
TOTAL_STRENGTH=$(cat knowledge_base/knowledge_graph.json | jq '[.nodes[].strength] | add')
echo "   Knowledge nodes: $GRAPH_SIZE"
echo "   Total strength: $TOTAL_STRENGTH"
echo "   File: knowledge_base/knowledge_graph.json"
echo ""

# Summary
echo "=============================================="
echo "✅ DEMONSTRATION COMPLETE"
echo ""
echo "Key Observations:"
echo "  • Knowledge accumulated across conversations"
echo "  • Different agents share the same knowledge"
echo "  • Memory persists in knowledge graph"
echo "  • System adapts responses based on history"
echo "  • Auto-save preserves learning"
echo ""
echo "The backend is now smarter than when we started! 🧠"
