#!/bin/bash
##############################################################################
# ARK Uninstaller
# Enhancement #3 - Complete removal with optional backup
##############################################################################

ARK_HOME="${ARK_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║                    ARK Uninstaller                            ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "This will remove ARK from: $ARK_HOME"
echo ""
echo "⚠️  WARNING: This will delete:"
echo "   - All ARK program files"
echo "   - Configuration files"
echo "   - Log files"
echo ""
echo "💾 Data that can be BACKED UP:"
echo "   - Knowledge base"
echo "   - Agent memories"
echo "   - Custom configurations"
echo ""

read -p "Do you want to backup your data first? (Y/n): " BACKUP
if [[ ! "$BACKUP" =~ ^[Nn]$ ]]; then
    BACKUP_FILE="$HOME/ark-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    echo "📦 Creating backup..."
    
    # Backup data and config
    tar -czf "$BACKUP_FILE" -C "$ARK_HOME" \
        data/ \
        config/ \
        logs/ \
        2>/dev/null
    
    if [ -f "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo "✅ Backup saved to: $BACKUP_FILE ($BACKUP_SIZE)"
    else
        echo "⚠️  Backup failed (directories may be empty)"
    fi
    echo ""
fi

read -p "Proceed with uninstallation? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "❌ Uninstallation cancelled"
    exit 0
fi

echo ""
echo "🗑️  Uninstalling ARK..."

# Stop running services
echo "   Stopping services..."
pkill -f ark-redis 2>/dev/null || true
pkill -f intelligent-backend 2>/dev/null || true
pkill -f "node.*ark" 2>/dev/null || true
sleep 1

# Remove from shell RC files
for RC in ~/.bashrc ~/.zshrc ~/.profile; do
    if [ -f "$RC" ]; then
        if grep -q "ARK" "$RC"; then
            echo "   Removing from $(basename $RC)..."
            # Create backup
            cp "$RC" "${RC}.bak-$(date +%Y%m%d)"
            # Remove ARK lines
            sed -i.tmp '/ARK/d' "$RC" 2>/dev/null || sed -i '' '/ARK/d' "$RC" 2>/dev/null
            rm -f "${RC}.tmp"
        fi
    fi
done

# Remove systemd services (if they exist)
if command -v systemctl &>/dev/null; then
    for service in ark ark-redis ark-web; do
        if systemctl list-unit-files | grep -q "$service.service"; then
            echo "   Removing systemd service: $service"
            sudo systemctl stop "$service" 2>/dev/null || true
            sudo systemctl disable "$service" 2>/dev/null || true
            sudo rm -f "/etc/systemd/system/$service.service"
        fi
    done
    sudo systemctl daemon-reload 2>/dev/null || true
fi

# Remove installation directory
echo "   Removing files from: $ARK_HOME"
if [ -d "$ARK_HOME" ]; then
    rm -rf "$ARK_HOME"
    echo "   ✅ Removed installation directory"
else
    echo "   ℹ️  Installation directory not found"
fi

echo ""
echo "✅ ARK has been uninstalled"
echo ""

if [ -n "$BACKUP_FILE" ] && [ -f "$BACKUP_FILE" ]; then
    echo "💾 Your data backup is at: $BACKUP_FILE"
    echo ""
fi

echo "💡 To complete removal:"
echo "   1. Restart your terminal or run: source ~/.bashrc"
if [ -n "$BACKUP_FILE" ]; then
    echo "   2. To restore data later: tar -xzf $BACKUP_FILE -C /new/ark/location"
fi
echo ""
echo "👋 Thank you for using ARK!"

##############################################################################
# INSTALLATION INSTRUCTIONS
##############################################################################
#
# To add uninstaller to your ARK installation:
#
# 1. Copy this file to: $INSTALL_DIR/bin/ark-uninstall
# 2. Make it executable: chmod +x $INSTALL_DIR/bin/ark-uninstall
# 3. Add to installer's launcher script creation section
#
# Or integrate into create-unified-ark.sh:
#
# After creating ark-redis launcher, add:
#
#   # Create uninstaller
#   cp "$SCRIPT_DIR/enhancements/03-uninstaller.sh" "$INSTALL_DIR/bin/ark-uninstall"
#   chmod +x "$INSTALL_DIR/bin/ark-uninstall"
#
##############################################################################
# USAGE
##############################################################################
#
# Run uninstaller:
#   ark-uninstall
#
# Or directly:
#   $ARK_HOME/bin/ark-uninstall
#
# Features:
#   - Interactive prompts
#   - Optional data backup
#   - Stops all services
#   - Removes PATH entries
#   - Cleans systemd services
#   - Complete removal
#
##############################################################################
