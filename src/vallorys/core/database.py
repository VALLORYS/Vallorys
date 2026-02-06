"""Database connection and session management."""

from typing import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from vallorys.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Create async engine
engine = create_async_engine(
    str(settings.database_url),
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


async def init_database() -> None:
    """Initialize database connection."""
    logger.info("Initializing database connection")
    # In production, use Alembic migrations instead
    async with engine.begin() as conn:
        # Only for development - create tables
        if settings.app_env == "development":
            await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


async def close_database() -> None:
    """Close database connection."""
    logger.info("Closing database connection")
    await engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class TenantSession:
    """Context manager for tenant-scoped database sessions."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.schema = f"tenant_{tenant_id}"

    async def __aenter__(self) -> AsyncSession:
        self.session = async_session_factory()
        # Set search path to tenant schema
        await self.session.execute(
            f"SET search_path TO {self.schema}, public"  # noqa: S608
        )
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()
