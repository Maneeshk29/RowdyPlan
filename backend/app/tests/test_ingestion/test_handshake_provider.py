"""Tests for Handshake ingestion via Apify."""
from __future__ import annotations

import pytest
import httpx

from app.ingestion.handshake_provider import HandshakeProvider


@pytest.mark.asyncio
async def test_handshake_provider_normalizes_apify_items(monkeypatch):
    provider = HandshakeProvider(actor_id="test~handshake", token="token")

    async def fake_run_apify():
        return [
            {
                "jobId": "hs-123",
                "jobTitle": "Software Engineering Intern",
                "companyName": "Roadrunner Tech",
                "jobDescription": "<p>Build React and Python services using SQL.</p>",
                "qualifications": "Computer Science major; GPA 3.0+; Must be authorized to work in the United States",
                "eligibleMajors": [{"name": "Computer Science"}],
                "graduationYears": ["2027"],
                "locations": [{"name": "San Antonio, TX"}],
                "applyUrl": "https://example.com/apply/hs-123",
                "employmentType": "Internship",
            }
        ]

    monkeypatch.setattr(provider, "_run_apify", fake_run_apify)

    jobs = await provider.fetch_jobs()

    assert len(jobs) == 1
    job = jobs[0]
    assert job["source"] == "handshake"
    assert job["source_id"] == "hs-123"
    assert job["title"] == "Software Engineering Intern"
    assert "python" in [skill.lower() for skill in job["skills"]]
    assert "Computer Science" in job["majors"]
    assert job["minimum_gpa"] == 3.0
    assert job["work_authorization_required"] is True


def test_handshake_provider_normalizes_nested_employer():
    provider = HandshakeProvider(actor_id="test~handshake", token="token")
    job = provider._normalize_handshake_job({
        "jobTitle": "Python Intern", "employer": {"id": "company-1", "name": "Test Employer"},
        "jobDescription": "Build Python services.",
    })
    assert job["organization"] == "Test Employer"


def test_reingestion_preserves_opportunity_identity(monkeypatch):
    from app.api.mock_store import store

    monkeypatch.setattr(store, "opportunities", [])
    original, created = store.upsert_opportunity({
        "id": "original-id", "source": "handshake", "source_id": "hs-1", "title": "Python Intern",
    })
    assert created
    updated, created = store.upsert_opportunity({
        "id": "new-normalization-id", "source": "handshake", "source_id": "hs-1", "title": "Updated Python Intern",
    })
    assert not created
    assert updated["id"] == original["id"] == "original-id"
    assert updated["title"] == "Updated Python Intern"
    assert len(store.opportunities) == 1


def test_maximedupre_actor_output_keeps_job_description_and_filters():
    provider = HandshakeProvider(actor_id="maximedupre~handshake-jobs-scraper", token="test-token")
    job = provider._normalize_handshake_job({
        "id": "actor-job-123",
        "url": "https://app.joinhandshake.com/public/jobs/123",
        "title": "Accounting Intern",
        "employer": {"name": "Test Employer", "industry": "Accounting"},
        "roleTypes": ["Accounting"],
        "employmentTypes": ["internship"],
        "locations": ["San Antonio, Texas"],
        "workplace": "hybrid",
        "compensation": {"minAmount": 18, "maxAmount": 22, "currency": "USD", "cadence": "hour"},
        "descriptionText": "Use Excel to reconcile accounts. GPA 3.0+.",
        "descriptionHtml": "<p>Use Excel to reconcile accounts. GPA 3.0+.</p>",
        "postedAt": "2026-10-01T14:30:00Z",
        "expiresAt": "2026-12-01T14:30:00Z",
        "collectedAt": "2026-10-04T14:30:00Z",
    })
    assert job["description"] == "Use Excel to reconcile accounts. GPA 3.0+."
    assert "excel" in job["skills"]
    assert job["minimum_gpa"] == 3.0
    assert job["employment_type"] == "internship"
    assert job["location"] == "San Antonio, Texas / hybrid"
    assert job["industry"] == "Accounting"
    assert job["compensation"] == "USD 18-22/hour"
    assert job["source_id"] == "actor-job-123"
    assert job["deadline"].startswith("2026-12-01")


@pytest.mark.asyncio
@pytest.mark.parametrize("collection, identifier", [("actors", "maximedupre~handshake-jobs-scraper"), ("actor-tasks", "task-123")])
async def test_apify_request_uses_bearer_token_and_actor_input(monkeypatch, collection, identifier):
    original_client = httpx.AsyncClient
    observed = []

    def handle_request(request):
        import json

        observed.append(request)
        assert request.headers["authorization"] == "Bearer test-token"
        assert "token" not in request.url.params
        assert request.url.path == f"/v2/{collection}/{identifier}/run-sync-get-dataset-items"
        assert json.loads(request.content) == {"keywords": ["accounting intern"], "maxDiscoveryItems": 10}
        return httpx.Response(200, json=[{"title": "Accounting Intern", "descriptionText": "Use Excel."}])

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(handle_request), **kwargs))
    provider = HandshakeProvider(token="test-token")
    provider.actor_id = identifier if collection == "actors" else None
    provider.task_id = identifier if collection == "actor-tasks" else None
    provider.actor_input = {"keywords": ["accounting intern"], "maxDiscoveryItems": 10}
    jobs = await provider.fetch_jobs()
    assert len(observed) == 1
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Accounting Intern"


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["latest_actor", "latest_task", "dataset"])
async def test_existing_run_import_only_reads_dataset(monkeypatch, mode):
    original_client = httpx.AsyncClient
    observed = []
    expected_path = {
        "latest_actor": "/v2/actors/test~handshake/runs/last/dataset/items",
        "latest_task": "/v2/actor-tasks/task-123/runs/last/dataset/items",
        "dataset": "/v2/datasets/dataset-123/items",
    }[mode]

    def handle_request(request):
        observed.append(request)
        assert request.method == "GET"
        assert request.url.path == expected_path
        assert request.headers["authorization"] == "Bearer test-token"
        assert "token" not in request.url.params
        if mode != "dataset":
            assert request.url.params["status"] == "SUCCEEDED"
        return httpx.Response(200, json=[{
            "id": "hs-123", "title": "Accounting Intern", "employer": {"name": "Test Employer"},
            "descriptionText": "Use Excel.", "url": "https://app.joinhandshake.com/public/jobs/123",
        }])

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(handle_request), **kwargs))
    provider = HandshakeProvider(token="test-token", dataset_id="dataset-123" if mode == "dataset" else None,
                                 use_latest_run=mode != "dataset")
    provider.actor_id = "test~handshake" if mode == "latest_actor" else None
    provider.task_id = "task-123" if mode == "latest_task" else None
    jobs = await provider.fetch_all()
    assert len(observed) == 1
    assert len(jobs) == 1
    assert jobs[0]["source"] == "handshake"
    assert jobs[0]["source_id"] == "hs-123"


@pytest.mark.asyncio
async def test_latest_run_reports_missing_successful_run(monkeypatch):
    original_client = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(404, json={"error": {"type": "not-found"}}))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original_client(transport=transport, **kwargs))
    provider = HandshakeProvider(actor_id="test~handshake", token="test-token", use_latest_run=True)
    with pytest.raises(ValueError, match="No successful Handshake run"):
        await provider.fetch_jobs()
