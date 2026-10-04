"""Abstract base class for university opportunity providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.ingestion.normalization import normalize_opportunity, deduplicate


class UniversityOpportunityProvider(ABC):
    """
    Base class for university-specific data providers.
    Implement this for each university to feed opportunities into Rowdy Plan.
    """

    @abstractmethod
    async def fetch_jobs(self) -> list[dict]:
        """Fetch job/internship postings."""
        ...

    @abstractmethod
    async def fetch_events(self) -> list[dict]:
        """Fetch career events, workshops, fairs."""
        ...

    @abstractmethod
    async def fetch_research(self) -> list[dict]:
        """Fetch research opportunities."""
        ...

    @abstractmethod
    async def fetch_organizations(self) -> list[dict]:
        """Fetch student organizations."""
        ...

    @abstractmethod
    async def fetch_programs(self) -> list[dict]:
        """Fetch special programs (honors, mentorship, etc.)."""
        ...

    async def fetch_all(self) -> list[dict]:
        """Fetch all opportunity types, normalize, and deduplicate."""
        all_opps = []

        jobs = await self.fetch_jobs()
        all_opps.extend(jobs)

        events = await self.fetch_events()
        all_opps.extend(events)

        research = await self.fetch_research()
        all_opps.extend(research)

        organizations = await self.fetch_organizations()
        all_opps.extend(organizations)

        programs = await self.fetch_programs()
        all_opps.extend(programs)

        return deduplicate(all_opps)
