#!/bin/bash
# ARK Portable USB Node Export Script
# Creates a portable Docker image for offline deployment

set -e

echo "📦 ARK Portable Node Export"
echo "============================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
IMAGE_NAME="1true/ark-backend"
IMAGE_TAG="latest"
EXPORT_DIR="./ark-portable"
EXPORT_FILE="ark-node.tar.gz"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Build the image first
echo "🏗️  Building Docker image..."
docker-compose build ark-backend
echo -e "${GREEN}✅ Image built${NC}"
echo ""

# Tag the image
echo "🏷️  Tagging image as ${IMAGE_NAME}:${IMAGE_TAG}..."
docker tag ark-backend:latest ${IMAGE_NAME}:${IMAGE_TAG}
echo -e "${GREEN}✅ Image tagged${NC}"
echo ""

# Create export directory
mkdir -p ${EXPORT_DIR}

# Export Docker image
echo "💾 Exporting Docker image (this may take a few minutes)..."
docker save ${IMAGE_NAME}:${IMAGE_TAG} | gzip > ${EXPORT_DIR}/${EXPORT_FILE}
echo -e "${GREEN}✅ Image exported${NC}"
echo ""

# Copy necessary files
echo "📋 Copying deployment files..."
cp docker-compose.yml ${EXPORT_DIR}/
cp .env.production ${EXPORT_DIR}/.env
cp docker-deploy.sh ${EXPORT_DIR}/
cp docker-import.sh ${EXPORT_DIR}/
chmod +x ${EXPORT_DIR}/*.sh
echo -e "${GREEN}✅ Files copied${NC}"
echo ""

# Create README for portable deployment
cat > ${EXPORT_DIR}/README.txt << 'EOF'
ARK Portable Node - Deployment Instructions
============================================

This package contains a portable ARK node that can be deployed on any
Linux system with Docker installed.

REQUIREMENTS:
- Docker 20.0 or higher
- Docker Compose 1.29 or higher
- 2GB RAM minimum
- 1GB disk space
- Linux kernel 3.10+

QUICK START:
1. Copy this entire folder to your target system
2. Run: ./docker-import.sh
3. Access dashboard at: http://localhost:4173/dashboard-demo.html

DETAILED STEPS:
1. Install Docker (if not installed):
   sudo apt update
   sudo apt install -y docker.io docker-compose
   sudo systemctl enable docker --now
   sudo usermod -aG docker $USER
   newgrp docker

2. Import the ARK image:
   ./docker-import.sh

3. (Optional) Edit .env file to customize configuration

4. Start services:
   docker-compose up -d

5. Check status:
   docker-compose ps
   docker-compose logs -f

6. Access:
   - Dashboard: http://localhost:4173/dashboard-demo.html
   - API: http://localhost:8101
   - Docs: http://localhost:8101/docs

MANAGEMENT:
- Start:   docker-compose up -d
- Stop:    docker-compose down
- Restart: docker-compose restart
- Logs:    docker-compose logs -f
- Shell:   docker exec -it ark-backend bash

PORTS USED:
- 8101: Backend API + WebSocket
- 4173: Frontend Dashboard
- 6379: Redis (internal)
- 8104: Federation mesh

SUPPORT:
- GitHub: https://github.com/Superman08091992/ark
- Docs: See QUICKSTART.md in repository

EOF

echo -e "${GREEN}✅ README created${NC}"
echo ""

# Calculate size
SIZE=$(du -h ${EXPORT_DIR}/${EXPORT_FILE} | cut -f1)

# Display summary
echo "📊 Export Summary:"
echo "=================="
echo -e "${CYAN}Export directory:${NC} ${EXPORT_DIR}"
echo -e "${CYAN}Image file:${NC}       ${EXPORT_FILE}"
echo -e "${CYAN}Size:${NC}             ${SIZE}"
echo -e "${CYAN}Image:${NC}            ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""

# List contents
echo "📦 Package contents:"
ls -lh ${EXPORT_DIR}
echo ""

echo -e "${GREEN}🎉 Export complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Copy ${EXPORT_DIR} to USB drive or target system"
echo "2. On target system, run: ./docker-import.sh"
echo "3. Start services: docker-compose up -d"
echo ""
echo "To create multi-arch image (ARM + x86):"
echo "  docker buildx create --use"
echo "  docker buildx build --platform linux/amd64,linux/arm64 -t ${IMAGE_NAME}:${IMAGE_TAG} ."
echo ""
