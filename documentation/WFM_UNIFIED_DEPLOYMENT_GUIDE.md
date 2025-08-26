# WFM Unified Application Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the WFM (Workforce Management) unified application to both Azure cloud and local development environments. The unified application consists of four main components:

- **wfmApp**: Next.js frontend application with integrated BPMN modeler
- **wfmServices**: FastAPI backend microservices
- **intServices**: Integration layer for external systems
- **wfmProcess**: BPMN workflow engine backend

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     wfmApp      │    │   wfmServices   │    │   intServices   │    │   wfmProcess    │
│   (Frontend)    │────│   (Backend)     │────│  (Integration)  │────│   (Workflow)    │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8082    │    │   Port: 8090    │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         └───────────────────────┼───────────────────────┼───────────────────────┘
                                 │                       │
                    ┌─────────────────┐    ┌─────────────────┐
                    │   MongoDB       │    │   PostgreSQL    │
                    │   (Atlas)       │    │   (wfmProcess)  │
                    └─────────────────┘    └─────────────────┘
```

## Prerequisites

### For Azure Deployment
- Azure subscription with appropriate permissions
- Azure DevOps organization and project
- Docker Hub account
- Self-hosted Azure DevOps agent (macOS)

### For Local Development
- Docker and Docker Compose
- Node.js 18+
- Python 3.11+
- Git

## Environment Configuration

The application supports two environments with separate configuration files:

### Local Environment Files
- `wfmApp/.env.local` - Frontend local configuration
- `wfmServices/.env.local.example` - Backend services local template
- `intServices/.env.local.example` - Integration services local template
- `wfmProcess/backend/.env.local.example` - Process engine local template

### Cloud Environment Files
- `wfmApp/.env.cloud` - Frontend cloud configuration
- `wfmServices/.env.cloud.example` - Backend services cloud template
- `intServices/.env.cloud.example` - Integration services cloud template
- `wfmProcess/backend/.env.cloud.example` - Process engine cloud template

## Azure Cloud Deployment

### Step 1: Azure DevOps Setup

1. **Create Variable Group**
   ```bash
   # In Azure DevOps: Pipelines → Library → Variable Groups
   # Create group: wfm-deployment-vars
   ```

2. **Add Required Variables**
   ```
   DOCKER_HUB_PASSWORD: [Your Docker Hub Access Token]
   MONGODB_URL: mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB
   REDIS_URL: redis://default:kIdJfI3xoLxHiKFnCrkGBYffiDla8Hh@redis-15514.c56.east-us.azure.redns.redis-cloud.com:15514
   JWT_SECRET_KEY: [Generate a secure JWT secret key]
   POSTGRES_ADMIN_PASSWORD: [Secure password for PostgreSQL]
   ```

3. **Create Service Connection**
   - Go to Project Settings → Service Connections
   - Create Azure Resource Manager connection
   - Name it `wfm-azure-conn`

4. **Create Environment**
   - Go to Pipelines → Environments
   - Create environment `wfm-production`

### Step 2: Pipeline Deployment

1. **Create Pipeline**
   ```bash
   # Use the pipeline file: wfmInfra/azure-pipelines-unified.yml
   ```

2. **Run Pipeline**
   - The pipeline will automatically:
     - Build all Docker images
     - Push to Docker Hub
     - Create Azure resources
     - Deploy applications
     - Configure networking

### Step 3: Post-Deployment Configuration

1. **Update MongoDB Atlas IP Allowlist**
   - Add Azure Web App outbound IPs to MongoDB Atlas
   - IPs are displayed in pipeline output

2. **Update Redis Cloud IP Allowlist**
   - Add Azure Web App outbound IPs to Redis Cloud
   - Configure SSL/TLS settings

3. **Verify Deployment**
   - Frontend: https://wfmapp-webapp.azurewebsites.net
   - Backend: https://wfmservices-webapp.azurewebsites.net/health
   - Integration: https://intservices-webapp.azurewebsites.net/health
   - Process Engine: https://wfmprocess-webapp.azurewebsites.net/health

## Local Development Setup

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd wfmUnified
git checkout feature/load-save-intg
```

### Step 2: Environment Configuration

1. **Copy Environment Files**
   ```bash
   # wfmServices
   cp wfmServices/.env.local.example wfmServices/.env.local
   
   # intServices
   cp intServices/.env.local.example intServices/.env.local
   
   # wfmProcess
   cp wfmProcess/backend/.env.local.example wfmProcess/backend/.env.local
   ```

2. **Update Configuration**
   - Edit each `.env.local` file with your specific settings
   - Ensure database URLs and credentials are correct

### Step 3: Start Services

1. **Using Docker Compose (Recommended)**
   ```bash
   # Start all services including databases
   docker-compose -f docker-compose.unified.yml up -d
   
   # View logs
   docker-compose -f docker-compose.unified.yml logs -f
   
   # Stop services
   docker-compose -f docker-compose.unified.yml down
   ```

2. **Manual Service Startup**
   ```bash
   # Start PostgreSQL and Redis
   docker-compose -f docker-compose.unified.yml up -d wfm-postgres wfm-redis
   
   # Start wfmProcess
   cd wfmProcess/backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload
   
   # Start wfmServices (in separate terminal)
   cd wfmServices
   python -m uvicorn api_gateway.main:app --host 0.0.0.0 --port 8000 --reload
   
   # Start intServices (in separate terminal)
   cd intServices
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload
   
   # Start wfmApp (in separate terminal)
   cd wfmApp
   npm run dev
   ```

### Step 4: Verify Local Setup

1. **Check Service Health**
   ```bash
   # Frontend
   curl http://localhost:3000
   
   # Backend Services
   curl http://localhost:8000/health
   
   # Integration Services
   curl http://localhost:8082/health
   
   # Process Engine
   curl http://localhost:8090/health
   ```

2. **Access Applications**
   - Frontend: http://localhost:3000
   - API Gateway: http://localhost:8000/docs
   - Integration Services: http://localhost:8082/docs
   - Process Engine: http://localhost:8090/docs

## Database Setup

### PostgreSQL (wfmProcess)

The PostgreSQL database is automatically initialized with the required schema when using Docker Compose. The initialization script is located at `wfmProcess/docker/postgres/init.sql`.

**Manual Setup:**
```sql
-- Connect to PostgreSQL and run the initialization script
psql -h localhost -U wfmprocess -d wfmprocess -f wfmProcess/docker/postgres/init.sql
```

### MongoDB (wfmServices & intServices)

Uses MongoDB Atlas cloud instance. Ensure your IP is allowlisted in MongoDB Atlas.

## Integration Between Services

### wfmApp → wfmProcess Integration

The BPMN modeler components from wfmProcess frontend have been integrated into wfmApp:

1. **BPMN Modeler Route**: `/modelling`
2. **Components Location**: `wfmApp/components/modelling/`
3. **API Integration**: Uses `NEXT_PUBLIC_PROCESS_ENGINE_URL`

### Service Communication

- **wfmApp** → **wfmServices**: REST API calls for business logic
- **wfmApp** → **wfmProcess**: BPMN workflow operations
- **wfmServices** → **intServices**: External system integrations
- **wfmServices** → **wfmProcess**: Workflow triggers and status updates
- **intServices** → **wfmProcess**: External event processing

## Monitoring and Troubleshooting

### Logs

**Local Development:**
```bash
# Docker Compose logs
docker-compose -f docker-compose.unified.yml logs -f [service-name]

# Individual service logs
docker logs wfm_frontend
docker logs wfm_api_gateway
docker logs wfm_process_engine
```

**Azure Deployment:**
```bash
# Azure CLI
az webapp log tail --resource-group wfm-rg --name wfmapp-webapp
az webapp log tail --resource-group wfm-rg --name wfmservices-webapp
```

### Common Issues

1. **Database Connection Issues**
   - Verify IP allowlists for MongoDB Atlas and Redis Cloud
   - Check connection strings and credentials

2. **Service Communication Issues**
   - Verify environment variables for service URLs
   - Check network connectivity between services

3. **Docker Build Issues**
   - Ensure Docker is running
   - Check Dockerfile syntax and dependencies

## Security Considerations

1. **Environment Variables**
   - Never commit `.env` files to version control
   - Use secure, unique JWT secret keys
   - Rotate database credentials regularly

2. **Network Security**
   - All services communicate within Docker network locally
   - Azure services use HTTPS and VNet integration
   - Database connections use SSL/TLS

3. **Access Control**
   - Implement proper authentication and authorization
   - Use role-based access control (RBAC)
   - Monitor access logs

## Backup and Recovery

### Database Backups

**PostgreSQL:**
```bash
# Local backup
docker exec wfm_postgres pg_dump -U wfmprocess wfmprocess > backup.sql

# Azure backup (automatic with Azure Database for PostgreSQL)
```

**MongoDB:**
```bash
# MongoDB Atlas provides automatic backups
# Manual backup using mongodump
mongodump --uri="mongodb+srv://..." --out=backup/
```

## Performance Optimization

1. **Database Indexing**
   - PostgreSQL indexes are created automatically via init script
   - Monitor MongoDB Atlas performance insights

2. **Caching**
   - Redis is used for session and application caching
   - Configure appropriate TTL values

3. **Resource Scaling**
   - Azure: Scale App Service Plans based on load
   - Local: Adjust Docker resource limits

## Support and Maintenance

- **Documentation**: Keep this guide updated with changes
- **Version Control**: Use semantic versioning for releases
- **Testing**: Implement automated testing for all components
- **Monitoring**: Set up application performance monitoring

For technical support or questions:
- **Organization**: Tsaro Labs
- **Email**: admin@tsarolabs.com
- **Repository**: [Repository URL]
