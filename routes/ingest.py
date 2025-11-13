"""
Ingest Route

POST /api/v1/ingest - Submit trade setup for full pipeline processing

Workflow:
1. Validate trade setup (basic validation)
2. Generate correlation_id if not provided
3. Send to Unified Signal Router
4. Return tracking information

Author: ARK Trading Intelligence
Version: 1.0.0
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field, validator

from shared.agent_bus import agent_bus, AgentMessage
from agents.unified_signal_router import UnifiedSignalRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["ingest"])


# Request/Response Models
class TradeSetupRequest(BaseModel):
    """Trade setup submission payload"""
    
    # Required fields
    symbol: str = Field(..., description="Ticker symbol (e.g., 'AAPL', 'TSLA')")
    direction: str = Field(..., description="'long', 'short', or 'swing'")
    price: float = Field(..., gt=0, description="Current price")
    
    # Optional fundamental data
    float_: Optional[float] = Field(None, alias="float", description="Float size (millions)")
    market_cap: Optional[float] = Field(None, description="Market cap (millions)")
    volume: Optional[float] = Field(None, description="Current volume")
    avg_volume: Optional[float] = Field(None, description="Average volume")
    short_interest: Optional[float] = Field(None, description="Short interest %")
    
    # Optional technical data
    indicators: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Technical indicators")
    
    # Optional catalyst/sentiment
    catalyst: Optional[str] = Field(None, description="News catalyst or event")
    sentiment: Optional[str] = Field(None, description="'bullish', 'bearish', 'neutral'")
    
    # Optional metadata
    pattern: Optional[str] = Field(None, description="Suggested pattern name")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    
    # Optional correlation_id for tracing
    correlation_id: Optional[str] = Field(None, description="Correlation ID for distributed tracing")
    
    @validator('direction')
    def validate_direction(cls, v):
        allowed = ['long', 'short', 'swing']
        if v.lower() not in allowed:
            raise ValueError(f"direction must be one of {allowed}")
        return v.lower()
    
    @validator('sentiment')
    def validate_sentiment(cls, v):
        if v is None:
            return v
        allowed = ['bullish', 'bearish', 'neutral']
        if v.lower() not in allowed:
            raise ValueError(f"sentiment must be one of {allowed}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "TSLA",
                "direction": "long",
                "price": 250.50,
                "float": 15.5,
                "market_cap": 800000,
                "volume": 125000000,
                "avg_volume": 95000000,
                "short_interest": 22.5,
                "catalyst": "Strong earnings beat + EV delivery numbers exceed expectations",
                "sentiment": "bullish",
                "indicators": {
                    "rsi": 68.5,
                    "macd": 2.3,
                    "volume_ratio": 1.32
                }
            }
        }


class IngestResponse(BaseModel):
    """Response after trade setup ingestion"""
    
    status: str = Field(..., description="'accepted', 'rejected', 'error'")
    setup_id: str = Field(..., description="UUID of the trade setup")
    correlation_id: str = Field(..., description="Correlation ID for tracking")
    message: str = Field(..., description="Human-readable status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Optional tracking info
    processing_stage: Optional[str] = Field(None, description="Current pipeline stage")
    estimated_completion_seconds: Optional[int] = Field(None, description="Estimated processing time")


# Background processing
async def process_trade_setup_background(trade_setup: Dict, correlation_id: str):
    """
    Process trade setup through the pipeline in the background.
    
    This allows the API to return immediately while processing continues.
    """
    try:
        # Get singleton router instance
        router_agent = UnifiedSignalRouter()
        
        # Process through full pipeline
        await router_agent.process_trade_setup(trade_setup, correlation_id)
        
        logger.info(f"✅ Successfully processed trade setup {trade_setup['setup_id']} (correlation: {correlation_id})")
        
    except Exception as e:
        logger.error(f"❌ Error processing trade setup {trade_setup.get('setup_id', 'unknown')}: {str(e)}")
        logger.exception(e)


# Endpoints
@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_trade_setup(
    request: TradeSetupRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit a trade setup for full pipeline processing.
    
    **Workflow**:
    1. Validate trade setup (basic validation)
    2. Generate setup_id and correlation_id
    3. Queue for background processing through Unified Signal Router
    4. Return tracking information
    
    **Processing Pipeline**:
    - Pattern matching (Pattern Engine)
    - Quality scoring (Trade Scorer)
    - Risk validation (HRM)
    - Execution planning (Trade Plan Builder)
    - Send to Kenny (execution agent)
    - Telegram notification
    
    **Response**: Immediate acceptance with tracking info
    
    **Note**: Processing happens asynchronously. Use correlation_id to track progress.
    """
    try:
        # Generate IDs
        setup_id = str(uuid.uuid4())
        correlation_id = request.correlation_id or str(uuid.uuid4())
        
        # Build trade setup dictionary
        trade_setup = {
            "setup_id": setup_id,
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": request.symbol.upper(),
            "direction": request.direction,
            "price": request.price,
            "float_": request.float_,
            "market_cap": request.market_cap,
            "volume": request.volume,
            "avg_volume": request.avg_volume,
            "short_interest": request.short_interest,
            "indicators": request.indicators or {},
            "catalyst": request.catalyst,
            "sentiment": request.sentiment,
            "pattern": request.pattern,
            "metadata": request.metadata or {},
            "agents_processed": [],
            "status": "pending",
            "validation_errors": []
        }
        
        # Queue for background processing
        background_tasks.add_task(process_trade_setup_background, trade_setup, correlation_id)
        
        logger.info(f"📥 Ingested trade setup: {request.symbol} {request.direction} @ ${request.price} (correlation: {correlation_id})")
        
        return IngestResponse(
            status="accepted",
            setup_id=setup_id,
            correlation_id=correlation_id,
            message=f"Trade setup for {request.symbol} accepted for processing",
            processing_stage="queued",
            estimated_completion_seconds=5
        )
        
    except Exception as e:
        logger.error(f"❌ Error ingesting trade setup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest trade setup: {str(e)}"
        )


@router.get("/ingest/status/{correlation_id}")
async def get_processing_status(correlation_id: str):
    """
    Check processing status of a trade setup using its correlation_id.
    
    Returns:
    - Processing stage
    - Agent history
    - Any validation errors
    - Final status if completed
    """
    try:
        # Query agent bus for conversation history
        messages = agent_bus.get_conversation_history(correlation_id)
        
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No trade setup found with correlation_id: {correlation_id}"
            )
        
        # Extract processing stages from messages
        stages = []
        for msg in messages:
            stages.append({
                "agent": msg.from_agent,
                "timestamp": msg.timestamp.isoformat(),
                "message_type": msg.message_type.value
            })
        
        # Determine current status
        last_message = messages[-1]
        final_status = last_message.payload.get('status', 'processing')
        
        return {
            "correlation_id": correlation_id,
            "status": final_status,
            "stages": stages,
            "total_messages": len(messages),
            "last_updated": last_message.timestamp.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching status for {correlation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch processing status: {str(e)}"
        )
