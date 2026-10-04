"""
Candidate Retrieval for Rowdy Plan Recommendation Engine.

Retrieves candidate opportunities, careers, and experiences
using embedding similarity and attribute-based filtering.
"""

import numpy as np
from typing import Optional

from app.recommendation.embeddings import EmbeddingService


class CandidateRetriever:
    """
    Retrieves candidate items (jobs, careers, experiences) using
    embedding similarity and filtering.

    Works with in-memory data for testing/mock scenarios and
    can be extended to use pgvector for production.
    """

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self._embedding_service = embedding_service or EmbeddingService()

    def retrieve_jobs(
        self,
        student_embedding: np.ndarray,
        filters: dict,
        limit: int = 50,
        opportunities: Optional[list[dict]] = None,
    ) -> list[dict]:
        """
        Retrieve candidate job opportunities by embedding similarity + filters.

        Args:
            student_embedding: Student profile embedding vector.
            filters: Dict of filter criteria (location, job_type, etc.).
            limit: Maximum number of results to return.
            opportunities: Optional list of opportunity dicts for in-memory mode.
                          If None, returns empty list (DB mode not yet implemented).

        Returns:
            List of opportunity dicts sorted by similarity score.
        """
        if opportunities is None:
            return []

        # Apply hard filters first
        filtered = self._apply_filters(opportunities, filters)

        # Score by embedding similarity
        scored = []
        for opp in filtered:
            opp_embedding = self._embedding_service.build_opportunity_embedding(opp)
            similarity = self._embedding_service.compute_similarity(
                student_embedding, opp_embedding
            )
            scored.append({
                **opp,
                "_retrieval_score": float(similarity),
            })

        # Sort by similarity descending
        scored.sort(key=lambda x: x["_retrieval_score"], reverse=True)

        return scored[:limit]

    def retrieve_careers(
        self,
        student_embedding: np.ndarray,
        limit: int = 10,
        career_paths: Optional[list[dict]] = None,
    ) -> list[dict]:
        """
        Retrieve career paths by embedding similarity.

        Args:
            student_embedding: Student profile embedding vector.
            limit: Maximum number of results.
            career_paths: Optional list of career path dicts for in-memory mode.

        Returns:
            List of career dicts sorted by similarity.
        """
        if career_paths is None:
            return []

        scored = []
        for career in career_paths:
            # Build a text representation of the career
            career_text = self._career_to_text(career)
            career_embedding = self._embedding_service.encode(career_text)
            similarity = self._embedding_service.compute_similarity(
                student_embedding, career_embedding
            )
            scored.append({
                **career,
                "_retrieval_score": float(similarity),
            })

        scored.sort(key=lambda x: x["_retrieval_score"], reverse=True)
        return scored[:limit]

    def retrieve_experiences(
        self,
        student_embedding: np.ndarray,
        student_profile: dict,
        limit: int = 20,
        available_experiences: Optional[list[dict]] = None,
    ) -> list[dict]:
        """
        Retrieve relevant experiences (events, workshops, competitions)
        for the student.

        Args:
            student_embedding: Student profile embedding vector.
            student_profile: Student profile dict for additional filtering.
            limit: Maximum number of results.
            available_experiences: Optional list of experience dicts.

        Returns:
            List of experience dicts sorted by relevance.
        """
        if available_experiences is None:
            return []

        scored = []
        for exp in available_experiences:
            exp_text = self._experience_to_text(exp)
            exp_embedding = self._embedding_service.encode(exp_text)
            similarity = self._embedding_service.compute_similarity(
                student_embedding, exp_embedding
            )

            # Boost score for experiences matching student's career interests
            boost = self._compute_interest_boost(student_profile, exp)

            final_score = float(similarity) + boost
            scored.append({
                **exp,
                "_retrieval_score": final_score,
            })

        scored.sort(key=lambda x: x["_retrieval_score"], reverse=True)
        return scored[:limit]

    def retrieve_from_list(
        self,
        student_embedding: np.ndarray,
        items: list[dict],
        text_key: str = "description",
        limit: int = 20,
    ) -> list[dict]:
        """
        Generic retrieval from a list of items using embedding similarity.
        Useful for testing and mock data.

        Args:
            student_embedding: Student embedding vector.
            items: List of item dicts.
            text_key: Key containing text to embed for each item.
            limit: Max results.

        Returns:
            Scored and sorted list of items.
        """
        scored = []
        for item in items:
            text = item.get(text_key, "")
            if not text:
                # Try building from multiple fields
                text = " ".join(
                    str(v) for v in item.values() if isinstance(v, str)
                )
            item_embedding = self._embedding_service.encode(text)
            similarity = self._embedding_service.compute_similarity(
                student_embedding, item_embedding
            )
            scored.append({
                **item,
                "_retrieval_score": float(similarity),
            })

        scored.sort(key=lambda x: x["_retrieval_score"], reverse=True)
        return scored[:limit]

    def _apply_filters(
        self, opportunities: list[dict], filters: dict
    ) -> list[dict]:
        """Apply hard filters to a list of opportunities."""
        result = list(opportunities)

        # Filter by job type
        job_type = filters.get("job_type")
        if job_type:
            job_type_lower = job_type.lower()
            result = [
                opp for opp in result
                if opp.get("type", "").lower() == job_type_lower
                or not opp.get("type")
            ]

        # Filter by location
        location = filters.get("location")
        if location:
            location_lower = location.lower()
            result = [
                opp for opp in result
                if not opp.get("location")
                or location_lower in opp.get("location", "").lower()
                or opp.get("location", "").lower() == "remote"
            ]

        # Filter by work type (remote/hybrid/on-site)
        work_type = filters.get("work_type")
        if work_type:
            work_type_lower = work_type.lower()
            result = [
                opp for opp in result
                if not opp.get("work_type")
                or opp.get("work_type", "").lower() == work_type_lower
                or opp.get("work_type", "").lower() == "flexible"
            ]

        # Filter by minimum match threshold
        min_score = filters.get("min_score")
        if min_score:
            result = [
                opp for opp in result
                if opp.get("_retrieval_score", 0) >= min_score
            ]

        # Filter by required major
        major = filters.get("major")
        if major:
            major_lower = major.lower()
            result = [
                opp for opp in result
                if not opp.get("required_majors")
                or any(
                    major_lower in m.lower() or m.lower() in major_lower
                    for m in opp.get("required_majors", [])
                )
            ]

        return result

    def _career_to_text(self, career: dict) -> str:
        """Convert career dict to text for embedding."""
        parts = []
        if career.get("name"):
            parts.append(career["name"])
        if career.get("description"):
            parts.append(career["description"])
        if career.get("required_skills"):
            parts.append(f"Skills: {', '.join(career['required_skills'][:15])}")
        if career.get("industries"):
            parts.append(f"Industries: {', '.join(career['industries'][:5])}")
        return ". ".join(parts) if parts else "Career path"

    def _experience_to_text(self, exp: dict) -> str:
        """Convert experience dict to text for embedding."""
        parts = []
        if exp.get("title"):
            parts.append(exp["title"])
        if exp.get("description"):
            parts.append(exp["description"][:300])
        if exp.get("skills"):
            parts.append(f"Skills: {', '.join(exp['skills'][:10])}")
        if exp.get("type"):
            parts.append(f"Type: {exp['type']}")
        return ". ".join(parts) if parts else "Experience"

    def _compute_interest_boost(
        self, student_profile: dict, experience: dict
    ) -> float:
        """Compute a small boost for experiences matching student interests."""
        boost = 0.0
        student_interests = set(
            i.lower() for i in student_profile.get("career_interests", [])
        )
        student_industries = set(
            i.lower() for i in student_profile.get("industries", [])
        )

        exp_tags = set(
            t.lower() for t in experience.get("tags", [])
        )
        exp_career = experience.get("career_path", "").lower()

        # Boost if experience matches career interest
        if exp_career and exp_career in student_interests:
            boost += 0.1

        # Boost if experience tags match industries
        if exp_tags & student_industries:
            boost += 0.05

        return boost
