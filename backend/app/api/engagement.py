"""Student-side engagement endpoints: activity, outcome reports and event check-in."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.mock_store import store

router = APIRouter(tags=["engagement"])

ActivityKind = Literal[
    "resume_analyzed", "interview_practiced", "mission_added", "mission_completed", "plan_generated",
]
OutcomeType = Literal[
    "full_time", "internship", "grad_school", "military_service", "still_seeking", "not_seeking",
]


class ActivityIn(BaseModel):
    student_id: str = Field(min_length=1, max_length=64)
    kind: ActivityKind
    detail: str = Field(default="", max_length=200)


class OutcomeIn(BaseModel):
    student_id: str = Field(min_length=1, max_length=64)
    outcome_type: OutcomeType
    employer: str = Field(default="", max_length=120)
    title: str = Field(default="", max_length=120)
    degree_required: bool = False
    salary: Optional[int] = Field(default=None, ge=0, le=1_000_000)


class CheckInIn(BaseModel):
    student_id: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=4, max_length=12)


def _require_real_student(student_id: str) -> dict:
    student = store.get_student(student_id)
    if not student or student.get("is_demo"):
        raise HTTPException(status_code=404, detail="Student profile not found. Rebuild your plan and try again.")
    return student


@router.post("/activity", status_code=status.HTTP_201_CREATED)
async def record_activity(body: ActivityIn):
    """Record a student action so advisors can see engagement."""
    _require_real_student(body.student_id)
    activity = store.add_activity(body.student_id, body.kind, body.detail)
    return {"id": activity["id"], "kind": activity["kind"]}


@router.post("/outcomes", status_code=status.HTTP_201_CREATED)
async def report_outcome(body: OutcomeIn):
    """Self-report a first-destination outcome (job, internship, grad school...)."""
    _require_real_student(body.student_id)
    data = body.model_dump(exclude={"student_id"})
    if body.outcome_type in {"still_seeking", "not_seeking"}:
        data.update(employer="", title="", degree_required=False, salary=None)
    record = store.set_outcome(body.student_id, {**data, "source": "self_report"})
    store.add_activity(body.student_id, "outcome_reported", body.outcome_type)
    return record


@router.post("/events/check-in")
async def check_in_by_code(body: CheckInIn):
    """Check in by typing the code shown at the event (no link needed)."""
    code = body.code.strip().upper()
    event = next((e for e in store.campus_events.values() if e["check_in_code"] == code), None)
    if not event:
        raise HTTPException(status_code=404, detail="No event uses that check-in code.")
    return await check_in(event["id"], body)


@router.get("/events/{event_id}")
async def get_event(event_id: str):
    """Public event details for the check-in page (never exposes the code)."""
    event = store.get_campus_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {k: event.get(k) for k in ("id", "title", "host", "location", "starts_at")}


@router.post("/events/{event_id}/check-in")
async def check_in(event_id: str, body: CheckInIn):
    """Check a student in to an event with the organizer's code."""
    event = store.get_campus_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if body.code.strip().upper() != event["check_in_code"]:
        raise HTTPException(status_code=403, detail="That check-in code does not match this event.")
    _require_real_student(body.student_id)
    checkin, created = store.add_checkin(event_id, body.student_id)
    if created:
        store.add_activity(body.student_id, "event_checkin", event["title"])
    return {"event": event["title"], "checked_in_at": checkin["timestamp"], "already_checked_in": not created}
