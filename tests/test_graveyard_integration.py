"""
Unit tests for Graveyard integration with HRM
Tests immutable ethics enforcement and action validation
"""

import pytest
import sys
import os
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from graveyard.ethics import (
    validate_against_graveyard,
    get_rules,
    get_categories,
    get_rule,
    IMMUTABLE_RULES,
    ETHICAL_CATEGORIES
)


class TestGraveyardCore:
    """Test Graveyard core functionality"""
    
    def test_rules_immutable(self):
        """Test that rules are read-only copies"""
        rules = get_rules()
        original_value = rules['max_position_size']
        
        # Try to modify (should not affect Graveyard)
        rules['max_position_size'] = 0.99
        
        # Get fresh copy
        fresh_rules = get_rules()
        assert fresh_rules['max_position_size'] == original_value
        assert fresh_rules['max_position_size'] != 0.99
    
    def test_all_rules_present(self):
        """Test that all expected rules exist"""
        rules = get_rules()
        
        required_rules = [
            'no_insider_trading',
            'no_market_manipulation',
            'max_position_size',
            'max_daily_loss',
            'require_stop_loss',
            'require_hrm_approval',
            'protect_user_data',
            'immutable_graveyard'
        ]
        
        for rule in required_rules:
            assert rule in rules, f"Rule '{rule}' missing from Graveyard"
    
    def test_categories_structure(self):
        """Test that all ethical categories are defined"""
        categories = get_categories()
        
        expected_categories = [
            'trading',
            'risk_management',
            'governance',
            'privacy',
            'integrity',
            'autonomy'
        ]
        
        for category in expected_categories:
            assert category in categories, f"Category '{category}' missing"
            assert isinstance(categories[category], list)
            assert len(categories[category]) > 0
    
    def test_get_specific_rule(self):
        """Test retrieving specific rules"""
        max_pos = get_rule('max_position_size')
        assert max_pos == 0.10
        
        max_loss = get_rule('max_daily_loss')
        assert max_loss == 0.05
        
        max_lev = get_rule('max_leverage')
        assert max_lev == 2.0
        
        no_insider = get_rule('no_insider_trading')
        assert no_insider is True


class TestGraveyardValidation:
    """Test action validation against Graveyard rules"""
    
    def test_valid_trade_action(self):
        """Test that a compliant trade action is approved"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'SPY',
                'position_size_pct': 0.05,  # Within 10% limit
                'stop_loss': 450,
                'take_profit': 470,
                'leverage': 1.5,  # Within 2x limit
                'risk_reward_ratio': 2.0
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        assert result['approved'] is True
        assert result['compliance_score'] >= 0.95
        assert len(result['violations']) == 0
        assert len(result['rules_checked']) > 0
    
    def test_excessive_position_size(self):
        """Test that excessive position size is rejected"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'TSLA',
                'position_size_pct': 0.25,  # Exceeds 10% limit!
                'stop_loss': 200,
                'leverage': 1.0
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        assert result['approved'] is False
        assert result['compliance_score'] < 1.0
        
        # Check for specific violation
        violation_rules = [v['rule'] for v in result['violations']]
        assert 'max_position_size' in violation_rules
        
        # Check severity
        pos_violation = next(v for v in result['violations'] if v['rule'] == 'max_position_size')
        assert pos_violation['severity'] in ['HIGH', 'CRITICAL']
    
    def test_missing_stop_loss(self):
        """Test that missing stop-loss triggers violation"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'BTC-USD',
                'position_size_pct': 0.08,
                'stop_loss': None,  # Missing!
                'leverage': 1.0
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        assert result['approved'] is False
        
        violation_rules = [v['rule'] for v in result['violations']]
        assert 'require_stop_loss' in violation_rules
    
    def test_excessive_leverage(self):
        """Test that excessive leverage is rejected"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'ETH-USD',
                'position_size_pct': 0.05,
                'stop_loss': 3000,
                'leverage': 5.0  # Exceeds 2x limit!
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        assert result['approved'] is False
        
        violation_rules = [v['rule'] for v in result['violations']]
        assert 'max_leverage' in violation_rules
    
    def test_market_manipulation_detected(self):
        """Test that market manipulation intent is flagged"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'MEME',
                'position_size_pct': 0.05,
                'stop_loss': 10,
                'manipulative_intent': True  # Red flag!
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        assert result['approved'] is False
        
        violation_rules = [v['rule'] for v in result['violations']]
        assert 'no_market_manipulation' in violation_rules
        
        # Should be critical severity
        manip_violation = next(v for v in result['violations'] if v['rule'] == 'no_market_manipulation')
        assert manip_violation['severity'] == 'CRITICAL'
    
    def test_multiple_violations(self):
        """Test action with multiple rule violations"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'YOLO',
                'position_size_pct': 0.50,  # Way too high!
                'stop_loss': None,  # Missing!
                'leverage': 10.0,  # Way too high!
                'risk_reward_ratio': 0.5  # Too low!
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        assert result['approved'] is False
        assert len(result['violations']) >= 3
        assert result['compliance_score'] < 0.5
    
    def test_data_privacy_violation(self):
        """Test that data privacy violations are detected"""
        action = {
            'action_type': 'data_handling',
            'parameters': {
                'operation': 'share',
                'data_type': 'personal',
                'user_consent': False  # No consent!
            },
            'agent': 'Joey',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Joey')
        
        assert result['approved'] is False
        
        violation_rules = [v['rule'] for v in result['violations']]
        assert 'require_consent' in violation_rules or 'protect_user_data' in violation_rules
    
    def test_hrm_approval_requirement(self):
        """Test that HIGH-RISK actions require HRM approval"""
        # Low-risk action (small position, has stop-loss, no leverage) - should NOT require approval
        low_risk_action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'SPY',
                'position_size_pct': 0.05,  # Small position
                'stop_loss': 450,  # Has protection
                'leverage': 1.0,  # No leverage
                'hrm_approved': False
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result_low_risk = validate_against_graveyard(low_risk_action, 'Kenny')
        
        # Low-risk actions don't require HRM approval
        violation_rules_low = [v['rule'] for v in result_low_risk['violations']]
        assert 'require_hrm_approval' not in violation_rules_low, "Low-risk action should not require HRM approval"
        
        # High-risk action (large position, no stop-loss, leveraged) - SHOULD require approval
        high_risk_action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'VOLATILE',
                'position_size_pct': 0.09,  # Large position (>8%)
                'stop_loss': None,  # No protection!
                'leverage': 2.0,  # Leveraged
                'hrm_approved': False  # Not approved!
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result_high_risk = validate_against_graveyard(high_risk_action, 'Kenny')
        
        # High-risk actions DO require HRM approval
        violation_rules_high = [v['rule'] for v in result_high_risk['violations']]
        assert 'require_hrm_approval' in violation_rules_high, "High-risk action must require HRM approval"


class TestGraveyardEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_exact_limit_position_size(self):
        """Test position size exactly at limit (should pass)"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'position_size_pct': 0.10,  # Exactly at 10% limit
                'stop_loss': 100,
                'leverage': 1.0
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        # At exact limit might trigger warning but should not violate
        pos_violations = [v for v in result['violations'] if v['rule'] == 'max_position_size']
        # Either no violation or low severity warning
        if pos_violations:
            assert pos_violations[0]['severity'] in ['LOW', 'MEDIUM']
    
    def test_empty_action(self):
        """Test validation with minimal action data"""
        action = {
            'action_type': 'general',
            'parameters': {},
            'agent': 'Unknown',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Unknown')
        
        # Should process without crashing
        assert 'approved' in result
        assert 'compliance_score' in result
        assert 'violations' in result
    
    def test_unknown_action_type(self):
        """Test handling of unknown action types"""
        action = {
            'action_type': 'unknown_experimental',
            'parameters': {
                'something': 'random'
            },
            'agent': 'Test',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Test')
        
        # Should handle gracefully, may flag as requiring approval
        assert 'approved' in result
        assert isinstance(result['violations'], list)
    
    def test_validation_response_structure(self):
        """Test that validation response has required fields"""
        action = {
            'action_type': 'trade',
            'parameters': {'symbol': 'TEST'},
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        # Check all required fields present
        required_fields = [
            'approved',
            'violations',
            'warnings',
            'rules_checked',
            'compliance_score',
            'timestamp',
            'agent'
        ]
        
        for field in required_fields:
            assert field in result, f"Required field '{field}' missing from validation result"
        
        # Check types
        assert isinstance(result['approved'], bool)
        assert isinstance(result['violations'], list)
        assert isinstance(result['warnings'], list)
        assert isinstance(result['rules_checked'], list)
        assert isinstance(result['compliance_score'], float)
        assert 0.0 <= result['compliance_score'] <= 1.0


class TestKennyMockActions:
    """Test mock actions from Kenny (Action agent)"""
    
    def test_kenny_valid_file_read(self):
        """Test that Kenny reading files is allowed"""
        action = {
            'action_type': 'file_operation',
            'parameters': {
                'operation': 'read',
                'file_path': '/app/files/data.json',
                'destructive': False
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        # Read operations should generally be safe
        assert result['compliance_score'] > 0.8
    
    def test_kenny_valid_file_write(self):
        """Test that Kenny writing files is allowed with constraints"""
        action = {
            'action_type': 'file_operation',
            'parameters': {
                'operation': 'write',
                'file_path': '/app/files/output.json',
                'destructive': False,
                'backup_exists': True
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        # Write with backup should be acceptable
        assert result['compliance_score'] > 0.7
    
    def test_kenny_dangerous_delete(self):
        """Test that Kenny deleting files triggers review"""
        action = {
            'action_type': 'file_operation',
            'parameters': {
                'operation': 'delete',
                'file_path': '/app/files/important.db',
                'destructive': True,
                'backup_exists': False  # No backup!
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        # Destructive operations should require approval
        violation_rules = [v['rule'] for v in result['violations']]
        assert 'require_hrm_approval' in violation_rules
    
    def test_kenny_risky_trade_rejected(self):
        """Test that Kenny's risky trade proposal is rejected"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'VOLATILE_PENNY_STOCK',
                'position_size_pct': 0.30,  # Too large!
                'stop_loss': None,  # No protection!
                'leverage': 3.0,  # Too high!
                'risk_reward_ratio': 0.8,  # Too low!
                'market_conditions': 'highly_volatile'
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        assert result['approved'] is False
        assert len(result['violations']) >= 3
        assert result['compliance_score'] < 0.5
        
        # Check for specific violations
        violation_rules = [v['rule'] for v in result['violations']]
        assert 'max_position_size' in violation_rules
        assert 'require_stop_loss' in violation_rules
        assert 'max_leverage' in violation_rules
    
    def test_kenny_conservative_trade_approved(self):
        """Test that Kenny's conservative trade is approved"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'SPY',
                'position_size_pct': 0.03,  # Conservative 3%
                'stop_loss': 580,
                'take_profit': 600,
                'leverage': 1.0,  # No leverage
                'risk_reward_ratio': 3.0,  # Excellent R:R
                'market_conditions': 'stable',
                'strategy': 'conservative_mean_reversion'
            },
            'agent': 'Kenny',
            'timestamp': datetime.now().isoformat()
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        assert result['approved'] is True
        assert result['compliance_score'] >= 0.95
        assert len(result['violations']) == 0


class TestGraveyardFileImmutability:
    """Test that Graveyard ethics.py file is immutable"""
    
    def test_file_permissions_readonly(self):
        """Test that ethics.py has read-only permissions"""
        import stat
        
        ethics_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'graveyard',
            'ethics.py'
        )
        
        if os.path.exists(ethics_path):
            mode = os.stat(ethics_path).st_mode
            
            # Check that write permissions are not set
            owner_write = bool(mode & stat.S_IWUSR)
            group_write = bool(mode & stat.S_IWGRP)
            other_write = bool(mode & stat.S_IWOTH)
            
            # File should be read-only (444 or similar)
            assert not (owner_write or group_write or other_write), \
                "ethics.py should be read-only (chmod 444)"
        else:
            pytest.skip("ethics.py file not found in expected location")


def run_all_tests():
    """Run all Graveyard integration tests"""
    print("=" * 60)
    print("GRAVEYARD INTEGRATION TEST SUITE")
    print("=" * 60)
    print()
    
    test_classes = [
        TestGraveyardCore,
        TestGraveyardValidation,
        TestGraveyardEdgeCases,
        TestKennyMockActions,
        TestGraveyardFileImmutability
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n📋 Running {test_class.__name__}...")
        print("-" * 60)
        
        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            method = getattr(test_instance, method_name)
            
            try:
                method()
                print(f"  ✅ {method_name}")
                passed_tests += 1
            except AssertionError as e:
                print(f"  ❌ {method_name}: {str(e)}")
                failed_tests.append((test_class.__name__, method_name, str(e)))
            except Exception as e:
                print(f"  ⚠️  {method_name}: {str(e)}")
                failed_tests.append((test_class.__name__, method_name, f"Exception: {str(e)}"))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {len(failed_tests)} ❌")
    print(f"Success rate: {(passed_tests / total_tests * 100):.1f}%")
    
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for class_name, method_name, error in failed_tests:
            print(f"  • {class_name}.{method_name}")
            print(f"    {error}")
    else:
        print("\n🎉 ALL TESTS PASSED!")
    
    print("=" * 60)
    
    return len(failed_tests) == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
