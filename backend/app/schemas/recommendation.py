from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.career import CareerMatchResult


class JobMatchResult(BaseModel):
    opportunity_id: str
    title: str
    organization: str = ""
    match_score: int = Field(..., ge=0, le=100)
    score_breakdown: dict = {}
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    reasoning: list[str] = []
    recommended_actions: list[str] = []
    qualification_status: str = "UNKNOWN"  # QUALIFIED, LIKELY_QUALIFIED, SKILL_GAP, NOT_ELIGIBLE, UNKNOWN


class ExperienceMatchResult(BaseModel):
    type: str
    title: str
    description: str = ""
    relevance_score: int = Field(..., ge=0, le=100)
    reason: str = ""
    action: str = ""


class BulletRewrite(BaseModel):
    original: str
    rewrite: str
    reason: str


class ResumeAnalysis(BaseModel):
    resume_score: int = Field(..., ge=0, le=100)
    ats_compatibility: int = Field(..., ge=0, le=100)
    missing_keywords: list[str] = []
    weak_bullets: list[dict] = []  # {"original": str, "suggestion": str}
    strong_bullets: list[str] = []
    missing_technical_skills: list[str] = []
    missing_measurable_impact: list[str] = []
    recommended_rewrites: list[dict] = []  # {"original": str, "rewrite": str, "reason": str}


class SkillGap(BaseModel):
    skill: str
    current_level: str = "none"  # none, beginner, intermediate, advanced
    required_level: str = "intermediate"
    priority: str = "medium"  # low, medium, high, critical
    resources: list[str] = []


class TimelineItem(BaseModel):
    period: str  # "Now", "Next 30 Days", "Next Semester", "Next Year"
    title: str
    actions: list[str] = []


class ProcessingStep(BaseModel):
    step: str
    status: str = "pending"  # pending, in_progress, complete


class RowdyPlanRequest(BaseModel):
    student_id: UUID
    include_resume_analysis: bool = True
    max_career_matches: int = Field(5, ge=1, le=20)
    max_job_matches: int = Field(20, ge=1, le=100)


class RowdyPlanResponse(BaseModel):
    student: dict = {}
    profile_strength: int = Field(..., ge=0, le=100)
    career_matches: list[CareerMatchResult] = []
    job_matches: list[JobMatchResult] = []
    experience_matches: list[ExperienceMatchResult] = []
    resume_analysis: Optional[ResumeAnalysis] = None
    skill_gaps: list[SkillGap] = []
    next_steps: list[str] = []
    timeline: list[TimelineItem] = []
    processing_steps: list[ProcessingStep] = []
