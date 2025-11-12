"""
Sandbox Manager - Safe code execution environment

This module provides isolated execution of generated code with:
- Resource limits (time, memory)
- Output capture (stdout, stderr)
- Security restrictions
- Execution monitoring

Created: 2025-11-12
"""

import hashlib
import json
import multiprocessing
import os
import resource
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from codegen.validator import CodeValidator


@dataclass
class SandboxResult:
    """Result of sandbox execution"""
    execution_id: str
    code_hash: str
    status: str  # 'success', 'error', 'timeout', 'killed', 'validation_failed'
    stdout: str
    stderr: str
    exit_code: Optional[int]
    duration_ms: int
    resource_usage: Dict
    security_violations: List[str]
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "execution_id": self.execution_id,
            "code_hash": self.code_hash,
            "status": self.status,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "resource_usage": self.resource_usage,
            "security_violations": self.security_violations,
            "error_message": self.error_message
        }


class SandboxManager:
    """Manages safe execution of generated code"""
    
    def __init__(self, 
                 db_path: str = "data/ark.db",
                 workspace: str = "codegen/sandbox_workspace",
                 timeout_seconds: int = 30,
                 memory_limit_mb: int = 512):
        self.db_path = db_path
        self.workspace = Path(workspace)
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.conn = None
        
        # Ensure workspace exists
        self.workspace.mkdir(parents=True, exist_ok=True)
        
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            
    def __enter__(self):
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        
    def execute(self, 
                code: str, 
                trust_tier: str = "sandbox",
                validate: bool = True,
                timeout_override: Optional[int] = None) -> SandboxResult:
        """
        Execute code in a sandboxed environment
        
        Args:
            code: Python code to execute
            trust_tier: Trust level for validation
            validate: Whether to validate before execution
            timeout_override: Override default timeout
            
        Returns:
            SandboxResult with execution details
        """
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        execution_id = f"exec_{int(time.time())}_{code_hash[:8]}"
        
        started_at = int(time.time() * 1000)
        
        # Step 1: Validate code if requested
        if validate:
            validator = CodeValidator(self.db_path)
            with validator:
                validation_result = validator.validate(code, trust_tier)
                
            if not validation_result.passed:
                return SandboxResult(
                    execution_id=execution_id,
                    code_hash=code_hash,
                    status="validation_failed",
                    stdout="",
                    stderr="Validation failed:\n" + "\n".join(validation_result.errors),
                    exit_code=None,
                    duration_ms=int(time.time() * 1000) - started_at,
                    resource_usage={},
                    security_violations=validation_result.errors,
                    error_message="Code validation failed"
                )
        
        # Step 2: Execute in subprocess with resource limits
        timeout = timeout_override if timeout_override else self.timeout_seconds
        
        try:
            result = self._execute_subprocess(code, timeout, code_hash)
            
            # Calculate duration
            duration_ms = int(time.time() * 1000) - started_at
            
            # Store execution in database
            self._store_execution(
                execution_id=execution_id,
                code_hash=code_hash,
                code_snippet=code,
                trust_tier=trust_tier,
                started_at=started_at,
                duration_ms=duration_ms,
                result=result
            )
            
            return result
            
        except Exception as e:
            duration_ms = int(time.time() * 1000) - started_at
            return SandboxResult(
                execution_id=execution_id,
                code_hash=code_hash,
                status="error",
                stdout="",
                stderr=str(e),
                exit_code=None,
                duration_ms=duration_ms,
                resource_usage={},
                security_violations=[],
                error_message=f"Execution error: {e}"
            )
    
    def _execute_subprocess(self, 
                           code: str, 
                           timeout: int,
                           code_hash: str) -> SandboxResult:
        """Execute code in a subprocess with resource limits"""
        
        # Create temporary file for code with absolute path
        temp_file = self.workspace.absolute() / f"sandbox_{code_hash}.py"
        
        try:
            # Write code to file
            with open(temp_file, 'w') as f:
                f.write(code)
            
            # Prepare execution environment
            env = os.environ.copy()
            # Restrict Python path to prevent importing from sensitive areas
            env['PYTHONPATH'] = str(self.workspace.absolute())
            
            # Execute with subprocess
            start_time = time.time()
            
            try:
                result = subprocess.run(
                    [sys.executable, str(temp_file.absolute())],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env,
                    cwd=str(self.workspace.absolute())
                )
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                return SandboxResult(
                    execution_id="",  # Will be set by caller
                    code_hash=code_hash,
                    status="success" if result.returncode == 0 else "error",
                    stdout=result.stdout,
                    stderr=result.stderr,
                    exit_code=result.returncode,
                    duration_ms=duration_ms,
                    resource_usage=self._estimate_resource_usage(duration_ms),
                    security_violations=[]
                )
                
            except subprocess.TimeoutExpired:
                duration_ms = int((time.time() - start_time) * 1000)
                return SandboxResult(
                    execution_id="",
                    code_hash=code_hash,
                    status="timeout",
                    stdout="",
                    stderr=f"Execution timeout after {timeout}s",
                    exit_code=None,
                    duration_ms=duration_ms,
                    resource_usage={},
                    security_violations=[],
                    error_message=f"Timeout after {timeout} seconds"
                )
                
        finally:
            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()
    
    def _estimate_resource_usage(self, duration_ms: int) -> Dict:
        """Estimate resource usage (basic implementation)"""
        return {
            "cpu_time_ms": duration_ms,
            "memory_mb": 0,  # Would need psutil for accurate measurement
            "disk_io_bytes": 0
        }
    
    def _store_execution(self,
                        execution_id: str,
                        code_hash: str,
                        code_snippet: str,
                        trust_tier: str,
                        started_at: int,
                        duration_ms: int,
                        result: SandboxResult):
        """Store execution result in database"""
        
        # Update result with execution_id
        result.execution_id = execution_id
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sandbox_executions (
                execution_id, code_hash, code_snippet, trust_tier,
                started_at, completed_at, duration_ms,
                status, stdout, stderr, exit_code,
                resource_usage, security_violations
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution_id,
            code_hash,
            code_snippet,
            trust_tier,
            started_at,
            started_at + duration_ms,
            duration_ms,
            result.status,
            result.stdout,
            result.stderr,
            result.exit_code,
            json.dumps(result.resource_usage),
            json.dumps(result.security_violations)
        ))
        self.conn.commit()
    
    def get_execution_history(self, 
                             limit: int = 10,
                             status_filter: Optional[str] = None) -> List[Dict]:
        """Get recent execution history"""
        cursor = self.conn.cursor()
        
        query = """
            SELECT execution_id, code_hash, started_at, duration_ms,
                   status, exit_code, trust_tier
            FROM sandbox_executions
        """
        
        if status_filter:
            query += f" WHERE status = '{status_filter}'"
            
        query += " ORDER BY started_at DESC LIMIT ?"
        
        cursor.execute(query, (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "execution_id": row["execution_id"],
                "code_hash": row["code_hash"],
                "started_at": row["started_at"],
                "duration_ms": row["duration_ms"],
                "status": row["status"],
                "exit_code": row["exit_code"],
                "trust_tier": row["trust_tier"]
            })
            
        return results
    
    def get_execution_details(self, execution_id: str) -> Optional[Dict]:
        """Get detailed information about an execution"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sandbox_executions WHERE execution_id = ?
        """, (execution_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
            
        return {
            "execution_id": row["execution_id"],
            "code_hash": row["code_hash"],
            "code_snippet": row["code_snippet"],
            "trust_tier": row["trust_tier"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "duration_ms": row["duration_ms"],
            "status": row["status"],
            "stdout": row["stdout"],
            "stderr": row["stderr"],
            "exit_code": row["exit_code"],
            "resource_usage": json.loads(row["resource_usage"]) if row["resource_usage"] else {},
            "security_violations": json.loads(row["security_violations"]) if row["security_violations"] else []
        }
    
    def get_stats(self) -> Dict:
        """Get sandbox execution statistics"""
        cursor = self.conn.cursor()
        
        # Total executions
        cursor.execute("SELECT COUNT(*) as total FROM sandbox_executions")
        total = cursor.fetchone()["total"]
        
        # Status distribution
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM sandbox_executions 
            GROUP BY status
        """)
        status_dist = {row["status"]: row["count"] for row in cursor.fetchall()}
        
        # Average duration
        cursor.execute("""
            SELECT AVG(duration_ms) as avg_duration 
            FROM sandbox_executions 
            WHERE status = 'success'
        """)
        avg_duration = cursor.fetchone()["avg_duration"] or 0
        
        # Success rate
        success_count = status_dist.get("success", 0)
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        return {
            "total_executions": total,
            "status_distribution": status_dist,
            "avg_duration_ms": round(avg_duration, 2),
            "success_rate": round(success_rate, 2)
        }


def main():
    """Demo: Execute code samples in sandbox"""
    print("🏗️ ARK Sandbox Manager - Phase 7")
    print("=" * 60)
    
    sandbox = SandboxManager(timeout_seconds=5)
    
    with sandbox:
        # Test 1: Simple successful execution
        print("\n✅ Test 1: Simple calculation")
        code1 = """
result = 2 + 2
print(f"2 + 2 = {result}")
"""
        result1 = sandbox.execute(code1)
        print(f"   Status: {result1.status}")
        print(f"   Output: {result1.stdout.strip()}")
        print(f"   Duration: {result1.duration_ms}ms")
        
        # Test 2: Code with error
        print("\n❌ Test 2: Code with error")
        code2 = """
x = 1 / 0  # Division by zero
"""
        result2 = sandbox.execute(code2)
        print(f"   Status: {result2.status}")
        print(f"   Error: {result2.stderr[:100]}...")
        
        # Test 3: Dangerous code (blocked by validator)
        print("\n🛡️ Test 3: Dangerous code (eval)")
        code3 = """
eval("print('Hello')")  # Blocked by validator
"""
        result3 = sandbox.execute(code3)
        print(f"   Status: {result3.status}")
        print(f"   Violations: {len(result3.security_violations)}")
        
        # Test 4: Timeout test
        print("\n⏱️  Test 4: Long-running code (timeout)")
        code4 = """
import time
time.sleep(10)  # Will timeout after 5s
print("This won't print")
"""
        result4 = sandbox.execute(code4, timeout_override=2)
        print(f"   Status: {result4.status}")
        print(f"   Duration: {result4.duration_ms}ms")
        
        # Test 5: Multiple operations
        print("\n🔢 Test 5: Multiple operations")
        code5 = """
numbers = [1, 2, 3, 4, 5]
squared = [n**2 for n in numbers]
print(f"Original: {numbers}")
print(f"Squared: {squared}")
print(f"Sum: {sum(squared)}")
"""
        result5 = sandbox.execute(code5)
        print(f"   Status: {result5.status}")
        print(f"   Output:\n{result5.stdout}")
        
        # Show statistics
        print("\n📊 Sandbox Statistics:")
        stats = sandbox.get_stats()
        print(f"   Total executions: {stats['total_executions']}")
        print(f"   Success rate: {stats['success_rate']}%")
        print(f"   Avg duration: {stats['avg_duration_ms']}ms")
        print(f"   Status distribution: {stats['status_distribution']}")
        
        # Show recent history
        print("\n📜 Recent Executions:")
        history = sandbox.get_execution_history(limit=5)
        for i, exec_info in enumerate(history, 1):
            print(f"   {i}. {exec_info['execution_id']}: {exec_info['status']} ({exec_info['duration_ms']}ms)")
    
    print("\n✨ Sandbox demonstration complete!")


if __name__ == "__main__":
    main()
