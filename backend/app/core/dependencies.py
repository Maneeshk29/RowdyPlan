"""FastAPI dependency injection helpers."""

from typing import AsyncGenerator, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.database.session import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session, ensuring it is closed afterwards."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_settings() -> Settings:
    """Return the application settings singleton."""
    return settings


async def get_redis() -> Optional[object]:
    """Return a Redis connection, or None if Redis is unavailable.

    This is intentionally lenient so the app can start without Redis
    (e.g. during local development or testing).
    """
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        # Quick connectivity check
        await client.ping()
        return client
    except Exception:
        return None
