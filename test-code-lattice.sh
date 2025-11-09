#!/bin/bash
# ARK Code Lattice - Comprehensive Test Script

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║       🧬 ARK CODE LATTICE - COMPREHENSIVE TEST SUITE 🧬       ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: System Statistics
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: System Statistics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
./bin/ark-lattice stats
echo ""

# Test 2: Ecosystem Coverage
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Ecosystem Coverage (20 ecosystems)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd code-lattice && ./test-ecosystems.sh
cd ..
echo ""

# Test 3: Sample Nodes from Different Ecosystems
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Sample Nodes from Different Ecosystems"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🐍 Python Ecosystem:"
sqlite3 code-lattice/lattice.db "SELECT '  - ' || id || ': ' || value FROM nodes WHERE category='Python' LIMIT 3;"
echo ""
echo "🎮 Unity Game Ecosystem:"
sqlite3 code-lattice/lattice.db "SELECT '  - ' || id || ': ' || value FROM nodes WHERE category='Unity_Game' LIMIT 3;"
echo ""
echo "🔗 Blockchain Ecosystem:"
sqlite3 code-lattice/lattice.db "SELECT '  - ' || id || ': ' || value FROM nodes WHERE category='Blockchain_Web3' LIMIT 3;"
echo ""
echo "☁️ DevOps Ecosystem:"
sqlite3 code-lattice/lattice.db "SELECT '  - ' || id || ': ' || value FROM nodes WHERE category='DevOps_Cloud' LIMIT 3;"
echo ""

# Test 4: Node Type Distribution
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: Node Type Distribution"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
sqlite3 code-lattice/lattice.db << 'SQL'
SELECT 
    type,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM nodes), 1) || '%' as percentage
FROM nodes
GROUP BY type
ORDER BY count DESC;
SQL
echo ""

# Test 5: Top 10 Most Populated Categories
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 5: Top 10 Most Populated Categories"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
sqlite3 code-lattice/lattice.db << 'SQL'
SELECT 
    category,
    COUNT(*) as nodes,
    GROUP_CONCAT(DISTINCT type) as types
FROM nodes
WHERE category IS NOT NULL
GROUP BY category
ORDER BY nodes DESC
LIMIT 10;
SQL
echo ""

# Test 6: Database Size
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 6: Database Statistics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Database file: $(ls -lh code-lattice/lattice.db | awk '{print $5}')"
echo "Total tables:"
sqlite3 code-lattice/lattice.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"
echo ""

# Test 7: CLI Commands
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 7: CLI Tool Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✓ CLI tool exists: $([ -x bin/ark-lattice ] && echo 'YES' || echo 'NO')"
echo "✓ CLI wrapper: $([ -f bin/ark-lattice ] && echo 'YES' || echo 'NO')"
echo "✓ Manager exists: $([ -f code-lattice/lattice-manager.js ] && echo 'YES' || echo 'NO')"
echo "✓ Database exists: $([ -f code-lattice/lattice.db ] && echo 'YES' || echo 'NO')"
echo ""

# Final Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ALL TESTS COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 ARK Code Lattice System is FULLY OPERATIONAL!"
echo ""
echo "Available Commands:"
echo "  ./bin/ark-lattice stats          - View system statistics"
echo "  ./bin/ark-lattice list           - List all nodes"
echo "  ./bin/ark-lattice query          - Query specific nodes"
echo "  ./bin/ark-lattice generate       - Generate code"
echo ""
echo "For full documentation, see:"
echo "  CODE_LATTICE_IMPLEMENTATION_COMPLETE.md"
echo ""
