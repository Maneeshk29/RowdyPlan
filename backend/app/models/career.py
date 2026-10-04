from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

from app.database.base import Base


class CareerPath(Base):
    __tablename__ = "career_paths"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    typical_skills = Column(JSON, default=list)
    typical_coursework = Column(JSON, default=list)
    typical_certifications = Column(JSON, default=list)
    entry_level_titles = Column(JSON, default=list)
    mid_level_titles = Column(JSON, default=list)
    senior_titles = Column(JSON, default=list)
    related_industries = Column(JSON, default=list)
    average_salary_range = Column(JSON, default=dict)  # {"min": ..., "max": ...}
    growth_outlook = Column(String(200), nullable=True)

    if Vector is not None:
        embedding = Column(Vector(384), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "typical_skills": self.typical_skills or [],
            "typical_coursework": self.typical_coursework or [],
            "typical_certifications": self.typical_certifications or [],
            "entry_level_titles": self.entry_level_titles or [],
            "mid_level_titles": self.mid_level_titles or [],
            "senior_titles": self.senior_titles or [],
            "related_industries": self.related_industries or [],
            "average_salary_range": self.average_salary_range or {},
            "growth_outlook": self.growth_outlook,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
