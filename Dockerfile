FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    QDRANT_URL=local \
    QDRANT_STORAGE_PATH=/workspace/data/qdrant_storage \
    API_BASE_URL=http://localhost:7860 \
    IMAGE_BASE_URL=http://localhost:7860

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY data/ ./data/
COPY images/ ./images/
COPY frontend/ ./frontend/
COPY scripts/ ./scripts/
COPY .env.example .env

EXPOSE 7860

CMD ["sh", "-c", "gunicorn -w 2 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:${PORT:-7860} --timeout 300"]

