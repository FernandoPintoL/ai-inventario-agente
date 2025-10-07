#!/usr/bin/env python3
"""
Intelligent Agent Main Application

A FastAPI application that provides natural language to SQL conversion
using OpenAI and Langchain for inventory management queries.
"""

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from app.api import router
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import IntelligentAgentException
from app.database import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger = setup_logging()
    logger.info("="*70)
    logger.info("Starting Intelligent Agent application...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Port: {settings.port}")
    logger.info(f"Database Host: {settings.db_host}")
    logger.info("="*70)

    # Test database connection (non-blocking)
    try:
        logger.info("Testing database connection...")
        tables = db_manager.langchain_db.get_usable_table_names()
        logger.info(f"✅ Database connected successfully. Available tables: {len(tables)}")
    except Exception as e:
        logger.warning(f"⚠️  Database connection failed: {e}")
        logger.warning("Application will start anyway. Database features may be limited.")
        # NO raise - permitir que la app inicie sin DB

    # Iniciar scheduler de alertas (completamente opcional)
    try:
        logger.info("Starting stock monitor scheduler...")
        from app.scheduler import stock_scheduler
        stock_scheduler.start()
        logger.info("✅ Stock monitor scheduler started successfully")
    except Exception as e:
        logger.warning(f"⚠️  Failed to start stock monitor scheduler: {e}")
        logger.warning("Scheduler disabled. Manual alerts only.")
        # No raise - el scheduler es opcional

    logger.info("="*70)
    logger.info("✅ Application startup complete - Ready to accept requests")
    logger.info("="*70)

    yield

    # Shutdown
    logger.info("="*70)
    logger.info("Shutting down Intelligent Agent application...")
    logger.info("="*70)

    # Detener scheduler
    try:
        from app.scheduler import stock_scheduler
        stock_scheduler.stop()
        logger.info("Stock monitor scheduler stopped")
    except Exception as e:
        logger.warning(f"Error stopping scheduler: {e}")

    try:
        db_manager.close()
        logger.info("Database connection closed")
    except Exception as e:
        logger.warning(f"Error closing database: {e}")

    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Configure servers based on environment
    servers = []
    if settings.is_production:
        servers.append({"url": settings.base_url, "description": "Production server"})
    else:
        servers.append({"url": settings.base_url, "description": "Development server"})

    app = FastAPI(
        title="Intelligent Agent API",
        description="Natural language to SQL conversion service for inventory management",
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,  # Disable docs in production
        redoc_url="/redoc" if not settings.is_production else None,  # Disable redoc in production
        openapi_url="/openapi.json",
        lifespan=lifespan,
        servers=servers
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Configure trusted hosts based on environment
    trusted_hosts = settings.allowed_hosts_list
    if settings.is_production:
        trusted_hosts = trusted_hosts + ["*.railway.app"]
    else:
        trusted_hosts = trusted_hosts + ["*"]

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=trusted_hosts
    )

    # Include routers
    app.include_router(router)

    # Global exception handler
    @app.exception_handler(IntelligentAgentException)
    async def intelligent_agent_exception_handler(request: Request, exc: IntelligentAgentException):
        logger = get_logger("main")
        logger.error(f"Application exception: {exc.message}")
        return JSONResponse(
            status_code=500,
            content={
                "error": exc.message,
                "error_type": exc.__class__.__name__,
                "details": exc.details
            }
        )

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "service": "Intelligent Agent API",
            "version": "1.0.0",
            "description": "Natural language to SQL conversion service",
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "health": "/api/v1/health",
                "query": "/api/v1/query"
            }
        }

    # Legacy endpoint for backward compatibility
    @app.post("/human_query", include_in_schema=False)
    async def legacy_human_query(request: Request):
        """Legacy endpoint for backward compatibility."""
        logger = get_logger("main")
        logger.warning("Using deprecated endpoint /human_query. Use /api/v1/query instead.")

        # Redirect to new endpoint
        body = await request.body()
        headers = dict(request.headers)

        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.server_url}/api/v1/query",
                content=body,
                headers=headers
            )
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )

    return app


def main():
    """Main entry point for running the application."""
    try:
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)

        # Create application
        app = create_application()

        # Configure uvicorn based on environment
        uvicorn_config = {
            "host": settings.host,
            "port": settings.port,
            "log_level": settings.log_level.lower(),
            "access_log": True,
        }

        # Development-specific settings
        if settings.is_development:
            uvicorn_config.update({
                "app": "main:create_application",
                "factory": True,
                "reload": True,  # Auto-reload on code changes
                "reload_dirs": ["app", "config"],  # Watch these directories
            })
        else:
            # Production-specific settings
            uvicorn_config.update({
                "app": app,
                "reload": False,
                "workers": 1,  # Railway handles scaling
                "loop": "uvloop",  # Better performance
                "http": "httptools",  # Better performance
            })

        print(f"Starting Intelligent Agent API on {settings.environment} environment")
        print(f"Server running at: {settings.base_url}")

        # Run the application
        uvicorn.run(**uvicorn_config)

    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()