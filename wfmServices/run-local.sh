#!/usr/bin/env bash
set -euo pipefail

# Simple local dev runner to build and run backend + frontend via Docker
# Requirements: docker, docker-compose (v2), and access to Mongo Atlas and Redis Cloud URIs

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)

# Load .env if present for local secrets
if [ -f "$SCRIPT_DIR/.env" ]; then
  echo "Loading environment from $SCRIPT_DIR/.env"
  # shellcheck disable=SC1090
  source "$SCRIPT_DIR/.env"
fi

: "${MONGO_URI:?Set MONGO_URI in wfmServices/.env for local run}"
: "${REDIS_URL:?Set REDIS_URL in wfmServices/.env for local run}"
JWT_SECRET=${JWT_SECRET:-local-dev-secret}
TAG=${TAG:-local}

# Build images
echo "Building backend service images..."
docker build -t wfm-api-gateway:$TAG --build-arg SERVICE_NAME=api_gateway "$SCRIPT_DIR"
docker build -t wfm-auth-service:$TAG --build-arg SERVICE_NAME=auth_service "$SCRIPT_DIR"
docker build -t wfm-config-service:$TAG --build-arg SERVICE_NAME=config_service "$SCRIPT_DIR"
docker build -t wfm-rules-service:$TAG --build-arg SERVICE_NAME=rules_service "$SCRIPT_DIR"
docker build -t wfm-scheduler-service:$TAG --build-arg SERVICE_NAME=scheduler_service "$SCRIPT_DIR"
docker build -t wfm-issue-service:$TAG --build-arg SERVICE_NAME=issue_service "$SCRIPT_DIR"
docker build -t wfm-analytics-service:$TAG --build-arg SERVICE_NAME=analytics_service "$SCRIPT_DIR"
docker build -t wfm-dashboard-service:$TAG --build-arg SERVICE_NAME=dashboard_service "$SCRIPT_DIR"

echo "Building frontend image..."
docker build -t wfm-frontend:$TAG -f "$ROOT_DIR/wfmApp/Dockerfile" "$ROOT_DIR/wfmApp"

# Create a compose file on the fly and run
cat > "$SCRIPT_DIR/docker-compose.local.yml" <<YAML
version: '3.8'
services:
  api-gateway:
    image: wfm-api-gateway:$TAG
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=$MONGO_URI
      - REDIS_URL=$REDIS_URL
      - DATABASE_NAME=wfm
      - JWT_SECRET_KEY=$JWT_SECRET
      - ENVIRONMENT=development
  auth-service:
    image: wfm-auth-service:$TAG
    ports:
      - "8001:8001"
    environment:
      - MONGODB_URL=$MONGO_URI
      - REDIS_URL=$REDIS_URL
      - DATABASE_NAME=wfm
      - JWT_SECRET_KEY=$JWT_SECRET
      - ENVIRONMENT=development
  config-service:
    image: wfm-config-service:$TAG
    ports:
      - "8002:8002"
    environment:
      - MONGODB_URL=$MONGO_URI
      - REDIS_URL=$REDIS_URL
      - DATABASE_NAME=wfm
      - JWT_SECRET_KEY=$JWT_SECRET
      - ENVIRONMENT=development
  rules-service:
    image: wfm-rules-service:$TAG
    ports:
      - "8003:8003"
    environment:
      - MONGODB_URL=$MONGO_URI
      - REDIS_URL=$REDIS_URL
      - DATABASE_NAME=wfm
      - JWT_SECRET_KEY=$JWT_SECRET
      - ENVIRONMENT=development
  scheduler-service:
    image: wfm-scheduler-service:$TAG
    ports:
      - "8004:8004"
    environment:
      - MONGODB_URL=$MONGO_URI
      - REDIS_URL=$REDIS_URL
      - DATABASE_NAME=wfm
      - JWT_SECRET_KEY=$JWT_SECRET
      - ENVIRONMENT=development
  issue-service:
    image: wfm-issue-service:$TAG
    ports:
      - "8005:8005"
    environment:
      - MONGODB_URL=$MONGO_URI
      - REDIS_URL=$REDIS_URL
      - DATABASE_NAME=wfm
      - JWT_SECRET_KEY=$JWT_SECRET
      - ENVIRONMENT=development
  analytics-service:
    image: wfm-analytics-service:$TAG
    ports:
      - "8006:8006"
    environment:
      - MONGODB_URL=$MONGO_URI
      - REDIS_URL=$REDIS_URL
      - DATABASE_NAME=wfm
      - JWT_SECRET_KEY=$JWT_SECRET
      - ENVIRONMENT=development
  dashboard-service:
    image: wfm-dashboard-service:$TAG
    ports:
      - "8007:8007"
    environment:
      - MONGODB_URL=$MONGO_URI
      - REDIS_URL=$REDIS_URL
      - DATABASE_NAME=wfm
      - JWT_SECRET_KEY=$JWT_SECRET
      - ENVIRONMENT=development
  wfmapp:
    image: wfm-frontend:$TAG
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8000
      - NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:8000
YAML

echo "Starting local stack..."
docker compose -f "$SCRIPT_DIR/docker-compose.local.yml" up -d

echo ""
echo "Frontend: http://localhost:3000"
echo "API Gateway: http://localhost:8000"
echo "To stop: docker compose -f $SCRIPT_DIR/docker-compose.local.yml down"
