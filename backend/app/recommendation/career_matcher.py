"""
Deterministic career path matching engine.

Predicts the top career paths that fit a student's profile using
skill overlap, experience alignment, and education match.
"""
from __future__ import annotations

from typing import Any


# Comprehensive career database with skills, coursework, and recommendations
CAREER_DATABASE: list[dict] = [
    {
        "name": "Software Engineer",
        "description": "Design, develop, and maintain software systems and applications.",
        "typical_skills": ["python", "java", "javascript", "c++", "git", "sql", "data structures", "algorithms", "rest api", "testing", "agile", "docker"],
        "typical_coursework": ["Data Structures", "Algorithms", "Software Engineering", "Operating Systems", "Database Systems", "Computer Architecture"],
        "typical_certifications": ["AWS Certified Developer", "Azure Developer Associate", "Google Associate Cloud Engineer"],
        "entry_level_titles": ["Junior Software Engineer", "Software Developer", "Associate Software Engineer"],
        "mid_level_titles": ["Software Engineer", "Senior Developer", "Tech Lead"],
        "senior_titles": ["Staff Engineer", "Principal Engineer", "Engineering Manager"],
        "related_industries": ["Technology", "Finance", "Healthcare", "E-commerce", "Defense"],
        "average_salary_range": {"min": 75000, "max": 150000},
        "growth_outlook": "Strong — 25% growth projected through 2031",
        "recommended_projects": ["Build a full-stack web application", "Contribute to open source", "Create a REST API with authentication"],
        "recommended_events": ["Local tech meetups", "Hackathons", "Company tech talks"],
    },
    {
        "name": "Data Engineer",
        "description": "Build and maintain data pipelines, warehouses, and ETL systems.",
        "typical_skills": ["python", "sql", "spark", "airflow", "etl", "data warehousing", "aws", "kafka", "docker", "postgresql", "snowflake", "dbt"],
        "typical_coursework": ["Database Systems", "Distributed Systems", "Data Structures", "Statistics", "Cloud Computing", "Big Data"],
        "typical_certifications": ["AWS Data Analytics", "Google Professional Data Engineer", "Databricks Data Engineer"],
        "entry_level_titles": ["Junior Data Engineer", "Data Analyst", "ETL Developer"],
        "mid_level_titles": ["Data Engineer", "Senior Data Engineer", "Analytics Engineer"],
        "senior_titles": ["Staff Data Engineer", "Principal Data Engineer", "Data Architecture Lead"],
        "related_industries": ["Technology", "Finance", "Healthcare", "E-commerce", "Consulting"],
        "average_salary_range": {"min": 80000, "max": 160000},
        "growth_outlook": "Very strong — high demand across all industries",
        "recommended_projects": ["Build an ETL pipeline", "Create a data warehouse", "Real-time streaming data project"],
        "recommended_events": ["Data engineering meetups", "dbt Community events", "Cloud provider workshops"],
    },
    {
        "name": "Data Scientist",
        "description": "Apply statistical and machine learning methods to extract insights from data.",
        "typical_skills": ["python", "r", "sql", "statistics", "machine learning", "pandas", "numpy", "scikit-learn", "data visualization", "jupyter", "tensorflow"],
        "typical_coursework": ["Statistics", "Machine Learning", "Linear Algebra", "Probability", "Data Mining", "Database Systems"],
        "typical_certifications": ["IBM Data Science Professional", "Google Data Analytics", "AWS Machine Learning Specialty"],
        "entry_level_titles": ["Junior Data Scientist", "Data Analyst", "Research Analyst"],
        "mid_level_titles": ["Data Scientist", "Senior Data Scientist", "ML Scientist"],
        "senior_titles": ["Principal Data Scientist", "Head of Data Science", "Chief Data Officer"],
        "related_industries": ["Technology", "Finance", "Healthcare", "Research", "Marketing"],
        "average_salary_range": {"min": 85000, "max": 165000},
        "growth_outlook": "Strong — 36% growth projected",
        "recommended_projects": ["Kaggle competition", "Predictive modeling project", "NLP text classification"],
        "recommended_events": ["Data science conferences", "Kaggle meetups", "ML paper reading groups"],
    },
    {
        "name": "Machine Learning Engineer",
        "description": "Build and deploy machine learning models and systems at scale.",
        "typical_skills": ["python", "tensorflow", "pytorch", "mlops", "docker", "kubernetes", "sql", "deep learning", "model deployment", "aws", "data pipelines"],
        "typical_coursework": ["Machine Learning", "Deep Learning", "Linear Algebra", "Statistics", "Distributed Systems", "Algorithms"],
        "typical_certifications": ["AWS ML Specialty", "Google ML Engineer", "TensorFlow Developer Certificate"],
        "entry_level_titles": ["ML Engineer", "AI Developer", "Junior ML Engineer"],
        "mid_level_titles": ["Senior ML Engineer", "Applied Scientist", "ML Platform Engineer"],
        "senior_titles": ["Staff ML Engineer", "Principal ML Engineer", "Head of ML"],
        "related_industries": ["Technology", "AI/ML", "Healthcare", "Finance", "Autonomous Vehicles"],
        "average_salary_range": {"min": 100000, "max": 200000},
        "growth_outlook": "Very strong — fastest growing tech role",
        "recommended_projects": ["Train and deploy a deep learning model", "Build an ML pipeline", "Create an AI-powered application"],
        "recommended_events": ["NeurIPS", "ICML", "Local AI meetups"],
    },
    {
        "name": "Business Intelligence Analyst",
        "description": "Transform data into actionable business insights through reporting and dashboards.",
        "typical_skills": ["sql", "tableau", "power bi", "excel", "python", "data visualization", "business analysis", "etl", "data modeling", "reporting"],
        "typical_coursework": ["Business Analytics", "Statistics", "Database Systems", "Data Visualization", "Accounting", "Economics"],
        "typical_certifications": ["Tableau Desktop Specialist", "Microsoft Power BI", "Google Business Intelligence"],
        "entry_level_titles": ["BI Analyst", "Data Analyst", "Reporting Analyst"],
        "mid_level_titles": ["Senior BI Analyst", "BI Developer", "Analytics Manager"],
        "senior_titles": ["Director of BI", "Head of Analytics", "VP of Data"],
        "related_industries": ["Finance", "Consulting", "Retail", "Healthcare", "Technology"],
        "average_salary_range": {"min": 60000, "max": 120000},
        "growth_outlook": "Steady — consistent demand",
        "recommended_projects": ["Build a Tableau dashboard", "Create a Power BI report", "Business case analysis"],
        "recommended_events": ["Tableau conferences", "Business analytics workshops", "Industry meetups"],
    },
    {
        "name": "Product Manager",
        "description": "Define product strategy, prioritize features, and bridge business and engineering.",
        "typical_skills": ["product strategy", "agile", "user research", "data analysis", "sql", "communication", "roadmapping", "a/b testing", "jira", "stakeholder management"],
        "typical_coursework": ["Product Management", "Business Strategy", "UX Design", "Marketing", "Statistics", "Software Engineering"],
        "typical_certifications": ["Certified Scrum Product Owner", "Product Management Certificate", "Google Project Management"],
        "entry_level_titles": ["Associate PM", "Product Analyst", "Junior PM"],
        "mid_level_titles": ["Product Manager", "Senior PM", "Group PM"],
        "senior_titles": ["Director of Product", "VP Product", "Chief Product Officer"],
        "related_industries": ["Technology", "SaaS", "E-commerce", "Finance", "Healthcare"],
        "average_salary_range": {"min": 80000, "max": 170000},
        "growth_outlook": "Strong — growing demand in tech",
        "recommended_projects": ["Product case study", "User research project", "Product roadmap exercise"],
        "recommended_events": ["ProductCon", "Local PM meetups", "Design thinking workshops"],
    },
    {
        "name": "Cybersecurity Analyst",
        "description": "Protect systems and networks from security threats and vulnerabilities.",
        "typical_skills": ["network security", "penetration testing", "siem", "firewall", "incident response", "vulnerability assessment", "linux", "python", "encryption", "compliance"],
        "typical_coursework": ["Network Security", "Cryptography", "Operating Systems", "Computer Networks", "Digital Forensics", "Ethics in Computing"],
        "typical_certifications": ["CompTIA Security+", "CEH", "CISSP", "CompTIA CySA+", "OSCP"],
        "entry_level_titles": ["Security Analyst", "SOC Analyst", "Junior Penetration Tester"],
        "mid_level_titles": ["Senior Security Analyst", "Security Engineer", "Incident Responder"],
        "senior_titles": ["Security Architect", "CISO", "Director of Security"],
        "related_industries": ["Defense", "Finance", "Healthcare", "Government", "Technology"],
        "average_salary_range": {"min": 70000, "max": 150000},
        "growth_outlook": "Very strong — 35% growth projected",
        "recommended_projects": ["CTF competitions", "Home lab security setup", "Vulnerability assessment report"],
        "recommended_events": ["DEF CON", "BSides", "Cybersecurity career fairs"],
    },
    {
        "name": "DevOps Engineer",
        "description": "Automate and streamline software delivery and infrastructure management.",
        "typical_skills": ["docker", "kubernetes", "ci/cd", "aws", "terraform", "linux", "python", "bash", "jenkins", "monitoring", "git"],
        "typical_coursework": ["Operating Systems", "Computer Networks", "Cloud Computing", "Software Engineering", "Systems Administration"],
        "typical_certifications": ["AWS Solutions Architect", "CKA", "HashiCorp Terraform Associate", "Docker Certified Associate"],
        "entry_level_titles": ["Junior DevOps Engineer", "Systems Administrator", "Build Engineer"],
        "mid_level_titles": ["DevOps Engineer", "Site Reliability Engineer", "Platform Engineer"],
        "senior_titles": ["Senior DevOps Engineer", "Staff SRE", "Director of Platform Engineering"],
        "related_industries": ["Technology", "Finance", "E-commerce", "Cloud Providers", "SaaS"],
        "average_salary_range": {"min": 85000, "max": 170000},
        "growth_outlook": "Strong — critical for modern software delivery",
        "recommended_projects": ["Set up a CI/CD pipeline", "Deploy an app on Kubernetes", "Infrastructure as code project"],
        "recommended_events": ["KubeCon", "DevOps Days", "Cloud provider workshops"],
    },
    {
        "name": "Cloud Engineer",
        "description": "Design and manage cloud infrastructure and services.",
        "typical_skills": ["aws", "azure", "gcp", "terraform", "docker", "kubernetes", "networking", "linux", "python", "serverless", "iam"],
        "typical_coursework": ["Cloud Computing", "Computer Networks", "Distributed Systems", "Operating Systems", "Database Systems"],
        "typical_certifications": ["AWS Solutions Architect", "Azure Administrator", "Google Cloud Engineer", "AWS Cloud Practitioner"],
        "entry_level_titles": ["Junior Cloud Engineer", "Cloud Support Engineer", "Cloud Administrator"],
        "mid_level_titles": ["Cloud Engineer", "Senior Cloud Engineer", "Cloud Architect"],
        "senior_titles": ["Principal Cloud Architect", "Director of Cloud Infrastructure", "VP of Engineering"],
        "related_industries": ["Technology", "Cloud Providers", "Finance", "Healthcare", "Government"],
        "average_salary_range": {"min": 90000, "max": 175000},
        "growth_outlook": "Very strong — cloud adoption continues to accelerate",
        "recommended_projects": ["Multi-cloud deployment project", "Serverless application", "Cloud cost optimization"],
        "recommended_events": ["AWS re:Invent", "Google Cloud Next", "Azure conferences"],
    },
    {
        "name": "Full Stack Developer",
        "description": "Build complete web applications spanning frontend and backend.",
        "typical_skills": ["javascript", "react", "node.js", "python", "html", "css", "sql", "rest api", "git", "typescript", "mongodb", "docker"],
        "typical_coursework": ["Web Development", "Software Engineering", "Database Systems", "Data Structures", "UI/UX Design"],
        "typical_certifications": ["Meta Front-End Developer", "AWS Developer Associate", "MongoDB Developer"],
        "entry_level_titles": ["Junior Developer", "Web Developer", "Frontend Developer"],
        "mid_level_titles": ["Full Stack Developer", "Senior Developer", "Lead Developer"],
        "senior_titles": ["Staff Engineer", "Engineering Manager", "CTO"],
        "related_industries": ["Technology", "E-commerce", "Startups", "Media", "Finance"],
        "average_salary_range": {"min": 70000, "max": 145000},
        "growth_outlook": "Strong — web remains dominant platform",
        "recommended_projects": ["Build a SaaS application", "Create a portfolio website", "Open source contribution"],
        "recommended_events": ["React conferences", "Local web dev meetups", "Hackathons"],
    },
    {
        "name": "Mobile Developer",
        "description": "Build native and cross-platform mobile applications.",
        "typical_skills": ["swift", "kotlin", "react native", "flutter", "java", "ios", "android", "rest api", "git", "firebase", "ui design"],
        "typical_coursework": ["Mobile App Development", "Software Engineering", "Data Structures", "UI/UX Design", "Human-Computer Interaction"],
        "typical_certifications": ["Google Associate Android Developer", "Apple Certified iOS Developer", "Meta React Native Certificate"],
        "entry_level_titles": ["Junior Mobile Developer", "iOS Developer", "Android Developer"],
        "mid_level_titles": ["Senior Mobile Developer", "Mobile Lead", "Mobile Architect"],
        "senior_titles": ["Principal Mobile Engineer", "Director of Mobile", "VP Engineering"],
        "related_industries": ["Technology", "E-commerce", "Social Media", "Healthcare", "Finance"],
        "average_salary_range": {"min": 75000, "max": 155000},
        "growth_outlook": "Steady — mobile usage continues growing",
        "recommended_projects": ["Publish an app to App Store/Play Store", "Cross-platform app with Flutter", "Mobile UI/UX project"],
        "recommended_events": ["WWDC", "Google I/O", "Mobile dev meetups"],
    },
    {
        "name": "UX Researcher",
        "description": "Conduct user research to inform product design decisions.",
        "typical_skills": ["user research", "usability testing", "surveys", "interviews", "data analysis", "figma", "prototyping", "a/b testing", "communication", "empathy"],
        "typical_coursework": ["Human-Computer Interaction", "Psychology", "Statistics", "UX Design", "Research Methods", "Communication"],
        "typical_certifications": ["Google UX Design", "Nielsen Norman UX Certification", "UXPA Certification"],
        "entry_level_titles": ["UX Research Assistant", "Junior UX Researcher", "User Research Intern"],
        "mid_level_titles": ["UX Researcher", "Senior UX Researcher", "Design Researcher"],
        "senior_titles": ["Lead UX Researcher", "Director of UX Research", "VP of Design"],
        "related_industries": ["Technology", "Design Agencies", "E-commerce", "Healthcare", "Finance"],
        "average_salary_range": {"min": 70000, "max": 140000},
        "growth_outlook": "Growing — companies investing more in UX",
        "recommended_projects": ["Conduct a usability study", "User persona creation", "Competitive analysis"],
        "recommended_events": ["UX conferences", "Design thinking workshops", "Research meetups"],
    },
    {
        "name": "Systems Engineer",
        "description": "Design and manage complex computing systems and infrastructure.",
        "typical_skills": ["linux", "networking", "python", "bash", "virtualization", "storage", "monitoring", "automation", "windows server", "troubleshooting"],
        "typical_coursework": ["Operating Systems", "Computer Networks", "Systems Administration", "Computer Architecture", "Distributed Systems"],
        "typical_certifications": ["CompTIA Linux+", "RHCE", "CCNA", "Windows Server MCSA"],
        "entry_level_titles": ["Junior Systems Engineer", "Systems Administrator", "IT Support Engineer"],
        "mid_level_titles": ["Systems Engineer", "Senior Systems Engineer", "Infrastructure Engineer"],
        "senior_titles": ["Principal Systems Engineer", "Director of Infrastructure", "VP of IT"],
        "related_industries": ["Technology", "Defense", "Government", "Telecommunications", "Healthcare"],
        "average_salary_range": {"min": 65000, "max": 140000},
        "growth_outlook": "Steady — fundamental role in IT",
        "recommended_projects": ["Home server lab", "Network automation project", "Monitoring dashboard"],
        "recommended_events": ["LISA conference", "Linux meetups", "IT infrastructure events"],
    },
    {
        "name": "Database Administrator",
        "description": "Manage, optimize, and secure database systems.",
        "typical_skills": ["sql", "postgresql", "mysql", "oracle", "mongodb", "database design", "performance tuning", "backup recovery", "replication", "data modeling"],
        "typical_coursework": ["Database Systems", "Data Structures", "SQL Programming", "Data Modeling", "Systems Administration"],
        "typical_certifications": ["Oracle DBA", "Microsoft SQL Server", "MongoDB DBA", "AWS Database Specialty"],
        "entry_level_titles": ["Junior DBA", "Database Analyst", "Data Specialist"],
        "mid_level_titles": ["DBA", "Senior DBA", "Database Engineer"],
        "senior_titles": ["Lead DBA", "Database Architect", "Director of Data Infrastructure"],
        "related_industries": ["Technology", "Finance", "Healthcare", "Government", "E-commerce"],
        "average_salary_range": {"min": 65000, "max": 135000},
        "growth_outlook": "Stable — databases remain foundational",
        "recommended_projects": ["Design a normalized database schema", "Performance tuning project", "Database migration"],
        "recommended_events": ["Database conferences", "PostgreSQL meetups", "Data management workshops"],
    },
    {
        "name": "Research Scientist",
        "description": "Conduct original research in computer science, AI, or related fields.",
        "typical_skills": ["python", "research methodology", "statistics", "machine learning", "academic writing", "latex", "data analysis", "deep learning", "experimentation"],
        "typical_coursework": ["Research Methods", "Advanced Algorithms", "Machine Learning", "Statistics", "Thesis/Capstone", "Graduate Seminars"],
        "typical_certifications": ["No standard certifications — publications and degrees matter most"],
        "entry_level_titles": ["Research Assistant", "Research Intern", "Graduate Researcher"],
        "mid_level_titles": ["Research Scientist", "Applied Scientist", "Postdoctoral Researcher"],
        "senior_titles": ["Senior Research Scientist", "Principal Researcher", "Research Director"],
        "related_industries": ["Academia", "Technology", "AI Labs", "Government Research", "Healthcare"],
        "average_salary_range": {"min": 80000, "max": 200000},
        "growth_outlook": "Growing — AI research demand very high",
        "recommended_projects": ["Publish a research paper", "Undergraduate thesis", "Reproduce a seminal paper"],
        "recommended_events": ["Academic conferences", "Research symposiums", "Paper reading groups"],
    },
]


class CareerMatcher:
    """Matches students with career paths using deterministic skill and profile analysis."""

    def __init__(self, career_database: list[dict] | None = None):
        self.careers = career_database or CAREER_DATABASE

    def match_careers(
        self,
        student: dict,
        career_paths: list[dict] | None = None,
        student_features: dict | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """Return top career matches for a student, ranked by score."""
        paths = career_paths or self.careers
        results = []

        for career in paths:
            scored = self._score_career(student, career, student_features)
            results.append(scored)

        results.sort(key=lambda x: x["career_match_score"], reverse=True)
        return results[:limit]

    def _score_career(self, student: dict, career: dict, student_features: dict | None = None) -> dict:
        student_skills = set(s.lower() for s in (student.get("skills", []) + student.get("technical_skills", [])))
        career_skills = set(s.lower() for s in career.get("typical_skills", []))

        # Skill match (50% weight)
        if career_skills:
            skill_overlap = student_skills & career_skills
            skill_score = (len(skill_overlap) / len(career_skills)) * 100
        else:
            skill_overlap = set()
            skill_score = 0

        # Coursework match (15% weight)
        student_courses = set(c.lower() for c in student.get("coursework", []))
        career_courses = set(c.lower() for c in career.get("typical_coursework", []))
        if career_courses:
            course_overlap = sum(1 for cc in career_courses if any(sc in cc or cc in sc for sc in student_courses))
            course_score = (course_overlap / len(career_courses)) * 100
        else:
            course_score = 0

        # Experience relevance (20% weight)
        experience = student.get("experience", [])
        exp_text = " ".join(
            f"{e.get('type', '')} {e.get('title', '')} {e.get('description', '')}"
            for e in experience
        ).lower()
        career_keywords = career_skills | set(career.get("name", "").lower().split())
        exp_hits = sum(1 for kw in career_keywords if kw in exp_text) if career_keywords else 0
        exp_score = min(100, (exp_hits / max(1, len(career_keywords))) * 100 + len(experience) * 8)

        # Interest alignment (15% weight)
        interests = set(i.lower() for i in student.get("career_interests", []))
        industries = set(i.lower() for i in student.get("industries", []))
        career_industries = set(i.lower() for i in career.get("related_industries", []))
        career_name_lower = career.get("name", "").lower()

        interest_score = 0
        if career_name_lower in interests or any(career_name_lower in i or i in career_name_lower for i in interests):
            interest_score = 100
        elif industries & career_industries:
            interest_score = 70
        elif interests:
            interest_score = 20

        # Weighted total
        total = (
            0.50 * skill_score
            + 0.15 * course_score
            + 0.20 * exp_score
            + 0.15 * interest_score
        )
        total = min(100, max(0, round(total)))

        # Find relevant experience entries
        relevant_exp = []
        for e in experience:
            e_text = f"{e.get('type', '')} {e.get('title', '')} {e.get('description', '')}".lower()
            if any(sk in e_text for sk in list(career_skills)[:5]):
                relevant_exp.append(e.get("title", "Unknown"))

        missing_skills = sorted(career_skills - student_skills)

        return {
            "career_name": career.get("name", ""),
            "career_match_score": total,
            "matching_skills": sorted(skill_overlap),
            "missing_skills": missing_skills[:10],
            "relevant_experience": relevant_exp[:5],
            "recommended_courses": career.get("typical_coursework", [])[:4],
            "recommended_projects": career.get("recommended_projects", [])[:3],
            "recommended_events": career.get("recommended_events", [])[:3],
            "recommended_jobs": career.get("entry_level_titles", [])[:3],
            "next_action": self._suggest_next_action(total, missing_skills, student),
        }

    def _suggest_next_action(self, score: int, missing_skills: list, student: dict) -> str:
        if score >= 80:
            return "You're well-prepared — start applying to entry-level positions now."
        elif score >= 60:
            if missing_skills:
                top = ", ".join(missing_skills[:2])
                return f"Build skills in {top} to strengthen your candidacy."
            return "Gain more hands-on experience through projects or internships."
        elif score >= 40:
            return "Take relevant coursework and build portfolio projects in this area."
        else:
            return "Explore this career through informational interviews and introductory courses."
