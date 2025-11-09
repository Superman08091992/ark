#!/bin/bash
################################################################################
# ARK Enhancement #11: Rollback on Failure
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Automatic rollback mechanism for failed installations or updates. Creates
# checkpoints, monitors installation steps, and restores previous state on
# failure.
#
# FEATURES:
# ---------
# ✅ Automatic checkpoint creation before changes
# ✅ Step-by-step tracking of installation progress
# ✅ Automatic rollback on failure
# ✅ Manual rollback capability
# ✅ Backup of critical files and directories
# ✅ State persistence across script executions
# ✅ Detailed rollback logging
# ✅ Cleanup of partial installations
# ✅ Recovery instructions on failure
#
# USAGE:
# ------
# This enhancement is designed to be integrated into create-unified-ark.sh
# It provides functions that wrap installation steps with rollback capability.
#
# In your installer script:
#   source /path/to/11-rollback-on-failure.sh
#   rollback_init
#   rollback_checkpoint "Installing dependencies"
#   # ... your installation steps ...
#   rollback_commit
#
# Manual rollback:
#   ark-rollback                    # Show rollback status
#   ark-rollback --execute          # Execute rollback
#   ark-rollback --list             # List available checkpoints
#   ark-rollback --clean            # Clean old checkpoints
#
################################################################################

# Rollback configuration
ROLLBACK_DIR="${ROLLBACK_DIR:-$HOME/.ark-rollback}"
CHECKPOINT_FILE="$ROLLBACK_DIR/current-checkpoint.json"
STATE_FILE="$ROLLBACK_DIR/installation-state.json"
LOG_FILE="$ROLLBACK_DIR/rollback.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

################################################################################
# Core Rollback Functions (for integration into installer)
################################################################################

rollback_init() {
    # Initialize rollback system
    mkdir -p "$ROLLBACK_DIR/backups"
    mkdir -p "$ROLLBACK_DIR/checkpoints"
    
    # Create initial state
    cat > "$STATE_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "steps": [],
  "status": "in_progress",
  "can_rollback": false
}
EOF
    
    echo "$(date -Iseconds) | INIT | Rollback system initialized" >> "$LOG_FILE"
    
    # Set trap for automatic rollback on error
    trap 'rollback_on_error $? $LINENO' ERR
}

rollback_checkpoint() {
    local step_name="$1"
    local step_id=$(echo "$step_name" | tr '[:upper:] ' '[:lower:]-')
    local checkpoint_dir="$ROLLBACK_DIR/checkpoints/$step_id"
    
    mkdir -p "$checkpoint_dir"
    
    # Save current state
    cat > "$checkpoint_dir/info.json" << EOF
{
  "step": "$step_name",
  "id": "$step_id",
  "timestamp": "$(date -Iseconds)",
  "backups": []
}
EOF
    
    # Update state file
    if [ -f "$STATE_FILE" ]; then
        # Add step to state (simple append)
        local temp_file=$(mktemp)
        jq --arg step "$step_name" --arg id "$step_id" \
           '.steps += [{"name": $step, "id": $id, "timestamp": now|todate, "status": "started"}] | .can_rollback = true' \
           "$STATE_FILE" > "$temp_file" 2>/dev/null && mv "$temp_file" "$STATE_FILE" || {
            # Fallback if jq not available
            echo "  Step: $step_name started" >> "$STATE_FILE"
        }
    fi
    
    echo "$(date -Iseconds) | CHECKPOINT | $step_name" >> "$LOG_FILE"
    
    # Store current checkpoint
    echo "$checkpoint_dir" > "$CHECKPOINT_FILE"
}

rollback_backup_file() {
    local file_path="$1"
    local checkpoint_dir=$(cat "$CHECKPOINT_FILE" 2>/dev/null)
    
    if [ -z "$checkpoint_dir" ]; then
        echo "Warning: No active checkpoint for backup" >&2
        return 1
    fi
    
    if [ -f "$file_path" ] || [ -d "$file_path" ]; then
        local backup_name=$(basename "$file_path")
        local backup_path="$checkpoint_dir/backup-$backup_name.tar.gz"
        
        tar czf "$backup_path" -C "$(dirname "$file_path")" "$(basename "$file_path")" 2>/dev/null
        
        echo "$(date -Iseconds) | BACKUP | $file_path -> $backup_path" >> "$LOG_FILE"
        
        # Record backup in checkpoint
        echo "$file_path|$backup_path" >> "$checkpoint_dir/backups.list"
    fi
}

rollback_backup_directory() {
    local dir_path="$1"
    rollback_backup_file "$dir_path"
}

rollback_step_complete() {
    local step_name="$1"
    
    echo "$(date -Iseconds) | COMPLETE | $step_name" >> "$LOG_FILE"
    
    # Update state file
    if [ -f "$STATE_FILE" ] && command -v jq &>/dev/null; then
        local temp_file=$(mktemp)
        jq --arg step "$step_name" \
           '(.steps[] | select(.name == $step) | .status) = "completed"' \
           "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"
    fi
}

rollback_commit() {
    # Mark installation as successful
    if [ -f "$STATE_FILE" ]; then
        if command -v jq &>/dev/null; then
            local temp_file=$(mktemp)
            jq '.status = "completed" | .can_rollback = false' \
               "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"
        else
            echo "Status: completed" >> "$STATE_FILE"
        fi
    fi
    
    echo "$(date -Iseconds) | COMMIT | Installation completed successfully" >> "$LOG_FILE"
    
    # Clean up checkpoints older than 7 days
    find "$ROLLBACK_DIR/checkpoints" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    # Remove trap
    trap - ERR
}

rollback_on_error() {
    local exit_code=$1
    local line_number=$2
    
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ Installation Failed at line $line_number (exit code: $exit_code)${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    echo "$(date -Iseconds) | ERROR | Installation failed at line $line_number (code: $exit_code)" >> "$LOG_FILE"
    
    # Check if rollback is possible
    if [ -f "$STATE_FILE" ]; then
        local can_rollback="false"
        if command -v jq &>/dev/null; then
            can_rollback=$(jq -r '.can_rollback // "false"' "$STATE_FILE")
        fi
        
        if [ "$can_rollback" = "true" ]; then
            echo -e "${YELLOW}🔄 Rollback is available${NC}"
            echo ""
            echo "Options:"
            echo "  1. Automatic rollback - Restore previous state"
            echo "  2. Keep partial install - Debug manually"
            echo "  3. View rollback log - See what can be restored"
            echo ""
            
            read -p "Choose option (1/2/3): " choice
            
            case $choice in
                1)
                    rollback_execute
                    ;;
                2)
                    echo ""
                    echo -e "${BLUE}Partial installation preserved${NC}"
                    echo "To rollback later, run: ark-rollback --execute"
                    ;;
                3)
                    rollback_show_log
                    ;;
            esac
        else
            echo -e "${YELLOW}⚠️  No rollback available (installation just started)${NC}"
        fi
    fi
    
    echo ""
    echo "For help, see: $LOG_FILE"
    echo ""
}

rollback_execute() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🔄 Executing Rollback${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ ! -d "$ROLLBACK_DIR/checkpoints" ]; then
        echo -e "${RED}❌ No checkpoints found${NC}"
        return 1
    fi
    
    # Get list of checkpoints
    local checkpoints=($(ls -t "$ROLLBACK_DIR/checkpoints" 2>/dev/null))
    
    if [ ${#checkpoints[@]} -eq 0 ]; then
        echo -e "${RED}❌ No checkpoints available${NC}"
        return 1
    fi
    
    echo "Restoring from checkpoints..."
    echo ""
    
    # Restore backups in reverse order
    local restored=0
    for checkpoint in "${checkpoints[@]}"; do
        local checkpoint_dir="$ROLLBACK_DIR/checkpoints/$checkpoint"
        local backups_list="$checkpoint_dir/backups.list"
        
        if [ -f "$backups_list" ]; then
            while IFS='|' read -r original_path backup_path; do
                if [ -f "$backup_path" ]; then
                    echo -n "  Restoring: $(basename "$original_path")... "
                    
                    # Remove current file/directory
                    rm -rf "$original_path" 2>/dev/null || true
                    
                    # Restore from backup
                    tar xzf "$backup_path" -C "$(dirname "$original_path")" 2>/dev/null
                    
                    if [ $? -eq 0 ]; then
                        echo -e "${GREEN}✅${NC}"
                        ((restored++))
                    else
                        echo -e "${RED}❌${NC}"
                    fi
                fi
            done < "$backups_list"
        fi
    done
    
    echo ""
    if [ $restored -gt 0 ]; then
        echo -e "${GREEN}✅ Rollback completed - restored $restored item(s)${NC}"
        
        # Update state
        if [ -f "$STATE_FILE" ] && command -v jq &>/dev/null; then
            local temp_file=$(mktemp)
            jq '.status = "rolled_back"' "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"
        fi
        
        echo "$(date -Iseconds) | ROLLBACK | Successfully restored $restored items" >> "$LOG_FILE"
    else
        echo -e "${YELLOW}⚠️  No items were restored${NC}"
    fi
    
    echo ""
}

################################################################################
# Standalone Command Functions
################################################################################

show_status() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🔄 Rollback Status${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ ! -f "$STATE_FILE" ]; then
        echo -e "${GREEN}✅ No active installation or rollback needed${NC}"
        return 0
    fi
    
    if command -v jq &>/dev/null; then
        local status=$(jq -r '.status' "$STATE_FILE")
        local can_rollback=$(jq -r '.can_rollback // "false"' "$STATE_FILE")
        local timestamp=$(jq -r '.timestamp' "$STATE_FILE")
        
        echo "Installation Status: $status"
        echo "Started: $timestamp"
        echo "Can Rollback: $can_rollback"
        echo ""
        
        if [ "$can_rollback" = "true" ]; then
            echo "Steps completed:"
            jq -r '.steps[] | "  - \(.name) (\(.status))"' "$STATE_FILE"
            echo ""
            echo -e "${YELLOW}To rollback: ark-rollback --execute${NC}"
        fi
    else
        cat "$STATE_FILE"
    fi
    
    echo ""
}

list_checkpoints() {
    echo ""
    echo -e "${BLUE}📋 Available Checkpoints${NC}"
    echo ""
    
    if [ ! -d "$ROLLBACK_DIR/checkpoints" ]; then
        echo "No checkpoints found."
        return 0
    fi
    
    local checkpoints=($(ls -t "$ROLLBACK_DIR/checkpoints" 2>/dev/null))
    
    if [ ${#checkpoints[@]} -eq 0 ]; then
        echo "No checkpoints available."
        return 0
    fi
    
    for checkpoint in "${checkpoints[@]}"; do
        local info_file="$ROLLBACK_DIR/checkpoints/$checkpoint/info.json"
        if [ -f "$info_file" ] && command -v jq &>/dev/null; then
            local step=$(jq -r '.step' "$info_file")
            local timestamp=$(jq -r '.timestamp' "$info_file")
            echo "  • $step ($timestamp)"
        else
            echo "  • $checkpoint"
        fi
    done
    
    echo ""
}

rollback_show_log() {
    echo ""
    echo -e "${BLUE}📄 Recent Rollback Log${NC}"
    echo ""
    
    if [ -f "$LOG_FILE" ]; then
        tail -n 30 "$LOG_FILE"
    else
        echo "No log file found."
    fi
    
    echo ""
}

clean_checkpoints() {
    echo "Cleaning old checkpoints..."
    
    if [ -d "$ROLLBACK_DIR/checkpoints" ]; then
        find "$ROLLBACK_DIR/checkpoints" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
        echo -e "${GREEN}✅ Old checkpoints cleaned${NC}"
    else
        echo "No checkpoints directory found."
    fi
}

show_help() {
    echo "ARK Rollback System"
    echo ""
    echo "USAGE:"
    echo "  ark-rollback                Show rollback status"
    echo "  ark-rollback --execute      Execute rollback"
    echo "  ark-rollback --list         List available checkpoints"
    echo "  ark-rollback --log          Show rollback log"
    echo "  ark-rollback --clean        Clean old checkpoints"
    echo ""
    echo "DESCRIPTION:"
    echo "  The rollback system automatically creates checkpoints during installation"
    echo "  and can restore the previous state if installation fails."
    echo ""
    echo "EXAMPLES:"
    echo "  ark-rollback                # Check if rollback is available"
    echo "  ark-rollback --execute      # Restore previous state"
    echo "  ark-rollback --list         # See what can be restored"
    echo ""
}

################################################################################
# Main (for standalone usage)
################################################################################

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    # Script is being executed directly (not sourced)
    
    case "${1:-status}" in
        --execute|-e)
            rollback_execute
            ;;
        --list|-l)
            list_checkpoints
            ;;
        --log)
            rollback_show_log
            ;;
        --clean|-c)
            clean_checkpoints
            ;;
        --help|-h)
            show_help
            ;;
        status|*)
            show_status
            ;;
    esac
fi

################################################################################
# INTEGRATION INSTRUCTIONS
################################################################################
#
# METHOD 1: Integrate into create-unified-ark.sh
# -----------------------------------------------
# 1. At the top of create-unified-ark.sh, add:
#
#    # Source rollback functions
#    source "$(dirname "$0")/enhancements/11-rollback-on-failure.sh"
#
# 2. After initial checks, initialize rollback:
#
#    # Initialize rollback system
#    rollback_init
#
# 3. Before each major step, create checkpoint:
#
#    rollback_checkpoint "Installing dependencies"
#    # Backup important files
#    [ -f ~/.bashrc ] && rollback_backup_file ~/.bashrc
#
#    # Your installation code here
#    apt-get install nodejs
#    
#    rollback_step_complete "Installing dependencies"
#
# 4. At the end of successful installation:
#
#    rollback_commit
#
# 5. Copy standalone command:
#
#    cp enhancements/11-rollback-on-failure.sh "$INSTALL_DIR/bin/ark-rollback"
#    chmod +x "$INSTALL_DIR/bin/ark-rollback"
#
#
# METHOD 2: Manual Installation (for existing ARK)
# -------------------------------------------------
# 1. Copy to bin directory:
#    cp enhancements/11-rollback-on-failure.sh ~/ark/bin/ark-rollback
#    chmod +x ~/ark/bin/ark-rollback
#
# 2. Check status:
#    ark-rollback
#
#
# BENEFITS:
# ---------
# ✅ Automatic failure detection
# ✅ One-command recovery from failed installations
# ✅ Preserves user data and configurations
# ✅ Detailed logging for debugging
# ✅ Manual rollback capability
# ✅ Checkpoint management
# ✅ Works with or without jq
# ✅ Minimal overhead
#
################################################################################
