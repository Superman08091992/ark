# Portable ARK - Configuration Options & Customization

## 🤔 Your Questions Answered

### Q: "Does it use a dockerfile?"

**A:** Yes and No - you have **2 deployment options**:

1. **Simple Mode** (Current portable setup) - Uses Node.js directly, no custom Dockerfile
2. **Advanced Mode** (Your existing Dockerfiles) - Full containerized microservices

### Q: "Do you know how i want it?"

**A:** Let me explain both options so you can choose!

### Q: "What are the options when setting it up?"

**A:** Multiple options for customization - see below!

---

## 📦 Deployment Options Explained

### **Option A: Simple Portable Mode** (Current Setup)

**What I created for you:**
```yaml
# Simplified docker-compose.yml
services:
  backend:
    image: node:20-alpine  # No custom Dockerfile
    command: sh -c "npm install && node intelligent-backend.cjs"
    volumes:
      - ./:/app  # Everything from USB
    ports:
      - "8000:8000"
  
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ./ollama_data:/root/.ollama
```

**Pros:**
- ✅ **Fastest setup** - no build step
- ✅ **Smallest size** - uses official images
- ✅ **Easy debugging** - direct file access
- ✅ **Quick updates** - edit files on USB

**Cons:**
- ⚠️ No isolation between services
- ⚠️ Installs npm packages on each start (can cache)

**Best for:** Quick portable use, development, testing

---

### **Option B: Full Microservices Mode** (Your Existing Setup)

**What you already have:**
```yaml
# Full docker-compose.yml
services:
  ark-core:       # Python FastAPI backend
  ark-frontend:   # Svelte frontend
  agents:         # Python agent services
  redis:          # Cache layer
  db-init:        # Database initialization
```

**With custom Dockerfiles:**
- `Dockerfile.core` - Python backend
- `Dockerfile.frontend` - Svelte UI
- `Dockerfile.agents` - Agent services
- `Dockerfile.db` - Database init

**Pros:**
- ✅ **Production-ready** - proper isolation
- ✅ **Scalable** - microservices architecture
- ✅ **Cached builds** - faster subsequent starts
- ✅ **Redis caching** - better performance

**Cons:**
- ⚠️ Longer first-time build
- ⚠️ More complex
- ⚠️ Larger disk usage

**Best for:** Production deployment, team use, scaling

---

## 🎯 Which One Do You Want?

### **Tell me your preference:**

**A) Portable & Simple** (current)
- Just want USB drive that works anywhere
- Don't need frontend UI
- Quick setup priority
- **→ Use existing `create-portable-ark.sh`**

**B) Full-Featured Production**
- Want complete microservices
- Need Redis caching
- Want Svelte frontend UI
- Production deployment
- **→ I'll create "create-portable-ark-full.sh"**

**C) Hybrid (Best of Both)**
- Node.js backend (simple)
- Ollama (portable)
- Optional frontend
- Optional Redis
- **→ I'll create configurable setup**

---

## 🔧 Configuration Options Available

### **1. Backend Choice**

**Option 1A: Node.js Backend** (Current)
```bash
# Uses intelligent-backend.cjs directly
# Lightweight, no Python needed
```

**Option 1B: Python Backend** (Your existing)
```bash
# Uses FastAPI backend
# More features, requires build
```

**Option 1C: Both**
```bash
# Run both backends
# Node.js on :8000, Python on :8001
```

---

### **2. Frontend Choice**

**Option 2A: No Frontend** (Current)
```bash
# API-only, use curl or Postman
# Smallest footprint
```

**Option 2B: Svelte UI** (Your existing)
```bash
# Full web interface
# Access via browser
```

**Option 2C: Simple HTML Frontend**
```bash
# Lightweight chat interface
# Single HTML file
```

---

### **3. LLM Integration**

**Option 3A: Ollama (Local)** (Current)
```bash
# Runs on USB drive
# Complete privacy
# ~4GB model storage
```

**Option 3B: External LLM API**
```bash
# Connect to OpenAI/Anthropic
# No local storage needed
# Requires API key
```

**Option 3C: Both**
```bash
# Ollama for offline
# API for better quality
# Configurable fallback
```

---

### **4. Storage Configuration**

**Option 4A: All on USB** (Current)
```bash
# Everything portable
# Slower I/O
# Complete portability
```

**Option 4B: Hybrid Storage**
```bash
# Models on local disk (fast)
# Data on USB (portable)
# Best performance
```

**Option 4C: Redis + USB**
```bash
# Redis cache (fast reads)
# USB for persistence
# Balance speed/portability
```

---

### **5. Auto-Start Options**

**Option 5A: Manual Start** (Current)
```bash
# Run start-ark.sh when needed
# Full control
```

**Option 5B: Auto-Start on Plug**
```bash
# USB triggers autorun script
# Windows/Mac only
# Requires setup
```

**Option 5C: Systemd Service**
```bash
# Start on host boot
# Linux only
# Production deployment
```

---

## 📋 Configuration Templates

### **Template 1: Current Setup (Simple Portable)**

```bash
./create-portable-ark.sh /path/to/usb

# Creates:
# - Node.js backend
# - Ollama LLM
# - All data on USB
# - Manual start
# - No frontend UI
```

**Customize by editing `docker-compose.yml` on USB**

---

### **Template 2: Full Production Setup**

```bash
./create-portable-ark-full.sh /path/to/usb --full

# Creates:
# - Python FastAPI backend
# - Svelte frontend UI
# - Redis cache
# - Ollama LLM
# - All microservices
# - Health checks
```

**I can create this script for you!**

---

### **Template 3: Hybrid Setup**

```bash
./create-portable-ark.sh /path/to/usb \
  --backend=node \
  --frontend=simple \
  --llm=ollama \
  --storage=hybrid \
  --cache=redis

# Creates:
# - Node.js backend (lightweight)
# - Simple HTML frontend
# - Ollama (local)
# - Models on host disk
# - Data on USB
# - Redis for caching
```

**I can add command-line options!**

---

## 🎨 Customization Examples

### **Add Redis Caching to Current Setup**

Edit `docker-compose.yml` on USB:

```yaml
services:
  backend:
    # ... existing config ...
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - ./redis_data:/data
```

---

### **Add Svelte Frontend**

```yaml
services:
  frontend:
    image: node:20-alpine
    working_dir: /app
    command: sh -c "cd frontend && npm install && npm run dev"
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app/frontend
    depends_on:
      - backend
```

---

### **Use External LLM API**

Edit on USB:

```yaml
services:
  backend:
    environment:
      - OLLAMA_HOST=https://api.openai.com/v1
      - OPENAI_API_KEY=sk-...
      - LLM_PROVIDER=openai  # or anthropic, cohere
```

Then update `agent_tools.cjs`:

```javascript
async queryLLM({ prompt }) {
  const provider = process.env.LLM_PROVIDER || 'ollama';
  
  if (provider === 'openai') {
    return this.queryOpenAI({ prompt });
  } else if (provider === 'anthropic') {
    return this.queryAnthropic({ prompt });
  } else {
    return this.queryOllama({ prompt });
  }
}
```

---

## 🚀 Advanced Options

### **Option: Distributed Setup**

Run backend on powerful server, access from USB:

```yaml
# On USB (lightweight client)
services:
  frontend:
    image: node:20-alpine
    environment:
      - BACKEND_URL=http://my-server:8000  # Remote backend
    ports:
      - "3000:3000"
```

```yaml
# On server (heavy lifting)
services:
  backend:
    # ... full backend setup ...
  ollama:
    # ... LLM with GPU ...
  redis:
    # ... caching ...
```

---

### **Option: Multi-LLM Setup**

Run multiple LLM models:

```yaml
services:
  ollama-small:
    image: ollama/ollama:latest
    command: sh -c "ollama serve & ollama pull llama2:7b"
    ports:
      - "11434:11434"
  
  ollama-large:
    image: ollama/ollama:latest
    command: sh -c "ollama serve & ollama pull llama2:70b"
    ports:
      - "11435:11434"
```

Configure routing in backend:

```javascript
const model = complexity > 0.8 ? 'llama2:70b' : 'llama2:7b';
const port = model.includes('70b') ? 11435 : 11434;
```

---

### **Option: GPU Acceleration**

If host has NVIDIA GPU:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## 🎛️ Environment Variables

Create `.env` file on USB for easy configuration:

```bash
# Backend Settings
BACKEND_TYPE=node          # node | python | both
PORT=8000
LOG_LEVEL=info             # debug | info | warn | error

# LLM Settings
LLM_PROVIDER=ollama        # ollama | openai | anthropic
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2
OPENAI_API_KEY=sk-...      # if using OpenAI
ANTHROPIC_API_KEY=sk-...   # if using Anthropic

# Storage Settings
STORAGE_MODE=usb           # usb | hybrid | local
MEMORY_PATH=/app/kyle_infinite_memory
KNOWLEDGE_PATH=/app/knowledge_base

# Cache Settings
REDIS_ENABLED=false        # true | false
REDIS_URL=redis://redis:6379

# Frontend Settings
FRONTEND_ENABLED=false     # true | false
FRONTEND_TYPE=svelte       # svelte | simple | none

# Features
AUTO_RESEARCH=true
SOURCE_CITATIONS=true
QUIET_MODE=true
REPETITION_TRACKING=true
```

Then reference in `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - PORT=${PORT:-8000}
      - LLM_PROVIDER=${LLM_PROVIDER:-ollama}
      - OLLAMA_HOST=${OLLAMA_HOST:-http://ollama:11434}
```

---

## 🔨 What Should I Build for You?

**Please tell me what you want:**

### **Option 1: Keep Simple Setup** ✅ (Current)
"The simple setup is fine, just show me how to customize it"

### **Option 2: Full Production Setup** 🏭
"I want all microservices, Redis, frontend, the works"

### **Option 3: Hybrid with Options** 🎛️
"I want a configurable setup with command-line options"

### **Option 4: Custom Combination** 🎨
"I want [specific features] - tell me what you need"

---

## 🎯 Quick Decision Guide

**Choose SIMPLE if:**
- You want portability above all
- Don't need web UI
- Want fastest setup
- Experimenting/testing

**Choose FULL if:**
- Production deployment
- Need scalability
- Want all features
- Team/multi-user

**Choose HYBRID if:**
- Want flexibility
- Different use cases
- Performance matters
- Configure per host

---

## 📞 Tell Me What You Need!

**What's your use case?**
- Personal portable AI?
- Team development?
- Production deployment?
- 24/7 server?
- Raspberry Pi?

**What features are must-have?**
- Web UI? (yes/no)
- Redis caching? (yes/no)
- GPU support? (yes/no)
- Multiple LLMs? (yes/no)
- Remote access? (yes/no)

**What's your priority?**
- Speed? (simple setup)
- Features? (full setup)
- Portability? (USB focus)
- Scale? (microservices)

**I'll create exactly what you need!** 🚀
