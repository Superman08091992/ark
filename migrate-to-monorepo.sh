#!/bin/bash
##############################################################################
# ARK Monorepo Migration Script
# Reorganizes the project into a clean monorepo structure
##############################################################################

set -e

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║           ARK Monorepo Migration                                      ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Confirm
read -p "This will restructure your project. Continue? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Migration cancelled."
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "1️⃣  Creating backup..."
BACKUP_NAME="ark-pre-migration-$(date +%Y%m%d-%H%M%S).tar.gz"
tar --exclude='node_modules' --exclude='.git' --exclude='deps' --exclude='venv' \
    -czf "/tmp/$BACKUP_NAME" .
echo "✅ Backup created: /tmp/$BACKUP_NAME"

echo ""
echo "2️⃣  Creating new directory structure..."

# Create main structure
mkdir -p apps/{web,api}/src
mkdir -p packages/{shared,config}/src
mkdir -p data/{knowledge_base,kyle_infinite_memory,agent_logs,mock_files}
mkdir -p scripts
mkdir -p docs/{guides,api,architecture}
mkdir -p tools
mkdir -p .github/workflows

echo "✅ Directories created"

echo ""
echo "3️⃣  Moving frontend files to apps/web/..."

# Move Astro/React frontend
if [ -d "src" ]; then
    cp -r src/* apps/web/src/ 2>/dev/null || true
fi
if [ -d "public" ]; then
    cp -r public apps/web/ 2>/dev/null || true
fi
if [ -f "astro.config.mjs" ]; then
    cp astro.config.mjs apps/web/
fi
if [ -d ".astro" ]; then
    cp -r .astro apps/web/ 2>/dev/null || true
fi

# Move frontend specific files
for file in tailwind.config.js postcss.config.js tsconfig.json; do
    if [ -f "$file" ]; then
        cp "$file" apps/web/
    fi
done

echo "✅ Frontend files moved"

echo ""
echo "4️⃣  Moving backend files to apps/api/..."

# Move backend files
for file in intelligent-backend.cjs agent_tools.cjs smart-backend.cjs mock-backend.cjs; do
    if [ -f "$file" ]; then
        cp "$file" apps/api/src/
    fi
done

# Move backend related files
for file in *.cjs *.js; do
    if [ -f "$file" ] && ! [ -f "apps/api/src/$file" ]; then
        if [[ ! "$file" =~ ^(astro|tailwind|postcss|vite) ]]; then
            cp "$file" apps/api/src/ 2>/dev/null || true
        fi
    fi
done

echo "✅ Backend files moved"

echo ""
echo "5️⃣  Organizing agents..."

# Move agents
if [ -d "agents" ]; then
    # Keep agents folder but organize it
    echo "✅ Agents already in place"
else
    mkdir -p agents
fi

# Move Kyle if exists
if [ -d "kyle" ]; then
    mv kyle agents/ 2>/dev/null || cp -r kyle agents/
fi
if [ -d "joey" ]; then
    mv joey agents/ 2>/dev/null || cp -r joey agents/
fi

echo "✅ Agents organized"

echo ""
echo "6️⃣  Moving data directories..."

# Move data if not already there
if [ -d "knowledge_base" ] && [ ! "$(ls -A data/knowledge_base 2>/dev/null)" ]; then
    cp -r knowledge_base/* data/knowledge_base/ 2>/dev/null || true
fi
if [ -d "kyle_infinite_memory" ] && [ ! "$(ls -A data/kyle_infinite_memory 2>/dev/null)" ]; then
    cp -r kyle_infinite_memory/* data/kyle_infinite_memory/ 2>/dev/null || true
fi
if [ -d "agent_logs" ] && [ ! "$(ls -A data/agent_logs 2>/dev/null)" ]; then
    cp -r agent_logs/* data/agent_logs/ 2>/dev/null || true
fi

echo "✅ Data directories organized"

echo ""
echo "7️⃣  Moving scripts..."

# Move installation scripts
for script in install-ark-host.sh create-ark-installer.sh create-usb-host-system.sh \
              start-ngrok.sh bundle-model-installer.sh; do
    if [ -f "$script" ]; then
        cp "$script" scripts/
        chmod +x "scripts/$script"
    fi
done

echo "✅ Scripts moved"

echo ""
echo "8️⃣  Organizing documentation..."

# Move documentation
for doc in *.md; do
    if [ -f "$doc" ] && [ "$doc" != "README.md" ]; then
        cp "$doc" docs/ 2>/dev/null || true
    fi
done

echo "✅ Documentation organized"

echo ""
echo "9️⃣  Creating workspace configuration..."

# Create pnpm-workspace.yaml
cat > pnpm-workspace.yaml << 'EOF'
packages:
  - 'apps/*'
  - 'packages/*'
  - 'agents/*'
EOF

# Create turbo.json
cat > turbo.json << 'EOF'
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**", ".astro/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {
      "outputs": []
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": []
    }
  }
}
EOF

# Create apps/web/package.json
cat > apps/web/package.json << 'EOF'
{
  "name": "@ark/web",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "check": "astro check"
  },
  "dependencies": {
    "astro": "^5.15.3",
    "@astrojs/react": "^3.0.0",
    "@astrojs/tailwind": "^5.0.2",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "tailwindcss": "^3.4.13"
  }
}
EOF

# Create apps/api/package.json
cat > apps/api/package.json << 'EOF'
{
  "name": "@ark/api",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "node --watch src/intelligent-backend.cjs",
    "start": "node src/intelligent-backend.cjs",
    "build": "echo 'No build needed for Node.js backend'"
  },
  "dependencies": {
    "fastify": "^5.6.1",
    "express": "^4.19.2",
    "axios": "^1.7.1"
  }
}
EOF

# Create packages/shared/package.json
cat > packages/shared/package.json << 'EOF'
{
  "name": "@ark/shared",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "main": "./src/index.ts",
  "types": "./src/index.ts"
}
EOF

# Update root package.json
cat > package.json << 'EOF'
{
  "name": "ark-monorepo",
  "version": "1.0.0",
  "private": true,
  "type": "module",
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
    "deploy": "turbo run build && netlify deploy --prod",
    "clean": "rm -rf apps/*/node_modules packages/*/node_modules node_modules"
  },
  "devDependencies": {
    "turbo": "^2.1.0",
    "prettier": "^3.3.3",
    "eslint": "^9.15.0"
  }
}
EOF

echo "✅ Workspace configured"

echo ""
echo "🔟 Creating README files..."

# Create apps/web/README.md
cat > apps/web/README.md << 'EOF'
# ARK Web Application

Frontend application built with Astro and React.

## Development

```bash
pnpm dev
```

## Build

```bash
pnpm build
```

## Deploy

Automatically deployed via Netlify when pushing to main branch.
EOF

# Create apps/api/README.md
cat > apps/api/README.md << 'EOF'
# ARK API Server

Backend API server with AI agent integration.

## Development

```bash
pnpm dev
```

## Start

```bash
pnpm start
```
EOF

# Create main README.md
cat > README.md << 'EOF'
# ARK - Adaptive Reasoning & Knowledge System

A monorepo containing the complete ARK system.

## Structure

- `apps/web` - Frontend (Astro + React)
- `apps/api` - Backend API server
- `packages/shared` - Shared utilities
- `agents/` - AI agents (Kyle, Joey)
- `data/` - Knowledge base and agent memories
- `deps/` - Bundled dependencies (Node.js, Redis)
- `scripts/` - Installation and deployment scripts
- `docs/` - Documentation

## Quick Start

```bash
# Install dependencies
pnpm install

# Start development
pnpm dev

# Build for production
pnpm build

# Deploy
pnpm deploy
```

## Documentation

See `docs/` directory for detailed documentation.

## Installation

For system installation, see `scripts/install-ark-host.sh`
EOF

echo "✅ README files created"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║              ✅ MONOREPO MIGRATION COMPLETE! ✅                      ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 New structure created:"
echo "   - apps/web/     → Frontend"
echo "   - apps/api/     → Backend"
echo "   - packages/     → Shared code"
echo "   - agents/       → AI agents"
echo "   - data/         → Storage"
echo "   - scripts/      → Installation scripts"
echo "   - docs/         → Documentation"
echo ""
echo "🚀 Next steps:"
echo "   1. Review the new structure"
echo "   2. Run: pnpm install"
echo "   3. Run: pnpm dev"
echo "   4. Test everything works"
echo "   5. Commit changes: git add . && git commit -m 'refactor: Migrate to monorepo structure'"
echo ""
echo "💾 Backup saved at: /tmp/$BACKUP_NAME"
