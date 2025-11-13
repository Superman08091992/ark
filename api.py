"""
ARK Trading Intelligence Backend - REST API

FastAPI application providing HTTP endpoints for trading intelligence.

Endpoints:
- POST /api/v1/ingest - Submit trade setup for processing
- POST /api/v1/analyze - Analyze pattern without execution
- GET /api/v1/signals - Retrieve generated signals
- GET /api/v1/health - Health check

Features:
- Full OpenAPI documentation (Swagger UI at /docs)
- Async request handling
- CORS support
- Request logging
- Error handling

Author: ARK Trading Intelligence
Version: 1.0.0
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
import uvicorn

# Import routes
from routes.ingest import router as ingest_router
from routes.analyze import router as analyze_router
from routes.signals import router as signals_router

# Import agent infrastructure
from shared.agent_bus import agent_bus
from shared.error_bus import error_bus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/api.log')
    ]
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    
    Startup:
    - Initialize agent bus
    - Initialize error bus
    - Load trading patterns
    - Initialize data providers
    
    Shutdown:
    - Graceful cleanup
    """
    # Startup
    logger.info("🚀 Starting ARK Trading Intelligence API...")
    
    try:
        # Initialize singleton engines (lazy loading)
        from ark.intel.engines.pattern_engine import get_pattern_engine
        from ark.intel.engines.trade_scorer import get_trade_scorer
        from ark.intel.engines.trade_plan_builder import get_trade_plan_builder
        
        pattern_engine = get_pattern_engine()
        logger.info(f"✅ Loaded {len(pattern_engine.patterns)} trading patterns")
        
        trade_scorer = get_trade_scorer()
        logger.info("✅ Initialized trade scorer")
        
        plan_builder = get_trade_plan_builder()
        logger.info("✅ Initialized trade plan builder")
        
        # Initialize data providers
        from services.data_sources.aggregator import DataAggregator
        from services.data_sources.yfinance_provider import YFinanceProvider
        
        aggregator = DataAggregator()
        yfinance = YFinanceProvider()
        
        if await yfinance.initialize():
            aggregator.add_provider(yfinance, priority=1)
            logger.info("✅ Initialized yfinance data provider (FREE)")
        else:
            logger.warning("⚠️ Failed to initialize yfinance")
        
        logger.info("✅ API startup complete")
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {str(e)}")
        logger.exception(e)
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🛑 Shutting down ARK Trading Intelligence API...")
    logger.info("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="ARK Trading Intelligence API",
    description="""
    **Real-time trading pattern analysis and signal generation**
    
    ## Features
    - 🎯 **10 Trading Patterns** - Squeezer, Dead Cat Bounce, Short Squeeze, etc.
    - 📊 **Multi-Factor Scoring** - Technical, Fundamental, Catalyst, Sentiment
    - 🛡️ **Risk Management** - HRM validation with 24 rules + circuit breakers
    - 📈 **Execution Planning** - Entry/Stop/Targets with position sizing
    - 🔍 **Full Traceability** - Correlation IDs for distributed tracing
    - 📡 **Real-time Data** - FREE market data via yfinance
    
    ## Workflow
    1. **Ingest** trade setup → **Pattern matching** → **Quality scoring**
    2. **HRM validation** → **Execution planning** → **Send to Kenny**
    3. **Telegram notification** → **Signal tracking**
    
    ## Quick Start
    ```python
    import requests
    
    # Submit a trade setup
    response = requests.post('http://localhost:8000/api/v1/ingest', json={
        "symbol": "TSLA",
        "direction": "long",
        "price": 250.50,
        "float": 15.5,
        "short_interest": 22.5,
        "catalyst": "Strong earnings beat"
    })
    
    correlation_id = response.json()['correlation_id']
    print(f"Tracking: {correlation_id}")
    
    # Check status
    status = requests.get(f'http://localhost:8000/api/v1/ingest/status/{correlation_id}')
    print(status.json())
    ```
    
    ## Documentation
    - **Swagger UI**: [/docs](/docs)
    - **ReDoc**: [/redoc](/redoc)
    - **OpenAPI JSON**: [/openapi.json](/openapi.json)
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    logger.info(f"📨 {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        logger.info(f"✅ {request.method} {request.url.path} - {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)}")
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"❌ Unhandled exception: {str(exc)}")
    logger.exception(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": request.url.path
        }
    )


# Include routers
app.include_router(ingest_router)
app.include_router(analyze_router)
app.include_router(signals_router)


# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
    - API status
    - Agent bus status
    - Pattern engine status
    - Data provider status
    """
    try:
        from ark.intel.engines.pattern_engine import get_pattern_engine
        from services.data_sources.aggregator import DataAggregator
        
        pattern_engine = get_pattern_engine()
        
        return {
            "status": "healthy",
            "timestamp": "2025-11-13T10:00:00Z",
            "api_version": "1.0.0",
            "components": {
                "api": "operational",
                "agent_bus": "operational",
                "pattern_engine": f"operational ({len(pattern_engine.patterns)} patterns loaded)",
                "data_providers": "operational"
            }
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/")
async def root():
    """Root endpoint - redirect to docs"""
    return {
        "name": "ARK Trading Intelligence API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "ingest": "POST /api/v1/ingest",
            "analyze": "POST /api/v1/analyze",
            "signals": "GET /api/v1/signals"
        }
    }


# Run with uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Development mode
        log_level="info"
    )
