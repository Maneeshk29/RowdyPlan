from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CareerPathResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    typical_skills: list[str] = []
    typical_coursework: list[str] = []
    typical_certifications: list[str] = []
    entry_level_titles: list[str] = []
    mid_level_titles: list[str] = []
    senior_titles: list[str] = []
    related_industries: list[str] = []
    average_salary_range: dict = {}
    growth_outlook: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CareerMatchResult(BaseModel):
    career_name: str
    career_match_score: int = Field(..., ge=0, le=100)
    matching_skills: list[str] = []
    missing_skills: list[str] = []
    relevant_experience: list[str] = []
    recommended_courses: list[str] = []
    recommended_projects: list[str] = []
    recommended_events: list[str] = []
    recommended_jobs: list[str] = []
    next_action: str = ""
