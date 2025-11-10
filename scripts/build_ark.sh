#!/usr/bin/env bash
#
# ARK Multi-Platform Docker Build Script
#
# Builds ARK container image with multi-architecture support using buildx.
# Supports parameterized Python and Redis versions.
#
# Usage:
#   ./scripts/build_ark.sh [OPTIONS]
#
# Options:
#   --python-version VERSION    Python version (default: 3.12)
#   --redis-version VERSION     Redis version (default: 7)
#   --tag TAG                   Image tag (default: ark:arch)
#   --platform PLATFORMS        Target platforms (default: linux/amd64,linux/arm64)
#   --push                      Push to registry after build
#   --no-cache                  Build without using cache
#   --help                      Show this help message
#
# Examples:
#   ./scripts/build_ark.sh
#   ./scripts/build_ark.sh --python-version 3.11 --redis-version 6
#   ./scripts/build_ark.sh --tag ark:v1.0.0 --push
#   ./scripts/build_ark.sh --platform linux/amd64 --no-cache

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PYTHON_VERSION="3.12"
REDIS_VERSION="7"
IMAGE_TAG="ark:arch"
PLATFORMS="linux/amd64,linux/arm64"
PUSH_FLAG=""
CACHE_FLAG=""

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Log function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" >&2
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $*"
}

# Show banner
log "=========================================="
log "    ARK Multi-Platform Docker Build"
log "=========================================="
log ""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --python-version)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        --redis-version)
            REDIS_VERSION="$2"
            shift 2
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --platform)
            PLATFORMS="$2"
            shift 2
            ;;
        --push)
            PUSH_FLAG="--push"
            shift
            ;;
        --no-cache)
            CACHE_FLAG="--no-cache"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --python-version VERSION    Python version (default: 3.12)"
            echo "  --redis-version VERSION     Redis version (default: 7)"
            echo "  --tag TAG                   Image tag (default: ark:arch)"
            echo "  --platform PLATFORMS        Target platforms (default: linux/amd64,linux/arm64)"
            echo "  --push                      Push to registry after build"
            echo "  --no-cache                  Build without using cache"
            echo "  --help, -h                  Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 --python-version 3.11 --redis-version 6"
            echo "  $0 --tag ark:v1.0.0 --push"
            echo "  $0 --platform linux/amd64 --no-cache"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Display build configuration
log_info "Build Configuration:"
log_info "  Python Version: $PYTHON_VERSION"
log_info "  Redis Version: $REDIS_VERSION"
log_info "  Image Tag: $IMAGE_TAG"
log_info "  Platforms: $PLATFORMS"
log_info "  Push to Registry: ${PUSH_FLAG:-disabled}"
log_info "  Cache: ${CACHE_FLAG:-enabled}"
log ""

# Check prerequisites
log_info "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    log_error "docker not found. Please install Docker."
    exit 1
fi
log "  ✓ Docker available"

# Check buildx
if ! docker buildx version &> /dev/null; then
    log_error "docker buildx not available. Please install or enable buildx."
    exit 1
fi
log "  ✓ Docker buildx available"

# Check Dockerfile exists
DOCKERFILE="$PROJECT_ROOT/Dockerfile.arch"
if [[ ! -f "$DOCKERFILE" ]]; then
    log_error "Dockerfile not found: $DOCKERFILE"
    exit 1
fi
log "  ✓ Dockerfile.arch found"

log ""
log_info "Prerequisites check passed"
log ""

# Create buildx builder if not exists
BUILDER_NAME="ark-builder"
if ! docker buildx inspect "$BUILDER_NAME" &> /dev/null; then
    log_info "Creating buildx builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" --use
    log "  ✓ Builder created"
else
    log_info "Using existing buildx builder: $BUILDER_NAME"
    docker buildx use "$BUILDER_NAME"
fi

# Bootstrap builder
log_info "Bootstrapping builder..."
docker buildx inspect --bootstrap
log "  ✓ Builder ready"
log ""

# Build command
BUILD_CMD="docker buildx build \
    --platform $PLATFORMS \
    -t $IMAGE_TAG \
    -f $DOCKERFILE \
    --build-arg PYTHON_VERSION=$PYTHON_VERSION \
    --build-arg REDIS_VERSION=$REDIS_VERSION \
    $CACHE_FLAG \
    $PUSH_FLAG \
    $PROJECT_ROOT"

log_info "Starting build..."
log_info "Command: $BUILD_CMD"
log ""

START_TIME=$(date +%s)

# Execute build
if eval "$BUILD_CMD"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    log ""
    log "=========================================="
    log "✅ Build completed successfully!"
    log "=========================================="
    log ""
    log_info "Image: $IMAGE_TAG"
    log_info "Platforms: $PLATFORMS"
    log_info "Python Version: $PYTHON_VERSION"
    log_info "Redis Version: $REDIS_VERSION"
    log_info "Duration: ${DURATION}s"
    log ""
    
    if [[ -z "$PUSH_FLAG" ]]; then
        log_info "Image built locally. To load for local use:"
        log_info "  docker buildx build --platform linux/amd64 -t $IMAGE_TAG --load $PROJECT_ROOT"
        log ""
        log_info "To push to registry:"
        log_info "  $0 --tag $IMAGE_TAG --push"
    else
        log_info "Image pushed to registry successfully"
    fi
    
    log ""
    log_info "Next steps:"
    log_info "  1. Test image: docker run --rm $IMAGE_TAG --version"
    log_info "  2. Deploy with docker-compose: docker-compose up -d"
    log_info "  3. Verify health: curl http://localhost:9090/healthz"
    log ""
    
    exit 0
else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    log ""
    log "=========================================="
    log_error "❌ Build FAILED"
    log "=========================================="
    log ""
    log_error "Duration: ${DURATION}s"
    log ""
    log_error "Troubleshooting:"
    log_error "  1. Check Dockerfile syntax: docker build --check $DOCKERFILE"
    log_error "  2. Verify build context: ls -la $PROJECT_ROOT"
    log_error "  3. Check Docker daemon: docker ps"
    log_error "  4. Review buildx builders: docker buildx ls"
    log ""
    
    exit 1
fi
