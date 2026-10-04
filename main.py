"""Vercel entrypoint for the existing frontend and FastAPI backend."""

import sys
from pathlib import Path

# The backend uses top-level app imports when run from backend/ locally.
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.main import app  # noqa: E402, F401
