#!/bin/bash
#
# ARK Tools Launcher
# Unified interface for all ARK tools
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ARK_BASE_PATH="${ARK_BASE_PATH:-$(pwd)}"
TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_header() {
    echo -e "\n${CYAN}${BOLD}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║${NC}                    ${BOLD}ARK TOOLS SUITE${NC}                           ${CYAN}${BOLD}║${NC}"
    echo -e "${CYAN}${BOLD}╚═══════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_menu() {
    print_header
    
    echo -e "${BOLD}Available Tools:${NC}\n"
    
    echo -e "${GREEN}1)${NC} ${BOLD}System Administration${NC} - Health checks, database management, logs"
    echo -e "   ${CYAN}ark-admin.py${NC} [health|db-list|db-vacuum|peers|logs]"
    
    echo -e "\n${GREEN}2)${NC} ${BOLD}Backup & Restore${NC} - Full system backup and recovery"
    echo -e "   ${CYAN}ark-backup.sh${NC} [full|data-only|config-only|list|restore]"
    
    echo -e "\n${GREEN}3)${NC} ${BOLD}Real-Time Monitoring${NC} - Live system metrics and performance"
    echo -e "   ${CYAN}ark-monitor.py${NC} [--interval 2]"
    
    echo -e "\n${GREEN}4)${NC} ${BOLD}Database Management${NC} - Query, analyze, and export data"
    echo -e "   ${CYAN}ark-db.py${NC} [list|query|schema|stats|export|search|recent]"
    
    echo -e "\n${GREEN}5)${NC} ${BOLD}Federation Network${NC} - P2P peer management and synchronization"
    echo -e "   ${CYAN}ark-federation.py${NC} [peers|info|add|remove|trust|stats|sync]"
    
    echo -e "\n${GREEN}6)${NC} ${BOLD}Development Tools${NC} - Linting, testing, dev servers"
    echo -e "   ${CYAN}ark-dev.sh${NC} [setup|lint|test|dev|format]"
    
    echo -e "\n${GREEN}7)${NC} ${BOLD}Quick Actions${NC} - Common operations"
    echo -e "\n${GREEN}0)${NC} Exit\n"
    
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_quick_actions() {
    echo -e "\n${BOLD}Quick Actions:${NC}\n"
    echo -e "${GREEN}a)${NC} System health check"
    echo -e "${GREEN}b)${NC} Full system backup"
    echo -e "${GREEN}c)${NC} Start monitoring"
    echo -e "${GREEN}d)${NC} List databases"
    echo -e "${GREEN}e)${NC} View federation peers"
    echo -e "${GREEN}f)${NC} Start dev servers"
    echo -e "${GREEN}g)${NC} Run all tests"
    echo -e "${GREEN}h)${NC} Vacuum databases"
    echo -e "${GREEN}0)${NC} Back to main menu\n"
}

activate_venv() {
    if [ -f "$ARK_BASE_PATH/venv/bin/activate" ]; then
        source "$ARK_BASE_PATH/venv/bin/activate"
    fi
}

# Main menu handlers
admin_menu() {
    print_header
    echo -e "${BOLD}System Administration${NC}\n"
    echo "1) Health check"
    echo "2) List databases"
    echo "3) Vacuum databases"
    echo "4) Analyze databases"
    echo "5) List federation peers"
    echo "6) Analyze logs"
    echo "7) Rotate logs"
    echo "0) Back"
    echo ""
    read -p "Select option: " opt
    
    activate_venv
    
    case $opt in
        1) python3 "$TOOLS_DIR/admin/ark-admin.py" health ;;
        2) python3 "$TOOLS_DIR/admin/ark-admin.py" db-list ;;
        3) python3 "$TOOLS_DIR/admin/ark-admin.py" db-vacuum ;;
        4) python3 "$TOOLS_DIR/admin/ark-admin.py" db-analyze ;;
        5) python3 "$TOOLS_DIR/admin/ark-admin.py" peers ;;
        6) python3 "$TOOLS_DIR/admin/ark-admin.py" logs --days 7 ;;
        7) python3 "$TOOLS_DIR/admin/ark-admin.py" rotate-logs --days 30 ;;
        0) return ;;
        *) echo "Invalid option" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
}

backup_menu() {
    print_header
    echo -e "${BOLD}Backup & Restore${NC}\n"
    echo "1) Full system backup"
    echo "2) Data-only backup"
    echo "3) Config-only backup"
    echo "4) List backups"
    echo "5) Restore from backup"
    echo "0) Back"
    echo ""
    read -p "Select option: " opt
    
    case $opt in
        1) bash "$TOOLS_DIR/backup/ark-backup.sh" full ;;
        2) bash "$TOOLS_DIR/backup/ark-backup.sh" data-only ;;
        3) bash "$TOOLS_DIR/backup/ark-backup.sh" config-only ;;
        4) bash "$TOOLS_DIR/backup/ark-backup.sh" list ;;
        5)
            bash "$TOOLS_DIR/backup/ark-backup.sh" list
            echo ""
            read -p "Enter backup filename: " backup_file
            bash "$TOOLS_DIR/backup/ark-backup.sh" restore "$ARK_BASE_PATH/backups/$backup_file"
            ;;
        0) return ;;
        *) echo "Invalid option" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
}

monitoring_menu() {
    print_header
    echo -e "${BOLD}Real-Time Monitoring${NC}\n"
    echo "Starting monitor... (Press Ctrl+C to stop)"
    echo ""
    sleep 2
    
    activate_venv
    python3 "$TOOLS_DIR/monitoring/ark-monitor.py" --interval 2
}

database_menu() {
    print_header
    echo -e "${BOLD}Database Management${NC}\n"
    echo "1) List tables (ARK)"
    echo "2) List tables (Reasoning)"
    echo "3) Database statistics (ARK)"
    echo "4) Database statistics (Reasoning)"
    echo "5) Execute custom query"
    echo "6) Search table"
    echo "7) Show recent entries"
    echo "0) Back"
    echo ""
    read -p "Select option: " opt
    
    activate_venv
    
    case $opt in
        1) python3 "$TOOLS_DIR/database/ark-db.py" list ark ;;
        2) python3 "$TOOLS_DIR/database/ark-db.py" list reasoning ;;
        3) python3 "$TOOLS_DIR/database/ark-db.py" stats ark ;;
        4) python3 "$TOOLS_DIR/database/ark-db.py" stats reasoning ;;
        5)
            read -p "Database (ark/reasoning): " db
            read -p "SQL query: " query
            python3 "$TOOLS_DIR/database/ark-db.py" query "$db" "$query"
            ;;
        6)
            read -p "Database (ark/reasoning): " db
            read -p "Table name: " table
            read -p "Search term: " term
            python3 "$TOOLS_DIR/database/ark-db.py" search "$db" "$table" "$term"
            ;;
        7)
            read -p "Database (ark/reasoning): " db
            read -p "Table name: " table
            read -p "Limit (default 10): " limit
            python3 "$TOOLS_DIR/database/ark-db.py" recent "$db" "$table" "${limit:-10}"
            ;;
        0) return ;;
        *) echo "Invalid option" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
}

federation_menu() {
    print_header
    echo -e "${BOLD}Federation Network${NC}\n"
    echo "1) List all peers"
    echo "2) Peer information"
    echo "3) Add peer"
    echo "4) Remove peer"
    echo "5) Update trust tier"
    echo "6) Network statistics"
    echo "7) Synchronization status"
    echo "8) Generate keys"
    echo "9) Show keys"
    echo "0) Back"
    echo ""
    read -p "Select option: " opt
    
    activate_venv
    
    case $opt in
        1) python3 "$TOOLS_DIR/federation/ark-federation.py" peers ;;
        2)
            read -p "Peer ID: " peer_id
            python3 "$TOOLS_DIR/federation/ark-federation.py" info "$peer_id"
            ;;
        3)
            read -p "Peer ID: " peer_id
            read -p "Host: " host
            read -p "Port: " port
            read -p "Trust tier (core/trusted/verified/unverified): " trust
            python3 "$TOOLS_DIR/federation/ark-federation.py" add "$peer_id" "$host" "$port" "$trust"
            ;;
        4)
            read -p "Peer ID: " peer_id
            python3 "$TOOLS_DIR/federation/ark-federation.py" remove "$peer_id"
            ;;
        5)
            read -p "Peer ID: " peer_id
            read -p "Trust tier (core/trusted/verified/unverified): " trust
            python3 "$TOOLS_DIR/federation/ark-federation.py" trust "$peer_id" "$trust"
            ;;
        6) python3 "$TOOLS_DIR/federation/ark-federation.py" stats ;;
        7) python3 "$TOOLS_DIR/federation/ark-federation.py" sync ;;
        8) python3 "$TOOLS_DIR/federation/ark-federation.py" genkeys ;;
        9) python3 "$TOOLS_DIR/federation/ark-federation.py" keys ;;
        0) return ;;
        *) echo "Invalid option" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
}

dev_menu() {
    print_header
    echo -e "${BOLD}Development Tools${NC}\n"
    echo "1) Setup dev environment"
    echo "2) Show dev info"
    echo "3) Run linters"
    echo "4) Format code"
    echo "5) Run tests"
    echo "6) Reset databases"
    echo "7) Seed test data"
    echo "8) Start dev servers"
    echo "9) Tail logs"
    echo "0) Back"
    echo ""
    read -p "Select option: " opt
    
    case $opt in
        1) bash "$TOOLS_DIR/dev/ark-dev.sh" setup ;;
        2) bash "$TOOLS_DIR/dev/ark-dev.sh" info ;;
        3) bash "$TOOLS_DIR/dev/ark-dev.sh" lint ;;
        4) bash "$TOOLS_DIR/dev/ark-dev.sh" format ;;
        5) bash "$TOOLS_DIR/dev/ark-dev.sh" test ;;
        6) bash "$TOOLS_DIR/dev/ark-dev.sh" reset-db ;;
        7) bash "$TOOLS_DIR/dev/ark-dev.sh" seed ;;
        8) bash "$TOOLS_DIR/dev/ark-dev.sh" dev ;;
        9)
            read -p "Log file (default: reasoning_api.log): " logfile
            bash "$TOOLS_DIR/dev/ark-dev.sh" logs "${logfile:-reasoning_api.log}"
            ;;
        0) return ;;
        *) echo "Invalid option" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
}

quick_actions_menu() {
    print_quick_actions
    read -p "Select action: " opt
    
    activate_venv
    
    case $opt in
        a) python3 "$TOOLS_DIR/admin/ark-admin.py" health ;;
        b) bash "$TOOLS_DIR/backup/ark-backup.sh" full ;;
        c) python3 "$TOOLS_DIR/monitoring/ark-monitor.py" ;;
        d) python3 "$TOOLS_DIR/database/ark-db.py" list ark && python3 "$TOOLS_DIR/database/ark-db.py" list reasoning ;;
        e) python3 "$TOOLS_DIR/federation/ark-federation.py" peers ;;
        f) bash "$TOOLS_DIR/dev/ark-dev.sh" dev ;;
        g) bash "$TOOLS_DIR/dev/ark-dev.sh" test ;;
        h) python3 "$TOOLS_DIR/admin/ark-admin.py" db-vacuum ;;
        0) return ;;
        *) echo "Invalid option" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
}

# Main loop
while true; do
    clear
    print_menu
    read -p "Select tool (0-7): " choice
    
    case $choice in
        1) admin_menu ;;
        2) backup_menu ;;
        3) monitoring_menu ;;
        4) database_menu ;;
        5) federation_menu ;;
        6) dev_menu ;;
        7) quick_actions_menu ;;
        0) echo -e "\n${GREEN}Goodbye!${NC}\n"; exit 0 ;;
        *) echo -e "\n${RED}Invalid option${NC}"; sleep 1 ;;
    esac
done
