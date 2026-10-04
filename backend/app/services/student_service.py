"""Student profile CRUD service."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select, update, delete
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

try:
    from app.models.student import StudentProfile
    HAS_MODEL = True
except Exception:
    HAS_MODEL = False


class StudentService:
    """CRUD operations for student profiles. Works with DB or in-memory fallback."""

    async def create_profile(self, db: Any, profile_data: dict) -> dict:
        if HAS_SQLALCHEMY and HAS_MODEL and db is not None:
            student = StudentProfile(
                id=uuid.uuid4(),
                **profile_data,
            )
            db.add(student)
            await db.commit()
            await db.refresh(student)
            return student.to_dict()

        # In-memory fallback
        profile = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            **profile_data,
        }
        return profile

    async def get_profile(self, db: Any, student_id: uuid.UUID) -> dict | None:
        if HAS_SQLALCHEMY and HAS_MODEL and db is not None:
            result = await db.execute(
                select(StudentProfile).where(StudentProfile.id == student_id)
            )
            student = result.scalar_one_or_none()
            return student.to_dict() if student else None
        return None

    async def update_profile(self, db: Any, student_id: uuid.UUID, update_data: dict) -> dict | None:
        if HAS_SQLALCHEMY and HAS_MODEL and db is not None:
            result = await db.execute(
                select(StudentProfile).where(StudentProfile.id == student_id)
            )
            student = result.scalar_one_or_none()
            if not student:
                return None
            for key, value in update_data.items():
                if value is not None and hasattr(student, key):
                    setattr(student, key, value)
            student.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(student)
            return student.to_dict()
        return None

    async def delete_profile(self, db: Any, student_id: uuid.UUID) -> bool:
        if HAS_SQLALCHEMY and HAS_MODEL and db is not None:
            result = await db.execute(
                select(StudentProfile).where(StudentProfile.id == student_id)
            )
            student = result.scalar_one_or_none()
            if student:
                await db.delete(student)
                await db.commit()
                return True
        return False

    async def list_profiles(self, db: Any, skip: int = 0, limit: int = 20) -> list[dict]:
        if HAS_SQLALCHEMY and HAS_MODEL and db is not None:
            result = await db.execute(
                select(StudentProfile).offset(skip).limit(limit)
            )
            students = result.scalars().all()
            return [s.to_dict() for s in students]
        return []
