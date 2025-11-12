#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARK Reasoning API Server

FastAPI-based reasoning API that exposes agent reasoning chains to the
intelligent-backend.cjs (Node.js) through clean async interfaces.

Architecture:
- FastAPI endpoints for each agent's reasoning
- WebSocket support for streaming reasoning traces
- Redis pub/sub for live updates
- SQLite logging for reasoning traces
- HRM orchestration for multi-agent coordination
- ReasoningEngine base class for clean 5-stage pipeline
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import agents
from agents.kyle import KyleAgent
from agents.joey import JoeyAgent
from agents.kenny import KennyAgent
from agents.aletheia import AletheiaAgent
from agents.id import IDAgent
from agents.hrm import HRMAgent

# Import reasoning components
from reasoning.intra_agent_reasoner import ReasoningDepth
from reasoning.reasoning_engine import (
    ReasoningEngine,
    AgentReasoningEngine,
    ReasoningResult,
    ReasoningStage
)
from reasoning.memory_sync import (
    MemorySyncManager,
    init_memory_sync,
    cleanup_memory_sync,
    get_memory_sync
)

# Import dashboard WebSocket components
from dashboard_websockets import (
    websocket_federation,
    websocket_memory,
    start_dashboard_tasks,
    stop_dashboard_tasks
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agent registry
agents: Dict[str, Any] = {}

# Reasoning engines for each agent
reasoning_engines: Dict[str, ReasoningEngine] = {}

# Memory sync manager
memory_sync: Optional[MemorySyncManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agents and reasoning infrastructure on startup"""
    global memory_sync
    
    logger.info("🚀 Starting ARK Reasoning API Server...")
    
    # Create data directory for database
    Path("data").mkdir(exist_ok=True)
    
    # Initialize memory sync (SQLite + Redis)
    try:
        memory_sync = await init_memory_sync()
        logger.info("✅ Memory synchronization initialized (SQLite + Redis)")
    except Exception as e:
        logger.warning(f"⚠️  Memory sync initialization failed: {e}")
        memory_sync = None
    
    # Initialize all agents
    try:
        agents['kyle'] = KyleAgent()
        agents['joey'] = JoeyAgent()
        agents['kenny'] = KennyAgent()
        agents['aletheia'] = AletheiaAgent()
        agents['id'] = IDAgent()
        agents['hrm'] = HRMAgent()
        
        logger.info("✅ All agents initialized successfully")
        
        # Initialize reasoning engines for each agent
        for agent_name, agent in agents.items():
            if agent_name != 'hrm' and hasattr(agent, 'intra_reasoner'):
                reasoning_engines[agent_name] = AgentReasoningEngine(
                    agent_name=agent_name,
                    intra_reasoner=agent.intra_reasoner,
                    agent_instance=agent,
                    default_depth=ReasoningDepth.DEEP
                )
                logger.info(f"✅ ReasoningEngine initialized for {agent_name}")
        
        # Register agents with HRM for orchestration
        hrm = agents['hrm']
        if hasattr(hrm, 'register_agent_for_reasoning'):
            for name, agent in agents.items():
                if name != 'hrm':
                    hrm.register_agent_for_reasoning(name, agent)
            logger.info("✅ Agents registered with HRM orchestrator")
    
    except Exception as e:
        logger.error(f"❌ Failed to initialize agents: {e}")
        raise
    
    # Start dashboard broadcast tasks
    try:
        await start_dashboard_tasks()
        logger.info("✅ Dashboard WebSocket tasks started")
    except Exception as e:
        logger.warning(f"⚠️  Dashboard tasks initialization failed: {e}")
    
    logger.info("🎉 ARK Reasoning API Server ready!")
    
    yield
    
    logger.info("🛑 Shutting down ARK Reasoning API Server...")
    
    # Stop dashboard tasks
    await stop_dashboard_tasks()
    
    # Cleanup memory sync
    if memory_sync:
        await cleanup_memory_sync()


app = FastAPI(
    title="ARK Reasoning API",
    description="Hierarchical reasoning API for ARK autonomous agents",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for Node.js backend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ReasoningRequest(BaseModel):
    query: str = Field(..., description="The input query to reason about")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context information")
    depth: Optional[str] = Field("DEEP", description="Reasoning depth: SHALLOW, MODERATE, DEEP, EXHAUSTIVE")
    stream: Optional[bool] = Field(False, description="Stream stage-by-stage results")


class StageResponse(BaseModel):
    stage: str
    confidence: float
    duration_ms: float
    traces: List[str]
    metadata: Dict[str, Any]


class ReasoningResponse(BaseModel):
    agent: str
    query: str
    final_output: Any
    overall_confidence: float
    stages: List[StageResponse]
    total_duration_ms: float
    timestamp: str
    session_id: Optional[str] = None


class OrchestrationRequest(BaseModel):
    query: str
    agents: List[str]
    mode: Optional[str] = "parallel"  # parallel, sequential, adaptive


class OrchestrationResponse(BaseModel):
    orchestrator: str
    results: Dict[str, Any]
    aggregated_decision: Any
    reasoning_traces: List[Dict[str, Any]]
    timestamp: str
    total_duration_ms: float


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ark-reasoning-api",
        "agents": list(agents.keys()),
        "timestamp": datetime.now().isoformat()
    }


# Agent status
@app.get("/agents")
async def list_agents():
    """List all available agents"""
    agent_info = {}
    for name, agent in agents.items():
        info = {
            "name": agent.name,
            "role": agent.role,
            "status": "active"
        }
        
        # Add reasoning stats if available
        if hasattr(agent, 'get_reasoning_statistics'):
            info['reasoning_stats'] = agent.get_reasoning_statistics()
        
        agent_info[name] = info
    
    return {
        "agents": agent_info,
        "count": len(agent_info)
    }


# Kyle reasoning endpoint
@app.post("/agent/kyle/reason", response_model=ReasoningResponse)
async def kyle_reason(request: ReasoningRequest):
    """Kyle market signal analysis with hierarchical reasoning"""
    try:
        engine = reasoning_engines.get('kyle')
        if not engine:
            raise HTTPException(status_code=503, detail="Kyle reasoning engine not available")
        
        # Parse depth
        depth = ReasoningDepth[request.depth.upper()] if request.depth else ReasoningDepth.DEEP
        
        # Publish reasoning start
        if memory_sync:
            await memory_sync.publish_reasoning_start(
                'kyle',
                request.query,
                {'depth': depth.name}
            )
        
        # Execute reasoning pipeline
        result: ReasoningResult = await engine.reason(
            query=request.query,
            context=request.context,
            depth=depth
        )
        
        # Log to database
        session_id = None
        if memory_sync:
            session_id = await memory_sync.log_reasoning_session(result)
        
        # Convert to response format
        return ReasoningResponse(
            agent="kyle",
            query=result.query,
            final_output=result.final_output,
            overall_confidence=result.overall_confidence,
            stages=[
                StageResponse(
                    stage=s.stage.value,
                    confidence=s.confidence,
                    duration_ms=s.duration_ms,
                    traces=s.traces,
                    metadata=s.metadata
                )
                for s in result.stages
            ],
            total_duration_ms=result.total_duration_ms,
            timestamp=result.timestamp,
            session_id=session_id
        )
    
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid reasoning depth: {request.depth}")
    except Exception as e:
        logger.error(f"Kyle reasoning failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Generic agent reasoning endpoint (works for all agents)
@app.post("/agent/{agent_name}/reason", response_model=ReasoningResponse)
async def agent_reason(agent_name: str, request: ReasoningRequest):
    """Generic reasoning endpoint for any agent"""
    try:
        # Get reasoning engine
        engine = reasoning_engines.get(agent_name)
        if not engine:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_name}' not found or reasoning not available"
            )
        
        # Parse depth
        depth = ReasoningDepth[request.depth.upper()] if request.depth else ReasoningDepth.DEEP
        
        # Publish reasoning start
        if memory_sync:
            await memory_sync.publish_reasoning_start(
                agent_name,
                request.query,
                {'depth': depth.name}
            )
        
        # Execute reasoning pipeline
        result: ReasoningResult = await engine.reason(
            query=request.query,
            context=request.context,
            depth=depth
        )
        
        # Publish stage completions
        if memory_sync:
            for stage in result.stages:
                await memory_sync.publish_stage_complete(agent_name, stage)
        
        # Log to database
        session_id = None
        if memory_sync:
            session_id = await memory_sync.log_reasoning_session(result)
        
        # Convert to response format
        return ReasoningResponse(
            agent=agent_name,
            query=result.query,
            final_output=result.final_output,
            overall_confidence=result.overall_confidence,
            stages=[
                StageResponse(
                    stage=s.stage.value,
                    confidence=s.confidence,
                    duration_ms=s.duration_ms,
                    traces=s.traces,
                    metadata=s.metadata
                )
                for s in result.stages
            ],
            total_duration_ms=result.total_duration_ms,
            timestamp=result.timestamp,
            session_id=session_id
        )
    
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid reasoning depth: {request.depth}")
    except Exception as e:
        logger.error(f"{agent_name} reasoning failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Memory Query Endpoints

@app.get("/reasoning/session/{session_id}")
async def get_reasoning_session(session_id: str):
    """Retrieve a specific reasoning session by ID"""
    if not memory_sync:
        raise HTTPException(status_code=503, detail="Memory sync not available")
    
    session = memory_sync.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@app.get("/reasoning/sessions")
async def query_reasoning_sessions(
    agent_name: Optional[str] = None,
    min_confidence: Optional[float] = None,
    limit: int = 100
):
    """Query reasoning sessions with filters"""
    if not memory_sync:
        raise HTTPException(status_code=503, detail="Memory sync not available")
    
    sessions = memory_sync.query_sessions(
        agent_name=agent_name,
        min_confidence=min_confidence,
        limit=limit
    )
    
    return {
        "sessions": sessions,
        "count": len(sessions),
        "filters": {
            "agent_name": agent_name,
            "min_confidence": min_confidence,
            "limit": limit
        }
    }


# HRM orchestration endpoint
@app.post("/orchestrate", response_model=OrchestrationResponse)
async def orchestrate_reasoning(request: OrchestrationRequest):
    """
    HRM-orchestrated multi-agent reasoning
    
    This is the main entry point for complex queries requiring
    coordination between multiple agents.
    """
    start_time = time.time()
    
    try:
        hrm = agents['hrm']
        
        logger.info(f"🎭 HRM orchestrating: {request.agents} in {request.mode} mode")
        
        results = {}
        reasoning_traces = []
        
        if request.mode == "parallel":
            # Execute all agents in parallel
            tasks = []
            for agent_name in request.agents:
                if agent_name in agents and agent_name != 'hrm':
                    agent = agents[agent_name]
                    task = agent.process_message(request.query)
                    tasks.append((agent_name, task))
            
            # Await all tasks
            for agent_name, task in tasks:
                try:
                    result = await task
                    results[agent_name] = result
                    reasoning_traces.append({
                        "agent": agent_name,
                        "result": result,
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Agent {agent_name} failed: {e}")
                    results[agent_name] = {"error": str(e)}
        
        elif request.mode == "sequential":
            # Execute agents sequentially
            for agent_name in request.agents:
                if agent_name in agents and agent_name != 'hrm':
                    agent = agents[agent_name]
                    try:
                        result = await agent.process_message(request.query)
                        results[agent_name] = result
                        reasoning_traces.append({
                            "agent": agent_name,
                            "result": result,
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.error(f"Agent {agent_name} failed: {e}")
                        results[agent_name] = {"error": str(e)}
        
        # HRM aggregates and validates
        aggregated_decision = {
            "query": request.query,
            "agents_consulted": request.agents,
            "mode": request.mode,
            "results_summary": {
                name: "success" if "error" not in result else "failed"
                for name, result in results.items()
            },
            "hrm_verdict": "approved"  # HRM would validate this
        }
        
        duration_ms = (time.time() - start_time) * 1000
        
        return OrchestrationResponse(
            orchestrator="hrm",
            results=results,
            aggregated_decision=aggregated_decision,
            reasoning_traces=reasoning_traces,
            timestamp=datetime.now().isoformat(),
            total_duration_ms=duration_ms
        )
    
    except Exception as e:
        logger.error(f"Orchestration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for streaming reasoning
@app.websocket("/ws/reasoning/{agent_name}")
async def websocket_reasoning(websocket: WebSocket, agent_name: str):
    """
    WebSocket endpoint for streaming reasoning traces in real-time
    """
    await websocket.accept()
    
    try:
        logger.info(f"🔌 WebSocket connected for agent: {agent_name}")
        
        while True:
            # Receive query from client
            data = await websocket.receive_text()
            query = json.loads(data)
            
            # Send acknowledgment
            await websocket.send_json({
                "type": "ack",
                "agent": agent_name,
                "query": query.get("input"),
                "timestamp": datetime.now().isoformat()
            })
            
            # Process reasoning (this is simplified - in production would stream traces)
            if agent_name in agents:
                agent = agents[agent_name]
                
                # Send processing status
                await websocket.send_json({
                    "type": "processing",
                    "agent": agent_name,
                    "stage": "reasoning",
                    "timestamp": datetime.now().isoformat()
                })
                
                # Execute reasoning
                result = await agent.process_message(query.get("input", ""))
                
                # Send result
                await websocket.send_json({
                    "type": "result",
                    "agent": agent_name,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Agent {agent_name} not found"
                })
    
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for agent: {agent_name}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


# Dashboard WebSocket endpoints
@app.websocket("/ws/federation")
async def federation_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for Federation Mesh dashboard
    Real-time P2P network topology and sync traffic
    """
    await websocket_federation(websocket)


@app.websocket("/ws/memory")
async def memory_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for Memory Engine dashboard
    Real-time memory consolidation metrics and events
    """
    await websocket_memory(websocket)


# Statistics endpoint
@app.get("/statistics")
async def get_statistics():
    """Get reasoning statistics for all agents"""
    stats = {}
    
    for name, agent in agents.items():
        agent_stats = {}
        
        # Get runtime statistics from agent
        if hasattr(agent, 'get_reasoning_statistics'):
            agent_stats['runtime'] = agent.get_reasoning_statistics()
        elif hasattr(agent, 'get_hierarchical_statistics'):
            agent_stats['runtime'] = agent.get_hierarchical_statistics()
        
        # Get historical statistics from memory database
        if memory_sync and name != 'hrm':
            try:
                agent_stats['historical'] = memory_sync.get_agent_statistics(name)
            except Exception as e:
                logger.warning(f"Failed to get historical stats for {name}: {e}")
        
        stats[name] = agent_stats
    
    return {
        "timestamp": datetime.now().isoformat(),
        "agents": stats
    }


@app.get("/agent/{agent_name}/statistics")
async def get_agent_statistics(agent_name: str):
    """Get detailed statistics for a specific agent"""
    if agent_name not in agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    agent = agents[agent_name]
    stats = {
        "agent": agent_name,
        "runtime": None,
        "historical": None
    }
    
    # Runtime stats
    if hasattr(agent, 'get_reasoning_statistics'):
        stats['runtime'] = agent.get_reasoning_statistics()
    
    # Historical stats from database
    if memory_sync:
        try:
            stats['historical'] = memory_sync.get_agent_statistics(agent_name)
        except Exception as e:
            logger.warning(f"Failed to get historical stats for {agent_name}: {e}")
    
    return stats


if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "reasoning_api:app",
        host="0.0.0.0",
        port=8101,
        reload=True,
        log_level="info"
    )
