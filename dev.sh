#!/bin/bash
set -e

echo "Starting local dev environment..."

# Start Redis only (DB is on Supabase)
docker compose up -d redis
export REDIS_URL="redis://localhost:6379"

# Activate virtual environment
source venv/bin/activate

# Run migrations
echo "Running migrations..."
alembic upgrade head

# Start Next.js dev server in background on port 3000
echo "Starting Next.js frontend..."
(cd web && npm run dev > /tmp/nextjs.log 2>&1) &
FRONTEND_PID=$!

# Trap Ctrl+C to clean up
trap "echo 'Shutting down...'; kill $FRONTEND_PID 2>/dev/null; docker compose stop db redis" INT TERM

# Give Next.js a moment to start
sleep 2

echo ""
echo "  API:      http://localhost:8000"
echo "  Docs:     http://localhost:8000/docs"
echo "  Frontend: http://localhost:3000"
echo ""
uvicorn app.main:app --reload --port 8000

# Cleanup on exit
kill $FRONTEND_PID 2>/dev/null
docker compose stop db redis
