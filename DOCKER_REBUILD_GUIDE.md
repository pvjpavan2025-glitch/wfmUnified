# WFM Docker Complete Rebuild Guide

This guide provides step-by-step instructions for completely rebuilding the WFM (Workforce Management) Docker environment from scratch.

## When to Use This Guide

Use this complete rebuild process when:
- Making significant code changes that require fresh containers
- Cleaning up after removing unnecessary Docker files
- Resolving persistent caching issues
- Starting with a clean slate for testing

## Prerequisites

- Docker and Docker Compose installed
- Terminal/Command line access
- Navigate to the project root directory: `/Users/pavan.pvj/code/wfmUnified`

## Complete Rebuild Process

### Step 1: Stop All Running Containers
```bash
docker-compose down
```

### Step 2: Remove All Containers (Optional Cleanup)
```bash
docker container prune -f
```

### Step 3: Remove All WFM Docker Images
First, list all WFM-related images:
```bash
docker image ls | grep -E "(wfmunified|wfm)"
```

Remove all WFM images:
```bash
docker image rm wfmunified-wfmapp wfmunified-auth-service wfmunified-wfmprocess-backend wfmunified-analytics-service wfmunified-api-gateway wfmunified-config-service wfmunified-dashboard-service wfmunified-rules-service wfmunified-vendor-service wfmunified-issue-service wfmunified-order-service wfmunified-process-service wfmunified-scheduler-service
```

### Step 4: Clean Up Unused Images
```bash
docker image prune -f
```

### Step 5: Rebuild All Images from Scratch
```bash
docker-compose build --no-cache
```
*Note: This step takes several minutes as it rebuilds all services without using cached layers.*

### Step 6: Start All Services
```bash
docker-compose up -d
```

### Step 7: Wait for Services to Initialize
```bash
sleep 15
```

### Step 8: Verify Services are Running
```bash
docker compose ps
```

## Service Verification

### Check Auth Service
```bash
curl -s http://localhost:8001/health
```
Expected response: `{"status":"healthy","service":"auth-service"}`

### Test Login
```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Check Frontend
```bash
curl -s http://localhost:3000 | head -5
```
Should return HTML content (frontend redirects to /login when not authenticated).

## Service Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Auth Service | 8001 | http://localhost:8001 |
| API Gateway | 8000 | http://localhost:8000 |
| Config Service | 8002 | http://localhost:8002 |
| Rules Service | 8003 | http://localhost:8003 |
| Scheduler Service | 8004 | http://localhost:8004 |
| Issue Service | 8005 | http://localhost:8005 |
| Analytics Service | 8006 | http://localhost:8006 |
| Dashboard Service | 8007 | http://localhost:8007 |
| BPMN Backend | 8100 | http://localhost:8100 |
| Postgres | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| Traefik Dashboard | 8080 | http://localhost:8080 |

## Expected Service Status

After rebuild, these services should be running:
- ✅ wfm_auth_service (healthy)
- ✅ wfm_unified_frontend
- ✅ wfm_api_gateway
- ✅ wfm-postgres (healthy)
- ✅ wfm-redis (healthy)
- ✅ wfm-bpmn-backend (healthy)
- ✅ All microservices (analytics, config, rules, scheduler, issue, dashboard)

Some services may show "Restarting" initially - this is normal as they establish database connections.

## Troubleshooting

### If Services Fail to Start
1. Check logs: `docker compose logs [service-name]`
2. Verify Docker daemon is running
3. Ensure no port conflicts with other applications

### If Auth Service is Unhealthy
1. Check auth service logs: `docker compose logs auth-service`
2. Verify Dockerfile.auth exists in wfmServices directory
3. Ensure simple_main.py exists in auth_service directory

### If Frontend Shows Errors
1. Clear browser cache completely (Ctrl+Shift+Delete)
2. Use hard refresh (Ctrl+F5 or Cmd+Shift+R)
3. Check frontend logs: `docker compose logs wfmapp`

## Login Credentials

Use these credentials to test the application:
- **Username**: `admin`
- **Password**: `admin123`

Alternative credentials:
- **Username**: `admin1`  
- **Password**: `Admin123!`

## Complete One-Line Rebuild Command

For experienced users, here's the complete rebuild in one command:
```bash
docker-compose down && docker container prune -f && docker image ls | grep wfmunified | awk '{print $1":"$2}' | xargs -r docker image rm && docker image prune -f && docker-compose build --no-cache && docker-compose up -d
```

## Separate builds:

### Build only FE
docker-compose build --no-cache wfmapp
docker-compose up -d

### Build but DONT start
- Start all other services first:
  - docker-compose up -d --scale wfmapp=0
- Build wfmApp separately later:
  - docker-compose build wfmapp && docker-compose up -d wfmapp

### REmove only few images and rebuild
- docker-compose stop wfmapp api-gateway order-service vendor-service
- docker image rm wfmunified-wfmapp:latest wfmunified-api-gateway:latest wfmunified-order-service:latest wfmunified-vendor-service:latest
- docker images | grep wfmunified
- docker image rm wfmunified-wfmapp wfmunified-api-gateway wfmunified-order-service wfmunified-vendor-service
  - docker rmi -f b9b6f468e2dd d1835e664b17 1366468a6003 ead0c7611f44
- docker-compose build --no-cache wfmapp api-gateway order-service vendor-service
- docker-compose up -d order-service vendor-service
- docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
- docker logs wfm_order_service --tail 10


## Notes

- The rebuild process removes ALL containers and images, ensuring a completely fresh start
- Build time varies depending on system performance (typically 5-10 minutes)
- All data in containers is lost during this process (use volumes for persistent data)
- The auth service is configured with `restart: unless-stopped` for automatic recovery
