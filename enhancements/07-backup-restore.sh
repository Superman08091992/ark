#!/bin/bash
##############################################################################
# ARK Backup & Restore System
# Enhancement #7 - Data backup and restore capabilities
##############################################################################

##############################################################################
# PART 1: BACKUP SCRIPT (ark-backup)
##############################################################################

backup_ark() {
    ARK_HOME="${ARK_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
    BACKUP_FILE="${1:-$HOME/ark-backup-$(date +%Y%m%d-%H%M%S).tar.gz}"
    
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║                    ARK Backup System                          ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📦 Creating ARK backup..."
    echo "   Source: $ARK_HOME"
    echo "   Backup file: $BACKUP_FILE"
    echo ""
    
    # What to backup
    ITEMS=(
        "data/knowledge_base"
        "data/kyle_infinite_memory"
        "data/agent_logs"
        "config"
        "logs"
    )
    
    # Check what exists
    echo "📁 Items to backup:"
    EXISTING_ITEMS=()
    for item in "${ITEMS[@]}"; do
        if [ -e "$ARK_HOME/$item" ]; then
            SIZE=$(du -sh "$ARK_HOME/$item" 2>/dev/null | cut -f1)
            echo "   ✅ $item ($SIZE)"
            EXISTING_ITEMS+=("$item")
        else
            echo "   ⏭️  $item (doesn't exist, skipping)"
        fi
    done
    
    if [ ${#EXISTING_ITEMS[@]} -eq 0 ]; then
        echo ""
        echo "⚠️  No data to backup!"
        exit 1
    fi
    
    echo ""
    read -p "Proceed with backup? (Y/n): " CONFIRM
    if [[ "$CONFIRM" =~ ^[Nn]$ ]]; then
        echo "Backup cancelled"
        exit 0
    fi
    
    echo ""
    echo "📦 Creating backup archive..."
    
    # Create backup
    if tar -czf "$BACKUP_FILE" -C "$ARK_HOME" "${EXISTING_ITEMS[@]}" 2>/dev/null; then
        SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
        echo ""
        echo "✅ Backup complete!"
        echo ""
        echo "📄 Backup Details:"
        echo "   File: $BACKUP_FILE"
        echo "   Size: $SIZE"
        echo "   Created: $(date)"
        echo ""
        echo "💡 To restore this backup:"
        echo "   ark-restore $BACKUP_FILE"
        echo ""
        echo "   Or manually:"
        echo "   tar -xzf $BACKUP_FILE -C \$ARK_HOME"
    else
        echo ""
        echo "❌ Backup failed!"
        exit 1
    fi
}

##############################################################################
# PART 2: RESTORE SCRIPT (ark-restore)
##############################################################################

restore_ark() {
    ARK_HOME="${ARK_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
    BACKUP_FILE="$1"
    
    if [ -z "$BACKUP_FILE" ]; then
        echo "Usage: ark-restore <backup-file.tar.gz>"
        echo ""
        echo "Available backups:"
        find "$HOME" -name "ark-backup-*.tar.gz" -type f -exec ls -lh {} \; 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
        exit 1
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "❌ Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║                   ARK Restore System                          ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📦 Restoring ARK from backup..."
    echo "   Backup: $BACKUP_FILE"
    echo "   Target: $ARK_HOME"
    echo ""
    
    # Show backup contents
    echo "📋 Backup contains:"
    tar -tzf "$BACKUP_FILE" 2>/dev/null | head -n 20 | sed 's/^/   /'
    TOTAL_FILES=$(tar -tzf "$BACKUP_FILE" 2>/dev/null | wc -l)
    if [ $TOTAL_FILES -gt 20 ]; then
        echo "   ... and $((TOTAL_FILES - 20)) more files"
    fi
    
    echo ""
    echo "⚠️  WARNING: This will overwrite current data!"
    echo ""
    read -p "Proceed with restore? (y/N): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo "Restore cancelled"
        exit 0
    fi
    
    # Stop services before restore
    echo ""
    echo "⏸️  Stopping services..."
    pkill -f ark-redis 2>/dev/null || true
    pkill -f intelligent-backend 2>/dev/null || true
    sleep 1
    
    # Create backup of current state
    echo "📦 Creating safety backup of current state..."
    SAFETY_BACKUP="$HOME/ark-pre-restore-$(date +%Y%m%d-%H%M%S).tar.gz"
    tar -czf "$SAFETY_BACKUP" -C "$ARK_HOME" data/ config/ logs/ 2>/dev/null || true
    echo "   Safety backup: $SAFETY_BACKUP"
    
    # Restore
    echo ""
    echo "📥 Restoring files..."
    if tar -xzf "$BACKUP_FILE" -C "$ARK_HOME"; then
        echo ""
        echo "✅ Restore complete!"
        echo ""
        echo "🔄 Please restart ARK services:"
        echo "   ark-redis &"
        echo "   ark"
        echo ""
        echo "💾 Safety backup of old data:"
        echo "   $SAFETY_BACKUP"
    else
        echo ""
        echo "❌ Restore failed!"
        echo ""
        echo "💾 Your data is safe in the safety backup:"
        echo "   $SAFETY_BACKUP"
        exit 1
    fi
}

##############################################################################
# PART 3: AUTOMATIC BACKUP SCHEDULER
##############################################################################

setup_auto_backup() {
    ARK_HOME="${ARK_HOME:-/opt/ark}"
    BACKUP_DIR="${1:-$HOME/ark-backups}"
    SCHEDULE="${2:-daily}"  # daily, weekly, hourly
    
    echo "Setting up automatic backups..."
    echo "   Schedule: $SCHEDULE"
    echo "   Location: $BACKUP_DIR"
    
    mkdir -p "$BACKUP_DIR"
    
    # Create backup script
    cat > "$ARK_HOME/bin/ark-auto-backup" << 'AUTO_BACKUP_EOF'
#!/bin/bash
ARK_HOME="${ARK_HOME:-/opt/ark}"
BACKUP_DIR="${ARK_BACKUP_DIR:-$HOME/ark-backups}"
BACKUP_FILE="$BACKUP_DIR/auto-backup-$(date +%Y%m%d-%H%M%S).tar.gz"

# Create backup
tar -czf "$BACKUP_FILE" -C "$ARK_HOME" data/ config/ 2>/dev/null

# Keep only last 7 backups
cd "$BACKUP_DIR"
ls -t ark-backup-*.tar.gz auto-backup-*.tar.gz 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null

echo "Backup created: $BACKUP_FILE"
AUTO_BACKUP_EOF
    
    chmod +x "$ARK_HOME/bin/ark-auto-backup"
    
    # Add to crontab based on schedule
    case "$SCHEDULE" in
        hourly)
            CRON_ENTRY="0 * * * * $ARK_HOME/bin/ark-auto-backup"
            ;;
        daily)
            CRON_ENTRY="0 2 * * * $ARK_HOME/bin/ark-auto-backup"
            ;;
        weekly)
            CRON_ENTRY="0 2 * * 0 $ARK_HOME/bin/ark-auto-backup"
            ;;
    esac
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    
    echo "✅ Automatic backup configured!"
    echo "   Backups will be saved to: $BACKUP_DIR"
    echo "   Last 7 backups will be kept"
}

##############################################################################
# USAGE EXAMPLES
##############################################################################
#
# Backup:
#   ark-backup                                    # Auto-named backup
#   ark-backup ~/my-ark-backup.tar.gz            # Custom name
#
# Restore:
#   ark-restore ~/ark-backup-20251108.tar.gz
#
# Auto-backup setup:
#   ark-auto-backup-setup daily                  # Daily at 2 AM
#   ark-auto-backup-setup weekly                 # Weekly on Sunday
#
# List backups:
#   ls -lh ~/ark-backup-*.tar.gz
#
##############################################################################
# INSTALLATION
##############################################################################
#
# Add to installer:
#
#   # Create backup script
#   cat > "$INSTALL_DIR/bin/ark-backup" << 'BACKUP_EOF'
#   [paste backup_ark function here]
#   backup_ark "$@"
#   BACKUP_EOF
#   chmod +x "$INSTALL_DIR/bin/ark-backup"
#
#   # Create restore script
#   cat > "$INSTALL_DIR/bin/ark-restore" << 'RESTORE_EOF'
#   [paste restore_ark function here]
#   restore_ark "$@"
#   RESTORE_EOF
#   chmod +x "$INSTALL_DIR/bin/ark-restore"
#
##############################################################################
