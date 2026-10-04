"""Opportunity browsing and search endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.api.mock_store import store

router = APIRouter(tags=["opportunities"])


@router.get("/opportunities")
async def list_opportunities(
    type: Optional[str] = Query(None, description="Filter by type: job, event, research, organization, program"),
    skills: Optional[str] = Query(None, description="Comma-separated skills to filter by"),
    location: Optional[str] = Query(None, description="Location filter"),
    skip: int = 0,
    limit: int = 50,
):
    """List opportunities with optional filters."""
    filters = {}
    if type:
        filters["type"] = type
    if skills:
        filters["skills"] = [s.strip() for s in skills.split(",")]
    if location:
        filters["location"] = location

    return store.list_opportunities(filters=filters, skip=skip, limit=limit)


@router.get("/opportunities/{opportunity_id}")
async def get_opportunity(opportunity_id: str):
    """Get a specific opportunity by ID."""
    opp = store.get_opportunity(opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@router.post("/opportunities/search")
async def search_opportunities(body: dict):
    """Search opportunities by text query."""
    query = body.get("query", "").lower()
    if not query:
        return store.list_opportunities()

    all_opps = store.list_opportunities()
    results = []
    for opp in all_opps:
        searchable = f"{opp.get('title', '')} {opp.get('description', '')} {opp.get('organization', '')} {' '.join(opp.get('skills', []))}".lower()
        if query in searchable:
            results.append(opp)

    return results
