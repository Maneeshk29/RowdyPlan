# RowdyPlan

**Your opportunities. Your path. One plan.**

RowdyPlan is a predictive career intelligence engine built for UTSA students. You tell it who you are — your major, GPA, skills, and goals — and it tells you exactly which opportunities you're qualified for, what's holding you back, and what to do next.

This is **not a chatbot**. It's a prediction system. Every score is deterministic: same input, same output, no LLM-generated numbers.

---

## What It Does

1. **You fill out a profile** — major, GPA, year, skills, career goals, and optionally upload your resume
2. **The engine runs** — it scores you against 48 real UTSA-area opportunities (jobs, research, events, orgs, programs)
3. **You get a dashboard** with:
   - **Career path predictions** — which careers fit your skills (ranked by match %)
   - **Job/opportunity matches** — each one scored with a detailed breakdown (skills, experience, education, career interest, location, goal fit)
   - **Qualification status** — QUALIFIED, LIKELY_QUALIFIED, SKILL_GAP, or NOT_ELIGIBLE for each opportunity
   - **Skill gap analysis** — exactly which skills you're missing, prioritized by importance
   - **Resume intelligence** — ATS score, bullet quality analysis, rewrite suggestions
   - **A timeline** — what to do now, in 30 days, next semester, and next year
4. **"Why Not Me?"** — click any opportunity to see exactly why your score is what it is and what closes the gap

---

## How the Scoring Works

No black boxes. Every number comes from weighted formulas using set intersection and cosine similarity.

### Career Matching
| Weight | Factor |
|--------|--------|
| 50% | Skill overlap (your skills vs. career's typical skills) |
| 15% | Coursework alignment |
| 20% | Experience relevance |
| 15% | Stated career interest |

### Job/Opportunity Matching
| Weight | Factor |
|--------|--------|
| 35% | Skill similarity |
| 20% | Experience level |
| 15% | Education match (GPA, major) |
| 10% | Career interest alignment |
| 10% | Location preference |
| 10% | Goal fit (internship vs. full-time vs. research) |

### Resume Scoring (out of 100)
| Points | Factor |
|--------|--------|
| 40 | Keyword coverage for target career |
| 20 | Section completeness (education, experience, skills, projects) |
| 20 | Bullet quality (action verbs, measurable impact) |
| 20 | Impact metrics (numbers, percentages, quantified results) |

### Qualification Filter
Each opportunity gets one of:
- **QUALIFIED** — you meet all hard requirements
- **LIKELY_QUALIFIED** — you're close (e.g., GPA within 0.2 of minimum)
- **SKILL_GAP** — you have the basics but missing key skills
- **NOT_ELIGIBLE** — wrong major, GPA too low, or wrong graduation year
- **UNKNOWN** — not enough data to determine

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│              index.html (single file)                │
│                                                      │
│  Landing Page → Onboarding Wizard → Dashboard        │
│  Explore Hub · Career Plan · Interview Room · Chat   │
│                                                      │
│  Calls backend REST API via fetch()                  │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (same origin :8000)
┌──────────────────────▼──────────────────────────────┐
│                  FASTAPI BACKEND                     │
│                                                      │
│  /api/rowdy-plan/generate-inline  ← main endpoint   │
│  /api/students/profile            ← CRUD profiles    │
│  /api/resume/upload               ← PDF/DOCX parse   │
│  /api/resume/analyze              ← ATS scoring       │
│  /api/careers/recommendations     ← career matching   │
│  /api/jobs/recommendations        ← job matching      │
│  /api/experiences/recommendations ← experience gaps   │
│  /api/opportunities               ← browse all        │
│  /api/feedback                    ← event logging     │
│  /api/admin/seed                  ← load UTSA data    │
│                                                      │
├──────────────────────────────────────────────────────┤
│              RECOMMENDATION ENGINE                   │
│                                                      │
│  ProfileBuilder     → validates & enriches profile   │
│  FeatureExtractor   → 122-skill taxonomy vectors     │
│  CareerMatcher      → 15 career paths scored         │
│  JobMatcher         → weighted 6-factor scoring      │
│  ExperienceMatcher  → 22 university experiences      │
│  ResumeAnalyzer     → ATS score + bullet rewrites    │
│  GapAnalyzer        → skill gaps prioritized         │
│  RankingEngine      → sort + diversity + qualify     │
│  PlanGenerator      → orchestrates full pipeline     │
│                                                      │
├──────────────────────────────────────────────────────┤
│               DATA LAYER                             │
│                                                      │
│  InMemoryStore (demo)  ← works without any database  │
│  UTSAProvider          ← 48 mock UTSA opportunities  │
│  PostgreSQL + pgvector ← production (optional)       │
│  Sentence-transformers ← embeddings (optional)       │
└──────────────────────────────────────────────────────┘
```

---

## Project Structure

```
RowdyPlan/
├── index.html                          # Frontend (single-page app)
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entry point, serves frontend
│   │   ├── api/                        # REST endpoints
│   │   │   ├── students.py             # Student profile CRUD
│   │   │   ├── resume.py               # Resume upload & analysis
│   │   │   ├── careers.py              # Career recommendations
│   │   │   ├── jobs.py                 # Job recommendations
│   │   │   ├── experiences.py          # Experience recommendations
│   │   │   ├── rowdy_plan.py           # Main plan generation endpoint
│   │   │   ├── opportunities.py        # Browse/search opportunities
│   │   │   ├── feedback.py             # User feedback events
│   │   │   ├── admin.py                # Seed data, manage opportunities
│   │   │   └── mock_store.py           # In-memory database for demo mode
│   │   ├── recommendation/             # The prediction engine
│   │   │   ├── plan_generator.py       # Orchestrates the full pipeline
│   │   │   ├── career_matcher.py       # 15 careers, weighted scoring
│   │   │   ├── job_matcher.py          # 6-factor opportunity scoring
│   │   │   ├── experience_matcher.py   # 22 university experiences
│   │   │   ├── resume_analyzer.py      # ATS scoring, bullet rewrites
│   │   │   ├── gap_analysis.py         # Skill gap prioritization
│   │   │   ├── feature_extractor.py    # 122-skill vector extraction
│   │   │   ├── profile_builder.py      # Profile strength calculator
│   │   │   ├── ranking.py              # Sort, diversity, qualification
│   │   │   ├── candidate_retrieval.py  # Cosine similarity retrieval
│   │   │   └── embeddings.py           # Sentence-transformer embeddings
│   │   ├── ingestion/                  # Data providers
│   │   │   ├── base_provider.py        # Abstract provider interface
│   │   │   ├── utsa_provider.py        # 48 mock UTSA opportunities
│   │   │   └── normalization.py        # Dedup & validation
│   │   ├── models/                     # SQLAlchemy database models
│   │   ├── schemas/                    # Pydantic request/response schemas
│   │   ├── services/                   # Business logic layer
│   │   ├── tests/                      # 75 tests across 7 test files
│   │   ├── core/                       # Config, dependencies
│   │   ├── database/                   # DB session, base model
│   │   └── workers/                    # Celery background tasks (structure)
│   ├── seeds/                          # Sample student data
│   ├── demo.py                         # CLI walkthrough of the full pipeline
│   ├── requirements.txt                # Python dependencies
│   ├── Dockerfile                      # Container build
│   └── docker-compose.yml              # App + PostgreSQL + Redis
```

---

## Quick Start

### Run the prototype (no database needed)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000** in your browser. That's it.

The app auto-seeds 48 UTSA opportunities on startup. Click "Build My Plan" to go through onboarding, or "Demo Dashboard" to jump straight in with a sample profile.

### Run the CLI demo

```bash
cd backend
python demo.py
```

Prints the full prediction pipeline step-by-step in your terminal — profile analysis, feature extraction, career matching, job matching, experience gaps, resume scoring, skill gaps, and the final plan.

### Run tests

```bash
cd backend
python -m pytest app/tests/ -v
```

75 tests covering the recommendation engine, API endpoints, services, and data ingestion.

### Run with Docker (production mode with PostgreSQL)

```bash
cd backend
docker-compose up --build
```

Starts the app, PostgreSQL with pgvector, and Redis.

---

## The Data

### 15 Career Paths
Software Engineer, Data Engineer, Data Scientist, ML Engineer, BI Analyst, Product Manager, Cybersecurity Analyst, DevOps Engineer, Cloud Engineer, Full Stack Developer, Mobile Developer, UX Researcher, Systems Engineer, DBA, Research Scientist

### 48 UTSA Opportunities
- **15 jobs** — USAA, Rackspace, H-E-B Digital, Booz Allen, Frost Bank, Accenture, SwRI, CPS Energy, Valero, UTSA IT
- **10 events** — Career expos, tech talks, workshops, hackathons
- **8 research** — AI/ML labs, cybersecurity, data science, software engineering
- **10 organizations** — ACM, IEEE, GDSC, Women in Cyber, Data Science Club, etc.
- **5 programs** — Mentorship, accelerators, leadership development

### 122-Skill Taxonomy
The feature extractor maps student skills to a 122-dimensional vector covering languages, frameworks, databases, cloud, DevOps, data science, security, and soft skills.

---

## Key Design Decisions

- **No LLM for scoring.** Every number comes from deterministic weighted formulas. LLMs are unreliable for numerical scoring — they hallucinate confidence. We use set intersection, cosine similarity, and rule-based logic instead.
- **InMemoryStore for demo.** The app works without PostgreSQL. A singleton in-memory store holds all data so you can run the prototype with zero setup.
- **Resume parsing is real.** Upload a PDF or DOCX and it extracts text, identifies skills, and scores against your target career using pdfplumber/PyPDF2/python-docx.
- **Frontend is one HTML file.** No build step, no React, no npm. One file with inline CSS and JS. The backend serves it directly.
- **Provider pattern for data.** The `UTSAProvider` follows an abstract `UniversityOpportunityProvider` interface. Swap in a Handshake scraper, LinkedIn API, or any other source — same shape, same pipeline.
- **Feedback events for future learning.** The `/api/feedback` endpoint collects click, view, apply, and dismiss events. These are stored for future learning-to-rank model training — the system gets smarter over time.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/rowdy-plan/generate-inline` | Generate a full plan from raw profile data |
| POST | `/api/rowdy-plan/generate` | Generate a plan for an existing student |
| POST | `/api/rowdy-plan/generate-stream` | SSE streaming version for frontend animation |
| POST | `/api/students/profile` | Create a student profile |
| GET | `/api/students/{id}/profile` | Get a student profile |
| PUT | `/api/students/{id}/profile` | Update a student profile |
| POST | `/api/resume/upload` | Upload and parse a PDF/DOCX resume |
| POST | `/api/resume/analyze` | Analyze resume against a target career |
| GET | `/api/careers` | List all career paths |
| GET | `/api/careers/recommendations` | Get career recommendations for a student |
| GET | `/api/jobs/recommendations` | Get job recommendations for a student |
| GET | `/api/experiences/recommendations` | Get experience recommendations |
| GET | `/api/opportunities` | List all opportunities |
| POST | `/api/opportunities/search` | Search opportunities with filters |
| POST | `/api/feedback` | Log a feedback event |
| POST | `/api/admin/seed` | Seed database with UTSA mock data |
| POST | `/api/admin/ingest` | Trigger data ingestion from a provider |
| GET | `/health` | Health check |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML/CSS/JS, Plus Jakarta Sans, JetBrains Mono |
| Backend | Python 3.12, FastAPI, Pydantic v2, Uvicorn |
| Database | InMemoryStore (demo), PostgreSQL + pgvector (production) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2), fallback to random vectors |
| Resume Parsing | pdfplumber, PyPDF2, python-docx |
| ML/Scoring | scikit-learn (cosine similarity), numpy |
| Background Jobs | Celery + Redis (structure in place) |
| Containerization | Docker, docker-compose |

---

## Built For

[RowdyHacks](https://rowdyhacks.org/) — UTSA's annual hackathon.

The goal: help every UTSA student find the right opportunities, understand what they're missing, and build a concrete plan to get where they want to go.
