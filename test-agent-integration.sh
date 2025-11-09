#!/bin/bash
# ARK Code Lattice Agent Integration - Test Suite

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║    🤖 ARK AGENT INTEGRATION TEST SUITE 🤖                     ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass_count=0
fail_count=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((pass_count++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((fail_count++))
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Integration Files Exist"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

[ -f "code-lattice-agent-integration.cjs" ]
test_result $? "code-lattice-agent-integration.cjs exists"

[ -f "agent-lattice-personalities.cjs" ]
test_result $? "agent-lattice-personalities.cjs exists"

[ -f "CODE_LATTICE_AGENT_INTEGRATION.md" ]
test_result $? "CODE_LATTICE_AGENT_INTEGRATION.md exists"

[ -f "code-lattice/lattice-manager.js" ]
test_result $? "lattice-manager.js exists"

[ -f "code-lattice/cli.js" ]
test_result $? "CLI tool exists"

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Node.js Module Loading"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test module syntax
node -c code-lattice-agent-integration.cjs 2>/dev/null
test_result $? "code-lattice-agent-integration.cjs syntax valid"

node -c agent-lattice-personalities.cjs 2>/dev/null
test_result $? "agent-lattice-personalities.cjs syntax valid"

node -c agent_tools.cjs 2>/dev/null
test_result $? "agent_tools.cjs syntax valid"

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Code Lattice System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test CLI tool
./bin/ark-lattice stats >/dev/null 2>&1
test_result $? "CLI tool executable and functional"

# Check database
[ -f "code-lattice/lattice.db" ]
test_result $? "SQLite database exists"

# Count nodes
node_count=$(sqlite3 code-lattice/lattice.db "SELECT COUNT(*) FROM nodes;" 2>/dev/null)
if [ "$node_count" = "308" ]; then
    test_result 0 "All 308 nodes loaded in database"
else
    test_result 1 "Node count mismatch: expected 308, got $node_count"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: Agent Integration Module"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test integration module can be loaded
cat > /tmp/test-integration.js << 'EOF'
const { getLatticeInterface } = require('./code-lattice-agent-integration.cjs');
const lattice = getLatticeInterface();
console.log(lattice.isEnabled());
EOF

cd /home/user/webapp && node /tmp/test-integration.js >/dev/null 2>&1
test_result $? "Integration module loads successfully"

rm -f /tmp/test-integration.js

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 5: Agent Personalities"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test personality module
cat > /tmp/test-personalities.js << 'EOF'
const { codeLatticeEnhancedPersonalities, shouldUseLattice } = require('./agent-lattice-personalities.cjs');

// Test all 6 agents exist
const agents = ['Kyle', 'Kenny', 'Joey', 'HRM', 'Aletheia', 'ID'];
const allExist = agents.every(agent => codeLatticeEnhancedPersonalities[agent]);
console.log('all_exist:', allExist);

// Test trigger detection
const triggered = shouldUseLattice('generate a REST API', 'Kenny');
console.log('trigger_works:', triggered);
EOF

cd /home/user/webapp && result=$(node /tmp/test-personalities.js 2>/dev/null)
if echo "$result" | grep -q "all_exist: true"; then
    test_result 0 "All 6 agent personalities defined"
else
    test_result 1 "Agent personalities incomplete"
fi

if echo "$result" | grep -q "trigger_works: true"; then
    test_result 0 "Trigger keyword detection working"
else
    test_result 1 "Trigger keyword detection failed"
fi

rm -f /tmp/test-personalities.js

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 6: Agent Tool Registry"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test tool registry has lattice
cat > /tmp/test-registry.js << 'EOF'
const { AgentToolRegistry } = require('./agent_tools.cjs');
const registry = new AgentToolRegistry();
console.log('has_lattice:', !!registry.lattice);
console.log('lattice_enabled:', registry.lattice.isEnabled());
const tools = registry.listTools();
console.log('lattice_tools:', tools.lattice ? tools.lattice.length : 0);
EOF

cd /home/user/webapp && result=$(node /tmp/test-registry.js 2>/dev/null)
if echo "$result" | grep -q "has_lattice: true"; then
    test_result 0 "Tool registry has lattice interface"
else
    test_result 1 "Tool registry missing lattice"
fi

if echo "$result" | grep -q "lattice_enabled: true"; then
    test_result 0 "Code Lattice is enabled"
else
    test_result 1 "Code Lattice is not enabled"
fi

tools_count=$(echo "$result" | grep "lattice_tools:" | cut -d: -f2 | tr -d ' ')
if [ "$tools_count" -ge "10" ]; then
    test_result 0 "Lattice has $tools_count tools available"
else
    test_result 1 "Expected 10+ lattice tools, got $tools_count"
fi

rm -f /tmp/test-registry.js

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 7: Agent Capabilities"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test each agent's core capability
cat > /tmp/test-capabilities.js << 'EOF'
const { getLatticeInterface } = require('./code-lattice-agent-integration.cjs');
const lattice = getLatticeInterface();

(async () => {
    try {
        // Test Kenny - generateCode
        const gen = await lattice.generateCode(['hello'], { language: 'python' });
        console.log('kenny_works:', gen.success);
        
        // Test Kyle - recommendNodes
        const rec = await lattice.recommendNodes('REST API');
        console.log('kyle_works:', rec.success);
        
        // Test Joey - documentCode
        const doc = await lattice.documentCode(gen);
        console.log('joey_works:', doc.success);
        
        // Test HRM - validateCode
        const val = await lattice.validateCode(gen);
        console.log('hrm_works:', val.success);
        
        // Test Aletheia - reflectOnGeneration
        const ref = await lattice.reflectOnGeneration(gen, val);
        console.log('aletheia_works:', ref.success);
        
        // Test ID - optimizeNodeUsage
        const opt = await lattice.optimizeNodeUsage();
        console.log('id_works:', opt.success);
    } catch (error) {
        console.error('error:', error.message);
    }
})();
EOF

cd /home/user/webapp && result=$(node /tmp/test-capabilities.js 2>/dev/null)

for agent in kenny kyle joey hrm aletheia id; do
    if echo "$result" | grep -q "${agent}_works: true"; then
        test_result 0 "$(echo $agent | awk '{print toupper(substr($0,1,1)) tolower(substr($0,2))}') capability functional"
    else
        test_result 1 "$(echo $agent | awk '{print toupper(substr($0,1,1)) tolower(substr($0,2))}') capability failed"
    fi
done

rm -f /tmp/test-capabilities.js

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 8: Documentation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check documentation completeness
doc_file="CODE_LATTICE_AGENT_INTEGRATION.md"
[ -f "$doc_file" ] && test_result 0 "Integration guide exists" || test_result 1 "Integration guide missing"

# Check for key sections
grep -q "Agent Capabilities" "$doc_file" 2>/dev/null
test_result $? "Documentation has Agent Capabilities section"

grep -q "API Endpoints" "$doc_file" 2>/dev/null
test_result $? "Documentation has API Endpoints section"

grep -q "Quick Start" "$doc_file" 2>/dev/null
test_result $? "Documentation has Quick Start section"

# Count documented agents
agent_count=$(grep -c "^### \*\*" "$doc_file" 2>/dev/null)
if [ "$agent_count" -ge "6" ]; then
    test_result 0 "All 6 agents documented"
else
    test_result 1 "Only $agent_count agents documented"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FINAL RESULTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

total=$((pass_count + fail_count))
pass_percent=$((pass_count * 100 / total))

echo -e "Tests Passed:  ${GREEN}$pass_count${NC}"
echo -e "Tests Failed:  ${RED}$fail_count${NC}"
echo -e "Total Tests:   $total"
echo -e "Success Rate:  ${GREEN}${pass_percent}%${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                            ║${NC}"
    echo -e "${GREEN}║   ✓ ALL TESTS PASSED - INTEGRATION OK!   ║${NC}"
    echo -e "${GREEN}║                                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo "🎉 Code Lattice is fully integrated with all 6 agents!"
    echo "✨ Ready for production use!"
    exit 0
else
    echo -e "${YELLOW}╔════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║                                            ║${NC}"
    echo -e "${YELLOW}║   ⚠️  SOME TESTS FAILED - REVIEW NEEDED   ║${NC}"
    echo -e "${YELLOW}║                                            ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Please review the failed tests above."
    exit 1
fi
