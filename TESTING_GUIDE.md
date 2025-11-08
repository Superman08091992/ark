# ARK Unified Installer - Testing Guide

## 🧪 Testing the Fixed Installer

### ✅ What Was Fixed

1. **`/tmp` Permission Error** - Now writes directly to shell RC file (Termux compatible)
2. **Silent Copy Failures** - Now shows status and warns about missing directories
3. **Missing docs Directory** - Added to directory creation list
4. **Launcher Script Verification** - Validates scripts created and executable
5. **Post-Install Verification** - Checks all critical files and binaries

---

## 📋 Test Plan

### **Test 1: Clean Termux Installation**

**Purpose:** Verify installer works on Android/Termux from scratch

**Steps:**
```bash
# 1. Pull latest code
cd ~/ark
git pull origin master

# 2. Create unified package
./create-unified-ark.sh

# Output should show:
# - ✅ Components collected
# - ✅ Installer created
# - ✅ README created
# - ✅ Package created

# 3. Extract and test in clean location
rm -rf ~/ark-test-clean
mkdir -p ~/ark-test-clean
tar -xzf ark-complete-*.tar.gz -C ~/ark-test-clean

# 4. Run installer
cd ~/ark-test-clean/ark-unified
./install.sh ~/ark-install-test

# Expected output:
# ╔═══════════════════════════════════════╗
# ║    ARK Unified Installer v1.0.0      ║
# ╚═══════════════════════════════════════╝
#
# 📋 Detected OS: android
# 📁 Installation directory: /data/data/.../ark-install-test
#
# 1️⃣ Installing dependencies...
#    ✅ Using bundled Node.js
#    ✅ Using bundled Redis
#
# 2️⃣ Creating installation directory...
#
# 3️⃣ Copying ARK files...
#    ✅ Copied lib/ directory
#    ℹ️ Note: data/ directory empty (will be created on first run)
#    ✅ Copied docs/ directory
#    ✅ Copied bundled dependencies
#
# 4️⃣ Creating launcher scripts...
#
# 🔍 Verifying launcher scripts...
#    ✅ ark created and executable
#    ✅ ark-redis created and executable
#
# 5️⃣ Creating configuration...
#
# 6️⃣ Setting up PATH...
#    ✅ Added ARK to /data/data/.../files/home/.bashrc
#
# 7️⃣ Verifying installation...
#    ✅ ark
#    ✅ ark-redis
#    ✅ ark.conf
#    ✅ Node.js (v20.10.0)
#    ✅ Redis (Redis server v=7.2.4)
#
# ╔═══════════════════════════════════════╗
# ║   ✅ ARK INSTALLATION COMPLETE! ✅   ║
# ╚═══════════════════════════════════════╝
```

**Expected Results:**
- ✅ No `/tmp` permission errors
- ✅ All steps complete successfully
- ✅ Launcher scripts created in `bin/` directory
- ✅ PATH added to `~/.bashrc` without errors
- ✅ All verification checks pass

**Verify Installation:**
```bash
# 5. Check launcher scripts exist
ls -l ~/ark-install-test/bin/
# Should show:
# - ark (executable)
# - ark-redis (executable)
# - ark-web (if frontend exists)

# 6. Test launchers directly
~/ark-install-test/bin/ark-redis --version
# Should output: Redis server v=7.2.4 ...

~/ark-install-test/bin/ark --version || echo "Backend script exists"
# May fail if intelligent-backend.cjs missing, but script should exist

# 7. Verify PATH was added
grep ARK_HOME ~/.bashrc
# Should show:
# export PATH="/data/data/.../ark-install-test/bin:$PATH"
# export ARK_HOME="/data/data/.../ark-install-test"

# 8. Source bashrc and test commands
source ~/.bashrc
which ark
which ark-redis
# Both should show paths in ~/ark-install-test/bin/
```

---

### **Test 2: Raspberry Pi Installation** (When Available)

**Purpose:** Verify installer works on Raspberry Pi with sudo

**Prerequisites:**
- Raspberry Pi running Raspberry Pi OS (Debian-based)
- sudo access
- Transfer `ark-complete-*.tar.gz` to Pi

**Steps:**
```bash
# 1. Extract package
tar -xzf ark-complete-*.tar.gz
cd ark-unified

# 2. Run installer with sudo
sudo ./install.sh

# Expected: Installation to /opt/ark (default)

# 3. Verify system installation
ls -l /opt/ark/
sudo /opt/ark/bin/ark-redis --version
sudo /opt/ark/bin/ark --version || echo "Backend script exists"

# 4. Check PATH added for all users
grep ARK_HOME /root/.bashrc

# 5. Test as regular user
ark-redis --version
ark --version || echo "Backend script exists"
```

**Expected Results:**
- ✅ Installation to `/opt/ark/` succeeds
- ✅ All files owned by root
- ✅ Executables work system-wide
- ✅ PATH added to appropriate shell RC file

---

### **Test 3: Missing Dependencies Scenario**

**Purpose:** Test installer behavior when components are missing

**Steps:**
```bash
# 1. Create package without some components
cd ~/ark
./create-unified-ark.sh

# 2. Manually remove a component from extracted archive
tar -xzf ark-complete-*.tar.gz
cd ark-unified
rm -rf lib/*   # Simulate missing backend

# 3. Run installer
./install.sh ~/ark-test-missing

# Expected output should include:
# ⚠️ Warning: lib/ directory empty or missing
# This may cause ARK to not function properly!

# 4. Verify installation still completes but with warnings
```

**Expected Results:**
- ✅ Installer shows warnings for missing components
- ✅ Still creates directory structure
- ✅ Verification step may fail if critical files missing

---

### **Test 4: Existing Installation Upgrade**

**Purpose:** Verify installer can upgrade existing installation

**Steps:**
```bash
# 1. Install version 1
./install.sh ~/ark-upgrade-test

# 2. Verify installation works
~/ark-upgrade-test/bin/ark-redis --version

# 3. Run installer again to same location
./install.sh ~/ark-upgrade-test

# 4. Check if PATH entry duplicated
grep -c ARK_HOME ~/.bashrc
# Should show 1, not 2 (installer checks for existing entry)
```

**Expected Results:**
- ✅ Installer updates existing files
- ✅ Does not duplicate PATH entries in shell RC
- ✅ Preserves user data in `data/` directory

---

### **Test 5: Permission Scenarios**

**Purpose:** Test installer with various permission configurations

**Termux Tests:**
```bash
# Test A: Install to writable user directory
./install.sh ~/ark-perms-test
# Expected: ✅ Success

# Test B: Install to read-only directory (if possible)
mkdir ~/ark-readonly
chmod 555 ~/ark-readonly
./install.sh ~/ark-readonly/ark
# Expected: ❌ Error (cannot create directory)
chmod 755 ~/ark-readonly  # Cleanup
```

**Raspberry Pi Tests:**
```bash
# Test C: Install to system directory without sudo
./install.sh /opt/ark
# Expected: ❌ Re-runs with sudo OR shows error

# Test D: Install to system directory with sudo
sudo ./install.sh
# Expected: ✅ Success
```

---

## 🐛 Common Issues & Solutions

### Issue: "lib/ directory empty or missing"

**Cause:** Backend files not copied to unified package

**Solution:**
```bash
# Verify source files exist
ls -la ~/ark/*.cjs
ls -la ~/ark/agents/

# Re-run package creation
cd ~/ark
./create-unified-ark.sh
```

---

### Issue: "ark command not found" after installation

**Cause:** PATH not updated in current shell session

**Solution:**
```bash
# Option 1: Source shell RC file
source ~/.bashrc

# Option 2: Use full path
~/ark-install-test/bin/ark

# Option 3: Restart terminal
```

---

### Issue: "Node.js binary not executable"

**Cause:** File permissions not preserved during extraction

**Solution:**
```bash
# Fix permissions
chmod +x ~/ark-install-test/deps/node/nodejs/bin/*
chmod +x ~/ark-install-test/deps/redis/bin/*
```

---

### Issue: Redis won't start with "Address already in use"

**Cause:** Redis already running on port 6379

**Solution:**
```bash
# Check for existing Redis
ps aux | grep redis-server

# Kill existing Redis
pkill redis-server

# Or use different port
ark-redis --port 6380
```

---

## ✅ Success Criteria

Installation is successful if ALL of the following are true:

1. **No Errors During Installation**
   - ✅ No `/tmp` permission denied errors
   - ✅ No file copy failures
   - ✅ No directory creation errors

2. **All Files Present**
   - ✅ `bin/ark` exists and is executable
   - ✅ `bin/ark-redis` exists and is executable
   - ✅ `config/ark.conf` exists
   - ✅ `deps/node/nodejs/bin/node` exists (if bundled)
   - ✅ `deps/redis/bin/redis-server` exists (if bundled)

3. **Verification Passes**
   - ✅ All 7 installation steps complete
   - ✅ Verification step shows all ✅ checkmarks
   - ✅ Node.js version displayed
   - ✅ Redis version displayed

4. **Functionality Works**
   - ✅ Can execute `ark-redis --version` successfully
   - ✅ Launcher scripts in PATH after sourcing shell RC
   - ✅ No duplicate PATH entries in shell RC file

---

## 📊 Test Results Template

Use this template to report test results:

```markdown
## Test Results

**Date:** [YYYY-MM-DD]
**Platform:** [Termux/Raspberry Pi/Linux/macOS]
**OS Version:** [e.g., Android 13, Raspberry Pi OS 11]

### Test 1: Clean Installation
- Status: [PASS/FAIL]
- Notes: 
  - [Any observations]
  - [Issues encountered]

### Test 2: Verification Steps
- `ark` script created: [YES/NO]
- `ark-redis` script created: [YES/NO]
- Node.js works: [YES/NO]
- Redis works: [YES/NO]
- PATH updated: [YES/NO]

### Test 3: Functionality
- Can start Redis: [YES/NO]
- Can execute `ark` command: [YES/NO]
- Configuration file exists: [YES/NO]

### Issues Found
1. [Issue description]
   - Error message: [Exact error text]
   - Steps to reproduce: [Detailed steps]

### Overall Result: [PASS/FAIL]
```

---

## 🚀 Next Steps After Testing

Once all tests pass:

1. **Tag Release**
   ```bash
   cd ~/ark
   git tag -a v1.0.0 -m "First stable release with fixed installer"
   git push origin v1.0.0
   ```

2. **Create GitHub Release**
   - Upload `ark-complete-YYYYMMDD.tar.gz` as release asset
   - Include installation instructions
   - Document known limitations

3. **Deploy to Raspberry Pi**
   - Transfer package to Pi
   - Run installation
   - Set up auto-start services

4. **Documentation**
   - Update main README with installation instructions
   - Create troubleshooting guide
   - Add video/GIF demonstrations

---

## 📝 Reporting Issues

If you encounter problems during testing:

1. **Capture Full Output**
   ```bash
   ./install.sh ~/ark-test 2>&1 | tee install.log
   ```

2. **Collect System Info**
   ```bash
   uname -a > system-info.txt
   echo "Shell: $SHELL" >> system-info.txt
   echo "PATH: $PATH" >> system-info.txt
   ```

3. **List Installation Directory**
   ```bash
   ls -laR ~/ark-test > directory-listing.txt
   ```

4. **Create GitHub Issue** with:
   - Test scenario that failed
   - Full installation log
   - System information
   - Expected vs actual behavior

---

**Good luck with testing!** 🎯

The fixes should resolve the `/tmp` permission issue and create fully functional launcher scripts on both Termux and Raspberry Pi.
