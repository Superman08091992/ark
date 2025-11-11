#!/bin/bash
# ============================================================================
# A.R.K. Post-Install Validation Script
# ============================================================================
# 
# Validates that all ARK systems are properly installed and functional
# ============================================================================

set -e

echo "🧪 A.R.K. Post-Install Validation"
echo "=================================="
echo ""

# Activate environment
if [[ -d venv ]]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found"
    exit 1
fi

TESTS_PASSED=0
TESTS_FAILED=0

# ============================================================================
# Test Functions
# ============================================================================

test_pass() {
    echo "  ✅ $1"
    ((TESTS_PASSED++))
}

test_fail() {
    echo "  ❌ $1"
    ((TESTS_FAILED++))
}

test_section() {
    echo ""
    echo "Testing: $1"
    echo "----------------------------------------"
}

# ============================================================================
# 1. Environment Tests
# ============================================================================

test_section "Environment Configuration"

# Check .env file
if [[ -f .env ]]; then
    test_pass ".env file exists"
    
    # Check critical variables
    if grep -q "ARK_ENV=" .env; then
        test_pass "ARK_ENV configured"
    else
        test_fail "ARK_ENV not configured"
    fi
    
    if grep -q "ARK_DB_PATH=" .env; then
        test_pass "ARK_DB_PATH configured"
    else
        test_fail "ARK_DB_PATH not configured"
    fi
else
    test_fail ".env file missing"
fi

# Check virtual environment
if python3 -c "import sys; sys.exit(0 if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 1)" 2>/dev/null; then
    test_pass "Virtual environment active"
else
    test_fail "Virtual environment not active"
fi

# ============================================================================
# 2. Database Tests
# ============================================================================

test_section "Database Systems"

# Check SQLite database
if [[ -f data/demo_memory.db ]]; then
    test_pass "Memory database exists"
    
    # Check tables
    tables=$(sqlite3 data/demo_memory.db ".tables" 2>/dev/null || echo "")
    
    if echo "$tables" | grep -q "reasoning_log"; then
        test_pass "reasoning_log table exists"
    else
        test_fail "reasoning_log table missing"
    fi
    
    if echo "$tables" | grep -q "memory_chunks"; then
        test_pass "memory_chunks table exists"
    else
        test_fail "memory_chunks table missing"
    fi
    
    if echo "$tables" | grep -q "reflections"; then
        test_pass "reflections table exists"
    else
        test_fail "reflections table missing"
    fi
    
    if echo "$tables" | grep -q "id_state"; then
        test_pass "id_state table exists"
    else
        test_fail "id_state table missing"
    fi
else
    test_fail "Memory database missing"
fi

# ============================================================================
# 3. Python Module Tests
# ============================================================================

test_section "Python Modules"

# Test core imports
python3 - << 'PYCODE'
import sys

modules_to_test = [
    ('fastapi', 'FastAPI'),
    ('yaml', 'PyYAML'),
    ('numpy', 'NumPy'),
    ('nacl', 'PyNaCl'),
    ('apscheduler', 'APScheduler'),
]

for module, name in modules_to_test:
    try:
        __import__(module)
        print(f"  ✅ {name} available")
    except ImportError:
        print(f"  ❌ {name} not available")
        sys.exit(1)

sys.exit(0)
PYCODE

if [[ $? -eq 0 ]]; then
    test_pass "Core Python modules installed"
else
    test_fail "Some Python modules missing"
fi

# ============================================================================
# 4. Memory Engine Tests
# ============================================================================

test_section "Memory Engine"

python3 - << 'PYCODE'
import sys
import logging
logging.basicConfig(level=logging.ERROR)

try:
    from memory.engine import MemoryEngine
    
    engine = MemoryEngine(db_path='data/demo_memory.db')
    
    # Test stats
    stats = engine.get_stats()
    
    if 'reasoning_log' in stats:
        print("  ✅ Memory engine initialized")
        print(f"  ✅ Stats: {stats['reasoning_log']['total_traces']} traces")
    else:
        print("  ❌ Memory engine stats incomplete")
        sys.exit(1)
    
    engine.close()
    sys.exit(0)

except Exception as e:
    print(f"  ❌ Memory engine error: {e}")
    sys.exit(1)

PYCODE

# ============================================================================
# 5. Reflection System Tests
# ============================================================================

test_section "Reflection System"

python3 - << 'PYCODE'
import sys
import logging
logging.basicConfig(level=logging.ERROR)

try:
    from reflection.reflection_engine import ReflectionEngine
    
    engine = ReflectionEngine(
        db_path='data/demo_memory.db',
        policy_path='reflection/reflection_policies.yaml'
    )
    
    # Test stats
    stats = engine.get_stats()
    
    if 'total_reflections' in stats:
        print("  ✅ Reflection engine initialized")
        print(f"  ✅ Stats: {stats['total_reflections']} reflections")
    else:
        print("  ❌ Reflection engine stats incomplete")
        sys.exit(1)
    
    engine.close()
    sys.exit(0)

except Exception as e:
    print(f"  ❌ Reflection engine error: {e}")
    sys.exit(1)

PYCODE

# ============================================================================
# 6. ID Growth System Tests
# ============================================================================

test_section "ID Growth System"

python3 - << 'PYCODE'
import sys
import logging
logging.basicConfig(level=logging.ERROR)

try:
    from id.model import IDModel
    
    model = IDModel(db_path='data/demo_memory.db')
    
    # Test stats
    stats = model.get_stats()
    
    if 'total_agents' in stats:
        print("  ✅ ID model initialized")
        print(f"  ✅ Stats: {stats['total_agents']} agents")
    else:
        print("  ❌ ID model stats incomplete")
        sys.exit(1)
    
    model.close()
    sys.exit(0)

except Exception as e:
    print(f"  ❌ ID model error: {e}")
    sys.exit(1)

PYCODE

# ============================================================================
# 7. Feature Extraction Tests
# ============================================================================

test_section "Feature Extraction"

python3 - << 'PYCODE'
import sys
import logging
logging.basicConfig(level=logging.ERROR)

try:
    from id.features import FeatureExtractor
    
    extractor = FeatureExtractor()
    
    # Test with sample data
    sample_traces = [{
        'agent': 'TestAgent',
        'confidence': 0.8,
        'duration_ms': 2000,
        'depth': 4,
        'input': 'Test input',
        'output': 'Test output with some content',
        'trust_tier': 'core'
    }]
    
    features = extractor.extract_from_traces(sample_traces)
    
    if len(features) >= 15:
        print(f"  ✅ Feature extraction working ({len(features)} features)")
    else:
        print(f"  ❌ Insufficient features extracted: {len(features)}")
        sys.exit(1)
    
    sys.exit(0)

except Exception as e:
    print(f"  ❌ Feature extraction error: {e}")
    sys.exit(1)

PYCODE

# ============================================================================
# 8. Federation Tests
# ============================================================================

test_section "Federation System"

if [[ -f data/federation/keys/peer_id.txt ]]; then
    peer_id=$(cat data/federation/keys/peer_id.txt)
    test_pass "Federation keys generated (Peer: $peer_id)"
else
    test_fail "Federation keys not generated"
fi

if [[ -f data/federation/keys/signing.key ]]; then
    test_pass "Signing key exists"
else
    test_fail "Signing key missing"
fi

if [[ -f data/federation/keys/verify.key ]]; then
    test_pass "Verify key exists"
else
    test_fail "Verify key missing"
fi

# ============================================================================
# 9. Service Scripts Tests
# ============================================================================

test_section "Service Management"

if [[ -f arkstart.sh ]] && [[ -x arkstart.sh ]]; then
    test_pass "arkstart.sh executable"
else
    test_fail "arkstart.sh not executable"
fi

if [[ -f arkstop.sh ]] && [[ -x arkstop.sh ]]; then
    test_pass "arkstop.sh executable"
else
    test_fail "arkstop.sh not executable"
fi

if [[ -f arkstatus.sh ]] && [[ -x arkstatus.sh ]]; then
    test_pass "arkstatus.sh executable"
else
    test_fail "arkstatus.sh not executable"
fi

# ============================================================================
# 10. Docker Tests
# ============================================================================

test_section "Docker Configuration"

if [[ -f Dockerfile ]]; then
    test_pass "Dockerfile exists"
else
    test_fail "Dockerfile missing"
fi

if [[ -f docker-compose.yml ]]; then
    test_pass "docker-compose.yml exists"
else
    test_fail "docker-compose.yml missing"
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo ""
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo "✅ All validation tests passed!"
    echo ""
    echo "Your ARK system is ready to use."
    echo "Start with: ./arkstart.sh"
    exit 0
else
    echo "⚠️  Some validation tests failed"
    echo ""
    echo "Please review the errors above and:"
    echo "  1. Check that all dependencies are installed"
    echo "  2. Verify database schema is initialized"
    echo "  3. Ensure all Python modules are available"
    echo ""
    echo "Re-run validation after fixes: ./ark-validate.sh"
    exit 1
fi
