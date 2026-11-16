"""Career Center console endpoints (staff).

Access rule:
- With ``STAFF_ACCESS_KEY`` configured and a matching ``X-Staff-Key`` header,
  the console shows live (real) student records.
- Otherwise it shows the synthetic demo cohort only. Real student data is
  never returned without the key.
"""
from __future__ import annotations

import hmac
import secrets
import uuid
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.mock_store import store
from app.core.config import settings
from app.services.career_center import CareerCenterAnalytics
from app.services.demo_cohort import load_demo_cohort

router = APIRouter(prefix="/career-center", tags=["career-center"])


def staff_scope(x_staff_key: Optional[str] = Header(default=None)) -> str:
    """Return 'live' for a valid staff key, otherwise 'demo'."""
    configured = settings.STAFF_ACCESS_KEY
    if x_staff_key:
        if configured and hmac.compare_digest(x_staff_key.encode(), configured.encode()):
            return "live"
        raise HTTPException(status_code=401, detail="Staff key not recognized.")
    if not settings.DEMO_COHORT_ENABLED:
        raise HTTPException(status_code=401, detail="A staff key is required.")
    load_demo_cohort(store)
    return "demo"


def analytics(scope: str = Depends(staff_scope)) -> CareerCenterAnalytics:
    return CareerCenterAnalytics(store, demo=scope == "demo")


class EventIn(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    host: str = Field(default="Career Center", max_length=80)
    location: str = Field(default="UTSA Main Campus", max_length=120)
    starts_at: Optional[datetime] = None


@router.get("/access")
async def access(scope: str = Depends(staff_scope)):
    """Tell the console which data it is showing."""
    return {
        "scope": scope,
        "staff_key_configured": bool(settings.STAFF_ACCESS_KEY),
        "note": "Synthetic demo cohort. No real student data." if scope == "demo" else "Live student records.",
    }


@router.get("/overview")
async def overview(cc: CareerCenterAnalytics = Depends(analytics)):
    return cc.overview()


@router.get("/caseload")
async def caseload(
    priority: Optional[Literal["high", "medium", "low"]] = None,
    limit: int = Query(default=200, ge=1, le=1000),
    cc: CareerCenterAnalytics = Depends(analytics),
):
    rows = cc.caseload(priority=priority, limit=limit)
    return {"scope": "demo" if cc.demo else "live", "count": len(rows), "students": rows}


@router.get("/students/{student_id}/brief")
async def brief(student_id: str, cc: CareerCenterAnalytics = Depends(analytics)):
    """Pre-meeting brief for an advisor appointment."""
    result = cc.brief(student_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Student not found in this scope")
    return result


@router.get("/outcomes.csv")
async def outcomes_csv(cc: CareerCenterAnalytics = Depends(analytics)):
    """First-destination style export of reported outcomes."""
    filename = f"rowdyplan-outcomes-{'demo' if cc.demo else 'live'}-{datetime.utcnow():%Y%m%d}.csv"
    return Response(
        content=cc.outcomes_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def create_event(body: EventIn, scope: str = Depends(staff_scope)):
    """Create a campus event with a QR check-in code.

    Events created in demo scope are flagged as demo and stay out of live reports.
    """
    event = store.add_campus_event({
        "id": f"evt-{uuid.uuid4().hex[:10]}",
        "title": body.title.strip(),
        "host": body.host.strip(),
        "location": body.location.strip(),
        "starts_at": (body.starts_at or datetime.utcnow()).isoformat(),
        "check_in_code": secrets.token_hex(3).upper(),
        "created_at": datetime.utcnow().isoformat(),
        "is_demo": scope == "demo",
    })
    return {**event, "check_in_path": f"/?checkin={event['id']}&code={event['check_in_code']}"}


@router.get("/events")
async def list_events(cc: CareerCenterAnalytics = Depends(analytics)):
    """Events in this scope with their check-in codes and attendance."""
    attendance = {row["id"]: row["check_ins"] for row in cc.overview()["events"]}
    events = [
        {**event, "check_ins": attendance.get(eid, 0),
         "check_in_path": f"/?checkin={eid}&code={event['check_in_code']}"}
        for eid, event in cc.events.items()
    ]
    return sorted(events, key=lambda e: e.get("starts_at") or "", reverse=True)
