"""
Experience matcher: recommends university experiences based on
what a student needs for their target career path.
"""
from __future__ import annotations

from typing import Any

from app.recommendation.career_matcher import CAREER_DATABASE


# University experiences that can fill skill/experience gaps
EXPERIENCE_CATALOG: list[dict] = [
    {"type": "research", "title": "Join a Faculty Research Lab", "description": "Work with a professor on active research in your area of interest.", "skills_developed": ["research methodology", "academic writing", "data analysis", "python", "statistics"], "careers": ["Research Scientist", "Data Scientist", "Machine Learning Engineer"]},
    {"type": "research", "title": "Undergraduate Research Program", "description": "Apply for structured undergraduate research opportunities.", "skills_developed": ["research methodology", "presentation", "critical thinking"], "careers": ["Research Scientist", "Data Scientist"]},
    {"type": "organization", "title": "Join ACM Student Chapter", "description": "Participate in programming competitions and tech talks.", "skills_developed": ["algorithms", "data structures", "networking", "teamwork"], "careers": ["Software Engineer", "Full Stack Developer"]},
    {"type": "organization", "title": "Join IEEE Student Branch", "description": "Engage with electrical and computer engineering community.", "skills_developed": ["networking", "systems", "hardware", "leadership"], "careers": ["Systems Engineer", "Cloud Engineer"]},
    {"type": "organization", "title": "Join Cybersecurity Club", "description": "Participate in CTF competitions and security workshops.", "skills_developed": ["network security", "penetration testing", "linux", "incident response"], "careers": ["Cybersecurity Analyst"]},
    {"type": "organization", "title": "Join Data Science Club", "description": "Work on data projects and participate in Kaggle competitions.", "skills_developed": ["python", "machine learning", "data visualization", "statistics"], "careers": ["Data Scientist", "Data Engineer", "Machine Learning Engineer", "Business Intelligence Analyst"]},
    {"type": "hackathon", "title": "Participate in RowdyHacks", "description": "UTSA's flagship hackathon — build a project in 24 hours.", "skills_developed": ["rapid prototyping", "teamwork", "presentation", "full stack"], "careers": ["Software Engineer", "Full Stack Developer", "Mobile Developer", "Product Manager"]},
    {"type": "hackathon", "title": "Participate in External Hackathons", "description": "Compete in HackTX, TAMUHack, or other regional hackathons.", "skills_developed": ["rapid prototyping", "teamwork", "networking"], "careers": ["Software Engineer", "Full Stack Developer"]},
    {"type": "event", "title": "Attend Career Fair", "description": "Connect with employers at UTSA career fairs.", "skills_developed": ["networking", "communication", "interview skills"], "careers": ["Software Engineer", "Data Engineer", "Cybersecurity Analyst", "Business Intelligence Analyst", "Product Manager"]},
    {"type": "event", "title": "Attend Tech Industry Workshops", "description": "Attend workshops on cloud, security, data, or development.", "skills_developed": ["specific technical skills", "industry knowledge"], "careers": ["Cloud Engineer", "DevOps Engineer", "Software Engineer"]},
    {"type": "certification", "title": "Earn AWS Cloud Practitioner", "description": "Get certified in cloud fundamentals.", "skills_developed": ["aws", "cloud computing", "networking"], "careers": ["Cloud Engineer", "DevOps Engineer", "Software Engineer"]},
    {"type": "certification", "title": "Earn CompTIA Security+", "description": "Industry-recognized entry-level security certification.", "skills_developed": ["network security", "compliance", "incident response", "encryption"], "careers": ["Cybersecurity Analyst", "Systems Engineer"]},
    {"type": "certification", "title": "Earn Google Data Analytics Certificate", "description": "Learn data analytics fundamentals.", "skills_developed": ["sql", "data visualization", "data analysis", "spreadsheets"], "careers": ["Data Scientist", "Business Intelligence Analyst", "Data Engineer"]},
    {"type": "internship", "title": "Apply for Local Internships", "description": "Apply to internships at San Antonio tech companies.", "skills_developed": ["professional experience", "industry exposure", "technical skills"], "careers": ["Software Engineer", "Data Engineer", "Cybersecurity Analyst", "Cloud Engineer"]},
    {"type": "internship", "title": "Apply for Summer REU Programs", "description": "NSF Research Experiences for Undergraduates programs.", "skills_developed": ["research", "academic writing", "specialized skills"], "careers": ["Research Scientist", "Data Scientist", "Machine Learning Engineer"]},
    {"type": "project", "title": "Build a Portfolio Project", "description": "Create a substantial project showcasing your skills.", "skills_developed": ["technical skills", "project management", "documentation"], "careers": ["Software Engineer", "Full Stack Developer", "Data Engineer", "Mobile Developer"]},
    {"type": "project", "title": "Contribute to Open Source", "description": "Find and contribute to an open source project on GitHub.", "skills_developed": ["git", "collaboration", "code review", "documentation"], "careers": ["Software Engineer", "DevOps Engineer", "Full Stack Developer"]},
    {"type": "leadership", "title": "Become an Organization Officer", "description": "Take a leadership role in a student organization.", "skills_developed": ["leadership", "communication", "project management", "teamwork"], "careers": ["Product Manager", "Software Engineer", "Business Intelligence Analyst"]},
    {"type": "leadership", "title": "Become a Teaching Assistant", "description": "TA for a CS or data course to deepen your knowledge.", "skills_developed": ["communication", "deep technical knowledge", "mentoring"], "careers": ["Research Scientist", "Software Engineer", "Data Scientist"]},
    {"type": "volunteer", "title": "Mentor Younger Students", "description": "Help freshmen and sophomores with coursework and career planning.", "skills_developed": ["leadership", "communication", "mentoring"], "careers": ["Product Manager", "UX Researcher"]},
    {"type": "program", "title": "Join Honors College Research", "description": "Honors thesis or capstone research project.", "skills_developed": ["research", "academic writing", "critical thinking"], "careers": ["Research Scientist", "Data Scientist"]},
    {"type": "competition", "title": "Enter Coding Competitions", "description": "ICPC, LeetCode contests, or CodeForces.", "skills_developed": ["algorithms", "data structures", "problem solving"], "careers": ["Software Engineer", "Machine Learning Engineer"]},
]


class ExperienceMatcher:
    """Recommends university experiences based on career gaps."""

    def __init__(self, experience_catalog: list[dict] | None = None):
        self.catalog = experience_catalog or EXPERIENCE_CATALOG

    def match_experiences(
        self,
        student: dict,
        career_target: str,
        available_experiences: list[dict] | None = None,
    ) -> list[dict]:
        """Return ranked experience recommendations for a student targeting a specific career."""
        experiences = available_experiences or self.catalog
        readiness = self._assess_readiness(student, career_target)
        gaps = readiness.get("weak_areas", [])
        student_skills = set(s.lower() for s in (student.get("skills", []) + student.get("technical_skills", [])))

        # Already-done experiences
        student_orgs = set(o.lower() if isinstance(o, str) else o.get("name", "").lower() for o in student.get("organizations", []))
        student_certs = set(c.lower() for c in student.get("certifications", []))
        student_hackathons = set(h.lower() for h in student.get("hackathons", []))

        results = []
        for exp in experiences:
            # Skip if the experience is for a different career
            exp_careers = [c.lower() for c in exp.get("careers", [])]
            if exp_careers and not any(career_target.lower() in c or c in career_target.lower() for c in exp_careers):
                continue

            # Skip if already done (rough check)
            title_lower = exp["title"].lower()
            if any(o in title_lower for o in student_orgs):
                continue
            if exp["type"] == "certification" and any(c in title_lower for c in student_certs):
                continue

            # Score: how many gap skills does this experience develop?
            exp_skills = set(s.lower() for s in exp.get("skills_developed", []))
            gap_skills = set(g.lower() for g in gaps)
            gap_coverage = len(exp_skills & gap_skills)
            new_skills = len(exp_skills - student_skills)

            relevance = min(100, gap_coverage * 25 + new_skills * 15 + 10)

            reason = self._build_reason(exp, gap_coverage, gap_skills & exp_skills, career_target)
            action = self._build_action(exp)

            results.append({
                "type": exp["type"],
                "title": exp["title"],
                "description": exp["description"],
                "relevance_score": relevance,
                "reason": reason,
                "action": action,
            })

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:15]

    def _assess_readiness(self, student: dict, career: str) -> dict:
        """Assess how ready a student is for a target career."""
        # Find career in database
        career_data = None
        for c in CAREER_DATABASE:
            if c["name"].lower() == career.lower():
                career_data = c
                break

        if not career_data:
            return {"readiness": 50, "strong_areas": [], "weak_areas": []}

        student_skills = set(s.lower() for s in (student.get("skills", []) + student.get("technical_skills", [])))
        career_skills = set(s.lower() for s in career_data.get("typical_skills", []))

        strong = sorted(student_skills & career_skills)
        weak = sorted(career_skills - student_skills)

        if career_skills:
            readiness = round((len(strong) / len(career_skills)) * 100)
        else:
            readiness = 50

        # Bonus for experience
        if student.get("experience"):
            readiness = min(100, readiness + len(student["experience"]) * 3)

        return {
            "readiness": readiness,
            "strong_areas": strong,
            "weak_areas": weak,
        }

    def assess_readiness(self, student: dict, career: str) -> dict:
        """Public interface for readiness assessment."""
        return self._assess_readiness(student, career)

    def _build_reason(self, exp: dict, gap_coverage: int, covered_gaps: set, career: str) -> str:
        if gap_coverage >= 3:
            return f"Highly relevant — develops {', '.join(list(covered_gaps)[:3])} which you need for {career}."
        elif gap_coverage >= 1:
            return f"Develops {', '.join(list(covered_gaps)[:2])}, filling a gap in your {career} preparation."
        else:
            return f"Builds relevant experience for a {career} career path."

    def _build_action(self, exp: dict) -> str:
        actions = {
            "research": "Talk to your advisor about available research positions.",
            "organization": "Attend the next meeting and introduce yourself.",
            "hackathon": "Register for the next upcoming event.",
            "event": "Add this to your calendar and attend.",
            "certification": "Start studying and schedule the exam.",
            "internship": "Update your resume and apply this week.",
            "project": "Start building this weekend — aim to complete in 2-4 weeks.",
            "leadership": "Express interest at the next organization meeting.",
            "volunteer": "Reach out to the program coordinator.",
            "program": "Check eligibility and apply before the deadline.",
            "competition": "Sign up and start practicing on LeetCode or similar.",
        }
        return actions.get(exp.get("type", ""), "Take action on this opportunity this week.")

    def suggest_actions(self, gaps: list[str], career: str) -> list[dict]:
        """Suggest concrete actions to fill skill gaps."""
        actions = []
        for gap in gaps[:5]:
            action = {
                "skill": gap,
                "suggestions": self._get_gap_suggestions(gap, career),
            }
            actions.append(action)
        return actions

    def _get_gap_suggestions(self, skill: str, career: str) -> list[str]:
        suggestions = []
        skill_lower = skill.lower()

        for exp in self.catalog:
            exp_skills = [s.lower() for s in exp.get("skills_developed", [])]
            if skill_lower in exp_skills:
                suggestions.append(exp["title"])

        if not suggestions:
            suggestions.append(f"Take an online course or tutorial on {skill}.")
            suggestions.append(f"Build a project that uses {skill}.")

        return suggestions[:3]
