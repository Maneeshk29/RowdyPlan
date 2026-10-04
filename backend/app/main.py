"""Rowdy Plan – FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.session import create_tables


# ---------------------------------------------------------------------------
# Lifespan – runs once on startup / shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables on startup."""
    await create_tables()
    yield


# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Router registration – guarded so the app can start before all routers exist
# ---------------------------------------------------------------------------
_ROUTER_MODULES = [
    "app.api.students",
    "app.api.resume",
    "app.api.careers",
    "app.api.jobs",
    "app.api.experiences",
    "app.api.rowdy_plan",
    "app.api.feedback",
    "app.api.opportunities",
    "app.api.admin",
]

for _module_path in _ROUTER_MODULES:
    try:
        import importlib

        _mod = importlib.import_module(_module_path)
        _router = getattr(_mod, "router", None)
        if _router is not None:
            app.include_router(_router, prefix=settings.API_PREFIX)
    except (ImportError, ModuleNotFoundError):
        # Router module hasn't been created yet – skip silently.
        pass


# ---------------------------------------------------------------------------
# Root / health endpoints
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    """Service identity."""
    return {"service": "Rowdy Plan", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health-check endpoint for load balancers / orchestrators."""
    return {"status": "healthy"}
