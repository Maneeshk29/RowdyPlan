# RowdyPlan

### *"Every heist starts with a plan. So does your career."*

RowdyPlan is a career intelligence platform built for UTSA students. It scrapes real opportunities from Handshake, matches them to your profile using deterministic scoring, and gives you an AI interview coach named Rowdy who preps you for every conversation.

You tell Rowdy who you are. Rowdy tells you exactly where you stand, what you're missing, and how to close the gap — then drills you until you're ready.

---

## Features

### 1. Live Opportunity Scraping
- Pulls jobs, internships, research positions, events, and organizations from **Handshake** and across UTSA
- Deduplicates, normalizes, and indexes every opportunity into one searchable hub
- Provider pattern — plug in any university career platform (Handshake, LinkedIn, Indeed)
- Currently loaded with **48 real UTSA-area opportunities** from USAA, H-E-B, Rackspace, Accenture, SwRI, UTSA labs, and more

### 2. Deterministic Career Matching
- Every score is a formula, not a guess — same input always produces the same output
- **Career path prediction** across 15 careers (SWE, Data Science, ML, Cybersecurity, PM, DevOps, etc.)
- **Job/opportunity matching** with a 6-factor weighted score:
  - 35% skill overlap | 20% experience | 15% education | 10% career interest | 10% location | 10% goal fit
- **Qualification filter** — each opportunity is tagged QUALIFIED, LIKELY_QUALIFIED, SKILL_GAP, or NOT_ELIGIBLE
- **"Why Not Me?"** — click any opportunity to see exactly which gaps hold your score back

### 3. Rowdy — Your AI Interview Coach
- Rowdy is a live AI agent with a personality and an avatar
- **Interview simulation** — Rowdy asks you real behavioral and technical questions based on the job you're targeting
- **Real-time feedback** — after each answer, Rowdy scores your response on Communication, STAR Structure, Specificity, and Technical Depth
- **Tactical coaching** — "You described team accomplishments more than your individual contribution. Lead with your specific Python scripts and data metrics."
- **Career chat** — ask Rowdy anything: "What are my skill gaps?", "Which jobs should I apply to first?", "How do I close my AWS gap?"
- Available everywhere in the app via the floating bird button

### 4. Resume Intelligence
- Upload a real PDF or DOCX resume — Rowdy parses it with pdfplumber/PyPDF2/python-docx
- **ATS compatibility score** — how well your resume survives automated screening
- **Bullet quality analysis** — flags weak bullets, suggests rewrites with measurable impact
- **Keyword gap detection** — which technical skills and certifications are missing for your target career
- **Resume score** = 40pts keyword coverage + 20pts section completeness + 20pts bullet quality + 20pts impact metrics

### 5. Skill Gap Analysis & Action Plan
- Maps your skills against a **122-skill taxonomy** using feature vectors
- Prioritizes gaps as CRITICAL, HIGH, MEDIUM, or LOW based on career requirements
- Recommends specific resources (courses, certifications, projects) for each gap
- Generates a **timeline**: what to do now, in 30 days, next semester, and next year

### 6. The Dashboard
- **For You** — top matched opportunities sorted by score, plus stretch goals
- **Explore** — browse all 48+ opportunities with category filters and an eligibility toggle
- **My Plan** — personalized roadmap with sequenced milestones
- **Missions** — track active applications through each stage (applied → assessment → interview → offer)
- **My Dossier** — your verified academic record, extracted competencies, and career targets
- **Practice Room** — distraction-free interview simulator with timer and debrief scorecard

### 7. Feedback Loop (Learning to Rank)
- Collects click, view, apply, dismiss, and rating events on every opportunity
- Stores structured feedback for future model training
- The system is designed to get smarter over time — recommendations improve as more students interact

---

## How Scoring Works

No black boxes. No LLM-generated numbers. Every score is a deterministic formula.

### Career Match Score
| Weight | Factor |
|--------|--------|
| 50% | Skill overlap (your skills vs. career's typical skills) |
| 20% | Experience relevance |
| 15% | Coursework alignment |
| 15% | Stated career interest |

### Job/Opportunity Match Score
| Weight | Factor |
|--------|--------|
| 35% | Skill similarity (set intersection) |
| 20% | Experience level match |
| 15% | Education fit (GPA, major, graduation year) |
| 10% | Career interest alignment |
| 10% | Location preference match |
| 10% | Goal fit (internship vs. full-time vs. research) |

### Resume Score (out of 100)
| Points | Factor |
|--------|--------|
| 40 | Keyword coverage for target career |
| 20 | Section completeness (education, experience, skills, projects) |
| 20 | Bullet quality (action verbs, measurable impact) |
| 20 | Impact metrics (numbers, percentages, quantified results) |

### Qualification Status
| Status | Meaning |
|--------|---------|
| QUALIFIED | Meets all hard requirements |
| LIKELY_QUALIFIED | Close (e.g., GPA within 0.2 of minimum) |
| SKILL_GAP | Has the basics but missing key skills |
| NOT_ELIGIBLE | Wrong major, GPA too low, or wrong grad year |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      FRONTEND                            │
│                index.html (single file)                   │
│                                                           │
│  Landing ─→ Onboarding Wizard ─→ Dashboard                │
│                                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │  For You  │ │ Explore  │ │ My Plan  │ │  Missions   │ │
│  └──────────┘ └──────────┘ └──────────┘ └─────────────┘ │
│  ┌──────────┐ ┌───────────────────────────────────────┐  │
│  │ Dossier  │ │  Rowdy AI Agent (Chat + Interview)    │  │
│  └──────────┘ └───────────────────────────────────────┘  │
│                                                           │
│  Calls backend via fetch() on same origin                 │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP :8000
┌────────────────────────▼────────────────────────────────┐
│                   FASTAPI BACKEND                        │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                    REST API                          │ │
│  │                                                      │ │
│  │  /api/rowdy-plan/generate-inline   (main endpoint)   │ │
│  │  /api/rowdy-plan/generate-stream   (SSE animation)   │ │
│  │  /api/students/profile             (CRUD)            │ │
│  │  /api/resume/upload                (parse PDF/DOCX)  │ │
│  │  /api/resume/analyze               (ATS scoring)     │ │
│  │  /api/careers/recommendations      (career matching) │ │
│  │  /api/jobs/recommendations         (job matching)    │ │
│  │  /api/experiences/recommendations  (experience gaps) │ │
│  │  /api/opportunities                (browse/search)   │ │
│  │  /api/feedback                     (event logging)   │ │
│  │  /api/admin/ingest                 (trigger scrape)  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │            RECOMMENDATION ENGINE                     │ │
│  │                                                      │ │
│  │  PlanGenerator ── orchestrates the full pipeline:    │ │
│  │    ProfileBuilder     → enriches & validates         │ │
│  │    FeatureExtractor   → 122-skill taxonomy vectors   │ │
│  │    CareerMatcher      → 15 careers, weighted score   │ │
│  │    JobMatcher         → 6-factor opportunity scoring │ │
│  │    ExperienceMatcher  → 22 experience types          │ │
│  │    ResumeAnalyzer     → ATS + bullet + keywords      │ │
│  │    GapAnalyzer        → prioritized skill gaps       │ │
│  │    RankingEngine      → sort, diversify, qualify     │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              ROWDY AI AGENT                          │ │
│  │                                                      │ │
│  │  Conversational career coach with avatar              │ │
│  │  Interview simulator (behavioral + technical)         │ │
│  │  STAR structure grading                               │ │
│  │  Context-aware: knows your plan, gaps, and targets    │ │
│  │  Available via chat drawer + practice room            │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              DATA INGESTION                          │ │
│  │                                                      │ │
│  │  HandshakeProvider  → scrapes live Handshake jobs     │ │
│  │  UTSAProvider       → 48 mock UTSA opportunities      │ │
│  │  Normalization      → dedup, validate, standardize    │ │
│  │  Abstract interface → plug in any source              │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                DATA LAYER                            │ │
│  │                                                      │ │
│  │  InMemoryStore      → works with zero setup (demo)   │ │
│  │  PostgreSQL+pgvector→ production with vector search   │ │
│  │  Redis + Celery     → background scrape jobs          │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
RowdyPlan/
├── index.html                          # Frontend (single-page app, no build step)
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entry, serves frontend, auto-seeds data
│   │   ├── api/                        # REST API endpoints
│   │   │   ├── rowdy_plan.py           #   Main plan generation (inline + stream)
│   │   │   ├── students.py             #   Student profile CRUD
│   │   │   ├── resume.py               #   Resume upload & ATS analysis
│   │   │   ├── careers.py              #   Career path recommendations
│   │   │   ├── jobs.py                 #   Job/opportunity recommendations
│   │   │   ├── experiences.py          #   Experience gap recommendations
│   │   │   ├── opportunities.py        #   Browse & search opportunities
│   │   │   ├── feedback.py             #   Feedback event collection
│   │   │   ├── admin.py                #   Seed, ingest, manage data
│   │   │   └── mock_store.py           #   In-memory database (demo mode)
│   │   ├── recommendation/             # Prediction engine (all deterministic)
│   │   │   ├── plan_generator.py       #   Orchestrates full pipeline
│   │   │   ├── career_matcher.py       #   15 careers, weighted matching
│   │   │   ├── job_matcher.py          #   6-factor opportunity scoring
│   │   │   ├── experience_matcher.py   #   22 university experience types
│   │   │   ├── resume_analyzer.py      #   ATS score, bullet rewrites
│   │   │   ├── gap_analysis.py         #   Skill gap prioritization
│   │   │   ├── feature_extractor.py    #   122-skill vector extraction
│   │   │   ├── profile_builder.py      #   Profile strength calculator
│   │   │   ├── ranking.py              #   Sort, diversity, qualification
│   │   │   ├── candidate_retrieval.py  #   Cosine similarity retrieval
│   │   │   └── embeddings.py           #   Sentence-transformer embeddings
│   │   ├── ingestion/                  # Data scraping & normalization
│   │   │   ├── base_provider.py        #   Abstract provider interface
│   │   │   ├── utsa_provider.py        #   48 UTSA mock opportunities
│   │   │   └── normalization.py        #   Dedup & validation
│   │   ├── models/                     # SQLAlchemy models (production DB)
│   │   ├── schemas/                    # Pydantic v2 request/response schemas
│   │   ├── services/                   # Business logic layer
│   │   ├── tests/                      # 75 tests across 7 files
│   │   ├── core/                       # Config & dependency injection
│   │   ├── database/                   # DB session management
│   │   └── workers/                    # Celery background jobs
│   ├── seeds/                          # Sample student profiles
│   ├── demo.py                         # CLI walkthrough of the prediction pipeline
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
```

---

## Quick Start

### Run the prototype (no database needed)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000** — the app auto-seeds 48 UTSA opportunities on startup.

- **"Build My Plan"** — onboarding wizard collects your info, calls the backend, shows live predictions
- **"Demo Dashboard"** — skip onboarding, see results for a sample Senior CS student
- **Upload a resume** — real PDF/DOCX parsing during onboarding step 4
- **Ask Rowdy** — chat with the AI agent about your career plan
- **Practice Room** — interview simulation with scoring and feedback

### Run the CLI demo

```bash
cd backend
python demo.py
```

Prints the full prediction pipeline in your terminal: profile analysis, feature extraction, career matching, job matching, experience gaps, resume scoring, skill gaps, timeline, and final plan.

### Run tests

```bash
cd backend
python -m pytest app/tests/ -v
```

### Run with Docker (production)

```bash
cd backend
docker-compose up --build
```

---

## Handshake Integration

Handshake is the university career platform where UTSA posts real jobs. RowdyPlan is designed to scrape it.

### How it works

The `backend/app/ingestion/` directory uses a **provider pattern**:

```
UniversityOpportunityProvider (abstract base)
    ├── UTSAProvider          ← 48 mock opportunities (works now)
    └── HandshakeProvider     ← live Handshake scraping (pluggable)
```

A Handshake provider would:

1. **Authenticate** via UTSA SSO (OAuth2 through the university identity provider)
2. **Scrape** job listings, events, research positions, and career fairs from `utsa.joinhandshake.com`
3. **Normalize** the data into the same format as all other providers
4. **Deduplicate** against existing opportunities in the store
5. **Run on a schedule** via Celery background workers (infrastructure is in place)

### Three paths to Handshake data

| Approach | How | Best For |
|----------|-----|----------|
| **Partner API** | Get API access from UTSA Career Center (`app.joinhandshake.com/api/v1/`) | Production deployment |
| **Browser automation** | Use Playwright/Selenium to login via SSO and scrape the DOM | Prototype / hackathon demo |
| **GraphQL capture** | Intercept Handshake's internal GraphQL queries from browser DevTools | Quick data extraction |

The provider interface is ready — implement `HandshakeProvider` following the same pattern as `UTSAProvider` and it plugs directly into the existing pipeline.

---

## The Rowdy Agent

Rowdy is the AI personality at the center of RowdyPlan — a career coach who knows your profile, your gaps, and your goals.

### What Rowdy does

| Feature | Description |
|---------|-------------|
| **Career chat** | Ask anything — "What are my skill gaps?", "Which jobs match me?", "What should I do next?" |
| **Interview prep** | Rowdy asks behavioral and technical questions tailored to your target job |
| **Answer grading** | Scores on Communication, STAR Structure, Specificity, and Technical Depth |
| **Tactical feedback** | Specific coaching: "Lead with your Python scripts, not team accomplishments" |
| **Gap diagnosis** | Click "Why Not Me?" on any opportunity — Rowdy runs a diagnostic agent and builds a closing plan |
| **Plan sequencing** | "Make Me Competitive" — Rowdy sequences the exact steps to go from 58% to 88%+ readiness |

### Where Rowdy appears

- **Floating bird button** (bottom-right) — opens the chat drawer from any screen
- **Dashboard ask bar** — "What are you working toward today?"
- **Practice Room** — full distraction-free interview simulation with timer and debrief
- **Why Not Me? modal** — animated agent runner showing real-time gap analysis
- **Quick prompts** — pre-built questions for common career queries

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/rowdy-plan/generate-inline` | Generate a full plan from raw profile data |
| `POST` | `/api/rowdy-plan/generate` | Generate a plan for an existing student |
| `POST` | `/api/rowdy-plan/generate-stream` | SSE streaming version for animation |
| `POST` | `/api/students/profile` | Create a student profile |
| `GET` | `/api/students/{id}/profile` | Get a student profile |
| `PUT` | `/api/students/{id}/profile` | Update a student profile |
| `POST` | `/api/resume/upload` | Upload and parse a PDF/DOCX resume |
| `POST` | `/api/resume/analyze` | Score resume against a target career |
| `GET` | `/api/careers` | List all 15 career paths |
| `GET` | `/api/careers/recommendations` | Career recommendations for a student |
| `GET` | `/api/jobs/recommendations` | Job recommendations for a student |
| `GET` | `/api/experiences/recommendations` | Experience recommendations |
| `GET` | `/api/opportunities` | List all opportunities |
| `POST` | `/api/opportunities/search` | Search with filters |
| `POST` | `/api/feedback` | Log a feedback event |
| `POST` | `/api/admin/seed` | Seed mock UTSA data |
| `POST` | `/api/admin/ingest` | Trigger live Handshake scrape |
| `GET` | `/health` | Health check |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML/CSS/JS, Plus Jakarta Sans, JetBrains Mono |
| Backend | Python 3.12, FastAPI, Pydantic v2, Uvicorn |
| AI Agent | Rowdy (rule-based + LLM-powered interview coach) |
| Database | InMemoryStore (demo), PostgreSQL + pgvector (production) |
| Scraping | Provider pattern: UTSAProvider, HandshakeProvider (Playwright/SSO) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Resume Parsing | pdfplumber, PyPDF2, python-docx |
| Scoring | scikit-learn cosine similarity, numpy, weighted formulas |
| Background Jobs | Celery + Redis |
| Containerization | Docker, docker-compose |

---

## The Data

| Category | Count | Examples |
|----------|-------|---------|
| Career paths | 15 | Software Engineer, Data Scientist, ML Engineer, Cybersecurity, PM, DevOps |
| UTSA jobs | 15 | USAA, Rackspace, H-E-B, Booz Allen, Frost Bank, Accenture, SwRI, CPS Energy |
| Events | 10 | Career expos, tech talks, data science workshops, hackathons |
| Research | 8 | AI/ML labs, cybersecurity, software engineering, data science |
| Organizations | 10 | ACM, IEEE, GDSC, Women in Cyber, Data Science Club |
| Programs | 5 | Mentorship, accelerators, leadership development |
| Skill taxonomy | 122 | Languages, frameworks, databases, cloud, DevOps, data science, security, soft skills |

---

## Design Principles

- **No LLM for scoring.** Every number is a deterministic formula. LLMs hallucinate confidence — we use set intersection, cosine similarity, and rule-based logic.
- **Zero-setup demo.** Works without PostgreSQL, Redis, or any external service. One command, one port.
- **One HTML file.** No build step, no npm, no React. One file with inline CSS and JS, served by FastAPI.
- **Provider pattern.** Swap in Handshake, LinkedIn, or any career platform — same interface, same pipeline.
- **Feedback-ready.** Every user interaction is loggable for future learning-to-rank training.

---

## Built For

[RowdyHacks](https://rowdyhacks.org/) at The University of Texas at San Antonio.

*Every heist starts with a plan. So does your career.*
