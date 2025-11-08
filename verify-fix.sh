#!/bin/bash
##############################################################################
# Verify ARK Installer Fix
# Run this on Termux to check if you have the fixed version
##############################################################################

echo "🔍 ARK Installer Fix Verification"
echo ""

# Check 1: Git status
echo "1️⃣ Checking git status..."
cd ~/ark 2>/dev/null || { echo "❌ ~/ark directory not found!"; exit 1; }

CURRENT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null)
echo "   Current commit: $CURRENT_COMMIT"

# Check 2: Looking for the fix in create-unified-ark.sh
echo ""
echo "2️⃣ Checking for fix in create-unified-ark.sh..."
if grep -q "Write directly to shell rc file" create-unified-ark.sh; then
    echo "   ✅ Fix is present in source file"
else
    echo "   ❌ Fix NOT found in source file"
    echo "   Run: git pull origin master"
    exit 1
fi

# Check 3: Check if old package exists
echo ""
echo "3️⃣ Checking for old packages..."
if ls ark-complete-*.tar.gz &>/dev/null; then
    echo "   ⚠️  Old package(s) found:"
    ls -lh ark-complete-*.tar.gz
    echo ""
    echo "   These were created BEFORE the fix!"
    echo "   Delete them: rm -f ark-complete-*.tar.gz"
else
    echo "   ✅ No old packages found"
fi

# Check 4: Check if old ark-unified exists
echo ""
echo "4️⃣ Checking for old extracted directory..."
if [ -d ark-unified ]; then
    echo "   ⚠️  Old ark-unified directory found"
    echo "   Delete it: rm -rf ark-unified"
else
    echo "   ✅ No old extracted directory"
fi

# Check 5: Verify git remote
echo ""
echo "5️⃣ Checking git remote..."
REMOTE_URL=$(git remote get-url origin 2>/dev/null)
echo "   Remote: $REMOTE_URL"

# Check 6: Check if behind remote
echo ""
echo "6️⃣ Checking if behind remote..."
git fetch origin master &>/dev/null
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/master)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "   ✅ Up to date with remote"
else
    echo "   ⚠️  Behind remote!"
    echo "   Run: git pull origin master"
    BEHIND=$(git rev-list --count HEAD..origin/master)
    echo "   You are $BEHIND commit(s) behind"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                   RECOMMENDED ACTIONS                          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Run these commands in order:"
echo ""
echo "1. Update to latest code:"
echo "   cd ~/ark"
echo "   git pull origin master"
echo ""
echo "2. Clean up old files:"
echo "   rm -f ark-complete-*.tar.gz"
echo "   rm -rf ark-unified"
echo ""
echo "3. Create NEW package (with fix):"
echo "   ./create-unified-ark.sh"
echo ""
echo "4. Test the NEW package:"
echo "   rm -rf ~/ark-test ~/ark-test-install"
echo "   mkdir ~/ark-test"
echo "   tar -xzf ark-complete-*.tar.gz -C ~/ark-test"
echo "   cd ~/ark-test/ark-unified"
echo "   ./install.sh ~/ark-install-test"
echo ""
echo "✅ The NEW package will have the fix embedded!"
