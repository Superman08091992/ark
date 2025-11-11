#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Reflection API

FastAPI endpoints for reflection system:
- Trigger manual reflection cycles
- Query reflection statistics
- View reflection insights
- Configure reflection policies
"""

import logging
from typing import Dict, List, Optional

try:
    from fastapi import APIRouter, HTTPException, Query
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.warning("FastAPI not available - API endpoints disabled")

from reflection.reflection_engine import ReflectionEngine

logger = logging.getLogger(__name__)

# Create API router
if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/api/reflection", tags=["Reflection"])
else:
    # Dummy router for import compatibility
    class DummyRouter:
        def post(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
        
        def get(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
    
    router = DummyRouter()


# Request/Response models
if FASTAPI_AVAILABLE:
    class ReflectionTriggerResponse(BaseModel):
        status: str
        message: str
        result: Dict
    
    class ReflectionStatsResponse(BaseModel):
        total_reflections: int
        reflections_by_type: Dict[str, int]
        recent_24h: int
        avg_confidence_delta: float
    
    class ReflectionListResponse(BaseModel):
        reflections: List[Dict]
        total: int
        limit: int
        offset: int


# Global engine instance (initialized on first request)
_engine = None


def get_engine() -> ReflectionEngine:
    """Get or create reflection engine instance"""
    global _engine
    if _engine is None:
        _engine = ReflectionEngine(
            db_path='data/demo_memory.db',
            policy_path='reflection/reflection_policies.yaml'
        )
    return _engine


@router.post("/sleep", response_model=ReflectionTriggerResponse if FASTAPI_AVAILABLE else None)
def sleep_now():
    """
    Trigger reflection cycle manually
    
    This endpoint allows manual triggering of the reflection process
    outside of the normal scheduled midnight runs.
    
    Returns:
        ReflectionTriggerResponse with status and results
    """
    try:
        engine = get_engine()
        result = engine.generate_reflections()
        
        return {
            "status": "ok",
            "message": "Reflection cycle executed manually",
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Manual reflection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reflection failed: {str(e)}")


@router.get("/stats", response_model=ReflectionStatsResponse if FASTAPI_AVAILABLE else None)
def get_stats():
    """
    Get reflection statistics
    
    Returns:
        ReflectionStatsResponse with comprehensive statistics
    """
    try:
        engine = get_engine()
        stats = engine.get_stats()
        
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/list", response_model=ReflectionListResponse if FASTAPI_AVAILABLE else None)
def list_reflections(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    reflection_type: Optional[str] = Query(default=None)
):
    """
    List recent reflections
    
    Args:
        limit: Maximum number of reflections to return (1-500)
        offset: Number of reflections to skip (pagination)
        reflection_type: Filter by reflection type (optional)
    
    Returns:
        ReflectionListResponse with list of reflections
    """
    try:
        engine = get_engine()
        cursor = engine.db.cursor()
        
        # Build query
        where_clause = ""
        params = []
        
        if reflection_type:
            where_clause = "WHERE reflection_type = ?"
            params.append(reflection_type)
        
        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM reflections {where_clause}", params)
        total = cursor.fetchone()[0]
        
        # Get reflections
        cursor.execute(f"""
            SELECT 
                reflection_id,
                timestamp,
                chunk_id,
                tier,
                insight,
                confidence,
                confidence_delta,
                reflection_type
            FROM reflections
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])
        
        reflections = []
        for row in cursor.fetchall():
            reflections.append({
                'reflection_id': row[0],
                'timestamp': row[1],
                'chunk_id': row[2],
                'tier': row[3],
                'insight': row[4],
                'confidence': row[5],
                'confidence_delta': row[6],
                'reflection_type': row[7]
            })
        
        return {
            'reflections': reflections,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    except Exception as e:
        logger.error(f"Failed to list reflections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")


@router.get("/types")
def get_reflection_types():
    """
    Get available reflection types
    
    Returns:
        List of reflection types with counts
    """
    try:
        engine = get_engine()
        cursor = engine.db.cursor()
        
        cursor.execute("""
            SELECT reflection_type, COUNT(*) as count
            FROM reflections
            GROUP BY reflection_type
            ORDER BY count DESC
        """)
        
        types = []
        for row in cursor.fetchall():
            types.append({
                'type': row[0],
                'count': row[1]
            })
        
        return {
            'types': types,
            'total_types': len(types)
        }
    
    except Exception as e:
        logger.error(f"Failed to get types: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Type retrieval failed: {str(e)}")


@router.get("/insights/{chunk_id}")
def get_chunk_insights(chunk_id: str):
    """
    Get all reflections for a specific memory chunk
    
    Args:
        chunk_id: Memory chunk ID
        
    Returns:
        List of reflections for the chunk
    """
    try:
        engine = get_engine()
        cursor = engine.db.cursor()
        
        cursor.execute("""
            SELECT 
                reflection_id,
                timestamp,
                insight,
                confidence,
                confidence_delta,
                reflection_type
            FROM reflections
            WHERE chunk_id = ?
            ORDER BY timestamp DESC
        """, (chunk_id,))
        
        insights = []
        for row in cursor.fetchall():
            insights.append({
                'reflection_id': row[0],
                'timestamp': row[1],
                'insight': row[2],
                'confidence': row[3],
                'confidence_delta': row[4],
                'reflection_type': row[5]
            })
        
        return {
            'chunk_id': chunk_id,
            'insights': insights,
            'count': len(insights)
        }
    
    except Exception as e:
        logger.error(f"Failed to get chunk insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Insights retrieval failed: {str(e)}")


@router.delete("/purge")
def purge_old_reflections(days: int = Query(default=90, ge=1, le=365)):
    """
    Purge reflections older than specified days
    
    Args:
        days: Delete reflections older than this many days (1-365)
        
    Returns:
        Count of deleted reflections
    """
    try:
        engine = get_engine()
        cursor = engine.db.cursor()
        
        cursor.execute("""
            DELETE FROM reflections
            WHERE timestamp < datetime('now', ? || ' days')
        """, (f'-{days}',))
        
        deleted = cursor.rowcount
        engine.db.commit()
        
        return {
            'status': 'ok',
            'deleted': deleted,
            'days': days
        }
    
    except Exception as e:
        logger.error(f"Failed to purge reflections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Purge failed: {str(e)}")


if __name__ == '__main__':
    # Test API endpoints (without FastAPI server)
    print("=" * 60)
    print("ARK Reflection API - Test Suite")
    print("=" * 60)
    
    if not FASTAPI_AVAILABLE:
        print("FastAPI not available - skipping tests")
        exit(0)
    
    print("\n1. Testing manual reflection trigger...")
    result = sleep_now()
    print(f"Result: {result}")
    
    print("\n2. Testing statistics...")
    stats = get_stats()
    print(f"Stats: {stats}")
    
    print("\n3. Testing reflection list...")
    reflections = list_reflections(limit=5)
    print(f"Reflections: {len(reflections['reflections'])} of {reflections['total']}")
    
    print("\n4. Testing reflection types...")
    types = get_reflection_types()
    print(f"Types: {types}")
    
    print("\n" + "=" * 60)
    print("API test complete!")
    print("=" * 60)
