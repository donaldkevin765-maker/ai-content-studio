FROM python:3.12-slim

WORKDIR /app

# Install system deps (ffmpeg per moviepy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY pyproject.toml .
COPY api/ api/
COPY app/ app/
COPY assets/ assets/

# Install python deps
RUN pip install --no-cache-dir -e .

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
