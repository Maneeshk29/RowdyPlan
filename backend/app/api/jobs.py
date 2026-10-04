"""Job recommendation endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.api.mock_store import store
from app.recommendation.job_matcher import JobMatcher

router = APIRouter(tags=["jobs"])

job_matcher = JobMatcher()


@router.get("/jobs/recommendations")
async def get_job_recommendations(
    student_id: str = Query(..., description="Student profile ID"),
    limit: int = Query(20, ge=1, le=100),
):
    """Get personalized job/opportunity recommendations for a student."""
    student = store.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    opportunities = store.list_opportunities()
    if not opportunities:
        return {"student_id": student_id, "job_matches": [], "message": "No opportunities available. Seed the database first."}

    matches = job_matcher.rank_opportunities(student, opportunities)
    return {"student_id": student_id, "job_matches": matches[:limit]}
