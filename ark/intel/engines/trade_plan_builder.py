"""
Trade Plan Builder

Generates comprehensive execution plans for trade setups:
- Entry price calculation (limit, market, stop-limit)
- Stop loss placement (pattern-specific)
- Position sizing (risk-based)
- Profit targets (multi-level exits)
- Risk metrics (R:R ratio, max loss %)

Author: ARK Trading Intelligence
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OrderType(str, Enum):
    """Order execution types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class StopType(str, Enum):
    """Stop loss calculation methods."""
    PERCENTAGE = "percentage"
    ATR = "atr"
    SUPPORT_RESISTANCE = "support_resistance"
    PATTERN_SPECIFIC = "pattern_specific"


@dataclass
class ExecutionPlan:
    """Complete execution plan for a trade."""
    
    # Entry
    entry_price: float
    entry_type: OrderType
    entry_limit_price: Optional[float] = None
    
    # Stop Loss
    stop_loss: float
    stop_type: StopType
    stop_loss_percent: float
    
    # Position Sizing
    position_size_shares: int
    position_size_percent: float
    position_size_dollars: float
    
    # Profit Targets
    targets: List[Dict[str, Any]]
    
    # Risk Metrics
    risk_dollars: float
    risk_percent: float
    risk_reward_ratio: float
    max_loss_dollars: float
    max_gain_dollars: float
    
    # Metadata
    confidence: float
    notes: List[str]


class TradePlanBuilder:
    """
    Trade Plan Builder Engine
    
    Converts trade setups into actionable execution plans with:
    - Pattern-aware entry strategies
    - Risk-based position sizing
    - Multi-level profit targets
    - Comprehensive risk metrics
    """
    
    def __init__(self, 
                 account_size: float = 100000.0,
                 max_risk_per_trade: float = 0.02,
                 default_commission: float = 0.0):
        """
        Initialize Trade Plan Builder.
        
        Args:
            account_size: Total account capital
            max_risk_per_trade: Maximum risk per trade (0.02 = 2%)
            default_commission: Commission per trade (flat fee)
        """
        self.account_size = account_size
        self.max_risk_per_trade = max_risk_per_trade
        self.default_commission = default_commission
        
        logger.info(
            f"TradePlanBuilder initialized: "
            f"Account=${account_size:,.2f}, "
            f"Max Risk={max_risk_per_trade:.1%}"
        )
    
    def build_plan(self, trade_setup: Dict[str, Any]) -> ExecutionPlan:
        """
        Generate comprehensive execution plan.
        
        Args:
            trade_setup: Trade setup dictionary with pattern data
            
        Returns:
            ExecutionPlan with entry, stops, targets, sizing
        """
        # Extract key data
        symbol = trade_setup.get('symbol', 'UNKNOWN')
        price = trade_setup.get('price', 0)
        direction = trade_setup.get('direction', 'long')
        pattern = trade_setup.get('pattern', '')
        confidence = trade_setup.get('confidence', 0.5)
        
        logger.info(f"Building execution plan for {symbol} @ ${price:.2f} ({direction})")
        
        # Calculate entry
        entry_price, entry_type, entry_limit = self._calculate_entry(trade_setup)
        
        # Calculate stop loss
        stop_loss, stop_type = self._calculate_stop_loss(trade_setup, entry_price)
        stop_loss_percent = abs(stop_loss - entry_price) / entry_price
        
        # Calculate position size
        position_size, position_percent, position_dollars = self._calculate_position_size(
            trade_setup, entry_price, stop_loss
        )
        
        # Calculate profit targets
        targets = self._calculate_targets(trade_setup, entry_price, stop_loss)
        
        # Calculate risk metrics
        risk_dollars = abs(entry_price - stop_loss) * position_size
        risk_percent = risk_dollars / self.account_size
        
        if targets:
            avg_target = sum(t['price'] for t in targets) / len(targets)
            max_gain_dollars = abs(avg_target - entry_price) * position_size
            risk_reward_ratio = max_gain_dollars / risk_dollars if risk_dollars > 0 else 0
        else:
            max_gain_dollars = 0
            risk_reward_ratio = 0
        
        max_loss_dollars = risk_dollars + self.default_commission
        
        # Generate notes
        notes = self._generate_notes(trade_setup, stop_loss_percent, risk_reward_ratio)
        
        return ExecutionPlan(
            entry_price=entry_price,
            entry_type=entry_type,
            entry_limit_price=entry_limit,
            stop_loss=stop_loss,
            stop_type=stop_type,
            stop_loss_percent=stop_loss_percent,
            position_size_shares=position_size,
            position_size_percent=position_percent,
            position_size_dollars=position_dollars,
            targets=targets,
            risk_dollars=risk_dollars,
            risk_percent=risk_percent,
            risk_reward_ratio=risk_reward_ratio,
            max_loss_dollars=max_loss_dollars,
            max_gain_dollars=max_gain_dollars,
            confidence=confidence,
            notes=notes
        )
    
    def _calculate_entry(self, trade_setup: Dict[str, Any]) -> Tuple[float, OrderType, Optional[float]]:
        """
        Calculate entry price and order type.
        
        Args:
            trade_setup: Trade setup with pattern data
            
        Returns:
            (entry_price, order_type, limit_price)
        """
        price = trade_setup.get('price', 0)
        direction = trade_setup.get('direction', 'long')
        entry_strategy = trade_setup.get('entry_strategy', {})
        
        if not entry_strategy:
            # Default: market order
            return price, OrderType.MARKET, None
        
        strategy_type = entry_strategy.get('type', 'market')
        
        if strategy_type == 'breakout':
            # Enter on breakout: limit slightly above current price (long) or below (short)
            if direction == 'long':
                limit_price = price * 1.005  # 0.5% above
                return limit_price, OrderType.LIMIT, limit_price
            else:
                limit_price = price * 0.995  # 0.5% below
                return limit_price, OrderType.LIMIT, limit_price
        
        elif strategy_type == 'pullback':
            # Enter on pullback: limit below current price (long) or above (short)
            if direction == 'long':
                limit_price = price * 0.98  # 2% below
                return limit_price, OrderType.LIMIT, limit_price
            else:
                limit_price = price * 1.02  # 2% above
                return limit_price, OrderType.LIMIT, limit_price
        
        elif strategy_type in ['reversal_short', 'fade_entry', 'capitulation_entry']:
            # Wait for confirmation: use limit order at current price
            return price, OrderType.LIMIT, price
        
        else:
            # Default: market order
            return price, OrderType.MARKET, None
    
    def _calculate_stop_loss(self, trade_setup: Dict[str, Any], entry_price: float) -> Tuple[float, StopType]:
        """
        Calculate stop loss price.
        
        Args:
            trade_setup: Trade setup with pattern and risk data
            entry_price: Planned entry price
            
        Returns:
            (stop_loss_price, stop_type)
        """
        direction = trade_setup.get('direction', 'long')
        risk_management = trade_setup.get('risk_management', {})
        
        # Try pattern-specific stop first
        if risk_management:
            stop_type_str = risk_management.get('stop_loss_type', 'percentage')
            stop_value = risk_management.get('stop_loss_value', 0.05)
            
            if stop_type_str == 'percentage':
                # Percentage-based stop
                if direction == 'long':
                    stop_loss = entry_price * (1 - stop_value)
                else:
                    stop_loss = entry_price * (1 + stop_value)
                return stop_loss, StopType.PERCENTAGE
            
            elif stop_type_str == 'atr' or stop_type_str == 'volatility_based':
                # ATR-based stop
                atr = trade_setup.get('indicators', {}).get('atr', entry_price * 0.05)
                
                # Extract multiplier from stop_value (e.g., "2x_atr" -> 2.0)
                if isinstance(stop_value, str) and 'x' in stop_value:
                    multiplier = float(stop_value.split('x')[0])
                else:
                    multiplier = float(stop_value) if stop_value > 1 else 2.0
                
                if direction == 'long':
                    stop_loss = entry_price - (atr * multiplier)
                else:
                    stop_loss = entry_price + (atr * multiplier)
                return stop_loss, StopType.ATR
            
            elif stop_type_str in ['support_level', 'fixed']:
                # Support/resistance-based stop
                if isinstance(stop_value, str):
                    # Value is a field reference
                    support = trade_setup.get(stop_value, entry_price * 0.95)
                else:
                    # Value is explicit price or percentage
                    support = stop_value if stop_value > 1 else entry_price * (1 - stop_value)
                
                if direction == 'long':
                    stop_loss = support * 0.99  # Slightly below support
                else:
                    stop_loss = support * 1.01  # Slightly above resistance
                return stop_loss, StopType.SUPPORT_RESISTANCE
        
        # Fallback: use default 5% stop
        default_stop_pct = 0.05
        if direction == 'long':
            stop_loss = entry_price * (1 - default_stop_pct)
        else:
            stop_loss = entry_price * (1 + default_stop_pct)
        
        return stop_loss, StopType.PERCENTAGE
    
    def _calculate_position_size(self, 
                                 trade_setup: Dict[str, Any],
                                 entry_price: float,
                                 stop_loss: float) -> Tuple[int, float, float]:
        """
        Calculate position size based on risk.
        
        Args:
            trade_setup: Trade setup with risk parameters
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            (shares, percent_of_capital, dollar_amount)
        """
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share == 0:
            logger.warning("Risk per share is zero - using minimum position")
            risk_per_share = entry_price * 0.01  # 1% fallback
        
        # Calculate max risk dollars
        max_risk_dollars = self.account_size * self.max_risk_per_trade
        
        # Check for pattern-specific position size override
        risk_management = trade_setup.get('risk_management', {})
        position_size_max = risk_management.get('position_size_max')
        
        if position_size_max:
            # Use pattern's max position size
            max_position_pct = position_size_max
        else:
            # Default max position size
            max_position_pct = 0.10  # 10%
        
        # Calculate shares based on risk
        shares_by_risk = int(max_risk_dollars / risk_per_share)
        
        # Calculate shares based on max position size
        max_position_dollars = self.account_size * max_position_pct
        shares_by_max = int(max_position_dollars / entry_price)
        
        # Use the smaller of the two (more conservative)
        shares = min(shares_by_risk, shares_by_max)
        
        # Ensure at least 1 share
        shares = max(1, shares)
        
        # Calculate actual position metrics
        position_dollars = shares * entry_price
        position_percent = position_dollars / self.account_size
        
        logger.debug(
            f"Position sizing: {shares} shares @ ${entry_price:.2f} = "
            f"${position_dollars:,.2f} ({position_percent:.2%})"
        )
        
        return shares, position_percent, position_dollars
    
    def _calculate_targets(self, trade_setup: Dict[str, Any], entry_price: float, stop_loss: float) -> List[Dict[str, Any]]:
        """
        Calculate profit target levels.
        
        Args:
            trade_setup: Trade setup with target data
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            List of target dictionaries
        """
        direction = trade_setup.get('direction', 'long')
        profit_targets = trade_setup.get('profit_targets', [])
        
        if not profit_targets:
            # Generate default targets
            return self._generate_default_targets(entry_price, stop_loss, direction)
        
        targets = []
        for target_def in profit_targets:
            level = target_def.get('level', 0)
            percentage = target_def.get('percentage', 0)
            exit_portion = target_def.get('exit_portion', 0)
            description = target_def.get('description', '')
            
            # Calculate target price
            if direction == 'long':
                target_price = entry_price * (1 + percentage)
            else:
                target_price = entry_price * (1 - percentage)
            
            targets.append({
                "level": level,
                "price": target_price,
                "percentage_move": percentage,
                "exit_portion": exit_portion,
                "description": description
            })
        
        return targets
    
    def _generate_default_targets(self, entry_price: float, stop_loss: float, direction: str) -> List[Dict[str, Any]]:
        """Generate default 3-level targets based on risk."""
        risk = abs(entry_price - stop_loss)
        
        targets = []
        
        # Target 1: 1.5R (50% exit)
        if direction == 'long':
            t1_price = entry_price + (risk * 1.5)
        else:
            t1_price = entry_price - (risk * 1.5)
        
        targets.append({
            "level": 1,
            "price": t1_price,
            "percentage_move": abs(t1_price - entry_price) / entry_price,
            "exit_portion": 0.50,
            "description": "First target (1.5R)"
        })
        
        # Target 2: 2.5R (30% exit)
        if direction == 'long':
            t2_price = entry_price + (risk * 2.5)
        else:
            t2_price = entry_price - (risk * 2.5)
        
        targets.append({
            "level": 2,
            "price": t2_price,
            "percentage_move": abs(t2_price - entry_price) / entry_price,
            "exit_portion": 0.30,
            "description": "Second target (2.5R)"
        })
        
        # Target 3: 4R (20% exit)
        if direction == 'long':
            t3_price = entry_price + (risk * 4.0)
        else:
            t3_price = entry_price - (risk * 4.0)
        
        targets.append({
            "level": 3,
            "price": t3_price,
            "percentage_move": abs(t3_price - entry_price) / entry_price,
            "exit_portion": 0.20,
            "description": "Final target (4R)"
        })
        
        return targets
    
    def _generate_notes(self, trade_setup: Dict[str, Any], stop_pct: float, rr_ratio: float) -> List[str]:
        """Generate execution notes and warnings."""
        notes = []
        
        # Pattern warnings
        warnings = trade_setup.get('warnings', [])
        notes.extend(warnings[:3])  # Max 3 warnings
        
        # Stop distance note
        if stop_pct > 0.10:
            notes.append(f"⚠️ Wide stop ({stop_pct:.1%}) - consider reducing position size")
        elif stop_pct < 0.02:
            notes.append(f"⚡ Tight stop ({stop_pct:.1%}) - ensure adequate volatility buffer")
        
        # Risk-reward note
        if rr_ratio < 2.0:
            notes.append(f"⚠️ Low R:R ratio ({rr_ratio:.1f}:1) - consider passing")
        elif rr_ratio > 4.0:
            notes.append(f"✅ Excellent R:R ratio ({rr_ratio:.1f}:1)")
        
        # Confidence note
        confidence = trade_setup.get('confidence', 0)
        if confidence < 0.70:
            notes.append(f"⚠️ Lower confidence ({confidence:.0%}) - reduce size or wait")
        elif confidence > 0.85:
            notes.append(f"✅ High confidence ({confidence:.0%}) setup")
        
        return notes


# Module-level singleton
_builder_instance: Optional[TradePlanBuilder] = None


def get_trade_plan_builder(account_size: Optional[float] = None) -> TradePlanBuilder:
    """Get or create singleton Trade Plan Builder instance."""
    global _builder_instance
    if _builder_instance is None or account_size is not None:
        _builder_instance = TradePlanBuilder(
            account_size=account_size or 100000.0
        )
    return _builder_instance


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    builder = TradePlanBuilder(account_size=50000.0, max_risk_per_trade=0.02)
    
    # Example trade setup (from pattern engine)
    example = {
        "symbol": "TSLA",
        "price": 245.50,
        "direction": "long",
        "pattern": "Squeezer",
        "confidence": 0.87,
        "entry_strategy": {
            "type": "breakout",
            "trigger": "break_above_resistance"
        },
        "risk_management": {
            "stop_loss_type": "percentage",
            "stop_loss_value": 0.05,
            "position_size_max": 0.10
        },
        "profit_targets": [
            {"level": 1, "percentage": 0.15, "exit_portion": 0.33, "description": "First resistance"},
            {"level": 2, "percentage": 0.30, "exit_portion": 0.33, "description": "Extended move"},
            {"level": 3, "percentage": 0.50, "exit_portion": 0.34, "description": "Blow-off top"}
        ],
        "warnings": [
            "High volatility - use tight stops",
            "Watch for halt risk on rapid moves"
        ],
        "indicators": {
            "atr": 12.5
        }
    }
    
    print("\n📋 Trade Plan Builder Example:")
    print(f"   Symbol: {example['symbol']}")
    print(f"   Pattern: {example['pattern']}")
    print(f"   Confidence: {example['confidence']:.0%}")
    
    plan = builder.build_plan(example)
    
    print(f"\n💰 Execution Plan:")
    print(f"   Entry: ${plan.entry_price:.2f} ({plan.entry_type.value})")
    print(f"   Stop Loss: ${plan.stop_loss:.2f} ({plan.stop_type.value})")
    print(f"   Stop Distance: {plan.stop_loss_percent:.2%}")
    print(f"\n📊 Position Sizing:")
    print(f"   Shares: {plan.position_size_shares:,}")
    print(f"   Dollar Amount: ${plan.position_size_dollars:,.2f}")
    print(f"   % of Capital: {plan.position_size_percent:.2%}")
    print(f"\n🎯 Profit Targets:")
    for target in plan.targets:
        print(f"   Level {target['level']}: ${target['price']:.2f} "
              f"({target['percentage_move']:.1%}) - "
              f"Exit {target['exit_portion']:.0%}")
    print(f"\n⚖️ Risk Metrics:")
    print(f"   Risk: ${plan.risk_dollars:,.2f} ({plan.risk_percent:.2%})")
    print(f"   Max Loss: ${plan.max_loss_dollars:,.2f}")
    print(f"   Max Gain: ${plan.max_gain_dollars:,.2f}")
    print(f"   R:R Ratio: {plan.risk_reward_ratio:.2f}:1")
    print(f"\n📝 Notes:")
    for note in plan.notes:
        print(f"   {note}")
