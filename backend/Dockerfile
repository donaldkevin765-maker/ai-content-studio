FROM python:3.12-slim

WORKDIR /app

# Install system deps: ffmpeg per moviepy + psycopg2 per PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (caching)
COPY pyproject.toml ./
COPY migrations/ migrations/

# Install Python deps (con cache mount per velocizzare rebuild)
RUN pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY api/ api/
COPY app/ app/
COPY assets/ assets/
COPY scripts/ scripts/

# Create output dirs
RUN mkdir -p /app/output/videos /app/output/audio /app/output/images

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
