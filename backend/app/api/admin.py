"""Admin endpoints for opportunity management and data ingestion."""
from __future__ import annotations

import asyncio
from fastapi import APIRouter, HTTPException, status

from app.api.mock_store import store
from app.schemas.opportunity import OpportunityCreate, OpportunityUpdate
from app.ingestion.handshake_provider import HandshakeProvider
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
    provider_name = str(body.get("provider", "utsa")).lower()

    if provider_name == "utsa":
        provider = UTSAProvider(use_live_data=False)
    elif provider_name == "handshake":
        use_latest_run = body.get("use_latest_run", False)
        if not isinstance(use_latest_run, bool):
            raise HTTPException(status_code=422, detail="use_latest_run must be a boolean")
        dataset_id = body.get("dataset_id")
        if dataset_id is not None and (not isinstance(dataset_id, str) or not dataset_id.strip()):
            raise HTTPException(status_code=422, detail="dataset_id must be a non-empty string")
        provider = HandshakeProvider(
            actor_id=body.get("actor_id"),
            task_id=body.get("task_id"),
            actor_input=body.get("actor_input") or {},
            dataset_id=dataset_id,
            use_latest_run=use_latest_run,
        )
    else:
        raise HTTPException(status_code=422, detail=f"Unknown provider: {provider_name}")

    store.ingestion_status = {"status": "running", "last_run": None, "count": 0}

    try:
        opportunities = await provider.fetch_all()
        max_items = body.get("limit") or body.get("max_items")
        if max_items:
            opportunities = opportunities[: int(max_items)]

        added = 0
        updated = 0
        for opp in opportunities:
            _, created = store.upsert_opportunity(opp)
            if created:
                added += 1
            else:
                updated += 1

        from datetime import datetime
        store.ingestion_status = {
            "status": "complete",
            "provider": provider_name,
            "last_run": datetime.utcnow().isoformat(),
            "fetched": len(opportunities),
            "count": added,
            "added": added,
            "updated": updated,
            "total_available": len(store.opportunities),
        }
        return store.ingestion_status

    except ValueError as e:
        store.ingestion_status = {"status": "error", "provider": provider_name, "error": str(e)}
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        store.ingestion_status = {"status": "error", "provider": provider_name, "error": str(e)}
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
            store.upsert_opportunity(opp)
            existing_titles.add(opp.get("title", "").lower())
            added += 1

    return {
        "message": f"Seeded {added} opportunities",
        "total_opportunities": len(store.opportunities),
        "total_careers": len(store.careers),
    }
