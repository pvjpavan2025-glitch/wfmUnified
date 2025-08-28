# Workforce Management (WFM) Microservices

A comprehensive microservices-based Workforce Management system built with Python, following SOLID principles and designed for multi-tenant scalability.

## Architecture Overview

The WFM system consists of the following microservices:

- **API Gateway**: Central entry point for all external requests
- **Authentication & Authorization Service**: Handles user authentication, JWT tokens, and role-based access control
- **Configuration Service**: Manages system configurations and tenant-specific settings
- **Rules Engine Service**: Core service for rule processing, decomposition, and process recognition
- **Intelligent Scheduler Service**: Handles task scheduling, job management, and process execution
- **Issue Handler Service**: Manages issues, dependencies, and SLA tracking
- **Analytics & Reports Service**: Provides reporting and analytics capabilities

## Technology Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Databases**: MongoDB (primary), Redis (caching/queues)
- **Message Queue**: Redis Pub/Sub
- **Authentication**: JWT tokens
- **API Documentation**: OpenAPI/Swagger
- **Logging**: Structured logging with correlation IDs
- **Monitoring**: Prometheus metrics

## Quick Start

1. **Prerequisites**:
   - Docker and Docker Compose
   - Python 3.11+
   - MongoDB (running in Docker)
   - Redis (running in Docker)

2. **Environment Setup**:
   ```bash
   # Clone the repository
   git clone <repository-url>
   cd wfmv4
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Start Services**:
   ```bash
   # Start all services
   docker-compose up -d
   
   # Or start individual services
   python -m auth_service.main
   python -m config_service.main
   python -m rules_service.main
   python -m scheduler_service.main
   python -m issue_service.main
   python -m analytics_service.main
   python -m api_gateway.main
   ```

4. **Access Services**:
   - API Gateway: http://localhost:8000
   - Swagger Documentation: http://localhost:8000/docs
   - Authentication Service: http://localhost:8001
   - Configuration Service: http://localhost:8002
   - Rules Engine Service: http://localhost:8003
   - Scheduler Service: http://localhost:8004
   - Issue Handler Service: http://localhost:8005
   - Analytics Service: http://localhost:8006

## Multi-Tenant Architecture

All services are designed to be multi-tenant with the following features:
- Tenant isolation using `tenant_id` in all database operations
- Role-based access control (RBAC)
- Tenant-specific configurations
- Data segregation at the application level

## Development Guidelines

- Follow SOLID principles
- Use dependency injection
- Implement comprehensive logging with correlation IDs
- Write unit tests for all business logic
- Use type hints throughout the codebase
- Follow RESTful API design principles

## Next Steps

1. Set up CI/CD pipeline
2. Implement comprehensive monitoring and alerting
3. Add performance testing
4. Create deployment scripts for different environments
5. Implement backup and disaster recovery procedures
