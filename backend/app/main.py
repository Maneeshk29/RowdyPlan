"""Rowdy Plan – FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.staticfiles import MediaStaticFiles
from app.database.session import create_tables


# ---------------------------------------------------------------------------
# Lifespan – runs once on startup / shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables and seed data on startup."""
    await create_tables()

    # Auto-seed UTSA opportunities so the demo works immediately
    from app.api.mock_store import store
    if not store.opportunities:
        try:
            from app.ingestion.utsa_provider import UTSAProvider
            provider = UTSAProvider(use_live_data=False)
            opps = await provider.fetch_all()
            for opp in opps:
                store.add_opportunity(opp)
            print(f"[startup] Seeded {len(opps)} UTSA opportunities")
        except Exception as e:
            print(f"[startup] Seed warning: {e}")

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
    allow_origins=["*"],
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
FRONTEND_HTML = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "index.html")
FRONTEND_ASSETS = os.path.join(os.path.dirname(FRONTEND_HTML), "assets")
FRONTEND_MEDIA = os.path.join(os.path.dirname(FRONTEND_HTML), "public", "media")
if os.path.isdir(FRONTEND_ASSETS):
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS), name="assets")
if os.path.isdir(FRONTEND_MEDIA) and not os.environ.get("VERCEL"):
    # Vercel serves public/ directly; this mount is for local Uvicorn only.
    app.mount("/media", MediaStaticFiles(directory=FRONTEND_MEDIA), name="media")


@app.get("/")
async def serve_frontend(request: Request):
    """Serve the frontend single-page app."""
    accept = request.headers.get("accept", "")
    if os.path.exists(FRONTEND_HTML) and "text/html" in accept:
        return FileResponse(FRONTEND_HTML, media_type="text/html")
    return {"service": "Rowdy Plan", "version": "1.0.0", "note": "index.html not found — API-only mode"}


@app.get("/health")
async def health():
    """Health-check endpoint for load balancers / orchestrators."""
    return {"status": "healthy"}
