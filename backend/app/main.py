"""
FastAPI application entry point for AgriPulse Backend.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_jobs import router as jobs_router
from app.api.routes_tiles import router as tiles_router
from app.api.routes_stats import router as stats_router
from app.api.routes_alerts import router as alerts_router
from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting AgriPulse Backend...")
    
    # Startup
    settings = get_settings()
    logger.info(f"Environment: {settings.app_env}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AgriPulse Backend...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="AgriPulse API",
        description="Vietnam agricultural monitoring system using Sentinel-2 satellite imagery",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health_router)
    app.include_router(jobs_router)
    app.include_router(tiles_router)
    app.include_router(stats_router)
    app.include_router(alerts_router)
    
    return app


app = create_app()


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "service": "AgriPulse Backend",
        "version": "1.0.0",
        "docs": "/docs",
    }
