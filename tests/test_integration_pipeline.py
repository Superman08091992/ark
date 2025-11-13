"""
Integration Tests - Full Trading Intelligence Pipeline

Tests the complete pipeline:
Kyle → Joey → Pattern Engine → Trade Scorer → HRM → Kenny → Telegram

Author: ARK Trading Intelligence
Version: 1.0.0
"""

import pytest
import asyncio
import logging
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Test fixtures
@pytest.fixture
def sample_trade_setup() -> Dict[str, Any]:
    """Sample trade setup for testing"""
    return {
        "symbol": "TSLA",
        "direction": "long",
        "price": 250.50,
        "float_": 18.5,
        "market_cap": 800000,
        "volume": 85000000,
        "avg_volume": 35000000,
        "short_interest": 22.5,
        "catalyst": "Strong Q4 earnings beat with record deliveries",
        "sentiment": "bullish",
        "indicators": {
            "rsi": 68.5,
            "macd": 2.3,
            "macd_signal": 1.8,
            "atr": 12.5
        }
    }


@pytest.fixture
def mock_data_provider():
    """Mock data provider for testing"""
    from services.data_sources.base_provider import Quote, Bar
    from datetime import datetime
    
    class MockDataProvider:
        name = "mock_provider"
        
        async def initialize(self):
            return True
        
        async def get_quote(self, symbol: str):
            return Quote(
                symbol=symbol,
                bid=250.00,
                ask=250.50,
                last=250.25,
                volume=85000000,
                timestamp=datetime.utcnow(),
                source="mock"
            )
        
        async def get_bars(self, symbol: str, **kwargs):
            return [
                Bar(
                    symbol=symbol,
                    open=245.00,
                    high=252.00,
                    low=244.50,
                    close=250.50,
                    volume=85000000,
                    timestamp=datetime.utcnow(),
                    vwap=248.50,
                    source="mock"
                )
            ]
    
    return MockDataProvider()


# ============================
# Pattern Engine Tests
# ============================

@pytest.mark.asyncio
async def test_pattern_matching(sample_trade_setup):
    """Test pattern matching engine"""
    from ark.intel.engines.pattern_engine import get_pattern_engine
    
    logger.info("🔍 Testing pattern matching...")
    
    pattern_engine = get_pattern_engine()
    
    # Match patterns
    matches = pattern_engine.match_all_patterns(
        trade_setup=sample_trade_setup,
        direction_filter="long",
        min_confidence=0.60
    )
    
    logger.info(f"✅ Found {len(matches)} patterns")
    
    # Assertions
    assert len(matches) > 0, "Should find at least one pattern match"
    assert all(m.confidence >= 0.60 for m in matches), "All matches should meet min confidence"
    assert matches[0].confidence >= matches[-1].confidence, "Matches should be sorted by confidence"
    
    # Log best pattern
    best = matches[0]
    logger.info(f"🎯 Best pattern: {best.pattern_name} ({best.confidence:.1%})")


@pytest.mark.asyncio
async def test_trade_scoring(sample_trade_setup):
    """Test multi-factor trade scoring"""
    from ark.intel.engines.trade_scorer import get_trade_scorer
    
    logger.info("📊 Testing trade scoring...")
    
    trade_scorer = get_trade_scorer()
    
    # Calculate scores
    breakdown = trade_scorer.score_trade_setup(sample_trade_setup)
    
    logger.info(f"✅ Quality score: {breakdown.weighted_total:.1%} (Grade: {breakdown.grade})")
    
    # Assertions
    assert 0.0 <= breakdown.technical <= 1.0
    assert 0.0 <= breakdown.fundamental <= 1.0
    assert 0.0 <= breakdown.catalyst <= 1.0
    assert 0.0 <= breakdown.sentiment <= 1.0
    assert 0.0 <= breakdown.weighted_total <= 1.0
    assert breakdown.grade in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
    
    logger.info(f"   Technical: {breakdown.technical:.1%}")
    logger.info(f"   Fundamental: {breakdown.fundamental:.1%}")
    logger.info(f"   Catalyst: {breakdown.catalyst:.1%}")
    logger.info(f"   Sentiment: {breakdown.sentiment:.1%}")


@pytest.mark.asyncio
async def test_execution_planning(sample_trade_setup):
    """Test execution plan builder"""
    from ark.intel.engines.trade_plan_builder import get_trade_plan_builder
    
    logger.info("📋 Testing execution planning...")
    
    plan_builder = get_trade_plan_builder(account_size=100000.0)
    
    # Build plan
    plan = plan_builder.build_plan(sample_trade_setup)
    
    logger.info(f"✅ Plan: Entry ${plan.entry_price:.2f}, Stop ${plan.stop_loss:.2f}, "
                f"Size {plan.position_size_shares} shares ({plan.position_size_percent:.1%})")
    
    # Assertions
    assert plan.entry_price > 0
    assert plan.stop_loss > 0
    assert plan.stop_loss < plan.entry_price  # Long trade
    assert plan.position_size_shares > 0
    assert 0.0 < plan.position_size_percent <= 0.15  # Max 15% position
    assert plan.risk_reward_ratio >= 2.0  # Min 2:1 R:R
    assert len(plan.targets) >= 2  # At least 2 targets
    
    logger.info(f"   Risk/Reward: 1:{plan.risk_reward_ratio:.2f}")
    logger.info(f"   Risk: ${plan.risk_dollars:.2f}")


# ============================
# HRM Validation Tests
# ============================

@pytest.mark.asyncio
async def test_hrm_validation_approval(sample_trade_setup):
    """Test HRM validation - should approve good setup"""
    from agents.unified_signal_router import UnifiedSignalRouter
    
    logger.info("🛡️ Testing HRM validation (approval case)...")
    
    router = UnifiedSignalRouter(account_size=100000.0)
    
    # Validate
    result = await router._validate_with_hrm(sample_trade_setup, "test-correlation-1")
    
    logger.info(f"✅ HRM result: {'APPROVED' if result['approved'] else 'REJECTED'}")
    
    # Assertions
    assert result['approved'] is True, "Good setup should be approved"
    assert len(result['errors']) == 0, "Should have no errors"
    
    if result['warnings']:
        logger.info(f"⚠️ Warnings: {result['warnings']}")


@pytest.mark.asyncio
async def test_hrm_validation_rejection():
    """Test HRM validation - should reject bad setup"""
    from agents.unified_signal_router import UnifiedSignalRouter
    
    logger.info("🛡️ Testing HRM validation (rejection case)...")
    
    router = UnifiedSignalRouter(account_size=100000.0)
    
    # Create bad trade setup (penny stock)
    bad_setup = {
        "symbol": "BADSTK",
        "direction": "long",
        "price": 0.50,  # Penny stock
        "float_": 2.0,
        "market_cap": 5.0,  # Small cap
        "volume": 1000000,
        "avg_volume": 500000
    }
    
    # Validate
    result = await router._validate_with_hrm(bad_setup, "test-correlation-2")
    
    logger.info(f"✅ HRM result: {'APPROVED' if result['approved'] else 'REJECTED'}")
    
    # Assertions
    assert result['approved'] is False, "Bad setup should be rejected"
    assert len(result['errors']) > 0, "Should have errors"
    
    logger.info(f"❌ Rejection reasons: {result['errors']}")


# ============================
# Full Pipeline Tests
# ============================

@pytest.mark.asyncio
async def test_full_pipeline_success(sample_trade_setup):
    """Test complete pipeline from ingestion to completion"""
    from agents.unified_signal_router import UnifiedSignalRouter
    from shared.agent_bus import agent_bus
    
    logger.info("🚀 Testing full pipeline (success case)...")
    
    # Create router
    router = UnifiedSignalRouter(account_size=100000.0)
    
    # Mock Telegram service
    with patch.object(router.telegram, '_initialized', True):
        with patch.object(router.telegram, 'send_trade_signal', new_callable=AsyncMock) as mock_telegram:
            mock_telegram.return_value = True
            
            # Process through pipeline
            correlation_id = "test-full-pipeline-1"
            await router.process_trade_setup(sample_trade_setup, correlation_id)
            
            # Wait for async processing
            await asyncio.sleep(0.5)
            
            logger.info("✅ Pipeline completed")
            
            # Verify Telegram was called
            assert mock_telegram.called, "Telegram notification should be sent"
            
            # Check conversation history
            messages = agent_bus.get_conversation_history(correlation_id)
            logger.info(f"📨 Pipeline generated {len(messages)} messages")
            
            assert len(messages) > 0, "Should have messages in conversation"
            
            # Check stats
            stats = router.get_stats()
            logger.info(f"📈 Stats: {stats}")
            assert stats['total_processed'] >= 1
            assert stats['approved'] >= 1


@pytest.mark.asyncio
async def test_full_pipeline_rejection():
    """Test complete pipeline with HRM rejection"""
    from agents.unified_signal_router import UnifiedSignalRouter
    from shared.agent_bus import agent_bus
    
    logger.info("🚀 Testing full pipeline (rejection case)...")
    
    router = UnifiedSignalRouter(account_size=100000.0)
    
    # Bad setup (penny stock)
    bad_setup = {
        "symbol": "PENNY",
        "direction": "long",
        "price": 0.75,
        "float_": 1.5,
        "market_cap": 3.0,
        "volume": 500000,
        "avg_volume": 250000
    }
    
    # Process
    correlation_id = "test-rejection-1"
    await router.process_trade_setup(bad_setup, correlation_id)
    
    await asyncio.sleep(0.5)
    
    logger.info("✅ Pipeline completed (rejected)")
    
    # Check stats
    stats = router.get_stats()
    assert stats['rejected'] >= 1, "Should have rejections"
    
    logger.info(f"📈 Stats: {stats}")


# ============================
# Agent Communication Tests
# ============================

@pytest.mark.asyncio
async def test_agent_bus_communication():
    """Test agent bus message routing"""
    from shared.agent_bus import agent_bus, AgentMessage, MessageType
    
    logger.info("📡 Testing agent bus communication...")
    
    # Clear history
    agent_bus._message_history.clear()
    
    # Create test message
    correlation_id = "test-agent-bus-1"
    message = AgentMessage(
        message_id="test-msg-1",
        correlation_id=correlation_id,
        from_agent="kyle",
        to_agent="joey",
        message_type=MessageType.REQUEST,
        payload={"symbol": "TSLA", "action": "enrich"}
    )
    
    # Publish
    await agent_bus.publish(message)
    
    # Verify
    history = agent_bus.get_conversation_history(correlation_id)
    assert len(history) == 1
    assert history[0].from_agent == "kyle"
    assert history[0].to_agent == "joey"
    
    logger.info("✅ Agent bus working correctly")


@pytest.mark.asyncio
async def test_error_bus_escalation():
    """Test error bus escalation"""
    from shared.error_bus import error_bus, ErrorEscalation, ErrorSeverity
    
    logger.info("🚨 Testing error bus escalation...")
    
    # Create error
    error = ErrorEscalation(
        error_id="test-error-1",
        correlation_id="test-correlation-1",
        agent_name="test_agent",
        error_message="Test error message",
        severity=ErrorSeverity.WARNING,
        error_code="TEST_ERROR"
    )
    
    # Escalate
    await error_bus.escalate(error)
    
    # Verify
    errors = error_bus.get_errors_by_correlation("test-correlation-1")
    assert len(errors) >= 1
    assert errors[0].error_message == "Test error message"
    
    logger.info("✅ Error bus working correctly")


# ============================
# Correlation ID Tracing Tests
# ============================

@pytest.mark.asyncio
async def test_correlation_id_propagation(sample_trade_setup):
    """Test that correlation_id propagates through entire pipeline"""
    from agents.unified_signal_router import UnifiedSignalRouter
    from shared.agent_bus import agent_bus
    
    logger.info("🔗 Testing correlation ID propagation...")
    
    router = UnifiedSignalRouter(account_size=100000.0)
    
    # Mock Telegram
    with patch.object(router.telegram, '_initialized', True):
        with patch.object(router.telegram, 'send_trade_signal', new_callable=AsyncMock) as mock_telegram:
            mock_telegram.return_value = True
            
            # Process with unique correlation_id
            test_correlation_id = "test-correlation-propagation-123"
            await router.process_trade_setup(sample_trade_setup, test_correlation_id)
            
            await asyncio.sleep(0.5)
            
            # Get conversation history
            messages = agent_bus.get_conversation_history(test_correlation_id)
            
            logger.info(f"📨 Found {len(messages)} messages with correlation_id")
            
            # Verify all messages have same correlation_id
            assert len(messages) > 0, "Should have messages"
            for msg in messages:
                assert msg.correlation_id == test_correlation_id, "All messages should have same correlation_id"
            
            logger.info("✅ Correlation ID propagated correctly through pipeline")


# ============================
# Data Provider Tests
# ============================

@pytest.mark.asyncio
async def test_data_aggregator(mock_data_provider):
    """Test data aggregator with mock provider"""
    from services.data_sources.aggregator import DataAggregator
    
    logger.info("📊 Testing data aggregator...")
    
    aggregator = DataAggregator()
    aggregator.add_provider(mock_data_provider, priority=1)
    
    # Get quote
    quote = await aggregator.get_quote("TSLA")
    
    assert quote is not None
    assert quote.symbol == "TSLA"
    assert quote.last > 0
    
    logger.info(f"✅ Got quote: {quote.symbol} @ ${quote.last:.2f}")
    
    # Test caching
    quote2 = await aggregator.get_quote("TSLA", use_cache=True)
    assert quote2 is not None
    
    logger.info("✅ Data aggregator working with cache")


# ============================
# Telegram Service Tests
# ============================

def test_telegram_message_formatting():
    """Test Telegram message formatting"""
    from services.telegram_service import TelegramService
    
    logger.info("💬 Testing Telegram message formatting...")
    
    telegram = TelegramService()
    
    # Sample trade setup
    trade_setup = {
        "setup_id": "test-123",
        "correlation_id": "corr-456",
        "symbol": "TSLA",
        "direction": "long",
        "price": 250.50,
        "pattern": "Squeezer",
        "confidence": 0.85,
        "catalyst": "Strong earnings beat",
        "scores": {
            "quality_score": 0.78,
            "technical": 0.82,
            "fundamental": 0.75
        },
        "execution_plan": {
            "entry_price": 251.00,
            "stop_loss": 238.00,
            "targets": [
                {"price": 270.00, "percentage": 0.075, "exit_portion": 0.33},
                {"price": 285.00, "percentage": 0.135, "exit_portion": 0.33}
            ],
            "position_size_percent": 0.085,
            "risk_reward_ratio": 3.2
        },
        "status": "approved"
    }
    
    # Format message
    message = telegram.format_trade_signal(trade_setup)
    
    logger.info("✅ Message formatted")
    
    # Assertions
    assert "TSLA" in message
    assert "LONG SIGNAL" in message
    assert "Squeezer" in message
    assert "85.0%" in message  # Confidence
    assert "Entry" in message
    assert "Stop Loss" in message
    assert "Targets" in message
    
    logger.info(f"📝 Sample message:\n{message}")


# ============================
# Run Tests
# ============================

if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "-s"])
