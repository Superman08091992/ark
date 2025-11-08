# ARK Offline Installation Guide

**Answer to: "Can it work without internet after download?"**

---

## 🔴 **Current Reality (Standard Installer)**

**NO** - The standard `ark-installer` currently **REQUIRES internet** during installation.

### **What Needs Internet:**

```
1. Node.js download     (~40MB)  ❌ Internet required
2. Redis download       (~1MB)   ❌ Internet required  
3. Ollama download      (~200MB) ❌ Internet required
4. AI Model download    (~1.3GB+)❌ Internet required
5. System updates       (varies) ❌ Internet required
```

### **Current Installer Flow:**

```
Download ark-installer (68KB)
      ↓
Run ./ark-installer host
      ↓
[NEEDS INTERNET] Install Node.js via apt/brew/pacman
      ↓
[NEEDS INTERNET] Install Redis via package manager
      ↓
[NEEDS INTERNET] Install Ollama via curl script
      ↓
[NEEDS INTERNET] Download AI model via ollama pull
      ↓
Setup and start services
      ↓
Done ✅
```

**Total internet usage:** ~1.5GB - 5GB depending on model choice

---

## ✅ **Solution: True Offline Installer**

I can create a **fully offline installer** that bundles everything.

### **Option 1: Minimal Offline Bundle** (~1.6GB)

Contains:
- ✅ Node.js binary (40MB)
- ✅ Redis binary (1MB)
- ✅ Ollama binary (200MB)
- ✅ Smallest AI model: llama3.2:1b (1.3GB)
- ✅ All ARK scripts

**Result:** Single file, no internet needed after download

### **Option 2: Full Offline Bundle** (~4.8GB)

Contains:
- ✅ Node.js binary
- ✅ Redis binary
- ✅ Ollama binary
- ✅ Better AI model: llama3.1:8b (4.7GB)
- ✅ All ARK scripts

**Result:** Single file with high-quality model

---

## 🛠️ **How to Create Offline Installer**

### **Method 1: Using Docker (Recommended)**

```bash
# Create a Docker-based offline bundle
# This will build everything in a container and export

./create-offline-bundle.sh

# Choose model size:
# 1) Minimal (1.6GB) - llama3.2:1b
# 2) Full (4.8GB) - llama3.1:8b

# Output: ark-offline-installer
# Can be copied to USB and run anywhere!
```

### **Method 2: Manual Bundle**

```bash
# 1. Download dependencies on a machine with internet
mkdir ark-offline-bundle
cd ark-offline-bundle

# Download Node.js
wget https://nodejs.org/dist/v20.10.0/node-v20.10.0-linux-x64.tar.gz

# Download Redis
wget https://download.redis.io/releases/redis-7.2.3.tar.gz

# Download Ollama
curl -L https://ollama.ai/download/ollama-linux-amd64 -o ollama

# Download model
ollama pull llama3.2:1b
ollama pull llama3.2:1b -o model-export/

# 2. Bundle everything
tar -czf ark-complete-offline.tar.gz .

# 3. Create installer wrapper
# (Script provided below)
```

---

## 📦 **Offline Installer Architecture**

### **Structure:**

```
ark-offline-installer (1.6GB - 4.8GB)
│
├── [Self-extracting header script]
│
└── [Compressed payload]
    ├── node-v20.10.0-linux-x64/      (Node.js binary)
    ├── redis-7.2.3/                   (Redis source/binary)
    ├── ollama                         (Ollama binary)
    ├── models/
    │   └── llama3.2-1b.gguf          (AI model)
    ├── install-offline.sh             (Offline installer script)
    └── ark-scripts/
        ├── intelligent-backend.cjs
        ├── agent_tools.cjs
        └── ...
```

### **Installation Flow:**

```
./ark-offline-installer host
      ↓
Extract all binaries (no download!)
      ↓
Install Node.js from bundle
      ↓
Install Redis from bundle
      ↓
Install Ollama from bundle
      ↓
Import model from bundle
      ↓
Setup services
      ↓
Done! ✅ (No internet used)
```

---

## ⚠️ **Current Limitations**

### **What the Standard Installer Does:**

✅ Downloads as single file (68KB)  
❌ Requires internet for dependencies  
❌ Requires internet for AI model  
❌ Needs package manager updates  

### **What an Offline Installer Would Do:**

✅ Downloads as single file (1.6GB - 4.8GB)  
✅ No internet needed after download  
✅ Includes all dependencies  
✅ Includes AI model  
✅ Works on air-gapped systems  

---

## 🎯 **Workaround: Current Best Practice**

Until the offline installer is ready, here's the best approach:

### **Scenario 1: You Have Internet on Target Machine**

```bash
# Simple - use standard installer
wget https://github.com/Superman08091992/ark/raw/master/ark-installer
chmod +x ark-installer
sudo ./ark-installer host

# Internet will be used during installation
# Choose smallest model (option 1) for fastest download
```

### **Scenario 2: Air-Gapped / No Internet**

```bash
# ON A MACHINE WITH INTERNET:

# 1. Install dependencies
sudo apt install nodejs npm redis-server
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Download model
ollama pull llama3.2:1b

# 3. Package everything
mkdir ark-complete
cp /usr/bin/node ark-complete/
cp /usr/bin/redis-server ark-complete/
cp /usr/local/bin/ollama ark-complete/
cp -r ~/.ollama/models/ ark-complete/models/
tar -czf ark-airgap-bundle.tar.gz ark-complete/

# 4. Copy ark-airgap-bundle.tar.gz to target machine via USB

# ON AIR-GAPPED MACHINE:
tar -xzf ark-airgap-bundle.tar.gz
cd ark-complete
# Install binaries manually
sudo cp node /usr/local/bin/
sudo cp redis-server /usr/local/bin/
sudo cp ollama /usr/local/bin/
sudo cp -r models/ ~/.ollama/
```

---

## 💡 **What Would You Prefer?**

### **Option A: Keep Current (Requires Internet)**

**Pros:**
- ✅ Small download (68KB)
- ✅ Always gets latest dependencies
- ✅ Works today

**Cons:**
- ❌ Needs internet during install
- ❌ Takes 5-15 minutes to download everything
- ❌ Won't work on air-gapped systems

### **Option B: Create True Offline Installer**

**Pros:**
- ✅ No internet needed after download
- ✅ Works on air-gapped systems
- ✅ Faster installation (no downloads)
- ✅ Consistent - same versions everywhere

**Cons:**
- ❌ Large download (1.6GB - 4.8GB)
- ❌ Takes time to create
- ❌ Needs updating when dependencies change

---

## 🚀 **I Can Build This For You**

Would you like me to:

1. **Create a minimal offline bundle** (1.6GB with llama3.2:1b)
2. **Create a full offline bundle** (4.8GB with llama3.1:8b)
3. **Create both** and let users choose
4. **Just document the workaround** for now

---

## 📊 **Comparison Table**

| Feature | Standard Installer | Offline Bundle |
|---------|-------------------|----------------|
| Download size | 68KB | 1.6GB - 4.8GB |
| Internet during install | ✅ Required | ❌ Not needed |
| Installation time | 10-20 min | 2-5 min |
| Works air-gapped | ❌ No | ✅ Yes |
| Always up-to-date | ✅ Yes | ❌ No |
| Easy to distribute | ✅ Yes | ⚠️ Large file |

---

## ✅ **Summary**

**Your Question:** *"So it's all automatic once it's downloaded, no internet necessary?"*

**Answer:** 

**NO** - The current installer (68KB) requires internet to download:
- Node.js (~40MB)
- Redis (~1MB)
- Ollama (~200MB)
- AI Model (~1.3GB+)

**Total internet usage during install:** ~1.5GB - 5GB

**BUT** - I can create a **true offline installer** (~1.6GB - 4.8GB) that bundles everything and requires **NO internet** after the initial download.

---

## 🎯 **What Do You Want?**

1. **Keep current** (68KB, needs internet during install)
2. **Build offline version** (1.6GB+, no internet needed)
3. **Offer both options** (users choose)

Let me know and I'll implement it! 🚀

---

**Last Updated:** 2025-11-08
