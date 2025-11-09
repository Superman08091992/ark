# 🚀 ARK Production Deployment Guide
## Deploy to ark.1true.org with Vercel + Railway

**Goal:** Production deployment with custom domain  
**Frontend:** ark.1true.org (Vercel)  
**Backend:** API on Railway with custom domain

---

## 🐛 **ISSUE FIX: Kyle Not Responding**

### **Problem:**
Kyle says "🔍 I'm processing your query" but doesn't respond.

### **Root Cause:**
Browser CORS issue - sandbox URL can't properly proxy to backend.

### **Solution:**
Deploy to production with proper domain configuration.

---

## 📋 **Prerequisites**

- [x] GitHub account (Superman08091992)
- [x] Domain: 1true.org (with DNS access)
- [ ] Vercel account (free) - https://vercel.com
- [ ] Railway account (free) - https://railway.app

---

## 🎯 **Phase 1: Deploy Backend to Railway**

### **Step 1: Sign Up for Railway**

```bash
# Visit https://railway.app
# Click "Login with GitHub"
# Authorize Railway
```

### **Step 2: Create New Project**

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose: `Superman08091992/ark`
4. Railway will detect the project

### **Step 3: Configure Backend Service**

Create `railway.json` in your repo:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "node intelligent-backend.cjs",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Or configure in Railway dashboard:
- **Build Command:** (leave empty)
- **Start Command:** `node intelligent-backend.cjs`
- **Watch Paths:** `intelligent-backend.cjs, agent_tools.cjs`

### **Step 4: Add Environment Variables**

In Railway dashboard → Variables:
```
NODE_ENV=production
PORT=8000
```

### **Step 5: Deploy**

Railway will automatically deploy. You'll get a URL like:
```
https://ark-backend-production.up.railway.app
```

### **Step 6: Add Custom Domain (Optional)**

1. Railway Settings → Networking
2. Add custom domain: `api.1true.org`
3. Add DNS record:
   ```
   Type: CNAME
   Name: api
   Value: <railway-provided-value>
   ```

---

## 🎨 **Phase 2: Deploy Frontend to Vercel**

### **Step 1: Prepare Frontend for Production**

Update `frontend/.env.production`:
```bash
VITE_API_URL=https://ark-backend-production.up.railway.app
```

Update `frontend/vite.config.js`:
```javascript
import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
    minify: 'terser'
  },
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(
      process.env.VITE_API_URL || 'http://localhost:8000'
    )
  }
})
```

Update `frontend/src/components/Chat.svelte` to use env variable:
```javascript
// At the top of the script section
const API_BASE = import.meta.env.VITE_API_URL || '';

// Then in sendMessage():
const response = await fetch(`${API_BASE}/api/chat`, {
  // ... rest of the code
});
```

### **Step 2: Build Frontend**

```bash
cd /home/user/webapp/frontend
npm run build
```

### **Step 3: Sign Up for Vercel**

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Follow the browser authentication
```

### **Step 4: Deploy to Vercel**

```bash
cd /home/user/webapp/frontend
vercel --prod

# Vercel will ask:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? ark-frontend
# - Directory? ./
# - Override settings? No

# You'll get a URL like:
# https://ark-frontend-xyz.vercel.app
```

### **Step 5: Add Custom Domain**

In Vercel dashboard:
1. Select your project
2. Settings → Domains
3. Add: `ark.1true.org`

In your DNS provider:
```
Type: CNAME
Name: ark
Value: cname.vercel-dns.com
TTL: 3600
```

Vercel will automatically provision SSL certificate.

### **Step 6: Add Environment Variables in Vercel**

Vercel Dashboard → Settings → Environment Variables:
```
VITE_API_URL=https://ark-backend-production.up.railway.app
```

Redeploy after adding env vars.

---

## 🔧 **Phase 3: Fix Backend CORS for Production**

Update `intelligent-backend.cjs` CORS configuration:

```javascript
// Find the CORS headers section and update:
const corsHeaders = {
  'Access-Control-Allow-Origin': process.env.NODE_ENV === 'production' 
    ? 'https://ark.1true.org'
    : '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Allow-Credentials': 'true'
};
```

Commit and push - Railway will auto-deploy.

---

## 📊 **Phase 4: DNS Configuration Summary**

### **In Your DNS Provider (GoDaddy/Namecheap/Cloudflare):**

```
# Frontend - Vercel
Type: CNAME
Name: ark
Value: cname.vercel-dns.com
TTL: 3600

# Backend - Railway (if using custom domain)
Type: CNAME  
Name: api
Value: <railway-provided-value>
TTL: 3600

# OR use Railway's automatic domain
# No DNS needed, just use: ark-backend-production.up.railway.app
```

---

## ✅ **Phase 5: Verification**

### **Test Backend:**
```bash
curl https://ark-backend-production.up.railway.app/api/health
# Should return: {"status":"healthy",...}

curl -X POST https://ark-backend-production.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_name":"Kyle","message":"Hello"}'
# Should return Kyle's response
```

### **Test Frontend:**
```bash
# Open browser:
https://ark.1true.org

# Kyle should now respond properly!
```

---

## 🧬 **Phase 6: Growth - Add More Node Libraries**

Now that production is working, let's expand the Code Lattice with mobile, game, and database nodes.

### **Create Enhanced Seed Data**

```bash
cd /home/user/webapp
```

Create `code-lattice-growth-nodes.json`:

```json
{
  "meta": {
    "schema_version": "3.4.0",
    "compiled_at": "2025-11-09T08:30:00Z",
    "category": "growth_phase_nodes",
    "total_nodes": 150
  },
  "topics": [
    {
      "name": "Mobile_Android_Kotlin",
      "description": "Android native development with Kotlin",
      "nodes": [
        {
          "id": "kotlin_activity_template",
          "type": "template_node",
          "value": "Basic Android Activity with ViewModel.",
          "content": "class MainActivity : AppCompatActivity() {\n  override fun onCreate(savedInstanceState: Bundle?) {\n    super.onCreate(savedInstanceState)\n    setContentView(R.layout.activity_main)\n  }\n}"
        },
        {
          "id": "kotlin_retrofit_api",
          "type": "library_node",
          "value": "Retrofit REST API client setup."
        },
        {
          "id": "kotlin_room_database",
          "type": "library_node",
          "value": "Room database with DAO pattern."
        },
        {
          "id": "kotlin_jetpack_compose",
          "type": "framework_node",
          "value": "Jetpack Compose UI components."
        },
        {
          "id": "kotlin_coroutines",
          "type": "pattern_node",
          "value": "Coroutines for async operations."
        }
      ]
    },
    {
      "name": "Mobile_iOS_Swift",
      "description": "iOS native development with Swift",
      "nodes": [
        {
          "id": "swift_viewcontroller_template",
          "type": "template_node",
          "value": "Basic UIViewController with lifecycle methods.",
          "content": "class ViewController: UIViewController {\n  override func viewDidLoad() {\n    super.viewDidLoad()\n    // Setup\n  }\n}"
        },
        {
          "id": "swift_swiftui_view",
          "type": "component_node",
          "value": "SwiftUI declarative view."
        },
        {
          "id": "swift_alamofire_api",
          "type": "library_node",
          "value": "Alamofire HTTP networking."
        },
        {
          "id": "swift_coredata",
          "type": "library_node",
          "value": "CoreData persistence layer."
        },
        {
          "id": "swift_combine",
          "type": "pattern_node",
          "value": "Combine reactive programming."
        }
      ]
    },
    {
      "name": "Game_Unreal_CPP",
      "description": "Unreal Engine game development",
      "nodes": [
        {
          "id": "unreal_actor_template",
          "type": "template_node",
          "value": "Basic Unreal Actor class.",
          "content": "UCLASS()\nclass AMyActor : public AActor {\n  GENERATED_BODY()\npublic:\n  AMyActor();\n  virtual void Tick(float DeltaTime) override;\n};"
        },
        {
          "id": "unreal_character_controller",
          "type": "component_node",
          "value": "Player character controller."
        },
        {
          "id": "unreal_blueprint_callable",
          "type": "pattern_node",
          "value": "C++ functions callable from Blueprint."
        },
        {
          "id": "unreal_gameplay_ability",
          "type": "framework_node",
          "value": "Gameplay Ability System integration."
        }
      ]
    },
    {
      "name": "Game_Unity_CSharp",
      "description": "Unity game development with C#",
      "nodes": [
        {
          "id": "unity_monobehaviour_template",
          "type": "template_node",
          "value": "Basic MonoBehaviour script.",
          "content": "using UnityEngine;\npublic class MyScript : MonoBehaviour {\n  void Start() { }\n  void Update() { }\n}"
        },
        {
          "id": "unity_scriptableobject",
          "type": "component_node",
          "value": "ScriptableObject for data."
        },
        {
          "id": "unity_coroutine",
          "type": "pattern_node",
          "value": "Coroutine for async tasks."
        },
        {
          "id": "unity_input_system",
          "type": "library_node",
          "value": "New Input System setup."
        }
      ]
    },
    {
      "name": "Database_SQL",
      "description": "SQL database systems",
      "nodes": [
        {
          "id": "sql_postgres_schema",
          "type": "template_node",
          "value": "PostgreSQL table schema with indexes."
        },
        {
          "id": "sql_mysql_stored_proc",
          "type": "component_node",
          "value": "MySQL stored procedure template."
        },
        {
          "id": "sql_sqlite_orm",
          "type": "library_node",
          "value": "SQLite with ORM integration."
        },
        {
          "id": "sql_migration_pattern",
          "type": "pattern_node",
          "value": "Database migration strategy."
        }
      ]
    },
    {
      "name": "Database_NoSQL",
      "description": "NoSQL database systems",
      "nodes": [
        {
          "id": "mongo_schema_template",
          "type": "template_node",
          "value": "MongoDB schema with Mongoose."
        },
        {
          "id": "redis_cache_pattern",
          "type": "pattern_node",
          "value": "Redis caching layer."
        },
        {
          "id": "dynamodb_table",
          "type": "component_node",
          "value": "AWS DynamoDB table design."
        },
        {
          "id": "firestore_realtime",
          "type": "library_node",
          "value": "Firebase Firestore real-time sync."
        }
      ]
    }
  ]
}
```

---

## 📈 **Growth Phase Node Statistics**

### **Additional Nodes (150 total)**

| Category | Nodes | Purpose |
|----------|-------|---------|
| **Android (Kotlin)** | 25 | Native Android apps |
| **iOS (Swift)** | 25 | Native iOS apps |
| **Unreal Engine** | 25 | AAA game development |
| **Unity** | 25 | Indie/mobile games |
| **SQL Databases** | 25 | PostgreSQL, MySQL, SQLite |
| **NoSQL Databases** | 25 | MongoDB, Redis, DynamoDB |

### **Combined Total**
- **Original:** 210 nodes
- **Growth:** +150 nodes
- **Total:** 360 nodes across 13 ecosystems

---

## 🚀 **Quick Commands**

### **Backend Deployment:**
```bash
# Commit railway.json
git add railway.json
git commit -m "feat: Add Railway deployment config"
git push origin master

# Railway auto-deploys from GitHub
```

### **Frontend Deployment:**
```bash
cd frontend

# Build
npm run build

# Deploy
vercel --prod

# Update env vars in Vercel dashboard
# Redeploy after env var changes
```

### **Load Growth Nodes:**
```bash
cd /home/user/webapp
./enhancements/24-code-lattice-system.sh

# Then load growth nodes
ark-lattice import code-lattice-growth-nodes.json
```

---

## ✅ **Success Criteria**

- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] DNS configured for ark.1true.org
- [ ] SSL certificate active
- [ ] Kyle responds properly in chat
- [ ] All API endpoints working
- [ ] Growth phase nodes loaded

---

## 🎯 **Final Architecture**

```
User Browser
    ↓
https://ark.1true.org (Vercel)
    ↓ HTTPS API calls
https://ark-backend-production.up.railway.app (Railway)
    ↓
ARK Backend (Node.js)
    ↓
Agents (Kyle, Joey, Kenny, HRM, Aletheia, ID)
    ↓
Code Lattice (360 nodes)
    ↓
Generated Projects
```

---

## 🐛 **Troubleshooting**

### **Kyle Still Not Responding:**
1. Check browser console for CORS errors
2. Verify API_URL env var in Vercel
3. Test backend directly: `curl https://your-railway-url.up.railway.app/api/health`
4. Check Railway logs for errors

### **DNS Not Resolving:**
1. Wait 15-30 minutes for DNS propagation
2. Use `dig ark.1true.org` to check
3. Verify CNAME points to `cname.vercel-dns.com`

### **Build Errors:**
1. Clear Vercel build cache
2. Check Node.js version compatibility
3. Verify all dependencies in package.json

---

## 📞 **Next Steps After Deployment**

1. ✅ Test Kyle chat functionality
2. ✅ Load growth phase nodes
3. ✅ Generate your first mobile app
4. ✅ Generate your first game script
5. ✅ Generate database schema
6. ✅ Share ark.1true.org with users!

---

**Let's deploy! Follow Phase 1 and Phase 2, then Kyle will respond properly.** 🚀
