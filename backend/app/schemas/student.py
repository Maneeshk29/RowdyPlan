from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ExperienceItem(BaseModel):
    type: str = Field(..., description="Type: internship, job, research, project")
    title: str
    organization: str = ""
    description: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class StudentProfileCreate(BaseModel):
    major: str = Field(..., min_length=1, description="Student major")
    concentration: Optional[str] = None
    minor: Optional[str] = None
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    graduation_date: Optional[str] = None
    year: Optional[str] = Field(None, description="Freshman, Sophomore, Junior, Senior")
    university: str = "UTSA"
    skills: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    coursework: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    experience: list[dict] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    leadership: list[dict] = Field(default_factory=list)
    volunteering: list[dict] = Field(default_factory=list)
    competitions: list[str] = Field(default_factory=list)
    hackathons: list[str] = Field(default_factory=list)
    career_interests: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    work_preferences: list[str] = Field(default_factory=list)
    preferred_companies: list[str] = Field(default_factory=list)
    short_term_goal: Optional[str] = None
    long_term_goal: Optional[str] = None
    current_goal: str = Field(..., description="internship, full_time, research, campus_employment, exploring, graduate_school, networking")

    @field_validator("current_goal")
    @classmethod
    def validate_current_goal(cls, v: str) -> str:
        valid = {"internship", "full_time", "research", "campus_employment", "exploring", "graduate_school", "networking"}
        if v not in valid:
            raise ValueError(f"current_goal must be one of: {', '.join(sorted(valid))}")
        return v


class StudentProfileUpdate(BaseModel):
    major: Optional[str] = None
    concentration: Optional[str] = None
    minor: Optional[str] = None
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    graduation_date: Optional[str] = None
    year: Optional[str] = None
    university: Optional[str] = None
    skills: Optional[list[str]] = None
    technical_skills: Optional[list[str]] = None
    soft_skills: Optional[list[str]] = None
    coursework: Optional[list[str]] = None
    certifications: Optional[list[str]] = None
    experience: Optional[list[dict]] = None
    projects: Optional[list[dict]] = None
    organizations: Optional[list[str]] = None
    leadership: Optional[list[dict]] = None
    volunteering: Optional[list[dict]] = None
    competitions: Optional[list[str]] = None
    hackathons: Optional[list[str]] = None
    career_interests: Optional[list[str]] = None
    industries: Optional[list[str]] = None
    preferred_locations: Optional[list[str]] = None
    work_preferences: Optional[list[str]] = None
    preferred_companies: Optional[list[str]] = None
    short_term_goal: Optional[str] = None
    long_term_goal: Optional[str] = None
    current_goal: Optional[str] = None
    resume_text: Optional[str] = None
    resume_filename: Optional[str] = None


class StudentProfileResponse(BaseModel):
    id: UUID
    major: str
    concentration: Optional[str] = None
    minor: Optional[str] = None
    gpa: Optional[float] = None
    graduation_date: Optional[str] = None
    year: Optional[str] = None
    university: str = "UTSA"
    skills: list[str] = []
    technical_skills: list[str] = []
    soft_skills: list[str] = []
    coursework: list[str] = []
    certifications: list[str] = []
    experience: list[dict] = []
    projects: list[dict] = []
    organizations: list[str] = []
    leadership: list[dict] = []
    volunteering: list[dict] = []
    competitions: list[str] = []
    hackathons: list[str] = []
    career_interests: list[str] = []
    industries: list[str] = []
    preferred_locations: list[str] = []
    work_preferences: list[str] = []
    preferred_companies: list[str] = []
    short_term_goal: Optional[str] = None
    long_term_goal: Optional[str] = None
    current_goal: Optional[str] = None
    resume_text: Optional[str] = None
    resume_filename: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
