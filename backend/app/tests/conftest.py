"""Shared test fixtures for Rowdy Plan tests."""
from __future__ import annotations

import pytest


@pytest.fixture
def sample_student_profile() -> dict:
    return {
        "major": "Computer Science",
        "concentration": "Software Engineering",
        "minor": None,
        "gpa": 3.6,
        "graduation_date": "May 2026",
        "year": "Senior",
        "university": "UTSA",
        "skills": ["python", "java", "javascript", "sql", "git"],
        "technical_skills": ["react", "node.js", "docker", "rest api", "postgresql"],
        "soft_skills": ["teamwork", "communication"],
        "coursework": ["Data Structures", "Algorithms", "Software Engineering", "Database Systems"],
        "certifications": ["AWS Cloud Practitioner"],
        "experience": [
            {"type": "internship", "title": "Software Engineering Intern", "organization": "USAA",
             "description": "Built microservices using Java and Spring Boot.", "start_date": "May 2025", "end_date": "Aug 2025"},
        ],
        "projects": [
            {"title": "Task Manager App", "description": "Full-stack React + Node.js app", "skills": ["react", "node.js"]},
        ],
        "organizations": ["ACM UTSA"],
        "leadership": [],
        "volunteering": [],
        "competitions": [],
        "hackathons": ["RowdyHacks 2024"],
        "career_interests": ["Software Engineer", "Full Stack Developer"],
        "industries": ["Technology", "Finance"],
        "preferred_locations": ["San Antonio, TX", "Austin, TX", "Remote"],
        "work_preferences": ["hybrid", "remote"],
        "preferred_companies": ["USAA", "Google"],
        "short_term_goal": "Land a full-time SWE role",
        "long_term_goal": "Become a tech lead",
        "current_goal": "full_time",
        "resume_text": "EDUCATION\nUTSA B.S. Computer Science\nGPA: 3.6\n\nEXPERIENCE\nSoftware Engineering Intern, USAA\n- Developed microservices using Java and Spring Boot serving 10,000+ daily requests\n- Built React frontend improving workflow efficiency by 25%\n\nSKILLS\nPython, Java, JavaScript, React, Node.js, SQL, Docker, Git",
    }


@pytest.fixture
def sample_opportunity() -> dict:
    return {
        "id": "test-opp-001",
        "type": "job",
        "title": "Software Engineering Intern",
        "organization": "USAA",
        "description": "Build software for financial services.",
        "skills": ["java", "python", "react", "sql", "git", "agile"],
        "requirements": ["CS major", "Java experience", "GPA 3.0+"],
        "majors": ["Computer Science", "Software Engineering"],
        "graduation_years": ["2026", "2027"],
        "location": "San Antonio, TX",
        "minimum_gpa": 3.0,
        "url": "https://www.usaajobs.com",
        "source": "utsa",
    }


@pytest.fixture
def sample_career_path() -> dict:
    return {
        "name": "Software Engineer",
        "description": "Design, develop, and maintain software systems.",
        "typical_skills": ["python", "java", "javascript", "git", "sql", "docker", "algorithms", "data structures"],
        "typical_coursework": ["Data Structures", "Algorithms", "Software Engineering"],
        "typical_certifications": ["AWS Certified Developer"],
        "entry_level_titles": ["Junior Software Engineer"],
        "related_industries": ["Technology", "Finance"],
        "average_salary_range": {"min": 75000, "max": 150000},
    }


@pytest.fixture
def sample_resume_text() -> str:
    return """EDUCATION
University of Texas at San Antonio — B.S. Computer Science
GPA: 3.6 | Expected May 2026

EXPERIENCE
Software Engineering Intern, USAA | May 2025 – Aug 2025
- Developed microservices using Java and Spring Boot serving 10,000+ daily requests
- Built React frontend for internal employee tools, improving workflow efficiency by 25%
- Participated in Agile sprints and code reviews with a team of 8 engineers

Student Developer, UTSA IT | Jan 2024 – Dec 2024
- Maintained university web applications used by 30,000+ students
- Fixed 50+ bugs and implemented 10 new features

SKILLS
Python, Java, JavaScript, React, Node.js, SQL, PostgreSQL, Docker, Git, REST API, AWS

PROJECTS
Task Management App — Full-stack React + Node.js application with PostgreSQL
Weather API Service — Python FastAPI service aggregating weather data"""


@pytest.fixture
def mock_opportunities() -> list[dict]:
    return [
        {"id": "opp-1", "type": "job", "title": "SWE Intern", "organization": "USAA",
         "skills": ["java", "python", "react"], "requirements": ["CS major"],
         "majors": ["Computer Science"], "location": "San Antonio, TX", "minimum_gpa": 3.0},
        {"id": "opp-2", "type": "job", "title": "Data Analyst", "organization": "H-E-B",
         "skills": ["sql", "python", "tableau"], "requirements": ["Analytics major"],
         "majors": ["Data Science", "Statistics"], "location": "San Antonio, TX"},
        {"id": "opp-3", "type": "job", "title": "Cloud Engineer", "organization": "Rackspace",
         "skills": ["aws", "docker", "kubernetes", "linux"], "requirements": ["CS major"],
         "majors": ["Computer Science"], "location": "San Antonio, TX (Hybrid)"},
        {"id": "opp-4", "type": "event", "title": "Career Fair", "organization": "UTSA",
         "skills": ["networking"], "requirements": [], "majors": [], "location": "UTSA Campus"},
        {"id": "opp-5", "type": "research", "title": "AI Lab Research Assistant", "organization": "UTSA CS",
         "skills": ["python", "machine learning", "pytorch"], "requirements": ["GPA 3.2+"],
         "majors": ["Computer Science"], "location": "UTSA Main Campus", "minimum_gpa": 3.2},
        {"id": "opp-6", "type": "job", "title": "Security Analyst Intern", "organization": "Booz Allen",
         "skills": ["network security", "linux", "siem"], "requirements": ["Security clearance eligible"],
         "majors": ["Cybersecurity"], "location": "San Antonio, TX"},
        {"id": "opp-7", "type": "job", "title": "Mobile Developer", "organization": "H-E-B Digital",
         "skills": ["react native", "javascript", "typescript"], "requirements": ["CS or SE major"],
         "majors": ["Computer Science", "Software Engineering"], "location": "San Antonio, TX"},
        {"id": "opp-8", "type": "job", "title": "DevOps Intern", "organization": "Valero",
         "skills": ["docker", "kubernetes", "ci/cd", "linux"], "requirements": ["CS major"],
         "majors": ["Computer Science"], "location": "San Antonio, TX"},
        {"id": "opp-9", "type": "organization", "title": "ACM UTSA", "organization": "ACM",
         "skills": ["algorithms", "teamwork"], "requirements": [], "majors": [], "location": "UTSA"},
        {"id": "opp-10", "type": "program", "title": "Leadership Program", "organization": "UTSA",
         "skills": ["leadership", "communication"], "requirements": [], "majors": [], "location": "UTSA"},
    ]


@pytest.fixture
def mock_career_paths() -> list[dict]:
    return [
        {"name": "Software Engineer", "typical_skills": ["python", "java", "javascript", "git", "sql", "docker"],
         "typical_coursework": ["Data Structures", "Algorithms", "Software Engineering"],
         "related_industries": ["Technology", "Finance"]},
        {"name": "Data Scientist", "typical_skills": ["python", "r", "sql", "machine learning", "statistics"],
         "typical_coursework": ["Statistics", "Machine Learning", "Linear Algebra"],
         "related_industries": ["Technology", "Healthcare"]},
        {"name": "Cybersecurity Analyst", "typical_skills": ["network security", "linux", "python", "siem"],
         "typical_coursework": ["Network Security", "Cryptography"],
         "related_industries": ["Defense", "Finance"]},
        {"name": "Data Engineer", "typical_skills": ["python", "sql", "spark", "airflow", "etl"],
         "typical_coursework": ["Database Systems", "Distributed Systems"],
         "related_industries": ["Technology", "Finance"]},
        {"name": "Product Manager", "typical_skills": ["product strategy", "agile", "data analysis", "communication"],
         "typical_coursework": ["Product Management", "Business Strategy"],
         "related_industries": ["Technology", "SaaS"]},
    ]
