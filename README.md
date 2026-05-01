# Ascend Tutor — AI-Powered A-Level Mathematics Tutor

An intelligent tutoring system for Edexcel A-Level Pure Mathematics students. Built with FastAPI, LangGraph, and RAG over real Edexcel past papers and mark schemes.

**Live demo:** https://ascend-tutor-ai-agent.netlify.app

---

## What it does

- **Explains concepts** grounded in the Edexcel syllabus — not generic AI responses
- **Generates practice questions** from real past papers (2018–2024)
- **Marks student answers** against official mark schemes with partial credit
- **Tracks mastery** per topic using spaced repetition
- **Adapts in real time** — re-explains when students struggle, escalates difficulty when they're ready

---

## Tech stack

| Layer | Technology |
|---|---|
| API | FastAPI + Pydantic |
| Agent orchestration | LangGraph |
| LLM | Groq (Llama 4 Scout) |
| Vector database | Qdrant Cloud |
| Knowledge base | 13,418 chunks — Edexcel past papers, mark schemes, model answers, syllabus |
| Database | PostgreSQL (SQLAlchemy + Alembic) |
| Session state | Redis |
| Auth | JWT |
| Frontend | Vanilla HTML/JS with KaTeX math rendering |
| Deployment | Railway (API) + Netlify (frontend) |

---

## Architecture
Student message
↓
Intent agent        — classify: explain / quiz / hint / check_answer / off_topic
↓
Retrieval agent     — semantic search over 13,418 Edexcel chunks (Qdrant)
↓
┌─────────────────────────────────┐
│  Tutor agent    — RAG explanation│
│  Quiz agent     — past paper Q  │
│  Evaluator      — mark scheme   │
│  Hint agent     — scaffolded    │
└─────────────────────────────────┘
↓
Rules engine        — deterministic safety layer (no AI)
↓
Adapt agent         — update mastery, decide next action
↓
PostgreSQL          — persist session, update mastery scores

---

## Knowledge base

- **7 years** of Edexcel Pure Mathematics past papers (2018–2024)
- Paper 1 and Paper 2 for each year
- Mark schemes and model answers
- Official Edexcel specification
- Pure Mathematics 1 and 2 textbooks (OCR extracted)

---

## Local development

**Prerequisites:** Python 3.11+, Docker Desktop

```bash
git clone https://github.com/minthant98/tutor-agent.git
cd tutor-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start services
docker compose up -d

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`

---

## Environment variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for LLM inference |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant Cloud API key |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | JWT signing secret |

---

## Agent nodes

| Agent | Responsibility |
|---|---|
| Intent | Classify student message into explain/quiz/hint/check_answer/off_topic |
| Retrieval | Semantic search over Qdrant knowledge base |
| Tutor | Generate syllabus-grounded explanations |
| Quiz | Generate past-paper style questions with mark schemes |
| Evaluator | Score student answers with partial credit |
| Hint | Provide scaffolded hints without revealing answers |
| Rules engine | Deterministic safety layer — overrides AI decisions |
| Adapt | Update mastery scores, decide next session action |

---

## Deployment

- **API:** Railway — FastAPI + PostgreSQL + Redis
- **Vector DB:** Qdrant Cloud (free tier)
- **Frontend:** Netlify

---

## Built by

Min Thant Tin — [github.com/minthant98](https://github.com/minthant98)
