"""Experience recommendation endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.api.mock_store import store
from app.recommendation.experience_matcher import ExperienceMatcher

router = APIRouter(tags=["experiences"])

experience_matcher = ExperienceMatcher()


@router.get("/experiences/recommendations")
async def get_experience_recommendations(
    student_id: str = Query(..., description="Student profile ID"),
    career_target: str = Query("Software Engineer", description="Target career for recommendations"),
):
    """Get university experience recommendations for a student."""
    student = store.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    readiness = experience_matcher.assess_readiness(student, career_target)
    matches = experience_matcher.match_experiences(student, career_target)

    return {
        "student_id": student_id,
        "career_target": career_target,
        "readiness": readiness,
        "experience_matches": matches,
    }
