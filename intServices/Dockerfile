# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata first for better layer caching
COPY pyproject.toml setup.cfg setup.py README.md /app/

# Install dependencies
RUN pip install --upgrade pip && pip install -e .

# Copy source
COPY app /app/app
COPY .env.example /app/.env.example

# Non-root user
RUN useradd -m appuser
USER appuser

EXPOSE 8082

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]
