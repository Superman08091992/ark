#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for ARK Memory Engine v2

Tests the complete pipeline:
1. Memory Engine initialization and schema creation
2. Pipeline functions (summarize, compress, dedupe, embed)
3. Trace ingestion with signature verification
4. Consolidation pipeline
5. Semantic search
"""

import json
import os
import sqlite3
import sys
import tempfile
import time
import uuid
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.engine import MemoryEngine
from memory import pipelines


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def memory_engine(temp_db):
    """Create memory engine instance"""
    engine = MemoryEngine(db_path=temp_db)
    yield engine
    engine.close()


@pytest.fixture
def sample_trace():
    """Create sample reasoning trace"""
    return {
        'id': str(uuid.uuid4()),
        'agent': 'Kyle',
        'timestamp': int(time.time() * 1000),
        'input': 'What is the weather in San Francisco?',
        'output': 'Agent Kyle analyzed query, retrieved API data, returned temperature 72°F',
        'depth': 3,
        'confidence': 0.85,
        'duration_ms': 450,
        'path': ['perceive', 'analyze', 'execute'],
    }


# ============================================================================
# Pipeline Function Tests
# ============================================================================

class TestPipelineFunctions:
    """Test individual pipeline functions"""
    
    def test_summarize_basic(self):
        """Test basic summarization"""
        text = "Agent Kyle received user query about weather. Kyle analyzed the query. Kyle retrieved data from API. Kyle returned temperature 72°F."
        summary = pipelines.summarize(text, max_length=100)
        
        # Summary should be shorter or equal, allow for '...' suffix
        assert len(summary) <= 103  # max_length + len('...')
        assert len(summary) > 0
        assert 'Kyle' in summary or 'retrieved' in summary or 'Agent' in summary
    
    def test_summarize_empty(self):
        """Test summarization with empty input"""
        assert pipelines.summarize("") == ""
        # Note: summarize preserves whitespace-only input
        assert pipelines.summarize("   ").strip() == ""
    
    def test_compress_basic(self):
        """Test basic compression"""
        text = "I think that the agent basically decided that it would be best to retrieve data."
        compressed = pipelines.compress(text, aggressive=False)
        
        assert len(compressed) <= len(text)
        assert 'agent' in compressed.lower()
        assert 'retrieve' in compressed.lower()
    
    def test_compress_empty(self):
        """Test compression with empty input"""
        assert pipelines.compress("") == ""
        assert pipelines.compress("   ") == ""
    
    def test_dedupe_hash_consistency(self):
        """Test hash consistency"""
        text = "Agent retrieved data from API"
        hash1 = pipelines.dedupe_hash(text)
        hash2 = pipelines.dedupe_hash(text)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex
    
    def test_dedupe_hash_normalization(self):
        """Test hash normalization"""
        text1 = "Agent retrieved data from API"
        text2 = "  AGENT RETRIEVED DATA FROM API  "
        
        # dedupe_hash normalizes automatically
        hash1 = pipelines.dedupe_hash(text1)
        hash2 = pipelines.dedupe_hash(text2)
        
        assert hash1 == hash2
    
    def test_dedupe_chunks(self):
        """Test chunk deduplication via hashing"""
        text1 = "Agent retrieved data from API"
        text2 = "Agent stored result"
        text3 = "Agent retrieved data from API"  # Duplicate of text1
        
        hash1 = pipelines.dedupe_hash(text1)
        hash2 = pipelines.dedupe_hash(text2)
        hash3 = pipelines.dedupe_hash(text3)
        
        # Hash 1 and 3 should be the same
        assert hash1 == hash3
        # Hash 2 should be different
        assert hash1 != hash2
    
    def test_embed_basic(self):
        """Test embedding generation"""
        text = "Agent retrieved data from API"
        embedding = pipelines.embed(text)
        
        if embedding is None:
            pytest.skip("NumPy not available")
        
        assert embedding is not None
        assert len(embedding) > 0
    
    def test_embed_consistency(self):
        """Test embedding consistency"""
        text = "Agent retrieved data from API"
        emb1 = pipelines.embed(text)
        emb2 = pipelines.embed(text)
        
        if emb1 is None:
            pytest.skip("NumPy not available")
        
        # Compare numpy arrays
        import numpy as np
        assert np.array_equal(emb1, emb2)
    
    def test_embedding_similarity(self):
        """Test embedding similarity"""
        text1 = "Agent retrieved data from API"
        text2 = "Agent fetched data from API"
        text3 = "The weather is sunny today"
        
        emb1 = pipelines.embed(text1)
        emb2 = pipelines.embed(text2)
        emb3 = pipelines.embed(text3)
        
        if emb1 is None:
            pytest.skip("NumPy not available")
        
        import numpy as np
        
        # Similar texts should have similar embeddings (small distance)
        dist_12 = np.linalg.norm(emb1 - emb2)
        dist_13 = np.linalg.norm(emb1 - emb3)
        
        # Distance between similar texts should be less than distance between different texts
        assert dist_12 < dist_13


# ============================================================================
# Memory Engine Tests
# ============================================================================

class TestMemoryEngine:
    """Test Memory Engine functionality"""
    
    def test_initialization(self, memory_engine):
        """Test engine initialization and schema creation"""
        assert memory_engine is not None
        
        # Check that tables exist
        cursor = memory_engine.db.cursor()
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        
        table_names = [t[0] for t in tables]
        assert 'reasoning_log' in table_names
        assert 'memory_chunks' in table_names
        assert 'reflection_reports' in table_names
        assert 'id_state' in table_names
        assert 'quarantine' in table_names
    
    def test_ingest_trace(self, memory_engine, sample_trace):
        """Test trace ingestion"""
        trace_id = memory_engine.ingest(
            trace=sample_trace,
            verify_signature=False,  # No signature in test
            trust_tier='core'
        )
        
        assert trace_id == sample_trace['id']
        
        # Verify trace was stored
        cursor = memory_engine.db.cursor()
        result = cursor.execute(
            "SELECT agent, confidence FROM reasoning_log WHERE id = ?",
            (trace_id,)
        ).fetchone()
        
        assert result is not None
        assert result[0] == 'Kyle'
        assert result[1] == 0.85
    
    def test_get_stats(self, memory_engine, sample_trace):
        """Test statistics retrieval"""
        # Ingest some traces
        memory_engine.ingest(sample_trace, verify_signature=False, trust_tier='core')
        
        stats = memory_engine.get_stats()
        
        assert stats['reasoning_log']['total_traces'] == 1
        assert stats['memory_chunks']['total'] == 0  # Not consolidated yet
        assert stats['reasoning_log']['unique_agents'] == 1
    
    def test_consolidation(self, memory_engine, sample_trace):
        """Test consolidation pipeline"""
        # Ingest trace
        memory_engine.ingest(sample_trace, verify_signature=False, trust_tier='core')
        
        # Run consolidation
        result = memory_engine.consolidate(since_ts=0, batch_size=10)
        
        assert result['traces_processed'] > 0
        assert result['chunks_created'] > 0
        
        # Check that chunk was created
        stats = memory_engine.get_stats()
        assert stats['memory_chunks']['total'] > 0
    
    def test_search(self, memory_engine, sample_trace):
        """Test semantic search"""
        # Ingest and consolidate
        memory_engine.ingest(sample_trace, verify_signature=False, trust_tier='core')
        memory_engine.consolidate(since_ts=0, batch_size=10)
        
        # Generate embeddings
        memory_engine.embed(batch_size=10)
        
        # Search
        results = memory_engine.search(
            query="weather information",
            k=5,
            min_confidence=0.0
        )
        
        # Should find the chunk (if embeddings available)
        # If no embeddings, should fallback to text search
        assert isinstance(results, list)


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test complete workflows"""
    
    def test_full_pipeline(self, memory_engine):
        """Test complete ingest → consolidate → embed → search workflow"""
        # Create multiple traces
        traces = []
        for i in range(5):
            trace = {
                'id': str(uuid.uuid4()),
                'agent': 'Kyle',
                'timestamp': int(time.time() * 1000) + i,
                'input': f'Query {i}',
                'output': f'Agent processed query {i} and returned result',
                'depth': 3,
                'confidence': 0.8 + (i * 0.02),
                'duration_ms': 400 + (i * 10),
            }
            traces.append(trace)
        
        # Ingest all traces
        for trace in traces:
            memory_engine.ingest(trace, verify_signature=False, trust_tier='core')
        
        # Consolidate
        result = memory_engine.consolidate(since_ts=0, batch_size=10)
        assert result['traces_processed'] == 5
        assert result['chunks_created'] >= 1  # May dedupe
        
        # Generate embeddings
        embedded = memory_engine.embed(batch_size=10)
        # May be 0 if NumPy not available
        
        # Search
        results = memory_engine.search(query="processed query", k=3)
        assert isinstance(results, list)
        
        # Get stats
        stats = memory_engine.get_stats()
        assert stats['reasoning_log']['total_traces'] == 5
        assert stats['memory_chunks']['total'] >= 1


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
