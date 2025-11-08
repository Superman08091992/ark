#!/bin/bash
# Quick start script for ngrok tunnel to ARK
# Usage: ./start-ngrok.sh [port]

PORT=${1:-4321}
CONFIG_FILE="ngrok-config.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      ARK ngrok Tunnel Starter        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}❌ ngrok is not installed!${NC}"
    echo ""
    echo -e "${YELLOW}Install ngrok:${NC}"
    echo "  macOS:   brew install ngrok"
    echo "  Linux:   curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null"
    echo "           echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list"
    echo "           sudo apt update && sudo apt install ngrok"
    echo "  Windows: choco install ngrok"
    echo ""
    echo "  Or download from: https://ngrok.com/download"
    exit 1
fi

# Check if authtoken is configured
if ! ngrok config check &> /dev/null; then
    echo -e "${YELLOW}⚠️  ngrok authtoken not configured${NC}"
    echo ""
    echo -e "${BLUE}Steps to configure:${NC}"
    echo "  1. Sign up at https://dashboard.ngrok.com/signup"
    echo "  2. Copy your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "  3. Run: ngrok config add-authtoken YOUR_TOKEN_HERE"
    echo ""
    read -p "Press Enter after configuring authtoken, or Ctrl+C to exit..."
fi

# Check if development server is running
if ! curl -s http://localhost:$PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  No server detected on port $PORT${NC}"
    echo ""
    echo -e "${BLUE}Start your development server first:${NC}"
    echo "  npm run dev"
    echo ""
    read -p "Press Enter when server is running, or Ctrl+C to exit..."
fi

echo -e "${GREEN}✓ Starting ngrok tunnel on port $PORT...${NC}"
echo ""

# Start ngrok with custom config if exists, otherwise use simple command
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${BLUE}Using config: $CONFIG_FILE${NC}"
    ngrok start --config="$CONFIG_FILE" ark-web
else
    echo -e "${BLUE}Using default configuration${NC}"
    echo -e "${YELLOW}💡 Tip: Create $CONFIG_FILE for advanced options${NC}"
    echo ""
    ngrok http $PORT --log=stdout
fi

# Note: This script will keep running until you press Ctrl+C
