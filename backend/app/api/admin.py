"""Admin endpoints for opportunity management and data ingestion."""
from __future__ import annotations

import asyncio
from fastapi import APIRouter, HTTPException, status

from app.api.mock_store import store
from app.schemas.opportunity import OpportunityCreate, OpportunityUpdate
from app.ingestion.utsa_provider import UTSAProvider

router = APIRouter(tags=["admin"])


@router.post("/admin/opportunities", status_code=status.HTTP_201_CREATED)
async def create_opportunity(opp: OpportunityCreate):
    """Create a new opportunity (admin)."""
    data = opp.model_dump()
    if data.get("deadline"):
        data["deadline"] = data["deadline"].isoformat()
    result = store.add_opportunity(data)
    return result


@router.put("/admin/opportunities/{opportunity_id}")
async def update_opportunity(opportunity_id: str, opp: OpportunityUpdate):
    """Update an existing opportunity (admin)."""
    existing = store.get_opportunity(opportunity_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    update_data = opp.model_dump(exclude_none=True)
    if "deadline" in update_data and update_data["deadline"]:
        update_data["deadline"] = update_data["deadline"].isoformat()
    if "expiration_date" in update_data and update_data["expiration_date"]:
        update_data["expiration_date"] = update_data["expiration_date"].isoformat()
    result = store.update_opportunity(opportunity_id, update_data)
    return result


@router.delete("/admin/opportunities/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_opportunity(opportunity_id: str):
    """Delete an opportunity (admin)."""
    deleted = store.delete_opportunity(opportunity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Opportunity not found")


@router.post("/admin/ingest")
async def trigger_ingestion(body: dict):
    """Trigger data ingestion from a university provider."""
    provider_name = body.get("provider", "utsa")

    if provider_name == "utsa":
        provider = UTSAProvider(use_live_data=False)
    else:
        raise HTTPException(status_code=422, detail=f"Unknown provider: {provider_name}")

    store.ingestion_status = {"status": "running", "last_run": None, "count": 0}

    try:
        opportunities = await provider.fetch_all()

        # Add to store (dedup against existing)
        existing_titles = {o.get("title", "").lower() for o in store.opportunities}
        added = 0
        for opp in opportunities:
            if opp.get("title", "").lower() not in existing_titles:
                store.add_opportunity(opp)
                existing_titles.add(opp.get("title", "").lower())
                added += 1

        from datetime import datetime
        store.ingestion_status = {
            "status": "complete",
            "last_run": datetime.utcnow().isoformat(),
            "count": added,
            "total_available": len(store.opportunities),
        }
        return store.ingestion_status

    except Exception as e:
        store.ingestion_status = {"status": "error", "error": str(e)}
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/admin/ingestion-status")
async def get_ingestion_status():
    """Get the status of the last ingestion run."""
    return store.ingestion_status


@router.post("/admin/seed")
async def seed_database():
    """Seed the database with mock UTSA data."""
    provider = UTSAProvider(use_live_data=False)
    opportunities = await provider.fetch_all()

    existing_titles = {o.get("title", "").lower() for o in store.opportunities}
    added = 0
    for opp in opportunities:
        if opp.get("title", "").lower() not in existing_titles:
            store.add_opportunity(opp)
            existing_titles.add(opp.get("title", "").lower())
            added += 1

    return {
        "message": f"Seeded {added} opportunities",
        "total_opportunities": len(store.opportunities),
        "total_careers": len(store.careers),
    }
