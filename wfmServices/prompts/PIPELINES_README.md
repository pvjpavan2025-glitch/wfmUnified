Azure DevOps CI/CD for WFM Services

Overview
- wfmServices/azure-pipelines.yml builds and pushes images for all backend microservices to ACR and deploys them to Azure Web App for Containers (multi-container) using docker-compose.
- wfmApp/azure-pipelines.yml builds, pushes, and deploys the Next.js frontend container to its own Azure Web App for Containers.

Required Azure DevOps setup
1) Service connections
- azureSubscription: Azure Resource Manager connection with access to the target resource group and Web Apps
- acrServiceConnection: Docker Registry service connection pointing to your Azure Container Registry

2) Pipeline variables (set as variables/variable group; secrets as secret variables)
- acrLoginServer: myregistry.azurecr.io
- mongoUri: <MongoDB Atlas connection string>
- redisUrl: <Redis Cloud connection string>
- jwtSecret: <random secret>
- ACR_USER, ACR_PASSWORD: Only needed if Web App does not have ACR pull permissions (prefer enabling ACR access for the Web App)
- webAppNameBackend: <Backend app name>
- For frontend pipeline also set: webAppNameFrontend and backendUrl (e.g., https://<backend>.azurewebsites.net)

3) Initial Web App configuration
- Create 2 Linux Web Apps for Containers (one for backend, one for frontend). Assign them access to pull from ACR (via Access control or DOCKER_REGISTRY_SERVER_* app settings).

Deploy as a single unit
- You can run only the backend pipeline to deploy the backend stack; the frontend pipeline can follow or be triggered on changes to wfmApp. Ensure frontend NEXT_PUBLIC_* variables point to backendUrl.

Local development
- Use wfmServices/run-local.sh with a wfmServices/.env file containing MONGO_URI, REDIS_URL, JWT_SECRET to build and run both backend and frontend locally with Docker.
