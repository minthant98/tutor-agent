# Stride — AI A-Level Tutor

> Your AI Learning Companion. A Socratic A-Level tutor for UK and international students, grounded in real Edexcel and Cambridge past papers.

**Live:** https://tutor-agent-nu.vercel.app

---

## What it does

Stride is a B2C SaaS tutoring product targeting A-Level students (initially Pure Mathematics for Edexcel and Cambridge). Students chat with **Alex**, an AI tutor who teaches via guided questioning rather than giving direct answers, backed by retrieval over real exam board past papers and mark schemes.

A session moves through five phases as the student engages:

1. **Intro** — Alex asks what the student wants to work on
2. **Diagnostic** — one calibration question to gauge starting level
3. **Warmup** — an easy practice question to build confidence
4. **Main** — full Socratic practice: hints, evaluations, mastery updates
5. **Consolidation** — Alex summarises, regenerates the study plan based on today's session

Each practice question renders as a structured **Practice Question card** with a "Submit answer" button, and grading appears as a **Results card** showing marks awarded, what the student got right, and where they lost marks.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11), tool-calling state machine |
| LLM | Groq with 3-model fallback chain (llama-4-scout → llama-3.3-70b → llama-3.1-8b) |
| Frontend | Next.js 16 (App Router), KaTeX for math rendering |
| Database | Supabase PostgreSQL (SQLAlchemy + Alembic) |
| Session state | Upstash Redis |
| Vector search | Qdrant Cloud |
| Embeddings | SentenceTransformer `all-MiniLM-L6-v2` + CrossEncoder reranker |
| Math validation | SymPy (objective answer equivalence) |
| Auth | JWT (bcrypt password hashing) |
| Billing | Stripe (subscriptions + Customer Portal + webhooks) |
| Observability | PostHog (telemetry) + Sentry (errors) |
| Backend hosting | Google Cloud Run (europe-west2) |
| Frontend hosting | Vercel |

---

## Knowledge base (~34,000 chunks)

| Board | Past papers | Mark schemes | Syllabus | Model answers | Total |
|---|---|---|---|---|---|
| Edexcel A-Level Maths | 12,677 | 5,510 | 360 | 4,711 | **23,259** |
| Cambridge (CIE) A-Level Maths | 7,688 | 3,294 | 347 | — | **11,329** |

Indexed in Qdrant with payload filters for `exam_board`, `subject`, `doc_type`. Subject alias mapping handles board-specific naming (e.g. Cambridge ingested as `mathematics`, student profiles use `pure_mathematics`).

---

## Architecture

```
Student message (SSE stream)
      ↓
FastAPI session endpoint
      ↓
Tutor agent — system prompt with current phase + signal
      ↓
Phase 1: LLM tool selection (non-streaming, ~200ms)
      ↓
   ┌─────────────────────────────────────────────┐
   │  search_syllabus    — RAG over Qdrant        │
   │  generate_question  — RAG-grounded past-     │
   │                       paper-style question   │
   │                       with M1/A1/B1 marks    │
   │  evaluate_answer    — SymPy equivalence +    │
   │                       LLM mark scheme grade  │
   └─────────────────────────────────────────────┘
      ↓
Phase 2: Stream final response tokens (+ emit
         structured question/evaluation cards)
      ↓
Update mastery (exponential moving average, α=0.3)
Advance phase if turn count hits next threshold
Auto-regenerate study plan if entering consolidation
      ↓
Persist conversation to Postgres, save state to Redis
```

---

## Notable features

- **Structured grading** — `generate_question` and `evaluate_answer` outputs render as first-class UI cards (question + Submit button, results with marks breakdown), not buried in chat
- **3-model LLM fallback** — on rate-limit (429) or timeout, automatically falls through to the next model. Eliminates traffic-spike outages on the free Groq tier
- **Session continuity** — closing the tab mid-session is fine; the dashboard surfaces "Continue where you left off" and rebuilds Redis state from Postgres on resume
- **Mastery → study plan loop** — every graded answer updates a topic mastery EMA. Weak topics drive the auto-generated weekly study plan, which regenerates when the student reaches the consolidation phase
- **Tiered help signals** — students can request "Explain this concept" (full explanation + worked example) or "Give me a hint" (one scaffolded hint then a leading question)
- **Math equivalence check** — SymPy validates whether the student's answer is mathematically equivalent to the mark scheme, catching `x(x+2)` vs `x² + 2x` as the same answer
- **Telemetry** — PostHog captures the full funnel: signup → onboarding → session_started → question_generated → question_submitted → answer_evaluated → phase_advanced

---

## Pricing

- **Free** — 50 messages/day, Pure Mathematics only, Socratic tutoring, Explain & Guide modes, topic mastery tracking
- **Pro** — 50,000 MMK/month, all subjects (when expanded), unlimited messages, session memory & continuity, personalised study plan, weak topic coaching, 7-day free trial

---

## Local development

**Prerequisites:** Python 3.11+, Node.js 20+, Docker (optional, for local Postgres/Redis)

### Backend

```bash
git clone https://github.com/minthant98/tutor-agent.git
cd tutor-agent

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with API keys (see Environment variables below)

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`.

### Frontend

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`.

---

## Environment variables

### Backend (`/.env`)

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for LLM inference |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant Cloud API key |
| `DATABASE_URL` | asyncpg-style PostgreSQL URL (with `statement_cache_size=0` for Supabase pooler) |
| `SYNC_DATABASE_URL` | sync PostgreSQL URL for Alembic migrations |
| `REDIS_URL` | Upstash Redis URL (must be `rediss://` for TLS) |
| `SECRET_KEY` | JWT signing secret |
| `STRIPE_SECRET_KEY` | Stripe secret API key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `STRIPE_PRO_PRICE_ID` | Stripe `price_xxx` for the Pro subscription |
| `FRONTEND_URL` | Public frontend URL (used in Stripe redirects) |
| `SENTRY_DSN` | Sentry DSN (backend) |
| `POSTHOG_KEY` | PostHog project API key (server-side) |
| `POSTHOG_HOST` | PostHog ingestion host (default `https://us.i.posthog.com`) |
| `FREE_DAILY_MESSAGE_LIMIT` | Free tier rate limit (default 50, demo period) |

### Frontend (`web/.env.production` via Vercel)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API URL |
| `NEXT_PUBLIC_POSTHOG_KEY` | PostHog project API key (client-side) |
| `NEXT_PUBLIC_POSTHOG_HOST` | PostHog ingestion host |
| `NEXT_PUBLIC_SENTRY_DSN` | Sentry DSN (frontend) |

---

## Deployment

### Backend (Google Cloud Run)

```bash
# Build & push image via Cloud Build (Apple Silicon can't build the heavy ML image locally)
gcloud builds submit --tag gcr.io/ascend-tutor-prod/tutor-api:latest --timeout=20m

# Deploy to Cloud Run
gcloud run deploy ascend-api \
  --image gcr.io/ascend-tutor-prod/tutor-api:latest \
  --region europe-west2 \
  --platform managed

# Cold-start is killed by keeping min-instances=1
gcloud run services update ascend-api --region=europe-west2 --min-instances=1
```

Migrations run automatically on container startup via `start.sh`.

### Frontend (Vercel)

Auto-deploys from `main` branch via GitHub integration. Root directory is `web/`.

---

## Project structure

```
tutor_agent/
├── app/
│   ├── agents/            # tutor_agent.py (Alex), tools.py (RAG tools)
│   ├── api/v1/endpoints/  # auth, sessions, billing, study_plan
│   ├── core/              # config, llm fallback chain, telemetry, math_validator
│   ├── db/                # SQLAlchemy models + async session
│   ├── rag/               # Qdrant ingestor + retriever
│   ├── services/          # session_service, billing_service, study_plan_service
│   ├── workflows/         # SessionState typed dict
│   └── main.py            # FastAPI app factory
├── alembic/versions/      # database migrations
├── docs/                  # raw exam PDFs (edexcel/, cambridge/) — gitignored
├── scripts/               # ingest_docs.py for bulk RAG ingestion
└── web/                   # Next.js frontend (App Router)
    └── src/
        ├── app/           # (app), (auth), (onboarding) route groups
        ├── components/    # Logo, shared UI
        └── lib/           # api client, posthog, auth, math rendering
```

---

## Roadmap

**Live now:**
- Pure Mathematics for Edexcel and Cambridge
- Full session flow with structured grading
- Study plan + mastery tracking
- Stripe billing + free tier rate limiting

**Coming soon (in order of likely priority based on beta data):**
- Tiered hint system (Hint → More Hint → Walkthrough → Full Solution) to replace the binary Explain/Guide
- Past Paper Mode — retrieve and grade against real past paper Q+MS pairs (currently mark schemes are LLM-generated)
- Mechanics & Statistics, Physics, Chemistry subjects
- IB exam board
- Spaced repetition for weak topic review
- Mobile app

---

## Built by

Min Thant Tin — [github.com/minthant98](https://github.com/minthant98)
