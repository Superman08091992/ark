# Install ARK Anywhere - Quick Reference

## ✅ **YES - The Same Package Works Everywhere!**

The `ark-complete-YYYYMMDD.tar.gz` package created by `./create-unified-ark.sh` works on:
- ✅ Raspberry Pi (Debian/Raspbian)
- ✅ Android/Termux
- ✅ Linux (Ubuntu, Debian, Arch, etc.)
- ✅ macOS
- ✅ Any Unix-like system

**Same package, different commands based on system!**

---

## 🎯 **Installation Commands by Platform**

### **Raspberry Pi / Linux Server**

```bash
# Extract package
tar -xzf ark-complete-*.tar.gz
cd ark-unified

# Install to system location (needs sudo)
sudo ./install.sh

# Or custom location
sudo ./install.sh /opt/ark

# Start ARK
ark-redis &
ark
```

**Installs to:** `/opt/ark` (default)  
**Needs sudo:** Yes

---

### **Android/Termux**

```bash
# Extract package
tar -xzf ark-complete-*.tar.gz
cd ark-unified

# Install to home directory (no sudo)
./install.sh ~/ark

# Reload shell
source ~/.bashrc

# Start ARK
ark-redis &
ark
```

**Installs to:** `~/ark` (recommended)  
**Needs sudo:** No (doesn't exist on Android)

---

### **macOS**

```bash
# Extract package
tar -xzf ark-complete-*.tar.gz
cd ark-unified

# Install to system location
sudo ./install.sh

# Or user location
./install.sh ~/ark

# Start ARK
ark-redis &
ark
```

**Installs to:** `/opt/ark` (default) or `~/ark`  
**Needs sudo:** Yes for system install

---

### **User Installation (Any Platform)**

```bash
# Works on ALL platforms
# No sudo required
./install.sh ~/my-ark

# Add to PATH manually if needed
echo 'export PATH="$HOME/my-ark/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Start ARK
ark-redis &
ark
```

---

## 🔍 **How It Detects Your System**

The installer automatically detects:

```
Android/Termux  → Skips sudo, installs to ~/ark
Raspberry Pi    → Uses sudo, installs to /opt/ark
Linux           → Uses sudo, installs to /opt/ark
macOS           → Uses sudo, installs to /opt/ark
```

**You don't need to modify anything!** Just run the appropriate command for your platform.

---

## 📦 **What Gets Installed**

### On Raspberry Pi:
```
/opt/ark/
├── bin/
│   ├── ark           # Backend
│   ├── ark-web       # Web UI
│   └── ark-redis     # Redis
├── lib/              # Code
├── data/             # Storage
└── deps/             # Node.js + Redis
```

### On Android/Termux:
```
~/ark/
├── bin/
│   ├── ark           # Backend
│   ├── ark-web       # Web UI
│   └── ark-redis     # Redis
├── lib/              # Code
├── data/             # Storage
└── deps/             # Node.js + Redis
```

**Same structure, different location!**

---

## 🚀 **After Installation**

### All Platforms:

```bash
# Check installation
which ark

# Should show:
# Raspberry Pi: /opt/ark/bin/ark
# Android: ~/ark/bin/ark

# Start services
ark-redis &
ark

# Check it's running
ps aux | grep ark
```

---

## 🔄 **Create Package on Any Platform**

### On Android/Termux:

```bash
cd ~/ark
git pull origin master
./create-unified-ark.sh

# Creates: ark-complete-20251108.tar.gz
# Copy to computer via:
cp ark-complete-*.tar.gz ~/storage/shared/
```

### On Raspberry Pi:

```bash
cd ~/ark
git pull origin master
./create-unified-ark.sh

# Creates: ark-complete-20251108.tar.gz
# Use on other devices
```

### On Desktop:

```bash
cd ~/ark
git pull origin master
./create-unified-ark.sh

# Creates: ark-complete-20251108.tar.gz
# Upload to GitHub releases or copy to USB
```

---

## 💡 **Workflow Example**

### 1. Develop on Android/Termux:
```bash
# Make changes
cd ~/ark
nano lib/intelligent-backend.cjs

# Test locally
./install.sh ~/ark-test
~/ark-test/bin/ark

# Push to GitHub
git add .
git commit -m "feat: New feature"
git push
```

### 2. Package and Deploy:
```bash
# Create package
./create-unified-ark.sh

# Copy to shared storage
cp ark-complete-*.tar.gz ~/storage/shared/

# Transfer to Raspberry Pi
```

### 3. Install on Raspberry Pi:
```bash
# On Pi
scp ark-complete-*.tar.gz pi@raspberrypi:~/
ssh pi@raspberrypi

# Install
tar -xzf ark-complete-*.tar.gz
cd ark-unified
sudo ./install.sh

# Run
ark-redis &
ark
```

---

## 🎯 **Key Points**

1. **Same Package = Universal**
   - One `tar.gz` works everywhere
   - Installer auto-detects platform

2. **Installation Location:**
   - **System:** `/opt/ark` (needs sudo)
   - **User:** `~/ark` (no sudo)

3. **Android/Termux Special:**
   - No sudo available or needed
   - Automatically uses user install
   - Works perfectly!

4. **Raspberry Pi:**
   - Uses sudo for system install
   - Installs to `/opt/ark`
   - Works like any Linux

5. **Commands After Install:**
   ```bash
   ark-redis &  # Start Redis
   ark          # Start ARK backend
   ark-web      # Start web UI (if available)
   ```

---

## 📝 **Quick Commands**

### Test Installation:
```bash
which ark
ark --version  # (if implemented)
ls -la $(which ark)
```

### Uninstall:
```bash
# System install
sudo rm -rf /opt/ark

# User install
rm -rf ~/ark

# Remove from PATH
# Edit ~/.bashrc and remove ARK lines
```

### Reinstall:
```bash
# Just run install again
./install.sh
# Overwrites existing installation
```

---

## ✅ **Summary Table**

| Platform | Command | Install Location | Sudo? |
|----------|---------|------------------|-------|
| **Raspberry Pi** | `sudo ./install.sh` | `/opt/ark` | Yes |
| **Android/Termux** | `./install.sh ~/ark` | `~/ark` | No |
| **Linux Server** | `sudo ./install.sh` | `/opt/ark` | Yes |
| **macOS** | `sudo ./install.sh` | `/opt/ark` | Yes |
| **Any (user)** | `./install.sh ~/ark` | `~/ark` | No |

---

## 🎉 **You're All Set!**

The unified installer works everywhere with the same package. Just use the right command for your platform!

**One package, infinite possibilities!** 🚀
