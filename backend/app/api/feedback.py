"""Feedback event endpoints for the learning system."""
from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.api.mock_store import store
from app.schemas.feedback import FeedbackCreate

router = APIRouter(tags=["feedback"])


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def record_feedback(event: FeedbackCreate):
    """Record a student interaction event (view, save, dismiss, apply, etc.)."""
    data = event.model_dump()
    data["student_id"] = str(data["student_id"])
    result = store.add_feedback(data)
    return result


@router.get("/feedback")
async def list_feedback(
    student_id: str = Query(None),
    event_type: str = Query(None),
):
    """Get feedback events, optionally filtered by student or event type."""
    return store.list_feedback(student_id=student_id, event_type=event_type)
