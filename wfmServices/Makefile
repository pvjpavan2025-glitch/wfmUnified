# WFM Microservices Makefile

.PHONY: help install start stop clean test lint format docker-build docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install Python dependencies"
	@echo "  start        - Start all services locally"
	@echo "  stop         - Stop all services"
	@echo "  clean        - Clean up temporary files"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up    - Start services with Docker Compose"
	@echo "  docker-down  - Stop services with Docker Compose"

# Install dependencies
install:
	pip install -r requirements.txt

# Start all services locally
start:
	@echo "Starting WFM services..."
	@echo "Make sure MongoDB and Redis are running first!"
	@echo "Starting API Gateway..."
	python -m api_gateway.main &
	@echo "Starting Auth Service..."
	python -m auth_service.main &
	@echo "Starting Config Service..."
	python -m config_service.main &
	@echo "Starting Rules Service..."
	python -m rules_service.main &
	@echo "Starting Scheduler Service..."
	python -m scheduler_service.main &
	@echo "Starting Issue Service..."
	python -m issue_service.main &
	@echo "Starting Analytics Service..."
	python -m analytics_service.main &
	@echo "All services started!"

# Stop all services
stop:
	@echo "Stopping all services..."
	pkill -f "python -m.*main" || true
	@echo "Services stopped!"

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf logs/*

# Run tests
test:
	pytest tests/ -v

# Run linting
lint:
	flake8 .
	mypy .

# Format code
format:
	black .
	isort .

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Development helpers
dev-setup: install
	@echo "Setting up development environment..."
	cp env.example .env
	@echo "Please edit .env file with your configuration"

dev-start: dev-setup
	@echo "Starting development environment..."
	docker-compose up -d mongodb redis
	@echo "Waiting for databases to be ready..."
	sleep 10
	@echo "Starting services..."
	make start

# Database helpers
db-init:
	@echo "Initializing database..."
	python scripts/init_database.py

db-reset:
	@echo "Resetting database..."
	docker-compose down -v
	docker-compose up -d mongodb redis
	sleep 10
	make db-init

# Health checks
health-check:
	@echo "Checking service health..."
	curl -f http://localhost:8000/health || echo "API Gateway not responding"
	curl -f http://localhost:8001/health || echo "Auth Service not responding"
	curl -f http://localhost:8002/health || echo "Config Service not responding"
	curl -f http://localhost:8003/health || echo "Rules Service not responding"
	curl -f http://localhost:8004/health || echo "Scheduler Service not responding"
	curl -f http://localhost:8005/health || echo "Issue Service not responding"
	curl -f http://localhost:8006/health || echo "Analytics Service not responding" 