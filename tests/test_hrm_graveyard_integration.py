"""
Test HRM integration with Graveyard
Tests the full validation pipeline: Kenny action → HRM validation → Graveyard enforcement
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the database path for testing
os.environ['ARK_DB_PATH'] = '/tmp/ark_test.db'

from agents.hrm import HRMAgent
from graveyard.ethics import validate_against_graveyard


class TestHRMGraveyardIntegration:
    """Test full integration between HRM and Graveyard"""
    
    def setup_method(self):
        """Setup test environment"""
        # Create HRM agent (will initialize with Graveyard)
        self.hrm = HRMAgent()
    
    def test_hrm_loads_graveyard_rules(self):
        """Test that HRM successfully loads Graveyard rules at init"""
        assert hasattr(self.hrm, 'immutable_rules')
        assert hasattr(self.hrm, 'ethical_categories')
        assert len(self.hrm.immutable_rules) > 20
        assert 'trading' in self.hrm.ethical_categories
        assert 'risk_management' in self.hrm.ethical_categories
        print("✅ HRM loaded Graveyard rules")
    
    def test_hrm_validate_action_api(self):
        """Test HRM's public validate_action API"""
        # Valid action
        valid_action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'SPY',
                'position_size_pct': 0.05,
                'stop_loss': 450,
                'leverage': 1.0
            },
            'agent': 'Kenny',
            'timestamp': '2025-01-01T12:00:00'
        }
        
        result = asyncio.run(self.hrm.validate_action(valid_action, 'Kenny'))
        
        assert result['success'] is True
        assert result['data']['approved'] is True
        assert result['data']['compliance_score'] >= 0.95
        print("✅ HRM validated safe action")
    
    def test_hrm_reject_unsafe_action(self):
        """Test HRM rejects unsafe actions via Graveyard"""
        # Unsafe action
        unsafe_action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'RISKY',
                'position_size_pct': 0.50,  # Way too large!
                'stop_loss': None,  # No protection!
                'leverage': 5.0  # Too much leverage!
            },
            'agent': 'Kenny',
            'timestamp': '2025-01-01T12:00:00'
        }
        
        result = asyncio.run(self.hrm.validate_action(unsafe_action, 'Kenny'))
        
        assert result['success'] is True
        assert result['data']['approved'] is False
        assert len(result['data']['violations']) >= 3
        assert result['data']['compliance_score'] < 0.5
        print("✅ HRM rejected unsafe action")
    
    def test_hrm_tool_enforce_ethics_uses_graveyard(self):
        """Test that HRM's tool_enforce_ethics uses Graveyard"""
        context = "Execute a trade: buy 50% of capital in leveraged positions without stop-loss"
        
        result = asyncio.run(self.hrm.tool_enforce_ethics(context))
        
        assert result['success'] is True
        assert result['data']['graveyard_validation'] is True
        assert result['data']['approved'] is False  # Should reject this risky trade
        assert len(result['data']['violations']) > 0
        print("✅ HRM tool_enforce_ethics integrated with Graveyard")
    
    def test_hrm_parse_context_to_action(self):
        """Test HRM's context parsing for Graveyard validation"""
        # Test trading context
        trade_context = "buy TSLA with high leverage and no stop-loss"
        action = self.hrm._parse_context_to_action(trade_context)
        
        assert action['action_type'] == 'trade'
        assert 'parameters' in action
        assert action['parameters']['stop_loss'] is None
        
        # Test data handling context
        data_context = "collect personal data without user consent"
        action = self.hrm._parse_context_to_action(data_context)
        
        assert action['action_type'] == 'data_handling'
        print("✅ HRM context parsing works correctly")
    
    def test_graveyard_rules_summary(self):
        """Test HRM can display Graveyard rules summary"""
        summary = self.hrm._get_core_rules_summary()
        
        assert 'insider trading' in summary.lower()
        assert '10%' in summary or 'position' in summary.lower()
        print("✅ HRM displays Graveyard rules summary")
    
    def test_validation_loop_simulation(self):
        """Simulate full validation loop: Kenny → HRM → Graveyard"""
        print("\n" + "=" * 60)
        print("VALIDATION LOOP SIMULATION")
        print("=" * 60)
        
        # Scenario 1: Kenny proposes conservative trade
        print("\n📊 Scenario 1: Kenny proposes conservative trade")
        kenny_action_safe = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'SPY',
                'position_size_pct': 0.03,
                'stop_loss': 580,
                'take_profit': 600,
                'leverage': 1.0,
                'risk_reward_ratio': 3.0
            },
            'agent': 'Kenny',
            'timestamp': '2025-01-01T12:00:00'
        }
        
        print("  Kenny: Proposing trade...")
        result1 = asyncio.run(self.hrm.validate_action(kenny_action_safe, 'Kenny'))
        print(f"  HRM: Validated with Graveyard")
        print(f"  Result: {'✅ APPROVED' if result1['data']['approved'] else '❌ REJECTED'}")
        print(f"  Compliance: {result1['data']['compliance_score']:.1%}")
        print(f"  Violations: {len(result1['data']['violations'])}")
        
        assert result1['data']['approved'] is True
        
        # Scenario 2: Kenny proposes risky trade
        print("\n📊 Scenario 2: Kenny proposes risky trade")
        kenny_action_risky = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'MEME_STOCK',
                'position_size_pct': 0.25,  # Too large!
                'stop_loss': None,  # No protection!
                'leverage': 3.0,  # Too high!
                'risk_reward_ratio': 0.5  # Poor ratio!
            },
            'agent': 'Kenny',
            'timestamp': '2025-01-01T12:00:00'
        }
        
        print("  Kenny: Proposing risky trade...")
        result2 = asyncio.run(self.hrm.validate_action(kenny_action_risky, 'Kenny'))
        print(f"  HRM: Validated with Graveyard")
        print(f"  Result: {'✅ APPROVED' if result2['data']['approved'] else '❌ REJECTED'}")
        print(f"  Compliance: {result2['data']['compliance_score']:.1%}")
        print(f"  Violations: {len(result2['data']['violations'])}")
        
        if result2['data']['violations']:
            print("  🚫 Violations detected:")
            for v in result2['data']['violations']:
                print(f"    • {v['rule']}: {v['message']}")
        
        assert result2['data']['approved'] is False
        assert len(result2['data']['violations']) >= 3
        
        # Scenario 3: Kenny proposes file deletion
        print("\n📊 Scenario 3: Kenny proposes dangerous file operation")
        kenny_action_delete = {
            'action_type': 'file_operation',
            'parameters': {
                'operation': 'delete',
                'file_path': '/app/data/important.db',
                'destructive': True,
                'backup_exists': False
            },
            'agent': 'Kenny',
            'timestamp': '2025-01-01T12:00:00'
        }
        
        print("  Kenny: Proposing file deletion...")
        result3 = asyncio.run(self.hrm.validate_action(kenny_action_delete, 'Kenny'))
        print(f"  HRM: Validated with Graveyard")
        print(f"  Result: {'✅ APPROVED' if result3['data']['approved'] else '❌ REJECTED'}")
        print(f"  Compliance: {result3['data']['compliance_score']:.1%}")
        print(f"  Requires approval: {any(v['rule'] == 'require_hrm_approval' for v in result3['data']['violations'])}")
        
        print("\n" + "=" * 60)
        
        # Destructive operations should require HRM approval
        violation_rules = [v['rule'] for v in result3['data']['violations']]
        assert 'require_hrm_approval' in violation_rules


def run_integration_tests():
    """Run all HRM-Graveyard integration tests"""
    print("=" * 60)
    print("HRM + GRAVEYARD INTEGRATION TEST SUITE")
    print("=" * 60)
    print()
    
    test_instance = TestHRMGraveyardIntegration()
    test_methods = [
        'test_hrm_loads_graveyard_rules',
        'test_hrm_validate_action_api',
        'test_hrm_reject_unsafe_action',
        'test_hrm_tool_enforce_ethics_uses_graveyard',
        'test_hrm_parse_context_to_action',
        'test_graveyard_rules_summary',
        'test_validation_loop_simulation'
    ]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            # Setup
            test_instance.setup_method()
            
            # Run test
            method = getattr(test_instance, method_name)
            method()
            passed += 1
            
        except AssertionError as e:
            print(f"❌ {method_name}: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"⚠️  {method_name}: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {len(test_methods)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success rate: {(passed / len(test_methods) * 100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
    
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
