"""
Feature Extractor for Rowdy Plan Recommendation Engine.

Converts student profiles into numerical feature vectors
using taxonomies and encoding schemes.
"""

import numpy as np
from datetime import datetime


# ~100 common CS/engineering/business skills
SKILL_TAXONOMY = [
    # Programming Languages
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "r", "matlab", "scala", "perl", "bash",
    "html", "css",
    # Frameworks & Libraries
    "react", "angular", "vue", "node.js", "express", "django", "flask", "fastapi",
    "spring", "spring boot", ".net", "rails", "next.js", "svelte", "tailwind",
    "bootstrap", "jquery",
    # Data & ML
    "machine learning", "deep learning", "natural language processing",
    "computer vision", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "data analysis", "data visualization", "statistics", "big data", "spark",
    "hadoop", "tableau", "power bi",
    # Databases
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "dynamodb", "firebase", "neo4j", "cassandra",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "ci/cd", "jenkins", "github actions", "linux", "nginx",
    # Tools & Practices
    "git", "agile", "scrum", "jira", "rest api", "graphql", "microservices",
    "system design", "testing", "unit testing", "tdd",
    # Security
    "cybersecurity", "network security", "penetration testing", "encryption",
    "oauth", "authentication",
    # Mobile
    "android", "ios", "react native", "flutter",
    # Soft Skills & Business
    "communication", "leadership", "teamwork", "project management",
    "problem solving", "critical thinking", "presentation", "technical writing",
    "product management", "business analysis", "ux design", "ui design",
    "user research", "a/b testing",
    # Networking
    "networking", "tcp/ip", "dns", "load balancing",
    # Other Technical
    "blockchain", "iot", "embedded systems", "robotics", "game development",
    "ar/vr", "quantum computing",
]

# ~30 career paths
CAREER_TAXONOMY = [
    "software engineer", "data engineer", "data scientist", "ml engineer",
    "bi analyst", "product manager", "cybersecurity analyst", "devops engineer",
    "cloud engineer", "full stack developer", "mobile developer", "ux researcher",
    "systems engineer", "database administrator", "research scientist",
    "frontend developer", "backend developer", "site reliability engineer",
    "qa engineer", "technical program manager", "solutions architect",
    "data analyst", "ai researcher", "network engineer", "security engineer",
    "embedded systems engineer", "game developer", "technical writer",
    "it consultant", "blockchain developer",
]

# Major US cities and remote/hybrid options
LOCATION_TAXONOMY = [
    "san francisco", "new york", "seattle", "austin", "san antonio",
    "los angeles", "chicago", "boston", "denver", "atlanta",
    "dallas", "houston", "washington dc", "miami", "portland",
    "san jose", "san diego", "phoenix", "philadelphia", "minneapolis",
    "raleigh", "nashville", "charlotte", "detroit", "pittsburgh",
    "salt lake city", "columbus", "indianapolis", "kansas city", "tampa",
    "remote", "hybrid",
]


class FeatureExtractor:
    """Extracts numerical feature vectors from student profile data."""

    def __init__(self):
        # Build lookup indices for O(1) access
        self._skill_index = {
            skill.lower(): i for i, skill in enumerate(SKILL_TAXONOMY)
        }
        self._career_index = {
            career.lower(): i for i, career in enumerate(CAREER_TAXONOMY)
        }
        self._location_index = {
            loc.lower(): i for i, loc in enumerate(LOCATION_TAXONOMY)
        }

    def extract_skill_vector(self, skills: list[str]) -> np.ndarray:
        """
        Create a binary (one-hot style) vector over the skill taxonomy.

        Args:
            skills: List of skill strings from the student profile.

        Returns:
            numpy array of shape (len(SKILL_TAXONOMY),) with 1s for present skills.
        """
        vector = np.zeros(len(SKILL_TAXONOMY), dtype=np.float64)
        for skill in skills:
            skill_lower = skill.lower().strip()
            if skill_lower in self._skill_index:
                vector[self._skill_index[skill_lower]] = 1.0
            else:
                # Fuzzy match: check if skill is a substring of any taxonomy entry
                for tax_skill, idx in self._skill_index.items():
                    if skill_lower in tax_skill or tax_skill in skill_lower:
                        vector[idx] = 0.7  # Partial match weight
                        break
        return vector

    def extract_experience_vector(self, experience: list[dict]) -> np.ndarray:
        """
        Encode experience into a feature vector capturing count, diversity,
        recency, and duration.

        Args:
            experience: List of experience dicts with title, company,
                       duration_months, type, etc.

        Returns:
            numpy array of shape (8,) encoding experience features.
        """
        if not experience:
            return np.zeros(8, dtype=np.float64)

        # Feature 0: Total experience count (normalized, cap at 10)
        count = min(len(experience), 10) / 10.0

        # Feature 1: Total months of experience (normalized, cap at 60)
        total_months = sum(
            exp.get("duration_months", 0) for exp in experience
        )
        months_norm = min(total_months, 60) / 60.0

        # Feature 2: Type diversity (unique types / total possible types)
        exp_types = {"internship", "full-time", "part-time", "co-op",
                     "research", "project", "volunteer", "freelance"}
        student_types = set(
            exp.get("type", "other").lower() for exp in experience
        )
        type_diversity = len(student_types & exp_types) / len(exp_types)

        # Feature 3: Has internship
        has_internship = 1.0 if any(
            exp.get("type", "").lower() == "internship" for exp in experience
        ) else 0.0

        # Feature 4: Has full-time
        has_fulltime = 1.0 if any(
            exp.get("type", "").lower() == "full-time" for exp in experience
        ) else 0.0

        # Feature 5: Has research
        has_research = 1.0 if any(
            exp.get("type", "").lower() == "research" for exp in experience
        ) else 0.0

        # Feature 6: Average duration (normalized)
        avg_duration = (total_months / len(experience)) if experience else 0
        avg_duration_norm = min(avg_duration, 24) / 24.0

        # Feature 7: Skill diversity across experiences
        all_skills = set()
        for exp in experience:
            for skill in exp.get("skills_used", []):
                all_skills.add(skill.lower())
        skill_diversity = min(len(all_skills), 20) / 20.0

        return np.array([
            count,
            months_norm,
            type_diversity,
            has_internship,
            has_fulltime,
            has_research,
            avg_duration_norm,
            skill_diversity,
        ], dtype=np.float64)

    def extract_education_vector(
        self,
        major: str,
        gpa: float,
        coursework: list,
        certifications: list,
    ) -> np.ndarray:
        """
        Encode education data into a feature vector.

        Args:
            major: Student's major.
            gpa: GPA (0.0-4.0 scale).
            coursework: List of relevant courses.
            certifications: List of certifications.

        Returns:
            numpy array of shape (8,) encoding education features.
        """
        # Feature 0: GPA normalized (0-1)
        gpa_norm = max(0.0, min(gpa, 4.0)) / 4.0 if gpa else 0.0

        # Feature 1: Is CS/Engineering major
        cs_majors = {
            "computer science", "cs", "software engineering",
            "computer engineering", "information technology", "it",
            "information systems", "electrical engineering",
            "data science", "cybersecurity", "artificial intelligence",
        }
        is_cs = 1.0 if major.lower() in cs_majors else 0.0

        # Feature 2: Is STEM major (broader)
        stem_keywords = {
            "engineering", "science", "mathematics", "math", "physics",
            "chemistry", "biology", "statistics", "technology",
        }
        is_stem = is_cs or (
            1.0 if any(kw in major.lower() for kw in stem_keywords) else 0.0
        )

        # Feature 3: Is business major
        business_keywords = {
            "business", "management", "finance", "accounting",
            "marketing", "economics", "mba",
        }
        is_business = 1.0 if any(
            kw in major.lower() for kw in business_keywords
        ) else 0.0

        # Feature 4: Coursework breadth (normalized)
        coursework_count = min(len(coursework), 20) / 20.0

        # Feature 5: Certification count (normalized)
        cert_count = min(len(certifications), 5) / 5.0

        # Feature 6: Has technical coursework
        tech_course_keywords = {
            "algorithm", "data structure", "database", "operating system",
            "network", "security", "machine learning", "ai", "software",
            "programming", "web", "mobile", "cloud", "system",
        }
        tech_courses = sum(
            1 for c in coursework
            if any(kw in c.lower() for kw in tech_course_keywords)
        )
        tech_coursework_ratio = (
            min(tech_courses, 10) / 10.0 if coursework else 0.0
        )

        # Feature 7: Has industry certifications
        industry_cert_keywords = {
            "aws", "azure", "gcp", "cisco", "comptia", "google",
            "microsoft", "oracle", "pmp", "scrum", "agile",
        }
        has_industry_cert = 1.0 if any(
            any(kw in c.lower() for kw in industry_cert_keywords)
            for c in certifications
        ) else 0.0

        return np.array([
            gpa_norm,
            float(is_cs),
            float(is_stem),
            is_business,
            coursework_count,
            cert_count,
            tech_coursework_ratio,
            has_industry_cert,
        ], dtype=np.float64)

    def extract_career_interest_vector(
        self,
        interests: list[str],
        industries: list[str],
    ) -> np.ndarray:
        """
        Encode career interests and target industries.

        Args:
            interests: List of career interest strings.
            industries: List of target industry strings.

        Returns:
            numpy array of shape (len(CAREER_TAXONOMY) + 10,).
        """
        # Career path one-hot
        career_vec = np.zeros(len(CAREER_TAXONOMY), dtype=np.float64)
        for interest in interests:
            interest_lower = interest.lower().strip()
            if interest_lower in self._career_index:
                career_vec[self._career_index[interest_lower]] = 1.0
            else:
                # Fuzzy match
                for career, idx in self._career_index.items():
                    if interest_lower in career or career in interest_lower:
                        career_vec[idx] = 0.7
                        break

        # Industry encoding (simple one-hot for common industries)
        industry_list = [
            "technology", "finance", "healthcare", "education",
            "government", "consulting", "startup", "retail",
            "manufacturing", "media",
        ]
        industry_vec = np.zeros(len(industry_list), dtype=np.float64)
        for ind in industries:
            ind_lower = ind.lower().strip()
            for i, known_ind in enumerate(industry_list):
                if ind_lower == known_ind or ind_lower in known_ind or known_ind in ind_lower:
                    industry_vec[i] = 1.0
                    break

        return np.concatenate([career_vec, industry_vec])

    def extract_location_vector(
        self,
        locations: list[str],
        preferences: list[str],
    ) -> np.ndarray:
        """
        Encode location preferences.

        Args:
            locations: List of preferred location strings.
            preferences: List of work-type preferences (remote/hybrid/on-site).

        Returns:
            numpy array of shape (len(LOCATION_TAXONOMY),).
        """
        vector = np.zeros(len(LOCATION_TAXONOMY), dtype=np.float64)

        for loc in locations:
            loc_lower = loc.lower().strip()
            if loc_lower in self._location_index:
                vector[self._location_index[loc_lower]] = 1.0
            else:
                # Fuzzy match
                for known_loc, idx in self._location_index.items():
                    if loc_lower in known_loc or known_loc in loc_lower:
                        vector[idx] = 0.7
                        break

        # Encode work-type preferences
        for pref in preferences:
            pref_lower = pref.lower().strip()
            if pref_lower in ("remote", "hybrid"):
                if pref_lower in self._location_index:
                    vector[self._location_index[pref_lower]] = 1.0

        return vector

    def extract_all_features(self, profile: dict) -> dict:
        """
        Extract all feature vectors from a student profile.

        Args:
            profile: Normalized student profile dict.

        Returns:
            Dict of feature name -> numpy array.
        """
        # Combine all skill sources
        all_skills = list(profile.get("skills", []))
        all_skills.extend(profile.get("technical_skills", []))
        all_skills.extend(profile.get("soft_skills", []))
        all_skills.extend(profile.get("programming_languages", []))
        all_skills.extend(profile.get("frameworks", []))
        all_skills.extend(profile.get("tools", []))

        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for s in all_skills:
            s_lower = s.lower()
            if s_lower not in seen:
                seen.add(s_lower)
                unique_skills.append(s)

        return {
            "skill_vector": self.extract_skill_vector(unique_skills),
            "experience_vector": self.extract_experience_vector(
                profile.get("experience", [])
            ),
            "education_vector": self.extract_education_vector(
                major=profile.get("major", ""),
                gpa=profile.get("gpa", 0.0),
                coursework=profile.get("coursework", []),
                certifications=profile.get("certifications", []),
            ),
            "career_interest_vector": self.extract_career_interest_vector(
                interests=profile.get("career_interests", []),
                industries=profile.get("industries", []),
            ),
            "location_vector": self.extract_location_vector(
                locations=(
                    profile.get("location_preferences", [])
                    or profile.get("preferred_locations", [])
                ),
                preferences=(
                    profile.get("work_preferences", [])
                    or [profile.get("work_type_preference", "")]
                ),
            ),
        }
