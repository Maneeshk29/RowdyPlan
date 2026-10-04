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
