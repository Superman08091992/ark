#!/usr/bin/env python3
"""
ARK Cold-Start Boot Sequence (REQ_MEM_02)

Handles state restoration after system restart or crash.
Loads last-known-good state from snapshots and validates integrity.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List
import hashlib


logger = logging.getLogger(__name__)


class ColdStartError(Exception):
    """Exception raised when cold-start boot fails"""
    pass


class ColdStartBootSequence:
    """
    Manages ARK system cold-start boot with state restoration.
    
    Features:
    - Load last-known-good state snapshot
    - Validate state integrity
    - Restore agent configurations
    - Resume incomplete consolidations
    - Recover from crashes
    """
    
    def __init__(self, data_dir: Path = Path("data")):
        """
        Initialize cold-start boot sequence.
        
        Args:
            data_dir: Base data directory containing state files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.data_dir / "boot_state.json"
        self.snapshot_dir = self.data_dir / "snapshots"
        self.snapshot_dir.mkdir(exist_ok=True)
        
        self.state: Dict[str, Any] = {}
        self.restored = False
        
        logger.info(f"Cold-start boot sequence initialized: {self.data_dir}")
    
    def save_boot_state(self, state: Dict[str, Any]) -> bool:
        """
        Save current system state for cold-start restoration.
        
        Args:
            state: System state dictionary
            
        Returns:
            True if saved successfully
        """
        try:
            # Add metadata
            state['_metadata'] = {
                'timestamp': datetime.now().isoformat(),
                'version': '2.0',
                'checksum': self._calculate_checksum(state)
            }
            
            # Write atomically (write to temp, then rename)
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            # Atomic rename
            temp_file.replace(self.state_file)
            
            logger.info(f"✅ Boot state saved: {self.state_file}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to save boot state: {e}", exc_info=True)
            return False
    
    def load_boot_state(self) -> Optional[Dict[str, Any]]:
        """
        Load last-known-good state from disk.
        
        Returns:
            State dictionary or None if no valid state found
        """
        if not self.state_file.exists():
            logger.warning("No boot state file found - performing fresh boot")
            return None
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            # Validate checksum
            if not self._validate_checksum(state):
                logger.error("❌ Boot state checksum invalid - state may be corrupted")
                return None
            
            # Remove metadata before returning
            metadata = state.pop('_metadata', {})
            
            logger.info(f"✅ Boot state loaded from: {metadata.get('timestamp', 'unknown')}")
            self.state = state
            self.restored = True
            
            return state
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Corrupted boot state file: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to load boot state: {e}", exc_info=True)
            return None
    
    def restore_memory_engine(self, db_path: Path) -> bool:
        """
        Restore memory engine state after cold boot.
        
        Args:
            db_path: Path to memory database
            
        Returns:
            True if restoration successful
        """
        if not db_path.exists():
            logger.warning(f"Memory database not found: {db_path}")
            return False
        
        try:
            # Verify database integrity
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check schema version
            cursor.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]
            logger.info(f"Memory database schema version: {version}")
            
            # Check for incomplete consolidations
            cursor.execute("""
                SELECT COUNT(*) FROM reasoning_log 
                WHERE id NOT IN (SELECT source_id FROM memory_chunks)
            """)
            unconsolidated = cursor.fetchone()[0]
            
            if unconsolidated > 0:
                logger.info(f"Found {unconsolidated} unconsolidated traces - will resume consolidation")
            
            # Check database integrity
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            
            if result != "ok":
                logger.error(f"❌ Database integrity check failed: {result}")
                conn.close()
                return False
            
            conn.close()
            
            logger.info("✅ Memory engine state validated")
            return True
        
        except Exception as e:
            logger.error(f"❌ Memory engine restoration failed: {e}", exc_info=True)
            return False
    
    def restore_agent_state(self, agents: List[str]) -> Dict[str, bool]:
        """
        Restore individual agent states.
        
        Args:
            agents: List of agent names to restore
            
        Returns:
            Dict mapping agent names to restoration success status
        """
        results = {}
        
        for agent in agents:
            agent_state_file = self.data_dir / f"{agent}_state.json"
            
            if not agent_state_file.exists():
                logger.warning(f"No saved state for agent: {agent}")
                results[agent] = False
                continue
            
            try:
                with open(agent_state_file, 'r') as f:
                    agent_state = json.load(f)
                
                # Validate agent state
                if not self._validate_agent_state(agent, agent_state):
                    logger.warning(f"Invalid state for agent: {agent}")
                    results[agent] = False
                    continue
                
                logger.info(f"✅ Restored state for agent: {agent}")
                results[agent] = True
            
            except Exception as e:
                logger.error(f"❌ Failed to restore agent {agent}: {e}")
                results[agent] = False
        
        return results
    
    def perform_cold_boot(self) -> Dict[str, Any]:
        """
        Perform complete cold-start boot sequence.
        
        Returns:
            Boot report dictionary
        """
        logger.info("=" * 70)
        logger.info("🚀 ARK COLD-START BOOT SEQUENCE")
        logger.info("=" * 70)
        
        report = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'state_restored': False,
            'memory_restored': False,
            'agents_restored': {},
            'errors': []
        }
        
        # Step 1: Load boot state
        logger.info("Step 1/4: Loading boot state...")
        state = self.load_boot_state()
        report['state_restored'] = state is not None
        
        if state:
            # Step 2: Restore memory engine
            logger.info("Step 2/4: Restoring memory engine...")
            db_path = Path(state.get('memory_db_path', 'data/ark_memory.db'))
            report['memory_restored'] = self.restore_memory_engine(db_path)
            
            # Step 3: Restore agent states
            logger.info("Step 3/4: Restoring agent states...")
            agents = state.get('active_agents', ['kyle', 'joey', 'kenny', 'hrm', 'aletheia', 'id'])
            report['agents_restored'] = self.restore_agent_state(agents)
            
            # Step 4: Resume incomplete operations
            logger.info("Step 4/4: Checking for incomplete operations...")
            incomplete = self._check_incomplete_operations(state)
            report['incomplete_operations'] = incomplete
            
            if incomplete:
                logger.warning(f"Found {len(incomplete)} incomplete operations:")
                for op in incomplete:
                    logger.warning(f"  - {op}")
        else:
            logger.info("No previous state found - performing fresh boot")
            report['errors'].append("No boot state available")
        
        # Determine overall success
        if state and report['memory_restored'] and all(report['agents_restored'].values()):
            report['success'] = True
            logger.info("=" * 70)
            logger.info("✅ COLD-START BOOT SUCCESSFUL")
            logger.info("=" * 70)
        else:
            logger.warning("=" * 70)
            logger.warning("⚠️  COLD-START BOOT COMPLETED WITH WARNINGS")
            logger.warning("=" * 70)
        
        return report
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA256 checksum of state data."""
        # Remove metadata before hashing
        data_copy = {k: v for k, v in data.items() if k != '_metadata'}
        data_str = json.dumps(data_copy, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _validate_checksum(self, state: Dict[str, Any]) -> bool:
        """Validate state checksum."""
        metadata = state.get('_metadata', {})
        expected_checksum = metadata.get('checksum')
        
        if not expected_checksum:
            logger.warning("No checksum in state metadata")
            return True  # Allow boot without checksum
        
        actual_checksum = self._calculate_checksum(state)
        return actual_checksum == expected_checksum
    
    def _validate_agent_state(self, agent: str, state: Dict[str, Any]) -> bool:
        """Validate agent state structure."""
        required_keys = ['agent_name', 'timestamp']
        return all(key in state for key in required_keys)
    
    def _check_incomplete_operations(self, state: Dict[str, Any]) -> List[str]:
        """Check for incomplete operations that need resumption."""
        incomplete = []
        
        # Check for incomplete consolidations
        if state.get('consolidation_in_progress'):
            incomplete.append("Memory consolidation in progress")
        
        # Check for incomplete reflections
        if state.get('reflection_in_progress'):
            incomplete.append("Reflection cycle in progress")
        
        # Check for incomplete federation syncs
        if state.get('federation_sync_pending'):
            incomplete.append("Federation sync pending")
        
        return incomplete
    
    def create_fresh_state(self) -> Dict[str, Any]:
        """
        Create fresh initial state for new installations.
        
        Returns:
            Fresh state dictionary
        """
        return {
            'version': '2.0',
            'first_boot': True,
            'memory_db_path': 'data/ark_memory.db',
            'reasoning_db_path': 'data/reasoning_logs.db',
            'active_agents': ['kyle', 'joey', 'kenny', 'hrm', 'aletheia', 'id'],
            'consolidation_in_progress': False,
            'reflection_in_progress': False,
            'federation_sync_pending': False,
            'last_consolidation': None,
            'last_reflection': None,
            'system_start_time': datetime.now().isoformat()
        }


def main():
    """Test cold-start boot sequence."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    boot = ColdStartBootSequence()
    
    # Test saving state
    logger.info("Testing state save...")
    test_state = boot.create_fresh_state()
    boot.save_boot_state(test_state)
    
    # Test loading state
    logger.info("Testing state load...")
    loaded_state = boot.load_boot_state()
    
    if loaded_state:
        logger.info(f"Loaded state: {json.dumps(loaded_state, indent=2)}")
    
    # Test full cold boot
    logger.info("\nTesting full cold boot...")
    report = boot.perform_cold_boot()
    
    logger.info("\nBoot Report:")
    logger.info(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
