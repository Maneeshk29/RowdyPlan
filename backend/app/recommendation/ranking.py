"""
Ranking Engine for Rowdy Plan Recommendation Engine.

Sorts, diversifies, and filters recommendation results.
"""

from typing import Optional


class RankingEngine:
    """Ranks, diversifies, and filters recommendation results."""

    def rank(
        self,
        items: list[dict],
        score_key: str = "match_score",
        limit: Optional[int] = None,
    ) -> list[dict]:
        """
        Sort items by score descending, apply optional limit.

        Args:
            items: List of scored items.
            score_key: Key to sort by.
            limit: Max number of items to return.

        Returns:
            Sorted list of items, optionally truncated.
        """
        sorted_items = sorted(
            items,
            key=lambda x: x.get(score_key, 0),
            reverse=True,
        )
        if limit is not None:
            return sorted_items[:limit]
        return sorted_items

    def apply_diversity(
        self,
        items: list[dict],
        diversity_key: str,
        max_per_group: int = 3,
    ) -> list[dict]:
        """
        Ensure variety in results by limiting items per group.

        Uses a round-robin approach: iterates through items in score order,
        adding each item only if its group has not yet hit the cap.

        Args:
            items: List of scored items, assumed already sorted by score.
            diversity_key: Key to group items by (e.g., "organization", "industry").
            max_per_group: Maximum items per group value.

        Returns:
            Filtered list maintaining score order with diversity constraints.
        """
        group_counts: dict[str, int] = {}
        diversified: list[dict] = []

        for item in items:
            group = str(item.get(diversity_key, "unknown")).lower()
            current_count = group_counts.get(group, 0)
            if current_count < max_per_group:
                diversified.append(item)
                group_counts[group] = current_count + 1

        return diversified

    def apply_qualification_filter(
        self,
        student: dict,
        opportunity: dict,
    ) -> str:
        """
        Determine student's qualification status for an opportunity.

        Returns one of:
            QUALIFIED - Meets all requirements
            LIKELY_QUALIFIED - Meets most requirements, minor gaps
            SKILL_GAP - Has relevant background but missing key skills
            NOT_ELIGIBLE - Fails hard requirements (major, year, authorization)
            UNKNOWN - Insufficient data to determine

        Args:
            student: Student profile dict.
            opportunity: Opportunity dict with requirements.

        Returns:
            Qualification status string.
        """
        if not student or not opportunity:
            return "UNKNOWN"

        disqualifiers = 0
        soft_gaps = 0
        checks_performed = 0

        # Check major requirement
        required_majors = opportunity.get("required_majors", [])
        if required_majors:
            checks_performed += 1
            student_major = student.get("major", "").lower()
            major_match = any(
                m.lower() in student_major or student_major in m.lower()
                for m in required_majors
            )
            if not major_match:
                # Check if related majors are accepted
                preferred_majors = opportunity.get("preferred_majors", [])
                if preferred_majors:
                    related_match = any(
                        m.lower() in student_major or student_major in m.lower()
                        for m in preferred_majors
                    )
                    if not related_match:
                        disqualifiers += 1
                    else:
                        soft_gaps += 1
                else:
                    disqualifiers += 1

        # Check graduation year
        required_grad_years = opportunity.get("graduation_years", [])
        if required_grad_years:
            checks_performed += 1
            student_year = student.get("graduation_year", 0)
            if student_year and student_year not in required_grad_years:
                disqualifiers += 1

        # Check minimum GPA
        min_gpa = opportunity.get("minimum_gpa", 0)
        if min_gpa and min_gpa > 0:
            checks_performed += 1
            student_gpa = student.get("gpa", 0)
            if student_gpa and student_gpa < min_gpa:
                if student_gpa >= min_gpa - 0.2:
                    soft_gaps += 1  # Close enough
                else:
                    disqualifiers += 1

        # Check required skills (percentage match)
        required_skills = opportunity.get("required_skills", [])
        if required_skills:
            checks_performed += 1
            student_skills = set(s.lower() for s in student.get("skills", []))
            student_langs = set(
                s.lower() for s in student.get("programming_languages", [])
            )
            student_all_skills = student_skills | student_langs
            matched = sum(
                1
                for skill in required_skills
                if skill.lower() in student_all_skills
            )
            match_pct = matched / len(required_skills) if required_skills else 0
            if match_pct < 0.3:
                disqualifiers += 1
            elif match_pct < 0.6:
                soft_gaps += 1

        # Check work authorization
        required_auth = opportunity.get("work_authorization_required", "")
        if required_auth:
            checks_performed += 1
            student_auth = student.get("work_authorization", "").lower()
            if student_auth:
                req_auth_lower = required_auth.lower()
                if req_auth_lower in ("us citizen", "us_citizen"):
                    if student_auth not in (
                        "us citizen",
                        "us_citizen",
                        "permanent resident",
                        "green card",
                    ):
                        disqualifiers += 1
                elif req_auth_lower == "authorized":
                    valid_auths = {
                        "us citizen",
                        "us_citizen",
                        "permanent resident",
                        "green card",
                        "authorized",
                        "opt",
                        "cpt",
                        "h1b",
                    }
                    if student_auth not in valid_auths:
                        disqualifiers += 1

        # Determine status
        if checks_performed == 0:
            return "UNKNOWN"

        if disqualifiers > 0:
            if disqualifiers == 1 and checks_performed >= 3:
                return "SKILL_GAP"
            return "NOT_ELIGIBLE"

        if soft_gaps > 0:
            return "LIKELY_QUALIFIED"

        return "QUALIFIED"
