#!/bin/bash
# Start ChromaDB in background
chroma run --path /data/chroma --host 0.0.0.0 --port 8001 &

# Wait for ChromaDB to be ready
echo "Waiting for ChromaDB to start..."
sleep 5

# Start FastAPI
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
