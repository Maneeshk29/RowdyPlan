import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.mock_store import store
from app.core.config import settings
from app.ingestion.handshake_provider import HandshakeProvider
from app.main import app
from app.services import source_sync


@pytest.fixture
def live_sync(monkeypatch):
    monkeypatch.setattr(settings, "AUTO_SYNC_OPPORTUNITIES", True)
    monkeypatch.setattr(settings, "APIFY_API_TOKEN", "test-token")
    monkeypatch.setattr(settings, "APIFY_HANDSHAKE_ACTOR_ID", "test~handshake")
    monkeypatch.setattr(settings, "APIFY_HANDSHAKE_TASK_ID", None)
    monkeypatch.setattr(settings, "APIFY_ACM_INSTAGRAM_DATASET_ID", None)
    monkeypatch.setattr(store, "opportunities", [])
    monkeypatch.setattr(source_sync, "_cache", {})
    monkeypatch.setattr(source_sync, "_locks", {})


@pytest.mark.asyncio
async def test_cold_start_reads_completed_apify_run_and_caches(live_sync, monkeypatch):
    requests = []

    def respond(request):
        requests.append(request)
        assert request.method == "GET"
        assert request.url.params["status"] == "SUCCEEDED"
        assert "/runs/last/dataset/items" in request.url.path
        assert "token" not in request.url.params
        return httpx.Response(200, json=[{"id": 123, "title": "Python Intern", "url": "https://app.joinhandshake.com/jobs/123"}])

    real_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs))
    statuses = await asyncio.gather(source_sync.ensure_source("handshake"), source_sync.ensure_source("handshake"))
    assert len(requests) == 1
    assert statuses[0]["status"] == "ready"
    first_id = store.opportunities[0]["id"]
    store.opportunities.clear()
    await source_sync.ensure_source("handshake")
    assert len(requests) == 2
    assert store.opportunities[0]["id"] == first_id


@pytest.mark.asyncio
async def test_sync_error_retains_existing_jobs_and_reports_stale(live_sync, monkeypatch):
    store.upsert_opportunity({"id": "existing", "title": "Existing Job", "source": "handshake"})

    async def unavailable(self):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(HandshakeProvider, "fetch_all", unavailable)
    result = await source_sync.ensure_source("handshake")
    assert result["status"] == "stale"
    assert store.opportunities[0]["id"] == "existing"
    assert "provider unavailable" not in result["message"]


@pytest.mark.asyncio
async def test_empty_dataset_does_not_delete_cached_jobs(live_sync, monkeypatch):
    store.upsert_opportunity({"id": "existing", "title": "Existing Job", "source": "handshake"})

    async def empty(self):
        return []

    monkeypatch.setattr(HandshakeProvider, "fetch_all", empty)
    assert (await source_sync.ensure_source("handshake"))["status"] == "stale"
    assert len(store.opportunities) == 1


def test_inline_plan_loads_jobs_in_same_request(live_sync, monkeypatch):
    async def jobs(self):
        return [self._normalize_handshake_job({"id": 42, "title": "Python Intern", "skills": ["python"], "url": "https://app.joinhandshake.com/jobs/42"})]

    async def campus(self):
        return []

    monkeypatch.setattr(HandshakeProvider, "fetch_all", jobs)
    monkeypatch.setattr(source_sync.RowdyLinkProvider, "fetch_all", campus)
    response = TestClient(app).post("/api/rowdy-plan/generate-inline", json={"major": "Computer Science", "skills": ["python"], "opportunity_source": "handshake"})
    assert response.status_code == 200
    plan = response.json()
    assert len(plan["job_matches"]) == 1
    assert plan["job_matches"][0]["source_kind"] == "scraped"
    assert plan["job_matches"][0]["source_label"] == "Handshake"
    assert plan["source_status"][0]["status"] == "ready"
    assert plan["source_status"][2]["status"] == "unconfigured"


@pytest.mark.asyncio
async def test_successful_refresh_removes_no_longer_listed_jobs(live_sync, monkeypatch):
    store.upsert_opportunity({"id": "old", "source_id": "old", "title": "Removed", "source": "handshake"})

    async def updated(self):
        return [{"id": "new", "source_id": "new", "title": "New", "source": "handshake"}]

    monkeypatch.setattr(HandshakeProvider, "fetch_all", updated)
    await source_sync.ensure_source("handshake")
    assert [job["id"] for job in store.opportunities] == ["new"]
