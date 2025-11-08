# ARK Deployment Guide

Complete guide for deploying ARK using **Netlify** (production) or **ngrok** (quick testing).

---

## 🚀 Option 1: Netlify Deployment (Recommended for Production)

Netlify is perfect for static sites like ARK. It's free, fast, and has excellent CI/CD.

### Prerequisites

- GitHub account with ARK repository
- Netlify account (free tier is enough)

### Step-by-Step Setup

#### 1. Create Netlify Account

1. Go to: **https://app.netlify.com/signup**
2. Sign up with GitHub (recommended)
3. Authorize Netlify to access your repositories

#### 2. Create New Site

1. Click **"Add new site"** → **"Import an existing project"**
2. Choose **GitHub** as your Git provider
3. Select your **ARK repository** (Superman08091992/ark)
4. Configure build settings:

```
Build command:    npm run build
Publish directory: dist
```

5. Click **"Deploy site"**

#### 3. Configure Site Settings (Optional)

1. **Change site name:**
   - Site settings → General → Site details
   - Click "Change site name"
   - Example: `ark-system` → `ark-system.netlify.app`

2. **Add custom domain (if you have one):**
   - Site settings → Domain management
   - Add custom domain and follow DNS instructions

3. **Environment variables (if needed):**
   - Site settings → Environment variables
   - Add any secrets (none required for basic setup)

#### 4. Automatic Deployments

Netlify automatically deploys when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "feat: Add new feature"
git push origin master

# Netlify detects push and deploys automatically (2-3 minutes)
```

#### 5. Monitor Deployments

1. Go to: **https://app.netlify.com**
2. Click your site
3. View **"Deploys"** tab
4. See build logs, preview, and live URL

### Netlify CLI (Optional)

For local testing and manual deploys:

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Link your site
netlify link

# Test build locally
netlify build

# Deploy to preview
npm run deploy:preview

# Deploy to production
npm run deploy

# Run local dev server with Netlify functions
npm run netlify:dev
```

### Netlify Features You Get

✅ **Automatic HTTPS** - SSL certificates included  
✅ **CDN** - Global edge network  
✅ **Atomic deploys** - Zero downtime  
✅ **Instant rollback** - One-click revert  
✅ **Deploy previews** - Test before production  
✅ **Form handling** - Built-in forms (if needed)  
✅ **Edge functions** - Serverless at the edge  
✅ **Analytics** - Traffic insights (paid feature)

---

## ⚡ Option 2: ngrok (Quick Local Testing)

ngrok creates a secure tunnel to your local server. Perfect for:

- Quick demos
- Testing on mobile devices
- Sharing work-in-progress
- Webhook testing
- No deployment needed

### Prerequisites

```bash
# macOS (Homebrew)
brew install ngrok

# Linux (Ubuntu/Debian)
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Windows (Chocolatey)
choco install ngrok

# Or download directly
# https://ngrok.com/download
```

### Setup ngrok

1. **Sign up for free:** https://dashboard.ngrok.com/signup
2. **Get your authtoken:** https://dashboard.ngrok.com/get-started/your-authtoken
3. **Configure authtoken:**

```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

### Quick Start

#### Method 1: Using the provided script (easiest)

```bash
# Terminal 1: Start your development server
npm run dev

# Terminal 2: Start ngrok tunnel
npm run ngrok
# or
./start-ngrok.sh

# You'll see output like:
# Forwarding: https://abc123.ngrok.io -> http://localhost:4321
```

#### Method 2: Direct ngrok command

```bash
# Start dev server
npm run dev

# In another terminal, start ngrok
ngrok http 4321

# Custom subdomain (requires paid plan)
ngrok http 4321 --subdomain=ark-dev

# With custom domain (requires paid plan)
ngrok http 4321 --domain=ark.yourdomain.com
```

#### Method 3: Using config file

```bash
# Edit ngrok-config.yml with your authtoken
nano ngrok-config.yml

# Start tunnel using config
ngrok start --config=ngrok-config.yml ark-web
```

### ngrok Web Interface

ngrok provides a web interface at: **http://localhost:4040**

Features:
- **Request inspector** - See all HTTP requests
- **Replay requests** - Resend requests for testing
- **Status** - Connection status and metrics
- **Logs** - Detailed tunnel logs

### ngrok Advanced Features

#### Multiple Tunnels

```bash
# Start multiple services
ngrok start --config=ngrok-config.yml ark-web ark-api
```

#### Custom Headers

```bash
ngrok http 4321 --host-header=rewrite
```

#### Basic Auth Protection

```bash
ngrok http 4321 --basic-auth "user:password"
```

#### IP Restrictions (paid plans)

```bash
ngrok http 4321 --cidr-allow 1.2.3.4/32
```

### ngrok Pricing

- **Free:** 1 agent, random URLs, 40 connections/min
- **Personal ($10/mo):** Custom subdomains, more connections
- **Pro ($20/mo):** Custom domains, IP whitelisting
- **Business ($40/mo):** Multiple users, SSO

**For most use cases, the free tier is enough!**

---

## 📊 Comparison: Netlify vs ngrok

| Feature | Netlify | ngrok |
|---------|---------|-------|
| **Use Case** | Production hosting | Quick testing/demos |
| **Setup Time** | 5 minutes (one-time) | 30 seconds (each time) |
| **Uptime** | 24/7 | Only when running |
| **URL** | Permanent (ark.netlify.app) | Temporary (changes each time) |
| **SSL/HTTPS** | ✅ Automatic | ✅ Automatic |
| **Cost** | Free (generous limits) | Free (basic features) |
| **CDN** | ✅ Global | ❌ Direct tunnel |
| **Auto-deploy** | ✅ On git push | ❌ Manual |
| **Best For** | Public production site | Development/testing |

---

## 🔧 Troubleshooting

### Netlify Issues

**Build fails:**
```bash
# Check build logs in Netlify dashboard
# Common fixes:

# 1. Clear cache and retry
# Deploys → Options → Clear cache and deploy

# 2. Check Node version
# netlify.toml already sets NODE_VERSION = "20"

# 3. Verify build command works locally
npm run build
```

**404 errors:**
```bash
# Make sure dist/ directory is being created
ls -la dist/

# Check publish directory in netlify.toml
# Should be: publish = "dist"
```

**Large files excluded:**
```bash
# Check .netlifyignore
# Add files that should be excluded
```

### ngrok Issues

**"Authtoken not configured":**
```bash
# Add your authtoken
ngrok config add-authtoken YOUR_TOKEN_HERE
```

**"Port already in use":**
```bash
# Change port or kill existing process
lsof -ti:4321 | xargs kill -9
npm run dev
```

**"Connection refused":**
```bash
# Make sure dev server is running first
npm run dev
# Then start ngrok in another terminal
npm run ngrok
```

**Random URL changes:**
```bash
# Upgrade to paid plan for custom subdomain
# Or use free random URLs (they change each restart)
```

---

## 🎯 Recommended Workflow

### For Development

```bash
# Start dev server
npm run dev

# Quick share with ngrok
npm run ngrok
```

### For Staging/Production

```bash
# Make changes
git add .
git commit -m "feat: Add feature"
git push origin master

# Netlify auto-deploys in 2-3 minutes
# Check: https://app.netlify.com
```

### For Demos

**Option A (ngrok - quick):**
```bash
npm run dev
npm run ngrok
# Share the ngrok URL
```

**Option B (Netlify - professional):**
```bash
# Use deploy previews
git checkout -b feature/demo
# Make changes
git push origin feature/demo
# Get preview URL from Netlify
```

---

## 📝 Quick Reference

### Netlify Commands

```bash
npm run build              # Build for production
npm run deploy:preview     # Deploy to preview URL
npm run deploy             # Deploy to production
npm run netlify:dev        # Local dev with Netlify features
```

### ngrok Commands

```bash
npm run ngrok              # Start tunnel (default port 4321)
npm run ngrok:port 8080    # Start tunnel on custom port
./start-ngrok.sh 3000      # Direct script with port
```

### URLs

- **Netlify Dashboard:** https://app.netlify.com
- **ngrok Dashboard:** https://dashboard.ngrok.com
- **ngrok Inspector:** http://localhost:4040
- **Your Site:** (will be assigned after setup)

---

## 🔐 Security Notes

### Netlify
- ✅ Automatic HTTPS
- ✅ Security headers configured in `netlify.toml`
- ✅ DDoS protection included
- ✅ No sensitive data in repository (use environment variables)

### ngrok
- ✅ Encrypted tunnel (HTTPS)
- ⚠️ Temporary - URLs expire when tunnel closes
- ⚠️ Free tier URLs are discoverable (use basic auth if needed)
- ⚠️ Don't share tunnel URLs publicly for production use

---

## 📞 Support

### Netlify
- **Docs:** https://docs.netlify.com
- **Community:** https://answers.netlify.com
- **Status:** https://www.netlifystatus.com

### ngrok
- **Docs:** https://ngrok.com/docs
- **Support:** https://ngrok.com/support
- **Status:** https://status.ngrok.com

---

## ✅ Next Steps

1. **Choose deployment method:**
   - Production → Use Netlify
   - Quick testing → Use ngrok

2. **Follow the setup guide above**

3. **Test your deployment:**
   - Netlify: Push to GitHub and check deploy logs
   - ngrok: Start dev server and run `npm run ngrok`

4. **Share your live URL!** 🎉

---

**Last Updated:** 2025-11-08  
**ARK Version:** 1.0.0  
**Maintained by:** Superman08091992
