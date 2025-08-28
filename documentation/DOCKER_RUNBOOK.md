# WFM Docker Runbook

This guide covers how to containerize and run the full WFM stack:
- Backend microservices (wfmServices)
- Integration layer (intServices)
- Frontend app (wfmApp)
- Sample .env files for each
- How to bring everything up and test end-to-end using Make (including the OrderId report)

Requirements:
- Docker Desktop (with Docker Compose v2)
- macOS note: host networking uses host.docker.internal
- Optional: jq for pretty JSON (brew install jq)

---

## 1) Dockerizing wfmServices (all microservices)

The repo includes a Compose file that builds and runs all services:
- API Gateway (8000)
- Auth, Config, Rules (8001–8003)
- Scheduler (8004)
- Issue (8005), Analytics (8006), Dashboard (8007)
- Order Service (8008)
- Frontend app (wfmApp) at 3000 (optional in this stack)

Build images:
```bash
docker compose -f wfmServices/docker-compose.integrated.yml build
```

Run the stack:
```bash
docker compose -f wfmServices/docker-compose.integrated.yml up -d
```

Check health:
```bash
curl -s http://localhost:8003/health | jq   # rules-service
curl -s http://localhost:8004/health | jq   # scheduler-service
curl -s http://localhost:8005/health | jq   # issue-service
curl -s http://localhost:8008/health | jq   # order-service
```

Stop the stack:
```bash
docker compose -f wfmServices/docker-compose.integrated.yml down
```

Notes:
- Secrets in Compose should be provided via environment variables or Docker secrets in production. Replace any inline credentials with your own.
- All services expect a shared JWT secret; API Gateway also exposes /auth/token/test for dev tokens.

---

## 2) Dockerizing intServices (integration layer)

The integration layer has its own Compose file that brings up Postgres and the app:
- intservices (8082)
- Postgres (5432)

Build images:
```bash
docker compose -f intServices/docker-compose.yml build
```

Run the stack:
```bash
docker compose -f intServices/docker-compose.yml up -d
```

Check health:
```bash
curl -s http://localhost:8082/healthz -H "X-API-Key: change-me-please" | jq
```

Stop the stack:
```bash
docker compose -f intServices/docker-compose.yml down
```

Notes:
- By default, intServices is configured to talk to wfmServices via host.docker.internal on the host ports (8003, 8004, 8008). Ensure wfmServices stack is running if you set RULES_API_STUB/SCHEDULER_API_STUB=false.

---

## 3) Dockerizing wfmApp (frontend)

wfmApp has a Dockerfile that builds and serves the Next.js app on port 3000.

Build image:
```bash
docker build -t wfmapp:local -f wfmApp/Dockerfile wfmApp
```

Run container (stand-alone):
```bash
docker run --rm -p 3000:3000 \
  --env-file ./references/env-samples/.env.wfmApp.example \
  --name wfmapp wfmapp:local
```

Alternatively, wfmApp is already included as service `wfmapp` in wfmServices/docker-compose.integrated.yml. When you run that Compose file, the frontend will be built/launched automatically and served on http://localhost:3000.

---

## 4) Sample .env files

Use these as starting points. Copy into your repos (or reference with --env-file for docker run).

### 4.1) wfmApp (.env.local or .env)
```bash
# Frontend runtime envs
NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8000
NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:8000
NODE_ENV=production
```

### 4.2) intServices (.env)
```bash
# App
APP_NAME=Integration Layer
ENV=docker
PORT=8082
ALLOWED_ORIGINS=http://localhost:3000
API_KEY_NAME=X-API-Key
API_KEY=change-me-please

# Postgres (match docker-compose.yml)
DATABASE_URL=postgresql+asyncpg://intsvc:intsvc@db:5432/intservices

# External services (real services; set *_STUB=false when ready)
RULES_API_BASE_URL=http://host.docker.internal:8003
RULES_API_STUB=false
RULES_API_TOKEN=
SCHEDULER_API_BASE_URL=http://host.docker.internal:8004
SCHEDULER_API_STUB=false
SCHEDULER_API_TOKEN=
ORDER_API_BASE_URL=http://host.docker.internal:8008
ORDER_API_TOKEN=

# Optional: auto-mint JWT for Rules/Scheduler/Order if secrets align
RULES_JWT_SECRET=
```

### 4.3) wfmServices (.env)
```bash
# Common
MONGODB_URL=mongodb+srv://<user>:<password>@<cluster>/?retryWrites=true&w=majority&appName=<app>
REDIS_URL=redis://<user>:<password>@<host>:<port>
DATABASE_NAME=wfm
JWT_SECRET_KEY=replace-with-strong-secret
ENVIRONMENT=production
ENV_FILE=env.online

# Optional per-service overrides can be set per container in compose
```

Store these example files here for convenience if you want to reference them via --env-file:
- references/env-samples/.env.wfmApp.example
- references/env-samples/.env.intServices.example
- references/env-samples/.env.wfmServices.example

---

## 5) Bring everything up (recommended order)

1) Start wfmServices (backend + optional frontend):
```bash
docker compose -f wfmServices/docker-compose.integrated.yml up -d
```

2) Start intServices (integration layer + Postgres):
```bash
docker compose -f intServices/docker-compose.yml up -d
```

3) (Optional) If you want to run wfmApp stand-alone, build and run its container using the steps in section 3; otherwise, the integrated compose already runs it on port 3000.

4) Sanity checks:
```bash
# Mint a dev token via API Gateway
curl -s -X POST http://localhost:8000/auth/token/test -H 'Content-Type: application/json' \
  -d '{"user_id":"dev-user","username":"dev","tenant_id":"dev-tenant","roles":["admin"],"expires_in_minutes":60}' | jq

# intServices health
curl -s http://localhost:8082/healthz -H "X-API-Key: change-me-please" | jq

# Scheduler health
curl -s http://localhost:8004/health | jq
```

Stop everything:
```bash
# Stop intServices
docker compose -f intServices/docker-compose.yml down
# Stop wfmServices
docker compose -f wfmServices/docker-compose.integrated.yml down
```

---

## 6) Verify end-to-end (Make targets only)

From the `intServices` folder, run the automated verifier and reports:

- Full end-to-end verification (mints token, health checks, seeds analyst, ingests, prints report summary, lists jobs):
```bash
make verify-e2e
```

- Report for the most recent order (uses scripts/.last_order_id saved by the verifier):
```bash
make report-last-order
```

- Report for a specific OrderId (summary):
```bash
make report-order ORDER_ID=<mongo_id>
```

- Report for a specific OrderId (full JSON, includes jobs list):
```bash
make report-order-full ORDER_ID=<mongo_id>
```

Tips:
- Keep the same tenant_id across calls. The verifier and report helpers mint dev tokens for tenant "dev-tenant" by default; override TENANT_ID if required.
- If counts are unexpectedly zero, ensure the token’s tenant matches the one used during ingestion and that wfmServices are running.

---

## 7) Troubleshooting

- 401/403 errors: Token likely expired or wrong secret; re-mint using /auth/token/test and re-run.
- Empty jobs list: Check tenant consistency and that an active analyst exists.
- 502 from intServices ingestion: Ensure RULES_API_BASE_URL points to a reachable Rules Service and *_STUB=false.
- host.docker.internal resolution: On macOS, it resolves to the host automatically. For Linux, use host-gateway networking.
- Rebuild a single backend service:
```bash
docker compose -f wfmServices/docker-compose.integrated.yml build rules-service && \
  docker compose -f wfmServices/docker-compose.integrated.yml up -d rules-service
```

---

This runbook should get you from clean checkout to a running, testable stack with minimal friction. If you want these env samples as physical files, they are included under references/env-samples/ for quick --env-file usage.
