#!/bin/bash
# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start ChromaDB in background
echo "Starting ChromaDB..."
chroma run --path /data/chroma --host 0.0.0.0 --port 8001 &

# Wait for ChromaDB to be ready
echo "Waiting for ChromaDB to start..."
sleep 5

# Start FastAPI
echo "Starting FastAPI..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
