from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OpportunityCreate(BaseModel):
    type: str = Field(..., description="job, event, research, organization, program")
    title: str = Field(..., min_length=1)
    description: str = ""
    organization: str = ""
    skills: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    majors: list[str] = Field(default_factory=list)
    graduation_years: list[str] = Field(default_factory=list)
    location: Optional[str] = None
    deadline: Optional[datetime] = None
    url: Optional[str] = None
    source: str = "manual"
    minimum_gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    work_authorization_required: bool = False


class OpportunityUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    organization: Optional[str] = None
    skills: Optional[list[str]] = None
    requirements: Optional[list[str]] = None
    majors: Optional[list[str]] = None
    graduation_years: Optional[list[str]] = None
    location: Optional[str] = None
    deadline: Optional[datetime] = None
    url: Optional[str] = None
    source: Optional[str] = None
    minimum_gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    work_authorization_required: Optional[bool] = None
    ingestion_status: Optional[str] = None
    expiration_date: Optional[datetime] = None


class OpportunityResponse(BaseModel):
    id: UUID
    type: str
    title: str
    description: Optional[str] = None
    organization: Optional[str] = None
    skills: list[str] = []
    requirements: list[str] = []
    majors: list[str] = []
    graduation_years: list[str] = []
    location: Optional[str] = None
    deadline: Optional[datetime] = None
    url: Optional[str] = None
    source: Optional[str] = None
    ingestion_status: str = "active"
    minimum_gpa: Optional[float] = None
    work_authorization_required: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OpportunityFilter(BaseModel):
    type: Optional[str] = None
    skills: Optional[list[str]] = None
    majors: Optional[list[str]] = None
    location: Optional[str] = None
    deadline_before: Optional[datetime] = None
