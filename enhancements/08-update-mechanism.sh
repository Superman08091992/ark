#!/bin/bash
##############################################################################
# ARK Update Mechanism
# Enhancement #8 - In-place updates without reinstalling
##############################################################################

ARK_HOME="${ARK_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$ARK_HOME"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║                      ARK Updater                              ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if git repo
if [ ! -d ".git" ]; then
    echo "❌ Not a git repository"
    echo "   Updates only available for git installations"
    echo ""
    echo "💡 To enable updates:"
    echo "   cd $ARK_HOME"
    echo "   git init"
    echo "   git remote add origin https://github.com/Superman08091992/ark.git"
    echo "   git fetch origin"
    echo "   git branch --set-upstream-to=origin/master master"
    exit 1
fi

# Current version
CURRENT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

echo "📍 Current State:"
echo "   Branch: $CURRENT_BRANCH"
echo "   Commit: $CURRENT_COMMIT"
echo "   Location: $ARK_HOME"
echo ""

# Check for updates
echo "🔍 Checking for updates..."
git fetch origin 2>/dev/null

REMOTE_COMMIT=$(git rev-parse --short origin/$CURRENT_BRANCH 2>/dev/null || echo "unknown")

if [ "$CURRENT_COMMIT" = "$REMOTE_COMMIT" ]; then
    echo "✅ Already up to date!"
    echo "   You are running the latest version."
    exit 0
fi

echo "📦 Update available:"
echo "   Current: $CURRENT_COMMIT"
echo "   Latest:  $REMOTE_COMMIT"
echo ""

# Show changes
echo "📝 Changes in this update:"
git log --oneline --no-merges HEAD..origin/$CURRENT_BRANCH | head -n10 | sed 's/^/   /'
TOTAL_COMMITS=$(git log --oneline --no-merges HEAD..origin/$CURRENT_BRANCH | wc -l)
if [ $TOTAL_COMMITS -gt 10 ]; then
    echo "   ... and $((TOTAL_COMMITS - 10)) more commits"
fi

echo ""
read -p "Install update? (Y/n): " CONFIRM
if [[ "$CONFIRM" =~ ^[Nn]$ ]]; then
    echo "❌ Update cancelled"
    exit 0
fi

# Create backup
echo ""
echo "📦 Creating backup..."
BACKUP_FILE="/tmp/ark-backup-pre-update-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" -C "$ARK_HOME" . --exclude='.git' --exclude='node_modules' --exclude='*.tar.gz' 2>/dev/null

if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "   ✅ Backup created: $BACKUP_FILE ($BACKUP_SIZE)"
else
    echo "   ⚠️  Backup failed (continuing anyway)"
fi

# Stop services
echo ""
echo "⏸️  Stopping services..."
pkill -f ark-redis 2>/dev/null || true
pkill -f intelligent-backend 2>/dev/null || true
pkill -f "node.*ark" 2>/dev/null || true
sleep 2
echo "   ✅ Services stopped"

# Pull updates
echo ""
echo "⬇️  Downloading update..."
if git pull origin $CURRENT_BRANCH; then
    NEW_COMMIT=$(git rev-parse --short HEAD)
    echo "   ✅ Update downloaded"
    echo "   New version: $NEW_COMMIT"
else
    echo "   ❌ Update failed!"
    echo ""
    echo "💾 Restore from backup:"
    echo "   tar -xzf $BACKUP_FILE -C $ARK_HOME"
    exit 1
fi

# Update dependencies if package.json changed
if git diff --name-only $CURRENT_COMMIT HEAD | grep -q "package.json"; then
    echo ""
    echo "📦 Updating dependencies..."
    if [ -d "lib/web" ] && [ -f "lib/web/package.json" ]; then
        cd lib/web
        if command -v npm &>/dev/null; then
            npm install
            echo "   ✅ Dependencies updated"
        else
            echo "   ⚠️  npm not available, skipping"
        fi
        cd "$ARK_HOME"
    fi
fi

# Run migration scripts if they exist
if [ -d "migrations" ]; then
    echo ""
    echo "🔄 Running migrations..."
    for migration in migrations/*.sh; do
        if [ -f "$migration" ] && [ -x "$migration" ]; then
            echo "   Running $(basename $migration)..."
            bash "$migration"
        fi
    done
fi

# Restart services
echo ""
echo "🔄 Restarting services..."
if [ -f "bin/ark-redis" ]; then
    "$ARK_HOME/bin/ark-redis" --daemonize yes 2>/dev/null && echo "   ✅ Redis started"
fi
sleep 1
if [ -f "bin/ark" ]; then
    nohup "$ARK_HOME/bin/ark" > /dev/null 2>&1 &
    echo "   ✅ ARK backend started"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║                 ✅ UPDATE COMPLETE! ✅                        ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Updated from $CURRENT_COMMIT to $NEW_COMMIT"
echo ""
echo "💡 What's new:"
git log --oneline --no-merges $CURRENT_COMMIT..HEAD | head -n5 | sed 's/^/   /'
echo ""
echo "📝 View full changelog:"
echo "   git log $CURRENT_COMMIT..HEAD"
echo ""
echo "💾 Backup location:"
echo "   $BACKUP_FILE"
echo ""
echo "🔄 If there are issues, rollback with:"
echo "   tar -xzf $BACKUP_FILE -C $ARK_HOME"
echo "   ark-redis & ark"

##############################################################################
# ADDITIONAL FEATURES
##############################################################################

# Auto-update checker (add to .bashrc or startup)
check_updates_on_start() {
    ARK_HOME="${ARK_HOME:-/opt/ark}"
    if [ -d "$ARK_HOME/.git" ]; then
        cd "$ARK_HOME"
        git fetch origin --quiet 2>/dev/null
        LOCAL=$(git rev-parse HEAD 2>/dev/null)
        REMOTE=$(git rev-parse origin/master 2>/dev/null)
        
        if [ "$LOCAL" != "$REMOTE" ] && [ -n "$LOCAL" ] && [ -n "$REMOTE" ]; then
            COMMITS_BEHIND=$(git rev-list --count HEAD..origin/master 2>/dev/null || echo "0")
            if [ "$COMMITS_BEHIND" -gt 0 ]; then
                echo "💡 ARK update available! ($COMMITS_BEHIND new commits)"
                echo "   Run: ark-update"
            fi
        fi
    fi
}

##############################################################################
# USAGE
##############################################################################
#
# Check and install updates:
#   ark-update
#
# Check without installing:
#   ark-update --check
#
# Auto-update (no prompts):
#   ark-update --yes
#
# View changelog:
#   cd $ARK_HOME && git log
#
# Rollback:
#   tar -xzf /tmp/ark-backup-pre-update-*.tar.gz -C $ARK_HOME
#
##############################################################################
# INSTALLATION
##############################################################################
#
# Add to installer:
#   cp enhancements/08-update-mechanism.sh $INSTALL_DIR/bin/ark-update
#   chmod +x $INSTALL_DIR/bin/ark-update
#
# Add update check to shell RC:
#   echo 'check_updates_on_start' >> ~/.bashrc
#
##############################################################################
