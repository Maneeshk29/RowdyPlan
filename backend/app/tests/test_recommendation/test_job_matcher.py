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


def test_student_ui_fields_affect_job_match(matcher):
    student = {
        "major": "Computer Science",
        "graduation_date": "May 2027",
        "current_goal": "full_time",
        "skills": ["python"],
        "technical_skills": ["react", "docker"],
        "career_interests": ["Software Engineer"],
        "preferred_locations": ["Austin, TX", "Remote"],
        "work_preferences": ["hybrid"],
    }
    opp = {
        "id": "handshake-1",
        "type": "job",
        "title": "Frontend Software Engineer",
        "organization": "Test Corp",
        "description": "Build React apps and deploy with Docker.",
        "skills": ["react", "docker"],
        "requirements": ["Computer Science major"],
        "majors": ["Computer Science"],
        "graduation_years": ["2027"],
        "location": "Austin, TX",
        "job_type": "Full-time",
        "source": "handshake",
    }

    result = matcher.score_opportunity(student, opp)

    assert result["score_breakdown"]["skill"] == 100.0
    assert result["score_breakdown"]["location"] == 100.0
    assert result["score_breakdown"]["goal"] >= 80.0
    assert result["qualification_status"] in ("QUALIFIED", "LIKELY_QUALIFIED")


@pytest.mark.parametrize("gpa, expected_status", [(None, "UNKNOWN"), (0.0, "NOT_ELIGIBLE"), (2.9, "NOT_ELIGIBLE"), (3.0, "QUALIFIED")])
def test_gpa_requirement_handles_missing_and_zero(matcher, gpa, expected_status):
    result = matcher.score_opportunity(
        {"skills": ["python"], "gpa": gpa},
        {"title": "Python Intern", "skills": ["python"], "minimum_gpa": 3.0},
    )
    assert result["qualification_status"] == expected_status


def test_missing_job_skill_requirements_do_not_confirm_eligibility(matcher):
    result = matcher.score_opportunity(
        {"major": "Computer Science", "skills": ["python"], "current_goal": "internship"},
        {"title": "Certified Medical Assistant - Internal Medicine", "employment_type": "Full Time",
         "description": "Answering phones. CMA certification is required."},
    )
    assert result["qualification_status"] == "UNKNOWN"
    assert result["score_breakdown"]["goal"] < 50


def test_internship_goal_does_not_match_internal_medicine(matcher):
    assert matcher._compute_goal_match("internship", "job Internal Medicine") < 50


def test_employment_classification_takes_precedence_over_title(matcher):
    goal_text = matcher._opportunity_goal_text({
        "title": "Internal Communications", "type": "job", "employment_type": "full-time",
    })
    assert goal_text == "full-time"


@pytest.mark.parametrize("interest, description", [
    ("Software Engineer", "Answering phones and supporting patients."),
    ("ML Engineer", "Paid painting assistant."),
])
def test_career_keywords_use_complete_words(matcher, interest, description):
    score = matcher._compute_career_interest_match([interest], {"title": "Support Assistant", "description": description})
    assert score == 30


def test_missing_job_title_is_not_an_exact_career_match(matcher):
    assert matcher._compute_career_interest_match(["Software Engineer"], {"description": "Support patients."}) < 50
