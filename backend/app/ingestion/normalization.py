"""Opportunity normalization and deduplication utilities."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any


def normalize_opportunity(raw: dict, source: str, opp_type: str) -> dict:
    """Convert raw opportunity data to standard schema."""
    return {
        "id": raw.get("id") or str(uuid.uuid4()),
        "type": opp_type,
        "title": raw.get("title", "Untitled"),
        "description": raw.get("description", ""),
        "organization": raw.get("organization", raw.get("company", "")),
        "skills": raw.get("skills", []),
        "requirements": raw.get("requirements", []),
        "majors": raw.get("majors", []),
        "graduation_years": raw.get("graduation_years", []),
        "location": raw.get("location", ""),
        "deadline": raw.get("deadline"),
        "url": raw.get("url", ""),
        "source": source,
        "source_timestamp": raw.get("source_timestamp", datetime.utcnow().isoformat()),
        "expiration_date": raw.get("expiration_date"),
        "minimum_gpa": raw.get("minimum_gpa"),
        "work_authorization_required": raw.get("work_authorization_required", False),
        "ingestion_status": "active",
    }


def deduplicate(opportunities: list[dict]) -> list[dict]:
    """Remove duplicate opportunities by source id/url, then title + organization."""
    seen = set()
    unique = []
    for opp in opportunities:
        source_id = str(opp.get("source_id") or "").lower().strip()
        url = str(opp.get("url") or "").lower().strip()
        if source_id:
            key = ("source_id", source_id)
        elif url:
            key = ("url", url)
        else:
            key = (
                "title_org",
                opp.get("title", "").lower().strip(),
                opp.get("organization", "").lower().strip(),
            )
        if key not in seen:
            seen.add(key)
            unique.append(opp)
    return unique


def validate_opportunity(opp: dict) -> bool:
    """Check that an opportunity has required fields."""
    required = ["title", "type"]
    for field in required:
        if not opp.get(field):
            return False
    valid_types = {"job", "event", "research", "organization", "program"}
    if opp.get("type") not in valid_types:
        return False
    return True
