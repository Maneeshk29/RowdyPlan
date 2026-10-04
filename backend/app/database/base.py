"""SQLAlchemy DeclarativeBase with pgvector support."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase

try:
    from pgvector.sqlalchemy import Vector  # noqa: F401 – re-exported for convenience
except ImportError:
    # Allow the app to load even if pgvector is not installed yet
    Vector = None  # type: ignore[assignment, misc]


class Base(DeclarativeBase):
    """Application-wide SQLAlchemy declarative base.

    Uses pgvector extension for vector-similarity columns.
    Models should subclass this and will automatically be registered in
    ``Base.metadata`` so that ``create_tables()`` picks them up.
    """

    pass
