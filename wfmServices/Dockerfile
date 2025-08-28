FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Build argument for service name
ARG SERVICE_NAME=api_gateway

# Create a startup script
RUN echo '#!/bin/bash\npython -m '"$SERVICE_NAME"'.main' > /app/start.sh && chmod +x /app/start.sh

# Default command (can be overridden)
CMD ["/app/start.sh"] 