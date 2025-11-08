# ARK AI Model Guide

Complete guide to AI models in ARK - automatic download, bundled models, and manual setup.

---

## 🤖 **What Changed**

The ARK installer now:

✅ **Automatically downloads an AI model** during installation  
✅ **Gives you model choices** (different sizes and capabilities)  
✅ **Can bundle a model** in the installer (offline installation)  
✅ **Tests the model** after installation  

---

## 🚀 **Option 1: Automatic Download (Default)**

The standard `ark-installer` now prompts you to choose a model during host installation.

### **How It Works:**

```bash
# Install ARK host
sudo ./ark-installer host

# You'll see:
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

### **Model Comparison:**

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **llama3.2:1b** | 1.3GB | ⚡⚡⚡ | ⭐⭐⭐ | Quick responses, testing |
| **llama3.2:3b** | 2GB | ⚡⚡ | ⭐⭐⭐⭐ | General use, balanced |
| **qwen2.5:3b** | 2.5GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | Reasoning, math |
| **phi3:mini** | 2.4GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Fast, efficient |
| **llama3.1:8b** | 4.7GB | ⚡ | ⭐⭐⭐⭐⭐ | High quality output |
| **mistral:7b** | 4.1GB | ⚡ | ⭐⭐⭐⭐⭐ | Very capable |
| **codellama:7b** | 3.8GB | ⚡ | ⭐⭐⭐⭐⭐ | Code generation |

### **Recommendation:**

- **Testing/Demo:** llama3.2:1b (fastest download, good enough)
- **Daily Use:** llama3.2:3b or qwen2.5:3b (balanced)
- **Production:** llama3.1:8b or mistral:7b (best quality)
- **Coding:** codellama:7b (optimized for code)

---

## 📦 **Option 2: Bundled Model (Offline Install)**

Create an installer that **includes the AI model** inside it - no download needed!

### **Why Use This?**

- ✅ **Offline installation** - no internet needed
- ✅ **Faster deployment** - model already included
- ✅ **Consistent** - same model everywhere
- ✅ **Portable** - single file contains everything

### **How to Create:**

```bash
# 1. Make sure you have ollama installed
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Run the bundle script
./bundle-model-installer.sh

# You'll be prompted to choose a model:
📦 Which model do you want to bundle in the installer?

  1) llama3.2:1b     - Smallest (1.3GB) [RECOMMENDED]
  2) llama3.2:3b     - Medium (2GB)
  3) qwen2.5:3b      - Reasoning (2.5GB)
  4) phi3:mini       - Fast (2.4GB)
  5) Custom model name

# 3. Wait for build
# Output: ark-installer-with-model (size: ~67KB + model size)
```

### **Installer Sizes:**

| Model | Installer Size | Download Time |
|-------|---------------|---------------|
| llama3.2:1b | ~1.4GB | Fast |
| llama3.2:3b | ~2.1GB | Moderate |
| llama3.1:8b | ~4.8GB | Slower |

### **Using the Bundled Installer:**

```bash
# Show what model is included
./ark-installer-with-model model-info

# Install host (uses bundled model, no download)
sudo ./ark-installer-with-model host

# Create USB + install host with model
./ark-installer-with-model both /media/myusb

# Extract everything including model
./ark-installer-with-model extract ./ark-files
```

---

## 🔧 **Option 3: Manual Model Setup**

Skip automatic download and set up models yourself later.

### **During Installation:**

```bash
sudo ./ark-installer host

# When prompted, choose option 8 (Skip)
Enter choice [1-8]: 8

⏭️  Skipping model download. Install later with:
   ollama pull llama3.2:1b
```

### **Install Model Later:**

```bash
# List available models
ollama list

# Pull a model
ollama pull llama3.2:1b

# Or any other model
ollama pull mistral:7b
ollama pull codellama:7b
ollama pull llama3.1:8b

# Test the model
echo "Hello, how are you?" | ollama run llama3.2:1b
```

---

## 📊 **Complete Model Catalog**

### **Small Models (< 2GB)**

```bash
ollama pull llama3.2:1b        # 1.3GB - Fast, basic
ollama pull phi3:mini          # 2.4GB - Microsoft, efficient
ollama pull gemma:2b           # 1.7GB - Google, compact
ollama pull tinyllama          # 637MB - Tiny, very fast
```

### **Medium Models (2-4GB)**

```bash
ollama pull llama3.2:3b        # 2GB - Balanced
ollama pull qwen2.5:3b         # 2.5GB - Good reasoning
ollama pull mistral:7b         # 4.1GB - Very capable
ollama pull codellama:7b       # 3.8GB - Code focused
```

### **Large Models (> 4GB)**

```bash
ollama pull llama3.1:8b        # 4.7GB - High quality
ollama pull llama3.1:70b       # 40GB - Best quality (needs lots of RAM)
ollama pull mixtral:8x7b       # 26GB - Mixture of experts
ollama pull qwen2.5:14b        # 9GB - Enhanced reasoning
```

### **Specialized Models**

```bash
ollama pull codellama:7b       # Code generation
ollama pull llava:7b           # Vision + language
ollama pull mistral-openorca   # Instruction-tuned
ollama pull vicuna:7b          # Conversational
ollama pull wizardcoder:7b     # Code + chat
```

---

## 🎯 **Quick Decision Guide**

### **For Testing:**
```bash
sudo ./ark-installer host
# Choose: 1 (llama3.2:1b)
# Fast download, good enough for testing
```

### **For Production:**
```bash
sudo ./ark-installer host
# Choose: 5 (llama3.1:8b) or 6 (mistral:7b)
# Best quality responses
```

### **For Offline Install:**
```bash
./bundle-model-installer.sh
# Choose: 1 (llama3.2:1b) for smaller file
# Or: 2 (llama3.2:3b) for better quality
# Creates: ark-installer-with-model
```

### **For Coding:**
```bash
sudo ./ark-installer host
# Choose: 7 (codellama:7b)
# Optimized for code generation
```

---

## 🔍 **How the Installer Works**

### **Standard Installer Flow:**

```
1. Install dependencies (Node.js, Redis, Ollama)
   ↓
2. Create ARK directories (/opt/ark-host)
   ↓
3. Setup systemd services
   ↓
4. Start Redis and Ollama
   ↓
5. Prompt for model choice
   ↓
6. Download selected model (ollama pull)
   ↓
7. Test model
   ↓
8. Update config.yaml with selected model
   ↓
9. Done! ✅
```

### **Bundled Installer Flow:**

```
1. Install dependencies (Node.js, Redis, Ollama)
   ↓
2. Create ARK directories (/opt/ark-host)
   ↓
3. Setup systemd services
   ↓
4. Start Redis and Ollama
   ↓
5. Extract bundled model from installer
   ↓
6. Import model into Ollama (no download!)
   ↓
7. Test model
   ↓
8. Done! ✅ (Much faster - no internet needed)
```

---

## 💡 **Tips and Tricks**

### **Check Model Status:**

```bash
# List installed models
ollama list

# Show model details
ollama show llama3.2:1b

# Test a model
echo "Hello!" | ollama run llama3.2:1b
```

### **Manage Models:**

```bash
# Remove a model
ollama rm llama2

# Update a model
ollama pull llama3.2:1b

# Copy a model
ollama cp llama3.2:1b my-custom-model
```

### **Switch Models:**

```bash
# Edit ARK config
sudo nano /opt/ark-host/config.yaml

# Change the model line:
models:
  - llama3.2:3b  # Change this to your preferred model

# Restart ARK service
sudo systemctl restart ark-host
```

---

## 🆘 **Troubleshooting**

### **Model download fails:**

```bash
# Check internet connection
ping ollama.ai

# Try manually
ollama pull llama3.2:1b

# Check disk space
df -h
```

### **Model won't load:**

```bash
# Check Ollama service
systemctl status ark-ollama

# Restart Ollama
sudo systemctl restart ark-ollama

# Check logs
journalctl -u ark-ollama -n 50
```

### **Out of memory:**

```bash
# Check available RAM
free -h

# Use a smaller model
ollama pull llama3.2:1b  # Only 1.3GB

# Or increase swap
sudo fallocate -l 4G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📚 **More Resources**

- **Ollama Models:** https://ollama.ai/library
- **Model Comparisons:** https://ollama.ai/blog
- **ARK GitHub:** https://github.com/Superman08091992/ark

---

## ✅ **Summary**

| Method | Internet Needed | Setup Time | Best For |
|--------|----------------|------------|----------|
| **Auto Download** | ✅ Yes | 5-10 min | Normal installation |
| **Bundled Model** | ❌ No | 2-3 min | Offline/fast deployment |
| **Manual Setup** | ✅ Yes | Varies | Custom configurations |

**Recommendation:** Use auto download for first install, create bundled installer for distribution.

---

**Last Updated:** 2025-11-08
