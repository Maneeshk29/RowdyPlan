"""Tests for the career matching engine."""
from __future__ import annotations

import pytest
from app.recommendation.career_matcher import CareerMatcher, CAREER_DATABASE


@pytest.fixture
def matcher():
    return CareerMatcher()


def test_match_careers_returns_top5(matcher, sample_student_profile):
    results = matcher.match_careers(sample_student_profile, limit=5)
    assert len(results) <= 5


def test_cs_student_matches_swe(matcher, sample_student_profile):
    results = matcher.match_careers(sample_student_profile, limit=5)
    career_names = [r["career_name"] for r in results]
    assert "Software Engineer" in career_names or "Full Stack Developer" in career_names


def test_data_skills_match_data_careers(matcher):
    student = {
        "major": "Data Science",
        "skills": ["python", "sql", "r", "statistics"],
        "technical_skills": ["pandas", "scikit-learn", "data visualization"],
        "coursework": ["Statistics", "Machine Learning", "Linear Algebra"],
        "career_interests": ["Data Scientist"],
        "industries": ["Technology"],
        "experience": [],
    }
    results = matcher.match_careers(student, limit=5)
    career_names = [r["career_name"] for r in results]
    assert "Data Scientist" in career_names


def test_career_scores_are_deterministic(matcher, sample_student_profile):
    results1 = matcher.match_careers(sample_student_profile)
    results2 = matcher.match_careers(sample_student_profile)
    for r1, r2 in zip(results1, results2):
        assert r1["career_match_score"] == r2["career_match_score"]
        assert r1["career_name"] == r2["career_name"]


def test_career_has_required_fields(matcher, sample_student_profile):
    results = matcher.match_careers(sample_student_profile)
    required_fields = [
        "career_name", "career_match_score", "matching_skills",
        "missing_skills", "relevant_experience", "recommended_courses",
        "recommended_projects", "recommended_events", "recommended_jobs",
        "next_action",
    ]
    for result in results:
        for field in required_fields:
            assert field in result, f"Missing field: {field}"


def test_missing_skills_not_empty_for_partial_match(matcher, sample_student_profile):
    results = matcher.match_careers(sample_student_profile)
    # At least one career should have missing skills (no student has all skills for every career)
    has_missing = any(len(r["missing_skills"]) > 0 for r in results)
    assert has_missing


def test_career_match_scores_in_range(matcher, sample_student_profile):
    results = matcher.match_careers(sample_student_profile)
    for r in results:
        assert 0 <= r["career_match_score"] <= 100


def test_career_database_has_entries():
    assert len(CAREER_DATABASE) >= 10


def test_career_results_sorted_descending(matcher, sample_student_profile):
    results = matcher.match_careers(sample_student_profile)
    scores = [r["career_match_score"] for r in results]
    assert scores == sorted(scores, reverse=True)
