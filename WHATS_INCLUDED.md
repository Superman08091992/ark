# What's Included in ARK Repository

## ✅ **YES - Node.js and Redis are now bundled!**

As of commit `66c681f`, the ARK repository includes pre-downloaded dependencies.

---

## 📦 **Bundled Dependencies (In Repo)**

| Dependency | Version | Size | Location |
|------------|---------|------|----------|
| **Node.js** | v20.10.0 | 168MB | `deps/node/nodejs/` |
| **Redis** | v7.2.4 | 13MB | `deps/redis/bin/` |

**Total bundled:** 181MB

### **Benefits:**

✅ **Partial offline installation** - Node + Redis ready without download  
✅ **Faster setup** - 2 out of 4 dependencies included  
✅ **Consistent versions** - Same versions across all installs  
✅ **No package manager issues** - Direct binaries included  

---

## ❌ **NOT Included (Still Need Internet)**

| Dependency | Size | Why Not Included |
|------------|------|------------------|
| **Ollama** | ~200MB | Too large (approaching GitHub 100MB file limit) |
| **AI Models** | ~1.3GB+ | Way too large for repo |

**Internet needed during install:** ~1.5GB for Ollama + model

---

## 🚀 **Installation Experience**

### **What Happens Now:**

```
1. Git clone (repo size: ~181MB)
   ↓
2. Run ./ark-installer host
   ↓
3. ✅ Node.js detected (bundled) - instant!
   ✅ Redis detected (bundled) - instant!
   ⬇️  Ollama downloading... (~200MB)
   ⬇️  AI model downloading... (~1.3GB)
   ↓
4. Done!
```

### **Time Comparison:**

| Stage | Before (Old) | Now (With Bundled Deps) |
|-------|--------------|-------------------------|
| Git clone | ~5 seconds | ~30 seconds (larger repo) |
| Node.js install | ~2 minutes | ✅ Instant (bundled) |
| Redis install | ~1 minute | ✅ Instant (bundled) |
| Ollama install | ~3 minutes | ~3 minutes (same) |
| Model download | ~5-10 minutes | ~5-10 minutes (same) |
| **Total** | **~11-16 minutes** | **~8-13 minutes** |

**Net result:** ~3 minutes faster, more reliable

---

## 📊 **Repository Size**

```
Before:  2.8MB
Now:     ~183MB (181MB deps + 2MB code)
```

**Still acceptable for GitHub** (under 1GB soft limit)

---

## 🎯 **How the Installer Uses Bundled Deps**

The modified `install-ark-host.sh` now:

1. **Checks for bundled Node.js:**
   ```bash
   if [ -d "./deps/node/nodejs" ]; then
       echo "✅ Using bundled Node.js v20.10.0"
       export PATH="./deps/node/nodejs/bin:$PATH"
   else
       apt install nodejs npm  # Fallback
   fi
   ```

2. **Checks for bundled Redis:**
   ```bash
   if [ -f "./deps/redis/bin/redis-server" ]; then
       echo "✅ Using bundled Redis v7.2.4"
       cp deps/redis/bin/* /usr/local/bin/
   else
       apt install redis-server  # Fallback
   fi
   ```

3. **Always downloads Ollama + model** (not bundled)

---

## 💡 **Future: Complete Offline Option**

For **truly offline** installation, we plan to create **GitHub Release bundles**:

```
ark-offline-complete-v1.0.0.tar.gz (~1.6GB)
├── Node.js ✅
├── Redis ✅
├── Ollama ✅
├── AI Model (llama3.2:1b) ✅
```

Download once → Install anywhere (no internet)

---

## 📥 **How to Use**

### **Standard Installation (Partial Offline):**

```bash
# Clone repo (includes Node + Redis)
git clone https://github.com/Superman08091992/ark.git
cd ark

# Run installer (only downloads Ollama + model)
chmod +x ark-installer
sudo ./ark-installer host

# Node + Redis: ✅ Instant (bundled)
# Ollama: ⬇️  Downloads (~200MB)
# Model: ⬇️  Downloads (~1.3GB)
```

### **Download Just the Installer (68KB):**

```bash
# Tiny installer without bundled deps
wget https://raw.githubusercontent.com/Superman08091992/ark/master/ark-installer
chmod +x ark-installer
sudo ./ark-installer host

# Will download everything during install:
# Node, Redis, Ollama, Model (~1.5GB total)
```

---

## 🔄 **Updating Bundled Dependencies**

To update Node.js or Redis versions:

```bash
cd deps
./download-deps.sh

# Downloads latest versions
# Rebuilds Redis from source
# Updates VERSIONS.txt

git add deps/
git commit -m "chore: Update bundled dependencies"
```

---

## ✅ **Summary**

### **What You Get:**

| Feature | Status |
|---------|--------|
| Node.js bundled | ✅ Yes (168MB) |
| Redis bundled | ✅ Yes (13MB) |
| Ollama bundled | ❌ No (too large) |
| Model bundled | ❌ No (too large) |
| Partial offline install | ✅ Yes |
| Full offline install | ⏳ Coming (via releases) |

### **Internet Requirements:**

**During git clone:**
- ❌ NO internet needed (if you have the zip)
- ✅ YES if cloning directly

**During installation:**
- ❌ NO internet needed for Node + Redis
- ✅ YES needed for Ollama + model (~1.5GB)

---

## 📝 **Documentation**

- **deps/README.md** - Detailed bundled dependencies info
- **deps/VERSIONS.txt** - Version information
- **deps/download-deps.sh** - Script to update deps
- **OFFLINE_INSTALLATION.md** - Complete offline guide
- **ADDING_DEPENDENCIES_TO_REPO.md** - Technical details

---

**Last Updated:** 2025-11-08  
**Commit:** 66c681f  
**Bundled:** Node.js v20.10.0 + Redis v7.2.4  
**Repository Size:** ~183MB
