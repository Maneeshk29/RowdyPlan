"""Opportunity CRUD and search service."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select, update, delete
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

try:
    from app.models.opportunity import Opportunity
    HAS_MODEL = True
except Exception:
    HAS_MODEL = False


class OpportunityService:
    """CRUD and search operations for opportunities."""

    async def create_opportunity(self, db: Any, data: dict) -> dict:
        if HAS_SQLALCHEMY and HAS_MODEL and db is not None:
            opp = Opportunity(id=uuid.uuid4(), **data)
            db.add(opp)
            await db.commit()
            await db.refresh(opp)
            return opp.to_dict()

        return {"id": str(uuid.uuid4()), "created_at": datetime.utcnow().isoformat(), **data}

    async def get_opportunity(self, db: Any, opportunity_id: uuid.UUID) -> dict | None:
        if HAS_SQLALCHEMY and HAS_MODEL and db is not None:
            result = await db.execute(
                select(Opportunity).where(Opportunity.id == opportunity_id)
            )
            opp = result.scalar_one_or_none()
            return opp.to_dict() if opp else None
        return None

    async def update_opportunity(self, db: Any, opportunity_id: uuid.UUID, data: dict) -> dict | None:
        if HAS_SQLALCHEMY and HAS_MODEL and db is not None:
            result = await db.execute(
                select(Opportunity).where(Opportunity.id == opportunity_id)
            )
            opp = result.scalar_one_or_none()
            if not opp:
                return None
            for key, value in data.items():
                if value is not None and hasattr(opp, key):
                    setattr(opp, key, value)
            opp.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(opp)
            return opp.to_dict()
        return None

    async def delete_opportunity(self, db: Any, opportunity_id: uuid.UUID) -> bool:
        if HAS_SQLALCHEMY and HAS_MODEL and db is not None:
            result = await db.execute(
                select(Opportunity).where(Opportunity.id == opportunity_id)
            )
            opp = result.scalar_one_or_none()
            if opp:
                await db.delete(opp)
                await db.commit()
                return True
        return False

    async def list_opportunities(self, db: Any, filters: dict | None = None, skip: int = 0, limit: int = 50) -> list[dict]:
        if HAS_SQLALCHEMY and HAS_MODEL and db is not None:
            query = select(Opportunity)
            if filters:
                if filters.get("type"):
                    query = query.where(Opportunity.type == filters["type"])
                if filters.get("ingestion_status"):
                    query = query.where(Opportunity.ingestion_status == filters["ingestion_status"])
            query = query.offset(skip).limit(limit)
            result = await db.execute(query)
            return [o.to_dict() for o in result.scalars().all()]
        return []

    async def bulk_upsert(self, db: Any, opportunities: list[dict]) -> int:
        """Insert or update opportunities. Returns count of upserted records."""
        count = 0
        for opp_data in opportunities:
            if "id" not in opp_data:
                opp_data["id"] = str(uuid.uuid4())
            await self.create_opportunity(db, opp_data)
            count += 1
        return count
