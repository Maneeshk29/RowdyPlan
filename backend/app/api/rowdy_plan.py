"""Rowdy Plan generation endpoints — the main API."""
from __future__ import annotations

import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.mock_store import store
from app.recommendation.plan_generator import PlanGenerator

router = APIRouter(tags=["rowdy-plan"])

plan_generator = PlanGenerator()


@router.post("/rowdy-plan/generate")
async def generate_rowdy_plan(body: dict):
    """
    Generate a complete Rowdy Plan for a student.
    This is the main endpoint that runs the full recommendation pipeline.
    """
    student_id = body.get("student_id")
    if not student_id:
        raise HTTPException(status_code=422, detail="student_id is required")

    student = store.get_student(str(student_id))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    include_resume = body.get("include_resume_analysis", True)
    max_careers = body.get("max_career_matches", 5)
    max_jobs = body.get("max_job_matches", 20)

    opportunities = store.list_opportunities()

    plan = plan_generator.generate(
        student=student,
        opportunities=opportunities,
        include_resume_analysis=include_resume,
        max_career_matches=max_careers,
        max_job_matches=max_jobs,
    )

    return plan


@router.post("/rowdy-plan/generate-stream")
async def generate_rowdy_plan_stream(body: dict):
    """
    Generate a Rowdy Plan with Server-Sent Events for frontend animation.
    Sends processing step updates, then the complete plan.
    """
    student_id = body.get("student_id")
    if not student_id:
        raise HTTPException(status_code=422, detail="student_id is required")

    student = store.get_student(str(student_id))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    include_resume = body.get("include_resume_analysis", True)
    max_careers = body.get("max_career_matches", 5)
    max_jobs = body.get("max_job_matches", 20)

    async def event_stream():
        steps = [
            "Analyzing your background",
            "Reading your resume",
            "Understanding your goals",
            "Mapping your skills",
            "Comparing career paths",
            "Searching university opportunities",
            "Calculating your matches",
            "Building your Rowdy Plan",
        ]

        # Send progress events
        for step in steps:
            await asyncio.sleep(0.3)  # Simulated processing delay for animation
            event = {"step": step, "status": "complete"}
            yield f"data: {json.dumps(event)}\n\n"

        # Generate the actual plan
        opportunities = store.list_opportunities()
        plan = plan_generator.generate(
            student=student,
            opportunities=opportunities,
            include_resume_analysis=include_resume,
            max_career_matches=max_careers,
            max_job_matches=max_jobs,
        )

        # Send the complete result
        yield f"data: {json.dumps({'step': 'complete', 'result': plan})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
