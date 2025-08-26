# WFM Unified - Local Development Setup

## Quick Start Guide

This guide helps you set up the WFM Unified application for local development in under 10 minutes.

## Prerequisites

- Docker Desktop installed and running
- Node.js 18+ installed
- Git installed
- 8GB+ RAM available

## One-Command Setup

```bash
# Clone and start everything
git clone <repository-url> && cd wfmUnified
git checkout feature/load-save-intg
docker-compose -f docker-compose.unified.yml up -d
```

## Service URLs

Once started, access these URLs:

| Service | URL | Purpose |
|---------|-----|---------|
| **wfmApp** | http://localhost:3000 | Main frontend application |
| **API Gateway** | http://localhost:8000/docs | Backend API documentation |
| **Integration Services** | http://localhost:8082/docs | Integration API docs |
| **Process Engine** | http://localhost:8090/docs | Workflow engine API docs |
| **PostgreSQL** | localhost:5432 | Process engine database |
| **Redis** | localhost:6379 | Caching layer |

## Environment Configuration

### Required Environment Files

Copy these example files to create your local configuration:

```bash
# Backend Services
cp wfmServices/.env.local.example wfmServices/.env.local

# Integration Services  
cp intServices/.env.local.example intServices/.env.local

# Process Engine
cp wfmProcess/backend/.env.local.example wfmProcess/backend/.env.local
```

### Key Configuration Points

1. **Database URLs**: Pre-configured for local Docker containers
2. **Service URLs**: All point to localhost with appropriate ports
3. **MongoDB**: Uses cloud Atlas instance (no local setup needed)
4. **Redis**: Uses cloud Redis instance (local Redis also available)

## Development Workflow

### Starting Services

```bash
# Start all services
docker-compose -f docker-compose.unified.yml up -d

# Start specific services only
docker-compose -f docker-compose.unified.yml up -d wfm-postgres wfm-redis wfm-process

# View logs
docker-compose -f docker-compose.unified.yml logs -f
```

### Stopping Services

```bash
# Stop all services
docker-compose -f docker-compose.unified.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.unified.yml down -v
```

### Development Mode

For active development, you can run services individually:

```bash
# 1. Start databases only
docker-compose -f docker-compose.unified.yml up -d wfm-postgres wfm-redis

# 2. Start wfmApp in dev mode (hot reload)
cd wfmApp
npm install
npm run dev

# 3. Start wfmProcess in dev mode (in new terminal)
cd wfmProcess/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload

# 4. Start other services as needed
```

## Health Checks

Verify all services are running:

```bash
# Quick health check script
curl -s http://localhost:3000 > /dev/null && echo "✅ wfmApp: OK" || echo "❌ wfmApp: Failed"
curl -s http://localhost:8000/health > /dev/null && echo "✅ wfmServices: OK" || echo "❌ wfmServices: Failed"  
curl -s http://localhost:8082/health > /dev/null && echo "✅ intServices: OK" || echo "❌ intServices: Failed"
curl -s http://localhost:8090/health > /dev/null && echo "✅ wfmProcess: OK" || echo "❌ wfmProcess: Failed"
```

## Database Access

### PostgreSQL (Process Engine)

```bash
# Connect to PostgreSQL
docker exec -it wfm_postgres psql -U wfmprocess -d wfmprocess

# View tables
\dt workflow.*
\dt process.*
\dt audit.*
```

### Redis (Caching)

```bash
# Connect to Redis
docker exec -it wfm_redis redis-cli

# View keys
KEYS *
```

## Common Development Tasks

### Adding New BPMN Components

1. Create components in `wfmApp/components/modelling/`
2. Import BPMN.js dependencies in `wfmApp/package.json`
3. Add routes in `wfmApp/app/modelling/`

### Testing Workflow Integration

1. Access BPMN modeler: http://localhost:3000/modelling
2. Create a workflow and save
3. Check PostgreSQL for stored workflow
4. Test execution via Process Engine API

### Debugging Services

```bash
# View service logs
docker-compose -f docker-compose.unified.yml logs -f [service-name]

# Access service container
docker exec -it [container-name] /bin/bash

# Check service status
docker-compose -f docker-compose.unified.yml ps
```

## IDE Configuration

### VS Code Setup

Recommended extensions:
- Docker
- Python
- TypeScript and JavaScript
- PostgreSQL
- REST Client

### Environment Variables

Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./wfmProcess/backend/.venv/bin/python",
  "typescript.preferences.importModuleSpecifier": "relative"
}
```

## Troubleshooting

### Port Conflicts

If ports are already in use:

```bash
# Check what's using ports
lsof -i :3000
lsof -i :8000
lsof -i :8090

# Kill processes if needed
kill -9 <PID>
```

### Docker Issues

```bash
# Clean Docker system
docker system prune -a

# Rebuild containers
docker-compose -f docker-compose.unified.yml build --no-cache

# Reset volumes
docker-compose -f docker-compose.unified.yml down -v
docker volume prune
```

### Database Connection Issues

1. Verify PostgreSQL is running: `docker ps | grep postgres`
2. Check connection string in `.env.local` files
3. Ensure database is initialized: `docker logs wfm_postgres`

### Service Communication Issues

1. Check Docker network: `docker network ls`
2. Verify service names in docker-compose.yml
3. Test internal connectivity: `docker exec wfm_frontend curl http://api-gateway:8000/health`

## Performance Tips

### Resource Allocation

```bash
# Check Docker resource usage
docker stats

# Adjust Docker Desktop resources:
# Settings → Resources → Advanced
# Recommended: 4GB RAM, 2 CPUs minimum
```

### Development Optimization

1. **Use .dockerignore**: Exclude node_modules, .git, etc.
2. **Layer Caching**: Order Dockerfile commands for better caching
3. **Volume Mounts**: Use bind mounts for active development

## Testing

### Unit Tests

```bash
# Frontend tests
cd wfmApp
npm test

# Backend tests  
cd wfmProcess/backend
pytest

# Integration tests
cd intServices
python -m pytest tests/
```

### API Testing

Use the provided REST client files or Postman collections:

```bash
# Test API endpoints
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8090/workflows
```

## Git Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch
- `feature/load-save-intg`: Current feature branch

### Commit Guidelines

```bash
# Feature development
git checkout feature/load-save-intg
git add .
git commit -m "feat: add BPMN modeler integration"
git push origin feature/load-save-intg
```

## Next Steps

1. **Explore the Application**: Navigate through http://localhost:3000
2. **Create a Workflow**: Use the BPMN modeler to design processes
3. **Test Integration**: Verify data flows between services
4. **Review APIs**: Check out the Swagger documentation
5. **Customize**: Modify components and see changes in real-time

## Support

For development questions:
- Check logs first: `docker-compose logs -f`
- Review this documentation
- Check the main deployment guide
- Contact: admin@tsarolabs.com
