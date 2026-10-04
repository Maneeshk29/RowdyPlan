"""Tests for the job matching engine."""
from __future__ import annotations

import pytest
from app.recommendation.job_matcher import JobMatcher


@pytest.fixture
def matcher():
    return JobMatcher()


def test_score_opportunity_returns_valid_score(matcher, sample_student_profile, sample_opportunity):
    result = matcher.score_opportunity(sample_student_profile, sample_opportunity)
    assert 0 <= result["match_score"] <= 100
    assert "opportunity_id" in result
    assert "matched_skills" in result
    assert "missing_skills" in result


def test_skill_similarity_exact_match(matcher):
    student_skills = ["python", "java", "sql"]
    opp_skills = ["python", "java", "sql"]
    result = matcher._compute_skill_similarity(student_skills, opp_skills)
    # The method returns a tuple: (score, matched, missing)
    score = result[0] if isinstance(result, tuple) else result
    assert score == 100.0


def test_skill_similarity_no_match(matcher):
    student_skills = ["python", "java"]
    opp_skills = ["rust", "haskell", "elixir"]
    result = matcher._compute_skill_similarity(student_skills, opp_skills)
    score = result[0] if isinstance(result, tuple) else result
    assert score == 0.0


def test_skill_similarity_partial(matcher):
    student_skills = ["python", "java", "sql"]
    opp_skills = ["python", "java", "rust", "go"]
    result = matcher._compute_skill_similarity(student_skills, opp_skills)
    score = result[0] if isinstance(result, tuple) else result
    assert 40 <= score <= 60  # 2 out of 4 = 50%


def test_location_match_remote(matcher):
    # The agent's _compute_location_match takes (self, student_prefs, opp_location)
    score = matcher._compute_location_match(["remote"], "Remote")
    assert score == 100.0


def test_location_match_city(matcher):
    score = matcher._compute_location_match(["San Antonio, TX"], "San Antonio, TX")
    assert score == 100.0


def test_location_match_no_preference(matcher):
    score = matcher._compute_location_match([], "San Antonio, TX")
    assert score >= 50.0  # Neutral score for no preference


def test_goal_match_internship(matcher):
    score = matcher._compute_goal_match("internship", "internship")
    assert score >= 80.0


def test_goal_match_exploring(matcher):
    score = matcher._compute_goal_match("exploring", "job")
    assert score >= 40.0  # Exploring matches loosely


def test_rank_opportunities_sorted(matcher, sample_student_profile, mock_opportunities):
    results = matcher.rank_opportunities(sample_student_profile, mock_opportunities)
    scores = [r["match_score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_match_score_is_deterministic(matcher, sample_student_profile, sample_opportunity):
    result1 = matcher.score_opportunity(sample_student_profile, sample_opportunity)
    result2 = matcher.score_opportunity(sample_student_profile, sample_opportunity)
    assert result1["match_score"] == result2["match_score"]
    assert result1["score_breakdown"] == result2["score_breakdown"]


def test_missing_skills_identified(matcher, sample_student_profile, sample_opportunity):
    result = matcher.score_opportunity(sample_student_profile, sample_opportunity)
    # Missing skills should be skills in the opportunity but not in the student
    assert isinstance(result["missing_skills"], list)
    # "agile" is in the opportunity but not in student skills/technical_skills
    assert "agile" in result["missing_skills"]


def test_score_breakdown_keys(matcher, sample_student_profile, sample_opportunity):
    result = matcher.score_opportunity(sample_student_profile, sample_opportunity)
    expected_keys = {"skill", "experience", "education", "career_interest", "location", "goal"}
    assert set(result["score_breakdown"].keys()) == expected_keys


def test_reasoning_not_empty(matcher, sample_student_profile, sample_opportunity):
    result = matcher.score_opportunity(sample_student_profile, sample_opportunity)
    assert len(result["reasoning"]) > 0


def test_empty_opportunity_skills(matcher, sample_student_profile):
    opp = {"id": "test", "title": "Generic Job", "skills": [], "requirements": []}
    result = matcher.score_opportunity(sample_student_profile, opp)
    assert 0 <= result["match_score"] <= 100
