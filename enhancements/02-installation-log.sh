#!/bin/bash
##############################################################################
# ARK Installation Log Enhancement
# Enhancement #2 - Captures complete installation output to file
##############################################################################

# This is a code snippet to add to the installer, not a standalone script
# ADD THIS AT THE BEGINNING OF install.sh (after VERSION and INSTALL_DIR)

# Create installation log
INSTALL_LOG="$INSTALL_DIR/install-$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$(dirname "$INSTALL_LOG")" 2>/dev/null || INSTALL_LOG="/tmp/ark-install-$(date +%Y%m%d-%H%M%S).log"

# Redirect all output to both screen and log file
exec 1> >(tee -a "$INSTALL_LOG")
exec 2>&1

echo "📝 Installation log: $INSTALL_LOG"
echo "   Started: $(date)"
echo "   User: ${USER:-$(whoami)}"
echo "   Platform: $(uname -a)"
echo "   PWD: $(pwd)"
echo "   Script: $0"
echo "   Arguments: $@"
echo ""

##############################################################################
# INSTALLATION INSTRUCTIONS
##############################################################################
#
# To add logging to the installer:
#
# 1. Open create-unified-ark.sh
# 2. Find the line: INSTALL_DIR="${1:-/opt/ark}"
# 3. Add these lines immediately after:
#
#    # Create installation log
#    INSTALL_LOG="$INSTALL_DIR/install-$(date +%Y%m%d-%H%M%S).log"
#    mkdir -p "$(dirname "$INSTALL_LOG")" 2>/dev/null || INSTALL_LOG="/tmp/ark-install-$(date +%Y%m%d-%H%M%S).log"
#    
#    # Redirect all output to both screen and log file
#    exec 1> >(tee -a "$INSTALL_LOG")
#    exec 2>&1
#    
#    echo "📝 Installation log: $INSTALL_LOG"
#    echo "   Started: $(date)"
#    echo "   User: ${USER:-$(whoami)}"
#    echo "   Platform: $(uname -a)"
#    echo ""
#
# 4. Save and recreate package
#
##############################################################################
# BENEFITS
##############################################################################
#
# - Complete record of installation
# - Captures all output (stdout + stderr)
# - Timestamped filename
# - Easy to share for support
# - Debugging made simple
# - Audit trail for troubleshooting
#
##############################################################################
# USAGE AFTER INSTALLATION
##############################################################################
#
# View installation log:
#   cat $ARK_HOME/install-*.log
#
# Share log for support:
#   cat $ARK_HOME/install-*.log | curl -F 'f:1=<-' ix.io
#
# Check for errors:
#   grep -i error $ARK_HOME/install-*.log
#
##############################################################################
