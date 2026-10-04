"""
In-memory store for running the API without PostgreSQL.
Pre-loaded with seed data so endpoints work immediately.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.recommendation.career_matcher import CAREER_DATABASE


class InMemoryStore:
    """Singleton in-memory data store for development/demo mode."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.students: dict[str, dict] = {}
        self.opportunities: list[dict] = []
        self.careers: list[dict] = []
        self.feedback: list[dict] = []
        self.ingestion_status: dict = {"last_run": None, "status": "idle", "count": 0}
        self._load_careers()

    def _load_careers(self):
        """Pre-load career paths from the career database."""
        for career in CAREER_DATABASE:
            self.careers.append({
                "id": str(uuid.uuid4()),
                **career,
                "created_at": datetime.utcnow().isoformat(),
            })

    # ── Students ──────────────────────────────────────────────────────────

    def add_student(self, profile_data: dict) -> dict:
        student_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        student = {
            "id": student_id,
            "created_at": now,
            "updated_at": now,
            **profile_data,
        }
        self.students[student_id] = student
        return student

    def get_student(self, student_id: str) -> dict | None:
        return self.students.get(student_id)

    def update_student(self, student_id: str, update_data: dict) -> dict | None:
        student = self.students.get(student_id)
        if not student:
            return None
        for key, value in update_data.items():
            if value is not None:
                student[key] = value
        student["updated_at"] = datetime.utcnow().isoformat()
        return student

    def delete_student(self, student_id: str) -> bool:
        if student_id in self.students:
            del self.students[student_id]
            return True
        return False

    def list_students(self, skip: int = 0, limit: int = 20) -> list[dict]:
        all_students = list(self.students.values())
        return all_students[skip : skip + limit]

    # ── Opportunities ─────────────────────────────────────────────────────

    def add_opportunity(self, opp_data: dict) -> dict:
        opp_id = opp_data.get("id") or str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        opp = {"id": opp_id, "created_at": now, "updated_at": now, **opp_data}
        opp["id"] = opp_id
        self.opportunities.append(opp)
        return opp

    def upsert_opportunity(self, opp_data: dict) -> tuple[dict, bool]:
        """Update an existing opportunity by source/url/title key or add it."""
        key = self._opportunity_key(opp_data)
        now = datetime.utcnow().isoformat()

        for existing in self.opportunities:
            if self._opportunity_key(existing) == key:
                existing.update({
                    k: v for k, v in opp_data.items()
                    if v is not None and k not in {"id", "created_at"}
                })
                existing["updated_at"] = now
                return existing, False

        return self.add_opportunity(opp_data), True

    def _opportunity_key(self, opp: dict) -> tuple:
        source_id = str(opp.get("source_id") or "").lower().strip()
        source = str(opp.get("source") or "").lower().strip()
        url = str(opp.get("url") or "").lower().strip()
        title = str(opp.get("title") or "").lower().strip()
        org = str(opp.get("organization") or "").lower().strip()
        if source_id:
            return ("source_id", source, source_id)
        if url:
            return ("url", url)
        return ("title_org", title, org)

    def get_opportunity(self, opp_id: str) -> dict | None:
        for opp in self.opportunities:
            if opp.get("id") == opp_id:
                return opp
        return None

    def update_opportunity(self, opp_id: str, update_data: dict) -> dict | None:
        for opp in self.opportunities:
            if opp.get("id") == opp_id:
                for key, value in update_data.items():
                    if value is not None:
                        opp[key] = value
                opp["updated_at"] = datetime.utcnow().isoformat()
                return opp
        return None

    def delete_opportunity(self, opp_id: str) -> bool:
        for i, opp in enumerate(self.opportunities):
            if opp.get("id") == opp_id:
                self.opportunities.pop(i)
                return True
        return False

    def list_opportunities(self, filters: dict | None = None, skip: int = 0, limit: int | None = 50) -> list[dict]:
        result = self.opportunities
        if filters:
            if filters.get("source"):
                result = [o for o in result if o.get("source") == filters["source"]]
            if filters.get("type"):
                result = [o for o in result if o.get("type") == filters["type"]]
            if filters.get("skills"):
                req = set(s.lower() for s in filters["skills"])
                result = [o for o in result if req & set(s.lower() for s in o.get("skills", []))]
            if filters.get("location"):
                loc = filters["location"].lower()
                result = [o for o in result if loc in o.get("location", "").lower()]
        return result[skip:] if limit is None else result[skip : skip + limit]

    # ── Careers ───────────────────────────────────────────────────────────

    def get_career(self, career_id: str) -> dict | None:
        for c in self.careers:
            if c.get("id") == career_id:
                return c
        return None

    def list_careers(self) -> list[dict]:
        return self.careers

    # ── Feedback ──────────────────────────────────────────────────────────

    def add_feedback(self, event_data: dict) -> dict:
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            **event_data,
        }
        self.feedback.append(event)
        return event

    def list_feedback(self, student_id: str | None = None, event_type: str | None = None) -> list[dict]:
        result = self.feedback
        if student_id:
            result = [f for f in result if str(f.get("student_id")) == student_id]
        if event_type:
            result = [f for f in result if f.get("event_type") == event_type]
        return result


# Global singleton
store = InMemoryStore()
