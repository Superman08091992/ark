#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Architecture Tests

Tests the complete integration stack:
- ReasoningEngine 5-stage pipeline
- Memory synchronization (SQLite + Redis)
- Agent reasoning integration
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reasoning.reasoning_engine import (
    ReasoningEngine,
    AgentReasoningEngine,
    ReasoningResult,
    ReasoningStage
)
from reasoning.intra_agent_reasoner import ReasoningDepth
from reasoning.memory_sync import MemorySyncManager
from reasoning.kyle_reasoner import KyleReasoner


class MockAgent:
    """Mock agent for testing"""
    def __init__(self):
        self.name = "test_agent"
        self.role = "testing"
        self.intra_reasoner = KyleReasoner(
            default_depth=ReasoningDepth.MODERATE,
            enable_tree_of_selfs=True,
            max_branches_per_level=3
        )


async def test_reasoning_engine_pipeline():
    """Test ReasoningEngine 5-stage pipeline"""
    print("\n" + "="*80)
    print("TEST 1: ReasoningEngine 5-Stage Pipeline")
    print("="*80)
    
    # Create mock agent and reasoner
    agent = MockAgent()
    
    # Create reasoning engine
    engine = AgentReasoningEngine(
        agent_name="test_agent",
        intra_reasoner=agent.intra_reasoner,
        agent_instance=agent,
        default_depth=ReasoningDepth.MODERATE
    )
    
    # Execute reasoning
    print("\n📊 Executing reasoning pipeline...")
    result: ReasoningResult = await engine.reason(
        query="Analyze BTC price movement with high volume spike",
        context={"market": "crypto", "test_mode": True},
        depth=ReasoningDepth.MODERATE
    )
    
    # Validate result
    assert result.agent_name == "test_agent"
    assert result.query == "Analyze BTC price movement with high volume spike"
    assert len(result.stages) == 5, f"Expected 5 stages, got {len(result.stages)}"
    
    # Validate all 5 stages present
    expected_stages = {"perceive", "analyze", "hypothesize", "validate", "reflect"}
    actual_stages = {stage.stage.value for stage in result.stages}
    assert expected_stages == actual_stages, f"Stage mismatch: {actual_stages}"
    
    # Print stage summaries
    print("\n✅ Pipeline Execution Summary:")
    print(f"   Agent: {result.agent_name}")
    print(f"   Overall Confidence: {result.overall_confidence:.3f}")
    print(f"   Total Duration: {result.total_duration_ms:.1f}ms")
    print(f"\n   Stages:")
    
    for i, stage in enumerate(result.stages, 1):
        print(f"   {i}. {stage.stage.value.upper()}")
        print(f"      Confidence: {stage.confidence:.3f}")
        print(f"      Duration: {stage.duration_ms:.1f}ms")
        print(f"      Traces: {len(stage.traces)} items")
        if stage.metadata:
            print(f"      Metadata: {list(stage.metadata.keys())}")
    
    print("\n✅ TEST 1 PASSED: 5-stage pipeline executed successfully")
    return True


async def test_memory_synchronization():
    """Test memory synchronization (SQLite only, skip Redis)"""
    print("\n" + "="*80)
    print("TEST 2: Memory Synchronization (SQLite)")
    print("="*80)
    
    # Create temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_reasoning.db")
        
        # Create memory sync manager (without Redis)
        print("\n📦 Initializing memory sync...")
        memory_sync = MemorySyncManager(
            db_path=db_path,
            enable_pubsub=False  # Skip Redis for this test
        )
        
        await memory_sync.start()
        print("✅ Memory sync started (SQLite only)")
        
        # Create test reasoning result
        agent = MockAgent()
        engine = AgentReasoningEngine(
            agent_name="test_agent",
            intra_reasoner=agent.intra_reasoner,
            agent_instance=agent,
            default_depth=ReasoningDepth.SHALLOW
        )
        
        print("\n🧠 Generating reasoning result...")
        result = await engine.reason(
            query="Test query for memory sync",
            context={"test": True},
            depth=ReasoningDepth.SHALLOW
        )
        
        # Log to database
        print("\n💾 Logging to database...")
        session_id = await memory_sync.log_reasoning_session(result)
        print(f"✅ Logged session: {session_id}")
        
        # Retrieve session
        print("\n🔍 Retrieving session from database...")
        retrieved = memory_sync.get_session(session_id)
        assert retrieved is not None, "Session not found in database"
        assert retrieved['agent_name'] == 'test_agent'
        assert retrieved['query'] == 'Test query for memory sync'
        print(f"✅ Retrieved session: {retrieved['session_id']}")
        print(f"   Agent: {retrieved['agent_name']}")
        print(f"   Confidence: {retrieved['overall_confidence']}")
        print(f"   Stages: {len(retrieved['stages'])}")
        
        # Query sessions
        print("\n🔍 Querying all sessions...")
        sessions = memory_sync.query_sessions(agent_name='test_agent', limit=10)
        assert len(sessions) >= 1, "Should have at least 1 session"
        print(f"✅ Found {len(sessions)} session(s)")
        
        # Get agent statistics
        print("\n📊 Getting agent statistics...")
        stats = memory_sync.get_agent_statistics('test_agent')
        print(f"✅ Statistics:")
        print(f"   Total Sessions: {stats['total_sessions']}")
        print(f"   Avg Confidence: {stats['avg_confidence']:.3f}")
        print(f"   Avg Duration: {stats['avg_duration_ms']:.1f}ms")
        
        # Cleanup
        await memory_sync.stop()
        print("\n✅ Memory sync stopped")
    
    print("\n✅ TEST 2 PASSED: Memory synchronization works correctly")
    return True


async def test_confidence_calculation():
    """Test confidence calculation across stages"""
    print("\n" + "="*80)
    print("TEST 3: Confidence Calculation")
    print("="*80)
    
    agent = MockAgent()
    engine = AgentReasoningEngine(
        agent_name="test_agent",
        intra_reasoner=agent.intra_reasoner,
        agent_instance=agent,
        default_depth=ReasoningDepth.MODERATE
    )
    
    print("\n🧪 Testing confidence calculation...")
    result = await engine.reason(
        query="High confidence test query",
        context={"test": True},
        depth=ReasoningDepth.MODERATE
    )
    
    # Extract stage confidences
    stage_confidences = [s.confidence for s in result.stages]
    print(f"\n📊 Stage Confidences:")
    for i, (stage, conf) in enumerate(zip(result.stages, stage_confidences), 1):
        print(f"   {i}. {stage.stage.value}: {conf:.3f}")
    
    print(f"\n   Overall: {result.overall_confidence:.3f}")
    
    # Validate confidence in valid range
    assert 0.0 <= result.overall_confidence <= 1.0, "Confidence out of range"
    for conf in stage_confidences:
        assert 0.0 <= conf <= 1.0, f"Stage confidence out of range: {conf}"
    
    print("\n✅ TEST 3 PASSED: Confidence calculations are valid")
    return True


async def test_depth_scaling():
    """Test reasoning depth scaling"""
    print("\n" + "="*80)
    print("TEST 4: Reasoning Depth Scaling")
    print("="*80)
    
    agent = MockAgent()
    engine = AgentReasoningEngine(
        agent_name="test_agent",
        intra_reasoner=agent.intra_reasoner,
        agent_instance=agent,
        default_depth=ReasoningDepth.MODERATE
    )
    
    query = "Test depth scaling"
    depths = [ReasoningDepth.SHALLOW, ReasoningDepth.MODERATE, ReasoningDepth.DEEP]
    
    results = {}
    
    for depth in depths:
        print(f"\n🧪 Testing {depth.name} depth...")
        result = await engine.reason(query=query, depth=depth)
        results[depth.name] = {
            'duration': result.total_duration_ms,
            'confidence': result.overall_confidence,
            'stages': len(result.stages)
        }
        print(f"   Duration: {result.total_duration_ms:.1f}ms")
        print(f"   Confidence: {result.overall_confidence:.3f}")
    
    print(f"\n📊 Depth Comparison:")
    for depth_name, metrics in results.items():
        print(f"   {depth_name}:")
        print(f"      Duration: {metrics['duration']:.1f}ms")
        print(f"      Confidence: {metrics['confidence']:.3f}")
        print(f"      Stages: {metrics['stages']}")
    
    # All should have 5 stages regardless of depth
    for depth_name, metrics in results.items():
        assert metrics['stages'] == 5, f"{depth_name} should have 5 stages"
    
    print("\n✅ TEST 4 PASSED: Depth scaling works correctly")
    return True


async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("INTEGRATION ARCHITECTURE TEST SUITE")
    print("="*80)
    
    tests = [
        test_reasoning_engine_pipeline,
        test_memory_synchronization,
        test_confidence_calculation,
        test_depth_scaling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"   Passed: {passed}/{len(tests)}")
    print(f"   Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
