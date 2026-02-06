"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vallorys.config import get_settings
from vallorys.api.routes import router as api_router
from vallorys.core.logging import setup_logging
from vallorys.core.database import init_database, close_database
from vallorys.core.redis import init_redis, close_redis

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    setup_logging(settings.log_level, settings.log_format)
    logger.info("Starting VALLORYS", version="1.0.0", env=settings.app_env)

    await init_database()
    await init_redis()

    yield

    # Shutdown
    logger.info("Shutting down VALLORYS")
    await close_database()
    await close_redis()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="VALLORYS API",
        description="AI-powered real estate valuation platform",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(api_router, prefix=settings.api_prefix)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "vallorys.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
    )
