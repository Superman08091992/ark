#!/bin/bash
echo "🧬 ARK Code Lattice - Complete Ecosystem Test"
echo "=============================================="
echo ""

ecosystems=("C_Language" "Cplusplus" "Java" "TypeScript" "JavaScript" "Python" "Go" "Rust" "Kotlin_Android" "Swift_iOS" "CSharp_DotNet" "Unity_Game" "Unreal_Engine" "SQL_Databases" "NoSQL_Databases" "DevOps_Cloud" "Web_Frontend" "Machine_Learning" "Blockchain_Web3" "Security_Crypto")

for eco in "${ecosystems[@]}"; do
    count=$(sqlite3 lattice.db "SELECT COUNT(*) FROM nodes WHERE category='$eco';")
    echo "📂 $eco: $count nodes"
    sqlite3 lattice.db "SELECT '   - ' || id || ': ' || value FROM nodes WHERE category='$eco' LIMIT 3;"
    echo ""
done

echo "✅ Total nodes across all ecosystems:"
sqlite3 lattice.db "SELECT COUNT(*) FROM nodes;"
