"""
Simplified HRM-Graveyard integration tests (no DB dependencies)
Tests the core validation logic without requiring full agent initialization
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from graveyard.ethics import validate_against_graveyard, get_rules


class TestHRMGraveyardLogic:
    """Test HRM integration logic with Graveyard (simplified)"""
    
    def test_graveyard_available(self):
        """Test that Graveyard can be imported and used"""
        rules = get_rules()
        assert len(rules) > 20
        assert 'max_position_size' in rules
        print("✅ Graveyard module accessible")
    
    def test_kenny_safe_action_approved(self):
        """Test that Kenny's safe action gets approved"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'SPY',
                'position_size_pct': 0.05,
                'stop_loss': 450,
                'leverage': 1.0,
                'risk_reward_ratio': 2.5
            },
            'agent': 'Kenny',
            'timestamp': '2025-01-01T12:00:00'
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        assert result['approved'] is True
        assert result['compliance_score'] >= 0.95
        assert len(result['violations']) == 0
        print("✅ Kenny's safe action approved by Graveyard")
    
    def test_kenny_risky_action_rejected(self):
        """Test that Kenny's risky action gets rejected"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'VOLATILE',
                'position_size_pct': 0.30,  # Too large!
                'stop_loss': None,  # Missing!
                'leverage': 4.0,  # Too high!
                'risk_reward_ratio': 0.5  # Too low!
            },
            'agent': 'Kenny',
            'timestamp': '2025-01-01T12:00:00'
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        assert result['approved'] is False
        assert len(result['violations']) >= 3
        assert result['compliance_score'] < 0.6
        
        # Check for specific violations
        violation_rules = [v['rule'] for v in result['violations']]
        assert 'max_position_size' in violation_rules
        assert 'require_stop_loss' in violation_rules
        assert 'max_leverage' in violation_rules
        
        print("✅ Kenny's risky action rejected by Graveyard")
    
    def test_validation_pipeline_simulation(self):
        """Simulate the full Kenny → HRM → Graveyard validation pipeline"""
        print("\n" + "=" * 70)
        print("VALIDATION PIPELINE SIMULATION")
        print("=" * 70)
        
        # Test Case 1: Conservative trade (should pass)
        print("\n📈 Test Case 1: Conservative Trade")
        print("-" * 70)
        
        conservative_trade = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'SPY',
                'position_size_pct': 0.03,  # Small 3%
                'stop_loss': 580,
                'take_profit': 600,
                'leverage': 1.0,  # No leverage
                'risk_reward_ratio': 3.0,  # Excellent
                'strategy': 'conservative_mean_reversion'
            },
            'agent': 'Kenny',
            'timestamp': '2025-01-01T10:00:00'
        }
        
        print("1. Kenny proposes: Conservative SPY trade (3% position, no leverage)")
        result1 = validate_against_graveyard(conservative_trade, 'Kenny')
        print(f"2. Graveyard validates: {len(result1['rules_checked'])} rules checked")
        print(f"3. HRM decision: {'✅ APPROVED' if result1['approved'] else '❌ REJECTED'}")
        print(f"   Compliance Score: {result1['compliance_score']:.1%}")
        print(f"   Violations: {len(result1['violations'])}")
        
        assert result1['approved'] is True
        print("   ✅ Conservative trade approved\n")
        
        # Test Case 2: Aggressive trade (should fail)
        print("📈 Test Case 2: Aggressive Trade")
        print("-" * 70)
        
        aggressive_trade = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'MEME',
                'position_size_pct': 0.25,  # 25% - too large!
                'stop_loss': None,  # No protection!
                'leverage': 3.0,  # 3x leverage - too high!
                'risk_reward_ratio': 0.8,  # Poor ratio
                'strategy': 'yolo_momentum'
            },
            'agent': 'Kenny',
            'timestamp': '2025-01-01T14:00:00'
        }
        
        print("1. Kenny proposes: Aggressive MEME trade (25% position, 3x leverage)")
        result2 = validate_against_graveyard(aggressive_trade, 'Kenny')
        print(f"2. Graveyard validates: {len(result2['rules_checked'])} rules checked")
        print(f"3. HRM decision: {'✅ APPROVED' if result2['approved'] else '❌ REJECTED'}")
        print(f"   Compliance Score: {result2['compliance_score']:.1%}")
        print(f"   Violations: {len(result2['violations'])}")
        
        if result2['violations']:
            print("\n   🚫 Violations Detected:")
            for v in result2['violations']:
                severity_emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
                emoji = severity_emoji.get(v['severity'], '⚪')
                print(f"      {emoji} [{v['severity']}] {v['rule']}")
                print(f"         {v['message']}")
        
        assert result2['approved'] is False
        assert len(result2['violations']) >= 3
        print("\n   ✅ Aggressive trade rejected\n")
        
        # Test Case 3: Dangerous file operation (should require approval)
        print("📁 Test Case 3: Dangerous File Operation")
        print("-" * 70)
        
        file_deletion = {
            'action_type': 'file_operation',
            'parameters': {
                'operation': 'delete',
                'file_path': '/app/data/critical_database.db',
                'destructive': True,
                'backup_exists': False
            },
            'agent': 'Kenny',
            'timestamp': '2025-01-01T16:00:00'
        }
        
        print("1. Kenny proposes: Delete critical database (no backup)")
        result3 = validate_against_graveyard(file_deletion, 'Kenny')
        print(f"2. Graveyard validates: {len(result3['rules_checked'])} rules checked")
        print(f"3. HRM decision: {'✅ APPROVED' if result3['approved'] else '❌ REJECTED'}")
        print(f"   Compliance Score: {result3['compliance_score']:.1%}")
        print(f"   Violations: {len(result3['violations'])}")
        
        if result3['violations']:
            print("\n   🚫 Violations Detected:")
            for v in result3['violations']:
                print(f"      • [{v['severity']}] {v['rule']}: {v['message']}")
        
        # Should require HRM approval
        violation_rules = [v['rule'] for v in result3['violations']]
        assert 'require_hrm_approval' in violation_rules
        print("\n   ✅ Dangerous operation flagged for HRM approval\n")
        
        # Test Case 4: Data privacy violation (should fail)
        print("🔒 Test Case 4: Data Privacy Violation")
        print("-" * 70)
        
        privacy_violation = {
            'action_type': 'data_handling',
            'parameters': {
                'operation': 'collect',
                'data_type': 'personal',
                'data_sensitivity': 'high',
                'user_consent': False,  # No consent!
                'encryption': False  # Not encrypted!
            },
            'agent': 'Joey',
            'timestamp': '2025-01-01T18:00:00'
        }
        
        print("1. Joey proposes: Collect personal data without consent")
        result4 = validate_against_graveyard(privacy_violation, 'Joey')
        print(f"2. Graveyard validates: {len(result4['rules_checked'])} rules checked")
        print(f"3. HRM decision: {'✅ APPROVED' if result4['approved'] else '❌ REJECTED'}")
        print(f"   Compliance Score: {result4['compliance_score']:.1%}")
        print(f"   Violations: {len(result4['violations'])}")
        
        if result4['violations']:
            print("\n   🚫 Violations Detected:")
            for v in result4['violations']:
                print(f"      • [{v['severity']}] {v['rule']}: {v['message']}")
        
        assert result4['approved'] is False
        print("\n   ✅ Privacy violation rejected\n")
        
        print("=" * 70)
        print("VALIDATION PIPELINE: ALL TESTS PASSED ✅")
        print("=" * 70)
    
    def test_no_ethics_drift(self):
        """Test that rules cannot be modified at runtime"""
        # Get rules
        rules_before = get_rules()
        original_max_pos = rules_before['max_position_size']
        
        # Try to modify (should not affect Graveyard)
        rules_before['max_position_size'] = 0.99
        
        # Get fresh copy
        rules_after = get_rules()
        
        # Should be unchanged (immutable)
        assert rules_after['max_position_size'] == original_max_pos
        assert rules_after['max_position_size'] == 0.10
        
        print("✅ Graveyard rules immutable - no ethics drift possible")
    
    def test_validation_consistency(self):
        """Test that same action gets same validation result"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'TEST',
                'position_size_pct': 0.05,
                'stop_loss': 100,
                'leverage': 1.0
            },
            'agent': 'Kenny',
            'timestamp': '2025-01-01T12:00:00'
        }
        
        # Validate 5 times
        results = [validate_against_graveyard(action, 'Kenny') for _ in range(5)]
        
        # All results should be identical
        for i in range(1, 5):
            assert results[i]['approved'] == results[0]['approved']
            assert results[i]['compliance_score'] == results[0]['compliance_score']
            assert len(results[i]['violations']) == len(results[0]['violations'])
        
        print("✅ Validation is consistent and deterministic")


def run_simple_tests():
    """Run simplified integration tests"""
    print("=" * 70)
    print("HRM + GRAVEYARD INTEGRATION (SIMPLIFIED)")
    print("=" * 70)
    print()
    
    test_instance = TestHRMGraveyardLogic()
    test_methods = [
        'test_graveyard_available',
        'test_kenny_safe_action_approved',
        'test_kenny_risky_action_rejected',
        'test_no_ethics_drift',
        'test_validation_consistency',
        'test_validation_pipeline_simulation'
    ]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            method = getattr(test_instance, method_name)
            method()
            passed += 1
        except AssertionError as e:
            print(f"❌ {method_name}: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"⚠️  {method_name}: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total tests: {len(test_methods)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success rate: {(passed / len(test_methods) * 100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED - GRAVEYARD FULLY INTEGRATED!")
    
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)
