"""Read public campus feeds; never invent listings from a recommendation catalog."""
from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.ingestion.normalization import deduplicate, normalize_opportunity


def _date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        result = parsedate_to_datetime(value)
    except (ValueError, TypeError):
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result


class RowdyLinkProvider:
    source = "rowdylink"
    feed_url = "https://rowdylink.utsa.edu/events.rss"

    async def fetch_all(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            response = await client.get(self.feed_url)
            response.raise_for_status()
        return self.parse_feed(response.content)

    def parse_feed(self, content: bytes, now: datetime | None = None) -> list[dict]:
        if len(content) > 8 * 1024 * 1024 or b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
            raise ValueError("RowdyLink returned an unsupported event feed.")
        root = ET.fromstring(content)
        if root.tag != "rss":
            raise ValueError("RowdyLink did not return an RSS feed.")
        now = now or datetime.now(timezone.utc)
        events = []
        for item in root.findall("channel/item"):
            title = item.findtext("title", "").strip()
            url = item.findtext("link", "").strip()
            parsed = urlparse(url)
            if not title or parsed.scheme != "https" or parsed.hostname != "rowdylink.utsa.edu" or not parsed.path.startswith("/event/"):
                continue
            start = _date(item.findtext("{events}start"))
            end = _date(item.findtext("{events}end")) or start
            if not start or not end or end <= now or start > now + timedelta(days=180):
                continue
            if item.findtext("{events}status", "").lower() == "cancelled":
                continue
            soup = BeautifulSoup(item.findtext("description", ""), "html.parser")
            for unwanted in soup(["script", "style"]):
                unwanted.decompose()
            description = soup.select_one(".p-description") or soup
            event = normalize_opportunity({
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, url)),
                "title": title,
                "description": description.get_text(" ", strip=True)[:6000],
                "organization": item.findtext("{events}host", "UTSA"),
                "location": item.findtext("{events}location", "UTSA"),
                "url": url,
                "source_kind": "scraped",
                "source_label": "RowdyLink",
                "expiration_date": end.isoformat(),
            }, self.source, "event")
            event.update({"source_id": url, "starts_at": start.isoformat(), "categories": [c.text or "" for c in item.findall("category")]})
            events.append(event)
        return sorted(deduplicate(events), key=lambda event: event["starts_at"])


class ACMInstagramProvider:
    source = "instagram_acmutsa"

    def __init__(self, dataset_id: str | None = None):
        self.dataset_id = dataset_id or settings.APIFY_ACM_INSTAGRAM_DATASET_ID

    async def fetch_all(self) -> list[dict]:
        if not self.dataset_id or not settings.APIFY_API_TOKEN:
            raise ValueError("Set APIFY_ACM_INSTAGRAM_DATASET_ID and APIFY_API_TOKEN to import ACM UTSA posts.")
        url = f"https://api.apify.com/v2/datasets/{quote(self.dataset_id, safe='')}/items"
        async with httpx.AsyncClient(timeout=min(settings.APIFY_TIMEOUT_SECONDS, 10)) as client:
            response = await client.get(url, headers={"Authorization": f"Bearer {settings.APIFY_API_TOKEN}"}, params={"clean": "true", "format": "json"})
            response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("Instagram dataset must contain a list of posts.")
        return self.normalize_posts(payload)

    def normalize_posts(self, items: list[dict], now: datetime | None = None) -> list[dict]:
        now = now or datetime.now(timezone.utc)
        posts = []
        for item in items:
            if not isinstance(item, dict) or str(item.get("ownerUsername", "")).lower() != "acmutsa":
                continue
            url = str(item.get("url") or "")
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname not in {"instagram.com", "www.instagram.com"} or not parsed.path.startswith(("/p/", "/reel/")):
                continue
            caption = str(item.get("caption") or "").strip()
            posted = _date(item.get("timestamp"))
            if not caption or not posted or posted < now - timedelta(days=60) or posted > now:
                continue
            post = normalize_opportunity({
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, url)),
                "title": caption.splitlines()[0][:160], "description": caption[:6000],
                "organization": "ACM UTSA", "url": url,
                "source_kind": "scraped", "source_label": "Instagram of ACM UTSA",
            }, self.source, "organization")
            post.update({"source_id": url, "posted_at": posted.isoformat()})
            posts.append(post)
        return deduplicate(posts)
