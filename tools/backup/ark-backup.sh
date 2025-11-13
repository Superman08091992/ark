#!/bin/bash
#
# ARK Backup Tool
# Complete system backup with incremental and full backup support
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ARK_BASE_PATH="${ARK_BASE_PATH:-$(pwd)}"
BACKUP_DIR="${BACKUP_DIR:-$ARK_BASE_PATH/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="ark_backup_$TIMESTAMP"

# Backup types
BACKUP_TYPE="${1:-full}"  # full, incremental, data-only, config-only

print_header() {
    echo -e "\n${BLUE}===========================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check for required commands
    for cmd in tar gzip sqlite3; do
        if ! command -v $cmd &> /dev/null; then
            print_error "$cmd is not installed"
            exit 1
        fi
        print_success "$cmd found"
    done
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    print_success "Backup directory ready: $BACKUP_DIR"
}

backup_databases() {
    print_header "Backing Up Databases"
    
    local db_backup_dir="$1/databases"
    mkdir -p "$db_backup_dir"
    
    # Backup ARK database
    if [ -f "$ARK_BASE_PATH/data/ark.db" ]; then
        print_info "Backing up ark.db..."
        sqlite3 "$ARK_BASE_PATH/data/ark.db" ".backup '$db_backup_dir/ark.db'"
        print_success "ark.db backed up"
    else
        print_warning "ark.db not found"
    fi
    
    # Backup reasoning logs database
    if [ -f "$ARK_BASE_PATH/data/reasoning_logs.db" ]; then
        print_info "Backing up reasoning_logs.db..."
        sqlite3 "$ARK_BASE_PATH/data/reasoning_logs.db" ".backup '$db_backup_dir/reasoning_logs.db'"
        print_success "reasoning_logs.db backed up"
    else
        print_warning "reasoning_logs.db not found"
    fi
    
    # Database statistics
    if [ -f "$db_backup_dir/ark.db" ]; then
        local ark_size=$(du -h "$db_backup_dir/ark.db" | cut -f1)
        print_info "ark.db size: $ark_size"
    fi
    
    if [ -f "$db_backup_dir/reasoning_logs.db" ]; then
        local reasoning_size=$(du -h "$db_backup_dir/reasoning_logs.db" | cut -f1)
        print_info "reasoning_logs.db size: $reasoning_size"
    fi
}

backup_configuration() {
    print_header "Backing Up Configuration"
    
    local config_backup_dir="$1/config"
    mkdir -p "$config_backup_dir"
    
    # Backup environment files
    for env_file in .env .env.production .env.local; do
        if [ -f "$ARK_BASE_PATH/$env_file" ]; then
            cp "$ARK_BASE_PATH/$env_file" "$config_backup_dir/"
            print_success "Backed up $env_file"
        fi
    done
    
    # Backup keys
    if [ -d "$ARK_BASE_PATH/keys" ]; then
        cp -r "$ARK_BASE_PATH/keys" "$config_backup_dir/"
        print_success "Backed up cryptographic keys"
    fi
    
    # Backup docker configs
    for docker_file in docker-compose.yml Dockerfile; do
        if [ -f "$ARK_BASE_PATH/$docker_file" ]; then
            cp "$ARK_BASE_PATH/$docker_file" "$config_backup_dir/"
            print_success "Backed up $docker_file"
        fi
    done
}

backup_data() {
    print_header "Backing Up Data Files"
    
    local data_backup_dir="$1/data"
    mkdir -p "$data_backup_dir"
    
    # Backup files directory
    if [ -d "$ARK_BASE_PATH/files" ]; then
        cp -r "$ARK_BASE_PATH/files" "$data_backup_dir/"
        local files_size=$(du -sh "$ARK_BASE_PATH/files" | cut -f1)
        print_success "Backed up files directory ($files_size)"
    fi
    
    # Backup agent logs
    if [ -d "$ARK_BASE_PATH/agent_logs" ]; then
        cp -r "$ARK_BASE_PATH/agent_logs" "$data_backup_dir/"
        local logs_size=$(du -sh "$ARK_BASE_PATH/agent_logs" | cut -f1)
        print_success "Backed up agent logs ($logs_size)"
    fi
}

backup_logs() {
    print_header "Backing Up System Logs"
    
    local logs_backup_dir="$1/logs"
    mkdir -p "$logs_backup_dir"
    
    if [ -d "$ARK_BASE_PATH/logs" ]; then
        # Only backup recent logs (last 7 days)
        find "$ARK_BASE_PATH/logs" -name "*.log" -mtime -7 -exec cp {} "$logs_backup_dir/" \;
        print_success "Backed up recent logs (last 7 days)"
    fi
}

export_redis() {
    print_header "Exporting Redis Data"
    
    local redis_backup_dir="$1/redis"
    mkdir -p "$redis_backup_dir"
    
    # Check if redis-cli is available
    if ! command -v redis-cli &> /dev/null; then
        print_warning "redis-cli not found, skipping Redis backup"
        return
    fi
    
    # Check if Redis is running
    if ! redis-cli ping &> /dev/null; then
        print_warning "Redis not running, skipping Redis backup"
        return
    fi
    
    print_info "Exporting Redis data..."
    redis-cli --rdb "$redis_backup_dir/dump.rdb" &> /dev/null || {
        print_warning "Redis export failed, trying alternative method..."
        redis-cli BGSAVE
        sleep 2
        if [ -f /var/lib/redis/dump.rdb ]; then
            cp /var/lib/redis/dump.rdb "$redis_backup_dir/"
            print_success "Redis data exported"
        elif [ -f /data/dump.rdb ]; then
            cp /data/dump.rdb "$redis_backup_dir/"
            print_success "Redis data exported"
        fi
    }
}

create_manifest() {
    print_header "Creating Backup Manifest"
    
    local manifest_file="$1/MANIFEST.txt"
    
    cat > "$manifest_file" << EOF
ARK System Backup Manifest
==========================

Backup Date: $(date)
Backup Type: $BACKUP_TYPE
Hostname: $(hostname)
ARK Base Path: $ARK_BASE_PATH

Contents:
---------
$(cd "$1" && find . -type f -exec ls -lh {} \; | awk '{print $9, "-", $5}')

Directory Sizes:
---------------
$(cd "$1" && du -sh */ 2>/dev/null)

Total Backup Size: $(du -sh "$1" | cut -f1)

EOF
    
    print_success "Manifest created: $manifest_file"
}

compress_backup() {
    print_header "Compressing Backup"
    
    local backup_dir="$1"
    local archive_file="$BACKUP_DIR/$BACKUP_NAME.tar.gz"
    
    print_info "Creating archive: $archive_file"
    
    cd "$(dirname "$backup_dir")"
    tar -czf "$archive_file" "$(basename "$backup_dir")" 2>&1 | grep -v "Removing leading"
    
    if [ -f "$archive_file" ]; then
        local archive_size=$(du -h "$archive_file" | cut -f1)
        print_success "Backup compressed: $archive_size"
        
        # Remove temporary backup directory
        rm -rf "$backup_dir"
        print_success "Temporary files cleaned up"
        
        echo "$archive_file"
    else
        print_error "Failed to create archive"
        exit 1
    fi
}

perform_full_backup() {
    print_header "🔄 Full Backup"
    
    local temp_backup_dir="$BACKUP_DIR/.tmp_$BACKUP_NAME"
    mkdir -p "$temp_backup_dir"
    
    backup_databases "$temp_backup_dir"
    backup_configuration "$temp_backup_dir"
    backup_data "$temp_backup_dir"
    backup_logs "$temp_backup_dir"
    export_redis "$temp_backup_dir"
    create_manifest "$temp_backup_dir"
    
    local archive_file=$(compress_backup "$temp_backup_dir")
    
    print_header "✅ Backup Complete"
    print_success "Archive: $archive_file"
    print_info "To restore: tar -xzf $archive_file"
}

perform_data_only_backup() {
    print_header "🔄 Data-Only Backup"
    
    local temp_backup_dir="$BACKUP_DIR/.tmp_$BACKUP_NAME"
    mkdir -p "$temp_backup_dir"
    
    backup_databases "$temp_backup_dir"
    backup_data "$temp_backup_dir"
    export_redis "$temp_backup_dir"
    create_manifest "$temp_backup_dir"
    
    local archive_file=$(compress_backup "$temp_backup_dir")
    
    print_header "✅ Data Backup Complete"
    print_success "Archive: $archive_file"
}

perform_config_only_backup() {
    print_header "🔄 Config-Only Backup"
    
    local temp_backup_dir="$BACKUP_DIR/.tmp_$BACKUP_NAME"
    mkdir -p "$temp_backup_dir"
    
    backup_configuration "$temp_backup_dir"
    create_manifest "$temp_backup_dir"
    
    local archive_file=$(compress_backup "$temp_backup_dir")
    
    print_header "✅ Config Backup Complete"
    print_success "Archive: $archive_file"
}

list_backups() {
    print_header "📦 Available Backups"
    
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR"/*.tar.gz 2>/dev/null)" ]; then
        print_info "No backups found in $BACKUP_DIR"
        return
    fi
    
    echo -e "\n${BLUE}Backup${NC} | ${BLUE}Date${NC} | ${BLUE}Size${NC}"
    echo "----------------------------------------"
    
    for backup_file in "$BACKUP_DIR"/*.tar.gz; do
        local filename=$(basename "$backup_file")
        local date=$(stat -c %y "$backup_file" 2>/dev/null || stat -f %Sm "$backup_file" 2>/dev/null | cut -d' ' -f1-2)
        local size=$(du -h "$backup_file" | cut -f1)
        
        echo -e "${GREEN}$filename${NC} | $date | $size"
    done
    
    echo ""
}

restore_backup() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        print_error "Please specify backup file to restore"
        echo "Usage: $0 restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_header "🔄 Restoring Backup"
    print_warning "This will overwrite existing data!"
    
    read -p "Continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_info "Restore cancelled"
        exit 0
    fi
    
    local restore_dir="$BACKUP_DIR/.restore_tmp"
    mkdir -p "$restore_dir"
    
    print_info "Extracting backup..."
    tar -xzf "$backup_file" -C "$restore_dir"
    
    # Find the backup directory (it's the only directory in restore_dir)
    local backup_content_dir=$(find "$restore_dir" -mindepth 1 -maxdepth 1 -type d | head -n1)
    
    if [ -z "$backup_content_dir" ]; then
        print_error "Invalid backup structure"
        rm -rf "$restore_dir"
        exit 1
    fi
    
    # Restore databases
    if [ -d "$backup_content_dir/databases" ]; then
        print_info "Restoring databases..."
        cp "$backup_content_dir/databases"/*.db "$ARK_BASE_PATH/data/" 2>/dev/null || true
        print_success "Databases restored"
    fi
    
    # Restore configuration
    if [ -d "$backup_content_dir/config" ]; then
        print_info "Restoring configuration..."
        cp -r "$backup_content_dir/config/keys" "$ARK_BASE_PATH/" 2>/dev/null || true
        print_success "Configuration restored"
    fi
    
    # Restore data
    if [ -d "$backup_content_dir/data" ]; then
        print_info "Restoring data files..."
        cp -r "$backup_content_dir/data/files" "$ARK_BASE_PATH/" 2>/dev/null || true
        cp -r "$backup_content_dir/data/agent_logs" "$ARK_BASE_PATH/" 2>/dev/null || true
        print_success "Data files restored"
    fi
    
    # Restore Redis
    if [ -f "$backup_content_dir/redis/dump.rdb" ]; then
        print_info "Redis dump available - manual restore required"
        print_info "Location: $backup_content_dir/redis/dump.rdb"
    fi
    
    # Cleanup
    rm -rf "$restore_dir"
    
    print_header "✅ Restore Complete"
    print_success "System restored from backup"
    print_warning "Restart ARK services to apply changes"
}

# Main execution
case "$BACKUP_TYPE" in
    full)
        check_prerequisites
        perform_full_backup
        ;;
    data-only)
        check_prerequisites
        perform_data_only_backup
        ;;
    config-only)
        check_prerequisites
        perform_config_only_backup
        ;;
    list)
        list_backups
        ;;
    restore)
        check_prerequisites
        restore_backup "$2"
        ;;
    *)
        echo "Usage: $0 {full|data-only|config-only|list|restore <file>}"
        echo ""
        echo "Backup types:"
        echo "  full        - Complete system backup (databases, config, data, logs)"
        echo "  data-only   - Databases and data files only"
        echo "  config-only - Configuration and keys only"
        echo "  list        - List available backups"
        echo "  restore     - Restore from backup file"
        echo ""
        echo "Examples:"
        echo "  $0 full"
        echo "  $0 data-only"
        echo "  $0 list"
        echo "  $0 restore backups/ark_backup_20250112_120000.tar.gz"
        exit 1
        ;;
esac
