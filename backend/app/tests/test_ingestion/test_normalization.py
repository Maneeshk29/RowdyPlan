"""Tests for opportunity normalization and the UTSA provider."""
from __future__ import annotations

import pytest
import asyncio
from app.ingestion.normalization import normalize_opportunity, deduplicate, validate_opportunity
from app.ingestion.utsa_provider import UTSAProvider


def test_normalize_opportunity_has_required_fields():
    raw = {"title": "SWE Intern", "description": "Build software"}
    normalized = normalize_opportunity(raw, source="utsa", opp_type="job")
    assert "id" in normalized
    assert normalized["type"] == "job"
    assert normalized["title"] == "SWE Intern"
    assert normalized["source"] == "utsa"


def test_deduplicate_removes_duplicates():
    opps = [
        {"title": "SWE Intern", "organization": "USAA", "type": "job"},
        {"title": "SWE Intern", "organization": "USAA", "type": "job"},
        {"title": "Data Analyst", "organization": "H-E-B", "type": "job"},
    ]
    result = deduplicate(opps)
    assert len(result) == 2


def test_deduplicate_case_insensitive():
    opps = [
        {"title": "SWE Intern", "organization": "USAA"},
        {"title": "swe intern", "organization": "usaa"},
    ]
    result = deduplicate(opps)
    assert len(result) == 1


def test_validate_opportunity_rejects_incomplete():
    invalid = {"description": "No title or type"}
    assert not validate_opportunity(invalid)


def test_validate_opportunity_rejects_bad_type():
    invalid = {"title": "Test", "type": "invalid_type"}
    assert not validate_opportunity(invalid)


def test_validate_opportunity_accepts_valid():
    valid = {"title": "SWE Intern", "type": "job"}
    assert validate_opportunity(valid)


@pytest.mark.asyncio
async def test_utsa_provider_returns_data():
    provider = UTSAProvider(use_live_data=False)
    all_opps = await provider.fetch_all()
    assert len(all_opps) > 0

    # Check types are diverse
    types = set(o.get("type") for o in all_opps)
    assert "job" in types
    assert "event" in types
    assert "research" in types
    assert "organization" in types


@pytest.mark.asyncio
async def test_utsa_provider_jobs_not_empty():
    provider = UTSAProvider(use_live_data=False)
    jobs = await provider.fetch_jobs()
    assert len(jobs) >= 10  # We defined 15+ mock jobs


@pytest.mark.asyncio
async def test_utsa_provider_normalized_format():
    provider = UTSAProvider(use_live_data=False)
    jobs = await provider.fetch_jobs()
    for job in jobs:
        assert "title" in job
        assert "type" in job
        assert job["type"] == "job"
        assert "source" in job
        assert job["source"] == "utsa"
