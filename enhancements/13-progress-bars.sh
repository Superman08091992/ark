#!/bin/bash
################################################################################
# ARK Enhancement #13: Progress Bars and Visual Feedback
################################################################################
#
# WHAT THIS DOES:
# ---------------
# Adds visual progress indicators and animated feedback during installation
# and long-running operations. Makes the installation experience more engaging
# and helps users understand what's happening.
#
# FEATURES:
# ---------
# ✅ Animated progress bars with percentage
# ✅ Spinner animations for indefinite operations
# ✅ Multi-step progress tracking
# ✅ Download progress indicators
# ✅ Color-coded status messages
# ✅ Estimated time remaining
# ✅ Success/failure animations
# ✅ Customizable bar styles
# ✅ Works in any terminal
# ✅ No external dependencies
#
# USAGE:
# ------
# Source this file in your scripts, then use the functions:
#
#   source progress-bars.sh
#   
#   progress_bar 50 100 "Installing"      # Show 50% progress
#   spinner_start "Downloading..."        # Start spinner
#   spinner_stop                          # Stop spinner
#   multi_step_start 5                    # Start multi-step (5 steps)
#   multi_step_next "Step 1"              # Advance to next step
#   multi_step_complete                   # Complete all steps
#
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
GRAY='\033[0;90m'
NC='\033[0m'

# Unicode characters (with ASCII fallbacks)
if locale | grep -q "UTF-8"; then
    CHAR_BLOCK="█"
    CHAR_HALF="▌"
    CHAR_EMPTY="░"
    CHAR_TICK="✓"
    CHAR_CROSS="✗"
    CHAR_ARROW="➜"
    CHAR_SPINNER=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
else
    CHAR_BLOCK="#"
    CHAR_HALF="|"
    CHAR_EMPTY="-"
    CHAR_TICK="+"
    CHAR_CROSS="x"
    CHAR_ARROW=">"
    CHAR_SPINNER=("-" "\\" "|" "/")
fi

# Progress state
SPINNER_PID=""
MULTI_STEP_TOTAL=0
MULTI_STEP_CURRENT=0

################################################################################
# Simple Progress Bar
################################################################################

progress_bar() {
    local current=$1
    local total=$2
    local message="${3:-Progress}"
    local width=40
    
    # Calculate percentage
    local percent=$((current * 100 / total))
    local filled=$((width * current / total))
    local empty=$((width - filled))
    
    # Build progress bar
    local bar=""
    for ((i=0; i<filled; i++)); do
        bar+="$CHAR_BLOCK"
    done
    for ((i=0; i<empty; i++)); do
        bar+="$CHAR_EMPTY"
    done
    
    # Print with color
    if [ $percent -lt 50 ]; then
        local color=$YELLOW
    elif [ $percent -lt 100 ]; then
        local color=$BLUE
    else
        local color=$GREEN
    fi
    
    printf "\r${color}${message}: [${bar}] ${percent}%%${NC}"
    
    # New line if complete
    if [ $percent -eq 100 ]; then
        echo ""
    fi
}

################################################################################
# Advanced Progress Bar with ETA
################################################################################

progress_bar_advanced() {
    local current=$1
    local total=$2
    local message="${3:-Progress}"
    local start_time=${4:-$(date +%s)}
    local width=50
    
    # Calculate metrics
    local percent=$((current * 100 / total))
    local filled=$((width * current / total))
    local empty=$((width - filled))
    
    # Calculate ETA
    local elapsed=$(($(date +%s) - start_time))
    local rate=0
    [ $current -gt 0 ] && rate=$((elapsed / current))
    local remaining=$((rate * (total - current)))
    
    # Format time
    local eta_str="--:--"
    if [ $remaining -gt 0 ]; then
        local eta_min=$((remaining / 60))
        local eta_sec=$((remaining % 60))
        eta_str=$(printf "%02d:%02d" $eta_min $eta_sec)
    fi
    
    # Build bar
    local bar=""
    for ((i=0; i<filled; i++)); do
        bar+="$CHAR_BLOCK"
    done
    for ((i=0; i<empty; i++)); do
        bar+="$CHAR_EMPTY"
    done
    
    # Color based on progress
    if [ $percent -lt 30 ]; then
        local color=$RED
    elif [ $percent -lt 70 ]; then
        local color=$YELLOW
    elif [ $percent -lt 100 ]; then
        local color=$BLUE
    else
        local color=$GREEN
    fi
    
    # Print
    printf "\r${color}%-20s [%s] %3d%% ETA: %s${NC}" "$message" "$bar" "$percent" "$eta_str"
    
    if [ $percent -eq 100 ]; then
        echo ""
    fi
}

################################################################################
# Spinner Animation
################################################################################

spinner_animate() {
    local message="$1"
    local spinner_chars=("${CHAR_SPINNER[@]}")
    local i=0
    
    while true; do
        printf "\r${BLUE}${spinner_chars[i]} ${message}${NC}"
        i=$(( (i + 1) % ${#spinner_chars[@]} ))
        sleep 0.1
    done
}

spinner_start() {
    local message="${1:-Working...}"
    spinner_animate "$message" &
    SPINNER_PID=$!
    
    # Disable terminal cursor
    tput civis 2>/dev/null || true
}

spinner_stop() {
    if [ -n "$SPINNER_PID" ]; then
        kill $SPINNER_PID 2>/dev/null || true
        wait $SPINNER_PID 2>/dev/null || true
        SPINNER_PID=""
    fi
    
    # Re-enable terminal cursor
    tput cnorm 2>/dev/null || true
    
    # Clear line
    printf "\r%60s\r" " "
}

spinner_stop_success() {
    spinner_stop
    echo -e "${GREEN}${CHAR_TICK} ${1:-Done}${NC}"
}

spinner_stop_failure() {
    spinner_stop
    echo -e "${RED}${CHAR_CROSS} ${1:-Failed}${NC}"
}

################################################################################
# Multi-Step Progress
################################################################################

multi_step_start() {
    MULTI_STEP_TOTAL=$1
    MULTI_STEP_CURRENT=0
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Installation Progress (0/${MULTI_STEP_TOTAL})${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

multi_step_next() {
    local step_name="$1"
    MULTI_STEP_CURRENT=$((MULTI_STEP_CURRENT + 1))
    
    local percent=$((MULTI_STEP_CURRENT * 100 / MULTI_STEP_TOTAL))
    
    echo ""
    echo -e "${CYAN}${CHAR_ARROW} Step ${MULTI_STEP_CURRENT}/${MULTI_STEP_TOTAL}: ${step_name}${NC}"
    
    # Show progress bar
    progress_bar $MULTI_STEP_CURRENT $MULTI_STEP_TOTAL "Overall"
    echo ""
}

multi_step_complete() {
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ${CHAR_TICK} All steps completed successfully!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

################################################################################
# Download Progress (wrapper for curl/wget)
################################################################################

download_with_progress() {
    local url="$1"
    local output="$2"
    local name="${3:-Download}"
    
    echo -e "${BLUE}Downloading: ${name}${NC}"
    
    if command -v curl &>/dev/null; then
        curl -L --progress-bar "$url" -o "$output"
    elif command -v wget &>/dev/null; then
        wget --progress=bar:force "$url" -O "$output" 2>&1 | \
            grep --line-buffered "%" | \
            sed -u -e "s,\.,,g" | \
            awk '{print "\r" $2 " " $4}'
    else
        echo -e "${YELLOW}⚠️  No curl or wget available, downloading without progress...${NC}"
        # Fallback without progress
        if command -v python3 &>/dev/null; then
            python3 -c "import urllib.request; urllib.request.urlretrieve('$url', '$output')"
        else
            echo -e "${RED}❌ Cannot download: no suitable tool found${NC}"
            return 1
        fi
    fi
    
    echo -e "${GREEN}${CHAR_TICK} Download complete${NC}"
}

################################################################################
# Task Progress (for operations with known steps)
################################################################################

task_start() {
    local task_name="$1"
    echo -ne "${BLUE}${task_name}...${NC}"
}

task_success() {
    echo -e "\r${GREEN}${CHAR_TICK} ${1}${NC}"
}

task_failure() {
    echo -e "\r${RED}${CHAR_CROSS} ${1}${NC}"
}

task_warning() {
    echo -e "\r${YELLOW}⚠️  ${1}${NC}"
}

task_info() {
    echo -e "${GRAY}  ℹ️  ${1}${NC}"
}

################################################################################
# Loading Animation
################################################################################

loading_dots() {
    local message="$1"
    local duration=${2:-5}
    local start_time=$(date +%s)
    
    while [ $(($(date +%s) - start_time)) -lt $duration ]; do
        for dots in "" "." ".." "..."; do
            printf "\r${BLUE}${message}${dots}   ${NC}"
            sleep 0.3
        done
    done
    
    printf "\r%60s\r" " "
}

################################################################################
# Success/Failure Banners
################################################################################

show_success_banner() {
    local message="${1:-Success!}"
    
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}║  ${CHAR_TICK}  ${message}$(printf '%*s' $((52 - ${#message})))║${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

show_failure_banner() {
    local message="${1:-Failed!}"
    
    echo ""
    echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}║  ${CHAR_CROSS}  ${message}$(printf '%*s' $((52 - ${#message})))║${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

################################################################################
# Demo (when run directly)
################################################################################

demo_progress_bars() {
    echo "=== Progress Bar Demo ==="
    echo ""
    
    # Simple progress bar
    echo "1. Simple Progress Bar:"
    for i in {0..100..10}; do
        progress_bar $i 100 "Installing"
        sleep 0.2
    done
    
    sleep 1
    
    # Spinner
    echo ""
    echo "2. Spinner Animation:"
    spinner_start "Downloading packages..."
    sleep 3
    spinner_stop_success "Packages downloaded"
    
    sleep 1
    
    # Multi-step
    echo ""
    echo "3. Multi-Step Progress:"
    multi_step_start 4
    
    multi_step_next "Installing dependencies"
    sleep 1
    
    multi_step_next "Configuring environment"
    sleep 1
    
    multi_step_next "Building application"
    sleep 1
    
    multi_step_next "Running tests"
    sleep 1
    
    multi_step_complete
    
    # Task progress
    echo ""
    echo "4. Task Progress:"
    task_start "Checking system requirements"
    sleep 1
    task_success "System requirements met"
    
    task_start "Creating directories"
    sleep 1
    task_success "Directories created"
    
    task_start "Installing packages"
    sleep 1
    task_warning "Some packages already installed"
    
    # Success banner
    show_success_banner "Installation Complete!"
}

################################################################################
# Main (demo mode)
################################################################################

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    # Script is being executed directly (not sourced)
    
    case "${1:-demo}" in
        demo)
            demo_progress_bars
            ;;
        test-bar)
            for i in {0..100..5}; do
                progress_bar $i 100 "Testing"
                sleep 0.1
            done
            ;;
        test-spinner)
            spinner_start "Testing spinner..."
            sleep 5
            spinner_stop_success "Spinner test complete"
            ;;
        test-multi)
            multi_step_start 3
            multi_step_next "First step"
            sleep 1
            multi_step_next "Second step"
            sleep 1
            multi_step_next "Third step"
            sleep 1
            multi_step_complete
            ;;
        *)
            echo "ARK Progress Bars - Visual Feedback System"
            echo ""
            echo "USAGE:"
            echo "  source progress-bars.sh     # Use in your scripts"
            echo "  ./progress-bars.sh demo     # See demo"
            echo "  ./progress-bars.sh test-*   # Test specific feature"
            echo ""
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
#    # Source progress bar functions
#    source "$(dirname "$0")/enhancements/13-progress-bars.sh"
#
# 2. Use multi-step progress:
#
#    multi_step_start 8  # Total number of major steps
#    
#    multi_step_next "Detecting platform"
#    # ... detection code ...
#    
#    multi_step_next "Installing dependencies"
#    spinner_start "Installing Node.js..."
#    # ... installation code ...
#    spinner_stop_success "Node.js installed"
#    
#    # ... more steps ...
#    
#    multi_step_complete
#
# 3. For file downloads:
#
#    download_with_progress "$URL" "$OUTPUT" "Node.js"
#
# 4. For individual tasks:
#
#    task_start "Creating directories"
#    mkdir -p "$INSTALL_DIR/bin"
#    task_success "Directories created"
#
# 5. At the end:
#
#    show_success_banner "ARK Installation Complete!"
#
#
# METHOD 2: Use in Your Own Scripts
# ----------------------------------
# 1. Source the file:
#    source /path/to/13-progress-bars.sh
#
# 2. Use any of the functions:
#    progress_bar 50 100 "Processing"
#    spinner_start "Working..."
#    # ... your code ...
#    spinner_stop_success "Done!"
#
#
# AVAILABLE FUNCTIONS:
# --------------------
# • progress_bar <current> <total> [message]
# • progress_bar_advanced <current> <total> [message] [start_time]
# • spinner_start [message]
# • spinner_stop
# • spinner_stop_success [message]
# • spinner_stop_failure [message]
# • multi_step_start <total_steps>
# • multi_step_next <step_name>
# • multi_step_complete
# • download_with_progress <url> <output> [name]
# • task_start <message>
# • task_success <message>
# • task_failure <message>
# • task_warning <message>
# • task_info <message>
# • loading_dots <message> [duration]
# • show_success_banner [message]
# • show_failure_banner [message]
#
#
# BENEFITS:
# ---------
# ✅ Better user experience during installation
# ✅ Clear visual feedback on progress
# ✅ Reduces perceived wait time
# ✅ Professional appearance
# ✅ Easy to integrate
# ✅ No external dependencies
# ✅ Works in any terminal
# ✅ Graceful fallbacks for simple terminals
#
################################################################################
