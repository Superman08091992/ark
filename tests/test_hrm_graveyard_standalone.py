"""
Standalone HRM-Graveyard Integration Test
Tests HRM validation logic without requiring full database setup
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from graveyard.ethics import validate_against_graveyard, get_rules, get_rule


def test_graveyard_rules_loading():
    """Test that Graveyard rules can be loaded"""
    print("\n" + "="*70)
    print("TEST 1: Graveyard Rules Loading")
    print("="*70)
    
    rules = get_rules()
    print(f"✅ Loaded {len(rules)} immutable rules from Graveyard")
    
    # Check key rules
    key_rules = [
        ('no_insider_trading', True),
        ('no_market_manipulation', True),
        ('max_position_size', 0.10),
        ('max_daily_loss', 0.05),
        ('max_leverage', 2.0),
        ('require_stop_loss', True)
    ]
    
    for rule_name, expected_value in key_rules:
        actual_value = get_rule(rule_name)
        assert actual_value == expected_value, f"Rule {rule_name} mismatch: {actual_value} != {expected_value}"
        print(f"   ✅ {rule_name}: {actual_value}")
    
    print("\n✅ All key rules verified\n")


def test_kenny_action_validation():
    """Test validation of Kenny (executor) actions"""
    print("="*70)
    print("TEST 2: Kenny Action Validation")
    print("="*70)
    
    # Test 1: Valid trade
    print("\n1. Valid trade (should be approved)...")
    valid_trade = {
        'action_type': 'trade',
        'parameters': {
            'symbol': 'AAPL',
            'position_size_pct': 0.05,
            'stop_loss': 150.00,
            'leverage': 1.0,
            'risk_reward_ratio': 2.0
        }
    }
    
    result = validate_against_graveyard(valid_trade, 'Kenny')
    print(f"   Approved: {result['approved']}")
    print(f"   Compliance: {result['compliance_score']:.1%}")
    print(f"   Violations: {len(result['violations'])}")
    assert result['approved'], "Valid trade should be approved"
    print("   ✅ Valid trade correctly approved")
    
    # Test 2: Oversized position
    print("\n2. Oversized position (should be rejected)...")
    oversized_trade = {
        'action_type': 'trade',
        'parameters': {
            'symbol': 'TSLA',
            'position_size_pct': 0.15,  # EXCEEDS 10% limit
            'stop_loss': 200.00,
            'leverage': 1.0
        }
    }
    
    result = validate_against_graveyard(oversized_trade, 'Kenny')
    print(f"   Approved: {result['approved']}")
    print(f"   Violations: {len(result['violations'])}")
    assert not result['approved'], "Oversized position should be rejected"
    assert any(v['rule'] == 'max_position_size' for v in result['violations'])
    print("   ✅ Oversized position correctly rejected")
    
    # Test 3: Missing stop-loss
    print("\n3. Missing stop-loss (should be rejected)...")
    no_stoploss = {
        'action_type': 'trade',
        'parameters': {
            'symbol': 'BTC-USD',
            'position_size_pct': 0.08,
            'stop_loss': None,  # MISSING
            'leverage': 1.5
        }
    }
    
    result = validate_against_graveyard(no_stoploss, 'Kenny')
    print(f"   Approved: {result['approved']}")
    print(f"   Violations: {len(result['violations'])}")
    assert not result['approved'], "Trade without stop-loss should be rejected"
    assert any(v['rule'] == 'require_stop_loss' for v in result['violations'])
    print("   ✅ Missing stop-loss correctly flagged")
    
    # Test 4: Excessive leverage
    print("\n4. Excessive leverage (should be rejected)...")
    high_leverage = {
        'action_type': 'trade',
        'parameters': {
            'symbol': 'ETH-USD',
            'position_size_pct': 0.05,
            'stop_loss': 3000.00,
            'leverage': 5.0  # EXCEEDS 2x limit
        }
    }
    
    result = validate_against_graveyard(high_leverage, 'Kenny')
    print(f"   Approved: {result['approved']}")
    print(f"   Violations: {len(result['violations'])}")
    assert not result['approved'], "Excessive leverage should be rejected"
    assert any(v['rule'] == 'max_leverage' for v in result['violations'])
    print("   ✅ Excessive leverage correctly rejected")
    
    # Test 5: Market manipulation
    print("\n5. Market manipulation (should be CRITICAL violation)...")
    manipulation = {
        'action_type': 'trade',
        'parameters': {
            'symbol': 'GME',
            'position_size_pct': 0.03,
            'stop_loss': 50.00,
            'manipulative_intent': True,  # MANIPULATION FLAG
            'strategy': 'pump_and_dump'
        }
    }
    
    result = validate_against_graveyard(manipulation, 'Kenny')
    print(f"   Approved: {result['approved']}")
    print(f"   Violations: {len(result['violations'])}")
    assert not result['approved'], "Manipulation should be rejected"
    
    critical_violations = [v for v in result['violations'] if v['severity'] == 'CRITICAL']
    assert len(critical_violations) > 0, "Should have CRITICAL violations"
    print(f"   ✅ CRITICAL violations detected: {len(critical_violations)}")
    
    print("\n✅ All Kenny action validations passed\n")


def test_validation_pipeline():
    """Test full validation pipeline: Kyle → Joey → Kenny → HRM"""
    print("="*70)
    print("TEST 3: Full Validation Pipeline")
    print("="*70)
    
    print("\n📊 Simulating: Kyle → Joey → Kenny → HRM\n")
    
    # Step 1: Kyle detects signal
    print("1. Kyle detects market signal...")
    kyle_signal = {
        'action_type': 'market_signal',
        'parameters': {
            'symbol': 'AAPL',
            'signal_strength': 0.85,
            'signal_type': 'bullish',
            'confidence': 0.78
        }
    }
    kyle_result = validate_against_graveyard(kyle_signal, 'Kyle')
    print(f"   ✅ Kyle: Approved={kyle_result['approved']}, Compliance={kyle_result['compliance_score']:.1%}")
    assert kyle_result['approved'], "Kyle signal should be approved"
    
    # Step 2: Joey analyzes and proposes
    print("\n2. Joey proposes trade based on analysis...")
    joey_proposal = {
        'action_type': 'trade',
        'parameters': {
            'symbol': 'AAPL',
            'position_size_pct': 0.06,
            'stop_loss': 150.00,
            'take_profit': 165.00,
            'leverage': 1.0,
            'risk_reward_ratio': 2.5
        }
    }
    joey_result = validate_against_graveyard(joey_proposal, 'Joey')
    print(f"   ✅ Joey: Approved={joey_result['approved']}, Compliance={joey_result['compliance_score']:.1%}")
    assert joey_result['approved'], "Joey proposal should be approved"
    
    # Step 3: Kenny prepares execution
    print("\n3. Kenny prepares execution...")
    kenny_execution = {
        'action_type': 'trade',
        'parameters': {
            'symbol': 'AAPL',
            'action': 'buy',
            'position_size_pct': 0.06,
            'stop_loss': 150.00,
            'take_profit': 165.00,
            'leverage': 1.0,
            'hrm_validated': True  # Mark as HRM pre-approved
        }
    }
    kenny_result = validate_against_graveyard(kenny_execution, 'Kenny')
    print(f"   ✅ Kenny: Approved={kenny_result['approved']}, Compliance={kenny_result['compliance_score']:.1%}")
    assert kenny_result['approved'], "Kenny execution should be approved"
    
    # Step 4: HRM final validation
    print("\n4. HRM performs final validation...")
    hrm_result = validate_against_graveyard(kenny_execution, 'HRM')
    print(f"   ✅ HRM: Approved={hrm_result['approved']}, Compliance={hrm_result['compliance_score']:.1%}")
    assert hrm_result['approved'], "HRM should approve"
    
    print("\n✅ FULL PIPELINE APPROVED - Trade can execute")
    
    # Test rejection scenario
    print("\n" + "-"*70)
    print("Testing rejection scenario...")
    print("-"*70)
    
    print("\n1. Joey proposes risky trade...")
    risky_proposal = {
        'action_type': 'trade',
        'parameters': {
            'symbol': 'GME',
            'position_size_pct': 0.15,  # EXCEEDS limit
            'stop_loss': None,          # MISSING
            'leverage': 3.0             # TOO HIGH
        }
    }
    risky_result = validate_against_graveyard(risky_proposal, 'Joey')
    print(f"   ❌ Risky proposal: Approved={risky_result['approved']}")
    print(f"   ⚠️  Violations: {len(risky_result['violations'])}")
    
    for v in risky_result['violations']:
        print(f"      • [{v['severity']}] {v['rule']}: {v['message']}")
    
    assert not risky_result['approved'], "Risky trade should be rejected"
    assert len(risky_result['violations']) >= 2, "Should have multiple violations"
    
    print("\n✅ HRM CORRECTLY BLOCKED RISKY TRADE\n")


def test_immutability():
    """Test that Graveyard rules are truly immutable"""
    print("="*70)
    print("TEST 4: Graveyard Immutability")
    print("="*70)
    
    print("\n1. Loading original rules...")
    original_rules = get_rules()
    original_max_position = original_rules['max_position_size']
    print(f"   Original max_position_size: {original_max_position:.1%}")
    
    print("\n2. Attempting to modify returned copy...")
    original_rules['max_position_size'] = 0.50  # Try to change to 50%
    print(f"   Modified copy to: {original_rules['max_position_size']:.1%}")
    
    print("\n3. Re-loading rules from Graveyard...")
    fresh_rules = get_rules()
    fresh_max_position = fresh_rules['max_position_size']
    print(f"   Fresh max_position_size: {fresh_max_position:.1%}")
    
    assert fresh_max_position == 0.10, "Graveyard should be immutable"
    assert fresh_max_position != 0.50, "Modification should not affect Graveyard"
    
    print("\n✅ Graveyard immutability verified - rules cannot be modified\n")


def test_performance():
    """Test validation performance"""
    print("="*70)
    print("TEST 5: Validation Performance")
    print("="*70)
    
    import time
    
    action = {
        'action_type': 'trade',
        'parameters': {
            'symbol': 'AAPL',
            'position_size_pct': 0.05,
            'stop_loss': 150.00,
            'leverage': 1.0
        }
    }
    
    iterations = 1000
    print(f"\nRunning {iterations} validations...")
    
    start = time.time()
    for i in range(iterations):
        result = validate_against_graveyard(action, f'Agent{i % 6}')
    elapsed = time.time() - start
    
    avg_time = (elapsed / iterations) * 1000  # Convert to ms
    throughput = iterations / elapsed
    
    print(f"   ✅ Total time: {elapsed:.3f}s")
    print(f"   ✅ Average: {avg_time:.3f}ms per validation")
    print(f"   ✅ Throughput: {throughput:.0f} validations/second")
    
    # Performance targets
    assert avg_time < 10.0, f"Validation too slow: {avg_time:.3f}ms (target: <10ms)"
    assert throughput > 100, f"Throughput too low: {throughput:.0f}/s (target: >100/s)"
    
    print("\n✅ Performance targets met (< 10ms per validation)\n")


def run_all_tests():
    """Run all standalone tests"""
    
    print("\n" + "="*70)
    print("ARK GRAVEYARD-HRM INTEGRATION TEST SUITE")
    print("Standalone version (no database required)")
    print("="*70 + "\n")
    
    tests = [
        ("Graveyard Rules Loading", test_graveyard_rules_loading),
        ("Kenny Action Validation", test_kenny_action_validation),
        ("Validation Pipeline", test_validation_pipeline),
        ("Graveyard Immutability", test_immutability),
        ("Validation Performance", test_performance)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ TEST FAILED: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("TEST SUITE SUMMARY")
    print("="*70)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print("="*70 + "\n")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! 🎉\n")
        print("Graveyard Integration Status:")
        print("  ✅ Immutable ethics core functional")
        print("  ✅ All validation rules enforced")
        print("  ✅ Kenny actions properly validated")
        print("  ✅ Full pipeline (Kyle→Joey→Kenny→HRM) working")
        print("  ✅ Performance targets met (<10ms)")
        print("  ✅ Immutability guaranteed")
        print("\n✅ Ready for production deployment\n")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
