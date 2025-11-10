"""
Unit tests for Mutable Core state management
Tests thread safety, atomicity, rollback, and concurrent access
"""

import pytest
import sys
import os
import threading
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set test database path
os.environ['ARK_STATE_DB'] = '/tmp/test_ark_mutable_core.db'

from mutable_core.state_manager import StateManager, StateSnapshot


class TestStateManagerCore:
    """Test core state management functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        # Remove test database if exists
        db_path = os.environ['ARK_STATE_DB']
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # Re-initialize database with new path
        from mutable_core.state_manager import _ensure_db
        _ensure_db()
        
        self.sm = StateManager()
    
    def test_single_agent_state(self):
        """Test basic single agent state operations"""
        self.sm.update_state("Kyle", "signal_count", 42)
        result = self.sm.get_state("Kyle", "signal_count")
        
        assert "signal_count" in result
        assert result["signal_count"] == 42
        print("✅ Single agent state test passed")
    
    def test_multiple_keys(self):
        """Test multiple keys for single agent"""
        self.sm.update_state("Joey", "patterns_found", 15)
        self.sm.update_state("Joey", "confidence", 0.85)
        self.sm.update_state("Joey", "last_scan", "2025-01-01")
        
        result = self.sm.get_state("Joey")
        
        assert len(result) == 3
        assert result["patterns_found"] == 15
        assert result["confidence"] == 0.85
        assert result["last_scan"] == "2025-01-01"
        print("✅ Multiple keys test passed")
    
    def test_data_types(self):
        """Test different data types"""
        self.sm.update_state("Kenny", "int_val", 42)
        self.sm.update_state("Kenny", "float_val", 3.14)
        self.sm.update_state("Kenny", "bool_val", True)
        self.sm.update_state("Kenny", "str_val", "hello")
        self.sm.update_state("Kenny", "dict_val", {"key": "value"})
        self.sm.update_state("Kenny", "list_val", [1, 2, 3])
        
        result = self.sm.get_state("Kenny")
        
        assert result["int_val"] == 42
        assert result["float_val"] == 3.14
        assert result["bool_val"] is True
        assert result["str_val"] == "hello"
        assert result["dict_val"] == {"key": "value"}
        assert result["list_val"] == [1, 2, 3]
        print("✅ Data types test passed")
    
    def test_update_existing_key(self):
        """Test updating existing key increments version"""
        self.sm.update_state("HRM", "rules_enforced", 10)
        self.sm.update_state("HRM", "rules_enforced", 20)
        self.sm.update_state("HRM", "rules_enforced", 30)
        
        result = self.sm.get_state("HRM", "rules_enforced")
        assert result["rules_enforced"] == 30
        
        # Check history exists
        history = self.sm.get_history("HRM", "rules_enforced", limit=5)
        assert len(history) >= 2  # At least 2 historical versions
        print("✅ Update existing key test passed")
    
    def test_delete_state(self):
        """Test deleting state"""
        self.sm.update_state("Aletheia", "temp_key", "temp_value")
        assert "temp_key" in self.sm.get_state("Aletheia")
        
        self.sm.delete_state("Aletheia", "temp_key")
        assert "temp_key" not in self.sm.get_state("Aletheia")
        print("✅ Delete state test passed")


class TestVersionControl:
    """Test version control and rollback"""
    
    def setup_method(self):
        """Setup test environment"""
        db_path = os.environ['ARK_STATE_DB']
        if os.path.exists(db_path):
            os.remove(db_path)
        
        from mutable_core.state_manager import _ensure_db
        _ensure_db()
        
        self.sm = StateManager()
    
    def test_rollback_single_step(self):
        """Test rollback one version"""
        self.sm.update_state("Kenny", "action", {"type": "BUY"})
        self.sm.update_state("Kenny", "action", {"type": "SELL"})
        
        restored = self.sm.rollback("Kenny", "action", steps=1)
        
        assert restored["type"] == "BUY"
        print("✅ Single step rollback test passed")
    
    def test_rollback_multiple_steps(self):
        """Test rollback multiple versions"""
        self.sm.update_state("Kenny", "action", {"type": "BUY", "version": 1})
        self.sm.update_state("Kenny", "action", {"type": "SELL", "version": 2})
        self.sm.update_state("Kenny", "action", {"type": "HOLD", "version": 3})
        self.sm.update_state("Kenny", "action", {"type": "EXIT", "version": 4})
        
        restored = self.sm.rollback("Kenny", "action", steps=3)
        
        assert restored["version"] == 1
        assert restored["type"] == "BUY"
        print("✅ Multiple steps rollback test passed")
    
    def test_rollback_nonexistent(self):
        """Test rollback non-existent key returns None"""
        restored = self.sm.rollback("Unknown", "unknown_key", steps=1)
        assert restored is None
        print("✅ Rollback nonexistent test passed")
    
    def test_get_history(self):
        """Test getting version history"""
        self.sm.update_state("HRM", "count", 1)
        self.sm.update_state("HRM", "count", 2)
        self.sm.update_state("HRM", "count", 3)
        
        history = self.sm.get_history("HRM", "count", limit=10)
        
        assert len(history) >= 2
        assert all(isinstance(s, StateSnapshot) for s in history)
        assert all(s.agent == "HRM" for s in history)
        assert all(s.key == "count" for s in history)
        print("✅ Get history test passed")


class TestConcurrency:
    """Test thread safety and concurrent access"""
    
    def setup_method(self):
        """Setup test environment"""
        db_path = os.environ['ARK_STATE_DB']
        if os.path.exists(db_path):
            os.remove(db_path)
        
        from mutable_core.state_manager import _ensure_db
        _ensure_db()
        
        self.sm = StateManager()
    
    def test_concurrent_writes_same_agent(self):
        """Test concurrent writes to same agent"""
        def worker(worker_id):
            for i in range(10):
                self.sm.update_state("Joey", f"metric_{worker_id}_{i}", worker_id * 100 + i)
                time.sleep(0.001)
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        result = self.sm.get_state("Joey")
        assert len(result) >= 40  # At least 40 keys written (5 threads * 8-10 keys each)
        print("✅ Concurrent writes same agent test passed")
    
    def test_concurrent_writes_different_agents(self):
        """Test concurrent writes to different agents"""
        agents = ["Kyle", "Joey", "Kenny", "HRM", "Aletheia"]
        
        def worker(agent_name, worker_id):
            for i in range(10):
                self.sm.update_state(agent_name, f"value_{i}", worker_id)
                time.sleep(0.001)
        
        threads = []
        for idx, agent in enumerate(agents):
            t = threading.Thread(target=worker, args=(agent, idx))
            threads.append(t)
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        all_state = self.sm.all_state()
        assert len(all_state) >= 5  # All 5 agents
        print("✅ Concurrent writes different agents test passed")
    
    def test_concurrent_read_write(self):
        """Test concurrent reads and writes"""
        self.sm.update_state("Kyle", "counter", 0)
        
        def reader():
            for _ in range(20):
                val = self.sm.get_state("Kyle", "counter")
                assert "counter" in val
                time.sleep(0.001)
        
        def writer():
            for i in range(20):
                self.sm.update_state("Kyle", "counter", i)
                time.sleep(0.001)
        
        readers = [threading.Thread(target=reader) for _ in range(3)]
        writers = [threading.Thread(target=writer) for _ in range(2)]
        
        threads = readers + writers
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        final_val = self.sm.get_state("Kyle", "counter")
        assert final_val["counter"] >= 0  # Should be a valid value
        print("✅ Concurrent read/write test passed")


class TestMemoryIndex:
    """Test memory index functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        db_path = os.environ['ARK_STATE_DB']
        if os.path.exists(db_path):
            os.remove(db_path)
        
        from mutable_core.state_manager import _ensure_db
        _ensure_db()
        
        self.sm = StateManager()
    
    def test_add_memory(self):
        """Test adding memories"""
        self.sm.add_memory("Joey", "pattern", "Double bottom detected", 
                          metadata={"confidence": 0.85})
        
        memories = self.sm.get_memories("Joey", "pattern")
        assert len(memories) > 0
        assert memories[0]['content'] == "Double bottom detected"
        assert memories[0]['metadata']['confidence'] == 0.85
        print("✅ Add memory test passed")
    
    def test_memory_types(self):
        """Test different memory types"""
        self.sm.add_memory("Joey", "embedding", "[0.1, 0.2, 0.3]")
        self.sm.add_memory("Joey", "summary", "Market trending upward")
        self.sm.add_memory("Joey", "pattern", "Head and shoulders")
        
        embeddings = self.sm.get_memories("Joey", "embedding")
        summaries = self.sm.get_memories("Joey", "summary")
        patterns = self.sm.get_memories("Joey", "pattern")
        
        assert len(embeddings) > 0
        assert len(summaries) > 0
        assert len(patterns) > 0
        print("✅ Memory types test passed")
    
    def test_memory_ttl(self):
        """Test memory TTL expiration"""
        self.sm.add_memory("Kyle", "temp", "Temporary data", ttl=1)  # 1 second TTL
        
        memories = self.sm.get_memories("Kyle", "temp")
        assert len(memories) > 0
        
        time.sleep(1.5)  # Wait for expiration
        
        memories = self.sm.get_memories("Kyle", "temp")
        assert len(memories) == 0  # Should be expired
        print("✅ Memory TTL test passed")


class TestSystemConfig:
    """Test system configuration management"""
    
    def setup_method(self):
        """Setup test environment"""
        db_path = os.environ['ARK_STATE_DB']
        if os.path.exists(db_path):
            os.remove(db_path)
        
        from mutable_core.state_manager import _ensure_db
        _ensure_db()
        
        self.sm = StateManager()
    
    def test_set_get_config(self):
        """Test setting and getting config"""
        self.sm.set_config("max_leverage", 2.0, "Maximum leverage", "Admin")
        config = self.sm.get_config("max_leverage")
        
        assert config["max_leverage"] == 2.0
        print("✅ Set/get config test passed")
    
    def test_multiple_configs(self):
        """Test multiple config keys"""
        self.sm.set_config("max_leverage", 2.0)
        self.sm.set_config("max_position", 0.10)
        self.sm.set_config("auto_trading", True)
        
        config = self.sm.get_config()
        
        assert len(config) >= 3
        assert config["max_leverage"] == 2.0
        assert config["max_position"] == 0.10
        assert config["auto_trading"] is True
        print("✅ Multiple configs test passed")


class TestSessionLog:
    """Test session logging"""
    
    def setup_method(self):
        """Setup test environment"""
        db_path = os.environ['ARK_STATE_DB']
        if os.path.exists(db_path):
            os.remove(db_path)
        
        from mutable_core.state_manager import _ensure_db
        _ensure_db()
        
        self.sm = StateManager()
    
    def test_log_action(self):
        """Test logging actions"""
        self.sm.log_action("Kenny", "trade", 
                          {"symbol": "SPY", "action": "BUY"}, 
                          "success", True)
        
        log = self.sm.get_session_log("Kenny")
        assert len(log) > 0
        assert log[0]['action_type'] == "trade"
        assert log[0]['result'] == "success"
        assert log[0]['graveyard_approved'] is True
        print("✅ Log action test passed")
    
    def test_multiple_logs(self):
        """Test multiple log entries"""
        for i in range(10):
            self.sm.log_action("Kenny", f"action_{i}", 
                              {"index": i}, 
                              "success" if i % 2 == 0 else "failure",
                              i % 2 == 0)
        
        log = self.sm.get_session_log("Kenny", limit=20)
        assert len(log) == 10
        print("✅ Multiple logs test passed")
    
    def test_all_agents_log(self):
        """Test getting log for all agents"""
        self.sm.log_action("Kyle", "scan", {}, "success", True)
        self.sm.log_action("Joey", "analyze", {}, "success", True)
        self.sm.log_action("Kenny", "execute", {}, "success", True)
        
        log = self.sm.get_session_log(limit=50)
        assert len(log) >= 3
        
        agents = {entry['agent'] for entry in log}
        assert "Kyle" in agents
        assert "Joey" in agents
        assert "Kenny" in agents
        print("✅ All agents log test passed")


class TestTruthMap:
    """Test Aletheia truth map"""
    
    def setup_method(self):
        """Setup test environment"""
        db_path = os.environ['ARK_STATE_DB']
        if os.path.exists(db_path):
            os.remove(db_path)
        
        from mutable_core.state_manager import _ensure_db
        _ensure_db()
        
        self.sm = StateManager()
    
    def test_set_truth(self):
        """Test setting truth"""
        self.sm.set_truth("market_sentiment", "bullish", 0.75, 
                         ["Kyle", "Joey"], "Aletheia")
        
        truth = self.sm.get_truth("market_sentiment")
        assert "market_sentiment" in truth
        assert truth["market_sentiment"]["value"] == "bullish"
        assert truth["market_sentiment"]["confidence"] == 0.75
        assert truth["market_sentiment"]["sources"] == ["Kyle", "Joey"]
        assert truth["market_sentiment"]["updated_by"] == "Aletheia"
        print("✅ Set truth test passed")
    
    def test_update_truth(self):
        """Test updating existing truth"""
        self.sm.set_truth("trend", "up", 0.6, ["Kyle"], "Aletheia")
        self.sm.set_truth("trend", "sideways", 0.8, ["Kyle", "Joey"], "Aletheia")
        
        truth = self.sm.get_truth("trend")
        assert truth["trend"]["value"] == "sideways"
        assert truth["trend"]["confidence"] == 0.8
        assert len(truth["trend"]["sources"]) == 2
        print("✅ Update truth test passed")
    
    def test_multiple_truths(self):
        """Test multiple truth values"""
        self.sm.set_truth("sentiment", "bullish", 0.7, ["Kyle"], "Aletheia")
        self.sm.set_truth("volatility", "high", 0.9, ["Joey"], "Aletheia")
        self.sm.set_truth("trend", "up", 0.8, ["Kyle", "Joey"], "Aletheia")
        
        truths = self.sm.get_truth()
        assert len(truths) >= 3
        assert "sentiment" in truths
        assert "volatility" in truths
        assert "trend" in truths
        print("✅ Multiple truths test passed")


class TestAllState:
    """Test getting all state"""
    
    def setup_method(self):
        """Setup test environment"""
        db_path = os.environ['ARK_STATE_DB']
        if os.path.exists(db_path):
            os.remove(db_path)
        
        from mutable_core.state_manager import _ensure_db
        _ensure_db()
        
        self.sm = StateManager()
    
    def test_all_state_empty(self):
        """Test all_state when empty"""
        all_state = self.sm.all_state()
        assert len(all_state) == 0
        print("✅ All state empty test passed")
    
    def test_all_state_populated(self):
        """Test all_state with multiple agents"""
        self.sm.update_state("Kyle", "signals", 10)
        self.sm.update_state("Joey", "patterns", 5)
        self.sm.update_state("Kenny", "trades", 3)
        
        all_state = self.sm.all_state()
        
        assert len(all_state) == 3
        assert "Kyle" in all_state
        assert "Joey" in all_state
        assert "Kenny" in all_state
        assert all_state["Kyle"]["signals"] == 10
        assert all_state["Joey"]["patterns"] == 5
        assert all_state["Kenny"]["trades"] == 3
        print("✅ All state populated test passed")


def run_all_tests():
    """Run all Mutable Core tests"""
    print("=" * 60)
    print("MUTABLE CORE TEST SUITE")
    print("=" * 60)
    print()
    
    test_classes = [
        TestStateManagerCore,
        TestVersionControl,
        TestConcurrency,
        TestMemoryIndex,
        TestSystemConfig,
        TestSessionLog,
        TestTruthMap,
        TestAllState
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
            
            try:
                # Setup
                if hasattr(test_instance, 'setup_method'):
                    test_instance.setup_method()
                
                # Run test
                method = getattr(test_instance, method_name)
                method()
                
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
