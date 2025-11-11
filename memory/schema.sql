-- ARK Memory Engine v2 Schema
-- SQLite/DuckDB compatible schema for reasoning logs and memory chunks

-- Reasoning logs - raw traces from all agents
CREATE TABLE IF NOT EXISTS reasoning_log (
    id TEXT PRIMARY KEY,
    agent TEXT NOT NULL,
    ts INTEGER NOT NULL,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    depth INTEGER DEFAULT 3,
    confidence REAL DEFAULT 0.0,
    duration_ms REAL DEFAULT 0.0,
    path TEXT,  -- JSON array of cognitive levels
    signature TEXT,  -- Ed25519 signature for provenance
    peer_id TEXT,  -- Source peer (null = local)
    trust_tier TEXT DEFAULT 'unknown',  -- CORE/SANDBOX/EXTERNAL/UNKNOWN
    metadata TEXT,  -- JSON additional data
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Memory chunks - consolidated, embedded knowledge
CREATE TABLE IF NOT EXISTS memory_chunks (
    chunk_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,  -- References reasoning_log.id or other chunk_id
    ts INTEGER NOT NULL,
    text TEXT NOT NULL,
    summary TEXT,
    tokens INTEGER DEFAULT 0,
    embedding BLOB,  -- Vector embedding (numpy array serialized)
    hash TEXT UNIQUE NOT NULL,  -- SHA256 for deduplication
    provenance TEXT,  -- JSON trace of transformations
    trust_tier TEXT DEFAULT 'unknown',  -- From peer trust tier
    consolidated INTEGER DEFAULT 0,  -- 0=raw, 1=consolidated
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Reflection reports - post-task reviews
CREATE TABLE IF NOT EXISTS reflection_reports (
    report_id TEXT PRIMARY KEY,
    agent TEXT NOT NULL,
    ts INTEGER NOT NULL,
    traces_analyzed INTEGER DEFAULT 0,
    avg_confidence REAL DEFAULT 0.0,
    contradiction_rate REAL DEFAULT 0.0,
    duplicate_rate REAL DEFAULT 0.0,
    critiques TEXT,  -- JSON array of critique objects
    fixes TEXT,  -- JSON array of recommended fixes
    signature TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Reflections - nightly "sleep mode" insights
CREATE TABLE IF NOT EXISTS reflections (
    reflection_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    chunk_id TEXT,
    tier TEXT,
    summary_hash TEXT,
    insight TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    confidence_delta REAL DEFAULT 0.0,
    reflection_type TEXT,
    signature TEXT,
    metadata TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- ID behavioral state - agent identity model
CREATE TABLE IF NOT EXISTS id_state (
    state_id TEXT PRIMARY KEY,
    agent TEXT NOT NULL UNIQUE,
    ts INTEGER NOT NULL,
    risk_score REAL DEFAULT 0.5,
    latency_score REAL DEFAULT 0.5,
    preference_vector TEXT,  -- JSON object of preferences
    behavior_features TEXT,  -- JSON object of behavioral traits
    update_count INTEGER DEFAULT 0,
    last_updated INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Quarantine - suspicious/unverified traces
CREATE TABLE IF NOT EXISTS quarantine (
    quarantine_id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    peer_id TEXT,
    trust_tier TEXT,
    data TEXT,  -- JSON original trace
    ts INTEGER NOT NULL,
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_log_agent ON reasoning_log(agent, ts DESC);
CREATE INDEX IF NOT EXISTS idx_log_ts ON reasoning_log(ts DESC);
CREATE INDEX IF NOT EXISTS idx_log_signature ON reasoning_log(signature);
CREATE INDEX IF NOT EXISTS idx_log_peer ON reasoning_log(peer_id);

CREATE INDEX IF NOT EXISTS idx_chunk_hash ON memory_chunks(hash);
CREATE INDEX IF NOT EXISTS idx_chunk_source ON memory_chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_chunk_ts ON memory_chunks(ts DESC);
CREATE INDEX IF NOT EXISTS idx_chunk_tier ON memory_chunks(trust_tier);
CREATE INDEX IF NOT EXISTS idx_chunk_consolidated ON memory_chunks(consolidated);

CREATE INDEX IF NOT EXISTS idx_reflection_agent ON reflection_reports(agent, ts DESC);
CREATE INDEX IF NOT EXISTS idx_reflection_ts ON reflection_reports(ts DESC);

CREATE INDEX IF NOT EXISTS idx_reflections_timestamp ON reflections(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_reflections_chunk ON reflections(chunk_id);
CREATE INDEX IF NOT EXISTS idx_reflections_type ON reflections(reflection_type);

CREATE INDEX IF NOT EXISTS idx_quarantine_ts ON quarantine(ts DESC);
CREATE INDEX IF NOT EXISTS idx_quarantine_peer ON quarantine(peer_id);

-- Views for analytics
CREATE VIEW IF NOT EXISTS v_recent_reasoning AS
SELECT 
    agent,
    COUNT(*) as trace_count,
    AVG(confidence) as avg_confidence,
    AVG(duration_ms) as avg_duration,
    MAX(ts) as last_activity
FROM reasoning_log
WHERE ts > strftime('%s', 'now') - 86400  -- Last 24 hours
GROUP BY agent;

CREATE VIEW IF NOT EXISTS v_memory_stats AS
SELECT 
    COUNT(*) as total_chunks,
    SUM(CASE WHEN consolidated = 1 THEN 1 ELSE 0 END) as consolidated_count,
    SUM(tokens) as total_tokens,
    COUNT(DISTINCT hash) as unique_hashes,
    AVG(LENGTH(text)) as avg_text_length
FROM memory_chunks;

CREATE VIEW IF NOT EXISTS v_quarantine_summary AS
SELECT 
    reason,
    trust_tier,
    COUNT(*) as count,
    MAX(ts) as last_occurrence
FROM quarantine
GROUP BY reason, trust_tier
ORDER BY count DESC;
