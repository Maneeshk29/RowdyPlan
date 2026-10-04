"""
Job Matcher for Rowdy Plan Recommendation Engine.

Deterministic scoring of opportunities against student profiles
using weighted sub-scores for skills, experience, education,
career interest, location, and goals.
"""

from __future__ import annotations

import re
from typing import Any, Optional

try:
    from app.recommendation.feature_extractor import SKILL_TAXONOMY
except Exception:
    SKILL_TAXONOMY = []


class JobMatcher:
    """
    Scores and ranks job opportunities against a student profile.

    All scoring is deterministic -- uses set intersection, cosine similarity,
    and weighted rules. No LLM-generated numbers.

    match_score = (
        0.35 * skill_similarity +
        0.20 * experience_similarity +
        0.15 * education_match +
        0.10 * career_interest_match +
        0.10 * location_match +
        0.10 * student_goal_match
    )
    Each sub-score is 0-100.
    """

    WEIGHTS = {
        "skill": 0.35,
        "experience": 0.20,
        "education": 0.15,
        "career_interest": 0.10,
        "location": 0.10,
        "goal": 0.10,
    }

    GOAL_TYPE_MAP = {
        "internship": {"internship", "intern", "co-op", "co op"},
        "full-time": {"full-time", "full time", "full_time", "job", "contract"},
        "full_time": {"full-time", "full time", "full_time", "job", "contract"},
        "part-time": {"part-time", "freelance"},
        "part_time": {"part-time", "part time", "freelance"},
        "co-op": {"co-op", "internship"},
        "research": {"research", "research assistant", "lab"},
        "campus_employment": {"student worker", "campus", "on-campus", "part-time"},
        "exploring": set(),  # matches everything loosely
    }

    SKILL_ALIASES = {
        "js": "javascript",
        "reactjs": "react",
        "react.js": "react",
        "node": "node.js",
        "nodejs": "node.js",
        "postgres": "postgresql",
        "rest": "rest api",
        "apis": "rest api",
        "api": "rest api",
        "ml": "machine learning",
        "ai": "machine learning",
        "ci cd": "ci/cd",
        "cicd": "ci/cd",
        "k8s": "kubernetes",
        "ms excel": "excel",
        "powerbi": "power bi",
        "tableau desktop": "tableau",
    }

    MAJOR_ALIASES = {
        "cs": "computer science",
        "comp sci": "computer science",
        "se": "software engineering",
        "is": "information systems",
        "it": "information technology",
        "ds": "data science",
        "cyber": "cybersecurity",
    }

    CAREER_KEYWORDS = {
        "software engineer": {"software", "developer", "engineering", "swe", "backend", "frontend"},
        "data scientist": {"data", "analytics", "ml", "machine learning", "ai"},
        "data engineer": {"data", "etl", "pipeline", "warehouse"},
        "product manager": {"product", "pm", "management", "strategy"},
        "devops engineer": {"devops", "infrastructure", "cloud", "sre", "platform"},
        "cybersecurity analyst": {"security", "cyber", "infosec", "soc"},
        "full stack developer": {"full stack", "fullstack", "web developer", "web"},
        "ml engineer": {"machine learning", "ml", "ai", "deep learning", "model"},
        "mobile developer": {"mobile", "ios", "android", "flutter", "react native"},
        "cloud engineer": {"cloud", "aws", "azure", "gcp", "infrastructure"},
        "ux researcher": {"ux", "user experience", "design", "research", "usability"},
    }

    def score_opportunity(
        self,
        student: dict,
        opportunity: dict,
        student_features: dict | None = None,
        opp_features: dict | None = None,
    ) -> dict:
        """
        Compute full scoring breakdown for a student-opportunity pair.

        Args:
            student: Normalized student profile dict.
            opportunity: Opportunity dict.
            student_features: Pre-computed feature vectors for student.
            opp_features: Optional pre-computed features for opportunity.

        Returns:
            Dict with match_score, score_breakdown, matched/missing skills,
            reasoning, recommended_actions, and qualification_status.
        """
        all_student_skills = self._collect_student_skills(student)
        unique_opp_skills = self._collect_opportunity_skills(opportunity)

        # Compute sub-scores (each 0-100)
        skill_score, matched_skills, missing_skills = self._compute_skill_similarity(
            all_student_skills, unique_opp_skills,
        )
        experience_score = self._compute_experience_similarity(
            self._collect_student_experience(student),
            self._collect_opportunity_requirements(opportunity),
        )
        education_score = self._compute_education_match(student, opportunity)
        career_interest_score = self._compute_career_interest_match(
            student.get("career_interests", []),
            opportunity,
        )
        location_score = self._compute_location_match(
            self._collect_location_preferences(student),
            self._opportunity_location_text(opportunity),
        )
        goal_score = self._compute_goal_match(
            student.get("job_type_preference", student.get("current_goal", "")),
            self._opportunity_goal_text(opportunity),
        )

        # Deterministic weighted composite score
        match_score = (
            self.WEIGHTS["skill"] * skill_score
            + self.WEIGHTS["experience"] * experience_score
            + self.WEIGHTS["education"] * education_score
            + self.WEIGHTS["career_interest"] * career_interest_score
            + self.WEIGHTS["location"] * location_score
            + self.WEIGHTS["goal"] * goal_score
        )
        match_score = min(100, max(0, int(round(match_score))))

        # Determine qualification status before final score capping.
        qualification_status = self._determine_qualification(
            skill_score, student, opportunity, matched_skills, missing_skills,
        )
        if qualification_status == "NOT_ELIGIBLE":
            match_score = min(match_score, 39)
        elif qualification_status == "SKILL_GAP":
            match_score = min(match_score, 69)

        # Build reasoning and actions
        reasoning = self._build_reasoning(
            skill_score, experience_score, education_score,
            career_interest_score, location_score, goal_score,
            matched_skills, missing_skills, student, opportunity,
        )
        recommended_actions = self._build_recommended_actions(
            missing_skills, experience_score, student, opportunity,
        )

        return {
            "opportunity_id": str(opportunity.get("id", "")),
            "title": opportunity.get("title", ""),
            "organization": opportunity.get("organization", ""),
            "description": opportunity.get("description", ""),
            "location": opportunity.get("location", ""),
            "deadline": opportunity.get("deadline"),
            "url": opportunity.get("url", ""),
            "source": opportunity.get("source", ""),
            "compensation": opportunity.get("compensation", ""),
            "match_score": match_score,
            "score_breakdown": {
                "skill": round(skill_score, 1),
                "experience": round(experience_score, 1),
                "education": round(education_score, 1),
                "career_interest": round(career_interest_score, 1),
                "location": round(location_score, 1),
                "goal": round(goal_score, 1),
            },
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "reasoning": reasoning,
            "recommended_actions": recommended_actions,
            "qualification_status": qualification_status,
        }

    def _compute_skill_similarity(
        self,
        student_skills: list,
        opp_skills: list,
    ) -> tuple[float, list, list]:
        """
        Compute skill match score using set intersection with fuzzy matching.

        Returns:
            Tuple of (score 0-100, matched_skills list, missing_skills list).
        """
        if not opp_skills:
            return (50.0, [], [])  # Neutral score when no skills specified

        student_map = {
            self._canonical_skill(s): str(s).strip()
            for s in student_skills
            if str(s).strip()
        }
        opp_map = {
            self._canonical_skill(s): str(s).strip()
            for s in opp_skills
            if str(s).strip()
        }
        student_set = set(student_map)
        opp_set = set(opp_map)

        if not student_set:
            return (0.0, [], list(opp_skills))

        # Exact matches
        exact_matches = student_set & opp_set

        # Fuzzy matches (substring matching for remaining)
        remaining_opp = opp_set - exact_matches
        fuzzy_matched_opp = set()

        for opp_skill in remaining_opp:
            for stu_skill in student_set:
                if self._skills_are_related(stu_skill, opp_skill):
                    fuzzy_matched_opp.add(opp_skill)
                    break

        # Score: exact matches full credit, fuzzy 70%
        total_match_value = len(exact_matches) + 0.7 * len(fuzzy_matched_opp)
        score = (total_match_value / len(opp_set)) * 100.0
        score = min(score, 100.0)

        # Build matched/missing lists with original casing
        all_matched_lower = exact_matches | fuzzy_matched_opp
        matched = [opp_map[s] for s in opp_set if s in all_matched_lower]
        missing = [opp_map[s] for s in opp_set if s not in all_matched_lower]

        return (score, matched, missing)

    def _compute_experience_similarity(
        self,
        student_exp: list,
        opp_requirements: list,
    ) -> float:
        """
        Score experience relevance based on count, type, duration,
        and keyword overlap with requirements.

        Returns:
            Score 0-100.
        """
        if not opp_requirements and not student_exp:
            return 50.0
        if not student_exp:
            return 10.0

        score = 0.0

        # Base score for having any experience (30 pts)
        score += 30.0

        # Experience count bonus (up to 20)
        score += min(len(student_exp) * 10, 20)

        # Internship bonus (15 pts)
        if any(e.get("type", "").lower() == "internship" for e in student_exp):
            score += 15.0

        # Total duration bonus (up to 20)
        total_months = sum(e.get("duration_months", 0) for e in student_exp)
        score += min(total_months * 2, 20)

        # Keyword overlap with requirements (up to 15)
        if opp_requirements:
            exp_text = " ".join(
                f"{e.get('type', '')} {e.get('title', '')} "
                f"{e.get('organization', e.get('company', ''))} "
                f"{e.get('description', '')} {' '.join(e.get('skills_used', []))} "
                f"{' '.join(e.get('skills', []))}"
                for e in student_exp
            ).lower()

            matches = sum(
                1 for r in opp_requirements
                if any(word in exp_text for word in str(r).lower().split() if len(word) > 3)
            )
            if opp_requirements:
                keyword_score = (matches / len(opp_requirements)) * 15.0
                score += keyword_score

        return min(score, 100.0)

    def _compute_education_match(self, student: dict, opp: dict) -> float:
        """
        Score education match based on major, GPA, and coursework/certifications.

        Returns:
            Score 0-100.
        """
        score = 0.0

        # Major match (50 points possible)
        required_majors = [m.lower() for m in opp.get("required_majors", opp.get("majors", []))]
        preferred_majors = [m.lower() for m in opp.get("preferred_majors", [])]
        student_major = student.get("major", "").lower()

        if not required_majors and not preferred_majors:
            score += 50.0  # No major requirement = neutral
        elif student_major:
            if any(self._major_matches(student_major, m) for m in required_majors):
                score += 50.0
            elif any(self._major_matches(student_major, m) for m in preferred_majors):
                score += 35.0
            else:
                # STEM major gets partial credit
                stem_keywords = {
                    "engineering", "science", "computer", "data",
                    "math", "technology", "information",
                }
                if any(kw in student_major for kw in stem_keywords):
                    score += 20.0

        # GPA match (30 points possible)
        min_gpa = opp.get("minimum_gpa") or 0
        student_gpa = student.get("gpa") or 0
        if not min_gpa:
            score += 30.0  # No GPA requirement = full credit
        elif student_gpa >= min_gpa:
            score += 30.0
        elif student_gpa >= min_gpa - 0.2:
            score += 20.0
        elif student_gpa >= min_gpa - 0.5:
            score += 10.0

        # Coursework and certifications (20 points possible)
        coursework = student.get("coursework", [])
        certifications = student.get("certifications", [])
        if coursework:
            score += min(len(coursework) * 2, 10)
        if certifications:
            score += min(len(certifications) * 5, 10)

        return min(score, 100.0)

    def _compute_career_interest_match(
        self,
        student_interests: list,
        opp: dict,
    ) -> float:
        """
        Score how well the opportunity aligns with student career interests.

        Returns:
            Score 0-100.
        """
        if not student_interests:
            return 50.0  # Neutral when no interests specified

        opp_title = opp.get("title", "").lower()
        opp_category = opp.get("category", "").lower()
        opp_industry = opp.get("industry", "").lower()
        opp_desc = opp.get("description", "").lower()[:1000]
        opp_text = f"{opp_title} {opp_category} {opp_industry} {opp_desc}"

        best_score = 0.0

        for interest in student_interests:
            interest_lower = interest.lower()

            # Direct title match
            if opp_title and interest_lower and (
                self._contains_term(opp_title, interest_lower)
                or self._contains_term(interest_lower, opp_title)
            ):
                best_score = max(best_score, 100.0)
                break

            # Category match
            if opp_category and (
                interest_lower in opp_category or opp_category in interest_lower
            ):
                best_score = max(best_score, 80.0)
                continue

            # Keyword matching via career keywords map
            keywords = self.CAREER_KEYWORDS.get(interest_lower, set())
            kw_matches = sum(1 for kw in keywords if self._contains_term(opp_text, kw))
            if keywords and kw_matches > 0:
                kw_score = min((kw_matches / max(len(keywords), 1)) * 90, 90)
                best_score = max(best_score, kw_score)
                continue

            # Generic word overlap
            interest_words = set(interest_lower.split())
            if interest_words and any(self._contains_term(opp_text, w) for w in interest_words if len(w) > 3):
                best_score = max(best_score, 50.0)

        if best_score == 0.0:
            best_score = 30.0  # Base score for having interests

        return min(best_score, 100.0)

    def _compute_location_match(
        self,
        student_prefs: list,
        opp_location: str,
    ) -> float:
        """
        Score location match between student preferences and opportunity.

        Returns:
            Score 0-100.
        """
        if not opp_location:
            return 70.0  # No location specified = mostly fine

        opp_loc_lower = opp_location.lower()

        # Remote opportunities match everyone well
        if "remote" in opp_loc_lower:
            return 100.0

        if not student_prefs:
            return 60.0  # No preference stated = neutral

        prefs_lower = [p.lower() for p in student_prefs]

        # Check for exact or partial location match
        for pref in prefs_lower:
            if pref in opp_loc_lower or opp_loc_lower in pref:
                return 100.0

        # Hybrid gets decent credit
        if "hybrid" in opp_loc_lower:
            return 70.0

        # Student wants remote but job is on-site
        if any("remote" in pref for pref in prefs_lower):
            return 30.0

        # Same-state matching (Texas-specific for UTSA)
        texas_cities = {
            "san antonio", "austin", "dallas", "houston",
            "fort worth", "el paso", "san marcos",
        }
        student_texas = any(p in texas_cities for p in prefs_lower)
        opp_texas = any(city in opp_loc_lower for city in texas_cities)
        if student_texas and opp_texas:
            return 70.0

        return 40.0

    def _compute_goal_match(
        self,
        student_goal: str,
        opp_type: str,
    ) -> float:
        """
        Score alignment between student's job type preference and opportunity type.

        Returns:
            Score 0-100.
        """
        if not student_goal or not opp_type:
            return 60.0  # Neutral when unspecified

        goal_lower = student_goal.lower().replace("-", "_").strip()
        type_lower = opp_type.lower()

        # "exploring" matches everything loosely
        if goal_lower == "exploring":
            return 60.0

        # Direct match
        if goal_lower == type_lower.replace("-", "_").strip():
            return 100.0

        # Compatible types
        compatible = self.GOAL_TYPE_MAP.get(goal_lower, set())
        if any(self._contains_term(type_lower, gt) for gt in compatible):
            return 85.0

        if goal_lower == "internship" and self._contains_term(type_lower, "intern"):
            return 100.0
        if goal_lower == "full_time" and self._contains_term(type_lower, "job") and not any(
            self._contains_term(type_lower, term) for term in ("intern", "internship")
        ):
            return 85.0

        # Partial matches
        if goal_lower == "internship" and "job" in type_lower:
            return 40.0
        if goal_lower in ("full-time", "full_time") and "internship" in type_lower:
            return 30.0

        return 30.0

    def rank_opportunities(
        self,
        student: dict,
        opportunities: list[dict],
        student_features: dict | None = None,
    ) -> list[dict]:
        """
        Score and rank all opportunities for a student.

        Args:
            student: Normalized student profile dict.
            opportunities: List of opportunity dicts.
            student_features: Pre-computed feature vectors for student.

        Returns:
            List of scored opportunity dicts, sorted by match_score descending.
        """
        results = []
        for opp in opportunities:
            scored = self.score_opportunity(student, opp, student_features)
            results.append(scored)
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results

    # --- Feature collection helpers ---

    def _collect_student_skills(self, student: dict) -> list[str]:
        skills: list[str] = []
        for key in (
            "skills", "technical_skills", "soft_skills",
            "programming_languages", "frameworks", "tools",
            "coursework", "certifications",
        ):
            skills.extend(self._as_list(student.get(key, [])))

        for item in student.get("projects", []) or []:
            if isinstance(item, dict):
                skills.extend(self._as_list(item.get("skills", [])))
                skills.extend(self._extract_known_skills(
                    f"{item.get('title', '')} {item.get('description', '')}"
                ))

        resume_text = student.get("resume_text", "")
        if resume_text:
            skills.extend(self._extract_known_skills(resume_text))

        return self._dedupe_preserve(skills)

    def _collect_opportunity_skills(self, opportunity: dict) -> list[str]:
        skills = []
        for key in ("required_skills", "skills", "skill_tags", "tags"):
            skills.extend(self._as_list(opportunity.get(key, [])))
        skills.extend(self._extract_known_skills(self._opportunity_search_text(opportunity)))
        return self._dedupe_preserve(skills)

    def _collect_student_experience(self, student: dict) -> list[dict]:
        experience = list(student.get("experience", []) or [])
        for project in student.get("projects", []) or []:
            if isinstance(project, dict):
                experience.append({
                    "type": "project",
                    "title": project.get("title", ""),
                    "organization": project.get("organization", ""),
                    "description": project.get("description", ""),
                    "skills_used": project.get("skills", []),
                })
        return experience

    def _collect_opportunity_requirements(self, opportunity: dict) -> list[str]:
        requirements = []
        for key in (
            "requirements", "required_qualifications", "qualifications",
            "minimum_qualifications", "preferred_qualifications",
        ):
            requirements.extend(self._as_list(opportunity.get(key, [])))
        if not requirements:
            requirements.extend(self._extract_known_skills(self._opportunity_search_text(opportunity)))
        return self._dedupe_preserve(requirements)

    def _collect_location_preferences(self, student: dict) -> list[str]:
        return self._dedupe_preserve(
            self._as_list(student.get("location_preferences", []))
            + self._as_list(student.get("preferred_locations", []))
            + self._as_list(student.get("work_preferences", []))
            + self._as_list(student.get("work_type_preference", []))
        )

    def _opportunity_search_text(self, opportunity: dict) -> str:
        return " ".join(str(opportunity.get(key, "")) for key in (
            "title", "description", "organization", "requirements",
            "job_type", "employment_type", "category",
        ))

    def _opportunity_location_text(self, opportunity: dict) -> str:
        return " ".join(str(opportunity.get(key, "")) for key in (
            "location", "workplace", "workplace_type", "job_type", "employment_type",
        ))

    def _opportunity_goal_text(self, opportunity: dict) -> str:
        classifications = " ".join(str(opportunity.get(key) or "") for key in (
            "job_type", "employment_type",
        )).strip()
        if classifications:
            return classifications
        return " ".join(str(opportunity.get(key, "")) for key in (
            "type", "title", "job_type", "employment_type", "category",
        ))

    def _contains_term(self, text: str, term: str) -> bool:
        return bool(term and re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text))

    def _extract_known_skills(self, text: str) -> list[str]:
        if not text:
            return []
        haystack = f" {text.lower()} "
        skills = list(SKILL_TAXONOMY) or [
            "python", "java", "javascript", "typescript", "sql", "react",
            "node.js", "aws", "docker", "kubernetes", "machine learning",
            "data analysis", "excel", "communication", "leadership",
        ]
        found = []
        for skill in skills:
            canonical = self._canonical_skill(skill)
            pattern = r"(?<![a-z0-9+#.])" + re.escape(canonical) + r"(?![a-z0-9+#.])"
            if re.search(pattern, haystack):
                found.append(skill)
        return found

    def _canonical_skill(self, skill: Any) -> str:
        cleaned = str(skill).lower().strip()
        cleaned = cleaned.replace("_", " ").replace("-", " ")
        cleaned = re.sub(r"\s+", " ", cleaned)
        return self.SKILL_ALIASES.get(cleaned, cleaned)

    def _skills_are_related(self, student_skill: str, opp_skill: str) -> bool:
        if len(student_skill) >= 4 and len(opp_skill) >= 4:
            if student_skill in opp_skill or opp_skill in student_skill:
                return True
        student_tokens = {t for t in re.split(r"[^a-z0-9+#.]+", student_skill) if len(t) > 2}
        opp_tokens = {t for t in re.split(r"[^a-z0-9+#.]+", opp_skill) if len(t) > 2}
        return bool(student_tokens and opp_tokens and student_tokens == opp_tokens)

    def _major_matches(self, student_major: str, required_major: str) -> bool:
        student = self.MAJOR_ALIASES.get(student_major.lower().strip(), student_major.lower().strip())
        required = self.MAJOR_ALIASES.get(required_major.lower().strip(), required_major.lower().strip())
        return bool(student and required and (student in required or required in student))

    def _student_graduation_year(self, student: dict) -> str:
        explicit = student.get("graduation_year")
        if explicit:
            return str(explicit)
        grad_date = str(student.get("graduation_date", ""))
        match = re.search(r"\b(20[2-4]\d)\b", grad_date)
        return match.group(1) if match else ""

    def _as_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            result = []
            for item in value:
                if isinstance(item, dict):
                    result.extend(str(v) for v in item.values() if isinstance(v, (str, int, float)))
                else:
                    result.append(str(item))
            return [v.strip() for v in result if v and v.strip()]
        if isinstance(value, str):
            return [v.strip() for v in re.split(r"[,;\n|]+", value) if v.strip()]
        return [str(value).strip()] if str(value).strip() else []

    def _dedupe_preserve(self, values: list[str]) -> list[str]:
        seen = set()
        result = []
        for value in values:
            cleaned = str(value).strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key not in seen:
                seen.add(key)
                result.append(cleaned)
        return result

    # --- Private helpers for reasoning and actions ---

    def _build_reasoning(
        self,
        skill_score: float,
        experience_score: float,
        education_score: float,
        career_interest_score: float,
        location_score: float,
        goal_score: float,
        matched_skills: list,
        missing_skills: list,
        student: dict,
        opportunity: dict,
    ) -> list[str]:
        """Build human-readable reasoning for the match."""
        reasons = []

        total_skills = len(matched_skills) + len(missing_skills)
        if skill_score >= 70:
            skills_str = ", ".join(matched_skills[:5])
            reasons.append(
                f"Strong skill match ({len(matched_skills)} of {total_skills} "
                f"required skills): {skills_str}."
            )
        elif skill_score >= 40:
            reasons.append(
                f"Partial skill match ({len(matched_skills)} of {total_skills} "
                f"required skills). Missing: {', '.join(missing_skills[:3])}."
            )
        elif total_skills > 0:
            reasons.append(
                f"Limited skill overlap. Missing key skills: "
                f"{', '.join(missing_skills[:3])}."
            )

        if experience_score >= 70:
            reasons.append("Your experience aligns well with this role.")
        elif experience_score >= 40:
            reasons.append("Some relevant experience, but could strengthen further.")
        elif experience_score < 30:
            reasons.append(
                "Limited relevant experience. Projects or internships "
                "would strengthen your profile."
            )

        if education_score >= 70:
            major = student.get("major", "")
            if major:
                reasons.append(f"Your {major} background is a strong fit.")
            else:
                reasons.append("Education background is a strong fit.")

        if career_interest_score >= 70:
            reasons.append("This aligns well with your stated career interests.")

        if location_score >= 80:
            reasons.append("Location matches your preferences.")
        elif location_score < 50:
            reasons.append(
                "Location may not match your preferences. "
                "Check if remote options are available."
            )

        if not reasons:
            reasons.append("Matched based on your profile and career interests.")

        return reasons

    def _build_recommended_actions(
        self,
        missing_skills: list,
        experience_score: float,
        student: dict,
        opportunity: dict,
    ) -> list[str]:
        """Build actionable recommendations for the student."""
        actions = []

        if missing_skills:
            top_missing = missing_skills[:3]
            actions.append(
                f"Build skills in: {', '.join(top_missing)}"
            )

        if experience_score < 50:
            actions.append(
                "Seek projects, hackathons, or volunteer opportunities "
                "to build relevant experience."
            )

        if not student.get("has_resume") and not student.get("resume_text"):
            actions.append("Upload your resume to get better match insights.")

        opp_org = opportunity.get("organization", "")
        if opp_org:
            actions.append(f"Research {opp_org} to tailor your application.")

        actions.append("Tailor your resume keywords to match this posting.")

        return actions[:5]  # Cap at 5 actions

    def _determine_qualification(
        self,
        skill_score: float,
        student: dict,
        opportunity: dict,
        matched_skills: list,
        missing_skills: list,
    ) -> str:
        """Determine qualification status from scores and hard requirements."""
        missing_information = False
        # Check hard requirements
        required_majors = opportunity.get(
            "required_majors", opportunity.get("majors", [])
        )
        if required_majors:
            student_major = student.get("major", "").lower()
            if student_major and not any(
                self._major_matches(student_major, m.lower())
                for m in required_majors
            ):
                return "NOT_ELIGIBLE"
            missing_information |= not bool(student_major)

        required_years = opportunity.get("graduation_years", [])
        if required_years:
            student_year = self._student_graduation_year(student)
            normalized_years = {str(y) for y in required_years}
            if student_year and str(student_year) not in normalized_years:
                return "NOT_ELIGIBLE"
            missing_information |= not bool(student_year)

        min_gpa = opportunity.get("minimum_gpa", 0)
        if min_gpa:
            student_gpa = student.get("gpa")
            if student_gpa is not None and student_gpa < min_gpa:
                return "NOT_ELIGIBLE"
            missing_information |= student_gpa is None

        if opportunity.get("work_authorization_required"):
            student_auth = str(student.get("work_authorization") or "").lower().strip()
            allowed_auth = {
                "us citizen", "u.s. citizen", "us_citizen",
                "permanent resident", "green card", "authorized",
                "opt", "cpt", "h1b",
            }
            if student_auth and student_auth not in allowed_auth:
                return "NOT_ELIGIBLE"
            missing_information |= not bool(student_auth)

        if missing_information:
            return "UNKNOWN"

        if not matched_skills and not missing_skills:
            return "UNKNOWN"

        # Skill-based determination
        if skill_score >= 70:
            return "QUALIFIED"
        elif skill_score >= 50:
            return "LIKELY_QUALIFIED"
        elif skill_score >= 30:
            return "SKILL_GAP"
        else:
            if not matched_skills and missing_skills:
                return "NOT_ELIGIBLE"
            return "SKILL_GAP"
