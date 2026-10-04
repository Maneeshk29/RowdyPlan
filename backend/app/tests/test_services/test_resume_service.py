"""Tests for the resume parsing service."""
from __future__ import annotations

import pytest
from app.services.resume_service import ResumeService


@pytest.fixture
def service():
    return ResumeService()


def test_extract_sections_finds_education(service, sample_resume_text):
    sections = service.extract_sections(sample_resume_text)
    assert "education" in sections
    assert sections["education"]  # Not empty


def test_extract_sections_finds_experience(service, sample_resume_text):
    sections = service.extract_sections(sample_resume_text)
    assert "experience" in sections
    assert sections["experience"]


def test_extract_sections_finds_skills(service, sample_resume_text):
    sections = service.extract_sections(sample_resume_text)
    assert "skills" in sections
    assert sections["skills"]


def test_extract_skills_matches_known_skills(service, sample_resume_text):
    skills = service.extract_skills(sample_resume_text)
    assert "python" in skills
    assert "java" in skills
    assert "sql" in skills


def test_extract_keywords_not_empty(service, sample_resume_text):
    keywords = service.extract_keywords(sample_resume_text)
    assert len(keywords) > 0


def test_estimate_experience_level_entry(service):
    text = "Student developer, intern at USAA, freshman programmer"
    level = service.estimate_experience_level(text)
    assert level == "entry"


def test_estimate_experience_level_mid(service):
    text = "5 years of experience in software development as a mid-level engineer"
    level = service.estimate_experience_level(text)
    assert level == "mid"


def test_empty_resume_handled(service):
    sections = service.extract_sections("")
    # Should return empty sections without crashing
    assert isinstance(sections, dict)
    skills = service.extract_skills("")
    assert skills == []
    level = service.estimate_experience_level("")
    assert level == "entry"


def test_extract_skills_case_insensitive(service):
    text = "Experienced with Python, JAVA, and SQL databases"
    skills = service.extract_skills(text)
    assert "python" in skills
    assert "java" in skills
    assert "sql" in skills
