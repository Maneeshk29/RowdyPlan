from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import pytest

from app.ingestion.campus_provider import ACMInstagramProvider, RowdyLinkProvider


NOW = datetime(2030, 10, 4, tzinfo=timezone.utc)


def feed_item(title="Python Workshop", host="ACM UTSA", url="https://rowdylink.utsa.edu/event/123", end=None):
    start = NOW + timedelta(days=1)
    return f'''<item><title>{title}</title><link>{url}</link>
    <description>&lt;div class="p-description"&gt;Learn Python with ACM&lt;/div&gt;</description>
    <e:start>{format_datetime(start)}</e:start><e:end>{format_datetime(end or start + timedelta(hours=1))}</e:end>
    <e:host>{host}</e:host><e:location>UTSA</e:location><e:status>confirmed</e:status></item>'''


def rss(items):
    return f'<rss xmlns:e="events"><channel>{items}</channel></rss>'.encode()


def test_rowdylink_real_provenance_and_stable_ids():
    provider = RowdyLinkProvider()
    events = provider.parse_feed(rss(feed_item() + feed_item()), NOW)
    assert len(events) == 1
    event = events[0]
    assert event["description"] == "Learn Python with ACM"
    assert event["source_kind"] == "scraped"
    assert event["source_label"] == "RowdyLink"
    assert event["source_url"] == "https://rowdylink.utsa.edu/event/123"
    assert event["organization"] == "ACM UTSA"
    assert event["id"] == provider.parse_feed(rss(feed_item()), NOW)[0]["id"]


def test_rowdylink_skips_past_cancelled_invalid_and_offsite_events():
    content = feed_item(end=NOW - timedelta(hours=1))
    content += feed_item(url="https://rowdylink.utsa.edu.evil.test/event/123")
    content += feed_item().replace("confirmed", "cancelled")
    content += feed_item().replace("<e:start>", "<bad>").replace("</e:start>", "</bad>")
    assert RowdyLinkProvider().parse_feed(rss(content), NOW) == []


def test_rowdylink_rejects_entity_expansion_and_non_rss():
    with pytest.raises(ValueError):
        RowdyLinkProvider().parse_feed(b'<!DOCTYPE rss [<!ENTITY a "oops">]><rss/>', NOW)
    with pytest.raises(ValueError):
        RowdyLinkProvider().parse_feed(b"<html/>", NOW)


def test_instagram_only_imports_recent_verified_acm_posts():
    post = {"ownerUsername": "acmutsa", "url": "https://www.instagram.com/p/example/", "timestamp": NOW.isoformat(), "caption": "Python workshop\nJoin ACM UTSA"}
    posts = ACMInstagramProvider().normalize_posts([
        post, post,
        {**post, "ownerUsername": "another_account"},
        {**post, "url": "javascript:alert(1)"},
        {**post, "timestamp": (NOW - timedelta(days=90)).isoformat()},
        {**post, "timestamp": None},
    ], NOW)
    assert len(posts) == 1
    assert posts[0]["source_label"] == "Instagram of ACM UTSA"
    assert posts[0]["source_kind"] == "scraped"
    assert posts[0]["type"] == "organization"
    assert "starts_at" not in posts[0]
