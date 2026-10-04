from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

from app.database.base import Base


class StudentProfile(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    major = Column(String(200), nullable=False)
    concentration = Column(String(200), nullable=True)
    minor = Column(String(200), nullable=True)
    gpa = Column(Float, nullable=True)
    graduation_date = Column(String(50), nullable=True)
    year = Column(String(50), nullable=True)  # Freshman, Sophomore, Junior, Senior
    university = Column(String(200), default="UTSA")

    # Skills
    skills = Column(JSON, default=list)
    technical_skills = Column(JSON, default=list)
    soft_skills = Column(JSON, default=list)
    coursework = Column(JSON, default=list)
    certifications = Column(JSON, default=list)

    # Experience
    experience = Column(JSON, default=list)  # list of dicts
    projects = Column(JSON, default=list)
    organizations = Column(JSON, default=list)
    leadership = Column(JSON, default=list)
    volunteering = Column(JSON, default=list)
    competitions = Column(JSON, default=list)
    hackathons = Column(JSON, default=list)

    # Goals and preferences
    career_interests = Column(JSON, default=list)
    industries = Column(JSON, default=list)
    preferred_locations = Column(JSON, default=list)
    work_preferences = Column(JSON, default=list)  # remote, hybrid, in-person
    preferred_companies = Column(JSON, default=list)
    short_term_goal = Column(Text, nullable=True)
    long_term_goal = Column(Text, nullable=True)
    current_goal = Column(String(100), nullable=True)  # internship, full_time, research, etc.

    # Resume
    resume_text = Column(Text, nullable=True)
    resume_filename = Column(String(500), nullable=True)

    # Embeddings (pgvector)
    if Vector is not None:
        profile_embedding = Column(Vector(384), nullable=True)
        skills_embedding = Column(Vector(384), nullable=True)
        experience_embedding = Column(Vector(384), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "major": self.major,
            "concentration": self.concentration,
            "minor": self.minor,
            "gpa": self.gpa,
            "graduation_date": self.graduation_date,
            "year": self.year,
            "university": self.university,
            "skills": self.skills or [],
            "technical_skills": self.technical_skills or [],
            "soft_skills": self.soft_skills or [],
            "coursework": self.coursework or [],
            "certifications": self.certifications or [],
            "experience": self.experience or [],
            "projects": self.projects or [],
            "organizations": self.organizations or [],
            "leadership": self.leadership or [],
            "volunteering": self.volunteering or [],
            "competitions": self.competitions or [],
            "hackathons": self.hackathons or [],
            "career_interests": self.career_interests or [],
            "industries": self.industries or [],
            "preferred_locations": self.preferred_locations or [],
            "work_preferences": self.work_preferences or [],
            "preferred_companies": self.preferred_companies or [],
            "short_term_goal": self.short_term_goal,
            "long_term_goal": self.long_term_goal,
            "current_goal": self.current_goal,
            "resume_text": self.resume_text,
            "resume_filename": self.resume_filename,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
