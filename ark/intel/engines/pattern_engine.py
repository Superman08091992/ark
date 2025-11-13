"""
Pattern Intelligence Engine (PIE)

Matches trade setups against 10 defined trading patterns with confidence scoring.
Implements rule-based pattern recognition with required/preferred criteria evaluation.

Author: ARK Trading Intelligence
Version: 1.0.0
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OperatorType(str, Enum):
    """Supported comparison operators for pattern matching."""
    EQ = "eq"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    BETWEEN = "between"
    EXISTS = "exists"
    PATTERN = "pattern"


@dataclass
class MatchResult:
    """Result of pattern matching for a single trade setup."""
    pattern_id: str
    pattern_name: str
    matched: bool
    confidence: float
    required_score: float
    preferred_score: float
    failed_required: List[str]
    matched_preferred: List[str]
    details: Dict[str, Any]


class PatternEngine:
    """
    Pattern Intelligence Engine (PIE)
    
    Loads trading patterns from JSON files and matches them against TradeSetup objects.
    Provides confidence scoring based on required and preferred criteria.
    """
    
    def __init__(self, patterns_dir: Optional[Path] = None):
        """
        Initialize Pattern Engine.
        
        Args:
            patterns_dir: Directory containing pattern JSON files.
                         Defaults to ark/intel/patterns/
        """
        if patterns_dir is None:
            # Default to patterns directory relative to this file
            patterns_dir = Path(__file__).parent.parent / "patterns"
        
        self.patterns_dir = Path(patterns_dir)
        self.patterns: Dict[str, Dict] = {}
        self._load_patterns()
    
    def _load_patterns(self) -> None:
        """Load all pattern JSON files from patterns directory."""
        if not self.patterns_dir.exists():
            logger.error(f"Patterns directory not found: {self.patterns_dir}")
            return
        
        pattern_files = list(self.patterns_dir.glob("*.json"))
        logger.info(f"Loading {len(pattern_files)} pattern files from {self.patterns_dir}")
        
        for pattern_file in pattern_files:
            try:
                with open(pattern_file, 'r') as f:
                    pattern_data = json.load(f)
                    pattern_id = pattern_data.get('pattern_id')
                    if pattern_id:
                        self.patterns[pattern_id] = pattern_data
                        logger.debug(f"Loaded pattern: {pattern_id}")
                    else:
                        logger.warning(f"Pattern file missing pattern_id: {pattern_file}")
            except Exception as e:
                logger.error(f"Failed to load pattern file {pattern_file}: {e}")
        
        logger.info(f"Successfully loaded {len(self.patterns)} patterns")
    
    def match_pattern(self, trade_setup: Dict[str, Any], pattern_id: str) -> MatchResult:
        """
        Match a single pattern against a trade setup.
        
        Args:
            trade_setup: Trade setup dictionary (from TradeSetup.dict())
            pattern_id: ID of pattern to match
            
        Returns:
            MatchResult with confidence score and match details
        """
        if pattern_id not in self.patterns:
            logger.error(f"Pattern not found: {pattern_id}")
            return MatchResult(
                pattern_id=pattern_id,
                pattern_name="Unknown",
                matched=False,
                confidence=0.0,
                required_score=0.0,
                preferred_score=0.0,
                failed_required=[],
                matched_preferred=[],
                details={"error": "Pattern not found"}
            )
        
        pattern = self.patterns[pattern_id]
        rules = pattern.get('rules', {})
        
        # Evaluate required rules
        required_rules = rules.get('required', [])
        failed_required = []
        required_passed = 0
        
        for rule in required_rules:
            if self._evaluate_rule(trade_setup, rule):
                required_passed += 1
            else:
                failed_required.append(rule.get('description', 'Unknown rule'))
        
        # Required score (0.0 if any required rule fails)
        if len(required_rules) > 0:
            required_score = required_passed / len(required_rules) if required_passed == len(required_rules) else 0.0
        else:
            required_score = 1.0
        
        # Evaluate preferred rules (only if all required pass)
        preferred_rules = rules.get('preferred', [])
        matched_preferred = []
        preferred_score = 0.0
        
        if required_score == 1.0:
            for rule in preferred_rules:
                if self._evaluate_rule(trade_setup, rule):
                    weight = rule.get('weight', 0.1)
                    preferred_score += weight
                    matched_preferred.append(rule.get('description', 'Unknown rule'))
        
        # Calculate final confidence
        pattern_weight = pattern.get('confidence_weight', 1.0)
        base_confidence = 0.6  # Base confidence if all required pass
        preferred_boost = min(preferred_score, 0.4)  # Max 40% boost from preferred
        
        if required_score == 1.0:
            confidence = min((base_confidence + preferred_boost) * pattern_weight, 1.0)
            matched = True
        else:
            confidence = 0.0
            matched = False
        
        return MatchResult(
            pattern_id=pattern_id,
            pattern_name=pattern.get('name', pattern_id),
            matched=matched,
            confidence=confidence,
            required_score=required_score,
            preferred_score=preferred_score,
            failed_required=failed_required,
            matched_preferred=matched_preferred,
            details={
                "direction": pattern.get('direction'),
                "category": pattern.get('category'),
                "entry_strategy": pattern.get('entry_strategy'),
                "risk_management": pattern.get('risk_management'),
                "profit_targets": pattern.get('profit_targets'),
                "warnings": pattern.get('warnings', [])
            }
        )
    
    def _evaluate_rule(self, trade_setup: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """
        Evaluate a single rule against trade setup.
        
        Args:
            trade_setup: Trade setup dictionary
            rule: Rule definition with field, operator, value
            
        Returns:
            True if rule passes, False otherwise
        """
        field = rule.get('field')
        operator = rule.get('operator')
        expected_value = rule.get('value')
        
        if not field or not operator:
            logger.warning(f"Invalid rule: missing field or operator")
            return False
        
        # Extract actual value from trade setup (supports nested fields)
        actual_value = self._get_nested_field(trade_setup, field)
        
        if actual_value is None:
            # If field doesn't exist, check if it's optional
            if operator == OperatorType.EXISTS and expected_value is False:
                return True
            return False
        
        # Evaluate based on operator
        try:
            if operator == OperatorType.EQ:
                return str(actual_value).lower() == str(expected_value).lower()
            
            elif operator == OperatorType.GT:
                # Handle special cases like "2x_avg_volume"
                if isinstance(expected_value, str) and "x_" in expected_value:
                    multiplier, base_field = self._parse_multiplier_value(expected_value)
                    base_value = self._get_nested_field(trade_setup, base_field)
                    if base_value is None:
                        return False
                    return float(actual_value) > (float(base_value) * multiplier)
                return float(actual_value) > float(expected_value)
            
            elif operator == OperatorType.LT:
                if isinstance(expected_value, str) and "x_" in expected_value:
                    multiplier, base_field = self._parse_multiplier_value(expected_value)
                    base_value = self._get_nested_field(trade_setup, base_field)
                    if base_value is None:
                        return False
                    return float(actual_value) < (float(base_value) * multiplier)
                return float(actual_value) < float(expected_value)
            
            elif operator == OperatorType.GTE:
                return float(actual_value) >= float(expected_value)
            
            elif operator == OperatorType.LTE:
                return float(actual_value) <= float(expected_value)
            
            elif operator == OperatorType.BETWEEN:
                if isinstance(expected_value, list) and len(expected_value) == 2:
                    return float(expected_value[0]) <= float(actual_value) <= float(expected_value[1])
                return False
            
            elif operator == OperatorType.EXISTS:
                return bool(actual_value) == bool(expected_value)
            
            elif operator == OperatorType.PATTERN:
                # Pattern matching for special cases
                return self._evaluate_pattern_match(actual_value, expected_value, trade_setup)
            
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
                
        except (ValueError, TypeError) as e:
            logger.debug(f"Rule evaluation error for {field}: {e}")
            return False
    
    def _get_nested_field(self, data: Dict[str, Any], field_path: str) -> Any:
        """
        Get value from nested dictionary using dot notation.
        
        Args:
            data: Dictionary to search
            field_path: Field path like "indicators.rsi" or "float_"
            
        Returns:
            Value at field path, or None if not found
        """
        parts = field_path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return None
            else:
                return None
        
        return current
    
    def _parse_multiplier_value(self, value: str) -> Tuple[float, str]:
        """
        Parse multiplier expressions like "2x_avg_volume".
        
        Args:
            value: String like "2x_avg_volume"
            
        Returns:
            Tuple of (multiplier, base_field_name)
        """
        parts = value.split('x_')
        multiplier = float(parts[0]) if parts[0] else 1.0
        base_field = parts[1] if len(parts) > 1 else ""
        return multiplier, base_field
    
    def _evaluate_pattern_match(self, actual: Any, pattern: str, trade_setup: Dict) -> bool:
        """
        Evaluate special pattern-based matching.
        
        Args:
            actual: Actual value from trade setup
            pattern: Pattern name to match
            trade_setup: Full trade setup for context
            
        Returns:
            True if pattern matches
        """
        # Special pattern matching logic
        if pattern == "tight_consolidation":
            # Check if price is consolidating (simplified check)
            return "consolidat" in str(actual).lower()
        
        elif pattern == "breakout_setup":
            return "breakout" in str(actual).lower()
        
        elif pattern == "failed_breakout":
            return "failed" in str(actual).lower() or "reject" in str(actual).lower()
        
        elif pattern == "v_bottom":
            return "v" in str(actual).lower() or "reversal" in str(actual).lower()
        
        elif pattern == "breaking_resistance":
            return "break" in str(actual).lower()
        
        else:
            # Default: string contains check
            return pattern.lower() in str(actual).lower()
    
    def match_all_patterns(self, trade_setup: Dict[str, Any], 
                          direction_filter: Optional[str] = None,
                          min_confidence: float = 0.5) -> List[MatchResult]:
        """
        Match trade setup against all patterns.
        
        Args:
            trade_setup: Trade setup dictionary
            direction_filter: Optional filter ('long', 'short', 'both')
            min_confidence: Minimum confidence threshold (0.0-1.0)
            
        Returns:
            List of MatchResults sorted by confidence (descending)
        """
        results = []
        
        for pattern_id, pattern in self.patterns.items():
            # Apply direction filter if specified
            if direction_filter:
                pattern_direction = pattern.get('direction')
                if pattern_direction != 'both' and pattern_direction != direction_filter:
                    continue
            
            # Match pattern
            result = self.match_pattern(trade_setup, pattern_id)
            
            # Apply confidence filter
            if result.confidence >= min_confidence:
                results.append(result)
        
        # Sort by confidence descending
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        return results
    
    def get_pattern_details(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full pattern definition.
        
        Args:
            pattern_id: Pattern identifier
            
        Returns:
            Pattern dictionary or None if not found
        """
        return self.patterns.get(pattern_id)
    
    def list_patterns(self, direction: Optional[str] = None) -> List[Dict[str, str]]:
        """
        List all available patterns with metadata.
        
        Args:
            direction: Optional direction filter ('long', 'short', 'both')
            
        Returns:
            List of pattern metadata dicts
        """
        pattern_list = []
        
        for pattern_id, pattern in self.patterns.items():
            if direction and pattern.get('direction') not in [direction, 'both']:
                continue
            
            pattern_list.append({
                "pattern_id": pattern_id,
                "name": pattern.get('name', pattern_id),
                "description": pattern.get('description', ''),
                "direction": pattern.get('direction', 'unknown'),
                "category": pattern.get('category', 'unknown'),
                "confidence_weight": pattern.get('confidence_weight', 1.0)
            })
        
        return pattern_list
    
    def enrich_trade_setup(self, trade_setup: Dict[str, Any], 
                          match_result: MatchResult) -> Dict[str, Any]:
        """
        Enrich trade setup with pattern match results.
        
        Args:
            trade_setup: Original trade setup dictionary
            match_result: Pattern match result
            
        Returns:
            Enriched trade setup with pattern data
        """
        enriched = trade_setup.copy()
        
        enriched['pattern'] = match_result.pattern_name
        enriched['confidence'] = match_result.confidence
        
        # Add pattern-specific scoring weights
        pattern = self.patterns.get(match_result.pattern_id)
        if pattern:
            enriched['scoring_weights'] = pattern.get('scoring', {})
            enriched['entry_strategy'] = match_result.details.get('entry_strategy')
            enriched['risk_management'] = match_result.details.get('risk_management')
            enriched['profit_targets'] = match_result.details.get('profit_targets')
            enriched['warnings'] = match_result.details.get('warnings', [])
        
        # Track pattern engine processing
        if 'agents_processed' not in enriched:
            enriched['agents_processed'] = []
        enriched['agents_processed'].append('pattern_engine')
        
        return enriched


# Module-level singleton for convenient access
_engine_instance: Optional[PatternEngine] = None


def get_pattern_engine() -> PatternEngine:
    """Get or create singleton Pattern Engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = PatternEngine()
    return _engine_instance


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    engine = PatternEngine()
    
    print(f"\n📊 Pattern Intelligence Engine Loaded")
    print(f"   Patterns: {len(engine.patterns)}")
    
    # List all patterns
    print("\n🎯 Available Patterns:")
    for p in engine.list_patterns():
        print(f"   - {p['name']} ({p['direction']}) - {p['description'][:60]}...")
    
    # Example trade setup
    example_setup = {
        "symbol": "GME",
        "direction": "long",
        "float_": 15.5,  # 15.5M float
        "short_interest": 45,  # 45% short interest
        "volume": 25000000,
        "avg_volume": 8000000,
        "price": 22.50,
        "price_action": "tight_consolidation",
        "catalyst": "Ryan Cohen tweet",
        "indicators": {
            "rsi": 55
        }
    }
    
    print(f"\n🔍 Testing Squeezer Pattern Match:")
    result = engine.match_pattern(example_setup, "squeezer")
    print(f"   Matched: {result.matched}")
    print(f"   Confidence: {result.confidence:.2%}")
    print(f"   Required Score: {result.required_score:.2%}")
    print(f"   Preferred Score: {result.preferred_score:.2f}")
    if result.failed_required:
        print(f"   Failed: {result.failed_required}")
    if result.matched_preferred:
        print(f"   Matched Preferred: {result.matched_preferred}")
