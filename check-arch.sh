#!/bin/bash
##############################################################################
# Check System Architecture
# Helps diagnose bundled binary compatibility issues
##############################################################################

echo "🔍 System Architecture Check"
echo ""

echo "1️⃣ CPU Architecture:"
uname -m
echo ""

echo "2️⃣ Operating System:"
uname -o
echo ""

echo "3️⃣ Full System Info:"
uname -a
echo ""

echo "4️⃣ Architecture Detection:"
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        echo "   Platform: 64-bit Intel/AMD (x86_64)"
        echo "   Node.js needs: linux-x64"
        echo "   Redis needs: x86_64"
        ;;
    aarch64|arm64)
        echo "   Platform: 64-bit ARM (aarch64)"
        echo "   Node.js needs: linux-arm64"
        echo "   Redis needs: aarch64"
        ;;
    armv7l|armv8l)
        echo "   Platform: 32-bit ARM (armv7l)"
        echo "   Node.js needs: linux-armv7l"
        echo "   Redis needs: armv7l"
        ;;
    *)
        echo "   Platform: Unknown ($ARCH)"
        ;;
esac

echo ""
echo "5️⃣ Checking bundled binaries (if exist):"
if [ -f ~/ark/deps/node/nodejs/bin/node ]; then
    echo "   Node.js binary architecture:"
    file ~/ark/deps/node/nodejs/bin/node
else
    echo "   No Node.js binary found"
fi

if [ -f ~/ark/deps/redis/bin/redis-server ]; then
    echo "   Redis binary architecture:"
    file ~/ark/deps/redis/bin/redis-server
else
    echo "   No Redis binary found"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    SOLUTION                                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "For Android/Termux:"
echo "   • Bundled binaries DON'T work (wrong architecture)"
echo "   • Use Termux package manager instead:"
echo ""
echo "     pkg install nodejs redis"
echo ""
echo "This installs ARM-compatible versions for Android."
