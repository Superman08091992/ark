# ARK Monorepo Structure Plan

This document outlines the reorganization of ARK into a clean, production-ready monorepo.

## 🎯 Goal

Combine all frontend and backend code into a single, well-organized monorepo that's ready to launch.

## 📁 Proposed Structure

```
ark/
├── apps/                          # Applications
│   ├── web/                       # Main web application (Astro + React)
│   │   ├── src/
│   │   │   ├── pages/             # Astro pages
│   │   │   ├── components/        # React components
│   │   │   ├── layouts/           # Page layouts
│   │   │   └── styles/            # Global styles
│   │   ├── public/                # Static assets
│   │   ├── astro.config.mjs
│   │   └── package.json
│   │
│   └── api/                       # Backend API server
│       ├── src/
│       │   ├── server.ts          # Main server entry
│       │   ├── routes/            # API routes
│       │   ├── controllers/       # Business logic
│       │   ├── services/          # Core services
│       │   └── middleware/        # Express middleware
│       ├── intelligent-backend.cjs
│       ├── agent_tools.cjs
│       └── package.json
│
├── packages/                      # Shared packages
│   ├── shared/                    # Shared utilities
│   │   ├── src/
│   │   │   ├── types/             # TypeScript types
│   │   │   ├── utils/             # Utility functions
│   │   │   └── constants/         # Shared constants
│   │   └── package.json
│   │
│   └── config/                    # Shared configuration
│       ├── eslint-config/
│       ├── tsconfig/
│       └── prettier-config/
│
├── agents/                        # AI Agents
│   ├── kyle/                      # Kyle agent
│   │   ├── memory/                # Kyle's infinite memory
│   │   ├── tools/                 # Kyle's tools
│   │   └── kyle.cjs
│   │
│   └── joey/                      # Joey agent (if exists)
│       └── joey.cjs
│
├── data/                          # Data storage
│   ├── knowledge_base/            # Knowledge graph
│   ├── kyle_infinite_memory/      # Kyle's memories
│   ├── agent_logs/                # Agent conversation logs
│   └── mock_files/                # Mock data
│
├── deps/                          # Bundled dependencies
│   ├── node/                      # Node.js v20.10.0
│   ├── redis/                     # Redis v7.2.4
│   └── README.md
│
├── scripts/                       # Build & deployment scripts
│   ├── install-ark-host.sh       # Host installer
│   ├── create-ark-installer.sh   # Installer builder
│   ├── create-usb-host-system.sh # USB node creator
│   └── start-ngrok.sh             # ngrok tunnel
│
├── docs/                          # Documentation
│   ├── guides/
│   ├── api/
│   └── architecture/
│
├── tools/                         # Development tools
│   └── bundle-model-installer.sh
│
├── .github/                       # GitHub workflows
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
│
├── package.json                   # Root package.json (workspace)
├── pnpm-workspace.yaml           # PNPM workspace config
├── turbo.json                     # Turbo build config
├── netlify.toml                   # Netlify config
├── .gitignore
└── README.md
```

## 🔧 Technology Stack

### Frontend (apps/web)
- **Framework:** Astro v5
- **UI Library:** React v18
- **Styling:** TailwindCSS v3
- **Build:** Vite
- **Deploy:** Netlify

### Backend (apps/api)
- **Runtime:** Node.js v20
- **Framework:** Express/Fastify
- **Database:** Redis (cache)
- **AI:** Ollama (local LLM)
- **Storage:** File system (JSON)

### Monorepo Tools
- **Package Manager:** PNPM (workspaces)
- **Build System:** Turbo (caching)
- **Linting:** ESLint + Prettier
- **Testing:** Vitest
- **CI/CD:** GitHub Actions

## 📦 Workspace Configuration

### pnpm-workspace.yaml
```yaml
packages:
  - 'apps/*'
  - 'packages/*'
  - 'agents/*'
```

### Root package.json
```json
{
  "name": "ark-monorepo",
  "private": true,
  "workspaces": [
    "apps/*",
    "packages/*",
    "agents/*"
  ],
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "deploy": "turbo run deploy"
  }
}
```

## 🚀 Build & Deploy

### Development
```bash
# Install dependencies
pnpm install

# Start all apps in dev mode
pnpm dev

# Or start specific app
pnpm --filter @ark/web dev
pnpm --filter @ark/api dev
```

### Production Build
```bash
# Build all apps
pnpm build

# Deploy to Netlify
pnpm deploy
```

## 📊 Migration Steps

1. ✅ **Backup current state**
2. **Create new structure** (apps/, packages/, etc.)
3. **Move frontend files** to apps/web/
4. **Move backend files** to apps/api/
5. **Extract shared code** to packages/shared/
6. **Move agents** to agents/
7. **Organize docs** in docs/
8. **Move scripts** to scripts/
9. **Update imports** and paths
10. **Test build** and deployment
11. **Commit and push**

## ✅ Benefits

- ✅ **Single repo** - Everything in one place
- ✅ **Shared dependencies** - No duplication
- ✅ **Unified builds** - Build all apps together
- ✅ **Easy deployment** - One command deploys all
- ✅ **Better DX** - Clear organization
- ✅ **Scalable** - Easy to add new apps/packages

## 🎯 Ready to Launch

After restructuring:
- Frontend builds to `apps/web/dist/`
- Backend runs from `apps/api/`
- Shared code in `packages/`
- Everything deployable with one command

---

**Status:** Planning complete, ready to execute
**Next:** Run migration script to restructure
