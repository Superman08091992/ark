#!/usr/bin/env python3
"""
ARK System Lockfile Manager (REQ_INFRA_02)

Prevents multiple ARK instances from running simultaneously.
Uses PID-based locking with stale lock detection and automatic cleanup.
"""

import os
import sys
import time
import psutil
from pathlib import Path
from typing import Optional


class LockfileError(Exception):
    """Exception raised when lockfile operations fail"""
    pass


class SystemLockfile:
    """
    Manages ARK system-wide lockfile to prevent duplicate instances.
    
    Features:
    - PID-based locking
    - Stale lock detection
    - Automatic cleanup
    - Multiple lockfile support (backend, frontend, agents)
    """
    
    def __init__(self, lockfile_path: str = "/tmp/ark.lock", component: str = "system"):
        """
        Initialize lockfile manager.
        
        Args:
            lockfile_path: Path to lockfile (default: /tmp/ark.lock)
            component: Component name for multi-component locking
        """
        self.lockfile_path = Path(lockfile_path)
        self.component = component
        self.pid = os.getpid()
    
    def acquire(self, force: bool = False) -> bool:
        """
        Acquire the lockfile.
        
        Args:
            force: Force acquire by removing stale locks
            
        Returns:
            True if lock acquired, False otherwise
            
        Raises:
            LockfileError: If another instance is running
        """
        # Check if lockfile exists
        if self.lockfile_path.exists():
            # Read existing PID
            try:
                with open(self.lockfile_path, 'r') as f:
                    data = f.read().strip().split('\n')
                    if len(data) >= 2:
                        existing_pid = int(data[0])
                        existing_component = data[1]
                    else:
                        existing_pid = int(data[0])
                        existing_component = "unknown"
                
                # Check if process is still running
                if self._is_process_running(existing_pid):
                    if force:
                        print(f"⚠️  Force mode: Terminating existing process (PID: {existing_pid})")
                        self._terminate_process(existing_pid)
                    else:
                        raise LockfileError(
                            f"ARK {existing_component} is already running (PID: {existing_pid})\n"
                            f"Use --force to terminate existing instance or run 'arkstop.sh' first"
                        )
                else:
                    # Stale lockfile - remove it
                    print(f"🧹 Cleaning up stale lockfile (PID {existing_pid} not running)")
                    self.lockfile_path.unlink()
            
            except (ValueError, FileNotFoundError) as e:
                # Corrupted lockfile - remove it
                print(f"⚠️  Corrupted lockfile detected, removing: {e}")
                self.lockfile_path.unlink()
        
        # Write our PID to lockfile
        try:
            with open(self.lockfile_path, 'w') as f:
                f.write(f"{self.pid}\n")
                f.write(f"{self.component}\n")
                f.write(f"{time.time()}\n")
            
            print(f"✅ Lock acquired for {self.component} (PID: {self.pid})")
            return True
        
        except Exception as e:
            raise LockfileError(f"Failed to acquire lock: {e}")
    
    def release(self) -> bool:
        """
        Release the lockfile.
        
        Returns:
            True if lock released, False if no lock was held
        """
        if not self.lockfile_path.exists():
            return False
        
        try:
            # Verify we own this lock
            with open(self.lockfile_path, 'r') as f:
                existing_pid = int(f.readline().strip())
            
            if existing_pid == self.pid:
                self.lockfile_path.unlink()
                print(f"✅ Lock released for {self.component} (PID: {self.pid})")
                return True
            else:
                print(f"⚠️  Lock owned by different process (PID: {existing_pid})")
                return False
        
        except Exception as e:
            print(f"⚠️  Failed to release lock: {e}")
            return False
    
    def _is_process_running(self, pid: int) -> bool:
        """
        Check if a process is currently running.
        
        Args:
            pid: Process ID to check
            
        Returns:
            True if process exists, False otherwise
        """
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _terminate_process(self, pid: int, timeout: int = 5) -> bool:
        """
        Terminate a process gracefully (SIGTERM, then SIGKILL).
        
        Args:
            pid: Process ID to terminate
            timeout: Seconds to wait for graceful termination
            
        Returns:
            True if process terminated
        """
        try:
            process = psutil.Process(pid)
            
            # Try graceful termination first
            process.terminate()
            try:
                process.wait(timeout=timeout)
                print(f"✅ Process {pid} terminated gracefully")
                return True
            except psutil.TimeoutExpired:
                # Force kill if graceful failed
                print(f"⚠️  Process {pid} did not terminate gracefully, forcing...")
                process.kill()
                process.wait(timeout=2)
                print(f"✅ Process {pid} force-killed")
                return True
        
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"⚠️  Could not terminate process {pid}: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry"""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()


def check_component_lock(component: str) -> Optional[int]:
    """
    Check if a specific ARK component is locked.
    
    Args:
        component: Component name (backend, frontend, agents)
        
    Returns:
        PID if locked, None otherwise
    """
    lockfile = Path(f"/tmp/ark_{component}.lock")
    
    if not lockfile.exists():
        return None
    
    try:
        with open(lockfile, 'r') as f:
            pid = int(f.readline().strip())
        
        # Verify process is running
        if psutil.Process(pid).is_running():
            return pid
        else:
            # Stale lock - remove it
            lockfile.unlink()
            return None
    
    except (ValueError, FileNotFoundError, psutil.NoSuchProcess):
        return None


def main():
    """CLI for lockfile testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ARK Lockfile Manager")
    parser.add_argument("--acquire", action="store_true", help="Acquire lock")
    parser.add_argument("--release", action="store_true", help="Release lock")
    parser.add_argument("--check", action="store_true", help="Check lock status")
    parser.add_argument("--force", action="store_true", help="Force acquire (terminate existing)")
    parser.add_argument("--component", default="system", help="Component name")
    
    args = parser.parse_args()
    
    lock = SystemLockfile(component=args.component)
    
    if args.acquire:
        try:
            lock.acquire(force=args.force)
            print(f"✅ Lock acquired successfully")
        except LockfileError as e:
            print(f"❌ {e}")
            sys.exit(1)
    
    elif args.release:
        if lock.release():
            print("✅ Lock released successfully")
        else:
            print("⚠️  No lock was held")
    
    elif args.check:
        if lock.lockfile_path.exists():
            with open(lock.lockfile_path, 'r') as f:
                data = f.read().strip().split('\n')
                print(f"🔒 Lock exists:")
                print(f"   PID: {data[0]}")
                if len(data) > 1:
                    print(f"   Component: {data[1]}")
                if len(data) > 2:
                    print(f"   Timestamp: {data[2]}")
        else:
            print("✅ No lock exists")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
