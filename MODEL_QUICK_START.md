# AI Model Quick Start

**TL;DR:** ARK installer now automatically downloads an AI model for you!

---

## 🎯 **What You Get**

When you run:
```bash
sudo ./ark-installer host
```

You'll see:
```
📦 Choose an AI model for ARK:

  1) llama3.2:1b     - Fastest, smallest (1.3GB) [RECOMMENDED]
  2) llama3.2:3b     - Balanced (2GB)
  3) qwen2.5:3b      - Better reasoning (2.5GB)
  4) phi3:mini       - Microsoft, fast (2.4GB)
  5) llama3.1:8b     - High quality (4.7GB)
  6) mistral:7b      - Very capable (4.1GB)
  7) codellama:7b    - Best for coding (3.8GB)
  8) Skip            - Download manually later

Enter choice [1-8] (default: 1):
```

---

## ⚡ **Quick Recommendations**

| Your Need | Choose | Size | Time |
|-----------|--------|------|------|
| **Just testing** | 1 (llama3.2:1b) | 1.3GB | ~2 min |
| **Daily use** | 2 (llama3.2:3b) | 2GB | ~3 min |
| **Best quality** | 5 (llama3.1:8b) | 4.7GB | ~8 min |
| **Coding tasks** | 7 (codellama:7b) | 3.8GB | ~6 min |

---

## 📦 **Offline Installation**

Want to install WITHOUT internet? Create a bundled installer:

```bash
# 1. Build installer with embedded model
./bundle-model-installer.sh

# Choose model (recommend option 1 for smallest)
# Output: ark-installer-with-model (~1.4GB - 4.8GB)

# 2. Copy to USB or distribute

# 3. Install anywhere (no internet needed!)
sudo ./ark-installer-with-model host
```

**Benefits:**
- ✅ No download during installation
- ✅ Faster deployment
- ✅ Works offline
- ✅ Single file contains everything

---

## 🔧 **What Happens**

```
Install ARK Host
      ↓
Download/Bundle Model
      ↓
Import into Ollama
      ↓
Test Model
      ↓
Ready to Use! ✅
```

The model is automatically:
- Downloaded (or extracted if bundled)
- Imported into Ollama
- Tested to ensure it works
- Configured in ARK

---

## 📚 **Full Guide**

See [`AI_MODEL_GUIDE.md`](./AI_MODEL_GUIDE.md) for complete documentation.

---

## ✅ **Summary**

**Standard install:**
```bash
sudo ./ark-installer host
# Choose a model (default: llama3.2:1b)
# Wait ~2-8 minutes
# Done! Model ready to use
```

**Bundled install (offline):**
```bash
./bundle-model-installer.sh
# Choose model to bundle
# Distribute ark-installer-with-model
# Install anywhere (no internet!)
```

**Your ARK system will have an AI model ready to query!** 🎉

---

**Last Updated:** 2025-11-08
