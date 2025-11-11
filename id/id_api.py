#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK ID API

FastAPI endpoints for agent identity and behavioral modeling:
- Query agent states and features
- Trigger manual updates from reflections
- View learning curves and adaptation
- Monitor ID system statistics
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

from id.model import IDModel
from id.features import update_from_reflections

logger = logging.getLogger(__name__)

# Create API router
if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/api/id", tags=["ID System"])
else:
    # Dummy router for import compatibility
    class DummyRouter:
        def get(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
        
        def post(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
    
    router = DummyRouter()


# Request/Response models
if FASTAPI_AVAILABLE:
    class AgentStateResponse(BaseModel):
        agent: str
        behavior_features: Dict[str, float]
        learning_curve: Dict
        update_count: int
        last_updated: int
    
    class UpdateRequest(BaseModel):
        agent: str
        lookback_days: int = 7
    
    class UpdateResponse(BaseModel):
        status: str
        result: Dict


# Global model instance
_model = None


def get_model() -> IDModel:
    """Get or create ID model instance"""
    global _model
    if _model is None:
        _model = IDModel(db_path='data/demo_memory.db')
    return _model


@router.get("/agents")
def list_agents():
    """
    List all agents in ID system
    
    Returns:
        List of agent names with update counts
    """
    try:
        model = get_model()
        agents = model.get_all_agents()
        
        # Get details for each agent
        agent_list = []
        for agent in agents:
            state = model.get_state(agent)
            if state:
                agent_list.append({
                    'agent': agent,
                    'update_count': state['update_count'],
                    'last_updated': state['last_updated'],
                    'learning_phase': state.get('learning_curve', {}).get('learning_phase', 'unknown')
                })
        
        return {
            'agents': agent_list,
            'total': len(agent_list)
        }
    
    except Exception as e:
        logger.error(f"Failed to list agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")


@router.get("/state/{agent}", response_model=AgentStateResponse if FASTAPI_AVAILABLE else None)
def get_agent_state(agent: str):
    """
    Get current state for agent
    
    Args:
        agent: Agent name
        
    Returns:
        AgentStateResponse with full state
    """
    try:
        model = get_model()
        state = model.get_state(agent)
        
        if not state:
            raise HTTPException(status_code=404, detail=f"Agent {agent} not found")
        
        return {
            'agent': state['agent'],
            'behavior_features': state.get('behavior_features', {}),
            'learning_curve': state.get('learning_curve', {}),
            'update_count': state['update_count'],
            'last_updated': state['last_updated']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"State retrieval failed: {str(e)}")


@router.post("/update", response_model=UpdateResponse if FASTAPI_AVAILABLE else None)
def trigger_update(request: UpdateRequest if FASTAPI_AVAILABLE else Dict):
    """
    Trigger manual update from reflections
    
    Args:
        request: UpdateRequest with agent and lookback_days
        
    Returns:
        UpdateResponse with results
    """
    try:
        if not FASTAPI_AVAILABLE:
            agent = request.get('agent')
            lookback_days = request.get('lookback_days', 7)
        else:
            agent = request.agent
            lookback_days = request.lookback_days
        
        result = update_from_reflections(
            agent=agent,
            lookback_days=lookback_days
        )
        
        return {
            'status': 'ok',
            'result': result
        }
    
    except Exception as e:
        logger.error(f"Update failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.get("/history/{agent}")
def get_update_history(
    agent: str,
    limit: int = Query(default=10, ge=1, le=100)
):
    """
    Get update history for agent
    
    Args:
        agent: Agent name
        limit: Max number of updates (1-100)
        
    Returns:
        List of update records
    """
    try:
        model = get_model()
        history = model.get_update_history(agent, limit=limit)
        
        return {
            'agent': agent,
            'updates': history,
            'count': len(history)
        }
    
    except Exception as e:
        logger.error(f"Failed to get history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.get("/learning-curve/{agent}")
def get_learning_curve(agent: str):
    """
    Get learning curve for agent
    
    Args:
        agent: Agent name
        
    Returns:
        Learning curve statistics
    """
    try:
        model = get_model()
        curve = model.get_learning_curve(agent)
        
        if not curve:
            raise HTTPException(status_code=404, detail=f"Agent {agent} not found")
        
        return {
            'agent': agent,
            'learning_curve': curve
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get learning curve: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Learning curve retrieval failed: {str(e)}")


@router.get("/stats")
def get_stats():
    """
    Get ID system statistics
    
    Returns:
        System-wide statistics
    """
    try:
        model = get_model()
        stats = model.get_stats()
        
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.get("/features/{agent}")
def get_features(agent: str):
    """
    Get behavioral features for agent
    
    Args:
        agent: Agent name
        
    Returns:
        Dictionary of feature name -> value
    """
    try:
        model = get_model()
        state = model.get_state(agent)
        
        if not state:
            raise HTTPException(status_code=404, detail=f"Agent {agent} not found")
        
        features = state.get('behavior_features', {})
        
        # Categorize features
        categorized = {
            'performance': {},
            'behavioral': {},
            'learning': {},
            'ethical': {},
            'communication': {}
        }
        
        for name, value in features.items():
            if any(x in name for x in ['confidence', 'duration', 'completion']):
                categorized['performance'][name] = value
            elif any(x in name for x in ['risk', 'caution', 'thoroughness', 'decisiveness']):
                categorized['behavioral'][name] = value
            elif any(x in name for x in ['pattern', 'error', 'adaptation', 'reflection']):
                categorized['learning'][name] = value
            elif any(x in name for x in ['hrm', 'trust', 'security']):
                categorized['ethical'][name] = value
            elif any(x in name for x in ['clarity', 'detail', 'structured']):
                categorized['communication'][name] = value
            else:
                categorized['performance'][name] = value  # Default category
        
        return {
            'agent': agent,
            'features': categorized,
            'total_features': len(features)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get features: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Feature retrieval failed: {str(e)}")


if __name__ == '__main__':
    # Test API endpoints
    print("=" * 60)
    print("ARK ID API - Test Suite")
    print("=" * 60)
    
    if not FASTAPI_AVAILABLE:
        print("FastAPI not available - skipping tests")
        exit(0)
    
    print("\n1. Testing agent listing...")
    result = list_agents()
    print(f"Agents: {result}")
    
    print("\n2. Testing stats...")
    stats = get_stats()
    print(f"Stats: {stats}")
    
    print("\n" + "=" * 60)
    print("API test complete!")
    print("=" * 60)
