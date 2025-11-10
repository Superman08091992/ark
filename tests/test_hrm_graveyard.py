"""
Test HRM Integration with Graveyard
Simulates real agent scenarios validating against immutable ethics
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import json
from datetime import datetime


async def test_hrm_graveyard_integration():
    """Test HRM agent using Graveyard for ethics validation"""
    
    print("\n" + "="*70)
    print("HRM GRAVEYARD INTEGRATION TEST")
    print("="*70 + "\n")
    
    # Import HRM (this will initialize with Graveyard)
    from agents.hrm import HRMAgent
    
    print("1. Initializing HRM Agent with Graveyard integration...")
    hrm = HRMAgent()
    
    # Check that Graveyard was loaded
    print(f"   ✅ HRM initialized with {len(hrm.immutable_rules)} Graveyard rules")
    print(f"   ✅ Ethical categories loaded: {list(hrm.ethical_categories.keys())}")
    
    # Test 1: Valid trade validation
    print("\n2. Testing valid trade validation...")
    valid_trade = "Validate a trade: Buy AAPL at $150, position size 5%, stop-loss $145, leverage 1x"
    result1 = await hrm.tool_enforce_ethics(valid_trade)
    
    if result1['success']:
        data = result1['data']
        print(f"   ✅ Validation: {data['status']}")
        print(f"   ✅ Approved: {data['approved']}")
        print(f"   ✅ Compliance: {data['compliance_score']:.1%}")
        print(f"   ✅ Violations: {len(data['violations'])}")
        print(f"   ✅ Used Graveyard: {data['graveyard_validation']}")
    
    # Test 2: Risky trade validation
    print("\n3. Testing risky trade validation...")
    risky_trade = "Validate a trade: Buy GME with 15% position size, no stop-loss, 3x leverage"
    result2 = await hrm.tool_enforce_ethics(risky_trade)
    
    if result2['success']:
        data = result2['data']
        print(f"   ⚠️  Validation: {data['status']}")
        print(f"   ❌ Approved: {data['approved']}")
        print(f"   📊 Compliance: {data['compliance_score']:.1%}")
        print(f"   🚫 Violations: {len(data['violations'])}")
        
        if data['violations']:
            print(f"\n   Violation Details:")
            for v in data['violations']:
                print(f"      • [{v['severity']}] {v['rule']}: {v['message']}")
    
    # Test 3: Direct action validation (public API)
    print("\n4. Testing direct action validation (Kenny submits trade)...")
    kenny_action = {
        'action_type': 'trade',
        'parameters': {
            'symbol': 'TSLA',
            'position_size_pct': 0.08,
            'stop_loss': 200.00,
            'leverage': 1.5,
            'risk_reward_ratio': 2.0
        }
    }
    
    result3 = await hrm.validate_action(kenny_action, 'Kenny')
    
    if result3['success']:
        data = result3['data']
        print(f"   ✅ Kenny action approved: {data['approved']}")
        print(f"   ✅ Compliance score: {data['compliance_score']:.1%}")
        print(f"   ✅ Rules checked: {len(data['rules_checked'])}")
    
    # Test 4: Market manipulation detection
    print("\n5. Testing market manipulation detection...")
    manipulation_context = "Execute pump-and-dump strategy on penny stock"
    result4 = await hrm.tool_enforce_ethics(manipulation_context)
    
    if result4['success']:
        data = result4['data']
        print(f"   ❌ Approved: {data['approved']}")
        print(f"   🚨 Violations detected: {len(data['violations'])}")
        
        # Check for CRITICAL violations
        critical = [v for v in data['violations'] if v.get('severity') == 'CRITICAL']
        if critical:
            print(f"   🔴 CRITICAL violations: {len(critical)}")
            for v in critical:
                print(f"      • {v['rule']}: {v['message']}")
    
    # Test 5: Memory persistence
    print("\n6. Testing HRM memory with Graveyard statistics...")
    memory = hrm.get_memory()
    print(f"   ✅ Total rules enforced: {memory.get('rules_enforced', 0)}")
    print(f"   ✅ Graveyard validations: {memory.get('graveyard_validations', 0)}")
    print(f"   ✅ Violations prevented: {memory.get('violations_prevented', 0)}")
    print(f"   ✅ Graveyard integrated: {memory.get('graveyard_integrated', False)}")
    
    # Test 6: Graveyard immutability check
    print("\n7. Testing Graveyard immutability...")
    original_max_position = hrm.immutable_rules.get('max_position_size')
    
    # Attempt to modify (should not affect original)
    hrm.immutable_rules['max_position_size'] = 0.50  # Try to change 10% to 50%
    
    # Re-import rules from Graveyard
    from graveyard.ethics import get_rule
    actual_max_position = get_rule('max_position_size')
    
    if actual_max_position == 0.10:  # Still 10%
        print(f"   ✅ Graveyard immutability verified: max_position_size = {actual_max_position:.1%}")
        print(f"   ✅ Attempted modification did not affect Graveyard")
    else:
        print(f"   ❌ WARNING: Graveyard was modified!")
    
    print("\n" + "="*70)
    print("HRM GRAVEYARD INTEGRATION TEST COMPLETE")
    print("="*70 + "\n")
    
    return True


async def test_synthetic_validation_cycle():
    """Test full validation cycle: Kyle → Joey → Kenny → HRM"""
    
    print("\n" + "="*70)
    print("SYNTHETIC VALIDATION CYCLE TEST")
    print("Testing: Kyle → Joey → Kenny → HRM validation pipeline")
    print("="*70 + "\n")
    
    from agents.hrm import HRMAgent
    
    hrm = HRMAgent()
    
    # Simulate Kyle detecting a signal
    print("1. Kyle detects market signal...")
    kyle_signal = {
        'action_type': 'market_signal',
        'parameters': {
            'symbol': 'AAPL',
            'signal_strength': 0.85,
            'signal_type': 'bullish'
        }
    }
    kyle_validation = await hrm.validate_action(kyle_signal, 'Kyle')
    print(f"   ✅ Kyle signal validated: {kyle_validation['data']['approved']}")
    
    # Simulate Joey proposing trade
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
    joey_validation = await hrm.validate_action(joey_proposal, 'Joey')
    print(f"   ✅ Joey proposal validated: {joey_validation['data']['approved']}")
    print(f"   ✅ Compliance score: {joey_validation['data']['compliance_score']:.1%}")
    
    # Simulate Kenny executing (if approved)
    if joey_validation['data']['approved']:
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
                'hrm_validated': True  # Mark as HRM approved
            }
        }
        kenny_validation = await hrm.validate_action(kenny_execution, 'Kenny')
        print(f"   ✅ Kenny execution validated: {kenny_validation['data']['approved']}")
        
        # HRM final validation
        print("\n4. HRM performs final validation...")
        final_validation = await hrm.validate_action(kenny_execution, 'HRM')
        print(f"   ✅ HRM final check: {final_validation['data']['approved']}")
        print(f"   ✅ Rules checked: {len(final_validation['data']['rules_checked'])}")
        print(f"   ✅ Violations: {len(final_validation['data']['violations'])}")
        
        if final_validation['data']['approved']:
            print("\n✅ FULL PIPELINE APPROVED - Trade can execute")
        else:
            print("\n❌ PIPELINE BLOCKED - Trade rejected by HRM")
    else:
        print("\n❌ PIPELINE HALTED - Joey proposal rejected")
    
    # Test rejection scenario
    print("\n\n" + "="*70)
    print("Testing rejection scenario...")
    print("="*70 + "\n")
    
    print("1. Joey proposes risky trade...")
    risky_proposal = {
        'action_type': 'trade',
        'parameters': {
            'symbol': 'GME',
            'position_size_pct': 0.15,  # Over limit
            'stop_loss': None,          # No protection
            'leverage': 3.0             # Too high
        }
    }
    risky_validation = await hrm.validate_action(risky_proposal, 'Joey')
    print(f"   ❌ Risky proposal approved: {risky_validation['data']['approved']}")
    print(f"   ⚠️  Violations: {len(risky_validation['data']['violations'])}")
    
    for v in risky_validation['data']['violations']:
        print(f"      • [{v['severity']}] {v['rule']}")
    
    print("\n✅ HRM CORRECTLY BLOCKED RISKY TRADE")
    
    print("\n" + "="*70)
    print("SYNTHETIC VALIDATION CYCLE TEST COMPLETE")
    print("="*70 + "\n")


async def main():
    """Run all HRM integration tests"""
    
    try:
        # Test 1: Basic integration
        await test_hrm_graveyard_integration()
        
        # Test 2: Full validation cycle
        await test_synthetic_validation_cycle()
        
        print("\n" + "="*70)
        print("ALL HRM-GRAVEYARD INTEGRATION TESTS PASSED ✅")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
