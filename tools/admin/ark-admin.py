#!/usr/bin/env python3
"""
ARK Administration Tool
Complete system administration, health checks, and management
"""

import os
import sys
import argparse
import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import redis.asyncio as aioredis
    import asyncio
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis not available - federation features disabled")


class ARKAdmin:
    """ARK System Administration Tool"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getenv('ARK_BASE_PATH', os.getcwd()))
        self.data_dir = self.base_path / "data"
        self.logs_dir = self.base_path / "logs"
        self.keys_dir = self.base_path / "keys"
        
        # Database paths
        self.ark_db = self.data_dir / "ark.db"
        self.reasoning_db = self.data_dir / "reasoning_logs.db"
        
        # Redis connection
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = None
    
    async def connect_redis(self) -> bool:
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            return False
        try:
            self.redis = await aioredis.from_url(self.redis_url)
            await self.redis.ping()
            return True
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return False
    
    def get_db_connection(self, db_path: Path) -> sqlite3.Connection:
        """Get database connection"""
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        return sqlite3.connect(db_path)
    
    # ==================== SYSTEM HEALTH ====================
    
    async def check_system_health(self) -> Dict:
        """Comprehensive system health check"""
        health = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "checks": {}
        }
        
        # Check directories
        health["checks"]["directories"] = self._check_directories()
        
        # Check databases
        health["checks"]["databases"] = self._check_databases()
        
        # Check Redis
        if REDIS_AVAILABLE:
            redis_ok = await self.connect_redis()
            health["checks"]["redis"] = {
                "status": "ok" if redis_ok else "error",
                "connected": redis_ok
            }
        
        # Check processes
        health["checks"]["processes"] = self._check_processes()
        
        # Check disk space
        health["checks"]["disk_space"] = self._check_disk_space()
        
        # Determine overall status
        if any(check.get("status") == "error" for check in health["checks"].values()):
            health["status"] = "degraded"
        
        return health
    
    def _check_directories(self) -> Dict:
        """Check required directories exist"""
        required_dirs = ["data", "logs", "keys", "agent_logs", "files"]
        status = {"status": "ok", "directories": {}}
        
        for dirname in required_dirs:
            dir_path = self.base_path / dirname
            exists = dir_path.exists()
            status["directories"][dirname] = {
                "exists": exists,
                "path": str(dir_path)
            }
            if not exists:
                status["status"] = "warning"
        
        return status
    
    def _check_databases(self) -> Dict:
        """Check database health"""
        status = {"status": "ok", "databases": {}}
        
        for db_name, db_path in [("ark", self.ark_db), ("reasoning", self.reasoning_db)]:
            db_status = {
                "exists": db_path.exists(),
                "path": str(db_path)
            }
            
            if db_path.exists():
                try:
                    conn = self.get_db_connection(db_path)
                    cursor = conn.cursor()
                    
                    # Get table count
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                    table_count = cursor.fetchone()[0]
                    
                    # Get database size
                    db_size = db_path.stat().st_size
                    
                    db_status.update({
                        "tables": table_count,
                        "size_mb": round(db_size / 1024 / 1024, 2),
                        "readable": True
                    })
                    
                    conn.close()
                except Exception as e:
                    db_status["error"] = str(e)
                    db_status["readable"] = False
                    status["status"] = "error"
            else:
                status["status"] = "error"
            
            status["databases"][db_name] = db_status
        
        return status
    
    def _check_processes(self) -> Dict:
        """Check running ARK processes"""
        status = {"status": "ok", "processes": []}
        
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if any(proc in line for proc in ["reasoning_api", "uvicorn", "ark-federation"]):
                    status["processes"].append(line.strip())
            
            if not status["processes"]:
                status["status"] = "warning"
                status["message"] = "No ARK processes running"
        
        except Exception as e:
            status["status"] = "error"
            status["error"] = str(e)
        
        return status
    
    def _check_disk_space(self) -> Dict:
        """Check available disk space"""
        status = {"status": "ok"}
        
        try:
            result = subprocess.run(
                ["df", "-h", str(self.base_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 5:
                    status["total"] = parts[1]
                    status["used"] = parts[2]
                    status["available"] = parts[3]
                    status["percent_used"] = parts[4]
                    
                    # Warning if > 90% used
                    percent = int(parts[4].rstrip('%'))
                    if percent > 90:
                        status["status"] = "warning"
                        status["message"] = "Disk space > 90% used"
        
        except Exception as e:
            status["error"] = str(e)
        
        return status
    
    # ==================== DATABASE MANAGEMENT ====================
    
    def list_databases(self):
        """List all databases and their statistics"""
        print("\n📊 ARK Databases\n" + "="*60)
        
        for db_name, db_path in [("ARK Main", self.ark_db), ("Reasoning Logs", self.reasoning_db)]:
            print(f"\n{db_name}: {db_path}")
            
            if not db_path.exists():
                print("  ❌ Database not found")
                continue
            
            try:
                conn = self.get_db_connection(db_path)
                cursor = conn.cursor()
                
                # Get tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = cursor.fetchall()
                
                print(f"  📁 Tables: {len(tables)}")
                print(f"  💾 Size: {db_path.stat().st_size / 1024 / 1024:.2f} MB")
                
                # Table statistics
                for (table_name,) in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"    - {table_name}: {count:,} rows")
                
                conn.close()
            
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    def vacuum_databases(self):
        """Vacuum databases to reclaim space"""
        print("\n🧹 Vacuuming Databases\n" + "="*60)
        
        for db_name, db_path in [("ARK Main", self.ark_db), ("Reasoning Logs", self.reasoning_db)]:
            if not db_path.exists():
                print(f"⏭️  Skipping {db_name} - not found")
                continue
            
            print(f"\n{db_name}...")
            size_before = db_path.stat().st_size / 1024 / 1024
            
            try:
                conn = self.get_db_connection(db_path)
                conn.execute("VACUUM")
                conn.close()
                
                size_after = db_path.stat().st_size / 1024 / 1024
                saved = size_before - size_after
                
                print(f"  ✅ Before: {size_before:.2f} MB")
                print(f"  ✅ After: {size_after:.2f} MB")
                print(f"  ✅ Saved: {saved:.2f} MB ({saved/size_before*100:.1f}%)")
            
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    def analyze_databases(self):
        """Analyze and optimize databases"""
        print("\n📈 Analyzing Databases\n" + "="*60)
        
        for db_name, db_path in [("ARK Main", self.ark_db), ("Reasoning Logs", self.reasoning_db)]:
            if not db_path.exists():
                continue
            
            print(f"\n{db_name}...")
            
            try:
                conn = self.get_db_connection(db_path)
                conn.execute("ANALYZE")
                print("  ✅ Analysis complete")
                conn.close()
            
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    # ==================== FEDERATION MANAGEMENT ====================
    
    async def list_peers(self):
        """List federation peers"""
        if not await self.connect_redis():
            print("❌ Cannot connect to Redis")
            return
        
        print("\n🌐 Federation Peers\n" + "="*60)
        
        try:
            peer_count = 0
            async for key in self.redis.scan_iter(match="peer:*"):
                peer_count += 1
                peer_data = await self.redis.hgetall(key)
                
                peer_id = key.decode().replace("peer:", "")
                print(f"\n🔗 Peer: {peer_id}")
                
                for field, value in peer_data.items():
                    field_str = field.decode() if isinstance(field, bytes) else field
                    value_str = value.decode() if isinstance(value, bytes) else value
                    print(f"  {field_str}: {value_str}")
            
            if peer_count == 0:
                print("  No peers found")
            else:
                print(f"\n📊 Total peers: {peer_count}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def clear_redis(self, pattern: str = None):
        """Clear Redis keys"""
        if not await self.connect_redis():
            print("❌ Cannot connect to Redis")
            return
        
        pattern = pattern or "*"
        print(f"\n🗑️  Clearing Redis keys matching: {pattern}\n" + "="*60)
        
        try:
            count = 0
            async for key in self.redis.scan_iter(match=pattern):
                await self.redis.delete(key)
                count += 1
                if count % 100 == 0:
                    print(f"  Deleted {count} keys...")
            
            print(f"✅ Deleted {count} keys")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # ==================== LOG MANAGEMENT ====================
    
    def analyze_logs(self, days: int = 7):
        """Analyze logs for errors and warnings"""
        print(f"\n📋 Log Analysis (last {days} days)\n" + "="*60)
        
        cutoff = datetime.now() - timedelta(days=days)
        
        for log_file in self.logs_dir.glob("*.log"):
            print(f"\n📄 {log_file.name}")
            
            errors = 0
            warnings = 0
            
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if 'ERROR' in line or 'Error' in line:
                            errors += 1
                        elif 'WARNING' in line or 'Warning' in line:
                            warnings += 1
                
                print(f"  ⚠️  Warnings: {warnings}")
                print(f"  ❌ Errors: {errors}")
            
            except Exception as e:
                print(f"  ❌ Could not read: {e}")
    
    def rotate_logs(self, days: int = 30):
        """Rotate old logs"""
        print(f"\n🔄 Rotating logs older than {days} days\n" + "="*60)
        
        cutoff = datetime.now() - timedelta(days=days)
        rotated = 0
        
        for log_file in self.logs_dir.glob("*.log"):
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            if mtime < cutoff:
                archive_name = log_file.stem + f"_{mtime.strftime('%Y%m%d')}" + log_file.suffix + ".old"
                archive_path = log_file.parent / archive_name
                
                try:
                    log_file.rename(archive_path)
                    print(f"  ✅ Rotated: {log_file.name} -> {archive_name}")
                    rotated += 1
                except Exception as e:
                    print(f"  ❌ Failed to rotate {log_file.name}: {e}")
        
        if rotated == 0:
            print("  No logs to rotate")
        else:
            print(f"\n✅ Rotated {rotated} log files")


async def main():
    parser = argparse.ArgumentParser(
        description="ARK System Administration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s health              - Check system health
  %(prog)s db-list             - List databases and statistics
  %(prog)s db-vacuum           - Vacuum databases to reclaim space
  %(prog)s db-analyze          - Analyze and optimize databases
  %(prog)s peers               - List federation peers
  %(prog)s logs --days 7       - Analyze logs from last 7 days
  %(prog)s rotate-logs --days 30  - Rotate logs older than 30 days
  %(prog)s redis-clear peer:*  - Clear Redis peer keys
        """
    )
    
    parser.add_argument('command', choices=[
        'health', 'db-list', 'db-vacuum', 'db-analyze',
        'peers', 'redis-clear', 'logs', 'rotate-logs'
    ], help='Command to execute')
    
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days for log operations (default: 7)')
    
    parser.add_argument('--pattern', type=str,
                       help='Pattern for Redis key operations')
    
    parser.add_argument('--base-path', type=str,
                       help='ARK base path (default: ARK_BASE_PATH env or cwd)')
    
    args = parser.parse_args()
    
    admin = ARKAdmin(base_path=args.base_path)
    
    if args.command == 'health':
        health = await admin.check_system_health()
        print("\n🏥 System Health Check\n" + "="*60)
        print(json.dumps(health, indent=2))
    
    elif args.command == 'db-list':
        admin.list_databases()
    
    elif args.command == 'db-vacuum':
        admin.vacuum_databases()
    
    elif args.command == 'db-analyze':
        admin.analyze_databases()
    
    elif args.command == 'peers':
        await admin.list_peers()
    
    elif args.command == 'redis-clear':
        await admin.clear_redis(pattern=args.pattern)
    
    elif args.command == 'logs':
        admin.analyze_logs(days=args.days)
    
    elif args.command == 'rotate-logs':
        admin.rotate_logs(days=args.days)


if __name__ == "__main__":
    asyncio.run(main())
