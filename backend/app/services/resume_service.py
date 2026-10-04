"""Resume parsing and extraction service."""
from __future__ import annotations

import re
from typing import Any

# Known skills for extraction matching
KNOWN_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "rust", "ruby",
    "swift", "kotlin", "r", "matlab", "scala", "perl", "php", "html", "css", "sass",
    "sql", "nosql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite",
    "react", "angular", "vue", "next.js", "node.js", "express", "django", "flask", "fastapi",
    "spring", "spring boot", ".net", "rails", "laravel",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible", "jenkins",
    "ci/cd", "git", "github", "gitlab", "bitbucket",
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch",
    "scikit-learn", "pandas", "numpy", "matplotlib", "jupyter", "keras",
    "data structures", "algorithms", "rest api", "graphql", "microservices",
    "agile", "scrum", "jira", "confluence", "trello",
    "linux", "unix", "windows server", "bash", "powershell",
    "network security", "penetration testing", "encryption", "firewall", "siem",
    "tableau", "power bi", "excel", "looker", "data visualization",
    "figma", "sketch", "adobe xd", "photoshop", "illustrator",
    "spark", "hadoop", "kafka", "airflow", "dbt", "snowflake", "databricks",
    "etl", "data warehousing", "data modeling", "data pipeline",
    "leadership", "communication", "teamwork", "problem solving", "critical thinking",
    "project management", "time management", "presentation", "public speaking",
    "research", "technical writing", "mentoring", "collaboration",
    "android", "ios", "react native", "flutter", "mobile development",
    "blockchain", "web3", "solidity",
    "devops", "sre", "monitoring", "grafana", "prometheus",
    "unit testing", "integration testing", "test automation", "selenium",
    "oauth", "jwt", "authentication", "authorization",
    "api design", "system design", "distributed systems", "cloud computing",
    "data analysis", "statistics", "probability", "linear algebra",
    "product management", "user research", "a/b testing", "roadmapping",
    "cybersecurity", "incident response", "vulnerability assessment", "compliance",
    "serverless", "lambda", "iam", "s3", "ec2", "rds",
    "networking", "tcp/ip", "dns", "load balancing", "vpn",
]

# Section header patterns
SECTION_PATTERNS = {
    "education": r"(?i)\b(education|academic|university|degree|school)\b",
    "experience": r"(?i)\b(experience|employment|work\s*history|professional|internship)\b",
    "skills": r"(?i)\b(skills|technical\s*skills|proficiencies|technologies|competencies)\b",
    "projects": r"(?i)\b(projects|portfolio|personal\s*projects|academic\s*projects)\b",
    "certifications": r"(?i)\b(certifications?|licenses?|credentials?|certificates?)\b",
    "organizations": r"(?i)\b(organizations?|activities|memberships?|affiliations?|clubs?)\b",
    "leadership": r"(?i)\b(leadership|volunteer|community|extracurricular)\b",
}


class ResumeService:
    """Parses resumes from PDF/DOCX and extracts structured information."""

    def parse_pdf(self, file_bytes: bytes) -> str:
        """Extract text from a PDF file."""
        try:
            import pdfplumber
            import io
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                if text.strip():
                    return text
        except Exception:
            pass

        # Fallback to PyPDF2
        try:
            import PyPDF2
            import io
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text
        except Exception:
            return ""

    def parse_docx(self, file_bytes: bytes) -> str:
        """Extract text from a DOCX file."""
        try:
            import docx
            import io
            doc = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
            return text
        except Exception:
            return ""

    def parse_resume(self, filename: str, file_bytes: bytes) -> str:
        """Route to correct parser based on file extension."""
        lower = filename.lower()
        if lower.endswith(".pdf"):
            return self.parse_pdf(file_bytes)
        elif lower.endswith(".docx"):
            return self.parse_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {filename}. Only PDF and DOCX are supported.")

    def extract_sections(self, resume_text: str) -> dict:
        """Extract resume sections using header pattern matching."""
        sections = {key: "" for key in SECTION_PATTERNS}
        lines = resume_text.split("\n")

        current_section = None
        current_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_section:
                    current_lines.append("")
                continue

            # Check if this line is a section header
            matched_section = None
            for section_name, pattern in SECTION_PATTERNS.items():
                # Section headers are typically short lines
                if len(stripped) < 60 and re.search(pattern, stripped):
                    matched_section = section_name
                    break

            if matched_section:
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_lines).strip()
                current_section = matched_section
                current_lines = []
            elif current_section:
                current_lines.append(stripped)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_lines).strip()

        return sections

    def extract_skills(self, resume_text: str) -> list[str]:
        """Extract skills from resume text by matching against known taxonomy."""
        text_lower = resume_text.lower()
        found = []

        for skill in KNOWN_SKILLS:
            # Use word boundary for short skills, substring for compound skills
            if len(skill) <= 3:
                if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                    found.append(skill)
            else:
                if skill in text_lower:
                    found.append(skill)

        return sorted(set(found))

    def extract_keywords(self, resume_text: str) -> list[str]:
        """Extract important keywords using frequency analysis."""
        # Simple TF-based extraction
        words = re.findall(r'\b[a-zA-Z][a-zA-Z+#.]{2,}\b', resume_text.lower())
        stop_words = {
            "the", "and", "for", "with", "that", "this", "from", "are", "was",
            "were", "been", "have", "has", "had", "will", "would", "could",
            "should", "may", "can", "all", "each", "every", "both", "few",
            "more", "most", "other", "some", "such", "than", "too", "very",
            "just", "but", "not", "also", "into", "over", "about", "between",
            "through", "during", "before", "after", "above", "below", "use",
            "used", "using", "work", "worked", "working",
        }

        freq: dict[str, int] = {}
        for w in words:
            if w not in stop_words and len(w) > 2:
                freq[w] = freq.get(w, 0) + 1

        sorted_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [kw for kw, _ in sorted_keywords[:30]]

    def estimate_experience_level(self, resume_text: str) -> str:
        """Estimate experience level from resume content."""
        text_lower = resume_text.lower()

        # Count years of experience mentions
        year_matches = re.findall(r'(\d+)\+?\s*years?\s*(of\s*)?experience', text_lower)
        if year_matches:
            max_years = max(int(m[0]) for m in year_matches)
            if max_years >= 7:
                return "senior"
            elif max_years >= 3:
                return "mid"
            return "entry"

        # Check for seniority keywords
        senior_keywords = ["senior", "lead", "principal", "staff", "director", "manager", "architect"]
        mid_keywords = ["mid-level", "intermediate", "experienced"]
        entry_keywords = ["junior", "entry", "intern", "student", "graduate", "freshman", "sophomore"]

        for kw in senior_keywords:
            if kw in text_lower:
                return "senior"
        for kw in mid_keywords:
            if kw in text_lower:
                return "mid"
        for kw in entry_keywords:
            if kw in text_lower:
                return "entry"

        # Count job entries as a heuristic
        job_count = len(re.findall(r'(?i)(intern|developer|engineer|analyst|assistant|associate)', text_lower))
        if job_count >= 5:
            return "mid"

        return "entry"

    def full_extraction(self, filename: str, file_bytes: bytes) -> dict:
        """Parse resume and extract all structured data."""
        resume_text = self.parse_resume(filename, file_bytes)
        if not resume_text:
            return {"error": "Could not extract text from resume", "resume_text": ""}

        sections = self.extract_sections(resume_text)
        skills = self.extract_skills(resume_text)
        keywords = self.extract_keywords(resume_text)
        experience_level = self.estimate_experience_level(resume_text)

        return {
            "resume_text": resume_text,
            "sections": sections,
            "skills": skills,
            "keywords": keywords,
            "experience_level": experience_level,
        }
