"""
Routes Package

HTTP REST API endpoints for ARK Trading Intelligence Backend.

Available Endpoints:
- POST /api/v1/ingest - Submit trade setup for processing
- POST /api/v1/analyze - Analyze pattern without execution
- GET /api/v1/signals - Retrieve generated signals
- GET /api/v1/health - Health check endpoint

Author: ARK Trading Intelligence
Version: 1.0.0
"""

from .ingest import router as ingest_router
from .analyze import router as analyze_router
from .signals import router as signals_router

__all__ = ['ingest_router', 'analyze_router', 'signals_router']
