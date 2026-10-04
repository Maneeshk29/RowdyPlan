from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    student_id: UUID
    event_type: str = Field(..., description="job_viewed, job_saved, job_dismissed, job_applied, event_attended, recommendation_accepted, recommendation_rejected, career_interest_updated")
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None  # opportunity, career_path
    metadata: Optional[dict] = None


class FeedbackResponse(BaseModel):
    id: UUID
    student_id: UUID
    event_type: str
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    metadata: Optional[dict] = None
    timestamp: Optional[datetime] = None

    model_config = {"from_attributes": True}
