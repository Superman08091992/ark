# ARK Quick Start Guide

## 🚀 Deploy to Production (Netlify)

### One-Time Setup (5 minutes)

1. **Go to Netlify:** https://app.netlify.com/signup
2. **Sign up with GitHub** (authorize access)
3. **Import project:**
   - Click "Add new site" → "Import an existing project"
   - Choose GitHub → Select `Superman08091992/ark`
   - Build settings:
     - Build command: `npm run build`
     - Publish directory: `dist`
   - Click "Deploy site"
4. **Done!** Your site is live at `https://your-site-name.netlify.app`

### Auto-Deploy (Every Push)

```bash
# Make changes
git add .
git commit -m "feat: New feature"
git push origin master

# Netlify automatically deploys (2-3 minutes)
```

**Monitor:** https://app.netlify.com → Your site → Deploys

---

## ⚡ Quick Testing (ngrok)

### One-Time Setup (2 minutes)

```bash
# Install ngrok (choose your OS)
brew install ngrok                    # macOS
sudo apt install ngrok                # Linux
choco install ngrok                   # Windows

# Get authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
ngrok config add-authtoken YOUR_TOKEN_HERE
```

### Every Use (30 seconds)

```bash
# Terminal 1: Start dev server
npm run dev

# Terminal 2: Start tunnel
npm run ngrok

# Share the URL: https://xyz123.ngrok.io
```

**Inspector:** http://localhost:4040 (see all requests)

---

## 📥 Download Installer

### GitHub Download

1. Go to: https://github.com/Superman08091992/ark
2. Click `ark-installer` file
3. Click "Download raw file"
4. Save to your computer

### Git Clone

```bash
git clone https://github.com/Superman08091992/ark.git
cd ark
ls -lh ark-installer  # 67KB file
```

### Use Installer

```bash
chmod +x ark-installer

# Create USB node only
./ark-installer --usb /path/to/usb

# Create host installer only
./ark-installer --host-installer

# Create both
./ark-installer --both /path/to/usb
```

---

## 🛠️ Development Commands

```bash
npm run dev              # Start development server (localhost:4321)
npm run build            # Build for production
npm run preview          # Preview production build locally
npm run ngrok            # Share local dev with ngrok tunnel
npm run deploy           # Deploy to Netlify (production)
npm run deploy:preview   # Deploy to Netlify (preview URL)
```

---

## 📚 Full Documentation

- **Deployment:** See `DEPLOYMENT_GUIDE.md`
- **Installer:** See `INSTALLER_SUMMARY.md`
- **Storage:** See `LOCAL_STORAGE_INFO.md`
- **Supabase:** See `REMOVE_SUPABASE_GUIDE.md` (if needed)

---

## 🆘 Troubleshooting

### Netlify build fails
```bash
# Check build logs in Netlify dashboard
# Clear cache: Deploys → Options → Clear cache and deploy
```

### ngrok "authtoken not configured"
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

### Port already in use
```bash
lsof -ti:4321 | xargs kill -9
npm run dev
```

---

## 🎯 What You Get

✅ **Single-file installer** (`ark-installer` - 67KB)  
✅ **Local NVMe storage** (no database needed)  
✅ **Python 3.12 compatible** (all dependencies working)  
✅ **Netlify auto-deploy** (push to deploy)  
✅ **ngrok quick sharing** (instant tunnel)  
✅ **Clean repository** (single master branch)

---

**Need more help?** Open an issue: https://github.com/Superman08091992/ark/issues

**Latest commit:** a57210b  
**Last updated:** 2025-11-08
