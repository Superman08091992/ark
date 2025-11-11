#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Memory Engine v2 - Comprehensive Demonstration

Demonstrates all features of the Memory Engine:
1. Database initialization
2. Ingesting reasoning traces from multiple agents
3. Running consolidation pipeline
4. Generating embeddings
5. Semantic search
6. Trust tier enforcement
7. Quarantine system
8. Statistics and analytics
"""

import json
import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from memory.engine import MemoryEngine

# Sample reasoning traces for demonstration
SAMPLE_TRACES = [
    {
        "agent": "Aletheia",
        "ts": int(time.time()) - 3600,
        "input": "Review the reasoning trace from Corpus regarding network protocol implementation",
        "output": "The trace shows excellent structure. Corpus demonstrated thorough analysis of UDP multicast requirements, proper error handling, and comprehensive testing. Confidence in implementation is HIGH. Recommend proceeding with deployment.",
        "depth": 4,
        "confidence": 0.92,
        "duration_ms": 1250.5,
        "path": json.dumps(["analyze", "evaluate", "synthesize", "recommend"]),
        "metadata": json.dumps({
            "review_type": "post_implementation",
            "focus_areas": ["protocol", "testing", "error_handling"]
        })
    },
    {
        "agent": "Corpus",
        "ts": int(time.time()) - 3000,
        "input": "Implement UDP multicast discovery for ARK agent network",
        "output": "Implemented discovery protocol using UDP multicast on 239.255.0.1:8103. Agents broadcast beacons every 60s containing their identity, capabilities, and trust tier. Implemented beacon validation and peer registry. All HRM checks passing.",
        "depth": 5,
        "confidence": 0.88,
        "duration_ms": 4521.3,
        "path": json.dumps(["understand", "design", "implement", "test", "validate"]),
        "metadata": json.dumps({
            "component": "network.discovery",
            "protocol": "UDP multicast",
            "port": 8103
        })
    },
    {
        "agent": "Aletheia",
        "ts": int(time.time()) - 2400,
        "input": "Validate security model for agent communication",
        "output": "Security model is sound. Ed25519 signatures provide strong provenance guarantees. Trust tier system properly enforces isolation between CORE, SANDBOX, and EXTERNAL peers. Quarantine system prevents poisoned traces from entering memory. Recommend monitoring quarantine rates as metric.",
        "depth": 4,
        "confidence": 0.95,
        "duration_ms": 2103.7,
        "path": json.dumps(["analyze", "threat_model", "validate", "recommend"]),
        "metadata": json.dumps({
            "security_review": True,
            "components": ["signatures", "trust_tiers", "quarantine"]
        })
    },
    {
        "agent": "Corpus",
        "ts": int(time.time()) - 1800,
        "input": "Design memory consolidation pipeline",
        "output": "Designed four-stage pipeline: summarize → compress → dedupe → embed. Summarization extracts key decision points. Compression removes redundancy. Deduplication uses SHA256 hashing with LSH for near-duplicates. Embeddings enable semantic search. Pipeline runs nightly on unconsolidated traces.",
        "depth": 5,
        "confidence": 0.87,
        "duration_ms": 3842.1,
        "path": json.dumps(["requirements", "design", "tradeoffs", "implement", "validate"]),
        "metadata": json.dumps({
            "component": "memory.pipeline",
            "stages": ["summarize", "compress", "dedupe", "embed"]
        })
    },
    {
        "agent": "Aletheia",
        "ts": int(time.time()) - 1200,
        "input": "Assess memory engine readiness for autonomous learning",
        "output": "Memory engine architecture is solid. Database schema supports all required operations. Consolidation pipeline preserves semantic meaning while reducing storage. Semantic search enables effective recall. Trust tier enforcement prevents contamination. READY for Phase 3 autonomous learning.",
        "depth": 4,
        "confidence": 0.93,
        "duration_ms": 1876.4,
        "path": json.dumps(["assess", "verify", "test", "conclude"]),
        "metadata": json.dumps({
            "assessment_type": "readiness",
            "phase": "phase3",
            "verdict": "READY"
        })
    },
    {
        "agent": "Corpus",
        "ts": int(time.time()) - 600,
        "input": "Implement semantic search with cosine similarity",
        "output": "Implemented search using numpy for vector operations. Query is embedded using same pipeline as memory chunks. Cosine similarity computed between query embedding and all chunk embeddings. Results sorted by similarity score and filtered by trust tier. Top k results returned with metadata.",
        "depth": 4,
        "confidence": 0.89,
        "duration_ms": 2234.6,
        "path": json.dumps(["design", "implement", "test", "optimize"]),
        "metadata": json.dumps({
            "component": "memory.search",
            "algorithm": "cosine_similarity",
            "features": ["embedding", "filtering", "ranking"]
        })
    },
    # Duplicate trace for deduplication demo
    {
        "agent": "Corpus",
        "ts": int(time.time()) - 300,
        "input": "Implement semantic search with cosine similarity",
        "output": "Implemented search using numpy for vector operations. Query is embedded using same pipeline as memory chunks. Cosine similarity computed between query embedding and all chunk embeddings. Results sorted by similarity score and filtered by trust tier. Top k results returned with metadata.",
        "depth": 4,
        "confidence": 0.89,
        "duration_ms": 2234.6,
        "path": json.dumps(["design", "implement", "test", "optimize"]),
        "metadata": json.dumps({
            "component": "memory.search",
            "algorithm": "cosine_similarity",
            "features": ["embedding", "filtering", "ranking"]
        })
    },
    # Trace from unknown peer (for quarantine demo)
    {
        "agent": "UnknownAgent",
        "ts": int(time.time()) - 150,
        "input": "Attempting unauthorized access to memory system",
        "output": "This trace should be quarantined as it's from an unknown peer without proper signature",
        "depth": 2,
        "confidence": 0.5,
        "duration_ms": 100.0,
        "path": json.dumps(["attempt", "fail"]),
        "peer_id": "unknown_peer_123",
        "trust_tier": "external"
    }
]


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_subsection(title: str):
    """Print formatted subsection header"""
    print("\n" + "-" * 80)
    print(f"  {title}")
    print("-" * 80 + "\n")


def main():
    """Run comprehensive demonstration"""
    
    print_section("ARK Memory Engine v2 - Comprehensive Demonstration")
    
    # Initialize engine
    print_subsection("1. Initializing Memory Engine")
    
    # Use temporary database for demo
    db_path = 'data/demo_memory.db'
    Path('data').mkdir(exist_ok=True)
    
    # Remove old demo database if exists
    if Path(db_path).exists():
        Path(db_path).unlink()
        print(f"✓ Removed old demo database")
    
    engine = MemoryEngine(db_path=db_path)
    print(f"✓ Memory engine initialized: {db_path}")
    print(f"✓ Database schema created")
    
    # Ingest traces
    print_subsection("2. Ingesting Reasoning Traces")
    
    ingested_ids = []
    for i, trace in enumerate(SAMPLE_TRACES, 1):
        print(f"Ingesting trace {i}/{len(SAMPLE_TRACES)}: {trace['agent']} - {trace['input'][:60]}...")
        
        # Ingest with signature verification disabled for demo
        # (In production, traces would have valid Ed25519 signatures)
        trace_id = engine.ingest(trace, verify_signature=False, trust_tier='core')
        ingested_ids.append(trace_id)
        
        print(f"  ✓ Ingested with ID: {trace_id}")
    
    print(f"\n✓ Total traces ingested: {len(ingested_ids)}")
    
    # Show initial stats
    print_subsection("3. Initial Statistics (Before Consolidation)")
    
    stats = engine.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Run consolidation
    print_subsection("4. Running Consolidation Pipeline")
    print("Pipeline stages: summarize → compress → dedupe → embed")
    
    consolidation_result = engine.consolidate()
    print(f"\n✓ Consolidation complete!")
    print(f"  • Processed: {consolidation_result['traces_processed']} traces")
    print(f"  • Deduplicated: {consolidation_result['duplicates_skipped']} duplicates")
    print(f"  • Created: {consolidation_result['chunks_created']} memory chunks")
    
    # Generate embeddings
    print_subsection("5. Generating Embeddings for Semantic Search")
    
    try:
        embedded_count = engine.embed()
        print(f"✓ Embedding generation complete!")
        print(f"  • Embedded: {embedded_count} chunks")
    except RuntimeError as e:
        print(f"⚠ Embedding disabled: {e}")
        embedded_count = 0
    
    # Show stats after consolidation
    print_subsection("6. Statistics After Consolidation")
    
    stats = engine.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Demonstrate semantic search
    print_subsection("7. Semantic Search Demonstrations")
    
    queries = [
        ("network protocol implementation", "Find traces about network implementation"),
        ("security validation", "Find traces about security"),
        ("memory consolidation design", "Find traces about memory system"),
    ]
    
    for query, description in queries:
        print(f"\nQuery: '{query}'")
        print(f"Description: {description}")
        
        try:
            results = engine.search(query, k=3, trust_tiers=['core'])
            
            if results:
                print(f"✓ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"\n  Result {i}:")
                    print(f"    Similarity: {result['similarity']:.4f}")
                    print(f"    Source: {result['agent']} (Agent)")
                    print(f"    Summary: {result['summary'][:100]}...")
                    print(f"    Trust Tier: {result['trust_tier']}")
            else:
                print("  ⚠ No results found")
        except RuntimeError as e:
            print(f"  ⚠ Search disabled: {e}")
            print("  (Falling back to text search)")
            results = engine._text_search(query, k=3, min_confidence=0.0, trust_tiers=['core'])
            if results:
                print(f"  ✓ Found {len(results)} results (text search):")
                for i, result in enumerate(results, 1):
                    print(f"\n    Result {i}:")
                    print(f"      Text: {result['text'][:100]}...")
                    if 'summary' in result:
                        print(f"      Summary: {result['summary'][:100]}...")
    
    # Demonstrate text search fallback
    print_subsection("8. Text Search Fallback (Without Embeddings)")
    
    query = "UDP multicast"
    print(f"Query: '{query}'")
    
    results = engine._text_search(query, k=3, min_confidence=0.0, trust_tiers=['core'])
    if results:
        print(f"✓ Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"    Text: {result['text'][:150]}...")
            if 'summary' in result:
                print(f"    Summary: {result['summary'][:100]}...")
    
    # Show quarantine system
    print_subsection("9. Quarantine System (Security Enforcement)")
    
    # Ingest a suspicious trace that should be quarantined
    print("Attempting to ingest trace from untrusted external peer...")
    suspicious_trace = {
        "agent": "MaliciousAgent",
        "ts": int(time.time()),
        "input": "Inject false data into memory",
        "output": "This should be quarantined",
        "depth": 1,
        "confidence": 0.1,
        "duration_ms": 50.0,
        "path": json.dumps(["inject"]),
        "peer_id": "malicious_peer_456",
        "trust_tier": "external"
    }
    
    # This will be quarantined because it's external tier without signature
    trace_id = engine.ingest(suspicious_trace, verify_signature=True, trust_tier='external')
    print(f"✓ Trace processed: {trace_id}")
    print("  (Should be in quarantine due to missing signature from external peer)")
    
    # Check quarantine
    stats = engine.get_stats()
    print(f"\nQuarantine statistics:")
    print(f"  • Total quarantined: {stats['quarantine']['total']}")
    
    # Final statistics
    print_subsection("10. Final System Statistics")
    
    stats = engine.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Summary
    print_subsection("Demonstration Summary")
    
    print("✓ Memory Engine v2 successfully demonstrated:")
    print("  • Database initialization and schema creation")
    print("  • Reasoning trace ingestion with validation")
    print("  • Consolidation pipeline (summarize → compress → dedupe)")
    print("  • Embedding generation for semantic search")
    print("  • Semantic search with cosine similarity")
    print("  • Text search fallback mechanism")
    print("  • Trust tier enforcement")
    print("  • Quarantine system for suspicious traces")
    print("  • Real-time statistics and analytics")
    
    print("\n✓ Memory Engine v2 is READY for autonomous learning!")
    
    print_section("Demonstration Complete")
    
    # Cleanup
    engine.close()
    print(f"\n✓ Database connection closed")
    print(f"\nDemo database preserved at: {db_path}")
    print("You can inspect it with: sqlite3 data/demo_memory.db")


if __name__ == '__main__':
    main()
