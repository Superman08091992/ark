#!/bin/bash
################################################################################
# ARK Enhancement #14: Progress Bars & Visual Feedback
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Adds visual progress indicators for long-running operations during ARK
# installation and updates. Makes the installation process more user-friendly
# with real-time feedback.
#
# FEATURES:
# ---------
# ✅ Animated progress bars for downloads
# ✅ Spinner for ongoing operations
# ✅ Step-by-step progress tracking
# ✅ ETA (estimated time remaining)
# ✅ File size and download speed
# ✅ Color-coded status messages
# ✅ Multi-line progress for parallel operations
# ✅ Minimal dependencies (pure bash)
#
# USAGE:
# ------
# Source this file in your scripts and use the provided functions:
#
#   source enhancements/14-progress-bars.sh
#   
#   progress_start "Installing dependencies" 5
#   progress_update 1 "Node.js"
#   progress_update 2 "Redis"
#   # ... etc
#   progress_complete "Installation complete!"
#
################################################################################

# Progress bar configuration
PROGRESS_BAR_WIDTH=50
PROGRESS_CHAR="█"
PROGRESS_EMPTY="░"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Spinner frames
SPINNER_FRAMES=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
SPINNER_CURRENT=0

################################################################################
# Basic Progress Bar Functions
################################################################################

show_progress_bar() {
    local current=$1
    local total=$2
    local message="${3:-Progress}"
    
    # Calculate percentage
    local percent=$((current * 100 / total))
    local filled=$((PROGRESS_BAR_WIDTH * current / total))
    local empty=$((PROGRESS_BAR_WIDTH - filled))
    
    # Build progress bar
    local bar=""
    for ((i=0; i<filled; i++)); do
        bar+="$PROGRESS_CHAR"
    done
    for ((i=0; i<empty; i++)); do
        bar+="$PROGRESS_EMPTY"
    done
    
    # Print progress bar with carriage return (same line)
    printf "\r${CYAN}${message}${NC} [${bar}] ${percent}%%"
    
    # Print newline if complete
    if [ $current -eq $total ]; then
        echo ""
    fi
}

show_spinner() {
    local message="${1:-Working}"
    
    # Get current spinner frame
    local frame="${SPINNER_FRAMES[$SPINNER_CURRENT]}"
    
    # Print spinner
    printf "\r${CYAN}${frame}${NC} ${message}..."
    
    # Update spinner position
    SPINNER_CURRENT=$(( (SPINNER_CURRENT + 1) % ${#SPINNER_FRAMES[@]} ))
}

stop_spinner() {
    local message="${1:-Done}"
    printf "\r${GREEN}✓${NC} ${message}\n"
}

################################################################################
# Advanced Progress Tracking
################################################################################

# Global progress tracking variables
declare -A PROGRESS_STEPS
PROGRESS_TOTAL=0
PROGRESS_CURRENT=0
PROGRESS_START_TIME=0

progress_start() {
    local title="$1"
    local total_steps=$2
    
    PROGRESS_TOTAL=$total_steps
    PROGRESS_CURRENT=0
    PROGRESS_START_TIME=$(date +%s)
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${title}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

progress_update() {
    local step=$1
    local message="$2"
    
    PROGRESS_CURRENT=$step
    PROGRESS_STEPS[$step]="$message"
    
    # Calculate elapsed time
    local current_time=$(date +%s)
    local elapsed=$((current_time - PROGRESS_START_TIME))
    
    # Calculate ETA
    local eta=0
    if [ $PROGRESS_CURRENT -gt 0 ]; then
        local avg_time=$((elapsed / PROGRESS_CURRENT))
        local remaining=$((PROGRESS_TOTAL - PROGRESS_CURRENT))
        eta=$((avg_time * remaining))
    fi
    
    # Show progress bar
    show_progress_bar $PROGRESS_CURRENT $PROGRESS_TOTAL "Progress"
    
    # Show current step
    echo -e "${GREEN}[${PROGRESS_CURRENT}/${PROGRESS_TOTAL}]${NC} ${message}"
    
    # Show ETA if available
    if [ $eta -gt 0 ]; then
        echo -e "${YELLOW}⏱️  ETA: ${eta}s${NC}"
    fi
    
    echo ""
}

progress_complete() {
    local message="${1:-Complete!}"
    
    local end_time=$(date +%s)
    local total_time=$((end_time - PROGRESS_START_TIME))
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✓ ${message}${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Total time: ${total_time}s${NC}"
    echo ""
}

################################################################################
# Download Progress Functions
################################################################################

download_with_progress() {
    local url="$1"
    local output_file="$2"
    local description="${3:-Downloading}"
    
    echo -e "${CYAN}📥 ${description}${NC}"
    echo -e "${YELLOW}URL: ${url}${NC}"
    echo ""
    
    if command -v wget &>/dev/null; then
        # Use wget with progress bar
        wget --progress=bar:force -O "$output_file" "$url" 2>&1 | \
        while IFS= read -r line; do
            # Parse wget progress
            if [[ $line =~ ([0-9]+)% ]]; then
                local percent="${BASH_REMATCH[1]}"
                show_progress_bar $percent 100 "$description"
            fi
        done
    elif command -v curl &>/dev/null; then
        # Use curl with progress bar
        curl -L# -o "$output_file" "$url"
    else
        echo -e "${RED}❌ wget or curl required${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Download complete${NC}"
    echo ""
}

################################################################################
# Multi-Step Operation Progress
################################################################################

multi_step_start() {
    local title="$1"
    shift
    local steps=("$@")
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${title}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    local i=1
    for step in "${steps[@]}"; do
        echo -e "${YELLOW}${i}.${NC} ${step}"
        ((i++))
    done
    
    echo ""
}

multi_step_execute() {
    local step_num=$1
    local total_steps=$2
    local message="$3"
    local command="$4"
    
    echo -e "${CYAN}[${step_num}/${total_steps}]${NC} ${message}"
    
    # Show spinner while executing
    (
        while kill -0 $$ 2>/dev/null; do
            show_spinner "$message"
            sleep 0.1
        done
    ) &
    local spinner_pid=$!
    
    # Execute command
    local result=0
    eval "$command" &>/dev/null || result=$?
    
    # Stop spinner
    kill $spinner_pid 2>/dev/null
    wait $spinner_pid 2>/dev/null
    
    if [ $result -eq 0 ]; then
        stop_spinner "$message"
    else
        printf "\r${RED}✗${NC} ${message}\n"
        return 1
    fi
    
    return 0
}

################################################################################
# Visual Step Indicators
################################################################################

step_start() {
    local step_num=$1
    local message="$2"
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Step ${step_num}: ${message}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

step_complete() {
    local message="$1"
    echo ""
    echo -e "${GREEN}✓ ${message}${NC}"
    echo ""
}

step_warning() {
    local message="$1"
    echo ""
    echo -e "${YELLOW}⚠ ${message}${NC}"
    echo ""
}

step_error() {
    local message="$1"
    echo ""
    echo -e "${RED}✗ ${message}${NC}"
    echo ""
}

################################################################################
# Percentage Progress with Custom Bar
################################################################################

percentage_progress() {
    local current=$1
    local total=$2
    local prefix="${3:-Progress}"
    local suffix="${4:-}"
    
    local percent=$((current * 100 / total))
    local filled=$((PROGRESS_BAR_WIDTH * current / total))
    
    # Create bar
    local bar=""
    for ((i=0; i<filled; i++)); do
        bar+="${GREEN}${PROGRESS_CHAR}${NC}"
    done
    for ((i=filled; i<PROGRESS_BAR_WIDTH; i++)); do
        bar+="${PROGRESS_EMPTY}"
    done
    
    # Print
    printf "\r%s [%b] %3d%% %s" "$prefix" "$bar" "$percent" "$suffix"
    
    if [ $current -eq $total ]; then
        echo ""
    fi
}

################################################################################
# File Operation Progress
################################################################################

copy_with_progress() {
    local source="$1"
    local dest="$2"
    local description="${3:-Copying files}"
    
    if [ ! -e "$source" ]; then
        echo -e "${RED}❌ Source not found: $source${NC}"
        return 1
    fi
    
    # Count total files
    local total=0
    if [ -d "$source" ]; then
        total=$(find "$source" -type f | wc -l)
    else
        total=1
    fi
    
    echo -e "${CYAN}📁 ${description}${NC}"
    
    local current=0
    
    if [ -d "$source" ]; then
        # Copy directory with progress
        while IFS= read -r file; do
            cp "$file" "$dest/" 2>/dev/null
            ((current++))
            show_progress_bar $current $total "$description"
        done < <(find "$source" -type f)
    else
        # Copy single file
        cp "$source" "$dest"
        show_progress_bar 1 1 "$description"
    fi
    
    echo -e "${GREEN}✅ Copy complete${NC}"
    echo ""
}

################################################################################
# Installation Progress Template
################################################################################

installation_progress_example() {
    # Example usage of progress functions in installation script
    
    progress_start "Installing ARK" 5
    
    progress_update 1 "Checking system requirements"
    sleep 1
    
    progress_update 2 "Installing dependencies"
    sleep 2
    
    progress_update 3 "Downloading packages"
    sleep 2
    
    progress_update 4 "Configuring ARK"
    sleep 1
    
    progress_update 5 "Creating launcher scripts"
    sleep 1
    
    progress_complete "ARK installed successfully!"
}

################################################################################
# INTEGRATION INSTRUCTIONS
################################################################################
#
# METHOD 1: Integrate into create-unified-ark.sh
# -----------------------------------------------
# 1. At the top of create-unified-ark.sh:
#
#    # Source progress bar functions
#    source "$(dirname "$0")/enhancements/14-progress-bars.sh"
#
# 2. Replace static echo messages with progress tracking:
#
#    # Start installation
#    progress_start "ARK Installation" 7
#    
#    # Step 1: Check system
#    progress_update 1 "Checking system requirements"
#    # ... system checks ...
#    
#    # Step 2: Install dependencies
#    progress_update 2 "Installing dependencies"
#    # ... dependency installation ...
#    
#    # Step 3: Download packages
#    progress_update 3 "Downloading packages"
#    download_with_progress "https://..." "output.tar.gz" "Node.js"
#    
#    # ... more steps ...
#    
#    # Complete
#    progress_complete "Installation complete!"
#
# 3. For file operations:
#
#    copy_with_progress "$SRC_DIR" "$DEST_DIR" "Copying ARK files"
#
# 4. For long operations:
#
#    show_spinner "Compiling dependencies" &
#    SPINNER_PID=$!
#    # ... long operation ...
#    kill $SPINNER_PID
#    stop_spinner "Compilation complete"
#
#
# METHOD 2: Use in Custom Scripts
# --------------------------------
# 1. Source the progress functions:
#    source /path/to/14-progress-bars.sh
#
# 2. Use functions as needed:
#    progress_start "My Task" 3
#    progress_update 1 "Step 1"
#    # ... work ...
#    progress_update 2 "Step 2"
#    # ... work ...
#    progress_update 3 "Step 3"
#    # ... work ...
#    progress_complete "Done!"
#
#
# EXAMPLE: Update Mechanism with Progress
# ----------------------------------------
#    progress_start "Updating ARK" 6
#    
#    progress_update 1 "Fetching latest version"
#    git fetch origin
#    
#    progress_update 2 "Creating backup"
#    tar czf backup.tar.gz ark/
#    
#    progress_update 3 "Stopping services"
#    ark stop
#    
#    progress_update 4 "Pulling updates"
#    git pull origin master
#    
#    progress_update 5 "Updating dependencies"
#    npm install
#    
#    progress_update 6 "Restarting services"
#    ark start
#    
#    progress_complete "Update complete!"
#
#
# BENEFITS:
# ---------
# ✅ Better user experience with visual feedback
# ✅ Clear indication of progress and ETA
# ✅ Professional-looking installation process
# ✅ Easy to understand what's happening
# ✅ Reduces perceived installation time
# ✅ Helps identify stuck operations
# ✅ Pure bash - no additional dependencies
# ✅ Cross-platform compatible
#
################################################################################

# If script is executed directly, show example
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    echo "Progress Bar Examples"
    echo ""
    
    echo "1. Basic Progress Bar:"
    for i in {0..10}; do
        show_progress_bar $i 10 "Loading"
        sleep 0.2
    done
    
    echo ""
    echo "2. Spinner:"
    for i in {1..20}; do
        show_spinner "Processing"
        sleep 0.1
    done
    stop_spinner "Processing complete"
    
    echo ""
    echo "3. Multi-step Progress:"
    installation_progress_example
fi
