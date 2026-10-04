"""
Profile Builder for Rowdy Plan Recommendation Engine.

Normalizes raw student input into clean StudentProfile dicts,
merges resume data, and calculates profile completeness.
"""

from typing import Any


class ProfileBuilder:
    """Builds and normalizes student profiles for the recommendation engine."""

    # Fields and their weights for profile strength calculation
    STRENGTH_WEIGHTS = {
        "has_resume": 20,
        "has_skills": 20,
        "has_experience": 15,
        "has_goals": 15,
        "has_education": 10,
        "has_interests": 10,
        "has_location_prefs": 5,
        "has_certifications": 5,
    }

    def build_profile(self, student_data: dict) -> dict:
        """
        Normalize raw student input into a clean StudentProfile dict.

        Args:
            student_data: Raw student input from form or API.

        Returns:
            A normalized StudentProfile dict with consistent keys and types.
        """
        profile = {
            # Identity
            "student_id": str(student_data.get("student_id", "")),
            "name": self._clean_string(student_data.get("name", "")),
            "email": self._clean_string(student_data.get("email", "")),

            # Education
            "university": self._clean_string(
                student_data.get("university", "University of Texas at San Antonio")
            ),
            "major": self._clean_string(student_data.get("major", "")),
            "minor": self._clean_string(student_data.get("minor", "")),
            "gpa": self._normalize_gpa(student_data.get("gpa")),
            "graduation_year": self._normalize_year(student_data.get("graduation_year")),
            "degree_level": self._normalize_degree_level(student_data.get("degree_level", "bachelor")),
            "coursework": self._normalize_list(student_data.get("coursework", [])),
            "certifications": self._normalize_list(student_data.get("certifications", [])),

            # Skills
            "skills": self._normalize_skills(student_data.get("skills", [])),
            "programming_languages": self._normalize_list(
                student_data.get("programming_languages", [])
            ),
            "frameworks": self._normalize_list(student_data.get("frameworks", [])),
            "tools": self._normalize_list(student_data.get("tools", [])),

            # Experience
            "experience": self._normalize_experience(student_data.get("experience", [])),
            "projects": self._normalize_list(student_data.get("projects", [])),

            # Career
            "career_goal": self._clean_string(student_data.get("career_goal", "")),
            "career_interests": self._normalize_list(student_data.get("career_interests", [])),
            "industries": self._normalize_list(student_data.get("industries", [])),

            # Preferences
            "location_preferences": self._normalize_list(
                student_data.get("location_preferences", [])
            ),
            "work_type_preference": self._normalize_work_type(
                student_data.get("work_type_preference", "")
            ),
            "job_type_preference": self._normalize_job_type(
                student_data.get("job_type_preference", "")
            ),
            "work_authorization": self._clean_string(
                student_data.get("work_authorization", "")
            ),

            # Resume
            "resume_text": student_data.get("resume_text", ""),
            "has_resume": bool(student_data.get("resume_text", "")),
        }

        return profile

    def merge_resume_data(self, profile: dict, resume_data: dict) -> dict:
        """
        Merge parsed resume data into profile.
        Explicit student input is preferred over extracted resume data.

        Args:
            profile: The normalized student profile.
            resume_data: Data extracted from resume parsing.

        Returns:
            Updated profile with resume data merged in.
        """
        merged = dict(profile)

        # Skills: union of explicit and resume-extracted
        resume_skills = self._normalize_skills(resume_data.get("skills", []))
        existing_skills = set(s.lower() for s in merged.get("skills", []))
        for skill in resume_skills:
            if skill.lower() not in existing_skills:
                merged["skills"].append(skill)
                existing_skills.add(skill.lower())

        # Programming languages: union
        resume_langs = self._normalize_list(resume_data.get("programming_languages", []))
        existing_langs = set(l.lower() for l in merged.get("programming_languages", []))
        for lang in resume_langs:
            if lang.lower() not in existing_langs:
                merged["programming_languages"].append(lang)

        # Experience: add resume experiences not already present
        resume_exp = self._normalize_experience(resume_data.get("experience", []))
        existing_titles = set(
            e.get("title", "").lower() for e in merged.get("experience", [])
        )
        for exp in resume_exp:
            if exp.get("title", "").lower() not in existing_titles:
                merged["experience"].append(exp)

        # Certifications: union
        resume_certs = self._normalize_list(resume_data.get("certifications", []))
        existing_certs = set(c.lower() for c in merged.get("certifications", []))
        for cert in resume_certs:
            if cert.lower() not in existing_certs:
                merged["certifications"].append(cert)

        # Only fill empty fields from resume
        if not merged.get("major") and resume_data.get("major"):
            merged["major"] = self._clean_string(resume_data["major"])

        if not merged.get("gpa") and resume_data.get("gpa"):
            merged["gpa"] = self._normalize_gpa(resume_data["gpa"])

        if not merged.get("career_goal") and resume_data.get("career_goal"):
            merged["career_goal"] = self._clean_string(resume_data["career_goal"])

        merged["has_resume"] = True
        return merged

    def calculate_profile_strength(self, profile: dict) -> int:
        """
        Calculate profile completeness score (0-100).

        Args:
            profile: The normalized student profile.

        Returns:
            Integer score 0-100 based on how complete the profile is.
        """
        score = 0

        # Has resume (20 pts)
        if profile.get("has_resume") or profile.get("resume_text"):
            score += self.STRENGTH_WEIGHTS["has_resume"]

        # Has skills (20 pts) - scaled by count
        skills = profile.get("skills", [])
        if skills:
            skill_score = min(len(skills) / 5.0, 1.0)  # Max at 5+ skills
            score += int(self.STRENGTH_WEIGHTS["has_skills"] * skill_score)

        # Has experience (15 pts) - scaled by count
        experience = profile.get("experience", [])
        if experience:
            exp_score = min(len(experience) / 2.0, 1.0)  # Max at 2+ experiences
            score += int(self.STRENGTH_WEIGHTS["has_experience"] * exp_score)

        # Has goals (15 pts)
        if profile.get("career_goal") or profile.get("career_interests"):
            goal_score = 0.0
            if profile.get("career_goal"):
                goal_score += 0.6
            if profile.get("career_interests"):
                goal_score += 0.4
            score += int(self.STRENGTH_WEIGHTS["has_goals"] * min(goal_score, 1.0))

        # Has education (10 pts)
        edu_score = 0.0
        if profile.get("major"):
            edu_score += 0.4
        if profile.get("gpa"):
            edu_score += 0.3
        if profile.get("coursework"):
            edu_score += 0.3
        score += int(self.STRENGTH_WEIGHTS["has_education"] * min(edu_score, 1.0))

        # Has interests (10 pts)
        if profile.get("career_interests") or profile.get("industries"):
            score += self.STRENGTH_WEIGHTS["has_interests"]

        # Has location preferences (5 pts)
        if profile.get("location_preferences"):
            score += self.STRENGTH_WEIGHTS["has_location_prefs"]

        # Has certifications (5 pts)
        if profile.get("certifications"):
            score += self.STRENGTH_WEIGHTS["has_certifications"]

        return min(score, 100)

    # --- Private helpers ---

    def _clean_string(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _normalize_gpa(self, gpa: Any) -> float:
        if gpa is None:
            return 0.0
        try:
            gpa_val = float(gpa)
            return max(0.0, min(gpa_val, 4.0))
        except (ValueError, TypeError):
            return 0.0

    def _normalize_year(self, year: Any) -> int:
        if year is None:
            return 0
        try:
            return int(year)
        except (ValueError, TypeError):
            return 0

    def _normalize_degree_level(self, level: Any) -> str:
        if not level:
            return "bachelor"
        level_str = str(level).lower().strip()
        mapping = {
            "bs": "bachelor",
            "ba": "bachelor",
            "bachelor": "bachelor",
            "bachelors": "bachelor",
            "undergraduate": "bachelor",
            "ms": "master",
            "ma": "master",
            "master": "master",
            "masters": "master",
            "graduate": "master",
            "phd": "doctorate",
            "doctorate": "doctorate",
            "doctoral": "doctorate",
            "associate": "associate",
            "associates": "associate",
        }
        return mapping.get(level_str, "bachelor")

    def _normalize_skills(self, skills: Any) -> list:
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        if not isinstance(skills, list):
            return []
        return [str(s).strip() for s in skills if str(s).strip()]

    def _normalize_list(self, items: Any) -> list:
        if isinstance(items, str):
            items = [s.strip() for s in items.split(",") if s.strip()]
        if not isinstance(items, list):
            return []
        return [str(item).strip() for item in items if str(item).strip()]

    def _normalize_experience(self, experience: Any) -> list:
        if not isinstance(experience, list):
            return []
        normalized = []
        for exp in experience:
            if not isinstance(exp, dict):
                continue
            normalized.append({
                "title": str(exp.get("title", "")).strip(),
                "company": str(exp.get("company", "")).strip(),
                "duration_months": self._parse_duration(exp.get("duration_months", 0)),
                "description": str(exp.get("description", "")).strip(),
                "type": str(exp.get("type", "other")).strip().lower(),
                "skills_used": self._normalize_list(exp.get("skills_used", [])),
            })
        return normalized

    def _parse_duration(self, duration: Any) -> int:
        try:
            return max(0, int(duration))
        except (ValueError, TypeError):
            return 0

    def _normalize_work_type(self, work_type: Any) -> str:
        if not work_type:
            return ""
        wt = str(work_type).lower().strip()
        if wt in ("remote", "on-site", "onsite", "hybrid", "flexible"):
            if wt == "onsite":
                return "on-site"
            return wt
        return ""

    def _normalize_job_type(self, job_type: Any) -> str:
        if not job_type:
            return ""
        jt = str(job_type).lower().strip()
        valid = {"internship", "full-time", "part-time", "co-op", "contract", "research"}
        if jt in valid:
            return jt
        # Handle variations
        mapping = {
            "fulltime": "full-time",
            "full time": "full-time",
            "parttime": "part-time",
            "part time": "part-time",
            "intern": "internship",
        }
        return mapping.get(jt, "")
