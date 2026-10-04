"""Feedback event recording service."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

try:
    from app.models.feedback import FeedbackEvent
    HAS_MODEL = True
except Exception:
    HAS_MODEL = False


class FeedbackService:
    """Records and queries student interaction events for future learning-to-rank."""

    async def record_event(self, db: Any, event_data: dict) -> dict:
        if HAS_SQLALCHEMY and HAS_MODEL and db is not None:
            event = FeedbackEvent(id=uuid.uuid4(), **event_data)
            db.add(event)
            await db.commit()
            await db.refresh(event)
            return event.to_dict()

        return {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            **event_data,
        }

    async def get_student_events(self, db: Any, student_id: uuid.UUID, event_type: str | None = None) -> list[dict]:
        if HAS_SQLALCHEMY and HAS_MODEL and db is not None:
            query = select(FeedbackEvent).where(FeedbackEvent.student_id == student_id)
            if event_type:
                query = query.where(FeedbackEvent.event_type == event_type)
            query = query.order_by(FeedbackEvent.timestamp.desc())
            result = await db.execute(query)
            return [e.to_dict() for e in result.scalars().all()]
        return []

    async def get_entity_events(self, db: Any, entity_id: str, entity_type: str | None = None) -> list[dict]:
        if HAS_SQLALCHEMY and HAS_MODEL and db is not None:
            query = select(FeedbackEvent).where(FeedbackEvent.entity_id == entity_id)
            if entity_type:
                query = query.where(FeedbackEvent.entity_type == entity_type)
            result = await db.execute(query)
            return [e.to_dict() for e in result.scalars().all()]
        return []
