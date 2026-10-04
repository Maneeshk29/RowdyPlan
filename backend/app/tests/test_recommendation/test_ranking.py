"""Tests for the ranking engine."""
from __future__ import annotations

import pytest
from app.recommendation.ranking import RankingEngine


@pytest.fixture
def engine():
    return RankingEngine()


def test_rank_sorts_descending(engine):
    items = [
        {"name": "A", "match_score": 70},
        {"name": "B", "match_score": 90},
        {"name": "C", "match_score": 50},
    ]
    ranked = engine.rank(items, score_key="match_score")
    scores = [r["match_score"] for r in ranked]
    assert scores == [90, 70, 50]


def test_rank_with_limit(engine):
    items = [{"match_score": i * 10} for i in range(10)]
    ranked = engine.rank(items, limit=3)
    assert len(ranked) == 3


def test_qualification_filter_gpa_check(engine):
    """Student GPA below minimum should be NOT_ELIGIBLE or SKILL_GAP."""
    student = {"gpa": 2.5, "major": "Computer Science", "graduation_date": "May 2026"}
    opp = {"minimum_gpa": 3.0, "required_majors": [], "graduation_years": []}
    status = engine.apply_qualification_filter(student, opp)
    # GPA 2.5 is well below 3.0, so should be disqualified
    assert status in ("NOT_ELIGIBLE", "SKILL_GAP", "LIKELY_QUALIFIED")


def test_qualification_filter_major_check(engine):
    """Student with matching major should be qualified."""
    student = {"gpa": 3.5, "major": "Computer Science", "graduation_date": "May 2026"}
    opp = {"minimum_gpa": 3.0, "required_majors": ["Computer Science"], "graduation_years": []}
    status = engine.apply_qualification_filter(student, opp)
    assert status in ("QUALIFIED", "LIKELY_QUALIFIED")


def test_qualification_filter_grad_year_check(engine):
    """Student with matching graduation year should not be disqualified."""
    student = {"gpa": 3.5, "major": "Computer Science", "graduation_year": "2026"}
    opp = {"minimum_gpa": None, "required_majors": [], "graduation_years": ["2026", "2027"]}
    status = engine.apply_qualification_filter(student, opp)
    assert status != "NOT_ELIGIBLE"


def test_qualification_status_values(engine):
    valid = {"QUALIFIED", "LIKELY_QUALIFIED", "SKILL_GAP", "NOT_ELIGIBLE", "UNKNOWN"}
    student = {"gpa": 3.5, "major": "CS"}
    opp = {"minimum_gpa": 3.0, "required_majors": ["CS"], "graduation_years": ["2026"]}
    status = engine.apply_qualification_filter(student, opp)
    assert status in valid


def test_apply_diversity(engine):
    items = [
        {"match_score": 90, "organization": "USAA"},
        {"match_score": 85, "organization": "USAA"},
        {"match_score": 80, "organization": "USAA"},
        {"match_score": 75, "organization": "USAA"},
        {"match_score": 70, "organization": "H-E-B"},
    ]
    diverse = engine.apply_diversity(items, diversity_key="organization", max_per_group=2)
    usaa_count = sum(1 for d in diverse if d.get("organization") == "USAA")
    assert usaa_count <= 2
