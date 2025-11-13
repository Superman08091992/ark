"""
Unified Signal Router

Central orchestrator for the trading intelligence pipeline:
Kyle (Scanner) → Joey (Enricher) → Pattern Engine → Trade Scorer → HRM (Validator) → Kenny (Executor) → Telegram

Integrates:
- Agent communication via AgentBus
- Pattern Intelligence Engine
- Multi-factor Trade Scorer
- Trade Plan Builder
- HRM validation with ruleset
- Error handling via ErrorBus

Author: ARK Trading Intelligence
Version: 1.0.0
"""

import asyncio
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Agent communication
from shared.agent_bus import BaseAgent, AgentMessage, MessageType, agent_bus
from shared.error_bus import ErrorHandlerMixin, ErrorSeverity, error_bus

# Trading intelligence engines
from ark.intel.engines.pattern_engine import get_pattern_engine
from ark.intel.engines.trade_scorer import get_trade_scorer
from ark.intel.engines.trade_plan_builder import get_trade_plan_builder

logger = logging.getLogger(__name__)


class UnifiedSignalRouter(BaseAgent, ErrorHandlerMixin):
    """
    Central orchestrator for trading signal pipeline.
    
    Workflow:
    1. Receives TradeSetup from Kyle/Joey
    2. Runs Pattern Engine (pattern matching)
    3. Runs Trade Scorer (quality scoring)
    4. Validates with HRM (risk/ethics checks)
    5. Builds execution plan (Trade Plan Builder)
    6. Sends to Kenny for execution
    7. Notifies Telegram on completion
    """
    
    def __init__(self, 
                 account_size: float = 100000.0,
                 hrm_ruleset_path: Optional[Path] = None):
        """
        Initialize Unified Signal Router.
        
        Args:
            account_size: Trading account size for position sizing
            hrm_ruleset_path: Path to HRM ruleset YAML file
        """
        super().__init__("unified_signal_router", auto_subscribe=True)
        
        # Initialize engines
        self.pattern_engine = get_pattern_engine()
        self.trade_scorer = get_trade_scorer()
        self.plan_builder = get_trade_plan_builder(account_size)
        
        # Load HRM ruleset
        if hrm_ruleset_path is None:
            hrm_ruleset_path = Path(__file__).parent.parent / "config" / "HRM_RULESET.yaml"
        self.hrm_ruleset = self._load_hrm_ruleset(hrm_ruleset_path)
        
        # Statistics
        self.stats = {
            "total_processed": 0,
            "approved": 0,
            "rejected": 0,
            "errors": 0
        }
        
        self.logger.info(
            f"UnifiedSignalRouter initialized with account size ${account_size:,.2f}"
        )
    
    def _load_hrm_ruleset(self, path: Path) -> Dict[str, Any]:
        """Load HRM ruleset from YAML file."""
        try:
            with open(path, 'r') as f:
                ruleset = yaml.safe_load(f)
                self.logger.info(f"Loaded HRM ruleset from {path}")
                return ruleset
        except Exception as e:
            self.logger.error(f"Failed to load HRM ruleset: {e}")
            return {}
    
    async def handle_message(self, message: AgentMessage) -> None:
        """
        Handle incoming messages.
        
        Expects TradeSetup payload from Kyle or Joey.
        """
        if message.message_type != MessageType.REQUEST:
            return
        
        payload = message.payload
        
        # Check if this is a trade setup
        if 'trade_setup' not in payload and 'symbol' not in payload:
            self.logger.debug(f"Ignoring non-trade-setup message from {message.from_agent}")
            return
        
        # Extract or build trade setup
        trade_setup = payload.get('trade_setup', payload)
        
        # Ensure correlation ID
        if 'correlation_id' not in trade_setup:
            trade_setup['correlation_id'] = message.correlation_id
        
        self.logger.info(
            f"🔄 Processing trade setup: {trade_setup.get('symbol', 'UNKNOWN')} "
            f"(correlation: {message.correlation_id})"
        )
        
        # Process through pipeline
        await self.process_trade_setup(trade_setup, message.correlation_id)
    
    async def process_trade_setup(self, trade_setup: Dict[str, Any], correlation_id: str) -> None:
        """
        Process trade setup through full pipeline.
        
        Args:
            trade_setup: Trade setup dictionary
            correlation_id: Correlation ID for tracing
        """
        self.stats['total_processed'] += 1
        symbol = trade_setup.get('symbol', 'UNKNOWN')
        
        try:
            # ========== STAGE 1: PATTERN MATCHING ==========
            self.logger.info(f"🔍 Stage 1: Pattern matching for {symbol}")
            
            direction = trade_setup.get('direction', 'long')
            patterns = self.pattern_engine.match_all_patterns(
                trade_setup,
                direction_filter=direction,
                min_confidence=0.65
            )
            
            if not patterns:
                self.logger.warning(f"❌ No patterns matched for {symbol} (direction: {direction})")
                await self.report_error(
                    f"No patterns found for {symbol}",
                    severity=ErrorSeverity.WARNING,
                    error_code="NO_PATTERN_MATCH",
                    correlation_id=correlation_id
                )
                self.stats['rejected'] += 1
                return
            
            # Use best matching pattern
            best_pattern = patterns[0]
            self.logger.info(
                f"✅ Pattern matched: {best_pattern.pattern_name} "
                f"({best_pattern.confidence:.0%} confidence)"
            )
            
            # Enrich trade setup with pattern data
            trade_setup = self.pattern_engine.enrich_trade_setup(trade_setup, best_pattern)
            
            # ========== STAGE 2: QUALITY SCORING ==========
            self.logger.info(f"📊 Stage 2: Quality scoring for {symbol}")
            
            # Get pattern-specific weights if available
            scoring_weights = trade_setup.get('scoring_weights')
            
            score_breakdown = self.trade_scorer.score_trade_setup(
                trade_setup,
                weights=scoring_weights
            )
            
            self.logger.info(
                f"✅ Quality score: {score_breakdown.weighted_total:.0%} "
                f"(Tech: {score_breakdown.technical_score:.0%}, "
                f"Fund: {score_breakdown.fundamental_score:.0%}, "
                f"Cat: {score_breakdown.catalyst_score:.0%}, "
                f"Sent: {score_breakdown.sentiment_score:.0%})"
            )
            
            # Add scores to trade setup
            trade_setup['scores'] = {
                'technical_score': score_breakdown.technical_score,
                'fundamental_score': score_breakdown.fundamental_score,
                'catalyst_score': score_breakdown.catalyst_score,
                'sentiment_score': score_breakdown.sentiment_score,
                'weighted_total': score_breakdown.weighted_total,
                'confidence': score_breakdown.confidence
            }
            
            # ========== STAGE 3: HRM VALIDATION ==========
            self.logger.info(f"🛡️ Stage 3: HRM validation for {symbol}")
            
            validation_result = await self._validate_with_hrm(trade_setup, correlation_id)
            
            if not validation_result['approved']:
                self.logger.warning(
                    f"❌ HRM rejected {symbol}: {', '.join(validation_result['errors'])}"
                )
                
                # Send rejection message
                await self.send_message(
                    to_agent="hrm",
                    payload={
                        "trade_setup": trade_setup,
                        "status": "rejected",
                        "validation_errors": validation_result['errors']
                    },
                    message_type=MessageType.RESPONSE,
                    correlation_id=correlation_id
                )
                
                self.stats['rejected'] += 1
                return
            
            self.logger.info(f"✅ HRM approved {symbol}")
            trade_setup['status'] = 'approved'
            trade_setup['validation_errors'] = []
            
            # ========== STAGE 4: EXECUTION PLANNING ==========
            self.logger.info(f"📋 Stage 4: Building execution plan for {symbol}")
            
            execution_plan = self.plan_builder.build_plan(trade_setup)
            
            self.logger.info(
                f"✅ Plan built: Entry ${execution_plan.entry_price:.2f}, "
                f"Stop ${execution_plan.stop_loss:.2f}, "
                f"Size {execution_plan.position_size_shares} shares "
                f"({execution_plan.position_size_percent:.1%}), "
                f"R:R {execution_plan.risk_reward_ratio:.1f}:1"
            )
            
            # Add execution plan to trade setup
            trade_setup['execution_plan'] = {
                'entry_price': execution_plan.entry_price,
                'entry_type': execution_plan.entry_type.value,
                'stop_loss': execution_plan.stop_loss,
                'stop_type': execution_plan.stop_type.value,
                'position_size_shares': execution_plan.position_size_shares,
                'position_size_percent': execution_plan.position_size_percent,
                'targets': execution_plan.targets,
                'risk_reward_ratio': execution_plan.risk_reward_ratio,
                'risk_dollars': execution_plan.risk_dollars,
                'notes': execution_plan.notes
            }
            
            # ========== STAGE 5: SEND TO KENNY ==========
            self.logger.info(f"🚀 Stage 5: Sending to Kenny for execution: {symbol}")
            
            await self.send_message(
                to_agent="kenny",
                payload={
                    "trade_setup": trade_setup,
                    "action": "execute_plan",
                    "priority": "normal"
                },
                message_type=MessageType.REQUEST,
                correlation_id=correlation_id,
                priority=3  # High priority
            )
            
            # ========== STAGE 6: NOTIFY TELEGRAM ==========
            self.logger.info(f"📢 Stage 6: Broadcasting signal event: {symbol}")
            
            await self.send_event(
                payload={
                    "event_type": "signal_generated",
                    "symbol": symbol,
                    "direction": direction,
                    "pattern": best_pattern.pattern_name,
                    "confidence": trade_setup['confidence'],
                    "quality_score": score_breakdown.weighted_total,
                    "entry": execution_plan.entry_price,
                    "stop": execution_plan.stop_loss,
                    "targets": execution_plan.targets,
                    "risk_reward": execution_plan.risk_reward_ratio
                },
                correlation_id=correlation_id
            )
            
            self.stats['approved'] += 1
            
            self.logger.info(
                f"✅ Pipeline complete for {symbol} "
                f"(correlation: {correlation_id})"
            )
        
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"❌ Pipeline error for {symbol}: {e}", exc_info=True)
            
            await self.report_error(
                f"Pipeline failed for {symbol}: {str(e)}",
                severity=ErrorSeverity.ERROR,
                error_code="PIPELINE_ERROR",
                correlation_id=correlation_id,
                exception=e,
                context={"symbol": symbol, "stage": "unknown"}
            )
    
    async def _validate_with_hrm(self, trade_setup: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """
        Validate trade setup against HRM ruleset.
        
        Args:
            trade_setup: Trade setup to validate
            correlation_id: Correlation ID for tracing
            
        Returns:
            {"approved": bool, "errors": List[str], "warnings": List[str]}
        """
        if not self.hrm_ruleset or not self.hrm_ruleset.get('enabled'):
            self.logger.warning("HRM ruleset not loaded or disabled - auto-approving")
            return {"approved": True, "errors": [], "warnings": []}
        
        errors = []
        warnings = []
        
        # Validate ethics rules
        ethics_rules = self.hrm_ruleset.get('ethics', {}).get('rules', [])
        for rule in ethics_rules:
            if not rule.get('enabled', True):
                continue
            
            result = self._evaluate_rule(trade_setup, rule)
            if not result['passed']:
                severity = rule.get('severity', 'error')
                if severity == 'critical' or severity == 'error':
                    errors.append(result['message'])
                else:
                    warnings.append(result['message'])
        
        # Validate risk rules
        risk_rules = self.hrm_ruleset.get('risk', {}).get('rules', [])
        for rule in risk_rules:
            if not rule.get('enabled', True):
                continue
            
            result = self._evaluate_rule(trade_setup, rule)
            if not result['passed']:
                severity = rule.get('severity', 'error')
                if severity == 'critical' or severity == 'error':
                    errors.append(result['message'])
                else:
                    warnings.append(result['message'])
        
        # Validate pattern quality rules
        pattern_rules = self.hrm_ruleset.get('pattern_quality', {}).get('rules', [])
        for rule in pattern_rules:
            if not rule.get('enabled', True):
                continue
            
            result = self._evaluate_rule(trade_setup, rule)
            if not result['passed']:
                severity = rule.get('severity', 'error')
                if severity == 'critical' or severity == 'error':
                    errors.append(result['message'])
                else:
                    warnings.append(result['message'])
        
        # Check strict mode
        strict_mode = self.hrm_ruleset.get('strict_mode', True)
        approved = len(errors) == 0 and (not strict_mode or len(warnings) == 0)
        
        if not approved:
            await self.report_warning(
                f"HRM validation failed: {len(errors)} errors, {len(warnings)} warnings",
                error_code="HRM_VALIDATION_FAILED",
                correlation_id=correlation_id,
                context={"errors": errors, "warnings": warnings}
            )
        
        return {
            "approved": approved,
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_rule(self, trade_setup: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate single HRM rule against trade setup."""
        validation = rule.get('validation', {})
        field = validation.get('field', '')
        operator = validation.get('operator', '')
        value = validation.get('value')
        
        # Get field value (support nested fields)
        parts = field.split('.')
        current = trade_setup
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = None
                break
        
        field_value = current
        
        # Evaluate operator
        try:
            if operator == 'gte' and field_value is not None:
                passed = float(field_value) >= float(value)
            elif operator == 'lte' and field_value is not None:
                passed = float(field_value) <= float(value)
            elif operator == 'equals' or operator == 'eq':
                passed = str(field_value).lower() == str(value).lower()
            elif operator == 'not_equals':
                passed = str(field_value).lower() != str(value).lower()
            elif operator == 'exists':
                passed = (field_value is not None) == bool(value)
            elif operator == 'in':
                values = validation.get('values', [])
                passed = str(field_value).lower() in [str(v).lower() for v in values]
            elif operator == 'between':
                if isinstance(value, list) and len(value) == 2:
                    passed = float(value[0]) <= float(field_value) <= float(value[1])
                else:
                    passed = False
            elif operator == 'not_contains':
                values = validation.get('values', [])
                text = str(field_value).lower() if field_value else ''
                passed = not any(str(v).lower() in text for v in values)
            else:
                passed = True  # Unknown operator, pass by default
        except (ValueError, TypeError):
            passed = False
        
        return {
            "passed": passed,
            "message": rule.get('error_message', f"Rule {rule.get('id')} failed")
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            **self.stats,
            "approval_rate": self.stats['approved'] / self.stats['total_processed'] 
                            if self.stats['total_processed'] > 0 else 0.0
        }


# Global instance
_router_instance: Optional[UnifiedSignalRouter] = None


def get_unified_router(account_size: Optional[float] = None) -> UnifiedSignalRouter:
    """Get or create singleton Unified Signal Router."""
    global _router_instance
    if _router_instance is None or account_size is not None:
        _router_instance = UnifiedSignalRouter(account_size=account_size or 100000.0)
    return _router_instance


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def demo():
        # Create router
        router = UnifiedSignalRouter(account_size=50000.0)
        
        print("\n🚀 Unified Signal Router Demo")
        
        # Example trade setup from Kyle/Joey
        example_setup = {
            "symbol": "TSLA",
            "price": 245.50,
            "direction": "long",
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
                "macd_signal": 1.8,
                "atr": 12.5
            },
            "correlation_id": "test-demo-123"
        }
        
        print(f"\n📊 Processing setup: {example_setup['symbol']}")
        
        # Process through pipeline
        await router.process_trade_setup(example_setup, "test-demo-123")
        
        await asyncio.sleep(1)
        
        # Show stats
        print(f"\n📈 Router Statistics:")
        stats = router.get_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2%}" if value < 1 else f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
    
    asyncio.run(demo())
