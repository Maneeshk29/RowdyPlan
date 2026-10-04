"""Tests for the feature extractor."""
from __future__ import annotations

import pytest
import numpy as np
from app.recommendation.feature_extractor import FeatureExtractor


@pytest.fixture
def extractor():
    return FeatureExtractor()


def test_extract_skill_vector_shape(extractor):
    skills = ["python", "java", "sql"]
    vector = extractor.extract_skill_vector(skills)
    assert isinstance(vector, np.ndarray)
    assert len(vector) > 0


def test_extract_experience_vector_shape(extractor):
    experience = [
        {"type": "internship", "title": "SWE Intern", "organization": "USAA"},
    ]
    vector = extractor.extract_experience_vector(experience)
    assert isinstance(vector, np.ndarray)
    assert len(vector) > 0


def test_extract_education_vector(extractor):
    vector = extractor.extract_education_vector(
        major="Computer Science",
        gpa=3.6,
        coursework=["Data Structures", "Algorithms"],
        certifications=["AWS Cloud Practitioner"],
    )
    assert isinstance(vector, np.ndarray)
    assert len(vector) > 0


def test_skill_vector_different_for_different_skills(extractor):
    vec1 = extractor.extract_skill_vector(["python", "java", "sql"])
    vec2 = extractor.extract_skill_vector(["rust", "haskell", "elixir"])
    # Different skills should produce different vectors
    assert not np.array_equal(vec1, vec2)


def test_empty_skills_returns_zero_vector(extractor):
    vector = extractor.extract_skill_vector([])
    assert isinstance(vector, np.ndarray)
    assert np.sum(np.abs(vector)) == 0


def test_extract_all_features(extractor, sample_student_profile):
    features = extractor.extract_all_features(sample_student_profile)
    assert isinstance(features, dict)
    assert "skill_vector" in features
    assert "experience_vector" in features
    assert "education_vector" in features
