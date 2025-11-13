#!/usr/bin/env python3
"""
ARK Port Collision Detection (REQ_INFRA_03)

Pre-flight port availability checker to prevent startup failures due to port conflicts.
Provides remediation guidance for common port collision scenarios.
"""

import socket
import psutil
from typing import List, Dict, Optional, Tuple


class PortChecker:
    """
    Checks port availability before service startup.
    
    Features:
    - Port binding test
    - Process identification on ports
    - Remediation guidance
    - Batch port checking
    """
    
    # ARK default ports
    DEFAULT_PORTS = {
        'backend': 8101,
        'frontend': 5173,
        'redis': 6379,
        'dashboard': 3000
    }
    
    def __init__(self):
        """Initialize port checker"""
        pass
    
    def is_port_available(self, port: int, host: str = '0.0.0.0') -> bool:
        """
        Check if a port is available for binding.
        
        Args:
            port: Port number to check
            host: Host to bind (default: 0.0.0.0)
            
        Returns:
            True if port is available, False otherwise
        """
        try:
            # Try to create and bind a socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            sock.close()
            return True
        except OSError:
            return False
    
    def get_process_on_port(self, port: int) -> Optional[Dict[str, any]]:
        """
        Identify the process using a specific port.
        
        Args:
            port: Port number to check
            
        Returns:
            Dict with process info or None if no process found
        """
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port and conn.status == 'LISTEN':
                try:
                    process = psutil.Process(conn.pid)
                    return {
                        'pid': conn.pid,
                        'name': process.name(),
                        'cmdline': ' '.join(process.cmdline()),
                        'username': process.username(),
                        'create_time': process.create_time()
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return {
                        'pid': conn.pid,
                        'name': 'Unknown',
                        'cmdline': 'Access denied',
                        'username': 'Unknown',
                        'create_time': None
                    }
        return None
    
    def check_all_ark_ports(self) -> Dict[str, Dict]:
        """
        Check all ARK default ports.
        
        Returns:
            Dict mapping port names to availability status and process info
        """
        results = {}
        
        for service, port in self.DEFAULT_PORTS.items():
            available = self.is_port_available(port)
            process_info = None if available else self.get_process_on_port(port)
            
            results[service] = {
                'port': port,
                'available': available,
                'process': process_info
            }
        
        return results
    
    def get_remediation_guidance(self, port: int, process_info: Optional[Dict]) -> str:
        """
        Provide remediation guidance for port conflicts.
        
        Args:
            port: Conflicting port number
            process_info: Information about process using the port
            
        Returns:
            Human-readable remediation steps
        """
        if not process_info:
            return f"Port {port} appears busy but process could not be identified."
        
        pid = process_info.get('pid')
        name = process_info.get('name', 'Unknown')
        cmdline = process_info.get('cmdline', '')
        
        guidance = [
            f"Port {port} is currently in use:",
            f"  Process: {name} (PID: {pid})",
            f"  Command: {cmdline}",
            "",
            "Remediation options:",
        ]
        
        # Detect common scenarios
        if 'python' in name.lower() or 'uvicorn' in cmdline.lower():
            guidance.extend([
                f"  1. Stop the existing Python/Uvicorn process:",
                f"     kill {pid}",
                f"  2. Or use arkstop.sh to stop all ARK services",
                f"  3. Check for zombie processes: ps aux | grep {port}"
            ])
        
        elif 'node' in name.lower() or 'vite' in cmdline.lower():
            guidance.extend([
                f"  1. Stop the existing Node.js/Vite process:",
                f"     kill {pid}",
                f"  2. Or terminate from the terminal where it's running",
                f"  3. Check package.json scripts for alternative ports"
            ])
        
        elif 'redis' in name.lower():
            guidance.extend([
                f"  1. Use existing Redis instance (recommended)",
                f"  2. Or stop Redis: redis-cli shutdown",
                f"  3. Or change ARK to use different Redis port"
            ])
        
        else:
            guidance.extend([
                f"  1. Terminate the process: kill {pid}",
                f"  2. Or configure ARK to use a different port",
                f"  3. Check if this process is required for your system"
            ])
        
        return '\n'.join(guidance)
    
    def preflight_check(self, verbose: bool = True) -> Tuple[bool, List[str]]:
        """
        Perform comprehensive pre-flight port check for ARK startup.
        
        Args:
            verbose: Print detailed output
            
        Returns:
            Tuple of (all_clear: bool, error_messages: List[str])
        """
        results = self.check_all_ark_ports()
        errors = []
        
        if verbose:
            print("=" * 70)
            print("🔍 ARK Pre-Flight Port Check")
            print("=" * 70)
        
        all_clear = True
        
        for service, info in results.items():
            port = info['port']
            available = info['available']
            process = info['process']
            
            if available:
                if verbose:
                    print(f"✅ {service:12} (port {port:5}) - Available")
            else:
                all_clear = False
                if verbose:
                    print(f"❌ {service:12} (port {port:5}) - IN USE")
                
                error_msg = self.get_remediation_guidance(port, process)
                errors.append(error_msg)
                
                if verbose:
                    print(f"\n{error_msg}\n")
        
        if verbose:
            print("=" * 70)
            if all_clear:
                print("✅ All ports are available. ARK can start safely.")
            else:
                print(f"❌ {len(errors)} port conflict(s) detected. Resolve before starting ARK.")
            print("=" * 70)
        
        return all_clear, errors


def main():
    """CLI for port checking"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="ARK Port Availability Checker")
    parser.add_argument("--port", type=int, help="Check specific port")
    parser.add_argument("--all", action="store_true", help="Check all ARK ports")
    parser.add_argument("--preflight", action="store_true", help="Full pre-flight check")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    
    args = parser.parse_args()
    
    checker = PortChecker()
    
    if args.port:
        available = checker.is_port_available(args.port)
        if not args.quiet:
            if available:
                print(f"✅ Port {args.port} is available")
            else:
                print(f"❌ Port {args.port} is in use")
                process = checker.get_process_on_port(args.port)
                print(checker.get_remediation_guidance(args.port, process))
        sys.exit(0 if available else 1)
    
    elif args.all or args.preflight:
        all_clear, errors = checker.preflight_check(verbose=not args.quiet)
        sys.exit(0 if all_clear else 1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
