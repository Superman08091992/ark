#!/bin/bash
# ARK Portable Node Import Script
# Loads ARK Docker image from portable package

set -e

echo "📥 ARK Portable Node Import"
echo "============================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

IMAGE_FILE="ark-node.tar.gz"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo ""
    echo "Install Docker with:"
    echo "  sudo apt update"
    echo "  sudo apt install -y docker.io docker-compose"
    echo "  sudo systemctl enable docker --now"
    echo "  sudo usermod -aG docker \$USER"
    echo "  newgrp docker"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo ""
    echo "Install with: sudo apt install -y docker-compose"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"
echo ""

# Check if image file exists
if [ ! -f "$IMAGE_FILE" ]; then
    echo -e "${RED}❌ Image file not found: $IMAGE_FILE${NC}"
    echo ""
    echo "Make sure you're in the correct directory with $IMAGE_FILE"
    exit 1
fi

echo -e "${GREEN}✅ Image file found${NC}"
echo ""

# Get file size
SIZE=$(du -h $IMAGE_FILE | cut -f1)
echo "📦 Image size: $SIZE"
echo ""

# Load Docker image
echo "📥 Loading Docker image (this may take a few minutes)..."
docker load < $IMAGE_FILE
echo -e "${GREEN}✅ Image loaded successfully${NC}"
echo ""

# Create required directories
echo "📁 Creating required directories..."
mkdir -p data logs keys agent_logs
chmod 755 data logs keys agent_logs
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    if [ -f .env.production ]; then
        echo "📝 Creating .env from .env.production..."
        cp .env.production .env
        echo -e "${GREEN}✅ .env file created${NC}"
    else
        echo -e "${YELLOW}⚠️  No .env file found${NC}"
        echo "Please create .env file before starting services"
    fi
fi
echo ""

# Display loaded images
echo "🖼️  Loaded images:"
docker images | grep -E "REPOSITORY|1true/ark"
echo ""

echo -e "${GREEN}🎉 Import complete!${NC}"
echo ""
echo "Next steps:"
echo "1. (Optional) Edit .env for configuration"
echo "2. Start services: docker-compose up -d"
echo "3. Check status: docker-compose ps"
echo "4. View logs: docker-compose logs -f"
echo ""
echo "Access URLs:"
echo "- Dashboard: http://localhost:4173/dashboard-demo.html"
echo "- Backend API: http://localhost:8101"
echo "- API Docs: http://localhost:8101/docs"
echo ""
