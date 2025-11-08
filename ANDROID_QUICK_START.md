# ARK on Android - Quick Start

**TL;DR:** Yes, you can use `ark-installer` on Android via Termux! Here's how.

---

## ✅ **YES, It Works!**

```
┌─────────────────────────────────────────┐
│         Android Phone/Tablet            │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │         Termux App                │  │
│  │  (Linux environment on Android)   │  │
│  │                                   │  │
│  │  $ ./ark-installer usb ./my-usb  │  │
│  │  ✅ Creates USB node files        │  │
│  └───────────────────────────────────┘  │
│                 ↓                       │
│  ┌───────────────────────────────────┐  │
│  │      File Manager (Files app)     │  │
│  │  Copy files to USB drive (OTG)    │  │
│  └───────────────────────────────────┘  │
│                 ↓                       │
│         [USB Drive] 📁                  │
│     Now an ARK identity node!           │
└─────────────────────────────────────────┘
```

---

## 🚀 **3-Step Setup**

### **Step 1: Install Termux** (2 minutes)

**Download from F-Droid (NOT Google Play):**
- https://f-droid.org/packages/com.termux/

Or APK directly:
- https://github.com/termux/termux-app/releases

### **Step 2: Setup in Termux** (1 minute)

Open Termux and run:

```bash
# Update packages
pkg update && pkg upgrade -y

# Install wget
pkg install wget -y

# Enable storage access (IMPORTANT!)
termux-setup-storage
```

**⚠️ Grant permission when Android asks!**

### **Step 3: Download & Run** (30 seconds)

```bash
# Go to shared storage
cd ~/storage/shared/Download

# Download ark-installer
wget https://raw.githubusercontent.com/Superman08091992/ark/master/ark-installer

# Make executable
chmod +x ark-installer

# Create USB node
./ark-installer usb ./my-ark-usb

# ✅ Done! Files created in Download/my-ark-usb/
```

---

## 📁 **Copy to USB Drive**

### **Connect USB via OTG adapter:**

1. **Plug in USB** drive to phone (via OTG cable/adapter)
2. **Open Files app** (Files by Google, or any file manager)
3. **Navigate to:** `Internal Storage → Download → my-ark-usb`
4. **Copy entire folder** to USB drive
5. **Eject USB** safely
6. ✅ **Done!** Your USB is now an ARK identity node

---

## 📱 **What You Can Do**

### ✅ **Works (No Root Needed):**

- Download `ark-installer` ✅
- Create USB node files ✅
- Extract all files ✅
- View documentation ✅
- Run ARK backend locally ✅
- Share with ngrok ✅

### ⚠️ **Limited (Without Root):**

- Direct USB device access ❌
- Install as system service ❌
- Auto-start on boot ❌

**Workaround:** Use file manager to copy files to USB (works perfectly!)

---

## 🔧 **Available Commands**

```bash
# Show help
./ark-installer --help

# Create USB node
./ark-installer usb ./my-usb-folder

# Extract all files
./ark-installer extract ./extracted-files

# View documentation
./ark-installer docs
```

---

## ⚡ **EtchDroid Alternative**

**Question:** Can I use EtchDroid?

**Answer:** Not really needed for ARK.

**Why?**
- EtchDroid writes **disk images** (ISO/IMG files)
- ARK installer creates **file structures** (folders/files)
- ARK USB nodes are just files, not bootable images

**What to use instead:**
- ✅ **Termux + File Manager** (recommended)
- ✅ **USB OTG Helper** (better USB access)
- ✅ **Solid Explorer** (powerful file manager)

**When to use EtchDroid:**
- If you want a bootable ARK USB (advanced)
- Create disk image on desktop first
- Transfer to Android
- Write with EtchDroid

---

## 🎯 **One-Line Install**

Copy-paste this into Termux:

```bash
pkg update && pkg install wget -y && termux-setup-storage && cd ~/storage/shared/Download && wget https://raw.githubusercontent.com/Superman08091992/ark/master/ark-installer && chmod +x ark-installer && ./ark-installer --help
```

Then run:
```bash
./ark-installer usb ./my-ark-usb
```

---

## 🆘 **Troubleshooting**

### "Permission denied"

```bash
# Make sure you ran:
termux-setup-storage

# Grant storage permission:
# Settings → Apps → Termux → Permissions → Storage → Allow
```

### "Command not found"

```bash
# Make sure you're in the right folder:
cd ~/storage/shared/Download
ls -la ark-installer

# Make executable:
chmod +x ark-installer

# Run with ./
./ark-installer --help
```

### "Can't access USB"

- Android restricts direct USB writes
- **Solution:** Use file manager to copy files
- No root needed, works every time!

---

## 📚 **Full Guide**

For complete details, see: **`TERMUX_ETCHDROID_GUIDE.md`**

---

## ✅ **Summary**

| Question | Answer |
|----------|--------|
| **Works in Termux?** | ✅ Yes! Perfectly |
| **Needs root?** | ❌ No |
| **Can create USB nodes?** | ✅ Yes |
| **EtchDroid needed?** | ❌ No (use file manager) |
| **OTG adapter needed?** | ✅ Yes (to connect USB) |
| **Installation time?** | ⏱️ ~3 minutes total |

---

## 🎉 **You're Ready!**

Download Termux → Run installer → Copy to USB → Done!

**Repository:** https://github.com/Superman08091992/ark

**Questions?** Open issue: https://github.com/Superman08091992/ark/issues

---

**Last Updated:** 2025-11-08
