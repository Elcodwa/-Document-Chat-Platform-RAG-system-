FROM python:3.12-slim

# System dependencies:
#  - libpq5: PostgreSQL client library (needed by psycopg)
#  - default-libmysqlclient-dev, build-essential: needed to build a couple
#    of small C extensions pulled in transitively
#  - curl: used by the container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Pre-download and cache the local embedding model at build time, not on
# the first file upload a user makes - keeps the app responsive from the
# very first request instead of stalling on a ~100MB download.
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5')"

COPY . .

RUN mkdir -p /app/storage

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Runs pending Alembic migrations, then starts the API. Using `exec` so
# uvicorn receives signals directly (clean shutdown on `docker compose down`).
CMD alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000
