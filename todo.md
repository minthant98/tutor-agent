# tasks/todo.md
# Tutor Agent — Project Backlog

---

## ✅ DONE

### T-01 — Redis Session Persistence
- Moved `_states` dict → Redis
- Files: `app/core/redis_client.py`, `app/core/session_store.py`
- Updated: `app/api/v1/endpoints/sessions.py`
- Verified: serializer round-trips all SessionState fields including `image_bytes`

---

## 🔲 TODO

### T-02 — Dockerize App Service
**Why:** Needed before any cloud deployment. Currently only infra (db, redis, chromadb) runs in Docker; FastAPI runs locally.
**Effort:** Medium
**Depends on:** Stable requirements.txt
**Steps:**
- [ ] Generate clean `requirements.txt` (runtime deps only, no build tools)
- [ ] Write `Dockerfile` (python:3.11-slim, arm64)
- [ ] Add `app` service to `docker-compose.yml`
- [ ] Verify all 4 containers healthy with `docker compose ps`
- [ ] Smoke test all endpoints inside Docker

---

### T-03 — Environment Config Cleanup
**Why:** `.env` has `localhost` URLs that break inside Docker. Need two configs.
**Effort:** Low
**Steps:**
- [ ] Create `.env.local` (localhost URLs, for uvicorn dev)
- [ ] Create `.env.docker` (Docker service name URLs)
- [ ] Add `Makefile` targets: `make dev` and `make docker`
- [ ] Add `.env*.local` to `.gitignore`

---

### T-04 — Alembic Migrations
**Why:** Schema changes need versioned migrations, not `create_all()` on startup.
**Effort:** Medium
**Steps:**
- [ ] Confirm `alembic` is initialized (`alembic/`)
- [ ] Write baseline migration from current models
- [ ] Add migration step to Docker startup or README
- [ ] Document: never use `create_all()` in production

---

### T-05 — Subscription Tier Enforcement Audit
**Why:** Free tier blocks quiz/exam_practice in `start_session` but no checks in `send_message`. A user could bypass by calling `/message` directly.
**Effort:** Low
**Steps:**
- [ ] Audit all endpoints for tier checks
- [ ] Add tier validation to `session_service.process_message` or as a dependency
- [ ] Write test cases for each tier boundary

---

### T-06 — Rate Limiting
**Why:** No rate limiting on `/message` — a single user could hammer the Groq API.
**Effort:** Medium
**Depends on:** Redis (T-01 ✅ — Redis is now available)
**Steps:**
- [ ] Add `slowapi` or custom Redis counter middleware
- [ ] Limits: free=20 msg/day, pro=unlimited (or 500/day)
- [ ] Return 429 with `Retry-After` header

---

### T-07 — Production Deployment
**Why:** Portfolio/sale requires a live URL.
**Effort:** High
**Depends on:** T-02, T-03, T-04
**Suggested stack:** Railway or Render (free tier friendly, supports Docker Compose)
**Steps:**
- [ ] Choose hosting platform
- [ ] Set production env vars (secrets manager or platform dashboard)
- [ ] Set up CI/CD (GitHub Actions → auto-deploy on push to main)
- [ ] Add health check endpoint (`GET /health`)
- [ ] Configure CORS for production frontend domain

---

### T-08 — Frontend Polish
**Why:** Portfolio buyers will judge the UI first.
**Effort:** Medium
**Steps:**
- [ ] Add session history sidebar (list past sessions)
- [ ] Add progress dashboard (mastery scores per topic)
- [ ] Mobile responsive layout
- [ ] Loading states for agent responses (streaming or spinner)

---

## 📊 Priority Order (Portfolio/Sale focus)

1. T-05 — Security fix (quick win, looks bad in a demo if bypassable)
2. T-02 + T-03 — Dockerize (required for deployment)
3. T-04 — Migrations (required for production credibility)
4. T-06 — Rate limiting (required before any public URL)
5. T-07 — Deploy (the goal)
6. T-08 — Frontend polish (conversion/demo quality)