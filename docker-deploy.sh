#!/bin/bash
# ARK Docker Deployment Script
# Portable deployment for any Linux/Pi host

set -e

echo "🚀 ARK Docker Deployment"
echo "========================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo ""
    echo "Install Docker with:"
    echo "  sudo apt update"
    echo "  sudo apt install -y docker.io docker-compose"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo ""
    echo "Install Docker Compose with:"
    echo "  sudo apt install -y docker-compose"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"
echo ""

# Check if user is in docker group
if ! groups | grep -q docker; then
    echo -e "${YELLOW}⚠️  You are not in the docker group${NC}"
    echo "Add yourself with:"
    echo "  sudo usermod -aG docker \$USER"
    echo "  newgrp docker"
    echo ""
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found, creating from .env.production${NC}"
    cp .env.production .env
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo -e "${CYAN}📝 Please edit .env to customize your configuration${NC}"
    echo ""
fi

# Create required directories
echo "📁 Creating required directories..."
mkdir -p data logs keys agent_logs
chmod 755 data logs keys agent_logs
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Pull latest changes
echo "📥 Checking for updates..."
git fetch origin master
BEHIND=$(git rev-list HEAD..origin/master --count)
if [ "$BEHIND" -gt 0 ]; then
    echo -e "${CYAN}📦 $BEHIND commits behind, pulling updates...${NC}"
    git pull origin master
    echo -e "${GREEN}✅ Updated to latest version${NC}"
else
    echo -e "${GREEN}✅ Already up to date${NC}"
fi
echo ""

# Build Docker images
echo "🏗️  Building Docker images..."
docker-compose build
echo -e "${GREEN}✅ Images built successfully${NC}"
echo ""

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down
echo -e "${GREEN}✅ Containers stopped${NC}"
echo ""

# Start containers
echo "🚀 Starting ARK services..."
docker-compose up -d
echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
echo "=================="
docker-compose ps
echo ""

# Check backend health
echo "🔍 Checking backend health..."
if curl -s http://localhost:8101/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API is healthy${NC}"
else
    echo -e "${RED}❌ Backend API is not responding${NC}"
    echo "Check logs with: docker-compose logs ark-backend"
fi
echo ""

# Check Redis
echo "🔍 Checking Redis..."
if docker exec ark-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is healthy${NC}"
else
    echo -e "${RED}❌ Redis is not responding${NC}"
fi
echo ""

# Display access URLs
echo "🌐 Access URLs:"
echo "==============="
echo -e "${CYAN}Backend API:${NC}      http://localhost:8101"
echo -e "${CYAN}Dashboard:${NC}        http://localhost:4173/dashboard-demo.html"
echo -e "${CYAN}API Docs:${NC}         http://localhost:8101/docs"
echo -e "${CYAN}WebSocket (Fed):${NC}  ws://localhost:8101/ws/federation"
echo -e "${CYAN}WebSocket (Mem):${NC}  ws://localhost:8101/ws/memory"
echo ""

# Display useful commands
echo "📋 Useful Commands:"
echo "==================="
echo "View logs:         docker-compose logs -f"
echo "View backend logs: docker-compose logs -f ark-backend"
echo "Stop services:     docker-compose down"
echo "Restart services:  docker-compose restart"
echo "Shell access:      docker exec -it ark-backend bash"
echo ""

echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env for production settings"
echo "2. Access dashboard at http://localhost:4173/dashboard-demo.html"
echo "3. Check logs: docker-compose logs -f"
echo ""
