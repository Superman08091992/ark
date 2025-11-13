"""
Analyze Route

POST /api/v1/analyze - Analyze pattern without full execution

Workflow:
1. Validate trade setup
2. Run pattern matching only
3. Return pattern analysis with confidence scores
4. NO execution, NO HRM validation

Use case: Quick pattern analysis for research/backtesting

Author: ARK Trading Intelligence
Version: 1.0.0
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator

from ark.intel.engines.pattern_engine import get_pattern_engine, MatchResult
from ark.intel.engines.trade_scorer import get_trade_scorer, ScoreBreakdown

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["analyze"])


# Request Models
class AnalyzeRequest(BaseModel):
    """Pattern analysis request payload"""
    
    # Required fields
    symbol: str = Field(..., description="Ticker symbol")
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
    
    # Optional catalyst
    catalyst: Optional[str] = Field(None, description="News catalyst")
    sentiment: Optional[str] = Field(None, description="'bullish', 'bearish', 'neutral'")
    
    # Analysis options
    min_confidence: Optional[float] = Field(0.65, ge=0.0, le=1.0, description="Minimum pattern confidence threshold")
    include_scoring: Optional[bool] = Field(True, description="Include quality scoring")
    
    @validator('direction')
    def validate_direction(cls, v):
        allowed = ['long', 'short', 'swing']
        if v.lower() not in allowed:
            raise ValueError(f"direction must be one of {allowed}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "NVDA",
                "direction": "long",
                "price": 485.50,
                "float": 18.2,
                "short_interest": 3.5,
                "volume": 45000000,
                "avg_volume": 35000000,
                "catalyst": "New AI chip announcement driving momentum",
                "indicators": {
                    "rsi": 72.3,
                    "macd": 3.5
                },
                "min_confidence": 0.70
            }
        }


class PatternMatch(BaseModel):
    """Single pattern match result"""
    
    pattern_id: str
    pattern_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    base_confidence: float
    preferred_boost: float
    
    rules_matched: int
    rules_required: int
    rules_preferred: int
    
    profit_targets: List[Dict[str, Any]]
    stop_loss_percentage: float
    
    reasoning: str


class QualityScores(BaseModel):
    """Multi-factor quality scores"""
    
    technical: float = Field(..., ge=0.0, le=1.0)
    fundamental: float = Field(..., ge=0.0, le=1.0)
    catalyst: float = Field(..., ge=0.0, le=1.0)
    sentiment: float = Field(..., ge=0.0, le=1.0)
    
    weighted_total: float = Field(..., ge=0.0, le=1.0)
    grade: str  # 'A+', 'A', 'B+', etc.
    
    breakdown: Dict[str, Any]


class AnalyzeResponse(BaseModel):
    """Pattern analysis response"""
    
    symbol: str
    direction: str
    price: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Pattern matches
    patterns: List[PatternMatch]
    best_pattern: Optional[PatternMatch]
    total_patterns_tested: int
    
    # Quality scores (if requested)
    scores: Optional[QualityScores] = None
    
    # Summary
    recommendation: str  # 'strong_buy', 'buy', 'hold', 'sell', 'strong_sell', 'no_pattern'


# Endpoints
@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_pattern(request: AnalyzeRequest):
    """
    Analyze trading pattern without executing.
    
    **Workflow**:
    1. Pattern matching against all 10 patterns
    2. Return confidence scores and reasoning
    3. Optional: Multi-factor quality scoring
    
    **No execution**: This is analysis only, no trades sent to Kenny
    **No HRM validation**: For research/backtesting purposes
    
    **Use Cases**:
    - Pattern research
    - Backtesting strategies
    - Pre-validation before ingestion
    - Educational/learning purposes
    """
    try:
        # Build trade setup for analysis
        trade_setup = {
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
            "sentiment": request.sentiment
        }
        
        # Get pattern engine instance
        pattern_engine = get_pattern_engine()
        
        # Match all patterns
        pattern_matches = pattern_engine.match_all_patterns(
            trade_setup=trade_setup,
            direction_filter=request.direction,
            min_confidence=request.min_confidence
        )
        
        logger.info(f"🔍 Analyzed {request.symbol}: found {len(pattern_matches)} patterns above {request.min_confidence} confidence")
        
        # Convert to response format
        patterns_response = []
        for match in pattern_matches:
            patterns_response.append(PatternMatch(
                pattern_id=match.pattern_id,
                pattern_name=match.pattern_name,
                confidence=match.confidence,
                base_confidence=match.base_confidence,
                preferred_boost=match.preferred_boost,
                rules_matched=match.rules_matched,
                rules_required=match.rules_required,
                rules_preferred=match.rules_preferred,
                profit_targets=match.profit_targets,
                stop_loss_percentage=match.stop_loss_percentage,
                reasoning=match.reasoning
            ))
        
        # Get best pattern
        best_pattern = patterns_response[0] if patterns_response else None
        
        # Optional: Quality scoring
        scores_response = None
        if request.include_scoring and patterns_response:
            trade_scorer = get_trade_scorer()
            
            # Enrich with best pattern for scoring context
            enriched_setup = pattern_engine.enrich_trade_setup(trade_setup, pattern_matches[0])
            
            # Calculate scores
            score_breakdown = trade_scorer.score_trade_setup(enriched_setup)
            
            scores_response = QualityScores(
                technical=score_breakdown.technical,
                fundamental=score_breakdown.fundamental,
                catalyst=score_breakdown.catalyst,
                sentiment=score_breakdown.sentiment,
                weighted_total=score_breakdown.weighted_total,
                grade=score_breakdown.grade,
                breakdown={
                    "technical_details": score_breakdown.technical_details,
                    "fundamental_details": score_breakdown.fundamental_details,
                    "catalyst_details": score_breakdown.catalyst_details,
                    "sentiment_details": score_breakdown.sentiment_details
                }
            )
        
        # Generate recommendation
        recommendation = _generate_recommendation(
            best_pattern=best_pattern,
            scores=scores_response,
            direction=request.direction
        )
        
        return AnalyzeResponse(
            symbol=request.symbol.upper(),
            direction=request.direction,
            price=request.price,
            patterns=patterns_response,
            best_pattern=best_pattern,
            total_patterns_tested=len(pattern_engine.patterns),
            scores=scores_response,
            recommendation=recommendation
        )
        
    except Exception as e:
        logger.error(f"❌ Error analyzing pattern for {request.symbol}: {str(e)}")
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze pattern: {str(e)}"
        )


def _generate_recommendation(
    best_pattern: Optional[PatternMatch],
    scores: Optional[QualityScores],
    direction: str
) -> str:
    """
    Generate trading recommendation based on pattern and scores.
    
    Logic:
    - No pattern match → 'no_pattern'
    - Pattern + high scores (>0.80) → 'strong_buy'/'strong_sell'
    - Pattern + good scores (>0.65) → 'buy'/'sell'
    - Pattern + low scores → 'hold'
    """
    if not best_pattern:
        return "no_pattern"
    
    confidence = best_pattern.confidence
    quality = scores.weighted_total if scores else confidence
    
    # Strong signal
    if confidence >= 0.80 and quality >= 0.80:
        return "strong_buy" if direction == "long" else "strong_sell"
    
    # Good signal
    if confidence >= 0.70 and quality >= 0.65:
        return "buy" if direction == "long" else "sell"
    
    # Weak signal
    if confidence >= 0.65:
        return "hold"
    
    return "no_pattern"


@router.get("/analyze/patterns")
async def list_available_patterns():
    """
    List all available trading patterns with descriptions.
    
    Returns:
    - Pattern IDs and names
    - Direction support (long/short/swing)
    - Confidence weighting
    - Brief description
    """
    try:
        pattern_engine = get_pattern_engine()
        
        patterns_info = []
        for pattern_id, pattern_data in pattern_engine.patterns.items():
            patterns_info.append({
                "pattern_id": pattern_id,
                "name": pattern_data.get("name", pattern_id.replace("_", " ").title()),
                "confidence_weight": pattern_data.get("confidence_weight", 1.0),
                "directions": pattern_data.get("directions", ["long", "short"]),
                "description": pattern_data.get("description", ""),
                "stop_loss_pct": pattern_data.get("stop_loss_percentage", 0.08)
            })
        
        return {
            "total_patterns": len(patterns_info),
            "patterns": patterns_info
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing patterns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list patterns: {str(e)}"
        )
