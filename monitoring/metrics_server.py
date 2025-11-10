"""
ARK Metrics HTTP Server

Exposes Prometheus-compatible metrics endpoint and structured JSON metrics API.

Endpoints:
- GET /metrics - Prometheus text format exposition
- GET /metrics/json - Structured JSON format
- GET /slos - Current SLO status
- GET /healthz - Health check (includes metrics health)
- GET /readyz - Readiness check

Author: ARK System
Created: 2025-11-10
"""

import asyncio
import logging
from typing import Dict, Any
import json

try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logging.warning("aiohttp not available, metrics server will not start")

from monitoring.metrics import get_metrics_collector, check_slos, export_prometheus, get_all_metrics

logger = logging.getLogger(__name__)


class MetricsServer:
    """
    HTTP server for exposing metrics.
    
    Runs on port 9090 by default (standard Prometheus port).
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 9090):
        """
        Initialize metrics server.
        
        Args:
            host: Bind address
            port: Bind port (default 9090)
        """
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp required for metrics server")
        
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"MetricsServer initialized on {host}:{port}")
    
    
    def _setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_get("/metrics", self.handle_metrics_prometheus)
        self.app.router.add_get("/metrics/json", self.handle_metrics_json)
        self.app.router.add_get("/slos", self.handle_slos)
        self.app.router.add_get("/healthz", self.handle_health)
        self.app.router.add_get("/readyz", self.handle_ready)
    
    
    async def handle_metrics_prometheus(self, request: web.Request) -> web.Response:
        """
        Handle /metrics endpoint - Prometheus text format.
        
        Returns metrics in Prometheus exposition format.
        """
        try:
            metrics_text = export_prometheus()
            return web.Response(
                text=metrics_text,
                content_type="text/plain; version=0.0.4",
                status=200
            )
        except Exception as e:
            logger.error(f"Error exporting Prometheus metrics: {e}")
            return web.Response(
                text=f"Error: {str(e)}",
                status=500
            )
    
    
    async def handle_metrics_json(self, request: web.Request) -> web.Response:
        """
        Handle /metrics/json endpoint - Structured JSON format.
        
        Returns all metrics in JSON format with statistics.
        """
        try:
            metrics = get_all_metrics()
            return web.json_response(metrics, status=200)
        except Exception as e:
            logger.error(f"Error exporting JSON metrics: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500
            )
    
    
    async def handle_slos(self, request: web.Request) -> web.Response:
        """
        Handle /slos endpoint - SLO status.
        
        Returns current SLO compliance status.
        """
        try:
            slo_status = check_slos()
            return web.json_response(slo_status, status=200)
        except Exception as e:
            logger.error(f"Error checking SLOs: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500
            )
    
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """
        Handle /healthz endpoint - Health check.
        
        Returns 200 if metrics collector is functioning.
        """
        try:
            collector = get_metrics_collector()
            
            # Simple health check - can we get metrics?
            metrics = collector.get_all_metrics()
            
            health = {
                "status": "healthy",
                "timestamp": metrics["timestamp"],
                "metrics_count": (
                    len(metrics.get("counters", {})) +
                    len(metrics.get("gauges", {})) +
                    len(metrics.get("histograms", {}))
                )
            }
            
            return web.json_response(health, status=200)
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return web.json_response(
                {
                    "status": "unhealthy",
                    "error": str(e)
                },
                status=503
            )
    
    
    async def handle_ready(self, request: web.Request) -> web.Response:
        """
        Handle /readyz endpoint - Readiness check.
        
        Returns 200 if system is ready to serve traffic.
        """
        try:
            # Check if we have any recent metrics (last 60 seconds)
            collector = get_metrics_collector()
            metrics = collector.get_all_metrics()
            
            import time
            is_ready = (time.time() - metrics["timestamp"]) < 60
            
            if is_ready:
                return web.json_response(
                    {"status": "ready", "timestamp": metrics["timestamp"]},
                    status=200
                )
            else:
                return web.json_response(
                    {
                        "status": "not_ready",
                        "reason": "No recent metrics",
                        "last_update": metrics["timestamp"]
                    },
                    status=503
                )
        
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return web.json_response(
                {
                    "status": "not_ready",
                    "error": str(e)
                },
                status=503
            )
    
    
    async def start(self):
        """Start the metrics server."""
        if not AIOHTTP_AVAILABLE:
            logger.error("Cannot start metrics server - aiohttp not available")
            return
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        
        logger.info(f"Metrics server started on http://{self.host}:{self.port}")
        logger.info(f"  Prometheus: http://{self.host}:{self.port}/metrics")
        logger.info(f"  JSON: http://{self.host}:{self.port}/metrics/json")
        logger.info(f"  SLOs: http://{self.host}:{self.port}/slos")
    
    
    async def stop(self):
        """Stop the metrics server."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("Metrics server stopped")
    
    
    async def run_forever(self):
        """Start server and run forever."""
        await self.start()
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            logger.info("Metrics server shutdown requested")
        finally:
            await self.stop()


async def main():
    """Main entry point for standalone metrics server."""
    import sys
    import os
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    # Parse command line args
    host = os.environ.get("METRICS_HOST", "0.0.0.0")
    port = int(os.environ.get("METRICS_PORT", "9090"))
    
    # Create and run server
    server = MetricsServer(host=host, port=port)
    
    logger.info(f"Starting ARK Metrics Server on {host}:{port}")
    logger.info("Press Ctrl+C to stop")
    
    try:
        await server.run_forever()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await server.stop()


if __name__ == "__main__":
    if not AIOHTTP_AVAILABLE:
        print("ERROR: aiohttp is required")
        print("Install with: pip install aiohttp")
        import sys
        sys.exit(1)
    
    asyncio.run(main())
