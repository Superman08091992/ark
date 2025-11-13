"""
Multi-Factor Trade Scoring Engine

Scores trade setups across four dimensions:
1. Technical Analysis (chart patterns, indicators, price action)
2. Fundamental Analysis (financials, valuation, growth)
3. Catalyst Strength (news, events, market conditions)
4. Sentiment Analysis (social, institutional, analyst)

Author: ARK Trading Intelligence
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ScoreDimension(str, Enum):
    """Scoring dimensions for trade evaluation."""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    CATALYST = "catalyst"
    SENTIMENT = "sentiment"


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown for a trade setup."""
    technical_score: float
    fundamental_score: float
    catalyst_score: float
    sentiment_score: float
    weighted_total: float
    confidence: float
    factors: Dict[str, float]


class TradeScorer:
    """
    Multi-Factor Trade Scoring Engine
    
    Evaluates trade setups across multiple dimensions to generate
    comprehensive quality scores with confidence metrics.
    """
    
    # Default scoring weights (can be overridden per pattern)
    DEFAULT_WEIGHTS = {
        ScoreDimension.TECHNICAL: 0.35,
        ScoreDimension.FUNDAMENTAL: 0.25,
        ScoreDimension.CATALYST: 0.25,
        ScoreDimension.SENTIMENT: 0.15
    }
    
    def __init__(self):
        """Initialize Trade Scorer."""
        logger.info("Trade Scorer initialized")
    
    def score_trade_setup(self, 
                         trade_setup: Dict[str, Any],
                         weights: Optional[Dict[str, float]] = None) -> ScoreBreakdown:
        """
        Generate comprehensive score for trade setup.
        
        Args:
            trade_setup: Trade setup dictionary with market data
            weights: Optional custom weights for scoring dimensions
            
        Returns:
            ScoreBreakdown with dimensional and weighted scores
        """
        # Use custom weights or defaults
        if weights is None:
            weights = self.DEFAULT_WEIGHTS
        else:
            # Convert string keys to ScoreDimension if needed
            weights = {
                ScoreDimension(k) if isinstance(k, str) else k: v 
                for k, v in weights.items()
            }
        
        # Score each dimension
        technical = self._score_technical(trade_setup)
        fundamental = self._score_fundamental(trade_setup)
        catalyst = self._score_catalyst(trade_setup)
        sentiment = self._score_sentiment(trade_setup)
        
        # Calculate weighted total
        weighted_total = (
            technical * weights.get(ScoreDimension.TECHNICAL, 0.35) +
            fundamental * weights.get(ScoreDimension.FUNDAMENTAL, 0.25) +
            catalyst * weights.get(ScoreDimension.CATALYST, 0.25) +
            sentiment * weights.get(ScoreDimension.SENTIMENT, 0.15)
        )
        
        # Calculate confidence based on data completeness
        confidence = self._calculate_confidence(trade_setup)
        
        # Collect all factor scores
        factors = {
            **self._get_technical_factors(trade_setup),
            **self._get_fundamental_factors(trade_setup),
            **self._get_catalyst_factors(trade_setup),
            **self._get_sentiment_factors(trade_setup)
        }
        
        return ScoreBreakdown(
            technical_score=technical,
            fundamental_score=fundamental,
            catalyst_score=catalyst,
            sentiment_score=sentiment,
            weighted_total=weighted_total,
            confidence=confidence,
            factors=factors
        )
    
    def _score_technical(self, trade_setup: Dict[str, Any]) -> float:
        """
        Score technical analysis factors.
        
        Evaluates:
        - RSI (momentum)
        - MACD (trend)
        - Volume (participation)
        - Price action (pattern quality)
        - Support/Resistance (key levels)
        
        Returns:
            Technical score [0.0-1.0]
        """
        score = 0.0
        factors = []
        
        indicators = trade_setup.get('indicators', {})
        
        # RSI scoring (0.25 weight)
        rsi = indicators.get('rsi')
        if rsi is not None:
            direction = trade_setup.get('direction', 'long')
            if direction == 'long':
                # Long: prefer RSI 40-70 (not overbought)
                if 40 <= rsi <= 70:
                    factors.append(0.25)
                elif 30 <= rsi < 40 or 70 < rsi <= 80:
                    factors.append(0.15)
                else:
                    factors.append(0.05)
            else:
                # Short: prefer RSI 30-60 (not oversold)
                if 30 <= rsi <= 60:
                    factors.append(0.25)
                elif 20 <= rsi < 30 or 60 < rsi <= 70:
                    factors.append(0.15)
                else:
                    factors.append(0.05)
        
        # MACD scoring (0.20 weight)
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        if macd is not None and macd_signal is not None:
            direction = trade_setup.get('direction', 'long')
            if direction == 'long' and macd > macd_signal:
                factors.append(0.20)  # Bullish crossover
            elif direction == 'short' and macd < macd_signal:
                factors.append(0.20)  # Bearish crossover
            else:
                factors.append(0.08)
        
        # Volume analysis (0.25 weight)
        volume = trade_setup.get('volume')
        avg_volume = trade_setup.get('avg_volume')
        if volume and avg_volume:
            volume_ratio = volume / avg_volume
            if volume_ratio >= 3.0:
                factors.append(0.25)  # Excellent volume
            elif volume_ratio >= 1.5:
                factors.append(0.18)  # Good volume
            elif volume_ratio >= 1.0:
                factors.append(0.12)  # Average volume
            else:
                factors.append(0.05)  # Weak volume
        
        # Price action quality (0.15 weight)
        price_action = trade_setup.get('price_action', '')
        if any(keyword in price_action.lower() for keyword in ['breakout', 'consolidation', 'reversal', 'support']):
            factors.append(0.15)
        elif price_action:
            factors.append(0.08)
        
        # Support/Resistance (0.15 weight)
        support_level = trade_setup.get('support_level')
        resistance_level = trade_setup.get('resistance_level')
        if support_level or resistance_level:
            factors.append(0.15)
        
        return min(sum(factors), 1.0)
    
    def _score_fundamental(self, trade_setup: Dict[str, Any]) -> float:
        """
        Score fundamental factors.
        
        Evaluates:
        - Market cap (size/liquidity)
        - Float (supply)
        - Short interest (squeeze potential)
        - Financial metrics (if available)
        
        Returns:
            Fundamental score [0.0-1.0]
        """
        score = 0.0
        factors = []
        
        # Market cap scoring (0.20 weight)
        market_cap = trade_setup.get('market_cap')
        if market_cap:
            if 100 <= market_cap <= 2000:  # $100M-$2B sweet spot
                factors.append(0.20)
            elif 50 <= market_cap < 100 or 2000 < market_cap <= 10000:
                factors.append(0.12)
            else:
                factors.append(0.08)
        
        # Float analysis (0.30 weight)
        float_ = trade_setup.get('float_')
        if float_:
            if float_ < 10:  # Very low float
                factors.append(0.30)
            elif float_ < 30:  # Low float
                factors.append(0.22)
            elif float_ < 100:  # Medium float
                factors.append(0.15)
            else:  # High float
                factors.append(0.08)
        
        # Short interest (0.30 weight)
        short_interest = trade_setup.get('short_interest')
        direction = trade_setup.get('direction', 'long')
        if short_interest is not None:
            if direction == 'long':
                # Long: high SI = squeeze potential
                if short_interest > 30:
                    factors.append(0.30)
                elif short_interest > 15:
                    factors.append(0.20)
                else:
                    factors.append(0.10)
            else:
                # Short: low SI = less crowded
                if short_interest < 10:
                    factors.append(0.30)
                elif short_interest < 20:
                    factors.append(0.18)
                else:
                    factors.append(0.08)
        
        # Cost to borrow (0.20 weight) - for short squeeze potential
        cost_to_borrow = trade_setup.get('cost_to_borrow')
        if cost_to_borrow and direction == 'long':
            if cost_to_borrow > 100:
                factors.append(0.20)
            elif cost_to_borrow > 50:
                factors.append(0.12)
        
        return min(sum(factors), 1.0)
    
    def _score_catalyst(self, trade_setup: Dict[str, Any]) -> float:
        """
        Score catalyst strength.
        
        Evaluates:
        - News catalyst presence
        - Catalyst type (earnings, FDA, acquisition, etc.)
        - Timing (fresh vs stale)
        - Market reaction
        
        Returns:
            Catalyst score [0.0-1.0]
        """
        factors = []
        
        catalyst = trade_setup.get('catalyst', '')
        catalyst_strength = trade_setup.get('catalyst_strength', '')
        
        # Catalyst presence (0.40 weight)
        if catalyst and len(catalyst) > 10:
            # Strong keywords
            if any(keyword in catalyst.lower() for keyword in [
                'earnings beat', 'fda approval', 'acquisition', 'merger', 
                'breakthrough', 'partnership', 'contract win'
            ]):
                factors.append(0.40)
            # Moderate keywords
            elif any(keyword in catalyst.lower() for keyword in [
                'earnings', 'upgrade', 'news', 'announcement', 'guidance'
            ]):
                factors.append(0.25)
            else:
                factors.append(0.15)
        
        # Catalyst strength assessment (0.30 weight)
        if catalyst_strength:
            if catalyst_strength.lower() == 'strong':
                factors.append(0.30)
            elif catalyst_strength.lower() == 'moderate':
                factors.append(0.18)
            elif catalyst_strength.lower() == 'weak':
                factors.append(0.08)
        
        # Earnings beat metrics (0.30 weight)
        earnings_beat = trade_setup.get('earnings_beat')
        if earnings_beat is True:
            earnings_beat_percent = trade_setup.get('earnings_beat_percent', 0)
            if earnings_beat_percent > 20:
                factors.append(0.30)
            elif earnings_beat_percent > 10:
                factors.append(0.20)
            else:
                factors.append(0.12)
        
        return min(sum(factors), 1.0)
    
    def _score_sentiment(self, trade_setup: Dict[str, Any]) -> float:
        """
        Score sentiment factors.
        
        Evaluates:
        - Social media sentiment
        - Analyst ratings
        - Institutional activity
        - Retail interest
        
        Returns:
            Sentiment score [0.0-1.0]
        """
        factors = []
        
        sentiment = trade_setup.get('sentiment', '')
        direction = trade_setup.get('direction', 'long')
        
        # Overall sentiment (0.35 weight)
        if sentiment:
            if (direction == 'long' and sentiment.lower() == 'bullish') or \
               (direction == 'short' and sentiment.lower() == 'bearish'):
                factors.append(0.35)
            elif sentiment.lower() == 'neutral':
                factors.append(0.15)
            else:
                factors.append(0.05)
        
        # Social sentiment (0.25 weight)
        social_sentiment = trade_setup.get('social_sentiment', '')
        retail_sentiment = trade_setup.get('retail_sentiment', '')
        if social_sentiment or retail_sentiment:
            target = social_sentiment or retail_sentiment
            if (direction == 'long' and target.lower() == 'bullish') or \
               (direction == 'short' and target.lower() == 'bearish'):
                factors.append(0.25)
            else:
                factors.append(0.10)
        
        # Analyst upgrades/downgrades (0.25 weight)
        analyst_upgrades = trade_setup.get('analyst_upgrades', 0)
        analyst_downgrades = trade_setup.get('analyst_downgrades', 0)
        if direction == 'long' and analyst_upgrades > 0:
            factors.append(0.25)
        elif direction == 'short' and analyst_downgrades > 0:
            factors.append(0.25)
        
        # Insider buying/selling (0.15 weight)
        insider_buying = trade_setup.get('insider_buying')
        if insider_buying is not None:
            if (direction == 'long' and insider_buying) or \
               (direction == 'short' and not insider_buying):
                factors.append(0.15)
        
        return min(sum(factors), 1.0)
    
    def _calculate_confidence(self, trade_setup: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on data completeness.
        
        Args:
            trade_setup: Trade setup dictionary
            
        Returns:
            Confidence score [0.0-1.0]
        """
        # Critical fields (0.60 weight)
        critical_fields = ['symbol', 'price', 'volume', 'direction']
        critical_present = sum(1 for field in critical_fields if trade_setup.get(field))
        critical_score = (critical_present / len(critical_fields)) * 0.60
        
        # Important fields (0.30 weight)
        important_fields = ['float_', 'market_cap', 'catalyst', 'indicators']
        important_present = sum(1 for field in important_fields if trade_setup.get(field))
        important_score = (important_present / len(important_fields)) * 0.30
        
        # Optional fields (0.10 weight)
        optional_fields = ['sentiment', 'short_interest', 'analyst_upgrades']
        optional_present = sum(1 for field in optional_fields if trade_setup.get(field))
        optional_score = (optional_present / len(optional_fields)) * 0.10
        
        return critical_score + important_score + optional_score
    
    def _get_technical_factors(self, trade_setup: Dict[str, Any]) -> Dict[str, float]:
        """Extract technical factor scores."""
        factors = {}
        indicators = trade_setup.get('indicators', {})
        
        if 'rsi' in indicators:
            factors['rsi_quality'] = self._normalize_rsi_score(
                indicators['rsi'], 
                trade_setup.get('direction', 'long')
            )
        
        if 'volume' in trade_setup and 'avg_volume' in trade_setup:
            factors['volume_strength'] = min(
                trade_setup['volume'] / trade_setup['avg_volume'] / 3.0,
                1.0
            )
        
        return factors
    
    def _get_fundamental_factors(self, trade_setup: Dict[str, Any]) -> Dict[str, float]:
        """Extract fundamental factor scores."""
        factors = {}
        
        if 'float_' in trade_setup:
            factors['float_quality'] = max(0, 1.0 - (trade_setup['float_'] / 100.0))
        
        if 'short_interest' in trade_setup:
            factors['short_interest_score'] = min(trade_setup['short_interest'] / 50.0, 1.0)
        
        return factors
    
    def _get_catalyst_factors(self, trade_setup: Dict[str, Any]) -> Dict[str, float]:
        """Extract catalyst factor scores."""
        factors = {}
        
        if trade_setup.get('catalyst'):
            factors['catalyst_presence'] = 1.0 if len(trade_setup['catalyst']) > 10 else 0.5
        
        if trade_setup.get('earnings_beat'):
            factors['earnings_strength'] = 1.0
        
        return factors
    
    def _get_sentiment_factors(self, trade_setup: Dict[str, Any]) -> Dict[str, float]:
        """Extract sentiment factor scores."""
        factors = {}
        
        sentiment = trade_setup.get('sentiment', '')
        direction = trade_setup.get('direction', 'long')
        
        if sentiment:
            aligned = (direction == 'long' and sentiment.lower() == 'bullish') or \
                     (direction == 'short' and sentiment.lower() == 'bearish')
            factors['sentiment_alignment'] = 1.0 if aligned else 0.3
        
        return factors
    
    def _normalize_rsi_score(self, rsi: float, direction: str) -> float:
        """Normalize RSI to quality score based on direction."""
        if direction == 'long':
            if 40 <= rsi <= 70:
                return 1.0
            elif 30 <= rsi < 40 or 70 < rsi <= 80:
                return 0.6
            else:
                return 0.2
        else:  # short
            if 30 <= rsi <= 60:
                return 1.0
            elif 20 <= rsi < 30 or 60 < rsi <= 70:
                return 0.6
            else:
                return 0.2


# Module-level singleton
_scorer_instance: Optional[TradeScorer] = None


def get_trade_scorer() -> TradeScorer:
    """Get or create singleton Trade Scorer instance."""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = TradeScorer()
    return _scorer_instance


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    scorer = TradeScorer()
    
    # Example trade setup
    example = {
        "symbol": "TSLA",
        "direction": "long",
        "price": 245.50,
        "volume": 85000000,
        "avg_volume": 35000000,
        "float_": 18.5,
        "market_cap": 780000,
        "short_interest": 12,
        "catalyst": "Q4 earnings beat by 15%, record deliveries",
        "catalyst_strength": "strong",
        "sentiment": "bullish",
        "indicators": {
            "rsi": 58,
            "macd": 2.5,
            "macd_signal": 1.8
        }
    }
    
    print("\n📊 Trade Scoring Example:")
    print(f"   Symbol: {example['symbol']}")
    print(f"   Direction: {example['direction']}")
    
    breakdown = scorer.score_trade_setup(example)
    
    print(f"\n🎯 Score Breakdown:")
    print(f"   Technical:    {breakdown.technical_score:.2%}")
    print(f"   Fundamental:  {breakdown.fundamental_score:.2%}")
    print(f"   Catalyst:     {breakdown.catalyst_score:.2%}")
    print(f"   Sentiment:    {breakdown.sentiment_score:.2%}")
    print(f"   ──────────────────────────")
    print(f"   Weighted Total: {breakdown.weighted_total:.2%}")
    print(f"   Confidence:     {breakdown.confidence:.2%}")
    
    print(f"\n📈 Key Factors:")
    for factor, score in sorted(breakdown.factors.items(), key=lambda x: x[1], reverse=True):
        print(f"   {factor}: {score:.2%}")
