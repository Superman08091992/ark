# ARK Local Storage Configuration

## ✅ Current Setup: Local File Storage (No Supabase)

Your ARK system is **already configured** to save everything to local files on your NVMe drive. **No Supabase is being used.**

## 📂 Storage Directories

All data is stored in these local directories:

### 1. **Kyle's Infinite Memory** (`kyle_infinite_memory/`)
- **Purpose:** Kyle's permanent memory storage
- **Format:** Individual JSON files per memory
- **Structure:**
  ```
  kyle_infinite_memory/
  ├── master_index.json       # Topic index for fast lookup
  ├── catalog.json            # Memory metadata catalog
  ├── compressed_knowledge.json # Compressed facts
  └── kyle_*.json             # Individual memory files
  ```
- **Current Size:** ~92KB (16 memory files)

### 2. **Knowledge Base** (`knowledge_base/`)
- **Purpose:** Shared knowledge graph across all agents
- **Format:** Single JSON file with graph structure
- **Structure:**
  ```
  knowledge_base/
  └── knowledge_graph.json    # Central knowledge repository
  ```
- **Current Size:** ~187KB

### 3. **Agent Logs** (`agent_logs/`)
- **Purpose:** Conversation logs for all agents
- **Format:** JSON files per agent
- **Structure:**
  ```
  agent_logs/
  ├── kyle_logs.json
  ├── joey_logs.json
  └── [agent_name]_logs.json
  ```

### 4. **Mock Files** (`mock_files/`)
- **Purpose:** Testing and demo data
- **Format:** Various file types
- **Usage:** Development/testing only

## 🔧 Configuration in `intelligent-backend.cjs`

```javascript
const FILES_DIR = path.join(__dirname, 'mock_files');
const KNOWLEDGE_DIR = path.join(__dirname, 'knowledge_base');
const LOGS_DIR = path.join(__dirname, 'agent_logs');
const KYLE_MEMORY_DIR = path.join(__dirname, 'kyle_infinite_memory');
```

These paths are **relative to the project root**, so everything saves to:
- `/home/user/webapp/knowledge_base/`
- `/home/user/webapp/kyle_infinite_memory/`
- `/home/user/webapp/agent_logs/`
- `/home/user/webapp/mock_files/`

## 💾 Storage Mechanism

### How Memories are Saved:

1. **Memory Creation:**
   ```javascript
   const memoryId = `kyle_${Date.now()}_${randomString}`;
   const memoryFile = path.join(KYLE_MEMORY_DIR, `${memoryId}.json`);
   fs.writeFileSync(memoryFile, JSON.stringify(memory, null, 2));
   ```

2. **Index Update:**
   - `master_index.json` tracks which topics map to which memory files
   - `catalog.json` stores metadata for quick retrieval
   - Both updated on every memory save

3. **Knowledge Graph:**
   ```javascript
   const knowledgePath = path.join(KNOWLEDGE_DIR, 'knowledge_graph.json');
   fs.writeFileSync(knowledgePath, JSON.stringify(graph, null, 2));
   ```

## 🚀 Benefits of Local File Storage

✅ **Fast:** Direct NVMe access (no network latency)
✅ **Simple:** No database setup required
✅ **Portable:** Copy the folders, keep all data
✅ **No Costs:** No cloud database fees
✅ **Privacy:** All data stays on your machine
✅ **Reliable:** No connection issues
✅ **Debuggable:** Easy to inspect JSON files

## 📊 Performance

**Read Operations:**
- Master index loads into memory on startup
- Catalog provides O(1) memory lookup
- Compressed knowledge for fast fact retrieval

**Write Operations:**
- Append-only memory files (fast writes)
- Index updates are batched
- No locking needed (single process)

## 🔄 Backup Strategy

To backup your data:

```bash
# Backup all ARK data
tar -czf ark-data-backup-$(date +%Y%m%d).tar.gz \
  knowledge_base/ \
  kyle_infinite_memory/ \
  agent_logs/

# Or copy to USB (from USB+Host architecture)
cp -r knowledge_base/ kyle_infinite_memory/ /media/usb/ark/data/
```

## 🗂️ File Formats

### Memory File Example (`kyle_*.json`):
```json
{
  "id": "kyle_1762516037201_wj3qskvu3",
  "timestamp": 1762516037201,
  "userMessage": "What is entropy?",
  "agentResponse": "Entropy is a measure of disorder...",
  "extractedFacts": [
    "Entropy measures disorder in thermodynamics",
    "Higher entropy = more randomness"
  ],
  "topics": ["physics", "thermodynamics", "entropy"],
  "importance": 0.75,
  "sources": [
    {
      "url": "https://example.com/entropy",
      "excerpt": "...",
      "type": "primary"
    }
  ],
  "enhancedByLLM": true
}
```

### Master Index Example:
```json
{
  "physics": ["kyle_1762516037201_wj3qskvu3", "kyle_1762516047942_iszzm8y3c"],
  "entropy": ["kyle_1762516037201_wj3qskvu3"],
  "thermodynamics": ["kyle_1762516037201_wj3qskvu3"]
}
```

## 🛠️ Maintenance

### Clean Old Memories:
```bash
# Find memories older than 30 days with low importance
cd kyle_infinite_memory/
node -e "
const fs = require('fs');
const now = Date.now();
const thirtyDays = 30 * 24 * 60 * 60 * 1000;
fs.readdirSync('.').filter(f => f.startsWith('kyle_') && f.endsWith('.json')).forEach(file => {
  const data = JSON.parse(fs.readFileSync(file));
  if (data.importance < 0.3 && (now - data.timestamp) > thirtyDays) {
    console.log('Old low-importance:', file);
    // fs.unlinkSync(file); // Uncomment to actually delete
  }
});
"
```

### Check Storage Size:
```bash
du -sh knowledge_base/ kyle_infinite_memory/ agent_logs/
```

### Rebuild Indices:
```bash
# If indices get corrupted, Kyle rebuilds them on restart
node intelligent-backend.cjs
# Indices auto-rebuild from memory files
```

## 🚨 Important Notes

1. **No Database Required:**
   - SQLite, PostgreSQL, MySQL, Supabase - NONE are used
   - Everything is plain JSON files

2. **Automatic Directory Creation:**
   - Directories are created automatically if missing
   - No manual setup needed

3. **Concurrent Access:**
   - Single process model (no locking needed)
   - For multi-process, consider Redis or SQLite

4. **File Limits:**
   - Modern filesystems: millions of files OK
   - Each memory is 1-5KB
   - 10,000 memories = ~50MB

## 🔐 Security

**File Permissions:**
```bash
# Current permissions (should be user-only)
chmod 700 knowledge_base/ kyle_infinite_memory/ agent_logs/
chmod 600 knowledge_base/*.json kyle_infinite_memory/*.json
```

**Sensitive Data:**
- No API keys stored in memory files
- User messages saved as-is (be mindful of PII)
- Consider encryption for sensitive deployments

## 📈 Scaling

**Current Capacity:**
- ✅ Handles 10,000+ memories easily
- ✅ Fast lookup via indices
- ✅ Minimal RAM usage

**If You Need More:**
- Switch to SQLite (still local, more efficient)
- Use Redis for caching (keep files as backup)
- Implement file rotation (archive old memories)

## ✅ Verification

Check your storage is working:

```bash
# List recent memories
ls -lt kyle_infinite_memory/kyle_*.json | head -5

# Check knowledge graph
cat knowledge_base/knowledge_graph.json | jq '.nodes | length'

# View a memory
cat kyle_infinite_memory/kyle_*.json | jq '.'
```

---

## 🎉 Summary

**Your ARK system uses LOCAL FILE STORAGE:**
- ✅ Already configured correctly
- ✅ No Supabase or cloud database
- ✅ All data on your NVMe drive
- ✅ Fast, reliable, portable
- ✅ No connection issues

**No changes needed** - it's already saving straight to your NVMe!

If Vercel deployment can't access local files (which is expected), you have these options:
1. Keep backend separate (localhost) with local storage
2. Add SQLite to backend (still local DB)
3. Use Redis for Vercel backend (ephemeral)
4. Keep Vercel for frontend only (recommended)

**Recommended:** Deploy frontend to Vercel, keep backend local with your NVMe storage.
