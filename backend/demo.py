"""
Rowdy Plan — Full Predictive Model Demo
Walks through every step of the recommendation pipeline.
"""
import sys
import asyncio

sys.path.insert(0, '/Users/maneeshkumarlillyprabhu/Desktop/Rowdyhacks/backend')

from app.recommendation.profile_builder import ProfileBuilder
from app.recommendation.feature_extractor import FeatureExtractor
from app.recommendation.job_matcher import JobMatcher
from app.recommendation.career_matcher import CareerMatcher, CAREER_DATABASE
from app.recommendation.experience_matcher import ExperienceMatcher
from app.recommendation.resume_analyzer import ResumeAnalyzer
from app.recommendation.gap_analysis import GapAnalyzer
from app.recommendation.ranking import RankingEngine
from app.recommendation.plan_generator import PlanGenerator
from app.ingestion.utsa_provider import UTSAProvider


# ═══════════════════════════════════════════════════════════
# SAMPLE STUDENT
# ═══════════════════════════════════════════════════════════
student = {
    "major": "Computer Science",
    "concentration": "Software Engineering",
    "minor": None,
    "gpa": 3.6,
    "graduation_date": "May 2026",
    "year": "Senior",
    "university": "UTSA",
    "skills": ["python", "java", "javascript", "sql", "git"],
    "technical_skills": ["react", "node.js", "docker", "rest api", "postgresql"],
    "soft_skills": ["teamwork", "communication", "problem solving"],
    "coursework": ["Data Structures", "Algorithms", "Software Engineering", "Database Systems", "Operating Systems"],
    "certifications": ["AWS Cloud Practitioner"],
    "experience": [
        {"type": "internship", "title": "SWE Intern", "organization": "USAA",
         "description": "Built microservices using Java and Spring Boot. Developed React frontend. Worked in Agile sprints."},
        {"type": "job", "title": "Student Developer", "organization": "UTSA IT",
         "description": "Maintained university web apps. Fixed 50+ bugs and added 10 features."}
    ],
    "projects": [
        {"title": "Task Manager App", "description": "Full-stack React + Node.js + PostgreSQL"},
        {"title": "Weather API", "description": "Python FastAPI service with Docker deployment"}
    ],
    "organizations": ["ACM UTSA", "GDSC UTSA"],
    "hackathons": ["RowdyHacks 2024", "HackTX 2024"],
    "career_interests": ["Software Engineer", "Full Stack Developer"],
    "industries": ["Technology", "Finance"],
    "preferred_locations": ["San Antonio, TX", "Austin, TX", "Remote"],
    "work_preferences": ["hybrid", "remote"],
    "preferred_companies": ["USAA", "Google", "Microsoft"],
    "current_goal": "full_time",
    "short_term_goal": "Land a full-time SWE role after graduation",
    "long_term_goal": "Become a senior engineer and tech lead",
    "resume_text": """EDUCATION
University of Texas at San Antonio — B.S. Computer Science, Software Engineering
GPA: 3.6 | Expected May 2026

EXPERIENCE
Software Engineering Intern, USAA | May 2025 – Aug 2025
- Developed microservices using Java and Spring Boot serving 10,000+ daily requests
- Built React frontend for internal employee tools, improving workflow efficiency by 25%
- Participated in Agile sprints and code reviews with a team of 8 engineers

Student Developer, UTSA IT | Jan 2024 – Dec 2024
- Maintained and improved university web applications used by 30,000+ students
- Fixed 50+ bugs and implemented 10 new features in PHP and JavaScript

SKILLS
Python, Java, JavaScript, React, Node.js, SQL, PostgreSQL, Docker, Git, REST API, AWS

PROJECTS
Task Management App — Full-stack React + Node.js application with PostgreSQL
Weather API Service — Python FastAPI service aggregating weather data

ORGANIZATIONS
ACM UTSA | Google Developer Student Club UTSA"""
}


def main():
    print()
    print("=" * 65)
    print("       ROWDY PLAN — PREDICTIVE MODEL WALKTHROUGH")
    print("=" * 65)
    print()

    # ── STEP 1: PROFILE ANALYSIS ──────────────────────────────
    print("-" * 65)
    print("  STEP 1: PROFILE STRENGTH ANALYSIS")
    print("-" * 65)
    builder = ProfileBuilder()
    strength = builder.calculate_profile_strength(student)
    print(f"  Profile Strength Score: {strength}/100")
    print()
    total_skills = len(student["skills"]) + len(student["technical_skills"])
    checks = [
        ("Has major?", True, "Computer Science"),
        ("Has GPA?", True, "3.6"),
        ("Has skills?", True, f"{total_skills} skills"),
        ("Has experience?", True, f"{len(student['experience'])} entries"),
        ("Has resume?", True, f"{len(student['resume_text'])} chars"),
        ("Has coursework?", True, f"{len(student['coursework'])} courses"),
        ("Has certifications?", True, f"{len(student['certifications'])} certs"),
        ("Has career goals?", True, student["current_goal"]),
        ("Has projects?", True, f"{len(student['projects'])} projects"),
    ]
    for label, ok, detail in checks:
        icon = "+" if ok else " "
        print(f"    [{icon}] {label:22s} {detail}")
    print()

    # ── STEP 2: FEATURE EXTRACTION ────────────────────────────
    print("-" * 65)
    print("  STEP 2: FEATURE VECTOR EXTRACTION")
    print("-" * 65)
    extractor = FeatureExtractor()
    features = extractor.extract_all_features(student)
    print(f"  Skill vector:      {features['skill_vector'].shape} dimensions")
    print(f"  Experience vector:  {features['experience_vector'].shape} dimensions")
    print(f"  Education vector:   {features['education_vector'].shape} dimensions")
    nonzero = sum(1 for x in features["skill_vector"] if x > 0)
    print(f"  Skills matched in taxonomy: {nonzero} / {len(features['skill_vector'])}")
    print()

    # ── STEP 3: CAREER MATCHING ───────────────────────────────
    print("-" * 65)
    print("  STEP 3: CAREER PATH PREDICTION")
    print("  Weights: 50% skills + 15% coursework + 20% experience + 15% interest")
    print("-" * 65)
    career_matcher = CareerMatcher()
    career_matches = career_matcher.match_careers(student, limit=5)
    print()
    for i, c in enumerate(career_matches, 1):
        score = c["career_match_score"]
        bar_len = score // 2
        bar = "#" * bar_len + "." * (50 - bar_len)
        matching = ", ".join(c["matching_skills"][:5])
        missing = ", ".join(c["missing_skills"][:4])
        print(f"  #{i}  {c['career_name']}")
        print(f"      Score: {score}%  [{bar}]")
        print(f"      Matching:  {matching}")
        print(f"      Missing:   {missing}")
        print(f"      Action:    {c['next_action']}")
        print()

    # ── STEP 4: JOB MATCHING ─────────────────────────────────
    print("-" * 65)
    print("  STEP 4: JOB/OPPORTUNITY MATCHING")
    print("  Weights: 35% skill + 20% experience + 15% education")
    print("           + 10% career interest + 10% location + 10% goal")
    print("-" * 65)
    opps = asyncio.run(UTSAProvider(use_live_data=False).fetch_all())
    job_matcher = JobMatcher()
    ranking = RankingEngine()
    job_results = job_matcher.rank_opportunities(student, opps)

    for r in job_results:
        opp = next((o for o in opps if str(o.get("id", "")) == r["opportunity_id"]), {})
        r["qualification_status"] = ranking.apply_qualification_filter(student, opp)

    print()
    status_icons = {
        "QUALIFIED": "[QUALIFIED]    ",
        "LIKELY_QUALIFIED": "[LIKELY]       ",
        "SKILL_GAP": "[SKILL GAP]    ",
        "NOT_ELIGIBLE": "[NOT ELIGIBLE] ",
        "UNKNOWN": "[UNKNOWN]      ",
    }
    for j in job_results[:8]:
        qs = status_icons.get(j["qualification_status"], "[?]            ")
        bd = j["score_breakdown"]
        matched = ", ".join(j["matched_skills"][:5])
        missing = ", ".join(j["missing_skills"][:4])
        print(f"  {j['match_score']:3d}%  {qs}{j['title']}")
        print(f"        at {j['organization']}")
        print(f"        Scores: skill={bd['skill']:.0f}  exp={bd['experience']:.0f}  edu={bd['education']:.0f}  career={bd['career_interest']:.0f}  loc={bd['location']:.0f}  goal={bd['goal']:.0f}")
        if matched:
            print(f"        Matched: {matched}")
        if missing:
            print(f"        Missing: {missing}")
        print(f"        Why:     {j['reasoning'][0]}")
        print()

    # ── STEP 5: EXPERIENCE GAP ANALYSIS ──────────────────────
    print("-" * 65)
    print("  STEP 5: READINESS ASSESSMENT & EXPERIENCE GAPS")
    print("-" * 65)
    exp_matcher = ExperienceMatcher()
    readiness = exp_matcher.assess_readiness(student, "Software Engineer")
    rp = readiness["readiness"]
    rbar = "#" * (rp // 2) + "." * (50 - rp // 2)
    strong = ", ".join(readiness["strong_areas"][:6])
    weak = ", ".join(readiness["weak_areas"][:6])
    print(f"  Readiness for Software Engineer: {rp}%")
    print(f"  [{rbar}]")
    print()
    print(f"  Strong: {strong}")
    print(f"  Needs:  {weak}")
    print()
    exp_recs = exp_matcher.match_experiences(student, "Software Engineer")
    print("  Recommended experiences:")
    for e in exp_recs[:5]:
        print(f"    [{e['type']:12s}]  {e['title']}")
        print(f"                  -> {e['action']}")
    print()

    # ── STEP 6: RESUME ANALYSIS ──────────────────────────────
    print("-" * 65)
    print("  STEP 6: RESUME INTELLIGENCE")
    print("-" * 65)
    analyzer = ResumeAnalyzer()
    ra = analyzer.analyze(student["resume_text"], "Software Engineer", student)
    print(f"  Resume Score:       {ra['resume_score']}/100")
    print(f"  ATS Compatibility:  {ra['ats_compatibility']}/100")
    print(f"  Strong Bullets:     {len(ra['strong_bullets'])}")
    print(f"  Weak Bullets:       {len(ra['weak_bullets'])}")
    print()
    missing_tech = ", ".join(ra["missing_technical_skills"][:6])
    missing_kw = ", ".join(ra["missing_keywords"][:6])
    if missing_tech:
        print(f"  Missing tech skills: {missing_tech}")
    if missing_kw:
        print(f"  Missing keywords:    {missing_kw}")
    print()
    if ra["strong_bullets"]:
        print("  Strong bullets:")
        for b in ra["strong_bullets"][:2]:
            print(f'    "{b[:75]}"')
    if ra["recommended_rewrites"]:
        print()
        print("  Suggested rewrites:")
        for rw in ra["recommended_rewrites"][:2]:
            print(f'    Before: "{rw["original"][:65]}"')
            print(f'    After:  "{rw["rewrite"][:65]}"')
            print(f"    Why:    {rw['reason']}")
            print()

    # ── STEP 7: SKILL GAP PRIORITIZATION ─────────────────────
    print("-" * 65)
    print("  STEP 7: SKILL GAP PRIORITIZATION")
    print("-" * 65)
    swe_career = next(c for c in CAREER_DATABASE if c["name"] == "Software Engineer")
    gap_analyzer = GapAnalyzer()
    gaps = gap_analyzer.analyze_gaps(student, swe_career)
    gaps = gap_analyzer.prioritize_gaps(gaps)
    print()
    for g in gaps[:8]:
        priority_tag = {"critical": "CRIT", "high": "HIGH", "medium": "MED ", "low": "LOW "}.get(g["priority"], "?   ")
        print(f"  [{priority_tag}]  {g['skill']:20s}  {g['current_level']:12s} -> {g['required_level']:12s}")
        if g["resources"]:
            print(f"          Resource: {g['resources'][0]}")
    print()

    # ── STEP 8: FULL ROWDY PLAN ──────────────────────────────
    print("-" * 65)
    print("  STEP 8: FINAL ROWDY PLAN")
    print("-" * 65)
    generator = PlanGenerator()
    plan = generator.generate(student, opportunities=opps, max_career_matches=3, max_job_matches=5)
    print()
    print(f"  Profile Strength: {plan['profile_strength']}%")
    print(f"  Careers Matched:  {len(plan['career_matches'])}")
    print(f"  Jobs Matched:     {len(plan['job_matches'])}")
    print(f"  Experiences:      {len(plan['experience_matches'])}")
    print(f"  Skill Gaps:       {len(plan['skill_gaps'])}")
    print()

    print("  TIMELINE:")
    for t in plan["timeline"]:
        print(f"    [{t['period']}] {t['title']}")
        for a in t["actions"]:
            print(f"       -> {a}")
    print()

    print("  NEXT STEPS:")
    for i, s in enumerate(plan["next_steps"], 1):
        print(f"    {i}. {s}")
    print()

    print("  FRONTEND ANIMATION SEQUENCE:")
    for step in plan["processing_steps"]:
        icon = "[done]   " if step["status"] == "complete" else "[skip]   "
        print(f"    {icon} {step['step']}")
    print()

    print("=" * 65)
    print("  PREDICTION COMPLETE")
    print()
    print("  All scores are DETERMINISTIC — same input = same output.")
    print("  No LLM generates numerical scores.")
    print("  Scoring uses set intersection, weighted rules, and")
    print("  cosine similarity over feature vectors.")
    print("=" * 65)
    print()


if __name__ == "__main__":
    main()
