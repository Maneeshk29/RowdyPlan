"""Read-only source refreshes for serverless cold starts and periodic cache expiry."""
from __future__ import annotations

import asyncio
import logging
import time
import weakref
from datetime import datetime, timezone

from app.api.mock_store import store
from app.core.config import settings
from app.ingestion.campus_provider import ACMInstagramProvider, RowdyLinkProvider
from app.ingestion.handshake_provider import HandshakeProvider

logger = logging.getLogger(__name__)
_cache: dict[str, dict] = {}
_locks = weakref.WeakKeyDictionary()


async def ensure_source(source: str) -> dict:
    existing = store.list_opportunities(filters={"source": source}, limit=None)
    if not settings.AUTO_SYNC_OPPORTUNITIES:
        return {"source": source, "status": "manual", "count": len(existing)}
    if source == "handshake":
        if not settings.APIFY_API_TOKEN or not (settings.APIFY_HANDSHAKE_ACTOR_ID or settings.APIFY_HANDSHAKE_TASK_ID):
            return {"source": source, "status": "unconfigured", "count": len(existing)}
        provider = HandshakeProvider(use_latest_run=True, timeout_seconds=min(settings.APIFY_TIMEOUT_SECONDS, 30))
    elif source == "rowdylink":
        provider = RowdyLinkProvider()
    elif source == "instagram_acmutsa":
        if not settings.APIFY_ACM_INSTAGRAM_DATASET_ID:
            return {"source": source, "status": "unconfigured", "count": len(existing)}
        provider = ACMInstagramProvider()
    else:
        return {"source": source, "status": "manual", "count": len(existing)}

    lock = _locks.setdefault(asyncio.get_running_loop(), asyncio.Lock())
    async with lock:
        cached = _cache.get(source)
        existing = store.list_opportunities(filters={"source": source}, limit=None)
        if cached and time.monotonic() < cached["retry_at"] and (existing or cached["count"] == 0):
            return {k: v for k, v in cached.items() if k != "retry_at"}
        try:
            # Never start a paid Actor here. Read the last completed dataset instead.
            items = await asyncio.wait_for(provider.fetch_all(), timeout={"handshake": 30, "rowdylink": 12, "instagram_acmutsa": 10}[source])
            if not items and source == "handshake":
                raise ValueError("The latest Handshake dataset has no usable jobs.")
            for item in items:
                store.upsert_opportunity(item)
            active_ids = {item.get("source_id") or item.get("url") for item in items}
            store.opportunities[:] = [o for o in store.opportunities if o.get("source") != source or (o.get("source_id") or o.get("url")) in active_ids]
            status = {"source": source, "status": "ready", "count": len(items), "checked_at": datetime.now(timezone.utc).isoformat()}
            delay = settings.OPPORTUNITY_CACHE_TTL_SECONDS
        except Exception as error:
            logger.warning("Source refresh failed for %s (%s)", source, type(error).__name__)
            status = {"source": source, "status": "stale" if existing else "unavailable", "count": len(existing), "message": "Source refresh failed. Retry sync or check the provider configuration."}
            delay = 60
        _cache[source] = {**status, "retry_at": time.monotonic() + delay}
        return status


async def ensure_plan_sources(source: str | None) -> list[dict]:
    if source != "handshake":
        return []
    return [await ensure_source(name) for name in ("handshake", "rowdylink", "instagram_acmutsa")]
