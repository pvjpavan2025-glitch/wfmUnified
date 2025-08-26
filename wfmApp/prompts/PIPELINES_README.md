Azure DevOps CI/CD for WFM

Overview
- wfmApp/azure-pipelines.yml builds and deploys the Next.js frontend container to Azure Web App for Containers.
- wfmServices/azure-pipelines.yml builds and deploys all backend microservices as containers to Azure Web App for Containers (multi-container using docker-compose).

Required Azure DevOps setup
1) Service connections
- azureSubscription: Azure Resource Manager connection with access to the target resource group and Web Apps
- acrServiceConnection: Docker Registry service connection pointing to your Azure Container Registry

2) Pipeline variables (set as variables or variable group; secrets as secret variables)
- acrLoginServer: myregistry.azurecr.io
- mongoUri: <MongoDB Atlas connection string>
- redisUrl: <Redis Cloud connection string>
- jwtSecret: <random secret>
- ACR_USER, ACR_PASSWORD: Only needed if Web Apps do not have ACR pull permissions (use managed identity or webapp access to ACR where possible)
- webAppNameFrontend: <Frontend app name>
- webAppNameBackend: <Backend app name>

3) DNS/URLs
- backendUrl (for frontend): e.g., https://<backend>.azurewebsites.net

Notes
- For single-unit deployment, use the backend pipeline to deploy all backend services together; frontend is independent but must point to backendUrl.
- Mongo and Redis: Prefer managed services (Atlas/Redis Cloud/Azure equivalents) for production. Containers are fine for local/dev.
