#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Ascend API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
