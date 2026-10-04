from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Text, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

from app.database.base import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), nullable=False)  # job, event, research, organization, program
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    organization = Column(String(300), nullable=True)
    skills = Column(JSON, default=list)
    requirements = Column(JSON, default=list)
    majors = Column(JSON, default=list)
    graduation_years = Column(JSON, default=list)
    location = Column(String(300), nullable=True)
    deadline = Column(DateTime, nullable=True)
    url = Column(String(1000), nullable=True)
    source = Column(String(200), nullable=True)
    source_timestamp = Column(DateTime, nullable=True)
    ingestion_status = Column(String(50), default="active")
    expiration_date = Column(DateTime, nullable=True)
    minimum_gpa = Column(Float, nullable=True)
    work_authorization_required = Column(Boolean, default=False)

    if Vector is not None:
        embedding = Column(Vector(384), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "organization": self.organization,
            "skills": self.skills or [],
            "requirements": self.requirements or [],
            "majors": self.majors or [],
            "graduation_years": self.graduation_years or [],
            "location": self.location,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "url": self.url,
            "source": self.source,
            "source_timestamp": self.source_timestamp.isoformat() if self.source_timestamp else None,
            "ingestion_status": self.ingestion_status,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "minimum_gpa": self.minimum_gpa,
            "work_authorization_required": self.work_authorization_required,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
