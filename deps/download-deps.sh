#!/bin/bash
##############################################################################
# Download ARK Dependencies
# Downloads Node.js and Redis binaries to bundle in repository
##############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║              ARK Dependency Downloader                                ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Versions
NODE_VERSION="20.10.0"
REDIS_VERSION="7.2.4"

# Detect architecture
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        NODE_ARCH="x64"
        ;;
    aarch64|arm64)
        NODE_ARCH="arm64"
        ;;
    *)
        echo "❌ Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

echo "📋 Target architecture: $ARCH ($NODE_ARCH)"
echo ""

# Download Node.js
echo "1️⃣  Downloading Node.js v$NODE_VERSION..."
NODE_FILE="node-v${NODE_VERSION}-linux-${NODE_ARCH}.tar.xz"
NODE_URL="https://nodejs.org/dist/v${NODE_VERSION}/${NODE_FILE}"

if [ ! -f "node/$NODE_FILE" ]; then
    wget -q --show-progress "$NODE_URL" -O "node/$NODE_FILE"
    echo "✅ Node.js downloaded"
else
    echo "✅ Node.js already downloaded"
fi

# Extract Node.js
echo "   Extracting..."
cd node
tar -xf "$NODE_FILE"
mv "node-v${NODE_VERSION}-linux-${NODE_ARCH}" nodejs
rm "$NODE_FILE"
cd ..

NODE_SIZE=$(du -sh node/nodejs | cut -f1)
echo "   Size: $NODE_SIZE"

# Download Redis
echo ""
echo "2️⃣  Downloading Redis v$REDIS_VERSION..."
REDIS_FILE="redis-${REDIS_VERSION}.tar.gz"
REDIS_URL="https://download.redis.io/releases/${REDIS_FILE}"

if [ ! -f "redis/$REDIS_FILE" ]; then
    wget -q --show-progress "$REDIS_URL" -O "redis/$REDIS_FILE"
    echo "✅ Redis downloaded"
else
    echo "✅ Redis already downloaded"
fi

# Extract and build Redis
echo "   Extracting and building..."
cd redis
tar -xzf "$REDIS_FILE"
cd "redis-${REDIS_VERSION}"

# Build Redis (statically linked for portability)
make BUILD_TLS=yes MALLOC=libc -j$(nproc) 2>&1 | grep -E "(CC|LINK|Done)" || true

# Copy binaries
mkdir -p ../bin
cp src/redis-server ../bin/
cp src/redis-cli ../bin/
cp src/redis-benchmark ../bin/

cd ../..

# Cleanup
rm -rf "redis/redis-${REDIS_VERSION}"
rm -f "redis/$REDIS_FILE"

REDIS_SIZE=$(du -sh redis/bin | cut -f1)
echo "   Size: $REDIS_SIZE"

# Create version info
cat > VERSIONS.txt << EOF
ARK Dependencies

Downloaded: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Architecture: $ARCH

Node.js: v$NODE_VERSION
  Path: deps/node/nodejs/
  Size: $NODE_SIZE
  Binary: bin/node
  NPM: bin/npm

Redis: v$REDIS_VERSION
  Path: deps/redis/bin/
  Size: $REDIS_SIZE
  Binaries: redis-server, redis-cli, redis-benchmark

Total size: $(du -sh . | cut -f1)

Ollama and AI models are NOT included (too large for repo).
Use one of these options:
  1. Install via package manager: curl -fsSL https://ollama.ai/install.sh | sh
  2. Download from releases: github.com/Superman08091992/ark/releases
  3. Let installer download automatically during installation
EOF

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║              ✅ DEPENDENCIES DOWNLOADED! ✅                          ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Node.js v$NODE_VERSION:  $NODE_SIZE"
echo "📦 Redis v$REDIS_VERSION:   $REDIS_SIZE"
echo "📊 Total size:              $(du -sh . | cut -f1)"
echo ""
echo "📝 Version info saved to: deps/VERSIONS.txt"
echo ""
echo "🚀 Next steps:"
echo "   1. Commit deps/ to repository"
echo "   2. Modify install-ark-host.sh to use bundled deps"
echo "   3. Users can git clone and have Node + Redis ready!"
