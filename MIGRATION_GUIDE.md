# ARK Monorepo Migration Guide

## ✅ **Backup Created**

Your current code is safely backed up:
- Location: `/home/user/ark-backup-20251108-222655.tar.gz`
- Size: 8.9MB
- Includes: All code (excluding node_modules, .git, deps, venv)

---

## 🎯 **What Will Happen**

The migration script will reorganize your project from this:

### **Before (Current Mess):**
```
ark/
├── src/                    # Mixed frontend
├── frontend/               # Another frontend?
├── backend/                # Backend stuff
├── agents/                 # Agents
├── *.cjs files everywhere  # Backend scattered
├── knowledge_base/         # Data mixed in
├── 50+ .md files           # Docs everywhere
└── scripts scattered
```

### **After (Clean Monorepo):**
```
ark/
├── apps/
│   ├── web/                # 🎨 Frontend (Astro + React)
│   │   ├── src/
│   │   ├── public/
│   │   └── package.json
│   └── api/                # ⚙️  Backend (Node.js + Express)
│       ├── src/
│       └── package.json
│
├── packages/
│   └── shared/             # 📦 Shared code
│       └── src/
│
├── agents/                 # 🤖 AI Agents
│   ├── kyle/
│   └── joey/
│
├── data/                   # 💾 All data in one place
│   ├── knowledge_base/
│   ├── kyle_infinite_memory/
│   └── agent_logs/
│
├── scripts/                # 🔧 All scripts organized
│   ├── install-ark-host.sh
│   └── create-ark-installer.sh
│
├── docs/                   # 📚 All docs together
│   ├── guides/
│   └── api/
│
├── deps/                   # 📦 Bundled dependencies
│   ├── node/
│   └── redis/
│
├── package.json            # Root workspace config
├── pnpm-workspace.yaml     # Workspace definition
└── turbo.json              # Build orchestration
```

---

## 🚀 **Run the Migration**

```bash
cd ~/ark  # or /home/user/webapp

# Run migration script
./migrate-to-monorepo.sh

# Confirm when prompted
# Script will:
# 1. Create additional backup
# 2. Create new structure
# 3. Move files to correct locations
# 4. Create workspace configs
# 5. Update package.json files
```

---

## ⏱️ **Migration Time**

Estimated: ~2 minutes

---

## 🔍 **After Migration**

### **1. Verify Structure**
```bash
ls -la
# Should see: apps/, packages/, agents/, data/, scripts/, docs/
```

### **2. Install Dependencies**
```bash
# Install pnpm if not installed
npm install -g pnpm

# Install all workspace dependencies
pnpm install
```

### **3. Test Frontend**
```bash
# Start frontend dev server
cd apps/web
pnpm dev

# Should start on http://localhost:4321
```

### **4. Test Backend**
```bash
# In another terminal
cd apps/api
pnpm dev

# Backend should start
```

### **5. Test Full Stack**
```bash
# From root directory
pnpm dev

# Starts both frontend and backend!
```

---

## 📊 **Benefits of New Structure**

| Before | After |
|--------|-------|
| Files scattered everywhere | Clean organization |
| Hard to find things | Everything in its place |
| Confusing structure | Clear app boundaries |
| Multiple node_modules | Shared dependencies |
| Manual coordination | Turbo orchestrates builds |
| Complex deployment | One command deploys all |

---

## 🔧 **New Workflow**

### **Development**
```bash
# Start everything
pnpm dev

# Or start individually
pnpm --filter @ark/web dev      # Frontend only
pnpm --filter @ark/api dev      # Backend only
```

### **Building**
```bash
# Build everything
pnpm build

# Frontend builds to: apps/web/dist/
# Backend ready to run: apps/api/src/
```

### **Deployment**
```bash
# Deploy to Netlify
pnpm deploy

# Or
cd apps/web && netlify deploy --prod
```

---

## 🆘 **If Something Goes Wrong**

### **Restore from Backup**
```bash
# Go to parent directory
cd /home/user

# Remove current directory
rm -rf webapp/

# Extract backup
tar -xzf ark-backup-20251108-222655.tar.gz
```

### **Rollback Git Changes**
```bash
# If you committed
git reset --hard HEAD~1

# If you didn't commit yet
git checkout .
git clean -fd
```

---

## ✅ **Post-Migration Checklist**

- [ ] Run `./migrate-to-monorepo.sh`
- [ ] Verify new structure exists
- [ ] Run `pnpm install`
- [ ] Test `pnpm dev` (both apps start)
- [ ] Test `pnpm build` (both apps build)
- [ ] Check frontend works (http://localhost:4321)
- [ ] Check backend works
- [ ] Commit changes
- [ ] Push to GitHub
- [ ] Deploy to Netlify

---

## 🎉 **Ready to Deploy**

After migration, your monorepo is production-ready:

```bash
# Build everything
pnpm build

# Deploy frontend to Netlify
cd apps/web
netlify deploy --prod

# Backend can run on your server
cd apps/api
node src/intelligent-backend.cjs
```

---

## 📝 **Migration Command**

```bash
./migrate-to-monorepo.sh
```

**That's it!** The script does everything automatically. ✨

---

**Ready when you are!** 🚀
