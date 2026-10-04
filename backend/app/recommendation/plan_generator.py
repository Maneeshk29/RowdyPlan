"""
Rowdy Plan generator: orchestrates the full recommendation pipeline
and assembles the final plan output.
"""
from __future__ import annotations

from typing import Any

from app.recommendation.profile_builder import ProfileBuilder
from app.recommendation.feature_extractor import FeatureExtractor
from app.recommendation.job_matcher import JobMatcher
from app.recommendation.career_matcher import CareerMatcher
from app.recommendation.experience_matcher import ExperienceMatcher
from app.recommendation.resume_analyzer import ResumeAnalyzer
from app.recommendation.gap_analysis import GapAnalyzer
from app.recommendation.ranking import RankingEngine


class PlanGenerator:
    """Orchestrates the full Rowdy Plan generation pipeline."""

    def __init__(self):
        self.profile_builder = ProfileBuilder()
        self.feature_extractor = FeatureExtractor()
        self.job_matcher = JobMatcher()
        self.career_matcher = CareerMatcher()
        self.experience_matcher = ExperienceMatcher()
        self.resume_analyzer = ResumeAnalyzer()
        self.gap_analyzer = GapAnalyzer()
        self.ranking_engine = RankingEngine()

    def generate(
        self,
        student: dict,
        career_matches: list[dict] | None = None,
        job_matches: list[dict] | None = None,
        experience_matches: list[dict] | None = None,
        resume_analysis: dict | None = None,
        skill_gaps: list[dict] | None = None,
        opportunities: list[dict] | None = None,
        career_paths: list[dict] | None = None,
        include_resume_analysis: bool = True,
        max_career_matches: int = 5,
        max_job_matches: int = 20,
    ) -> dict:
        """
        Generate a complete Rowdy Plan for a student.

        Can accept pre-computed results (career_matches, job_matches, etc.)
        or compute everything from scratch using the student profile.

        Returns the full plan structure including career matches,
        job matches, experience recommendations, resume analysis,
        skill gaps, next steps, and timeline.
        """
        processing_steps = []

        # Step 1: Build/validate profile
        processing_steps.append({"step": "Analyzing your background", "status": "complete"})
        profile_strength = self.profile_builder.calculate_profile_strength(student)

        # Step 2: Resume analysis (use pre-computed or compute)
        if resume_analysis is None:
            if include_resume_analysis and student.get("resume_text"):
                processing_steps.append({"step": "Reading your resume", "status": "complete"})
                target = student.get("career_interests", ["Software Engineer"])[0] if student.get("career_interests") else "Software Engineer"
                resume_analysis = self.resume_analyzer.analyze(
                    student["resume_text"],
                    target,
                    student,
                )
            else:
                processing_steps.append({"step": "Reading your resume", "status": "skipped"})
        else:
            processing_steps.append({"step": "Reading your resume", "status": "complete"})

        # Step 3: Understand goals
        processing_steps.append({"step": "Understanding your goals", "status": "complete"})

        # Step 4: Feature extraction
        processing_steps.append({"step": "Mapping your skills", "status": "complete"})
        features = self.feature_extractor.extract_all_features(student)

        # Step 5: Career matching (use pre-computed or compute)
        processing_steps.append({"step": "Comparing career paths", "status": "complete"})
        if career_matches is None:
            career_matches = self.career_matcher.match_careers(
                student,
                career_paths,
                features,
                limit=max_career_matches,
            )

        # Step 6: Job matching (use pre-computed or compute)
        processing_steps.append({"step": "Searching university opportunities", "status": "complete"})
        if job_matches is None:
            job_matches = []
            if opportunities:
                job_opps = [o for o in opportunities if o.get("type") in ("job", "internship", "research", "campus")]
                if not job_opps:
                    job_opps = opportunities  # Use all if no job-type filter match
                raw_matches = self.job_matcher.rank_opportunities(student, job_opps, features)

                # Apply qualification filter
                for match in raw_matches:
                    opp = next((o for o in opportunities if str(o.get("id", "")) == match["opportunity_id"]), None)
                    if opp:
                        match["qualification_status"] = self.ranking_engine.apply_qualification_filter(student, opp)
                    else:
                        match["qualification_status"] = "UNKNOWN"

                job_matches = raw_matches[:max_job_matches]

        # Step 7: Calculate matches
        processing_steps.append({"step": "Calculating your matches", "status": "complete"})

        # Experience matching (use pre-computed or compute)
        top_career = career_matches[0]["career_name"] if career_matches else "Software Engineer"
        if experience_matches is None:
            experience_matches = self.experience_matcher.match_experiences(
                student,
                top_career,
            )

        # Gap analysis (use pre-computed or compute)
        if skill_gaps is None:
            from app.recommendation.career_matcher import CAREER_DATABASE
            career_data = None
            for c in CAREER_DATABASE:
                if c["name"].lower() == top_career.lower():
                    career_data = c
                    break
            career_data = career_data or CAREER_DATABASE[0]

            skill_gaps = self.gap_analyzer.analyze_gaps(student, career_data)
            skill_gaps = self.gap_analyzer.prioritize_gaps(skill_gaps)

        # Step 8: Build plan
        processing_steps.append({"step": "Building your Rowdy Plan", "status": "complete"})

        next_steps = self._generate_next_steps(
            career_matches, job_matches, experience_matches, skill_gaps, resume_analysis, student
        )
        timeline = self._generate_timeline(
            career_matches, job_matches, experience_matches, skill_gaps, resume_analysis, student
        )

        return {
            "student": self._safe_student_summary(student),
            "profile_strength": profile_strength,
            "career_matches": career_matches,
            "job_matches": job_matches,
            "experience_matches": experience_matches[:10],
            "resume_analysis": resume_analysis,
            "skill_gaps": skill_gaps[:10],
            "next_steps": next_steps,
            "timeline": timeline,
            "processing_steps": processing_steps,
        }

    def _generate_next_steps(
        self,
        career_matches: list,
        job_matches: list,
        experience_matches: list,
        skill_gaps: list,
        resume_analysis: dict | None,
        student: dict,
    ) -> list[str]:
        """Generate top 5 actionable next steps."""
        steps = []

        # Resume improvement
        if resume_analysis:
            score = resume_analysis.get("resume_score", 100)
            if score < 70:
                steps.append("Improve your resume — focus on adding measurable impact to bullet points.")

        # Skill gaps
        high_priority = [g for g in skill_gaps if g.get("priority") in ("critical", "high")]
        if high_priority:
            skills = ", ".join(g["skill"] for g in high_priority[:2])
            steps.append(f"Build skills in {skills} — these are high-priority for your target career.")

        # Top job
        if job_matches:
            top = job_matches[0]
            if top.get("match_score", 0) >= 70:
                steps.append(f"Apply to {top['title']} at {top.get('organization', 'the organization')} — strong match at {top['match_score']}%.")

        # Experience
        if experience_matches:
            top_exp = experience_matches[0]
            steps.append(f"{top_exp.get('action', 'Pursue')} — {top_exp.get('title', 'this opportunity')}.")

        # Career direction
        if career_matches:
            top_career = career_matches[0]
            if top_career.get("next_action"):
                steps.append(top_career["next_action"])

        # Always have at least one step
        if not steps:
            steps.append("Complete your profile to get personalized recommendations.")

        return steps[:5]

    def _generate_timeline(
        self,
        career_matches: list,
        job_matches: list,
        experience_matches: list,
        skill_gaps: list,
        resume_analysis: dict | None,
        student: dict,
    ) -> list[dict]:
        """Generate actionable timeline with 4 periods."""
        now_actions = []
        thirty_day_actions = []
        semester_actions = []
        year_actions = []

        # NOW: Immediate resume and profile fixes
        if resume_analysis and resume_analysis.get("resume_score", 100) < 80:
            now_actions.append("Update resume with measurable impact on bullet points.")
            missing = resume_analysis.get("missing_keywords", [])
            if missing:
                now_actions.append(f"Add missing keywords: {', '.join(missing[:3])}.")

        high_gaps = [g for g in skill_gaps if g.get("priority") == "critical"]
        if high_gaps:
            now_actions.append(f"Start learning {high_gaps[0]['skill']} — critical for your target career.")

        if not now_actions:
            now_actions.append("Review your Rowdy Plan matches and save opportunities you're interested in.")

        # NEXT 30 DAYS: Applications and experiences
        if job_matches:
            qualified = [j for j in job_matches if j.get("qualification_status") in ("QUALIFIED", "LIKELY_QUALIFIED")]
            count = min(10, len(qualified))
            if count:
                thirty_day_actions.append(f"Apply to {count} matched opportunities.")

        if experience_matches:
            for exp in experience_matches[:2]:
                thirty_day_actions.append(f"{exp.get('title', 'Complete a recommended experience')}.")

        if not thirty_day_actions:
            thirty_day_actions.append("Explore recommended career paths and start networking.")

        # NEXT SEMESTER: Skill building and deeper engagement
        medium_gaps = [g for g in skill_gaps if g.get("priority") in ("high", "medium")]
        for gap in medium_gaps[:2]:
            semester_actions.append(f"Complete coursework or certification in {gap['skill']}.")

        if career_matches:
            top = career_matches[0]
            if top.get("recommended_courses"):
                semester_actions.append(f"Take {top['recommended_courses'][0]} to strengthen your candidacy.")

        if not semester_actions:
            semester_actions.append("Build a portfolio project aligned with your target career.")

        # NEXT YEAR: Career preparation
        if career_matches:
            top = career_matches[0]
            year_actions.append(f"Target entry-level {top['career_name']} positions.")

        goal = student.get("current_goal", "")
        if goal == "graduate_school":
            year_actions.append("Prepare graduate school applications and secure recommendation letters.")
        elif goal in ("internship", "full_time"):
            year_actions.append("Leverage internship/project experience in full-time job applications.")

        if not year_actions:
            year_actions.append("Reassess your Rowdy Plan with updated experience and achievements.")

        return [
            {"period": "Now", "title": "Immediate Actions", "actions": now_actions[:3]},
            {"period": "Next 30 Days", "title": "Build Momentum", "actions": thirty_day_actions[:3]},
            {"period": "Next Semester", "title": "Skill Development", "actions": semester_actions[:3]},
            {"period": "Next Year", "title": "Career Launch", "actions": year_actions[:3]},
        ]

    def _safe_student_summary(self, student: dict) -> dict:
        """Return a safe student summary (no embeddings, no raw resume)."""
        return {
            "major": student.get("major", ""),
            "concentration": student.get("concentration", ""),
            "minor": student.get("minor", ""),
            "year": student.get("year", ""),
            "university": student.get("university", "UTSA"),
            "current_goal": student.get("current_goal", ""),
            "skills_count": len(student.get("skills", []) + student.get("technical_skills", [])),
            "experience_count": len(student.get("experience", [])),
            "has_resume": bool(student.get("resume_text")),
        }
