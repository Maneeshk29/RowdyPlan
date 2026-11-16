from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app


def test_missions_start_empty_and_plan_has_source_area():
    client = TestClient(app)
    html = client.get("/", headers={"Accept": "text/html"}).text
    page = BeautifulSoup(html, "html.parser")
    assert page.select("#mission-items .mission-card") == []
    assert page.select_one("#mission-count").has_attr("hidden")
    assert page.select_one("#mission-count").get_text() == "0"
    assert page.select_one("#missions-empty h2").get_text() == "No active missions"
    assert page.select_one("#active-mission-metric").get_text() == "0"
    assert page.select_one("#plan-source-items") is not None
    assert page.select_one('.source-resource a')["href"] == "https://www.instagram.com/acmutsa/"
    for icon in ("plus", "trash-2"):
        assert client.get(f"/assets/icons/{icon}.svg").status_code == 200


def test_onboarding_and_sync_do_not_depend_on_previous_instance():
    html = TestClient(app).get("/", headers={"Accept": "text/html"}).text
    onboarding = html.split("async function finishOnboardingToDashboard()", 1)[1].split("function addGenStep", 1)[0]
    sync = html.split("async function syncHandshakeJobs()", 1)[1].split("function updateDossierTab", 1)[0]
    assert "/admin/ingest" not in onboarding
    assert "/rowdy-plan/generate-inline" in onboarding
    assert "/rowdy-plan/generate-inline" in sync
    assert "Object.assign({}, currentProfile" in sync
