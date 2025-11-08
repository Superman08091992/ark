# ARK Installation via Termux + EtchDroid

Complete guide for installing ARK on Android using Termux and creating bootable USB with EtchDroid.

---

## 🤔 **Can You Use ark-installer in Termux?**

### ✅ **YES! It Works!**

The `ark-installer` is a **bash script**, and Termux provides a full Linux environment on Android. You can:

1. ✅ Download `ark-installer` in Termux
2. ✅ Make it executable (`chmod +x`)
3. ✅ Run it to create USB nodes
4. ✅ Extract files for inspection

### ⚠️ **Limitations on Android:**

1. **USB access limited:**
   - Android restricts direct USB device access
   - Can't format/partition USB like on desktop Linux
   - Need to use EtchDroid or similar apps for USB writing

2. **No systemd:**
   - `sudo ./ark-installer host` won't work (no systemd on Android)
   - Can run ARK services manually in Termux
   - Can't auto-start services on boot (without root)

3. **No root needed for USB node creation:**
   - Creating USB node files works fine
   - Just can't write directly to USB device
   - Workaround: Create in Termux, copy to USB with file manager

---

## 📱 **Method 1: Termux + File Manager (Recommended)**

This method works on **non-rooted** Android phones.

### Step 1: Install Termux

1. **Download Termux from F-Droid** (recommended)
   - https://f-droid.org/packages/com.termux/
   - **NOT from Google Play** (outdated version)

2. **Or download APK directly:**
   - https://github.com/termux/termux-app/releases
   - Install `termux-app_v*.apk`

### Step 2: Setup Termux

```bash
# Update packages
pkg update && pkg upgrade -y

# Install required tools
pkg install wget curl git bash nano openssh openssl -y

# Enable storage access (IMPORTANT!)
termux-setup-storage
# Grant permission when prompted
```

### Step 3: Download ark-installer

```bash
# Navigate to shared storage
cd ~/storage/shared/Download

# Download ark-installer
wget https://raw.githubusercontent.com/Superman08091992/ark/master/ark-installer

# Make executable
chmod +x ark-installer

# Verify it works
./ark-installer --help
```

### Step 4: Create USB Node Files

```bash
# Create USB node in a directory
./ark-installer usb ./my-ark-usb

# This creates:
# my-ark-usb/
#   ├── ark/
#   │   ├── identity/
#   │   │   ├── operator_id
#   │   │   ├── operator_key
#   │   │   └── operator_key.pub
#   │   └── manifest.json
```

### Step 5: Copy to USB via File Manager

1. **Connect USB drive** to Android (via OTG adapter)
2. **Open file manager** (Files by Google, Solid Explorer, etc.)
3. **Navigate to:** `Internal Storage/Download/my-ark-usb/`
4. **Copy entire folder** to USB drive
5. **Done!** Your USB is now an ARK identity node

---

## 🔥 **Method 2: EtchDroid (Create Bootable USB)**

EtchDroid writes raw disk images to USB drives. You can create a bootable ARK USB.

### What is EtchDroid?

- **App:** https://play.google.com/store/apps/details?id=eu.depau.etchdroid
- **Purpose:** Write ISO/IMG files to USB (like Rufus on Windows)
- **Supports:** RAW images, ISO files, compressed archives
- **No root required**

### Limitations for ARK:

❌ **EtchDroid writes disk images, not files**
- `ark-installer` creates file structures, not disk images
- EtchDroid is for bootable USB (OS installers, live Linux)
- ARK USB nodes are just files, not bootable images

### Workaround: Create IMG File First

If you want a bootable ARK USB via EtchDroid:

#### Option A: Create on Desktop, Transfer to Android

```bash
# On Linux/Mac desktop:

# Create disk image
dd if=/dev/zero of=ark-usb.img bs=1M count=64
mkfs.ext4 ark-usb.img

# Mount and populate
mkdir /tmp/ark-mount
sudo mount -o loop ark-usb.img /tmp/ark-mount
./ark-installer usb /tmp/ark-mount
sudo umount /tmp/ark-mount

# Transfer ark-usb.img to Android
# Use EtchDroid to write it to USB
```

#### Option B: Use Alternative Apps

Instead of EtchDroid, use apps that support file copying:

1. **DriveDroid** (root required)
   - Create bootable images
   - Mount phone storage as USB

2. **USB OTG Helper** (no root)
   - Better file-level USB access
   - Can format and copy files

3. **MiXplorer** (no root)
   - File manager with USB support
   - Can copy files directly

---

## 🚀 **Method 3: Run ARK Host in Termux**

You can run ARK services directly in Termux (no USB needed).

### Install Dependencies

```bash
# Update Termux
pkg update && pkg upgrade -y

# Install Node.js
pkg install nodejs -y

# Install Redis (if needed by ARK)
pkg install redis -y

# Install Python (if needed)
pkg install python -y

# Clone ARK repository
cd ~
git clone https://github.com/Superman08091992/ark.git
cd ark

# Extract installer contents
./ark-installer extract ./ark-files
cd ark-files
```

### Run ARK Services

```bash
# Start Redis (in background)
redis-server &

# Run ARK backend
node intelligent-backend.cjs

# Or if using Python components
python3 -m http.server 8080
```

### Access ARK

```bash
# From Android browser
http://localhost:8080

# Share with ngrok (if installed in Termux)
pkg install ngrok -y
ngrok http 8080
```

---

## 📋 **Complete Workflow: Termux + USB**

### Scenario: Create ARK USB Node on Android

```bash
# 1. Install Termux (F-Droid)
# 2. Setup Termux
pkg update && pkg upgrade -y
pkg install wget -y
termux-setup-storage

# 3. Download ark-installer
cd ~/storage/shared/Download
wget https://raw.githubusercontent.com/Superman08091992/ark/master/ark-installer
chmod +x ark-installer

# 4. Create USB node
./ark-installer usb ./my-ark-usb

# 5. Verify creation
ls -la my-ark-usb/ark/identity/
cat my-ark-usb/ark/identity/operator_id

# 6. Copy to USB using file manager
# Connect USB → Open Files app → Copy my-ark-usb folder to USB

# 7. Done! USB is now an ARK identity node
```

---

## 🔧 **Troubleshooting**

### "Permission denied" when accessing USB

```bash
# Make sure you ran:
termux-setup-storage

# Grant storage permission in Android settings
# Settings → Apps → Termux → Permissions → Storage → Allow
```

### "Cannot write to USB device"

- Android restricts direct USB writes without root
- **Solution:** Use file manager to copy files
- **Alternative:** Use USB OTG Helper app

### "ark-installer: not found"

```bash
# Make sure you're in the right directory
cd ~/storage/shared/Download
ls -la ark-installer

# Make executable
chmod +x ark-installer

# Run with ./
./ark-installer --help
```

### EtchDroid says "Invalid image"

- EtchDroid expects ISO/IMG files
- `ark-installer` is a bash script, not an image
- **Solution:** Use Method 1 (file manager) instead

### Want to create disk image for EtchDroid

```bash
# In Termux (requires root or use desktop)
# Create 64MB image
dd if=/dev/zero of=ark-usb.img bs=1M count=64

# Format (needs root or desktop Linux)
# Transfer to desktop for formatting
```

---

## 🎯 **Recommended Setup**

### For Non-Rooted Android:

1. **Install Termux** from F-Droid
2. **Download ark-installer** in Termux
3. **Create USB node** with `./ark-installer usb`
4. **Copy to USB** using Files app
5. ✅ Done!

### For Rooted Android:

1. **Install Termux**
2. **Install BusyBox** (better Linux tools)
3. **Direct USB access** possible
4. **Run as host** with full services

### For Bootable USB:

1. **Use desktop** Linux/Mac to create image
2. **Transfer IMG** to Android
3. **Use EtchDroid** to write image
4. Or skip EtchDroid - ARK doesn't need bootable USB

---

## 📱 **Apps You Need**

| App | Purpose | Root? | Link |
|-----|---------|-------|------|
| **Termux** | Linux environment | No | https://f-droid.org/packages/com.termux/ |
| **Files by Google** | USB file manager | No | Google Play Store |
| **Solid Explorer** | Advanced file manager | No | Google Play Store |
| **EtchDroid** | Write disk images | No | Google Play Store |
| **USB OTG Helper** | USB access | No | Google Play Store |
| **DriveDroid** | Mount as USB | Yes | Google Play Store |

---

## ✅ **Summary**

### Can you run ark-installer in Termux?
**YES!** ✅ Works perfectly for:
- Downloading the installer
- Creating USB node files
- Extracting contents
- Running ARK services locally

### Can you use EtchDroid?
**Limited** ⚠️ Because:
- EtchDroid writes disk images (ISO/IMG)
- ark-installer creates file structures
- ARK doesn't need bootable USB

### Best method?
**Termux + File Manager** 🎯
1. Create USB node in Termux
2. Copy files to USB with file manager
3. Simple, no root needed, works every time

---

## 🚀 **Quick Start Command**

```bash
# One-line setup in Termux:
pkg update && pkg install wget -y && termux-setup-storage && cd ~/storage/shared/Download && wget https://raw.githubusercontent.com/Superman08091992/ark/master/ark-installer && chmod +x ark-installer && ./ark-installer --help

# Create USB node:
./ark-installer usb ./my-ark-usb

# Then use file manager to copy to USB!
```

---

**Need help?** Open issue: https://github.com/Superman08091992/ark/issues

**Last Updated:** 2025-11-08
