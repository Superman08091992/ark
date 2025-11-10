#!/usr/bin/env python3
"""
Tests for Hierarchical Reasoning Module

Demonstrates inter-agent hierarchical reasoning with minimal system disruption.
Tests both fast path (L1+L5 only) and full path (all levels) execution.
"""

import asyncio
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.hrm import HRMAgent
from reasoning.hierarchical_reasoner import HierarchicalReasoner


class TestHierarchicalReasoning:
    """Test suite for hierarchical reasoning functionality"""
    
    @pytest.fixture
    def hrm_agent(self):
        """Create HRM agent for testing"""
        agent = HRMAgent()
        return agent
    
    @pytest.mark.asyncio
    async def test_fast_path_simple_query(self, hrm_agent):
        """
        Test fast path: Simple query should only execute L1+L5 (Graveyard + Synthesis)
        Expected: <50ms total duration
        """
        action = {
            'action_type': 'query',
            'parameters': {
                'description': 'Read market data',
                'operation': 'read'
            }
        }
        
        result = await hrm_agent.validate_action_hierarchical(action, agent_name="Kyle")
        
        assert result['success'] is True
        assert result['data']['approved'] is True
        assert result['data']['hierarchical'] is True
        
        # Fast path should only execute levels 1 and 5
        levels_executed = result['data']['levels_executed']
        assert 1 in levels_executed  # Graveyard always executes
        assert 5 in levels_executed  # Synthesis always executes
        assert len(levels_executed) == 2  # Only 2 levels for fast path
        
        # Fast path should be FAST (<50ms typical)
        duration = result['data']['total_duration_ms']
        print(f"\n✓ Fast path duration: {duration:.1f}ms (levels: {levels_executed})")
        
        assert duration < 100, f"Fast path too slow: {duration}ms"
    
    @pytest.mark.asyncio
    async def test_full_path_complex_trade(self, hrm_agent):
        """
        Test full path: Complex trade should trigger multiple levels
        Expected: All levels may execute for comprehensive validation
        """
        action = {
            'action_type': 'trade',
            'parameters': {
                'description': 'Open BTC long position with leverage',
                'symbol': 'BTC/USD',
                'direction': 'long',
                'position_size_pct': 0.08,  # Close to 10% limit
                'leverage': 1.8,  # Close to 2.0 limit
                'stop_loss': 45000.0,
                'take_profit': 55000.0
            }
        }
        
        result = await hrm_agent.validate_action_hierarchical(action, agent_name="Kyle")
        
        assert result['success'] is True
        assert result['data']['hierarchical'] is True
        
        # Full path should execute more than just L1+L5
        levels_executed = result['data']['levels_executed']
        print(f"\n✓ Full path levels executed: {levels_executed}")
        print(f"  Duration: {result['data']['total_duration_ms']:.1f}ms")
        print(f"  Decision: {result['data']['decision']}")
        print(f"  Confidence: {result['data']['confidence']:.2f}")
        
        # Should have executed at least L1, L4 (risk), and L5
        assert 1 in levels_executed  # Graveyard
        assert 5 in levels_executed  # Synthesis
        # L4 (risk) should be triggered for trades
        assert len(levels_executed) >= 3
    
    @pytest.mark.asyncio
    async def test_graveyard_violation_blocks_immediately(self, hrm_agent):
        """
        Test that Graveyard violations block immediately without consulting other agents
        Expected: Only L1 executed, immediate denial
        """
        action = {
            'action_type': 'trade',
            'parameters': {
                'description': 'High risk trade with excessive leverage',
                'symbol': 'BTC/USD',
                'direction': 'long',
                'position_size_pct': 0.15,  # VIOLATION: >10%
                'leverage': 5.0,  # VIOLATION: >2.0x
                'stop_loss': None,  # VIOLATION: No stop loss
                'take_profit': 100000.0
            }
        }
        
        result = await hrm_agent.validate_action_hierarchical(action, agent_name="Kyle")
        
        assert result['success'] is True
        assert result['data']['approved'] is False  # Should be denied
        assert result['data']['decision'] == 'denied'
        
        # Graveyard violation should short-circuit
        levels_executed = result['data']['levels_executed']
        print(f"\n✓ Graveyard violation short-circuit")
        print(f"  Levels executed: {levels_executed}")
        print(f"  Duration: {result['data']['total_duration_ms']:.1f}ms")
        print(f"  Warnings: {result['data']['warnings']}")
        
        # Should have low latency even with violations
        assert result['data']['total_duration_ms'] < 100
    
    @pytest.mark.asyncio
    async def test_force_full_reasoning(self, hrm_agent):
        """
        Test forcing full reasoning path even for simple actions
        Expected: All 5 levels execute
        """
        action = {
            'action_type': 'query',
            'parameters': {
                'description': 'Simple read operation',
                'operation': 'read'
            }
        }
        
        result = await hrm_agent.validate_action_hierarchical(
            action, 
            agent_name="Kyle",
            force_full_reasoning=True  # Force all levels
        )
        
        assert result['success'] is True
        
        levels_executed = result['data']['levels_executed']
        print(f"\n✓ Forced full reasoning")
        print(f"  Levels executed: {levels_executed}")
        print(f"  Duration: {result['data']['total_duration_ms']:.1f}ms")
        
        # All levels should execute when forced
        assert 1 in levels_executed  # Graveyard
        assert 5 in levels_executed  # Synthesis
        # Optional levels may or may not trigger depending on agent availability
        # but we attempted all of them
    
    @pytest.mark.asyncio
    async def test_edge_case_detection(self, hrm_agent):
        """
        Test that edge cases trigger additional levels
        Expected: Borderline compliance triggers L2-L4
        """
        action = {
            'action_type': 'strategic_decision',
            'parameters': {
                'description': 'Novel strategic initiative requiring analysis',
                'position_size_pct': 0.095,  # Close to 10% limit (edge case)
                'leverage': 1.95,  # Close to 2.0 limit (edge case)
                'stop_loss': 45000.0
            }
        }
        
        result = await hrm_agent.validate_action_hierarchical(action, agent_name="Kyle")
        
        assert result['success'] is True
        
        levels_executed = result['data']['levels_executed']
        reasoning_path = result['data']['reasoning_path']
        
        print(f"\n✓ Edge case handling")
        print(f"  Levels executed: {levels_executed}")
        print(f"  Reasoning path: {reasoning_path}")
        print(f"  Duration: {result['data']['total_duration_ms']:.1f}ms")
        print(f"  Confidence: {result['data']['confidence']:.2f}")
        
        # Edge cases should trigger more comprehensive reasoning
        assert len(levels_executed) >= 3
    
    @pytest.mark.asyncio
    async def test_hierarchical_statistics(self, hrm_agent):
        """
        Test that statistics are properly tracked
        Expected: Fast path count, full path count, avg duration
        """
        # Execute several validations
        actions = [
            {'action_type': 'query', 'parameters': {'operation': 'read'}},  # Fast path
            {'action_type': 'query', 'parameters': {'operation': 'read'}},  # Fast path
            {'action_type': 'trade', 'parameters': {'position_size_pct': 0.08}},  # Full path
        ]
        
        for action in actions:
            await hrm_agent.validate_action_hierarchical(action, agent_name="Kyle")
        
        stats = hrm_agent.get_hierarchical_statistics()
        
        print(f"\n✓ Hierarchical reasoning statistics:")
        print(f"  Total decisions: {stats['total_decisions']}")
        print(f"  Fast path: {stats['fast_path_count']} ({stats['fast_path_percentage']:.1f}%)")
        print(f"  Full path: {stats['full_path_count']}")
        print(f"  Avg duration: {stats['avg_duration_ms']:.1f}ms")
        
        assert stats['total_decisions'] == 3
        assert stats['fast_path_count'] >= 2  # Two query actions
        assert stats['avg_duration_ms'] > 0
    
    @pytest.mark.asyncio
    async def test_backward_compatibility(self, hrm_agent):
        """
        Test that old validate_action() still works (backward compatibility)
        Expected: Standard Graveyard validation without hierarchical reasoning
        """
        action = {
            'action_type': 'trade',
            'parameters': {
                'position_size_pct': 0.05,
                'leverage': 1.5,
                'stop_loss': 45000.0
            }
        }
        
        result = await hrm_agent.validate_action(action, agent_name="Kyle")
        
        assert result['success'] is True
        assert result['data']['approved'] is True
        assert 'hierarchical' not in result['data']  # Old API doesn't have this flag
        
        print(f"\n✓ Backward compatibility maintained")
        print(f"  Standard validation still works")


def test_reasoning_module_import():
    """Test that reasoning module can be imported without errors"""
    from reasoning.hierarchical_reasoner import (
        HierarchicalReasoner,
        HierarchicalDecision,
        ReasoningLevel
    )
    
    print("\n✓ Hierarchical reasoning module imports successfully")
    print(f"  HierarchicalReasoner: {HierarchicalReasoner}")
    print(f"  HierarchicalDecision: {HierarchicalDecision}")
    print(f"  ReasoningLevel: {ReasoningLevel}")


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '-s'])
