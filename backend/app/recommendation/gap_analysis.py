"""
Gap Analysis for Rowdy Plan Recommendation Engine.

Identifies skill gaps between a student's current profile
and the requirements of their target career.
"""


# Priority levels with defined sort order
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# Learning resources by skill category
SKILL_RESOURCES = {
    "python": [
        "Python for Everybody (Coursera)",
        "Automate the Boring Stuff with Python",
        "LeetCode Python track",
    ],
    "java": [
        "Java Programming MOOC (University of Helsinki)",
        "Effective Java by Joshua Bloch",
        "HackerRank Java track",
    ],
    "javascript": [
        "JavaScript.info",
        "freeCodeCamp JavaScript Certification",
        "Eloquent JavaScript",
    ],
    "typescript": [
        "TypeScript Handbook (official docs)",
        "Execute Program TypeScript course",
    ],
    "react": [
        "React official tutorial",
        "Full Stack Open (University of Helsinki)",
        "Build a project with React + TypeScript",
    ],
    "sql": [
        "SQLBolt interactive tutorials",
        "Mode Analytics SQL Tutorial",
        "LeetCode Database problems",
    ],
    "machine learning": [
        "Andrew Ng Machine Learning (Coursera)",
        "fast.ai Practical Deep Learning",
        "Kaggle competitions",
    ],
    "deep learning": [
        "fast.ai Practical Deep Learning",
        "Deep Learning Specialization (Coursera)",
        "Papers With Code",
    ],
    "data structures": [
        "LeetCode Top Interview Questions",
        "NeetCode 150",
        "Introduction to Algorithms (CLRS)",
    ],
    "algorithms": [
        "LeetCode Top Interview Questions",
        "NeetCode 150",
        "Grokking Algorithms",
    ],
    "aws": [
        "AWS Cloud Practitioner certification",
        "AWS Free Tier hands-on labs",
        "A Cloud Guru AWS courses",
    ],
    "docker": [
        "Docker official getting started",
        "Play with Docker labs",
        "Docker for Beginners (freeCodeCamp)",
    ],
    "kubernetes": [
        "Kubernetes the Hard Way",
        "KillerCoda interactive scenarios",
        "CKAD certification prep",
    ],
    "git": [
        "Git Branching interactive tutorial",
        "Oh My Git! game",
        "Contribute to open source projects",
    ],
    "linux": [
        "Linux Journey",
        "OverTheWire Bandit wargame",
        "RHCSA certification prep",
    ],
    "networking": [
        "Computer Networking: A Top-Down Approach",
        "CompTIA Network+ prep",
        "Cisco Networking Academy",
    ],
    "cybersecurity": [
        "CompTIA Security+ certification",
        "TryHackMe learning paths",
        "Hack The Box",
    ],
    "system design": [
        "System Design Interview by Alex Xu",
        "Designing Data-Intensive Applications",
        "GitHub system design primer",
    ],
    "communication": [
        "Toastmasters practice",
        "Technical writing courses (Google)",
        "Present at campus meetups or hackathons",
    ],
    "leadership": [
        "Student organization leadership roles",
        "Lead a team project",
        "Mentorship programs",
    ],
    "project management": [
        "Google Project Management Certificate (Coursera)",
        "Agile/Scrum fundamentals",
        "Lead a capstone or hackathon project",
    ],
    "data analysis": [
        "Google Data Analytics Certificate",
        "Kaggle Learn micro-courses",
        "Analyze a public dataset and publish findings",
    ],
    "statistics": [
        "Khan Academy Statistics and Probability",
        "StatQuest YouTube channel",
        "Practical Statistics for Data Scientists",
    ],
    "tensorflow": [
        "TensorFlow Developer Certificate",
        "TensorFlow official tutorials",
        "DeepLearning.AI TensorFlow Developer course",
    ],
    "pytorch": [
        "PyTorch official tutorials",
        "fast.ai (uses PyTorch)",
        "Build a project with PyTorch",
    ],
    "ci/cd": [
        "GitHub Actions quickstart",
        "Jenkins fundamentals",
        "Set up CI/CD for a personal project",
    ],
    "agile": [
        "Scrum.org open assessments",
        "Agile Manifesto and principles",
        "Participate in a sprint-based team project",
    ],
    "rest api": [
        "Build a REST API with Flask or FastAPI",
        "Postman API fundamentals",
        "RESTful API design best practices",
    ],
}

# Default resources for skills not in the map
DEFAULT_RESOURCES = [
    "Search for free courses on Coursera or edX",
    "Look for tutorials on YouTube or freeCodeCamp",
    "Build a personal project using this skill",
]


class GapAnalyzer:
    """Identifies and prioritizes skill gaps for career development."""

    def analyze_gaps(self, student: dict, target_career: dict) -> list[dict]:
        """
        Analyze skill gaps between student profile and target career requirements.

        Args:
            student: Student profile dict.
            target_career: Target career dict with required_skills, preferred_skills, etc.

        Returns:
            List of gap dicts, each describing a skill gap.
        """
        student_skills = set(s.lower() for s in student.get("skills", []))
        student_langs = set(
            s.lower() for s in student.get("programming_languages", [])
        )
        student_tools = set(s.lower() for s in student.get("tools", []))
        student_frameworks = set(s.lower() for s in student.get("frameworks", []))
        # Also accept "technical_skills" key used by some profile formats
        student_tech = set(
            s.lower() for s in student.get("technical_skills", [])
        )
        all_student_skills = (
            student_skills | student_langs | student_tools
            | student_frameworks | student_tech
        )

        # Also consider skills from experience
        for exp in student.get("experience", []):
            for skill in exp.get("skills_used", []):
                all_student_skills.add(skill.lower())

        # Also consider coursework as partial skill coverage
        coursework_skills = set(c.lower() for c in student.get("coursework", []))

        gaps = []

        # Required skills (also accept "typical_skills" as fallback)
        required_skills = target_career.get(
            "required_skills",
            target_career.get("typical_skills", []),
        )
        for skill in required_skills:
            skill_lower = skill.lower()
            if skill_lower not in all_student_skills:
                # Check if coursework partially covers it
                has_coursework = any(
                    skill_lower in cw or cw in skill_lower
                    for cw in coursework_skills
                )
                current_level = "beginner" if has_coursework else "none"
                gaps.append({
                    "skill": skill,
                    "current_level": current_level,
                    "required_level": "proficient",
                    "priority": "critical" if current_level == "none" else "high",
                    "resources": self._get_resources(skill_lower),
                })

        # Preferred skills
        preferred_skills = target_career.get("preferred_skills", [])
        for skill in preferred_skills:
            skill_lower = skill.lower()
            if skill_lower not in all_student_skills:
                has_coursework = any(
                    skill_lower in cw or cw in skill_lower
                    for cw in coursework_skills
                )
                current_level = "beginner" if has_coursework else "none"
                gaps.append({
                    "skill": skill,
                    "current_level": current_level,
                    "required_level": "familiar",
                    "priority": "medium",
                    "resources": self._get_resources(skill_lower),
                })

        # Nice-to-have skills
        nice_to_have = target_career.get("nice_to_have_skills", [])
        for skill in nice_to_have:
            skill_lower = skill.lower()
            if skill_lower not in all_student_skills:
                gaps.append({
                    "skill": skill,
                    "current_level": "none",
                    "required_level": "aware",
                    "priority": "low",
                    "resources": self._get_resources(skill_lower),
                })

        return gaps

    def prioritize_gaps(self, gaps: list[dict]) -> list[dict]:
        """
        Sort gaps by importance for career goal.

        Priority order: critical > high > medium > low.
        Within same priority, sort alphabetically for determinism.

        Args:
            gaps: List of gap dicts.

        Returns:
            Sorted list of gap dicts.
        """
        return sorted(
            gaps,
            key=lambda g: (
                PRIORITY_ORDER.get(g.get("priority", "low"), 3),
                g.get("skill", ""),
            ),
        )

    def _get_resources(self, skill: str) -> list[str]:
        """Get learning resources for a skill."""
        skill_lower = skill.lower().strip()

        # Direct match
        if skill_lower in SKILL_RESOURCES:
            return SKILL_RESOURCES[skill_lower]

        # Partial match
        for key, resources in SKILL_RESOURCES.items():
            if key in skill_lower or skill_lower in key:
                return resources

        return list(DEFAULT_RESOURCES)
