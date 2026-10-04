"""Student profile API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.mock_store import store
from app.schemas.student import StudentProfileCreate, StudentProfileUpdate, StudentProfileResponse

router = APIRouter(tags=["students"])


@router.post("/students/profile", status_code=status.HTTP_201_CREATED)
async def create_student_profile(profile: StudentProfileCreate):
    """Create a new student profile."""
    data = profile.model_dump()
    student = store.add_student(data)
    return student


@router.get("/students/{student_id}/profile")
async def get_student_profile(student_id: str):
    """Get a student profile by ID."""
    student = store.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/students/{student_id}/profile")
async def update_student_profile(student_id: str, update: StudentProfileUpdate):
    """Update an existing student profile."""
    existing = store.get_student(student_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Student not found")
    update_data = update.model_dump(exclude_none=True)
    updated = store.update_student(student_id, update_data)
    return updated


@router.delete("/students/{student_id}/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student_profile(student_id: str):
    """Delete a student profile."""
    deleted = store.delete_student(student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Student not found")


@router.get("/students")
async def list_students(skip: int = 0, limit: int = 20):
    """List all student profiles (admin)."""
    return store.list_students(skip=skip, limit=limit)
