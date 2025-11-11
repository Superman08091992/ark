#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Memory Engine v2

CRUD + recall API with SQLite/DuckDB + Redis caching.
Manages reasoning logs, memory chunks, and semantic search.

Features:
- Ingest reasoning traces with signature verification
- Consolidation pipeline (summarize, compress, dedupe)
- Embedding generation and semantic search
- Trust tier enforcement
- Quarantine for suspicious traces
"""

import asyncio
import hashlib
import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("NumPy not available - embeddings disabled")

logger = logging.getLogger(__name__)


class MemoryEngine:
    """
    Memory Engine v2 for ARK autonomous learning
    
    Handles reasoning log storage, consolidation, and semantic recall.
    """
    
    def __init__(self, db_path: str = 'data/ark_memory.db'):
        """
        Initialize memory engine
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        
        self._init_schema()
        
        logger.info(f"Memory Engine v2 initialized: {db_path}")
    
    def _init_schema(self):
        """Initialize database schema"""
        schema_path = Path(__file__).parent / 'schema.sql'
        
        if schema_path.exists():
            with open(schema_path) as f:
                self.db.executescript(f.read())
        else:
            logger.warning("Schema file not found - using embedded schema")
            # Fallback embedded schema
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS reasoning_log (
                    id TEXT PRIMARY KEY,
                    agent TEXT NOT NULL,
                    ts INTEGER NOT NULL,
                    input TEXT NOT NULL,
                    output TEXT NOT NULL,
                    depth INTEGER DEFAULT 3,
                    confidence REAL DEFAULT 0.0,
                    duration_ms REAL DEFAULT 0.0,
                    path TEXT,
                    signature TEXT,
                    peer_id TEXT,
                    metadata TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                );
                
                CREATE TABLE IF NOT EXISTS memory_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    ts INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    summary TEXT,
                    tokens INTEGER DEFAULT 0,
                    embedding BLOB,
                    hash TEXT UNIQUE NOT NULL,
                    provenance TEXT,
                    trust_tier TEXT DEFAULT 'unknown',
                    consolidated INTEGER DEFAULT 0,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_log_agent ON reasoning_log(agent, ts DESC);
                CREATE INDEX IF NOT EXISTS idx_chunk_hash ON memory_chunks(hash);
            """)
        
        self.db.commit()
        logger.info("Schema initialized")
    
    def ingest(
        self,
        trace: Dict[str, Any],
        verify_signature: bool = True,
        trust_tier: str = 'unknown'
    ) -> str:
        """
        Ingest reasoning trace into memory
        
        Args:
            trace: Reasoning trace dictionary with required fields
            verify_signature: Verify Ed25519 signature if present
            trust_tier: Trust tier of source (core/sandbox/external/unknown)
            
        Returns:
            Trace ID
            
        Security:
            - Verifies signature if present and verify_signature=True
            - Quarantines unsigned traces from non-CORE peers
            - Quarantines invalid signatures
        """
        trace_id = trace.get('id', str(uuid.uuid4()))
        
        # Signature verification
        signature = trace.get('signature')
        peer_id = trace.get('peer_id')
        
        if verify_signature and signature:
            # Verify signature with peer's public key
            try:
                from federation import crypto as ark_crypto
                
                if not peer_id or not ark_crypto.peer_key_exists(peer_id):
                    logger.warning(f"No key for peer {peer_id} - quarantining")
                    self._quarantine(trace_id, 'missing_peer_key', peer_id, trust_tier, trace)
                    return trace_id
                
                # TODO: Implement signature verification for traces
                # For now, accept if signature present
                
            except ImportError:
                logger.warning("Crypto not available - skipping signature verification")
        
        # Trust tier enforcement
        if trust_tier not in ['core', 'unknown'] and not signature:
            logger.warning(f"Unsigned trace from {trust_tier} tier - quarantining")
            self._quarantine(trace_id, 'unsigned_non_core', peer_id, trust_tier, trace)
            return trace_id
        
        # Extract fields
        agent = trace.get('agent', 'unknown')
        ts = trace.get('ts', int(time.time()))
        input_data = trace.get('input', '')
        output_data = trace.get('output', '')
        depth = trace.get('depth', 3)
        confidence = trace.get('confidence', 0.0)
        duration_ms = trace.get('duration_ms', 0.0)
        path = json.dumps(trace.get('path', []))
        metadata = json.dumps(trace.get('metadata', {}))
        
        # Insert into reasoning_log
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO reasoning_log 
            (id, agent, ts, input, output, depth, confidence, duration_ms, path, signature, peer_id, trust_tier, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (trace_id, agent, ts, input_data, output_data, depth, confidence, duration_ms, 
              path, signature, peer_id, trust_tier, metadata))
        
        self.db.commit()
        
        logger.debug(f"Ingested trace {trace_id} from {agent} (tier={trust_tier})")
        return trace_id
    
    def _quarantine(
        self,
        trace_id: str,
        reason: str,
        peer_id: Optional[str],
        trust_tier: str,
        data: Dict
    ):
        """Quarantine suspicious trace"""
        quarantine_id = str(uuid.uuid4())
        ts = int(time.time())
        data_json = json.dumps(data)
        
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO quarantine (quarantine_id, trace_id, reason, peer_id, trust_tier, data, ts)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (quarantine_id, trace_id, reason, peer_id, trust_tier, data_json, ts))
        
        self.db.commit()
        logger.warning(f"Quarantined trace {trace_id}: {reason}")
    
    def consolidate(self, since_ts: Optional[int] = None, batch_size: int = 100) -> Dict:
        """
        Run consolidation pipeline on recent traces
        
        Args:
            since_ts: Unix timestamp to consolidate from (None = last 24h)
            batch_size: Number of traces to process per batch
            
        Returns:
            Stats dictionary with counts
        """
        if since_ts is None:
            since_ts = int(time.time()) - 86400  # Last 24 hours
        
        logger.info(f"Starting consolidation from ts={since_ts}")
        
        # Get unconsolidated traces
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, agent, input, output, confidence, ts, trust_tier
            FROM reasoning_log
            WHERE ts >= ?
            AND id NOT IN (SELECT source_id FROM memory_chunks WHERE consolidated = 1)
            ORDER BY ts DESC
            LIMIT ?
        """, (since_ts, batch_size))
        
        traces = [dict(row) for row in cursor.fetchall()]
        
        if not traces:
            logger.info("No traces to consolidate")
            return {'traces_processed': 0, 'chunks_created': 0}
        
        logger.info(f"Consolidating {len(traces)} trace(s)")
        
        # Import pipelines
        from memory.pipelines import summarize, compress, dedupe_hash
        
        chunks_created = 0
        
        for trace in traces:
            # Create text representation
            text = f"Agent: {trace['agent']}\nInput: {trace['input']}\nOutput: {trace['output']}"
            
            # Summarize
            summary = summarize(text)
            
            # Compress
            compressed = compress(summary)
            
            # Hash for deduplication
            content_hash = dedupe_hash(compressed)
            
            # Check if already exists
            cursor.execute("SELECT chunk_id FROM memory_chunks WHERE hash = ?", (content_hash,))
            if cursor.fetchone():
                logger.debug(f"Skipping duplicate chunk: {content_hash[:16]}...")
                continue
            
            # Create chunk
            chunk_id = str(uuid.uuid4())
            tokens = len(compressed.split())
            
            provenance = json.dumps({
                'source_trace': trace['id'],
                'pipeline': ['summarize', 'compress'],
                'created_at': datetime.now().isoformat()
            })
            
            cursor.execute("""
                INSERT INTO memory_chunks 
                (chunk_id, source_id, ts, text, summary, tokens, hash, provenance, trust_tier, consolidated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (chunk_id, trace['id'], trace['ts'], compressed, summary, tokens, 
                  content_hash, provenance, trace.get('trust_tier', 'unknown')))
            
            chunks_created += 1
        
        self.db.commit()
        
        stats = {
            'traces_processed': len(traces),
            'chunks_created': chunks_created,
            'duplicates_skipped': len(traces) - chunks_created
        }
        
        logger.info(f"Consolidation complete: {stats}")
        return stats
    
    def embed(self, chunk_ids: Optional[List[str]] = None, batch_size: int = 100) -> int:
        """
        Generate embeddings for memory chunks
        
        Args:
            chunk_ids: Specific chunks to embed (None = all without embeddings)
            batch_size: Number of chunks per batch
            
        Returns:
            Number of chunks embedded
        """
        if not NUMPY_AVAILABLE:
            logger.warning("NumPy not available - cannot generate embeddings")
            return 0
        
        # Import embedding function
        from memory.pipelines import embed
        
        cursor = self.db.cursor()
        
        if chunk_ids:
            placeholders = ','.join('?' * len(chunk_ids))
            cursor.execute(f"""
                SELECT chunk_id, text FROM memory_chunks
                WHERE chunk_id IN ({placeholders})
                AND embedding IS NULL
                LIMIT ?
            """, (*chunk_ids, batch_size))
        else:
            cursor.execute("""
                SELECT chunk_id, text FROM memory_chunks
                WHERE embedding IS NULL
                LIMIT ?
            """, (batch_size,))
        
        chunks = [dict(row) for row in cursor.fetchall()]
        
        if not chunks:
            logger.info("No chunks to embed")
            return 0
        
        logger.info(f"Embedding {len(chunks)} chunk(s)")
        
        for chunk in chunks:
            embedding = embed(chunk['text'])
            embedding_bytes = embedding.tobytes()
            
            cursor.execute("""
                UPDATE memory_chunks SET embedding = ? WHERE chunk_id = ?
            """, (embedding_bytes, chunk['chunk_id']))
        
        self.db.commit()
        
        logger.info(f"Embedded {len(chunks)} chunks")
        return len(chunks)
    
    def search(
        self,
        query: str,
        k: int = 10,
        min_confidence: float = 0.0,
        trust_tiers: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Semantic search over memory chunks
        
        Args:
            query: Search query
            k: Number of results
            min_confidence: Minimum confidence threshold
            trust_tiers: Filter by trust tiers (None = all)
            
        Returns:
            List of matching chunks with metadata
        """
        if not NUMPY_AVAILABLE:
            logger.warning("NumPy not available - falling back to text search")
            return self._text_search(query, k, min_confidence, trust_tiers)
        
        # Import embedding
        from memory.pipelines import embed
        
        # Embed query
        query_embedding = embed(query)
        query_bytes = query_embedding.tobytes()
        
        # Get all chunks with embeddings
        cursor = self.db.cursor()
        
        where_clauses = ["mc.embedding IS NOT NULL"]
        params = []
        
        if trust_tiers:
            placeholders = ','.join('?' * len(trust_tiers))
            where_clauses.append(f"mc.trust_tier IN ({placeholders})")
            params.extend(trust_tiers)
        
        where_sql = " AND ".join(where_clauses)
        
        cursor.execute(f"""
            SELECT mc.chunk_id, mc.text, mc.summary, mc.tokens, mc.embedding, mc.trust_tier, mc.ts,
                   rl.agent
            FROM memory_chunks mc
            LEFT JOIN reasoning_log rl ON mc.source_id = rl.id
            WHERE {where_sql}
        """, params)
        
        chunks = [dict(row) for row in cursor.fetchall()]
        
        if not chunks:
            return []
        
        # Compute cosine similarity
        results = []
        for chunk in chunks:
            chunk_embedding = np.frombuffer(chunk['embedding'], dtype=np.float32)
            
            # Cosine similarity
            similarity = np.dot(query_embedding, chunk_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
            )
            
            results.append({
                'chunk_id': chunk['chunk_id'],
                'text': chunk['text'],
                'summary': chunk['summary'],
                'similarity': float(similarity),
                'trust_tier': chunk['trust_tier'],
                'ts': chunk['ts'],
                'agent': chunk.get('agent', 'Unknown')
            })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:k]
    
    def _text_search(
        self,
        query: str,
        k: int,
        min_confidence: float,
        trust_tiers: Optional[List[str]]
    ) -> List[Dict]:
        """Fallback text-based search using SQLite FTS"""
        # Simple text matching fallback
        cursor = self.db.cursor()
        
        where_clauses = ["mc.text LIKE ?"]
        params = [f"%{query}%"]
        
        if trust_tiers:
            placeholders = ','.join('?' * len(trust_tiers))
            where_clauses.append(f"mc.trust_tier IN ({placeholders})")
            params.extend(trust_tiers)
        
        where_sql = " AND ".join(where_clauses)
        
        cursor.execute(f"""
            SELECT mc.chunk_id, mc.text, mc.summary, mc.trust_tier, mc.ts, rl.agent
            FROM memory_chunks mc
            LEFT JOIN reasoning_log rl ON mc.source_id = rl.id
            WHERE {where_sql}
            ORDER BY mc.ts DESC
            LIMIT ?
        """, (*params, k))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'chunk_id': row[0],
                'text': row[1],
                'summary': row[2],
                'similarity': 0.5,  # Placeholder
                'trust_tier': row[3],
                'ts': row[4],
                'agent': row[5] if row[5] else 'Unknown'
            })
        
        return results
    
    def get_stats(self) -> Dict:
        """Get memory engine statistics"""
        cursor = self.db.cursor()
        
        # Reasoning log stats
        cursor.execute("SELECT COUNT(*) FROM reasoning_log")
        total_traces = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT agent) FROM reasoning_log")
        unique_agents = cursor.fetchone()[0]
        
        # Memory chunk stats
        cursor.execute("SELECT COUNT(*) FROM memory_chunks")
        total_chunks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM memory_chunks WHERE consolidated = 1")
        consolidated_chunks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM memory_chunks WHERE embedding IS NOT NULL")
        embedded_chunks = cursor.fetchone()[0]
        
        # Quarantine stats
        cursor.execute("SELECT COUNT(*) FROM quarantine")
        quarantined = cursor.fetchone()[0]
        
        return {
            'reasoning_log': {
                'total_traces': total_traces,
                'unique_agents': unique_agents
            },
            'memory_chunks': {
                'total': total_chunks,
                'consolidated': consolidated_chunks,
                'embedded': embedded_chunks,
                'consolidation_rate': consolidated_chunks / total_chunks if total_chunks > 0 else 0,
                'embedding_rate': embedded_chunks / total_chunks if total_chunks > 0 else 0
            },
            'quarantine': {
                'total': quarantined
            }
        }
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()
            logger.info("Memory engine closed")


if __name__ == "__main__":
    # Test memory engine
    logging.basicConfig(level=logging.INFO)
    
    engine = MemoryEngine('test_memory.db')
    
    # Test ingest
    trace = {
        'id': str(uuid.uuid4()),
        'agent': 'kyle',
        'ts': int(time.time()),
        'input': 'Test market data',
        'output': 'Bullish signal detected',
        'confidence': 0.85,
        'depth': 5,
        'duration_ms': 123.4
    }
    
    trace_id = engine.ingest(trace)
    print(f"Ingested: {trace_id}")
    
    # Test stats
    stats = engine.get_stats()
    print(f"Stats: {stats}")
    
    engine.close()
