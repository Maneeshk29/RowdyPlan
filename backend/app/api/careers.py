"""Career path recommendation endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.api.mock_store import store
from app.recommendation.career_matcher import CareerMatcher

router = APIRouter(tags=["careers"])

career_matcher = CareerMatcher()


@router.get("/careers/recommendations")
async def get_career_recommendations(
    student_id: str = Query(..., description="Student profile ID"),
    limit: int = Query(5, ge=1, le=20),
):
    """Get personalized career path recommendations for a student."""
    student = store.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    matches = career_matcher.match_careers(student, limit=limit)
    return {"student_id": student_id, "career_matches": matches}


@router.get("/careers")
async def list_careers():
    """List all available career paths."""
    return store.list_careers()


@router.get("/careers/{career_id}")
async def get_career(career_id: str):
    """Get a specific career path by ID."""
    career = store.get_career(career_id)
    if not career:
        raise HTTPException(status_code=404, detail="Career path not found")
    return career
