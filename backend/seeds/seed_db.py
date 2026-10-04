"""
Seed script: loads sample students, opportunities, and careers into the app.
Can be run standalone or imported.

Usage:
    python -m seeds.seed_db
"""
from __future__ import annotations

import json
import sys
import os

# Add parent to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.mock_store import store
from app.ingestion.utsa_provider import UTSAProvider


def load_students():
    """Load sample student profiles from JSON."""
    seed_path = os.path.join(os.path.dirname(__file__), "students.json")
    with open(seed_path) as f:
        students = json.load(f)

    for student_data in students:
        store.add_student(student_data)
        print(f"  Added student: {student_data.get('major')} {student_data.get('year')}")

    return len(students)


async def load_opportunities():
    """Load UTSA mock opportunities."""
    provider = UTSAProvider(use_live_data=False)
    opportunities = await provider.fetch_all()

    existing_titles = {o.get("title", "").lower() for o in store.opportunities}
    added = 0
    for opp in opportunities:
        if opp.get("title", "").lower() not in existing_titles:
            store.add_opportunity(opp)
            existing_titles.add(opp.get("title", "").lower())
            added += 1

    return added


def main():
    """Seed the in-memory store."""
    import asyncio

    print("Seeding Rowdy Plan...")

    # Students
    print("\nLoading students:")
    student_count = load_students()
    print(f"  → {student_count} students loaded")

    # Opportunities
    print("\nLoading opportunities:")
    opp_count = asyncio.run(load_opportunities())
    print(f"  → {opp_count} opportunities loaded")

    # Careers (already loaded by InMemoryStore init)
    print(f"\nCareers: {len(store.careers)} career paths available")

    print("\nSeed complete!")
    print(f"  Students: {len(store.students)}")
    print(f"  Opportunities: {len(store.opportunities)}")
    print(f"  Careers: {len(store.careers)}")


if __name__ == "__main__":
    main()
