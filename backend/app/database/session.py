"""Async SQLAlchemy engine and session factory.

Gracefully handles missing database drivers so the app can start
in demo/dev mode without PostgreSQL.
"""

import warnings

engine = None
async_session_factory = None

try:
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from app.core.config import settings

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True,
    )

    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
except Exception as e:
    warnings.warn(f"Database engine not available ({e}). Running in demo mode with in-memory store.")


async def create_tables() -> None:
    """Create all tables defined via the DeclarativeBase metadata.

    Skips silently if the database engine is not available.
    """
    if engine is None:
        warnings.warn("Skipping table creation — no database engine available.")
        return

    try:
        from app.database.base import Base  # noqa: F811
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        warnings.warn(f"Could not create tables: {e}")
