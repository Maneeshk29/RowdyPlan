"""
Resume analysis engine.

Analyzes resumes against target careers, generates ATS scores,
identifies weak bullets, and suggests rewrites.
All scoring is deterministic.
"""
from __future__ import annotations

import re
from typing import Any

from app.recommendation.career_matcher import CAREER_DATABASE


# Action verbs that strengthen resume bullets
STRONG_ACTION_VERBS = {
    "developed", "built", "designed", "implemented", "created", "led", "managed",
    "architected", "optimized", "automated", "deployed", "launched", "delivered",
    "engineered", "reduced", "increased", "improved", "spearheaded", "established",
    "streamlined", "orchestrated", "transformed", "migrated", "scaled", "mentored",
}

# Weak patterns in bullet points
WEAK_PATTERNS = [
    (r"^(responsible for|helped with|assisted in|worked on|involved in)", "Starts with a weak phrase — use a strong action verb instead."),
    (r"^(did|made|got|had)\b", "Starts with a generic verb — be more specific about your contribution."),
    (r"^(i |my )", "Uses first person — remove personal pronouns from resume bullets."),
    (r"(etc\.|and more|and so on|various)", "Uses vague language — be specific about what you did."),
]

# Impact indicators
IMPACT_PATTERNS = [
    r"\d+%",  # Percentages
    r"\$[\d,]+",  # Dollar amounts
    r"\d+\+?\s*(users|customers|clients|students|employees|projects|applications)",  # Quantities
    r"(reduced|increased|improved|grew|saved)\s+.*\d",  # Action + metric
]

# ATS-unfriendly patterns
ATS_PROBLEMS = [
    (r"[^\x00-\x7F]", "Contains non-ASCII characters that some ATS systems can't parse."),
    (r"\b(me|I|my|mine)\b", "Contains personal pronouns."),
]


class ResumeAnalyzer:
    """Analyzes resumes against target careers with deterministic scoring."""

    def analyze(self, resume_text: str, target_career: str, student_profile: dict | None = None) -> dict:
        """Full resume analysis against a target career."""
        if not resume_text or not resume_text.strip():
            return {
                "resume_score": 0,
                "ats_compatibility": 0,
                "missing_keywords": [],
                "weak_bullets": [],
                "strong_bullets": [],
                "missing_technical_skills": [],
                "missing_measurable_impact": [],
                "recommended_rewrites": [],
            }

        # Get target career keywords
        target_keywords = self._get_career_keywords(target_career)

        resume_score = self._score_resume(resume_text, target_keywords)
        ats_score = self._check_ats_compatibility(resume_text)
        missing_keywords = self._find_missing_keywords(resume_text, target_keywords)
        bullet_analysis = self._analyze_bullets(resume_text)
        impact_issues = self._check_measurable_impact(bullet_analysis.get("all_bullets", []))
        rewrites = self._suggest_rewrites(bullet_analysis.get("weak_bullets", []), target_career)

        # Missing technical skills (compared to career)
        resume_lower = resume_text.lower()
        career_data = self._find_career(target_career)
        career_skills = career_data.get("typical_skills", []) if career_data else []
        missing_tech = [s for s in career_skills if s.lower() not in resume_lower]

        return {
            "resume_score": resume_score,
            "ats_compatibility": ats_score,
            "missing_keywords": missing_keywords,
            "weak_bullets": bullet_analysis.get("weak_bullets", []),
            "strong_bullets": bullet_analysis.get("strong_bullets", []),
            "missing_technical_skills": missing_tech[:10],
            "missing_measurable_impact": impact_issues,
            "recommended_rewrites": rewrites,
        }

    def _score_resume(self, resume_text: str, target_keywords: list[str]) -> int:
        """Score a resume 0-100 based on keyword coverage, structure, and impact."""
        score = 0
        text_lower = resume_text.lower()

        # Keyword coverage (40 points)
        if target_keywords:
            matches = sum(1 for kw in target_keywords if kw.lower() in text_lower)
            keyword_pct = matches / len(target_keywords)
            score += round(keyword_pct * 40)

        # Section completeness (20 points)
        sections = ["education", "experience", "skills", "projects"]
        for section in sections:
            if section in text_lower:
                score += 5

        # Bullet quality (20 points)
        bullets = self._extract_bullets(resume_text)
        if bullets:
            strong_count = sum(1 for b in bullets if self._is_strong_bullet(b))
            bullet_quality = strong_count / len(bullets) if bullets else 0
            score += round(bullet_quality * 20)

        # Impact metrics (20 points)
        impact_count = sum(1 for pattern in IMPACT_PATTERNS if re.search(pattern, resume_text, re.IGNORECASE))
        score += min(20, impact_count * 5)

        return min(100, max(0, score))

    def _check_ats_compatibility(self, resume_text: str) -> int:
        """Score ATS compatibility 0-100."""
        score = 100

        # Penalize for ATS problems
        for pattern, _ in ATS_PROBLEMS:
            if re.search(pattern, resume_text):
                score -= 10

        # Check for standard section headers
        standard_headers = ["education", "experience", "skills"]
        for header in standard_headers:
            if header not in resume_text.lower():
                score -= 10

        # Check for reasonable length
        word_count = len(resume_text.split())
        if word_count < 100:
            score -= 20
        elif word_count > 1500:
            score -= 10

        # Check for contact information patterns
        if not re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', resume_text):
            score -= 5

        return max(0, score)

    def _find_missing_keywords(self, resume_text: str, target_keywords: list[str]) -> list[str]:
        """Find target keywords not present in resume."""
        text_lower = resume_text.lower()
        return [kw for kw in target_keywords if kw.lower() not in text_lower]

    def _analyze_bullets(self, resume_text: str) -> dict:
        """Analyze bullet points for quality."""
        bullets = self._extract_bullets(resume_text)
        weak = []
        strong = []

        for bullet in bullets:
            bullet_stripped = bullet.strip()
            if not bullet_stripped:
                continue

            is_weak = False
            weakness_reason = ""

            # Check weak patterns
            for pattern, reason in WEAK_PATTERNS:
                if re.search(pattern, bullet_stripped, re.IGNORECASE):
                    is_weak = True
                    weakness_reason = reason
                    break

            # Check for measurable impact
            has_impact = any(re.search(p, bullet_stripped, re.IGNORECASE) for p in IMPACT_PATTERNS)

            if is_weak:
                weak.append({"original": bullet_stripped, "suggestion": weakness_reason})
            elif self._is_strong_bullet(bullet_stripped):
                strong.append(bullet_stripped)
            elif not has_impact and len(bullet_stripped) > 20:
                weak.append({"original": bullet_stripped, "suggestion": "Add measurable impact or quantify your achievement."})

        return {
            "weak_bullets": weak[:10],
            "strong_bullets": strong[:10],
            "all_bullets": bullets,
        }

    def _suggest_rewrites(self, weak_bullets: list[dict], target_career: str) -> list[dict]:
        """Suggest rewrites for weak bullets."""
        rewrites = []

        for bullet_info in weak_bullets[:8]:
            original = bullet_info["original"]
            reason = bullet_info["suggestion"]
            rewrite = self._generate_rewrite(original, target_career)

            rewrites.append({
                "original": original,
                "rewrite": rewrite,
                "reason": reason,
            })

        return rewrites

    def _generate_rewrite(self, original: str, target_career: str) -> str:
        """Generate a suggested rewrite for a weak bullet. Rule-based, not LLM."""
        text = original.strip()

        # Remove weak starts
        for pattern, _ in WEAK_PATTERNS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

        # Capitalize first letter
        if text:
            # Try to start with a strong action verb
            words = text.split()
            if words and words[0].lower() not in STRONG_ACTION_VERBS:
                # Suggest a strong verb based on context
                context = text.lower()
                if any(w in context for w in ["code", "program", "software", "app", "application"]):
                    text = f"Developed {text}"
                elif any(w in context for w in ["team", "group", "member"]):
                    text = f"Led {text}"
                elif any(w in context for w in ["data", "analyz", "report"]):
                    text = f"Analyzed {text}"
                elif any(w in context for w in ["design", "ui", "ux", "interface"]):
                    text = f"Designed {text}"
                else:
                    text = f"Implemented {text}"

            text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()

        # Add impact suggestion if missing
        has_impact = any(re.search(p, text, re.IGNORECASE) for p in IMPACT_PATTERNS)
        if not has_impact:
            text += ", resulting in [quantify impact: e.g., 20% improvement, 500+ users served]"

        return text

    def _check_measurable_impact(self, bullets: list[str]) -> list[str]:
        """Find bullets that lack measurable impact."""
        no_impact = []
        for bullet in bullets:
            bullet = bullet.strip()
            if not bullet or len(bullet) < 15:
                continue
            has_impact = any(re.search(p, bullet, re.IGNORECASE) for p in IMPACT_PATTERNS)
            if not has_impact:
                no_impact.append(bullet)
        return no_impact[:10]

    def _extract_bullets(self, text: str) -> list[str]:
        """Extract bullet points from resume text."""
        bullets = []
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            # Match common bullet patterns
            if re.match(r'^[•‣◦⁃∙•\-\*\>]\s*', line):
                cleaned = re.sub(r'^[•‣◦⁃∙•\-\*\>]\s*', '', line)
                if cleaned:
                    bullets.append(cleaned)
            elif len(line) > 30 and line[0].isupper() and not line.endswith(":"):
                # Heuristic: lines that look like bullet content
                if any(line.lower().startswith(v) for v in STRONG_ACTION_VERBS):
                    bullets.append(line)
        return bullets

    def _is_strong_bullet(self, bullet: str) -> bool:
        """Check if a bullet point is strong."""
        words = bullet.lower().split()
        if not words:
            return False

        starts_with_action = words[0] in STRONG_ACTION_VERBS or words[0].rstrip("ed") in STRONG_ACTION_VERBS
        has_impact = any(re.search(p, bullet, re.IGNORECASE) for p in IMPACT_PATTERNS)

        return starts_with_action and has_impact

    def _get_career_keywords(self, target_career: str) -> list[str]:
        """Get important keywords for a target career."""
        career_data = self._find_career(target_career)
        if career_data:
            keywords = list(career_data.get("typical_skills", []))
            keywords.extend(career_data.get("typical_certifications", [])[:3])
            keywords.extend(career_data.get("typical_coursework", [])[:3])
            return keywords
        return []

    def _find_career(self, career_name: str) -> dict | None:
        """Find career data by name."""
        name_lower = career_name.lower()
        for career in CAREER_DATABASE:
            if career["name"].lower() == name_lower:
                return career
        # Fuzzy match
        for career in CAREER_DATABASE:
            if name_lower in career["name"].lower() or career["name"].lower() in name_lower:
                return career
        return None
