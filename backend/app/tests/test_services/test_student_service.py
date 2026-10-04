"""Tests for student profile building and strength calculation."""
from __future__ import annotations

import pytest
from app.recommendation.profile_builder import ProfileBuilder


@pytest.fixture
def builder():
    return ProfileBuilder()


def test_profile_builder_creates_profile(builder, sample_student_profile):
    profile = builder.build_profile(sample_student_profile)
    assert isinstance(profile, dict)
    assert profile.get("major") == "Computer Science"


def test_profile_builder_calculates_strength(builder, sample_student_profile):
    strength = builder.calculate_profile_strength(sample_student_profile)
    assert isinstance(strength, int)
    assert 0 <= strength <= 100


def test_profile_strength_increases_with_data(builder):
    minimal = {"major": "CS", "current_goal": "exploring"}
    full = {
        "major": "CS",
        "current_goal": "full_time",
        "skills": ["python", "java"],
        "technical_skills": ["react"],
        "experience": [{"type": "internship", "title": "Intern", "organization": "Co"}],
        "resume_text": "Some resume content",
        "coursework": ["Data Structures"],
        "certifications": ["AWS"],
        "career_interests": ["SWE"],
    }
    minimal_strength = builder.calculate_profile_strength(minimal)
    full_strength = builder.calculate_profile_strength(full)
    assert full_strength > minimal_strength


def test_merge_resume_data_prefers_explicit(builder):
    profile = {"skills": ["python", "java"], "major": "CS"}
    resume_data = {"skills": ["python", "go", "rust"], "major": "Data Science"}
    merged = builder.merge_resume_data(profile, resume_data)
    # Explicit profile skills should be preserved
    assert "python" in merged.get("skills", [])
    assert "java" in merged.get("skills", [])
    # Major from profile should take precedence
    assert merged["major"] == "CS"
