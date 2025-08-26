# 🚀 WFM Unified Azure Deployment Guide

## Overview
This guide provides complete instructions for deploying the WFM Unified application to Azure using Azure DevOps Pipelines.

## 📋 Prerequisites

### Azure Resources Required
- **Azure Subscription**: `536f83d4-d66d-4c2b-86f9-93e05ccf646d`
- **Azure DevOps Organization**: `https://dev.azure.com/tsaro/WFM`
- **Docker Hub Account**: `pavantsarolabs`

### External Services
- **MongoDB Atlas**: Cloud MongoDB instance
- **Redis Cloud**: Cloud Redis instance
- **Self-hosted Agent**: `pavans-MacBook-Pro`

## 🔧 Setup Instructions

### Step 1: Create Variable Group in Azure DevOps

1. Navigate to **Pipelines** → **Library**
2. Click **+ Variable group**
3. Create variable group: `wfm-deployment-vars`
4. Add the following variables (mark all as **Secret**):

```bash
# Docker Hub
DOCKER_HUB_PASSWORD: [Your Docker Hub Access Token]

# Database Connections
MONGODB_URL: mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB
REDIS_URL: redis://default:kIdJfI3xoLxHiKFnCrkGBYffiDla8Hh@redis-15514.c56.east-us.azure.redns.redis-cloud.com:15514

# Security
JWT_SECRET_KEY: [Generate with: openssl rand -base64 32]

# Azure PostgreSQL (will be created by pipeline)
POSTGRES_PASSWORD: [Strong password for PostgreSQL admin]
```

### Step 2: Create Azure Service Connection

1. Go to **Project Settings** → **Service Connections**
2. Click **New service connection** → **Azure Resource Manager**
3. Select **Service principal (automatic)**
4. Choose subscription: `536f83d4-d66d-4c2b-86f9-93e05ccf646d`
5. Name: `wfm-azure-conn`
6. Check **Grant access permission to all pipelines**

### Step 3: Create Environment

1. Go to **Pipelines** → **Environments**
2. Click **New environment**
3. Name: `wfm-production`
4. Resource: **None**

### Step 4: Run the Pipeline

1. Go to **Pipelines** → **New Pipeline**
2. Choose **Azure Repos Git**
3. Select **wfmUnified** repository
4. Choose **Existing Azure Pipelines YAML file**
5. Select: `/wfmInfra/azure-pipelines-unified.yml`
6. Choose source branch (main, develop, or feature/azurePipelines)
7. Click **Run**

## 🏗️ Architecture Overview

### Services Deployed
1. **wfm-app**: Next.js frontend application
2. **wfm-services**: Main backend API gateway
3. **wfm-int-services**: Integration services
4. **wfm-process**: BPMN workflow engine

### Azure Resources Created
- **Resource Group**: `wfm-unified-rg`
- **App Service Plan**: `wfm-unified-plan` (B2 SKU)
- **Web Apps**: 4 containerized applications
- **API Management**: `wfm-unified-apim`
- **PostgreSQL**: `wfm-postgres-server`
- **Virtual Network**: `wfm-unified-vnet`

### External Dependencies
- **MongoDB Atlas**: Document database
- **Redis Cloud**: Caching and session storage
- **Docker Hub**: Container registry

## 🌐 Deployment URLs

After successful deployment, your applications will be available at:

- **Frontend**: `https://wfm-app-webapp.azurewebsites.net`
- **Main API**: `https://wfm-services-webapp.azurewebsites.net`
- **Integration API**: `https://wfm-int-services-webapp.azurewebsites.net`
- **Process Engine**: `https://wfm-process-webapp.azurewebsites.net`
- **API Management**: `https://wfm-unified-apim.azure-api.net`

## 📡 API Management Endpoints

### WFM Services API (`/api/v1`)
```bash
# Authentication
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/verify

# Dashboard
GET  /api/v1/dashboard/metrics
GET  /api/v1/dashboard/recent-jobs

# Jobs Management
GET    /api/v1/jobs
POST   /api/v1/jobs
GET    /api/v1/jobs/{id}
PUT    /api/v1/jobs/{id}
DELETE /api/v1/jobs/{id}

# Technicians
GET    /api/v1/technicians
POST   /api/v1/technicians
GET    /api/v1/technicians/{id}
PUT    /api/v1/technicians/{id}

# Scheduling
GET  /api/v1/schedule
POST /api/v1/schedule/assign
PUT  /api/v1/schedule/{id}

# Analytics
GET /api/v1/analytics/performance
GET /api/v1/analytics/utilization
GET /api/v1/analytics/trends
```

### WFM Process API (`/process/v1`)
```bash
# Workflow Management
GET    /process/v1/workflows
POST   /process/v1/workflows
GET    /process/v1/workflows/{id}
PUT    /process/v1/workflows/{id}
DELETE /process/v1/workflows/{id}

# Process Execution
POST /process/v1/workflows/execute
GET  /process/v1/instances
GET  /process/v1/instances/{id}
POST /process/v1/instances/{id}/complete

# Process Monitoring
GET /process/v1/health
GET /process/v1/metrics
```

## 📝 Sample API Payloads

### Authentication
```json
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "password123",
  "tenant_id": "default"
}

Response:
{
  "user": {
    "id": "1",
    "username": "admin",
    "email": "admin@example.com",
    "roles": ["Admin"]
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Create Job
```json
POST /api/v1/jobs
{
  "job_number": "JOB-2024-001",
  "description": "HVAC Maintenance",
  "location": "Building A, Floor 3",
  "priority": "high",
  "estimated_hours": 4,
  "due_date": "2024-01-15T10:00:00Z",
  "technician_id": "tech-001"
}
```

### Execute Workflow
```json
POST /process/v1/workflows/execute
{
  "workflow_id": "maintenance-workflow",
  "variables": {
    "job_id": "JOB-2024-001",
    "priority": "high",
    "technician_id": "tech-001"
  }
}
```

## 🔍 Monitoring and Troubleshooting

### Health Check Endpoints
- Frontend: `https://wfm-app-webapp.azurewebsites.net/`
- Services: `https://wfm-services-webapp.azurewebsites.net/health`
- Integration: `https://wfm-int-services-webapp.azurewebsites.net/health`
- Process: `https://wfm-process-webapp.azurewebsites.net/health`

### Common Issues

#### 1. Database Connection Failures
- **Cause**: Web App outbound IPs not allowlisted
- **Solution**: Add Web App outbound IPs to MongoDB Atlas and Redis Cloud allowlists
- **Get IPs**: Check pipeline output or Azure Portal → Web App → Properties

#### 2. API Management Not Ready
- **Cause**: APIM takes 30-45 minutes to provision
- **Solution**: Wait for provisioning to complete, check Azure Portal

#### 3. Container Startup Issues
- **Cause**: Environment variables missing or incorrect
- **Solution**: Check Web App → Configuration → Application Settings

### Logs Access
```bash
# View container logs
az webapp log tail --resource-group wfm-unified-rg --name wfm-services-webapp

# Download logs
az webapp log download --resource-group wfm-unified-rg --name wfm-services-webapp
```

## 🔄 Pipeline Stages

### 1. Build Stage (15-20 minutes)
- Checkout source code from specified branch
- Setup Docker Buildx for multi-platform builds
- Build Docker images for all 4 services
- Push images to Docker Hub with build ID tags

### 2. Deploy Stage (20-30 minutes)
- Create Azure resource group
- Setup PostgreSQL database
- Create virtual network and subnets
- Deploy Web Apps with container images
- Configure environment variables
- Create API Management service (async)

### 3. Post-Deployment (5-10 minutes)
- Health check all services
- Verify API endpoints
- Display deployment URLs and information

## 🚀 Post-Deployment Steps

### 1. Configure IP Allowlists
Add the Web App outbound IPs (shown in pipeline output) to:
- MongoDB Atlas Network Access
- Redis Cloud Security settings

### 2. Test Application
1. Access frontend URL
2. Login with test credentials
3. Verify dashboard loads
4. Test BPMN modeler functionality

### 3. Configure Custom Domains (Optional)
- Setup custom domains in Azure DNS
- Configure SSL certificates
- Update API Management custom domains

### 4. Setup Monitoring
- Configure Application Insights
- Setup alerts for critical metrics
- Enable diagnostic logging

## 📊 Cost Optimization

### Current Configuration
- **App Service Plan**: B2 (shared across all apps)
- **API Management**: Developer tier
- **PostgreSQL**: Burstable B1ms
- **Estimated Monthly Cost**: ~$150-200

### Cost Reduction Options
1. Use F1 (Free) tier for development
2. Scale down PostgreSQL to B1ms
3. Use Consumption tier for API Management
4. Implement auto-scaling policies

## 🔐 Security Considerations

### Implemented Security
- HTTPS enforced on all endpoints
- JWT token authentication
- Environment variables stored as secrets
- Network isolation with VNet
- Database SSL connections required

### Additional Recommendations
- Enable Azure AD authentication
- Implement API rate limiting
- Setup Web Application Firewall
- Enable audit logging
- Regular security updates

## 📞 Support and Maintenance

### Regular Tasks
- Monitor application health
- Update container images
- Review security patches
- Backup database regularly
- Monitor costs and usage

### Troubleshooting Contacts
- **Azure Support**: Azure Portal → Help + Support
- **MongoDB Atlas**: Cloud support portal
- **Redis Cloud**: Support tickets
- **Application Issues**: Check container logs and health endpoints

---

**Deployment Complete!** 🎉

Your WFM Unified application is now running in Azure with full API Management, cloud databases, and monitoring capabilities.
