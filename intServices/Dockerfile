FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY pyproject.toml setup.py setup.cfg ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY app/ ./app/

# Create non-root user
RUN useradd --create-home --shell /bin/bash intservices
RUN chown -R intservices:intservices /app
USER intservices

# Expose port
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8082/healthz')" || exit 1

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082", "--reload"]
