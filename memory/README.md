# ARK Memory Engine v2

Autonomous learning memory consolidation and semantic search system.

## Overview

Memory Engine v2 provides persistent storage, consolidation, and semantic recall for ARK reasoning traces. It implements a 4-stage pipeline that transforms raw reasoning traces into searchable memory chunks.

### Features

- **Trace Ingestion**: Store reasoning logs with signature verification
- **Consolidation Pipeline**: 4-stage transformation (summarize → compress → dedupe → embed)
- **Semantic Search**: Vector-based similarity search over memory chunks
- **Trust Tier Enforcement**: Security policies based on Ed25519 signatures
- **Quarantine System**: Isolation of suspicious/unsigned traces
- **FastAPI Service**: REST endpoints for all operations

## Architecture

```
┌─────────────────┐
│ Reasoning Trace │
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ Ingest │ ◄── Signature Verification
    └────┬───┘     Trust Tier Check
         │
         ▼
  ┌──────────────┐
  │ Reasoning DB │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Consolidate  │ ◄── Summarize
  │   Pipeline   │     Compress
  └──────┬───────┘     Dedupe
         │
         ▼
  ┌──────────────┐
  │ Memory Chunk │
  └──────┬───────┘
         │
         ▼
    ┌────────┐
    │ Embed  │ ◄── Generate Vector
    └────┬───┘     Embedding
         │
         ▼
  ┌──────────────┐
  │ Searchable   │
  │   Memory     │
  └──────────────┘
```

## Components

### 1. Database Schema (`schema.sql`)

SQLite database with 5 tables:

- **reasoning_log**: Raw reasoning traces with signatures
- **memory_chunks**: Consolidated memory with embeddings
- **reflection_reports**: Aletheia self-review results
- **id_state**: Agent behavioral model state
- **quarantine**: Suspicious/unsigned traces

### 2. Memory Engine (`engine.py`)

Core CRUD + recall API:

```python
from memory import MemoryEngine

engine = MemoryEngine(db_path='data/ark_memory.db')

# Ingest trace
trace_id = engine.ingest(trace, verify_signature=True, trust_tier='core')

# Consolidate traces into chunks
result = engine.consolidate(since_ts=None, batch_size=100)

# Generate embeddings
embedded_count = engine.embed(chunk_ids=None, batch_size=50)

# Search memory
results = engine.search(query="weather data", k=10)

# Get statistics
stats = engine.get_stats()
```

### 3. Pipeline Functions (`pipelines.py`)

4-stage consolidation pipeline:

```python
from memory import pipelines

# Stage 1: Summarize
summary = pipelines.summarize(text, max_length=500)

# Stage 2: Compress
compressed = pipelines.compress(summary, target_ratio=0.6)

# Stage 3: Deduplicate
hash_val = pipelines.dedupe_hash(compressed, normalize=True)

# Stage 4: Embed
embedding = pipelines.embed(compressed, dimensions=384)
```

### 4. Scheduled Jobs (`jobs.py`)

Cron-compatible consolidation jobs:

```bash
# Run nightly consolidation
python memory/jobs.py consolidate

# Generate embeddings
python memory/jobs.py embed

# Full pipeline (consolidate + embed)
python memory/jobs.py full --dry-run
```

### 5. FastAPI Service (`services/memory_api.py`)

REST API on port 8701:

```bash
# Start service
python services/memory_api.py

# Or with uvicorn
uvicorn services.memory_api:app --host 0.0.0.0 --port 8701
```

## API Endpoints

### Health & Metrics

```bash
# Health check
GET /api/v1/memory/health

# Prometheus metrics
GET /metrics
```

### Trace Operations

```bash
# Ingest trace
POST /api/v1/memory/ingest
{
  "trace": {
    "id": "trace-123",
    "agent": "Kyle",
    "timestamp": 1700000000000,
    "input": "query text",
    "output": "response text",
    "confidence": 0.85
  },
  "verify_signature": true,
  "trust_tier": "core"
}

# Get trace by ID
GET /api/v1/memory/trace/{trace_id}
```

### Consolidation

```bash
# Run consolidation
POST /api/v1/memory/consolidate
{
  "since_ts": 1700000000000,
  "batch_size": 100,
  "dry_run": false
}

# Generate embeddings
POST /api/v1/memory/embed
{
  "chunk_ids": null,
  "batch_size": 50
}
```

### Search & Query

```bash
# Semantic search
POST /api/v1/memory/search
{
  "query": "weather information",
  "k": 10,
  "min_confidence": 0.7,
  "trust_tiers": ["core", "sandbox"]
}

# Get statistics
GET /api/v1/memory/stats

# Get chunk by ID
GET /api/v1/memory/chunk/{chunk_id}
```

## Security Features

### Signature Verification

All traces from non-CORE peers must be signed with Ed25519:

```python
from federation import crypto

# Sign trace
private_key = crypto.load_private_key('node-123')
envelope = crypto.sign_packet(private_key, trace)

# Verify on ingestion
trace_id = engine.ingest(
    trace=envelope['packet'],
    verify_signature=True,
    trust_tier='sandbox'
)
```

### Trust Tier Enforcement

Four trust tiers with different policies:

- **CORE**: Local agents, no signature required
- **SANDBOX**: Requires signature, limited learning
- **EXTERNAL**: Requires signature, read-only
- **UNKNOWN**: Quarantined by default

### Quarantine System

Suspicious traces are isolated:

```sql
SELECT * FROM quarantine WHERE reason = 'unsigned_non_core';
```

Quarantine reasons:
- `unsigned_non_core`: Non-CORE trace without signature
- `invalid_signature`: Signature verification failed
- `missing_peer_key`: No public key for peer
- `trust_violation`: Trust tier policy violation

## Configuration

### Database Configuration

```python
# Default SQLite
engine = MemoryEngine(db_path='data/ark_memory.db')

# Custom path
engine = MemoryEngine(db_path='/var/lib/ark/memory.db')
```

### Pipeline Configuration

```python
# Adjust summarization
summary = pipelines.summarize(text, max_length=200)

# Change compression ratio
compressed = pipelines.compress(text, target_ratio=0.5)

# Custom embedding dimensions
embedding = pipelines.embed(text, dimensions=512)
```

### Job Configuration

```json
{
  "consolidation": {
    "batch_size": 100,
    "max_age_hours": 24,
    "min_traces": 10
  },
  "embedding": {
    "batch_size": 50,
    "max_chunks_per_run": 500
  }
}
```

## Performance

### Consolidation Pipeline

- **Summarization**: ~1ms per trace
- **Compression**: ~0.5ms per trace
- **Deduplication**: ~0.1ms per trace (hash)
- **Embedding**: ~5ms per chunk (with NumPy)

### Database Operations

- **Ingest**: ~2ms per trace
- **Consolidate (batch 100)**: ~500ms
- **Search (k=10)**: ~50ms with embeddings, ~10ms text fallback

### Scalability

- Tested with 10,000+ traces
- SQLite handles millions of rows efficiently
- Consider DuckDB for analytical workloads

## Integration

### Node.js Event Bus

```javascript
// intelligent-backend.cjs
import fetch from 'node-fetch';

async function ingestTrace(trace) {
  const response = await fetch('http://localhost:8701/api/v1/memory/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      trace: trace,
      verify_signature: true,
      trust_tier: 'core'
    })
  });
  return response.json();
}
```

### Python Agents

```python
from memory import MemoryEngine

class Kyle:
    def __init__(self):
        self.memory = MemoryEngine()
    
    def reason(self, input_text):
        # Generate response
        output = self.process(input_text)
        
        # Store in memory
        trace = {
            'id': str(uuid.uuid4()),
            'agent': 'Kyle',
            'timestamp': int(time.time() * 1000),
            'input': input_text,
            'output': output,
            'confidence': self.confidence
        }
        self.memory.ingest(trace, verify_signature=False, trust_tier='core')
        
        return output
```

## Monitoring

### Prometheus Metrics

```
# HELP ark_memory_traces_total Total number of reasoning traces
# TYPE ark_memory_traces_total gauge
ark_memory_traces_total 1523

# HELP ark_memory_chunks_total Total number of memory chunks
# TYPE ark_memory_chunks_total gauge
ark_memory_chunks_total 412

# HELP ark_memory_chunks_with_embeddings Number of chunks with embeddings
# TYPE ark_memory_chunks_with_embeddings gauge
ark_memory_chunks_with_embeddings 398

# HELP ark_memory_avg_confidence Average confidence score
# TYPE ark_memory_avg_confidence gauge
ark_memory_avg_confidence 0.823

# Trust tier distribution
ark_memory_trust_tier{tier="core"} 1200
ark_memory_trust_tier{tier="sandbox"} 300
ark_memory_trust_tier{tier="external"} 23
```

### Logging

```bash
# View consolidation logs
tail -f logs/memory/consolidation.log

# Check quarantine
sqlite3 data/ark_memory.db "SELECT * FROM quarantine"

# Monitor stats
watch -n 5 'curl -s http://localhost:8701/api/v1/memory/stats | jq'
```

## Testing

```bash
# Run unit tests
pytest tests/test_memory_pipeline.py -v

# Run with coverage
pytest tests/test_memory_pipeline.py --cov=memory --cov-report=html

# Test specific functions
pytest tests/test_memory_pipeline.py::TestPipelineFunctions::test_summarize_basic

# Test pipeline manually
python memory/pipelines.py
```

## Troubleshooting

### NumPy Not Available

If embeddings fail:

```bash
# Install NumPy
pip install numpy

# Or use text search fallback (automatic)
results = engine.search(query="text", k=10)  # Uses text search if no embeddings
```

### Database Locked

If you see "database is locked":

```python
# Use WAL mode for better concurrency
engine.db.execute("PRAGMA journal_mode=WAL")
```

### Slow Consolidation

If consolidation is slow:

```python
# Reduce batch size
result = engine.consolidate(batch_size=50)

# Add index
engine.db.execute("CREATE INDEX IF NOT EXISTS idx_consolidated ON reasoning_log(consolidated)")
```

## Roadmap

### Phase 3.1 (Current)
- ✅ Database schema
- ✅ Memory engine CRUD
- ✅ Pipeline functions
- ✅ Scheduled jobs
- ✅ FastAPI service

### Phase 3.2 (Reflective Loop)
- [ ] Aletheia-led review
- [ ] Cross-agent critique
- [ ] Policy enforcement

### Phase 3.3 (ID Growth)
- [ ] Behavioral model updates
- [ ] Feature extraction
- [ ] EWMA integration

### Future Enhancements
- [ ] DuckDB support for analytics
- [ ] Advanced embedding models (sentence-transformers)
- [ ] Multi-modal memory (images, audio)
- [ ] Distributed memory federation

## License

Part of the ARK autonomous reasoning platform.
