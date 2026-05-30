FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install CPU-only torch first (avoids pulling CUDA - saves ~1.5GB)
RUN pip install --no-cache-dir \
    torch==2.3.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download ML models into the image (avoids cold-start HuggingFace downloads)
ENV HF_HOME=/app/.hf_cache
RUN python -c "\
from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('all-MiniLM-L6-v2'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2'); \
print('Models cached.')"

# Copy application code
COPY . .

ENV PYTHONPATH=/app
ENV HF_HOME=/app/.hf_cache

EXPOSE 8080

CMD ["./start.sh"]
