"""Tests for API endpoints using FastAPI TestClient."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def seeded_client(client):
    """Client with seed data loaded."""
    # Seed the database
    response = client.post("/api/admin/seed")
    assert response.status_code == 200
    return client


@pytest.fixture
def student_id(client):
    """Create a student and return their ID."""
    response = client.post("/api/students/profile", json={
        "major": "Computer Science",
        "current_goal": "full_time",
        "skills": ["python", "java", "sql"],
        "technical_skills": ["react", "docker"],
        "coursework": ["Data Structures", "Algorithms"],
        "career_interests": ["Software Engineer"],
        "experience": [
            {"type": "internship", "title": "SWE Intern", "organization": "USAA",
             "description": "Built microservices"}
        ],
    })
    assert response.status_code == 201
    return response.json()["id"]


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "Rowdy Plan"
    assert response.json()["version"] == "1.0.0"


def test_frontend_ai_interview_button(client):
    from bs4 import BeautifulSoup

    response = client.get("/", headers={"Accept": "text/html"})
    assert response.status_code == 200
    page = BeautifulSoup(response.text, "html.parser")
    button = page.select_one('.sidebar-nav button[aria-label="AI Interview"]')
    assert button is not None
    assert button.select_one(".nav-label").get_text(strip=True) == "AI Interview"
    assert button.select_one('[role="tooltip"]').get_text(strip=True) == "AI Interview"
    assert button["onclick"] == "enterDistractionFreeInterview()"
    logo = button.select_one("img.rowdy-logo")
    assert logo is not None
    assert logo["src"] == "/assets/rowdy-logo.png"
    assert logo["width"] == logo["height"] == "24"


def test_sidebar_tooltips_and_resume_tab(client):
    from bs4 import BeautifulSoup

    response = client.get("/", headers={"Accept": "text/html"})
    page = BeautifulSoup(response.text, "html.parser")
    buttons = page.select(".sidebar-nav .nav-btn")
    assert len(buttons) == 7
    for button in buttons:
        label = button["aria-label"]
        assert button.select_one(".nav-label").get_text(strip=True) == label
        assert button.select_one('[role="tooltip"]').get_text(strip=True) == label
        assert page.find(id=button["aria-controls"]) is not None
    resume_button = page.select_one('.sidebar-nav [data-tab="tab-resume"]')
    assert resume_button["aria-label"] == "Resume Optimization Tool"
    assert page.select_one("#tab-resume #resume-editor") is not None
    assert page.select_one("#tab-resume #resume-analyze-button") is not None
    for icon in ("file-search", "upload"):
        assert client.get(f"/assets/icons/{icon}.svg").status_code == 200


def test_interview_video_replaces_simulated_recording(client):
    from bs4 import BeautifulSoup

    response = client.get("/", headers={"Accept": "text/html"})
    page = BeautifulSoup(response.text, "html.parser")
    video = page.select_one("#tab-interview video")
    assert video is not None
    assert video.has_attr("controls") and video.has_attr("playsinline")
    assert not video.has_attr("autoplay")
    assert video["src"] == "/media/rowdy-ai-interview.mp4"
    assert video["poster"] == "/media/rowdy-ai-interview-poster.jpg"
    assert page.find(id="interview-timer") is None
    assert page.find(id="interview-debrief") is None
    assert "Rowdy is listening" not in response.text
    assert "finishInterviewAnswer" not in response.text
    media = client.head(video["src"])
    assert media.status_code == 200
    assert media.headers["content-type"] == "video/mp4"
    assert int(media.headers["content-length"]) > 0
    assert client.head(video["poster"]).headers["content-type"] == "image/jpeg"


@pytest.mark.parametrize("start,end", [(0, 1023), (4096, 5119)])
def test_interview_video_supports_seeking(client, start, end):
    from app.main import FRONTEND_MEDIA
    from pathlib import Path

    path = Path(FRONTEND_MEDIA) / "rowdy-ai-interview.mp4"
    response = client.get("/media/rowdy-ai-interview.mp4", headers={"Range": f"bytes={start}-{end}"})
    assert response.status_code == 206
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-range"] == f"bytes {start}-{end}/{path.stat().st_size}"
    assert len(response.content) == end - start + 1
    with path.open("rb") as source:
        source.seek(start)
        assert response.content == source.read(end - start + 1)


def test_interview_video_rejects_out_of_bounds_range(client):
    url = "/media/rowdy-ai-interview.mp4"
    size = int(client.head(url).headers["content-length"])
    response = client.get(url, headers={"Range": f"bytes={size}-"})
    assert response.status_code == 416


def test_interview_video_conditional_caching(client):
    url = "/media/rowdy-ai-interview.mp4"
    metadata = client.head(url)
    response = client.get(url, headers={"If-None-Match": metadata.headers["etag"]})
    assert response.status_code == 304
    assert response.content == b""


def test_interview_media_does_not_expose_other_files(client):
    assert client.get("/media/missing.mp4").status_code == 404
    assert client.get("/media/%2e%2e/%2e%2e/backend/.env").status_code == 404
    assert client.post("/media/rowdy-ai-interview.mp4").status_code == 405


def test_resume_editor_analysis_workflow(client, student_id):
    resume_text = "EDUCATION\nUTSA Computer Science\nEXPERIENCE\n- Helped with Python reports\nSKILLS\nPython, SQL"
    response = client.put(f"/api/students/{student_id}/profile", json={"resume_text": resume_text})
    assert response.status_code == 200
    response = client.post("/api/resume/analyze", json={"student_id": student_id, "target_career": "Data Scientist"})
    assert response.status_code == 200
    analysis = response.json()
    assert 0 <= analysis["resume_score"] <= 100
    assert analysis["recommended_rewrites"]
    assert "Helped with Python reports" == analysis["recommended_rewrites"][0]["original"]


def test_create_student_profile(client):
    response = client.post("/api/students/profile", json={
        "major": "Computer Science",
        "current_goal": "internship",
        "gpa": 3.5,
        "skills": ["python"],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["major"] == "Computer Science"
    assert data["current_goal"] == "internship"
    assert "id" in data


def test_get_student_profile(client, student_id):
    response = client.get(f"/api/students/{student_id}/profile")
    assert response.status_code == 200
    assert response.json()["id"] == student_id


def test_update_student_profile(client, student_id):
    response = client.put(f"/api/students/{student_id}/profile", json={
        "gpa": 3.8,
        "skills": ["python", "java", "go"],
    })
    assert response.status_code == 200
    assert response.json()["gpa"] == 3.8


def test_get_career_recommendations(seeded_client, student_id):
    response = seeded_client.get(f"/api/careers/recommendations?student_id={student_id}")
    assert response.status_code == 200
    data = response.json()
    assert "career_matches" in data
    assert len(data["career_matches"]) > 0
    assert data["career_matches"][0]["career_match_score"] >= 0


def test_get_job_recommendations(seeded_client, student_id):
    response = seeded_client.get(f"/api/jobs/recommendations?student_id={student_id}")
    assert response.status_code == 200
    data = response.json()
    assert "job_matches" in data


def test_generate_rowdy_plan(seeded_client, student_id):
    response = seeded_client.post("/api/rowdy-plan/generate", json={
        "student_id": student_id,
        "max_career_matches": 3,
        "max_job_matches": 5,
    })
    assert response.status_code == 200
    plan = response.json()
    assert "profile_strength" in plan
    assert "career_matches" in plan
    assert "job_matches" in plan
    assert "timeline" in plan
    assert "next_steps" in plan
    assert "processing_steps" in plan
    assert 0 <= plan["profile_strength"] <= 100


def test_create_opportunity(client):
    response = client.post("/api/admin/opportunities", json={
        "type": "job",
        "title": "Test Job",
        "organization": "Test Corp",
        "skills": ["python"],
    })
    assert response.status_code == 201
    assert response.json()["title"] == "Test Job"


def test_list_opportunities(seeded_client):
    response = seeded_client.get("/api/opportunities")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_record_feedback(client, student_id):
    response = client.post("/api/feedback", json={
        "student_id": student_id,
        "event_type": "job_viewed",
        "entity_id": "opp-123",
        "entity_type": "opportunity",
    })
    assert response.status_code == 201
    assert response.json()["event_type"] == "job_viewed"


def test_upload_resume_rejects_invalid_type(client):
    import io
    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.txt", io.BytesIO(b"text content"), "text/plain")},
    )
    assert response.status_code == 422


def test_missing_student_returns_404(client):
    response = client.get("/api/students/nonexistent-id-12345/profile")
    assert response.status_code == 404


def test_seed_endpoint(client):
    response = client.post("/api/admin/seed")
    assert response.status_code == 200
    data = response.json()
    assert "total_opportunities" in data
    assert data["total_opportunities"] > 0


def test_list_careers(client):
    response = client.get("/api/careers")
    assert response.status_code == 200
    careers = response.json()
    assert isinstance(careers, list)
    assert len(careers) >= 10


def test_search_opportunities(seeded_client):
    response = seeded_client.post("/api/opportunities/search", json={"query": "software"})
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)


@pytest.mark.parametrize("source, expected_count", [("handshake", 1), ("missing", 0)])
def test_inline_plan_filters_listing_source(client, monkeypatch, source, expected_count):
    from app.api.mock_store import store

    mock_listings = [
        {"id": f"demo-{index}", "type": "job", "source": "utsa", "title": "Demo Python Intern",
         "skills": ["python"]}
        for index in range(60)
    ]
    mock_listings.append(
        {"id": "hs-1", "type": "job", "source": "handshake", "title": "Python Intern",
         "skills": ["python"], "url": "https://app.joinhandshake.com/jobs/123"}
    )
    monkeypatch.setattr(store, "opportunities", mock_listings)
    response = client.post("/api/rowdy-plan/generate-inline", json={
        "major": "Computer Science", "skills": ["python"], "opportunity_source": source,
        "include_resume_analysis": False,
    })
    assert response.status_code == 200
    plan = response.json()
    assert plan["opportunity_source"] == source
    assert len(plan["job_matches"]) == expected_count
    if expected_count:
        assert plan["job_matches"][0]["url"] == "https://app.joinhandshake.com/jobs/123"
        assert plan["job_matches"][0]["source"] == "handshake"
        recommendations = client.get("/api/jobs/recommendations", params={
            "student_id": plan["student_id"], "source": source,
        }).json()
        assert len(recommendations["job_matches"]) == 1
        listings = client.get("/api/opportunities", params={"source": source}).json()
        assert [listing["id"] for listing in listings] == ["hs-1"]


def test_plan_preserves_failed_hard_requirement(client, monkeypatch):
    from app.api.mock_store import store

    monkeypatch.setattr(store, "opportunities", [
        {"id": "hs-1", "type": "job", "source": "handshake", "title": "Python Intern",
         "skills": ["python"], "majors": ["Computer Science"], "minimum_gpa": 3.5,
         "graduation_years": ["2027"]},
    ])
    response = client.post("/api/rowdy-plan/generate-inline", json={
        "major": "Computer Science", "skills": ["python"], "gpa": 3.4,
        "graduation_date": "May 2027", "opportunity_source": "handshake",
    })
    match = response.json()["job_matches"][0]
    assert match["qualification_status"] == "NOT_ELIGIBLE"
    assert match["match_score"] <= 39


@pytest.mark.parametrize("options", [{"use_latest_run": True}, {"dataset_id": "dataset-123"}])
def test_import_existing_handshake_output(client, monkeypatch, options):
    from app.api.mock_store import store
    from app.ingestion.handshake_provider import HandshakeProvider

    monkeypatch.setattr(store, "opportunities", [])
    monkeypatch.setattr(store, "ingestion_status", {})

    async def fake_fetch_all(provider):
        assert provider.use_latest_run == options.get("use_latest_run", False)
        assert provider.dataset_id == options.get("dataset_id")
        return [{"id": "hs-1", "type": "job", "source": "handshake", "source_id": "123",
                 "title": "Accounting Intern", "skills": ["excel"],
                 "url": "https://app.joinhandshake.com/public/jobs/123"}]

    monkeypatch.setattr(HandshakeProvider, "fetch_all", fake_fetch_all)
    for expected_added, expected_updated in [(1, 0), (0, 1)]:
        response = client.post("/api/admin/ingest", json={"provider": "handshake", **options})
        assert response.status_code == 200
        assert response.json()["fetched"] == 1
        assert response.json()["added"] == expected_added
        assert response.json()["updated"] == expected_updated
    assert len(store.opportunities) == 1


@pytest.mark.parametrize("options", [{"use_latest_run": "false"}, {"dataset_id": ""}, {"dataset_id": 123}])
def test_import_rejects_invalid_existing_output_options(client, options):
    response = client.post("/api/admin/ingest", json={"provider": "handshake", **options})
    assert response.status_code == 422
