"""Synthetic demo cohort for the Career Center console.

Every record is fictional and flagged ``is_demo``. The generator is seeded, so
all serverless instances build the same cohort and the console shows
consistent numbers without a database.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from app.api.mock_store import InMemoryStore

DEMO_SEED = 2026
DEMO_COHORT_SIZE = 240

# College -> majors -> (core skills, common gaps, degree-level job titles)
PROGRAMS: dict[str, dict[str, tuple[list[str], list[str], list[str]]]] = {
    "Computing": {
        "Computer Science": (["python", "java", "git", "data structures"], ["cloud", "docker", "system design", "sql"],
                             ["Software Engineer", "Backend Developer", "QA Engineer"]),
        "Cybersecurity": (["networking", "linux", "python"], ["security+", "incident response", "cloud security"],
                          ["Security Analyst", "SOC Analyst", "GRC Analyst"]),
        "Data Science": (["python", "statistics", "sql"], ["tableau", "machine learning", "cloud"],
                         ["Data Analyst", "Data Scientist", "BI Analyst"]),
    },
    "Business": {
        "Finance": (["excel", "financial modeling", "accounting"], ["sql", "python", "cfa level 1"],
                    ["Financial Analyst", "Credit Analyst", "Treasury Analyst"]),
        "Accounting": (["excel", "gaap", "quickbooks"], ["cpa coursework", "audit software", "data analytics"],
                       ["Staff Accountant", "Audit Associate", "Tax Associate"]),
        "Marketing": (["communication", "social media", "canva"], ["google analytics", "sql", "crm"],
                      ["Marketing Coordinator", "Digital Marketing Specialist", "Brand Associate"]),
    },
    "Engineering": {
        "Mechanical Engineering": (["cad", "matlab", "thermodynamics"], ["solidworks certification", "gd&t", "python"],
                                   ["Mechanical Engineer", "Manufacturing Engineer", "Design Engineer"]),
        "Electrical Engineering": (["circuits", "matlab", "c"], ["pcb design", "plc", "embedded systems"],
                                   ["Electrical Engineer", "Controls Engineer", "Test Engineer"]),
        "Civil Engineering": (["autocad", "statics", "surveying"], ["civil 3d", "eit exam", "project management"],
                              ["Civil Engineer", "Project Engineer", "Transportation Engineer"]),
    },
    "Sciences": {
        "Biology": (["lab techniques", "biology", "research"], ["data analysis", "r", "clinical experience"],
                    ["Research Associate", "Lab Technician", "Clinical Research Coordinator"]),
        "Mathematics": (["statistics", "calculus", "python"], ["sql", "actuarial exam p", "r"],
                        ["Actuarial Analyst", "Data Analyst", "Quantitative Analyst"]),
    },
    "Liberal Arts": {
        "Psychology": (["research methods", "communication", "spss"], ["data analysis", "case management", "excel"],
                       ["HR Coordinator", "Research Assistant", "Case Manager"]),
        "Communication": (["writing", "public speaking", "social media"], ["adobe creative suite", "analytics", "seo"],
                          ["Communications Specialist", "Content Strategist", "PR Coordinator"]),
    },
}

EMPLOYERS = [
    "USAA", "H-E-B", "Valero", "CPS Energy", "Frost Bank", "Rackspace Technology", "Southwest Research Institute",
    "Toyota Motor Manufacturing Texas", "Accenture", "Deloitte", "City of San Antonio", "University Health",
    "Texas Department of Transportation", "Lockheed Martin", "Booz Allen Hamilton", "IBM",
]
NON_DEGREE_TITLES = ["Retail Associate", "Server", "Customer Service Representative", "Warehouse Associate", "Barista"]

FIRST_NAMES = [
    "Ana", "Luis", "Maya", "Diego", "Priya", "Jordan", "Sofia", "Mateo", "Aaliyah", "Ethan", "Camila", "Noah",
    "Isabella", "Gabriel", "Zoe", "Adrian", "Valeria", "Kai", "Elena", "Marcus", "Leah", "Andres", "Nia", "Ryan",
]
LAST_NAMES = [
    "Garcia", "Nguyen", "Martinez", "Patel", "Johnson", "Hernandez", "Lopez", "Kim", "Rodriguez", "Williams",
    "Gonzalez", "Brown", "Ramirez", "Davis", "Flores", "Chen", "Torres", "Wilson", "Rivera", "Moore",
]

DEMO_EVENTS = [
    ("Fall Career & Internship Fair", "Career Center", 40),
    ("Resume Review Drop-In", "Career Center", 33),
    ("ACM Hack Night: Cloud Basics", "ACM UTSA", 28),
    ("Mock Interview Day", "Career Center", 24),
    ("Engineering Employer Showcase", "College of Engineering", 21),
    ("Accounting Firms Meet & Greet", "Business Career Services", 18),
    ("LinkedIn Profile Workshop", "Career Center", 15),
    ("Research Opportunities Panel", "Office of Undergraduate Research", 12),
    ("Cybersecurity CTF Practice", "Cyber Club", 10),
    ("Grad School Info Session", "Graduate School", 7),
]

YEAR_WEIGHTS = [("Freshman", 0.18), ("Sophomore", 0.22), ("Junior", 0.26), ("Senior", 0.34)]


def _pick_year(rng: random.Random) -> str:
    roll, total = rng.random(), 0.0
    for year, weight in YEAR_WEIGHTS:
        total += weight
        if roll <= total:
            return year
    return "Senior"


def demo_anchor() -> datetime:
    """Midnight UTC today, so timestamps match across instances on the same day."""
    now = datetime.utcnow()
    return datetime(now.year, now.month, now.day)


def load_demo_cohort(store: InMemoryStore) -> None:
    """Populate the store with the demo cohort once."""
    if any(s.get("is_demo") for s in store.students.values()):
        return

    rng = random.Random(DEMO_SEED)
    anchor = demo_anchor()
    programs = [(college, major, data) for college, majors in PROGRAMS.items() for major, data in majors.items()]

    events = []
    for index, (title, host, _) in enumerate(DEMO_EVENTS):
        event = store.add_campus_event({
            "id": f"demo-event-{index + 1:02d}",
            "title": title,
            "host": host,
            "location": "UTSA Main Campus",
            "starts_at": (anchor - timedelta(days=6 + index * 7, hours=-15)).isoformat(),
            "check_in_code": f"DEMO{index + 1:02d}",
            "created_at": (anchor - timedelta(days=20 + index * 7)).isoformat(),
            "is_demo": True,
        })
        events.append(event)

    for index in range(DEMO_COHORT_SIZE):
        college, major, (skills, gaps, titles) = programs[index % len(programs)]
        year = _pick_year(rng)
        grad_year = {"Freshman": 2030, "Sophomore": 2029, "Junior": 2028, "Senior": 2027}[year]
        if year == "Senior" and rng.random() < 0.55:
            grad_year = 2026  # recent graduates still in the cohort for outcome reporting
        engagement = rng.choices([0, 1, 2, 3], weights=[0.22, 0.30, 0.30, 0.18])[0]
        student_id = f"demo-{index + 1:03d}"
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"

        store.students[student_id] = {
            "id": student_id,
            "name": name,
            "is_demo": True,
            "college": college,
            "major": major,
            "year": year,
            "graduation_date": f"May {grad_year}",
            "gpa": round(rng.uniform(2.4, 3.95), 2),
            "university": "UTSA",
            "skills": rng.sample(skills, k=min(len(skills), 2 + engagement // 2)),
            "career_interests": [rng.choice(titles)],
            "first_generation": rng.random() < 0.45,
            "created_at": (anchor - timedelta(days=rng.randint(30, 160))).isoformat(),
        }

        strength = min(95, int(rng.gauss(42 + engagement * 12, 9)))
        store.save_plan_summary(student_id, {
            "profile_strength": max(10, strength),
            "resume_score": max(25, min(96, int(rng.gauss(52 + engagement * 10, 10)))),
            "top_matches": [
                {"title": rng.choice(titles), "organization": rng.choice(EMPLOYERS),
                 "match_score": max(30, min(97, strength + rng.randint(-8, 14)))}
                for _ in range(3)
            ],
            "skill_gaps": rng.sample(gaps, k=min(len(gaps), 2 + (engagement < 2))),
            "generated_at": (anchor - timedelta(days=rng.randint(1, 60))).isoformat(),
        })

        # Engagement history over the last ~90 days
        counts = {
            "plan_generated": 1 if engagement else rng.random() < 0.2,
            "resume_analyzed": [0, 1, 2, 4][engagement],
            "interview_practiced": [0, 0, 2, 5][engagement] + (rng.random() < 0.3),
            "mission_added": [0, 1, 3, 5][engagement],
            "mission_completed": [0, 0, 1, 3][engagement],
        }
        recent_window = 25 if engagement >= 2 else 85
        for kind, count in counts.items():
            for _ in range(int(count)):
                when = anchor - timedelta(days=rng.randint(1, recent_window), hours=rng.randint(8, 20))
                store.add_activity(student_id, kind, timestamp=when.isoformat(), is_demo=True)

        for event in events:
            attend_chance = [0.0, 0.12, 0.28, 0.45][engagement]
            if rng.random() < attend_chance:
                store.add_checkin(event["id"], student_id, timestamp=event["starts_at"], is_demo=True)
                store.add_activity(student_id, "event_checkin", detail=event["title"],
                                   timestamp=event["starts_at"], is_demo=True)

        # Outcomes: graduating seniors and some juniors with internships
        if year == "Senior" and rng.random() < [0.35, 0.55, 0.75, 0.9][engagement]:
            roll = rng.random()
            placed = roll < [0.55, 0.68, 0.8, 0.9][engagement]
            if placed:
                outcome_type = rng.choices(["full_time", "grad_school", "military_service"], weights=[0.82, 0.14, 0.04])[0]
                degree_required = outcome_type != "full_time" or rng.random() < [0.45, 0.58, 0.72, 0.84][engagement]
                title = rng.choice(titles) if degree_required else rng.choice(NON_DEGREE_TITLES)
                employer = rng.choice(EMPLOYERS) if outcome_type == "full_time" else (
                    "UTSA Graduate School" if outcome_type == "grad_school" else "U.S. Air Force")
                salary = int(rng.gauss(64000 if degree_required else 34000, 7000)) if outcome_type == "full_time" else None
            else:
                outcome_type, degree_required, title, employer, salary = "still_seeking", False, "", "", None
            record = store.set_outcome(student_id, {
                "outcome_type": outcome_type,
                "employer": employer,
                "title": title,
                "degree_required": degree_required,
                "salary": salary,
                "source": "self_report",
                "is_demo": True,
            })
            record["reported_at"] = (anchor - timedelta(days=rng.randint(2, 75))).isoformat()
        elif year == "Junior" and engagement >= 2 and rng.random() < 0.4:
            record = store.set_outcome(student_id, {
                "outcome_type": "internship",
                "employer": rng.choice(EMPLOYERS),
                "title": f"{rng.choice(titles)} Intern",
                "degree_required": True,
                "salary": None,
                "source": "self_report",
                "is_demo": True,
            })
            record["reported_at"] = (anchor - timedelta(days=rng.randint(2, 75))).isoformat()
