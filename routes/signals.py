"""
Signals Route

GET /api/v1/signals - Retrieve generated trading signals

Workflow:
1. Query AgentBus for completed signals
2. Filter by status, symbol, direction, date range
3. Return paginated results

Author: ARK Trading Intelligence
Version: 1.0.0
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from shared.agent_bus import agent_bus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["signals"])


# Response Models
class SignalSummary(BaseModel):
    """Summary of a generated trading signal"""
    
    setup_id: str
    correlation_id: str
    timestamp: datetime
    
    symbol: str
    direction: str
    price: float
    
    pattern: Optional[str] = None
    confidence: Optional[float] = None
    
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    position_size: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    
    status: str  # 'approved', 'sent', 'rejected'
    
    agents_processed: List[str]


class SignalsResponse(BaseModel):
    """Paginated signals response"""
    
    signals: List[SignalSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# Endpoints
@router.get("/signals", response_model=SignalsResponse)
async def get_signals(
    status_filter: Optional[str] = Query(None, description="Filter by status: 'approved', 'sent', 'rejected'"),
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., 'TSLA')"),
    direction: Optional[str] = Query(None, description="Filter by direction: 'long', 'short', 'swing'"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format: 2025-11-13T00:00:00)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Results per page")
):
    """
    Retrieve generated trading signals with filtering and pagination.
    
    **Filters**:
    - `status`: 'approved', 'sent', 'rejected'
    - `symbol`: Ticker symbol (e.g., 'TSLA')
    - `direction`: 'long', 'short', 'swing'
    - `min_confidence`: Minimum confidence score (0.0-1.0)
    - `start_date` / `end_date`: Date range (ISO format)
    
    **Pagination**:
    - `page`: Page number (default: 1)
    - `page_size`: Results per page (default: 50, max: 200)
    
    **Returns**: List of signal summaries with metadata
    """
    try:
        # Parse date filters
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Query all messages from agent bus
        # Note: In production, this would query a persistent database
        # For now, we'll use agent_bus message history (last 1000 messages)
        all_messages = agent_bus._message_history
        
        # Filter for signals (messages with trade_setup in payload)
        signal_messages = []
        for msg in all_messages:
            payload = msg.payload
            
            # Check if message contains a trade_setup
            if 'trade_setup' not in payload:
                continue
            
            trade_setup = payload['trade_setup']
            
            # Apply filters
            if status_filter and trade_setup.get('status') != status_filter:
                continue
            
            if symbol and trade_setup.get('symbol', '').upper() != symbol.upper():
                continue
            
            if direction and trade_setup.get('direction') != direction:
                continue
            
            if min_confidence and trade_setup.get('confidence', 0) < min_confidence:
                continue
            
            # Date range filter
            msg_timestamp = msg.timestamp
            if start_dt and msg_timestamp < start_dt:
                continue
            if end_dt and msg_timestamp > end_dt:
                continue
            
            signal_messages.append((msg, trade_setup))
        
        # Sort by timestamp (newest first)
        signal_messages.sort(key=lambda x: x[0].timestamp, reverse=True)
        
        # Pagination
        total = len(signal_messages)
        total_pages = (total + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_messages = signal_messages[start_idx:end_idx]
        
        # Build response
        signals = []
        for msg, trade_setup in page_messages:
            exec_plan = trade_setup.get('execution_plan', {})
            
            signals.append(SignalSummary(
                setup_id=trade_setup.get('setup_id', 'unknown'),
                correlation_id=msg.correlation_id,
                timestamp=msg.timestamp,
                symbol=trade_setup.get('symbol', 'UNKNOWN'),
                direction=trade_setup.get('direction', 'unknown'),
                price=trade_setup.get('price', 0.0),
                pattern=trade_setup.get('pattern'),
                confidence=trade_setup.get('confidence'),
                entry=exec_plan.get('entry_price'),
                stop_loss=exec_plan.get('stop_loss'),
                target=exec_plan.get('target_1'),  # First target
                position_size=exec_plan.get('position_size_percent'),
                risk_reward_ratio=exec_plan.get('risk_reward_ratio'),
                status=trade_setup.get('status', 'unknown'),
                agents_processed=trade_setup.get('agents_processed', [])
            ))
        
        logger.info(f"📊 Retrieved {len(signals)} signals (page {page}/{total_pages}, total: {total})")
        
        return SignalsResponse(
            signals=signals,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Error retrieving signals: {str(e)}")
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve signals: {str(e)}"
        )


@router.get("/signals/{correlation_id}")
async def get_signal_details(correlation_id: str):
    """
    Get detailed information for a specific signal by correlation_id.
    
    **Returns**:
    - Complete trade setup data
    - Full agent processing history
    - Pattern match details
    - Quality scores
    - Execution plan
    - Any validation errors
    """
    try:
        # Query agent bus for full conversation
        messages = agent_bus.get_conversation_history(correlation_id)
        
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No signal found with correlation_id: {correlation_id}"
            )
        
        # Extract trade setup from latest message
        trade_setup = None
        for msg in reversed(messages):
            if 'trade_setup' in msg.payload:
                trade_setup = msg.payload['trade_setup']
                break
        
        if not trade_setup:
            # Try to find in any message
            for msg in messages:
                if 'symbol' in msg.payload and 'direction' in msg.payload:
                    trade_setup = msg.payload
                    break
        
        # Build agent history
        agent_history = []
        for msg in messages:
            agent_history.append({
                "timestamp": msg.timestamp.isoformat(),
                "from_agent": msg.from_agent,
                "to_agent": msg.to_agent,
                "message_type": msg.message_type.value,
                "payload_summary": _summarize_payload(msg.payload)
            })
        
        return {
            "correlation_id": correlation_id,
            "trade_setup": trade_setup or {},
            "agent_history": agent_history,
            "total_messages": len(messages),
            "first_seen": messages[0].timestamp.isoformat() if messages else None,
            "last_updated": messages[-1].timestamp.isoformat() if messages else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving signal details for {correlation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve signal details: {str(e)}"
        )


def _summarize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a concise summary of message payload for history view"""
    summary = {}
    
    # Include key fields only
    include_fields = ['status', 'pattern', 'confidence', 'approval', 'rejection_reason', 'stage']
    for field in include_fields:
        if field in payload:
            summary[field] = payload[field]
    
    # Include trade_setup summary if present
    if 'trade_setup' in payload:
        ts = payload['trade_setup']
        summary['trade_setup'] = {
            'symbol': ts.get('symbol'),
            'direction': ts.get('direction'),
            'price': ts.get('price'),
            'status': ts.get('status')
        }
    
    return summary


@router.get("/signals/stats/summary")
async def get_signals_summary():
    """
    Get statistical summary of all signals.
    
    **Returns**:
    - Total signals generated
    - Breakdown by status (approved/rejected/sent)
    - Breakdown by direction (long/short/swing)
    - Average confidence score
    - Most common patterns
    - Daily/weekly counts
    """
    try:
        all_messages = agent_bus._message_history
        
        # Extract trade setups
        trade_setups = []
        for msg in all_messages:
            if 'trade_setup' in msg.payload:
                ts = msg.payload['trade_setup']
                ts['timestamp'] = msg.timestamp
                trade_setups.append(ts)
        
        if not trade_setups:
            return {
                "total_signals": 0,
                "status_breakdown": {},
                "direction_breakdown": {},
                "pattern_breakdown": {},
                "average_confidence": 0.0,
                "daily_counts": {},
                "weekly_counts": {}
            }
        
        # Status breakdown
        status_counts = {}
        for ts in trade_setups:
            status = ts.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Direction breakdown
        direction_counts = {}
        for ts in trade_setups:
            direction = ts.get('direction', 'unknown')
            direction_counts[direction] = direction_counts.get(direction, 0) + 1
        
        # Pattern breakdown
        pattern_counts = {}
        for ts in trade_setups:
            pattern = ts.get('pattern')
            if pattern:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Average confidence
        confidences = [ts.get('confidence', 0) for ts in trade_setups if ts.get('confidence') is not None]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Daily counts (last 7 days)
        daily_counts = {}
        for ts in trade_setups:
            date_key = ts['timestamp'].strftime('%Y-%m-%d')
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        # Sort daily counts by date
        daily_counts = dict(sorted(daily_counts.items(), key=lambda x: x[0], reverse=True)[:7])
        
        return {
            "total_signals": len(trade_setups),
            "status_breakdown": status_counts,
            "direction_breakdown": direction_counts,
            "pattern_breakdown": pattern_counts,
            "average_confidence": round(avg_confidence, 3),
            "daily_counts": daily_counts,
            "last_signal": trade_setups[-1]['timestamp'].isoformat() if trade_setups else None
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating signals summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )
