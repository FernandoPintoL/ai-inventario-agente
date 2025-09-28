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
    logger.info("Starting Intelligent Agent application...")

    try:
        # Test database connection
        tables = db_manager.langchain_db.get_usable_table_names()
        logger.info(f"Database connected successfully. Available tables: {len(tables)}")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Intelligent Agent application...")
    db_manager.close()
    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Intelligent Agent API",
        description="Natural language to SQL conversion service for inventory management",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        servers=[{"url": settings.server_url, "description": "Development server"}]
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts_list + ["*"]  # Configure for production
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

        # Run the application
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True,
            reload=False  # Set to True for development
        )

    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()