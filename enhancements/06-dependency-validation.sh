#!/bin/bash
##############################################################################
# ARK Dependency Validation
# Enhancement #6 - Validates that binaries actually work
##############################################################################

# This is integrated into the installer, not a standalone script
# ADD THIS TO INSTALLER AFTER DEPENDENCY INSTALLATION

##############################################################################
# VALIDATION CODE FOR INSTALLER
##############################################################################

validate_dependencies() {
    echo ""
    echo "🔍 Validating dependencies..."
    
    VALIDATION_OK=true
    
    # Validate Node.js
    if [ -d "$INSTALL_DIR/deps/node/nodejs" ]; then
        NODE_BIN="$INSTALL_DIR/deps/node/nodejs/bin/node"
        
        echo "   Testing Node.js..."
        
        # Test 1: Basic execution
        if ! "$NODE_BIN" --version &>/dev/null; then
            echo "      ❌ Node.js binary cannot execute"
            echo "         This may be an architecture mismatch"
            VALIDATION_OK=false
        else
            NODE_VERSION=$("$NODE_BIN" --version)
            echo "      ✅ Execution test passed ($NODE_VERSION)"
        fi
        
        # Test 2: JavaScript execution
        if "$NODE_BIN" -e "console.log('test')" &>/dev/null 2>&1; then
            echo "      ✅ JavaScript execution works"
        else
            echo "      ❌ Cannot execute JavaScript code"
            VALIDATION_OK=false
        fi
        
        # Test 3: NPM availability
        NPM_BIN="$INSTALL_DIR/deps/node/nodejs/bin/npm"
        if [ -f "$NPM_BIN" ]; then
            if "$NPM_BIN" --version &>/dev/null; then
                NPM_VERSION=$("$NPM_BIN" --version)
                echo "      ✅ NPM available ($NPM_VERSION)"
            fi
        fi
        
    elif command -v node &>/dev/null; then
        echo "   Testing system Node.js..."
        NODE_VERSION=$(node --version)
        echo "      ✅ System Node.js ($NODE_VERSION)"
        
        if node -e "console.log('test')" &>/dev/null 2>&1; then
            echo "      ✅ JavaScript execution works"
        else
            echo "      ❌ Cannot execute JavaScript"
            VALIDATION_OK=false
        fi
    else
        echo "   ❌ Node.js not found"
        VALIDATION_OK=false
    fi
    
    # Validate Redis
    echo ""
    if [ -d "$INSTALL_DIR/deps/redis/bin" ]; then
        REDIS_BIN="$INSTALL_DIR/deps/redis/bin/redis-server"
        
        echo "   Testing Redis..."
        
        # Test 1: Version command
        if ! "$REDIS_BIN" --version &>/dev/null; then
            echo "      ❌ Redis binary cannot execute"
            echo "         This may be an architecture mismatch"
            VALIDATION_OK=false
        else
            REDIS_VERSION=$("$REDIS_BIN" --version | head -n1)
            echo "      ✅ Execution test passed"
            echo "         $REDIS_VERSION"
        fi
        
        # Test 2: Memory test
        if "$REDIS_BIN" --test-memory 1 &>/dev/null; then
            echo "      ✅ Memory test passed"
        else
            echo "      ⚠️  Memory test failed (may still work)"
        fi
        
        # Test 3: Check redis-cli
        REDIS_CLI="$INSTALL_DIR/deps/redis/bin/redis-cli"
        if [ -f "$REDIS_CLI" ] && "$REDIS_CLI" --version &>/dev/null; then
            echo "      ✅ redis-cli available"
        fi
        
    elif command -v redis-server &>/dev/null; then
        echo "   Testing system Redis..."
        REDIS_VERSION=$(redis-server --version | head -n1)
        echo "      ✅ System Redis"
        echo "         $REDIS_VERSION"
        
        if redis-server --test-memory 1 &>/dev/null; then
            echo "      ✅ Memory test passed"
        fi
    else
        echo "   ❌ Redis not found"
        VALIDATION_OK=false
    fi
    
    # Validate architecture match
    echo ""
    echo "   Architecture Check:"
    SYSTEM_ARCH=$(uname -m)
    echo "      System: $SYSTEM_ARCH"
    
    if [ -f "$INSTALL_DIR/deps/node/nodejs/bin/node" ]; then
        if command -v file &>/dev/null; then
            NODE_ARCH=$(file "$INSTALL_DIR/deps/node/nodejs/bin/node" | grep -o 'x86-64\|x86_64\|aarch64\|ARM\|armv7' | head -n1)
            echo "      Node.js binary: $NODE_ARCH"
            
            case "$SYSTEM_ARCH" in
                x86_64)
                    if [[ "$NODE_ARCH" =~ "x86" ]]; then
                        echo "      ✅ Architecture match"
                    else
                        echo "      ⚠️  Architecture mismatch"
                    fi
                    ;;
                aarch64|arm64)
                    if [[ "$NODE_ARCH" =~ "aarch64\|ARM" ]]; then
                        echo "      ✅ Architecture match"
                    else
                        echo "      ⚠️  Architecture mismatch"
                    fi
                    ;;
            esac
        fi
    fi
    
    # Overall result
    echo ""
    if [ "$VALIDATION_OK" = true ]; then
        echo "✅ All dependencies validated successfully"
        return 0
    else
        echo "❌ Some dependencies failed validation"
        echo ""
        echo "⚠️  Installation may not work properly!"
        echo ""
        read -p "Continue anyway? (y/N): " CONTINUE
        if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
            echo "Installation aborted"
            exit 1
        fi
        return 1
    fi
}

##############################################################################
# INTEGRATION INTO INSTALLER
##############################################################################
#
# Add this function to create-unified-ark.sh after the dependency installation
# section (around line 220), then call it:
#
#   # After installing dependencies
#   validate_dependencies
#
# This will:
# 1. Test Node.js execution
# 2. Test JavaScript code execution
# 3. Check NPM availability
# 4. Test Redis execution
# 5. Run Redis memory test
# 6. Check redis-cli availability
# 7. Verify architecture compatibility
# 8. Provide clear pass/fail feedback
# 9. Allow user to continue or abort
#
##############################################################################
# BENEFITS
##############################################################################
#
# - Catches broken binaries immediately
# - Verifies architecture compatibility
# - Tests actual functionality, not just file existence
# - Provides clear error messages
# - Prevents silent failures
# - Saves debugging time later
# - Professional installation experience
#
##############################################################################
# EXAMPLE OUTPUT
##############################################################################
#
# 🔍 Validating dependencies...
#
#    Testing Node.js...
#       ✅ Execution test passed (v20.10.0)
#       ✅ JavaScript execution works
#       ✅ NPM available (10.2.3)
#
#    Testing Redis...
#       ✅ Execution test passed
#          Redis server v=7.2.4
#       ✅ Memory test passed
#       ✅ redis-cli available
#
#    Architecture Check:
#       System: aarch64
#       Node.js binary: aarch64
#       ✅ Architecture match
#
# ✅ All dependencies validated successfully
#
##############################################################################
