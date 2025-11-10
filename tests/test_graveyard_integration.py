"""
Unit Tests for Graveyard Integration with HRM
Tests immutability, validation, and integration with agent actions
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import json
from datetime import datetime
from graveyard.ethics import (
    validate_against_graveyard,
    get_rules,
    get_categories,
    get_rule,
    IMMUTABLE_RULES,
    ETHICAL_CATEGORIES
)


class TestGraveyardCore(unittest.TestCase):
    """Test core Graveyard functionality"""
    
    def test_graveyard_immutability(self):
        """Test that Graveyard rules cannot be modified"""
        rules = get_rules()
        original_count = len(rules)
        
        # Attempt to modify returned copy (should not affect original)
        rules['test_rule'] = 'malicious_value'
        
        # Get fresh copy
        fresh_rules = get_rules()
        
        self.assertEqual(len(fresh_rules), original_count)
        self.assertNotIn('test_rule', fresh_rules)
        print("✅ Graveyard immutability: Rules cannot be modified via get_rules()")
    
    def test_ethical_categories_complete(self):
        """Test that all expected categories exist"""
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
            self.assertIn(category, categories)
            self.assertIsInstance(categories[category], list)
            self.assertGreater(len(categories[category]), 0)
        
        print(f"✅ Ethical categories: All {len(expected_categories)} categories present")
    
    def test_rule_retrieval(self):
        """Test individual rule retrieval"""
        # Test key rules
        self.assertTrue(get_rule('no_insider_trading'))
        self.assertTrue(get_rule('no_market_manipulation'))
        self.assertEqual(get_rule('max_position_size'), 0.10)
        self.assertEqual(get_rule('max_daily_loss'), 0.05)
        self.assertEqual(get_rule('max_leverage'), 2.0)
        
        # Test non-existent rule
        self.assertIsNone(get_rule('nonexistent_rule'))
        
        print("✅ Rule retrieval: All key rules accessible")


class TestGraveyardValidation(unittest.TestCase):
    """Test Graveyard validation logic"""
    
    def test_valid_trade_action(self):
        """Test that valid trades are approved"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'AAPL',
                'position_size_pct': 0.05,  # 5% - within 10% limit
                'stop_loss': 150.00,
                'leverage': 1.0,
                'risk_reward_ratio': 2.0
            }
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        self.assertTrue(result['approved'])
        self.assertEqual(len(result['violations']), 0)
        self.assertGreater(result['compliance_score'], 0.9)
        self.assertEqual(result['agent'], 'Kenny')
        
        print(f"✅ Valid trade: Approved with {result['compliance_score']:.1%} compliance")
    
    def test_oversized_position_violation(self):
        """Test that oversized positions are rejected"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'TSLA',
                'position_size_pct': 0.15,  # 15% - EXCEEDS 10% limit
                'stop_loss': 200.00,
                'leverage': 1.0
            }
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        self.assertFalse(result['approved'])
        self.assertGreater(len(result['violations']), 0)
        
        # Check for position size violation
        violation_rules = [v['rule'] for v in result['violations']]
        self.assertIn('max_position_size', violation_rules)
        
        # Find the specific violation
        pos_violation = next(v for v in result['violations'] if v['rule'] == 'max_position_size')
        self.assertIn('HIGH', pos_violation['severity'])
        
        print(f"✅ Oversized position: Correctly rejected ({len(result['violations'])} violations)")
    
    def test_missing_stop_loss_violation(self):
        """Test that trades without stop-loss are flagged"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'BTC-USD',
                'position_size_pct': 0.08,
                'stop_loss': None,  # MISSING STOP-LOSS
                'leverage': 1.5
            }
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        self.assertFalse(result['approved'])
        
        violation_rules = [v['rule'] for v in result['violations']]
        self.assertIn('require_stop_loss', violation_rules)
        
        print(f"✅ Missing stop-loss: Correctly flagged")
    
    def test_excessive_leverage_violation(self):
        """Test that excessive leverage is rejected"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'ETH-USD',
                'position_size_pct': 0.05,
                'stop_loss': 3000.00,
                'leverage': 5.0  # EXCEEDS 2x limit
            }
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        self.assertFalse(result['approved'])
        
        violation_rules = [v['rule'] for v in result['violations']]
        self.assertIn('max_leverage', violation_rules)
        
        print(f"✅ Excessive leverage: Correctly rejected")
    
    def test_manipulative_intent_violation(self):
        """Test that market manipulation is detected"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'GME',
                'position_size_pct': 0.03,
                'stop_loss': 50.00,
                'manipulative_intent': True,  # MANIPULATION FLAG
                'strategy': 'pump_and_dump'
            }
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        self.assertFalse(result['approved'])
        
        violation_rules = [v['rule'] for v in result['violations']]
        self.assertIn('no_market_manipulation', violation_rules)
        
        # Should be CRITICAL severity
        manip_violation = next(v for v in result['violations'] if v['rule'] == 'no_market_manipulation')
        self.assertEqual(manip_violation['severity'], 'CRITICAL')
        
        print(f"✅ Market manipulation: CRITICAL violation detected")
    
    def test_multiple_violations(self):
        """Test action with multiple violations"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'SPY',
                'position_size_pct': 0.20,  # EXCEEDS limit
                'stop_loss': None,          # MISSING
                'leverage': 3.0,            # EXCEEDS limit
                'manipulative_intent': True # MANIPULATION
            }
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        self.assertFalse(result['approved'])
        self.assertGreaterEqual(len(result['violations']), 3)
        self.assertLess(result['compliance_score'], 0.5)
        
        print(f"✅ Multiple violations: {len(result['violations'])} violations detected, compliance={result['compliance_score']:.1%}")
    
    def test_data_privacy_validation(self):
        """Test data privacy rule enforcement"""
        action = {
            'action_type': 'data_handling',
            'parameters': {
                'operation': 'collect_user_data',
                'data_sensitivity': 'high',
                'user_consent': False,  # NO CONSENT
                'encryption': False
            }
        }
        
        result = validate_against_graveyard(action, 'Kyle')
        
        self.assertFalse(result['approved'])
        
        violation_rules = [v['rule'] for v in result['violations']]
        # Should flag privacy violations
        self.assertTrue(
            any('consent' in rule or 'privacy' in rule for rule in violation_rules)
        )
        
        print(f"✅ Data privacy: Privacy violations detected")
    
    def test_compliance_score_calculation(self):
        """Test compliance score is calculated correctly"""
        # Perfect compliance
        perfect_action = {
            'action_type': 'general',
            'parameters': {'description': 'routine check'}
        }
        perfect_result = validate_against_graveyard(perfect_action, 'HRM')
        self.assertGreaterEqual(perfect_result['compliance_score'], 0.9)
        
        # Poor compliance
        bad_action = {
            'action_type': 'trade',
            'parameters': {
                'position_size_pct': 0.25,  # Way over
                'stop_loss': None,
                'leverage': 10.0,
                'manipulative_intent': True
            }
        }
        bad_result = validate_against_graveyard(bad_action, 'Kenny')
        self.assertLess(bad_result['compliance_score'], 0.5)
        
        print(f"✅ Compliance scoring: Perfect={perfect_result['compliance_score']:.1%}, Poor={bad_result['compliance_score']:.1%}")


class TestKennyActionValidation(unittest.TestCase):
    """Test validation of Kenny (executor) actions"""
    
    def test_kenny_safe_file_operation(self):
        """Test that safe file operations are approved"""
        action = {
            'action_type': 'file_operation',
            'parameters': {
                'operation': 'create',
                'file_path': '/app/files/report.txt',
                'description': 'Create analysis report'
            }
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        self.assertTrue(result['approved'])
        print(f"✅ Kenny safe file operation: Approved")
    
    def test_kenny_dangerous_deletion(self):
        """Test that dangerous deletions require approval"""
        action = {
            'action_type': 'file_operation',
            'parameters': {
                'operation': 'delete',
                'file_path': '/app/critical_data.db',
                'hrm_approved': False  # NO APPROVAL
            }
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        # Should require HRM approval
        violation_rules = [v['rule'] for v in result['violations']]
        self.assertIn('require_hrm_approval', violation_rules)
        
        print(f"✅ Kenny dangerous deletion: HRM approval required")
    
    def test_kenny_trade_execution(self):
        """Test Kenny executing a trade action"""
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'AAPL',
                'action': 'buy',
                'position_size_pct': 0.07,
                'stop_loss': 150.00,
                'take_profit': 165.00,
                'leverage': 1.0,
                'risk_reward_ratio': 2.14
            }
        }
        
        result = validate_against_graveyard(action, 'Kenny')
        
        self.assertTrue(result['approved'])
        self.assertGreater(result['compliance_score'], 0.9)
        
        print(f"✅ Kenny trade execution: Approved with compliance={result['compliance_score']:.1%}")


class TestIntegrationScenarios(unittest.TestCase):
    """Test realistic integration scenarios"""
    
    def test_full_validation_pipeline(self):
        """Test complete validation pipeline from Kyle → Joey → Kenny → HRM"""
        
        # 1. Kyle detects signal
        kyle_signal = {
            'action_type': 'market_signal',
            'parameters': {
                'symbol': 'TSLA',
                'signal_strength': 0.85,
                'signal_type': 'bullish',
                'confidence': 0.78
            }
        }
        kyle_result = validate_against_graveyard(kyle_signal, 'Kyle')
        self.assertTrue(kyle_result['approved'])
        
        # 2. Joey analyzes and proposes trade
        joey_analysis = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'TSLA',
                'position_size_pct': 0.06,
                'stop_loss': 220.00,
                'take_profit': 250.00,
                'leverage': 1.0,
                'risk_reward_ratio': 2.5,
                'analysis_confidence': 0.78
            }
        }
        joey_result = validate_against_graveyard(joey_analysis, 'Joey')
        self.assertTrue(joey_result['approved'])
        
        # 3. Kenny prepares execution
        kenny_execution = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'TSLA',
                'action': 'buy',
                'position_size_pct': 0.06,
                'stop_loss': 220.00,
                'take_profit': 250.00,
                'leverage': 1.0,
                'hrm_approved': True  # HRM pre-approved
            }
        }
        kenny_result = validate_against_graveyard(kenny_execution, 'Kenny')
        self.assertTrue(kenny_result['approved'])
        
        # 4. HRM validates final action
        hrm_validation = validate_against_graveyard(kenny_execution, 'HRM')
        self.assertTrue(hrm_validation['approved'])
        
        print(f"✅ Full pipeline: Kyle → Joey → Kenny → HRM all approved")
    
    def test_hrm_blocks_unethical_action(self):
        """Test HRM blocking an unethical action from Kenny"""
        
        # Kenny proposes risky action
        risky_action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'GME',
                'position_size_pct': 0.15,  # Over limit
                'stop_loss': None,          # No protection
                'leverage': 3.0,            # Too high
                'urgency': 'immediate'
            }
        }
        
        # HRM validation
        hrm_result = validate_against_graveyard(risky_action, 'HRM')
        
        self.assertFalse(hrm_result['approved'])
        self.assertGreaterEqual(len(hrm_result['violations']), 2)
        
        print(f"✅ HRM blocks risky action: {len(hrm_result['violations'])} violations found")
    
    def test_emergency_halt_scenario(self):
        """Test emergency halt trigger"""
        
        # Critical violation that should trigger emergency halt
        critical_action = {
            'action_type': 'trade',
            'parameters': {
                'manipulative_intent': True,
                'insider_information': True,
                'position_size_pct': 0.50,  # Massive position
                'leverage': 10.0
            }
        }
        
        result = validate_against_graveyard(critical_action, 'Kenny')
        
        self.assertFalse(result['approved'])
        
        # Should have CRITICAL violations
        critical_violations = [v for v in result['violations'] if v['severity'] == 'CRITICAL']
        self.assertGreater(len(critical_violations), 0)
        
        print(f"✅ Emergency halt: {len(critical_violations)} CRITICAL violations detected")


class TestGraveyardPerformance(unittest.TestCase):
    """Test Graveyard performance and reliability"""
    
    def test_validation_speed(self):
        """Test that validation is fast enough for real-time use"""
        import time
        
        action = {
            'action_type': 'trade',
            'parameters': {
                'symbol': 'AAPL',
                'position_size_pct': 0.05,
                'stop_loss': 150.00
            }
        }
        
        iterations = 100
        start = time.time()
        
        for _ in range(iterations):
            result = validate_against_graveyard(action, 'TestAgent')
        
        elapsed = time.time() - start
        avg_time = elapsed / iterations
        
        # Should complete in under 10ms per validation
        self.assertLess(avg_time, 0.01)
        
        print(f"✅ Performance: {iterations} validations in {elapsed:.3f}s (avg {avg_time*1000:.2f}ms)")
    
    def test_concurrent_validations(self):
        """Test multiple concurrent validations"""
        actions = [
            {
                'action_type': 'trade', 
                'parameters': {
                    'symbol': f'SYM{i}', 
                    'position_size_pct': 0.05,
                    'stop_loss': 100.00,  # Include stop-loss
                    'leverage': 1.0
                }
            }
            for i in range(10)
        ]
        
        results = []
        for i, action in enumerate(actions):
            result = validate_against_graveyard(action, f'Agent{i}')
            results.append(result)
        
        # All should succeed
        for result in results:
            self.assertTrue(result['approved'])
        
        print(f"✅ Concurrent validations: {len(results)} successful")


def run_graveyard_integration_tests():
    """Run all Graveyard integration tests"""
    
    print("\n" + "="*70)
    print("ARK GRAVEYARD INTEGRATION TEST SUITE")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGraveyardCore))
    suite.addTests(loader.loadTestsFromTestCase(TestGraveyardValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestKennyActionValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestGraveyardPerformance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_graveyard_integration_tests()
    sys.exit(0 if success else 1)
