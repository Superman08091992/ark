# ARK Bundled Dependencies

This directory contains pre-downloaded dependencies to enable **partial offline installation**.

## 📦 What's Included

| Dependency | Version | Size | Status |
|------------|---------|------|--------|
| **Node.js** | v20.10.0 | 168MB | ✅ Bundled |
| **Redis** | v7.2.4 | 13MB | ✅ Bundled |
| **Ollama** | - | 200MB | ❌ Not included |
| **AI Models** | - | 1.3GB+ | ❌ Not included |

**Total bundled:** 181MB  
**Still need internet for:** Ollama + AI models (~1.5GB)

## 🎯 Benefits

✅ **Faster installation** - Node + Redis already downloaded  
✅ **Consistent versions** - Same versions across all installations  
✅ **Partial offline** - 2 out of 4 dependencies included  
✅ **Small repo size** - 181MB is acceptable for GitHub  

## 📁 Structure

```
deps/
├── node/
│   └── nodejs/               # Node.js v20.10.0 (portable)
│       ├── bin/
│       │   ├── node          # Node binary
│       │   └── npm           # NPM package manager
│       ├── lib/
│       └── include/
│
├── redis/
│   └── bin/                  # Redis v7.2.4 (compiled)
│       ├── redis-server      # Redis server
│       ├── redis-cli         # Redis client
│       └── redis-benchmark   # Benchmarking tool
│
├── download-deps.sh          # Script to download these deps
├── VERSIONS.txt              # Version information
└── README.md                 # This file
```

## 🚀 How It's Used

The `install-ark-host.sh` script automatically detects and uses these bundled dependencies:

```bash
# 1. Check for bundled Node.js
if [ -d "./deps/node/nodejs" ]; then
    echo "✅ Using bundled Node.js v20.10.0"
    export PATH="./deps/node/nodejs/bin:$PATH"
else
    echo "⬇️  Installing Node.js from system packages..."
    apt install nodejs npm
fi

# 2. Check for bundled Redis
if [ -f "./deps/redis/bin/redis-server" ]; then
    echo "✅ Using bundled Redis v7.2.4"
    cp deps/redis/bin/* /usr/local/bin/
else
    echo "⬇️  Installing Redis from system packages..."
    apt install redis-server
fi

# 3. Ollama still needs download (too large)
echo "⬇️  Installing Ollama..."
curl -fsSL https://ollama.ai/install.sh | sh

# 4. Download AI model (interactive choice)
ollama pull llama3.2:1b
```

## 📊 Installation Comparison

### Without Bundled Deps (Old Way)
```
Internet downloads needed:
- Node.js:    40MB
- Redis:      1MB
- Ollama:     200MB
- Model:      1.3GB+
---
Total:        ~1.5GB download
Time:         10-20 minutes
```

### With Bundled Deps (New Way)
```
Included in repo (no download):
- Node.js:    168MB ✅
- Redis:      13MB ✅

Internet downloads needed:
- Ollama:     200MB
- Model:      1.3GB+
---
Total:        ~1.5GB download (same)
But:          Node + Redis ready instantly!
Time:         8-15 minutes (slightly faster)
```

## 🔄 Updating Dependencies

To update the bundled dependencies:

```bash
cd deps
./download-deps.sh

# This will:
# 1. Download latest Node.js LTS
# 2. Download latest Redis stable
# 3. Build Redis from source
# 4. Update VERSIONS.txt
```

## 🌍 Platform Support

### Currently Supported:
- ✅ Linux x86_64 (AMD64)
- ✅ Linux ARM64 (aarch64)

### Not Yet Supported:
- ❌ macOS (use Homebrew instead)
- ❌ Windows (use WSL or official installers)

The `download-deps.sh` script detects your architecture and downloads the appropriate binaries.

## 💡 Why Not Include Ollama/Models?

### Ollama (~200MB)
- ⚠️  Approaching GitHub's 100MB file limit
- Could use Git LFS but adds complexity
- Easy to download (one curl command)

### AI Models (~1.3GB+)
- ❌ Way too large for GitHub repo
- ✅ Better suited for GitHub Releases
- ✅ Users can choose which model they want

## 📥 Complete Offline Installation

For **true offline installation**, download a release bundle:

```bash
# Download complete offline bundle from GitHub Releases
wget https://github.com/Superman08091992/ark/releases/download/v1.0.0/ark-offline-bundle.tar.gz

# This includes everything:
# - Node.js ✅
# - Redis ✅
# - Ollama ✅
# - AI Model ✅

# Extract and install (no internet needed)
tar -xzf ark-offline-bundle.tar.gz
cd ark-offline-bundle
sudo ./install-offline.sh
```

## ✅ Summary

**This directory enables:**
- ✅ Faster git clone (deps included)
- ✅ Partial offline installation
- ✅ Consistent dependency versions
- ✅ No package manager issues

**You still need internet for:**
- Ollama binary (~200MB)
- AI model (~1.3GB+)

**For completely offline:** Use GitHub Release bundles instead

---

**Last Updated:** 2025-11-08  
**Architecture:** x86_64  
**Node.js:** v20.10.0  
**Redis:** v7.2.4
