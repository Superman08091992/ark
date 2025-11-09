#!/bin/bash
# Check git status and provide recommendations

echo "🔍 Checking git status..."
echo ""

cd ~/ark 2>/dev/null || { echo "❌ ~/ark not found"; exit 1; }

# Show status
git status

echo ""
echo "📝 What changed:"
git diff --stat

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                   RECOMMENDED ACTIONS                          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Option 1: STASH your changes (save for later)"
echo "   git stash"
echo "   git pull origin master"
echo "   git stash pop    # Restore your changes"
echo ""
echo "Option 2: DISCARD your changes (keep GitHub version)"
echo "   git reset --hard HEAD"
echo "   git pull origin master"
echo ""
echo "Option 3: COMMIT your changes first"
echo "   git add -A"
echo "   git commit -m 'Your changes description'"
echo "   git pull origin master"
echo ""
