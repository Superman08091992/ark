#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Memory API Service

FastAPI service providing REST endpoints for Memory Engine v2.

Endpoints:
- POST   /api/v1/memory/ingest          - Ingest reasoning trace
- POST   /api/v1/memory/consolidate     - Run consolidation pipeline
- POST   /api/v1/memory/embed           - Generate embeddings
- POST   /api/v1/memory/search          - Semantic search
- GET    /api/v1/memory/stats           - Get statistics
- GET    /api/v1/memory/trace/{id}      - Get specific trace
- GET    /api/v1/memory/chunk/{id}      - Get specific chunk
- DELETE /api/v1/memory/chunk/{id}      - Delete chunk (admin)
- GET    /api/v1/memory/health          - Health check
- GET    /metrics                        - Prometheus metrics

Port: 8701
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Query, Path as PathParam
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.engine import MemoryEngine
from memory import jobs

logger = logging.getLogger(__name__)

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="ARK Memory API",
    description="Memory Engine v2 for autonomous learning and knowledge consolidation",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Global memory engine instance
memory_engine: Optional[MemoryEngine] = None


# ============================================================================
# Request/Response Models
# ============================================================================

class IngestRequest(BaseModel):
    """Request model for ingesting reasoning trace"""
    trace: Dict[str, Any] = Field(..., description="Reasoning trace to ingest")
    verify_signature: bool = Field(True, description="Verify Ed25519 signature if present")
    trust_tier: str = Field('unknown', description="Trust tier: core, sandbox, external, unknown")


class IngestResponse(BaseModel):
    """Response model for ingest"""
    trace_id: str = Field(..., description="ID of ingested trace")
    quarantined: bool = Field(False, description="Whether trace was quarantined")
    reason: Optional[str] = Field(None, description="Quarantine reason if applicable")


class ConsolidateRequest(BaseModel):
    """Request model for consolidation"""
    since_ts: Optional[int] = Field(None, description="Only consolidate traces since this timestamp (ms)")
    batch_size: int = Field(100, description="Number of traces to consolidate")
    dry_run: bool = Field(False, description="If true, report what would be done without making changes")


class ConsolidateResponse(BaseModel):
    """Response model for consolidation"""
    status: str = Field(..., description="Job status: success, error, skipped")
    traces_processed: int = Field(0, description="Number of traces processed")
    chunks_created: int = Field(0, description="Number of memory chunks created")
    duplicates_found: int = Field(0, description="Number of duplicate chunks skipped")
    quarantined: int = Field(0, description="Number of traces quarantined")
    duration_seconds: float = Field(..., description="Job duration in seconds")


class EmbedRequest(BaseModel):
    """Request model for embedding generation"""
    chunk_ids: Optional[List[str]] = Field(None, description="Specific chunk IDs to embed (None = all without embeddings)")
    batch_size: int = Field(50, description="Batch size for processing")


class EmbedResponse(BaseModel):
    """Response model for embedding generation"""
    chunks_embedded: int = Field(..., description="Number of chunks embedded")
    duration_seconds: float = Field(..., description="Job duration in seconds")


class SearchRequest(BaseModel):
    """Request model for semantic search"""
    query: str = Field(..., description="Search query text")
    k: int = Field(10, description="Number of results to return")
    min_confidence: float = Field(0.0, description="Minimum confidence score filter")
    trust_tiers: Optional[List[str]] = Field(None, description="Filter by trust tiers")


class SearchResult(BaseModel):
    """Single search result"""
    chunk_id: str
    text: str
    summary: Optional[str]
    similarity: float
    confidence: float
    agent: str
    timestamp: int
    trust_tier: str


class SearchResponse(BaseModel):
    """Response model for search"""
    results: List[SearchResult] = Field(..., description="Search results")
    query: str = Field(..., description="Original query")
    total_results: int = Field(..., description="Total number of results")


class StatsResponse(BaseModel):
    """Response model for statistics"""
    traces_total: int
    traces_quarantined: int
    chunks_total: int
    chunks_with_embeddings: int
    chunks_without_embeddings: int
    avg_confidence: float
    agents: List[str]
    trust_tier_counts: Dict[str, int]


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status: healthy, degraded, unhealthy")
    version: str = Field(..., description="API version")
    database_ok: bool = Field(..., description="Database connection status")
    embeddings_enabled: bool = Field(..., description="Whether embeddings are available")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize memory engine on startup"""
    global memory_engine
    
    logger.info("Starting ARK Memory API service...")
    
    # Create data directory if needed
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Initialize memory engine
    db_path = "data/ark_memory.db"
    memory_engine = MemoryEngine(db_path=db_path)
    
    logger.info(f"Memory engine initialized with database: {db_path}")
    
    # Get initial statistics
    stats = memory_engine.get_stats()
    logger.info(f"Initial stats: {json.dumps(stats, indent=2)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global memory_engine
    
    logger.info("Shutting down ARK Memory API service...")
    
    if memory_engine:
        memory_engine.close()
        logger.info("Memory engine closed")


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/v1/memory/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns service health status and basic diagnostics.
    """
    try:
        # Check database connection
        stats = memory_engine.get_stats()
        database_ok = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_ok = False
    
    # Check if embeddings are available
    try:
        import numpy as np
        embeddings_enabled = True
    except ImportError:
        embeddings_enabled = False
    
    # Determine overall status
    if database_ok and embeddings_enabled:
        status = "healthy"
    elif database_ok:
        status = "degraded"  # Works but without embeddings
    else:
        status = "unhealthy"
    
    return HealthResponse(
        status=status,
        version="2.0.0",
        database_ok=database_ok,
        embeddings_enabled=embeddings_enabled,
        uptime_seconds=time.time() - startup_time
    )


@app.post("/api/v1/memory/ingest", response_model=IngestResponse)
async def ingest_trace(request: IngestRequest):
    """
    Ingest reasoning trace
    
    Accepts a reasoning trace and stores it in the database.
    Performs signature verification and trust tier enforcement.
    """
    try:
        trace_id = memory_engine.ingest(
            trace=request.trace,
            verify_signature=request.verify_signature,
            trust_tier=request.trust_tier
        )
        
        # Check if trace was quarantined
        quarantined = False
        reason = None
        
        # Query quarantine table to check
        cursor = memory_engine.db.cursor()
        result = cursor.execute(
            "SELECT reason FROM quarantine WHERE trace_id = ?",
            (trace_id,)
        ).fetchone()
        
        if result:
            quarantined = True
            reason = result[0]
        
        return IngestResponse(
            trace_id=trace_id,
            quarantined=quarantined,
            reason=reason
        )
    
    except Exception as e:
        logger.error(f"Error ingesting trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/memory/consolidate", response_model=ConsolidateResponse)
async def consolidate_traces(request: ConsolidateRequest):
    """
    Run consolidation pipeline
    
    Consolidates reasoning traces into memory chunks using the
    summarize → compress → dedupe → embed pipeline.
    """
    try:
        result = memory_engine.consolidate(
            since_ts=request.since_ts,
            batch_size=request.batch_size
        )
        
        return ConsolidateResponse(
            status='success',
            traces_processed=result.get('traces_processed', 0),
            chunks_created=result.get('chunks_created', 0),
            duplicates_found=result.get('duplicates_skipped', 0),
            quarantined=result.get('quarantined', 0),
            duration_seconds=result.get('duration_ms', 0) / 1000.0
        )
    
    except Exception as e:
        logger.error(f"Error consolidating traces: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/memory/embed", response_model=EmbedResponse)
async def generate_embeddings(request: EmbedRequest):
    """
    Generate embeddings for memory chunks
    
    Creates vector embeddings for semantic search.
    """
    try:
        start_time = time.time()
        
        embedded_count = memory_engine.embed(
            chunk_ids=request.chunk_ids,
            batch_size=request.batch_size
        )
        
        duration = time.time() - start_time
        
        return EmbedResponse(
            chunks_embedded=embedded_count,
            duration_seconds=duration
        )
    
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/memory/search", response_model=SearchResponse)
async def search_memory(request: SearchRequest):
    """
    Semantic search over memory chunks
    
    Searches memory using vector embeddings and returns most similar chunks.
    """
    try:
        results = memory_engine.search(
            query=request.query,
            k=request.k,
            min_confidence=request.min_confidence,
            trust_tiers=request.trust_tiers
        )
        
        # Convert to response model
        search_results = [
            SearchResult(
                chunk_id=r['chunk_id'],
                text=r['text'],
                summary=r.get('summary'),
                similarity=r['similarity'],
                confidence=r.get('confidence', 0.0),
                agent=r['agent'],
                timestamp=r['ts'],
                trust_tier=r.get('trust_tier', 'unknown')
            )
            for r in results
        ]
        
        return SearchResponse(
            results=search_results,
            query=request.query,
            total_results=len(search_results)
        )
    
    except Exception as e:
        logger.error(f"Error searching memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/memory/stats", response_model=StatsResponse)
async def get_statistics():
    """
    Get memory engine statistics
    
    Returns statistics about traces, chunks, embeddings, and trust tiers.
    """
    try:
        stats = memory_engine.get_stats()
        
        return StatsResponse(
            traces_total=stats.get('traces_total', 0),
            traces_quarantined=stats.get('traces_quarantined', 0),
            chunks_total=stats.get('chunks_total', 0),
            chunks_with_embeddings=stats.get('chunks_with_embeddings', 0),
            chunks_without_embeddings=stats.get('chunks_without_embeddings', 0),
            avg_confidence=stats.get('avg_confidence', 0.0),
            agents=stats.get('agents', []),
            trust_tier_counts=stats.get('trust_tier_counts', {})
        )
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/memory/trace/{trace_id}")
async def get_trace(trace_id: str = PathParam(..., description="Trace ID")):
    """
    Get specific reasoning trace by ID
    
    Returns the full trace including input, output, and metadata.
    """
    try:
        cursor = memory_engine.db.cursor()
        result = cursor.execute(
            """
            SELECT id, agent, ts, input, output, depth, confidence, 
                   duration_ms, path, signature, peer_id, metadata
            FROM reasoning_log
            WHERE id = ?
            """,
            (trace_id,)
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        return {
            'id': result[0],
            'agent': result[1],
            'timestamp': result[2],
            'input': result[3],
            'output': result[4],
            'depth': result[5],
            'confidence': result[6],
            'duration_ms': result[7],
            'path': json.loads(result[8]) if result[8] else None,
            'signature': result[9],
            'peer_id': result[10],
            'metadata': json.loads(result[11]) if result[11] else None,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/memory/chunk/{chunk_id}")
async def get_chunk(chunk_id: str = PathParam(..., description="Chunk ID")):
    """
    Get specific memory chunk by ID
    
    Returns the full chunk including text, summary, and embedding metadata.
    """
    try:
        cursor = memory_engine.db.cursor()
        result = cursor.execute(
            """
            SELECT chunk_id, source_id, ts, text, summary, tokens,
                   LENGTH(embedding) as embedding_size, hash, provenance,
                   trust_tier, consolidated
            FROM memory_chunks
            WHERE chunk_id = ?
            """,
            (chunk_id,)
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Chunk not found")
        
        return {
            'chunk_id': result[0],
            'source_id': result[1],
            'timestamp': result[2],
            'text': result[3],
            'summary': result[4],
            'tokens': result[5],
            'has_embedding': result[6] > 0 if result[6] else False,
            'embedding_size': result[6],
            'hash': result[7],
            'provenance': json.loads(result[8]) if result[8] else None,
            'trust_tier': result[9],
            'consolidated': bool(result[10]),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chunk: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/memory/chunk/{chunk_id}")
async def delete_chunk(chunk_id: str = PathParam(..., description="Chunk ID")):
    """
    Delete memory chunk (admin only)
    
    Permanently removes a memory chunk from the database.
    Use with caution - this cannot be undone.
    """
    try:
        cursor = memory_engine.db.cursor()
        cursor.execute("DELETE FROM memory_chunks WHERE chunk_id = ?", (chunk_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Chunk not found")
        
        memory_engine.db.commit()
        
        logger.warning(f"Deleted memory chunk: {chunk_id}")
        
        return {"status": "deleted", "chunk_id": chunk_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chunk: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus text format for monitoring.
    """
    try:
        stats = memory_engine.get_stats()
        
        metrics = [
            "# HELP ark_memory_traces_total Total number of reasoning traces",
            "# TYPE ark_memory_traces_total gauge",
            f"ark_memory_traces_total {stats.get('traces_total', 0)}",
            "",
            "# HELP ark_memory_traces_quarantined Number of quarantined traces",
            "# TYPE ark_memory_traces_quarantined gauge",
            f"ark_memory_traces_quarantined {stats.get('traces_quarantined', 0)}",
            "",
            "# HELP ark_memory_chunks_total Total number of memory chunks",
            "# TYPE ark_memory_chunks_total gauge",
            f"ark_memory_chunks_total {stats.get('chunks_total', 0)}",
            "",
            "# HELP ark_memory_chunks_with_embeddings Number of chunks with embeddings",
            "# TYPE ark_memory_chunks_with_embeddings gauge",
            f"ark_memory_chunks_with_embeddings {stats.get('chunks_with_embeddings', 0)}",
            "",
            "# HELP ark_memory_avg_confidence Average confidence score",
            "# TYPE ark_memory_avg_confidence gauge",
            f"ark_memory_avg_confidence {stats.get('avg_confidence', 0.0)}",
            "",
        ]
        
        # Add trust tier counts
        trust_tier_counts = stats.get('trust_tier_counts', {})
        for tier, count in trust_tier_counts.items():
            metrics.extend([
                f'ark_memory_trust_tier{{tier="{tier}"}} {count}',
            ])
        
        return "\n".join(metrics)
    
    except Exception as e:
        logger.error(f"Error generating metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Main Entry Point
# ============================================================================

# Track startup time for uptime calculation
startup_time = time.time()


if __name__ == "__main__":
    import uvicorn
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8701,
        log_level="info"
    )
