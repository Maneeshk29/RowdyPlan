"""Tests for the Career Center console and student engagement endpoints."""
from __future__ import annotations

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

STAFF_KEY = "test-staff-key"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def staff_key(monkeypatch):
    monkeypatch.setattr(settings, "STAFF_ACCESS_KEY", STAFF_KEY)
    return {"X-Staff-Key": STAFF_KEY}


@pytest.fixture
def student_id(client):
    response = client.post("/api/students/profile", json={
        "major": "Computer Science", "year": "Senior", "graduation_date": "May 2026", "current_goal": "full_time",
        "skills": ["python", "sql"], "career_interests": ["Data Analyst"],
    })
    assert response.status_code == 201
    return response.json()["id"]


def test_console_defaults_to_demo_cohort(client):
    access = client.get("/api/career-center/access").json()
    assert access["scope"] == "demo"
    overview = client.get("/api/career-center/overview").json()
    assert overview["scope"] == "demo"
    assert overview["students"]["total"] == 240
    assert overview["outcomes"]["outcomes_reported"] > 0
    assert 0 <= overview["outcomes"]["degree_level_rate"] <= 100
    assert overview["by_program"] and overview["top_skill_gaps"] and overview["events"]


def test_demo_cohort_is_deterministic(client):
    first = client.get("/api/career-center/overview").json()
    second = client.get("/api/career-center/overview").json()
    assert first["outcomes"] == second["outcomes"]


def test_real_students_never_appear_without_staff_key(client, student_id):
    caseload = client.get("/api/career-center/caseload?limit=1000").json()
    assert all(row["student_id"].startswith("demo-") for row in caseload["students"])
    assert client.get(f"/api/career-center/students/{student_id}/brief").status_code == 404


def test_wrong_staff_key_is_rejected(client, staff_key):
    response = client.get("/api/career-center/overview", headers={"X-Staff-Key": "wrong"})
    assert response.status_code == 401


def test_key_without_configuration_is_rejected(client):
    response = client.get("/api/career-center/overview", headers={"X-Staff-Key": "anything"})
    assert response.status_code == 401


def test_live_scope_shows_real_outcomes_and_brief(client, staff_key, student_id):
    outcome = client.post("/api/outcomes", json={
        "student_id": student_id, "outcome_type": "full_time", "employer": "USAA",
        "title": "Data Analyst", "degree_required": True, "salary": 68000,
    })
    assert outcome.status_code == 201

    overview = client.get("/api/career-center/overview", headers=staff_key).json()
    assert overview["scope"] == "live"
    assert overview["outcomes"]["outcomes_reported"] >= 1
    assert all(not s.startswith("demo-") for s in
               [r["student_id"] for r in client.get("/api/career-center/caseload", headers=staff_key).json()["students"]])

    brief = client.get(f"/api/career-center/students/{student_id}/brief", headers=staff_key).json()
    assert brief["outcome"]["employer"] == "USAA"
    assert brief["talking_points"]
    assert "advisor decides" in brief["review_note"]

    csv_text = client.get("/api/career-center/outcomes.csv", headers=staff_key).text
    assert csv_text.splitlines()[0].startswith("student_id,name,college,major")
    assert student_id in csv_text


def test_still_seeking_clears_job_fields(client, student_id):
    record = client.post("/api/outcomes", json={
        "student_id": student_id, "outcome_type": "still_seeking", "employer": "Ignored", "salary": 50000,
    }).json()
    assert record["employer"] == "" and record["salary"] is None


def test_outcome_validation(client, student_id):
    assert client.post("/api/outcomes", json={"student_id": student_id, "outcome_type": "astronaut"}).status_code == 422
    assert client.post("/api/outcomes", json={"student_id": "missing", "outcome_type": "full_time"}).status_code == 404


def test_activity_requires_real_student(client, student_id):
    assert client.post("/api/activity", json={"student_id": student_id, "kind": "resume_analyzed"}).status_code == 201
    assert client.post("/api/activity", json={"student_id": "demo-001", "kind": "resume_analyzed"}).status_code == 404
    assert client.post("/api/activity", json={"student_id": student_id, "kind": "hacked"}).status_code == 422


def test_event_check_in_flow(client, staff_key, student_id):
    event = client.post("/api/career-center/events", headers=staff_key, json={"title": "Spring Career Fair"}).json()
    assert event["is_demo"] is False
    assert event["check_in_path"] == f"/?checkin={event['id']}&code={event['check_in_code']}"

    public = client.get(f"/api/events/{event['id']}").json()
    assert "check_in_code" not in public

    wrong = client.post(f"/api/events/{event['id']}/check-in", json={"student_id": student_id, "code": "ZZZZZZ"})
    assert wrong.status_code == 403

    first = client.post(f"/api/events/{event['id']}/check-in",
                        json={"student_id": student_id, "code": event["check_in_code"].lower()}).json()
    assert first["already_checked_in"] is False
    again = client.post("/api/events/check-in", json={"student_id": student_id, "code": event["check_in_code"]}).json()
    assert again["already_checked_in"] is True

    events = client.get("/api/career-center/events", headers=staff_key).json()
    created = next(e for e in events if e["id"] == event["id"])
    assert created["check_ins"] == 1


def test_demo_events_stay_out_of_live_scope(client, staff_key):
    demo_event = client.post("/api/career-center/events", json={"title": "Demo Workshop"}).json()
    assert demo_event["is_demo"] is True
    live_ids = {e["id"] for e in client.get("/api/career-center/events", headers=staff_key).json()}
    assert demo_event["id"] not in live_ids


def test_plan_generation_records_summary(client):
    from app.api.mock_store import store
    plan = client.post("/api/rowdy-plan/generate-inline", json={
        "major": "Computer Science", "year": "Junior", "skills": ["python"], "opportunity_source": "utsa",
    }).json()
    summary = store.plan_summaries[plan["student_id"]]
    assert "profile_strength" in summary and "skill_gaps" in summary
    assert any(a["kind"] == "plan_generated" for a in store.list_activities(plan["student_id"]))


def test_console_markup_present(client):
    html = client.get("/", headers={"Accept": "text/html"}).text
    page = BeautifulSoup(html, "html.parser")
    assert page.select_one("#view-career-center") is not None
    for pane in ("overview", "caseload", "events", "reports"):
        assert page.select_one(f"#cc-pane-{pane}") is not None
    assert page.select_one("#outcome-form") is not None
    assert page.select_one("#checkin-banner").has_attr("hidden")
    assert page.select_one("#trustModal") is not None
    # Console tiles must not reuse classes the student dashboard queries globally.
    assert not page.select("#view-career-center .metric-tile, #view-career-center .app-tab")
