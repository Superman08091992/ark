#!/usr/bin/env python3
"""
ARK Real-Time Monitoring Tool
Live system metrics, performance tracking, and alerts
"""

import os
import sys
import time
import psutil
import sqlite3
import signal
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import redis.asyncio as aioredis
    import asyncio
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'


class ARKMonitor:
    """Real-time ARK system monitor"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getenv('ARK_BASE_PATH', os.getcwd()))
        self.data_dir = self.base_path / "data"
        self.logs_dir = self.base_path / "logs"
        
        # Database paths
        self.ark_db = self.data_dir / "ark.db"
        self.reasoning_db = self.data_dir / "reasoning_logs.db"
        
        # Redis
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = None
        
        # Metrics history
        self.cpu_history = deque(maxlen=60)  # Last 60 seconds
        self.mem_history = deque(maxlen=60)
        self.db_queries = deque(maxlen=60)
        
        # Running flag
        self.running = True
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
        print(f"\n{Colors.YELLOW}Monitoring stopped{Colors.RESET}")
        sys.exit(0)
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_system_metrics(self) -> Dict:
        """Get current system metrics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(str(self.base_path))
        
        self.cpu_history.append(cpu_percent)
        self.mem_history.append(mem.percent)
        
        return {
            "cpu_percent": cpu_percent,
            "cpu_count": psutil.cpu_count(),
            "mem_percent": mem.percent,
            "mem_used_gb": mem.used / (1024**3),
            "mem_total_gb": mem.total / (1024**3),
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used / (1024**3),
            "disk_total_gb": disk.total / (1024**3),
        }
    
    def get_ark_processes(self) -> List[Dict]:
        """Get ARK-related processes"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(keyword in cmdline for keyword in ['reasoning_api', 'uvicorn', 'ark-federation', 'redis-server']):
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cmdline": cmdline[:80],
                        "cpu": proc.info['cpu_percent'] or 0.0,
                        "mem": proc.info['memory_percent'] or 0.0,
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return processes
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        stats = {}
        
        for db_name, db_path in [("ark", self.ark_db), ("reasoning", self.reasoning_db)]:
            if not db_path.exists():
                stats[db_name] = {"exists": False}
                continue
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get table count
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                
                # Get total row count (sample from main tables)
                total_rows = 0
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = cursor.fetchall()
                
                for (table,) in tables[:5]:  # Sample first 5 tables
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        total_rows += cursor.fetchone()[0]
                    except:
                        pass
                
                # Get database size
                db_size_mb = db_path.stat().st_size / (1024 * 1024)
                
                stats[db_name] = {
                    "exists": True,
                    "tables": table_count,
                    "rows_sample": total_rows,
                    "size_mb": round(db_size_mb, 2),
                }
                
                conn.close()
            except Exception as e:
                stats[db_name] = {"exists": True, "error": str(e)}
        
        return stats
    
    async def get_redis_stats(self) -> Dict:
        """Get Redis statistics"""
        if not REDIS_AVAILABLE:
            return {"available": False}
        
        try:
            if not self.redis:
                self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
            
            info = await self.redis.info()
            dbsize = await self.redis.dbsize()
            
            return {
                "available": True,
                "connected_clients": info.get('connected_clients', 0),
                "used_memory_mb": info.get('used_memory', 0) / (1024 * 1024),
                "keys": dbsize,
                "uptime_days": info.get('uptime_in_days', 0),
            }
        except Exception as e:
            return {"available": True, "error": str(e)}
    
    def render_bar(self, percent: float, width: int = 30) -> str:
        """Render a percentage bar"""
        filled = int(width * percent / 100)
        
        if percent < 50:
            color = Colors.GREEN
        elif percent < 80:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        
        bar = f"{color}{'█' * filled}{Colors.GRAY}{'░' * (width - filled)}{Colors.RESET}"
        return f"{bar} {percent:5.1f}%"
    
    def render_sparkline(self, data: deque, width: int = 40) -> str:
        """Render a sparkline chart"""
        if not data:
            return " " * width
        
        # Sparkline characters
        bars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        
        # Normalize data to 0-7 range
        max_val = max(data) if data else 1
        normalized = [int((val / max_val) * 7) if max_val > 0 else 0 for val in data]
        
        # Take last 'width' values
        values = list(normalized)[-width:]
        
        # Pad with zeros if needed
        values = [0] * (width - len(values)) + values
        
        # Color based on recent trend
        recent_avg = sum(list(data)[-10:]) / min(10, len(data)) if data else 0
        if recent_avg < 50:
            color = Colors.GREEN
        elif recent_avg < 80:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        
        return color + ''.join(bars[v] for v in values) + Colors.RESET
    
    def render_dashboard(self, metrics: Dict):
        """Render the monitoring dashboard"""
        self.clear_screen()
        
        # Header
        print(f"{Colors.BOLD}{Colors.CYAN}╔═══════════════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.RESET}        {Colors.BOLD}ARK SYSTEM MONITOR{Colors.RESET} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}        {Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}╚═══════════════════════════════════════════════════════════════════╝{Colors.RESET}\n")
        
        # System metrics
        sys_metrics = metrics['system']
        print(f"{Colors.BOLD}{Colors.BLUE}🖥️  SYSTEM RESOURCES{Colors.RESET}")
        print(f"  CPU:    {self.render_bar(sys_metrics['cpu_percent'])}  ({sys_metrics['cpu_count']} cores)")
        print(f"  Memory: {self.render_bar(sys_metrics['mem_percent'])}  ({sys_metrics['mem_used_gb']:.1f}/{sys_metrics['mem_total_gb']:.1f} GB)")
        print(f"  Disk:   {self.render_bar(sys_metrics['disk_percent'])}  ({sys_metrics['disk_used_gb']:.1f}/{sys_metrics['disk_total_gb']:.1f} GB)")
        
        # Sparklines
        print(f"\n{Colors.BOLD}{Colors.BLUE}📊 TRENDS (60s){Colors.RESET}")
        print(f"  CPU:    {self.render_sparkline(self.cpu_history)}")
        print(f"  Memory: {self.render_sparkline(self.mem_history)}")
        
        # Processes
        processes = metrics['processes']
        print(f"\n{Colors.BOLD}{Colors.BLUE}⚙️  ARK PROCESSES ({len(processes)}){Colors.RESET}")
        if processes:
            for proc in processes[:5]:  # Show top 5
                print(f"  {Colors.GREEN}[{proc['pid']:5d}]{Colors.RESET} {proc['name']:20s} CPU:{proc['cpu']:5.1f}% MEM:{proc['mem']:5.1f}%")
                if len(proc['cmdline']) > 60:
                    print(f"         {Colors.GRAY}{proc['cmdline'][:80]}...{Colors.RESET}")
        else:
            print(f"  {Colors.YELLOW}No ARK processes detected{Colors.RESET}")
        
        # Databases
        db_stats = metrics['databases']
        print(f"\n{Colors.BOLD}{Colors.BLUE}💾 DATABASES{Colors.RESET}")
        for db_name, stats in db_stats.items():
            if stats.get('exists'):
                if 'error' in stats:
                    print(f"  {db_name:12s}: {Colors.RED}Error - {stats['error']}{Colors.RESET}")
                else:
                    print(f"  {db_name:12s}: {Colors.GREEN}✓{Colors.RESET} {stats['tables']:3d} tables, ~{stats['rows_sample']:,} rows, {stats['size_mb']:6.1f} MB")
            else:
                print(f"  {db_name:12s}: {Colors.YELLOW}Not found{Colors.RESET}")
        
        # Redis
        redis_stats = metrics['redis']
        print(f"\n{Colors.BOLD}{Colors.BLUE}🔴 REDIS{Colors.RESET}")
        if redis_stats.get('available'):
            if 'error' in redis_stats:
                print(f"  Status: {Colors.RED}Error - {redis_stats['error']}{Colors.RESET}")
            else:
                print(f"  Status:  {Colors.GREEN}✓ Connected{Colors.RESET}")
                print(f"  Keys:    {redis_stats['keys']:,}")
                print(f"  Memory:  {redis_stats['used_memory_mb']:.1f} MB")
                print(f"  Clients: {redis_stats['connected_clients']}")
                print(f"  Uptime:  {redis_stats['uptime_days']} days")
        else:
            print(f"  Status: {Colors.YELLOW}Not available{Colors.RESET}")
        
        # Footer
        print(f"\n{Colors.GRAY}Press Ctrl+C to stop monitoring{Colors.RESET}")
    
    async def monitor_loop(self, interval: int = 2):
        """Main monitoring loop"""
        print(f"{Colors.CYAN}Starting ARK Monitor...{Colors.RESET}")
        time.sleep(1)
        
        while self.running:
            try:
                # Collect metrics
                metrics = {
                    "system": self.get_system_metrics(),
                    "processes": self.get_ark_processes(),
                    "databases": self.get_database_stats(),
                    "redis": await self.get_redis_stats(),
                }
                
                # Render dashboard
                self.render_dashboard(metrics)
                
                # Wait for next update
                await asyncio.sleep(interval)
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"{Colors.RED}Error: {e}{Colors.RESET}")
                await asyncio.sleep(interval)
        
        # Cleanup
        if self.redis:
            await self.redis.close()


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="ARK Real-Time System Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              - Start monitoring with 2s interval
  %(prog)s --interval 5 - Update every 5 seconds
  %(prog)s --base-path /opt/ark  - Monitor ARK at custom path
        """
    )
    
    parser.add_argument('--interval', type=int, default=2,
                       help='Update interval in seconds (default: 2)')
    
    parser.add_argument('--base-path', type=str,
                       help='ARK base path (default: ARK_BASE_PATH env or cwd)')
    
    args = parser.parse_args()
    
    monitor = ARKMonitor(base_path=args.base_path)
    await monitor.monitor_loop(interval=args.interval)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Monitor stopped{Colors.RESET}")
        sys.exit(0)
