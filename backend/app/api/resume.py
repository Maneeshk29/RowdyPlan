"""Resume upload and analysis endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from typing import Optional

from app.api.mock_store import store
from app.services.resume_service import ResumeService
from app.recommendation.resume_analyzer import ResumeAnalyzer

router = APIRouter(tags=["resume"])

resume_service = ResumeService()
resume_analyzer = ResumeAnalyzer()

ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    student_id: Optional[str] = Form(None),
):
    """
    Upload a PDF or DOCX resume. Parses and extracts structured data.
    Returns extracted information for the student to review and correct.
    """
    # Validate file type
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid file type. Only PDF and DOCX files are accepted. Got: {ext}",
        )

    # Read and validate size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 10 MB.",
        )

    # Parse resume
    try:
        result = resume_service.full_extraction(filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    # If student_id provided, update their profile with extracted data
    if student_id:
        student = store.get_student(student_id)
        if student:
            update_data = {
                "resume_text": result.get("resume_text", ""),
                "resume_filename": filename,
            }
            # Only update skills if student hasn't set them manually
            if not student.get("skills"):
                update_data["skills"] = result.get("skills", [])
            store.update_student(student_id, update_data)

    return {
        "filename": filename,
        "resume_text": result.get("resume_text", ""),
        "sections": result.get("sections", {}),
        "extracted_skills": result.get("skills", []),
        "keywords": result.get("keywords", []),
        "experience_level": result.get("experience_level", "entry"),
        "message": "Resume parsed successfully. Review the extracted information and correct any errors.",
    }


@router.post("/resume/analyze")
async def analyze_resume(body: dict):
    """
    Analyze a student's resume against a target career.
    Returns scoring, ATS compatibility, and improvement suggestions.
    """
    student_id = body.get("student_id")
    target_career = body.get("target_career", "Software Engineer")

    if not student_id:
        raise HTTPException(status_code=422, detail="student_id is required")

    student = store.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    resume_text = student.get("resume_text", "")
    if not resume_text:
        raise HTTPException(status_code=422, detail="No resume on file. Upload a resume first.")

    analysis = resume_analyzer.analyze(resume_text, target_career, student)
    return analysis
