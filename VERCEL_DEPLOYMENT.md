# Vercel Deployment Guide for ARK

## ✅ Vercel Configuration Complete

The Vercel bot should now work properly with the following configurations:

### Files Added

1. **vercel.json** - Main Vercel configuration
   - Framework: Astro
   - Build command: `npm run build`
   - Output directory: `dist`
   - Security headers configured
   - API rewrites enabled

2. **.vercelignore** - Files to exclude from deployment
   - Python files (venv, requirements.txt)
   - Large data files (knowledge_base, kyle_infinite_memory)
   - Scripts and installers
   - Development files

3. **astro.config.mjs** - Astro build configuration
   - Static output mode
   - Tailwind + React integrations
   - Node adapter for SSR (optional)

4. **.env.example** - Environment variable template
   - API URLs
   - Redis configuration
   - Feature flags

## 🚀 Deploying to Vercel

### Option 1: Automatic Deployment (Recommended)

1. **Connect to Vercel:**
   - Go to https://vercel.com
   - Click "Add New Project"
   - Import `Superman08091992/ark` from GitHub
   - Vercel will auto-detect Astro

2. **Configuration:**
   - Framework Preset: **Astro**
   - Root Directory: `./` (leave default)
   - Build Command: `npm run build` (auto-detected)
   - Output Directory: `dist` (auto-detected)

3. **Environment Variables:**
   Add these in Vercel dashboard:
   ```
   NODE_ENV=production
   VITE_API_URL=https://your-backend-api.com
   ```

4. **Deploy:**
   - Click "Deploy"
   - Vercel will build and deploy automatically
   - Every push to `master` will auto-deploy

### Option 2: Manual Deployment via CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel

# Production deployment
vercel --prod
```

## 🔧 Vercel Bot Integration

The Vercel bot will now:

✅ **Auto-deploy on push to master**
✅ **Create preview deployments for PRs**
✅ **Comment on PRs with preview URLs**
✅ **Show build status in GitHub**

### Bot Configuration

The bot uses `vercel.json` settings:
- **ignoreCommand**: `git diff --quiet HEAD^ HEAD ./`
  - Only deploys if files changed
  - Skips if only docs/tests updated

- **regions**: `["iad1"]`
  - Deploys to US East (Virginia)
  - Can change to your preferred region

## 📦 What Gets Deployed

**Included:**
- ✅ Frontend assets (Astro/React)
- ✅ Built JavaScript/CSS
- ✅ Public assets
- ✅ README.md

**Excluded (.vercelignore):**
- ❌ Python backend files
- ❌ Knowledge base data
- ❌ Scripts and installers
- ❌ Development files
- ❌ Documentation (except README)

## 🔐 Environment Variables in Vercel

Configure these in Vercel Dashboard → Settings → Environment Variables:

### Required:
```bash
NODE_ENV=production
```

### Optional (for full features):
```bash
VITE_API_URL=https://your-backend.com
REDIS_URL=redis://your-redis.com:6379
OLLAMA_API_URL=https://your-ollama.com
ENABLE_LLM=true
ENABLE_WEB_SEARCH=true
```

## 🐛 Troubleshooting

### Build Fails

**Issue:** Build command not found
**Fix:** Ensure `package.json` has `"build": "astro build"`

**Issue:** Dependencies missing
**Fix:** Run `npm install` locally first, then push

### Bot Not Commenting

**Issue:** Vercel bot not commenting on PRs
**Fix:**
1. Check Vercel integration in GitHub Settings → Integrations
2. Ensure bot has write access to repository
3. Re-authorize if needed

### Large Deployment Size

**Issue:** Deployment too large
**Fix:** Check `.vercelignore` includes:
```
knowledge_base/
kyle_infinite_memory/
agent_logs/
venv/
node_modules/
```

## 📊 Build Output

Expected build output:
```
✓ Built in 234ms
✓ Output: dist/
✓ Size: ~5MB
```

If build size > 50MB, add more to `.vercelignore`

## 🔄 Auto-Deploy Workflow

1. **Push to master:**
   ```bash
   git push origin master
   ```

2. **Vercel bot:**
   - Detects push
   - Reads `vercel.json`
   - Runs build
   - Deploys to production
   - Comments status

3. **Preview deployments:**
   - Create PR → Vercel deploys preview
   - Comment shows preview URL
   - Test before merging

## 🌐 Custom Domains

Add custom domain in Vercel:

1. Go to Project Settings → Domains
2. Add domain: `ark.1true.org`
3. Configure DNS:
   ```
   Type: CNAME
   Name: ark
   Value: cname.vercel-dns.com
   ```
4. Vercel auto-configures SSL

## 📈 Monitoring

View deployment logs:
1. Vercel Dashboard → Deployments
2. Click on deployment
3. View build logs
4. Check function logs

## ✅ Checklist

Before deploying:

- [ ] `vercel.json` exists and configured
- [ ] `.vercelignore` excludes large files
- [ ] `astro.config.mjs` configured
- [ ] Environment variables set in Vercel
- [ ] Build works locally: `npm run build`
- [ ] Preview works: `npm run preview`

## 🎉 Success

Once deployed, you'll get:

- 🌐 Production URL: `https://ark.vercel.app`
- 🔗 Custom domain: `https://ark.1true.org` (if configured)
- 🚀 Auto-deploy on push
- 📦 Preview deployments for PRs
- 📊 Analytics dashboard

---

**Status:** ✅ Vercel configuration complete and ready to deploy!

**Next:** Push to GitHub and watch Vercel auto-deploy
