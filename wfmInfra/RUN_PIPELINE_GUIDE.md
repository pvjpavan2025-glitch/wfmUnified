# 🚀 RUN WFM UNIFIED PIPELINE - Quick Start Guide

## ⚡ 5-Minute Setup

### Step 1: Azure DevOps Setup
1. Navigate to: `https://dev.azure.com/tsaro/WFM`
2. Go to **Pipelines** → **Library** → **+ Variable group**
3. Create: `wfm-deployment-vars` with these variables (mark as **Secret**):

```bash
DOCKER_HUB_PASSWORD=<your-docker-hub-token>
MONGODB_URL=mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB
REDIS_URL=redis://default:kIdJfI3xoLxHiKFnCrkGBYffiDla8Hh@redis-15514.c56.east-us.azure.redns.redis-cloud.com:15514
JWT_SECRET_KEY=<generate-with-openssl-rand-base64-32>
POSTGRES_PASSWORD=<strong-password-for-azure-postgres>
```

### Step 2: Service Connection
1. **Project Settings** → **Service Connections** → **New service connection**
2. **Azure Resource Manager** → **Service principal (automatic)**
3. Subscription: `536f83d4-d66d-4c2b-86f9-93e05ccf646d`
4. Name: `wfm-azure-conn`
5. ✅ **Grant access permission to all pipelines**

### Step 3: Environment
1. **Pipelines** → **Environments** → **New environment**
2. Name: `wfm-production`
3. Resource: **None**

### Step 4: Run Pipeline
1. **Pipelines** → **New Pipeline** → **Azure Repos Git**
2. Select: **wfmUnified** repository
3. **Existing Azure Pipelines YAML file**: `/wfmInfra/azure-pipelines-unified.yml`
4. Choose branch: `main`, `develop`, or `feature/azurePipelines`
5. **Run** 🚀

## 📊 What Happens Next

### Build Stage (15-20 min)
- ✅ Builds 4 Docker images (wfm-app, wfm-services, wfm-int-services, wfm-process)
- ✅ Pushes to Docker Hub: `pavantsarolabs/*`

### Deploy Stage (20-30 min)
- ✅ Creates resource group: `wfm-unified-rg`
- ✅ Sets up Azure PostgreSQL database
- ✅ Deploys 4 Web Apps with containers
- ✅ Creates API Management service
- ✅ Configures all environment variables

### Verification (5-10 min)
- ✅ Health checks all services
- ✅ Provides deployment URLs

## 🌐 Your Applications

After deployment:
- **Frontend**: `https://wfm-app-webapp.azurewebsites.net`
- **API Gateway**: `https://wfm-services-webapp.azurewebsites.net`
- **Integration**: `https://wfm-int-services-webapp.azurewebsites.net`
- **Process Engine**: `https://wfm-process-webapp.azurewebsites.net`
- **API Management**: `https://wfm-unified-apim.azure-api.net`

## 🔧 Post-Deployment Actions

### 1. Add IP Allowlists
Pipeline will show Web App outbound IPs. Add them to:
- **MongoDB Atlas**: Network Access → IP Access List
- **Redis Cloud**: Security → IP Access Control

### 2. Test Login
```bash
curl -X POST https://wfm-services-webapp.azurewebsites.net/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123","tenant_id":"default"}'
```

### 3. Verify Frontend
Visit: `https://wfm-app-webapp.azurewebsites.net`

## 🚨 Troubleshooting

### Pipeline Fails at Build
- Check Docker Hub credentials in variable group
- Verify self-hosted agent is online

### Services Won't Start
- Check outbound IPs are allowlisted in MongoDB/Redis
- Verify environment variables in Web App settings

### API Management Not Ready
- APIM takes 30-45 minutes to provision
- Check Azure Portal for status

## 📱 Monitor Progress

Watch pipeline in real-time:
- Build logs show Docker image creation
- Deploy logs show Azure resource creation
- Health checks confirm service availability

## ✅ Success Indicators

You'll know it worked when:
- ✅ All 4 Docker images pushed to Hub
- ✅ All 4 Web Apps show "Running" status
- ✅ Health endpoints return HTTP 200
- ✅ Frontend loads without errors

**Total Time: ~45-60 minutes** ⏱️

Ready to deploy? Just follow the 4 steps above! 🎉
