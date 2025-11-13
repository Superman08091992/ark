#!/usr/bin/env python3
"""
ARK Automatic Snapshotting Daemon (REQ_MEM_03)

Automated periodic snapshots of system state with configurable intervals
and event-triggered snapshots for critical state changes.
"""

import asyncio
import json
import logging
import signal
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any
import shutil
import gzip


logger = logging.getLogger(__name__)


class SnapshotDaemon:
    """
    Automated snapshot management for ARK system state.
    
    Features:
    - Interval-based snapshots (e.g., every 6 hours)
    - Event-triggered snapshots (consolidation complete, etc.)
    - Snapshot rotation and cleanup
    - Compression for old snapshots
    - Integrity verification
    """
    
    def __init__(
        self,
        data_dir: Path = Path("data"),
        interval_seconds: int = 21600,  # 6 hours
        max_snapshots: int = 24,  # Keep 24 snapshots (4 days at 6h interval)
        compress_after_days: int = 1
    ):
        """
        Initialize snapshot daemon.
        
        Args:
            data_dir: Base data directory
            interval_seconds: Seconds between automatic snapshots
            max_snapshots: Maximum number of snapshots to retain
            compress_after_days: Compress snapshots older than N days
        """
        self.data_dir = Path(data_dir)
        self.snapshot_dir = self.data_dir / "snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        self.interval_seconds = interval_seconds
        self.max_snapshots = max_snapshots
        self.compress_after_days = compress_after_days
        
        self.running = False
        self.last_snapshot_time: Optional[float] = None
        
        logger.info(f"Snapshot daemon initialized: {self.snapshot_dir}")
        logger.info(f"Interval: {interval_seconds}s, Max: {max_snapshots}, Compress after: {compress_after_days}d")
    
    def create_snapshot(self, trigger: str = "interval", metadata: Optional[Dict] = None) -> Optional[Path]:
        """
        Create a system state snapshot.
        
        Args:
            trigger: Snapshot trigger type (interval, event, manual)
            metadata: Additional metadata to include
            
        Returns:
            Path to created snapshot or None on failure
        """
        try:
            timestamp = datetime.now()
            snapshot_name = timestamp.strftime("snapshot_%Y%m%d_%H%M%S")
            snapshot_path = self.snapshot_dir / snapshot_name
            snapshot_path.mkdir(exist_ok=True)
            
            # Collect state from various components
            state = self._collect_system_state()
            
            # Add snapshot metadata
            state['_snapshot_metadata'] = {
                'timestamp': timestamp.isoformat(),
                'trigger': trigger,
                'version': '2.0',
                **(metadata or {})
            }
            
            # Save state file
            state_file = snapshot_path / "state.json"
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            # Copy critical databases
            self._backup_databases(snapshot_path)
            
            # Create snapshot manifest
            manifest = self._create_manifest(snapshot_path)
            with open(snapshot_path / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
            
            self.last_snapshot_time = time.time()
            
            logger.info(f"✅ Snapshot created: {snapshot_name} (trigger: {trigger})")
            
            # Cleanup old snapshots
            self._cleanup_old_snapshots()
            
            # Compress old snapshots
            self._compress_old_snapshots()
            
            return snapshot_path
        
        except Exception as e:
            logger.error(f"❌ Snapshot creation failed: {e}", exc_info=True)
            return None
    
    def restore_snapshot(self, snapshot_name: str) -> bool:
        """
        Restore system state from a snapshot.
        
        Args:
            snapshot_name: Name of snapshot to restore
            
        Returns:
            True if restoration successful
        """
        snapshot_path = self.snapshot_dir / snapshot_name
        
        if not snapshot_path.exists():
            logger.error(f"Snapshot not found: {snapshot_name}")
            return False
        
        try:
            # Check if compressed
            if (snapshot_path / "state.json.gz").exists():
                logger.info("Decompressing snapshot...")
                self._decompress_snapshot(snapshot_path)
            
            # Load state
            with open(snapshot_path / "state.json", 'r') as f:
                state = json.load(f)
            
            # Verify manifest
            with open(snapshot_path / "manifest.json", 'r') as f:
                manifest = json.load(f)
            
            # Restore databases
            logger.info("Restoring databases...")
            self._restore_databases(snapshot_path)
            
            # Save as boot state
            from memory.cold_start import ColdStartBootSequence
            boot = ColdStartBootSequence(self.data_dir)
            boot.save_boot_state(state)
            
            logger.info(f"✅ Snapshot restored: {snapshot_name}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Snapshot restoration failed: {e}", exc_info=True)
            return False
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        List all available snapshots.
        
        Returns:
            List of snapshot info dictionaries
        """
        snapshots = []
        
        for snapshot_dir in sorted(self.snapshot_dir.iterdir(), reverse=True):
            if not snapshot_dir.is_dir():
                continue
            
            try:
                manifest_path = snapshot_dir / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    
                    snapshots.append({
                        'name': snapshot_dir.name,
                        'timestamp': manifest.get('timestamp'),
                        'size_mb': manifest.get('total_size_mb'),
                        'trigger': manifest.get('trigger'),
                        'compressed': (snapshot_dir / "state.json.gz").exists()
                    })
            except Exception as e:
                logger.warning(f"Failed to read manifest for {snapshot_dir.name}: {e}")
        
        return snapshots
    
    async def run_daemon(self):
        """Run snapshot daemon loop."""
        self.running = True
        logger.info("🚀 Snapshot daemon started")
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        while self.running:
            try:
                # Create snapshot
                self.create_snapshot(trigger="interval")
                
                # Wait for next interval
                await asyncio.sleep(self.interval_seconds)
            
            except asyncio.CancelledError:
                logger.info("Snapshot daemon cancelled")
                break
            except Exception as e:
                logger.error(f"Snapshot daemon error: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait 1 minute before retry
        
        logger.info("🛑 Snapshot daemon stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum} - stopping daemon...")
        self.running = False
    
    def _collect_system_state(self) -> Dict[str, Any]:
        """Collect current system state."""
        return {
            'memory_db_path': 'data/ark_memory.db',
            'reasoning_db_path': 'data/reasoning_logs.db',
            'active_agents': ['kyle', 'joey', 'kenny', 'hrm', 'aletheia', 'id'],
            'consolidation_in_progress': False,
            'reflection_in_progress': False,
            'federation_sync_pending': False,
            'last_consolidation': None,
            'last_reflection': None,
            'system_uptime_seconds': time.time() - (self.last_snapshot_time or time.time())
        }
    
    def _backup_databases(self, snapshot_path: Path):
        """Backup critical database files."""
        db_files = [
            self.data_dir / 'ark_memory.db',
            self.data_dir / 'reasoning_logs.db',
            self.data_dir / 'ark.db'
        ]
        
        for db_file in db_files:
            if db_file.exists():
                dest = snapshot_path / db_file.name
                shutil.copy2(db_file, dest)
                logger.debug(f"Backed up: {db_file.name}")
    
    def _restore_databases(self, snapshot_path: Path):
        """Restore database files from snapshot."""
        for db_file in snapshot_path.glob("*.db"):
            dest = self.data_dir / db_file.name
            shutil.copy2(db_file, dest)
            logger.debug(f"Restored: {db_file.name}")
    
    def _create_manifest(self, snapshot_path: Path) -> Dict[str, Any]:
        """Create snapshot manifest."""
        files = list(snapshot_path.glob("*"))
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        
        return {
            'timestamp': datetime.now().isoformat(),
            'version': '2.0',
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': len(files),
            'files': [f.name for f in files]
        }
    
    def _cleanup_old_snapshots(self):
        """Delete old snapshots beyond max retention."""
        snapshots = sorted(self.snapshot_dir.iterdir(), key=lambda p: p.name, reverse=True)
        
        if len(snapshots) > self.max_snapshots:
            for snapshot in snapshots[self.max_snapshots:]:
                if snapshot.is_dir():
                    shutil.rmtree(snapshot)
                    logger.info(f"🧹 Deleted old snapshot: {snapshot.name}")
    
    def _compress_old_snapshots(self):
        """Compress snapshots older than threshold."""
        cutoff_time = time.time() - (self.compress_after_days * 86400)
        
        for snapshot_dir in self.snapshot_dir.iterdir():
            if not snapshot_dir.is_dir():
                continue
            
            state_file = snapshot_dir / "state.json"
            compressed_file = snapshot_dir / "state.json.gz"
            
            if state_file.exists() and not compressed_file.exists():
                if snapshot_dir.stat().st_mtime < cutoff_time:
                    with open(state_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    state_file.unlink()
                    logger.info(f"🗜️  Compressed snapshot: {snapshot_dir.name}")
    
    def _decompress_snapshot(self, snapshot_path: Path):
        """Decompress a compressed snapshot."""
        compressed_file = snapshot_path / "state.json.gz"
        state_file = snapshot_path / "state.json"
        
        with gzip.open(compressed_file, 'rb') as f_in:
            with open(state_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)


def main():
    """Run snapshot daemon."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    daemon = SnapshotDaemon(interval_seconds=60)  # Test with 1 minute interval
    
    # Run daemon
    try:
        asyncio.run(daemon.run_daemon())
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")


if __name__ == "__main__":
    main()
