# WFM End-to-End API Sequence (Integration Layer → wfmServices)

This guide walks you through a working end-to-end flow using the Integration Layer (intServices) to ingest an OSM order, transform it to the canonical Rules input, and forward it to wfmServices for orchestration (rules → jobs → schedule → issues). It also covers how to configure the API key and mint a JWT compatible with wfmServices.

References:
- Architecture PNG (attached)
- OSM sample payload: `references/input-order.json`
- End-to-end flows: `wfmServices/prompts/UML_END_TO_END_FLOW.md`
- New endpoints and flow updates introduced in this flow:
  - Order Service (wfmServices, port 8008):
    - POST /orders (creates READY order)
    - GET /orders/ready (list READY orders)
    - PATCH /orders/{order_id}/status
  - Rules Service (wfmServices, port 8003):
    - POST /rules/evaluate (existing)
    - POST /orders/process-ready (new) — fetch READY orders from Order Service and orchestrate jobs
  - Scheduler Service (wfmServices, port 8004):
    - GET /reports/orders/{order_id}/jobs-summary (new) — jobs summary and assignment breakdown for an order

---

## 1) Prerequisites

- intServices running (default: http://localhost:8082)
- wfmServices up via `docker-compose.integrated.yml`:
  - API Gateway: http://localhost:8000 (for minting local JWT)
  - Rules Service: http://localhost:8003
  - Scheduler Service: http://localhost:8004
  - Issue Service: http://localhost:8005
  - Order Service: http://localhost:8008
- Consistent JWT secret across wfmServices containers (compose sets `JWT_SECRET_KEY`) and the API Gateway `/auth/token/test` endpoint available.

Notes on tenants:
- All resources are tenant-scoped. Ensure your JWT contains the correct `tenant_id` and use the same tenant across Rules and Scheduler calls.
- Internally, Rules → Scheduler calls now forward the caller tenant. Jobs created via orchestration will appear under the same tenant you used to call Rules.

Optional: Ensure intServices knows how to contact wfmServices from Docker by using `host.docker.internal` (already set in `.env.example`).

---

## 2) Configure API Key for intServices

intServices requires an API key header on all routes unless disabled. Configure either via `.env` or environment variables.

- Header name: `X-API-Key` (configurable via `API_KEY_NAME`)
- Default value: `change-me-please` (set `API_KEY`)

Example `.env` snippet (intServices):
```
API_KEY_NAME=X-API-Key
API_KEY=change-me-please
```

Test health:
```bash
curl -s http://localhost:8082/healthz -H "X-API-Key: change-me-please"
```

---

## 3) Generate a JWT for wfmServices

For local dev, use API Gateway to mint a JWT signed with the same secret used by all services.

Request (default expires ~30 minutes; you can pass `expires_in_minutes` optionally):
```bash
curl -s -X POST http://localhost:8000/auth/token/test \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "dev-user",
    "username": "dev",
    "tenant_id": "dev-tenant",
    "roles": ["admin"]
  }'
```
Response contains `access_token`. Save it:
```bash
export WFM_JWT=$(curl -s -X POST http://localhost:8000/auth/token/test \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"dev-user","username":"dev","tenant_id":"dev-tenant","roles":["admin"], "expires_in_minutes": 60}' | jq -r .access_token)
```

Note: intServices can also mint a JWT automatically for Rules/Scheduler if you set `RULES_JWT_SECRET` to match wfmServices `JWT_SECRET_KEY` and do not pass `RULES_API_TOKEN`/`SCHEDULER_API_TOKEN`.

---

## 4) Configure intServices to call wfmServices

Ensure intServices is configured to call the actual Rules and Scheduler services (not stub mode):

- In intServices `.env` (or env vars):
```
RULES_API_BASE_URL=http://host.docker.internal:8003
RULES_API_STUB=false
RULES_API_TOKEN=$WFM_JWT  # optional if using RULES_JWT_SECRET
SCHEDULER_API_BASE_URL=http://host.docker.internal:8004
SCHEDULER_API_STUB=false
SCHEDULER_API_TOKEN=$WFM_JWT  # optional if using RULES_JWT_SECRET
ORDER_API_BASE_URL=http://host.docker.internal:8008
ORDER_API_TOKEN=$WFM_JWT  # optional if using RULES_JWT_SECRET
```
Then restart intServices:

```bash
docker compose -f intServices/docker-compose.yml restart
```

---

## 5) Sequence Overview

1. POST OSM order to intServices `/ingest/osm` with API key.
2. intServices transforms payload to canonical format.
3. intServices logs the order in Order Service as `READY` and injects the created DB `order_id` into the canonical payload.
4. intServices requests Rules Service to process (either direct `/rules/evaluate` with orchestration and `order_id`, or batch via `/orders/process-ready`).
5. Rules Service creates jobs in Scheduler, linking each job to the `order_id`; if `auto_schedule=true`, jobs are scheduled immediately.
6. Optionally, issues can be created in Issue Service for tracking.

Important behavior updates:
- Rules → Scheduler service calls now mint a service token scoped to the caller `tenant_id`. This ensures jobs and schedules are created under the same tenant as your JWT.
- Job payload enums (priority, status) are lowercase to match Scheduler models.
- Jobs now include `order_id` set to the Order Service DB id, enabling reports by order.

---

## 6) Step-by-step API calls

### A. Verify Services Health

```bash
# intServices
curl -s http://localhost:8082/healthz -H "X-API-Key: change-me-please" | jq

# wfmServices
curl -s http://localhost:8003/health | jq   # rules-service
curl -s http://localhost:8004/health | jq   # scheduler-service
curl -s http://localhost:8005/health | jq   # issue-service
curl -s http://localhost:8008/health | jq   # order-service
```

### B. Seed an analyst (optional, helps scheduling)

```bash
curl -s -X POST http://localhost:8004/analysts \
  -H "Authorization: Bearer $WFM_JWT" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Alice Analyst",
    "email": "alice@example.com",
    "tenant_id": "dev-tenant",
    "skills": ["fiber", "splicing"],
    "experience_years": 5,
  "max_concurrent_jobs": 3,
    "availability": {"mon": ["09:00-17:00"]},
    "status": "active"
  }' | jq
```

### C. Ingest OSM Order via intServices (order-first)

Use the provided `references/input-order.json` as a template and adjust values (Make sure you are in the intServices folder)

```bash
curl -s -X POST 'http://localhost:8082/ingest/osm?dry_run=false&orchestrate=true&split_jobs=true&auto_schedule=true' \
  -H 'X-API-Key: change-me-please' \
  -H 'Content-Type: application/json' \
  --data-binary @../references/input-order.json | jq
```
#### Query String Flags

- `orchestrate=true` – Ask Rules Service to orchestrate downstream.
- `split_jobs=true` – Create a job per `serviceOrderItem`.
- `auto_schedule=true` – Schedule jobs immediately.

**Example usage with all flags:**
```bash
curl -s -X POST 'http://localhost:8082/ingest/osm?orchestrate=true&split_jobs=true&auto_schedule=true' \
    -H 'X-API-Key: change-me-please' \
    -H 'Content-Type: application/json' \
    --data-binary @../references/input-order.json | jq
```

Payload behavior for orchestration flags:
- `orchestrate=true` – Ask Rules Service to orchestrate downstream job creation (and optionally scheduling).
- `split_jobs=true` – Create a job per `serviceOrderItem` present in the input (default grouping puts all items into a single job).
- `auto_schedule=true` – After job creation, immediately call Scheduler to assign an analyst and set scheduled times.

Examples:

Only orchestrate:
```bash
curl -s -X POST 'http://localhost:8082/ingest/osm?orchestrate=true' \
    -H 'X-API-Key: change-me-please' \
    -H 'Content-Type: application/json' \
    --data-binary @../references/input-order.json | jq
```

Split jobs and auto schedule:
```bash
curl -s -X POST 'http://localhost:8082/ingest/osm?split_jobs=true&auto_schedule=true' \
    -H 'X-API-Key: change-me-please' \
    -H 'Content-Type: application/json' \
    --data-binary @../references/input-order.json | jq
```

What happens under the hood now:
- intServices logs the incoming order in Order Service with status `ready` and gets back the DB id (e.g., `68a3...`).
- That `order_id` is injected into the canonical payload before calling Rules Service, so jobs created by Rules/Scheduler are linked to this order.

Expected result: JSON showing acceptance, the created order (with `_id`), the canonical payload (with `order_id`), and nested `rules_response` when orchestration is enabled.

### D. Inspect Jobs (Scheduler Service)

```bash
# List jobs in Scheduler Service (should show jobs if any were created)
curl -s 'http://localhost:8004/jobs?skip=0&limit=50' \
    -H "Authorization: Bearer $WFM_JWT" | jq '[.[] | {id: ._id, name: .name, status: .status, assigned_analyst: .assigned_analyst}]'
```
If the response is `[]`, no jobs have been created or ingested yet. 
- Confirm that the previous ingestion step succeeded and returned job objects.
- Check that `split_jobs=true` and `auto_schedule=true` were set in your ingest request.
- Review intServices and wfmServices logs for errors.
- Try ingesting again and verify the response for job IDs.

If at least one job exists but shows `status: "pending"`, you can schedule it explicitly:
```bash
JOB_ID=$(curl -s 'http://localhost:8004/jobs?skip=0&limit=1' -H "Authorization: Bearer $WFM_JWT" | jq -r '.[0]._id')
curl -s -X POST http://localhost:8004/jobs/$JOB_ID/schedule \
  -H "Authorization: Bearer $WFM_JWT" | jq
```
If job IDs are known, you can schedule explicitly:
```bash
curl -s -X POST http://localhost:8004/jobs/<job_id>/schedule \
  -H "Authorization: Bearer $WFM_JWT" | jq
```

### E. Create an Issue (Issue Service)

When creating issues directly, enums are lowercase:
- priority: one of `low|medium|high|critical`
- status: one of `active|inactive|pending|completed|failed|cancelled|open|closed`

```bash
curl -s -X POST http://localhost:8005/issues \
  -H "Authorization: Bearer $WFM_JWT" \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Install site access problem",
    "description": "Gate locked, need reschedule",
    "category": "ops",
    "priority": "medium",
    "tenant_id": "dev-tenant",
    "status": "open"
  }' | jq
```

Add a comment:
```bash
curl -s -X POST http://localhost:8005/issues/<issue_id>/comments \
  -H "Authorization: Bearer $WFM_JWT" \
  -H 'Content-Type: application/json' \
  -d '{
    "content": "Contacted customer, rescheduling.",
    "issue_id": "<issue_id>",
    "tenant_id": "dev-tenant"
  }' | jq
```

---

### F. Reporting by OrderId (jobs summary)

Once jobs are created with the DB order id, fetch an at-a-glance summary:

```bash
curl -s -S "http://localhost:8004/reports/orders/$ORDER_ID/jobs-summary" \
  -H "Authorization: Bearer $WFM_JWT" | jq
```

Sample response:

```json
{
  "order_id": "68a30bccc5fdc3bd0a0283fd",
  "total_jobs": 1,
  "status_counts": { "scheduled": 1 },
  "assignment": { "assigned": 1, "unassigned": 0 },
  "jobs": [
    {
      "id": "68a30bcd64b0b38133801ac1",
      "name": "Order OSM-REPORT-EXAMPLE",
      "status": "scheduled",
      "assigned_analyst": "68a209a4fa78ce6897514799",
      "order_id": "68a30bccc5fdc3bd0a0283fd",
      "scheduled_start": "2025-08-18T12:17:33.804000",
      "scheduled_end": "2025-08-19T12:17:33.804000"
    }
  ]
}
```

Tip: “to be started” corresponds to `status: "pending"`; “completed” is `status: "completed"`.

---

## 7) Troubleshooting

- 401/403 when calling wfmServices: ensure you are sending `Authorization: Bearer $WFM_JWT` and the token was minted by the running stack (`/auth/token/test`).
- Token expired: the `/auth/token/test` tokens are short-lived; re-mint with `{"expires_in_minutes": 60}` if needed and export `WFM_JWT` again.
- 502 from intServices ingestion: verify `RULES_API_BASE_URL` and that Rules Service is reachable; if running inside Docker, use `host.docker.internal`.
- 422 on Issue Service create: ensure enum values are lowercase per service definitions.
- DB/Redis connectivity: wfmServices depends on MongoDB/Redis endpoints configured via compose env vars; check service logs.
- Jobs created but not listed: verify tenant consistency. The same token/tenant used to ingest must be used to list jobs. Jobs are filtered by `tenant_id`.
- Jobs created but scheduling fails with 400: ensure you have at least one analyst with `status: "active"` in the same tenant, and reasonable `max_concurrent_jobs` (default is treated as 5 if not set).

---

## 8) Environment Variables Summary (intServices)

- `API_KEY_NAME` / `API_KEY` – header name and value for request authorization
- `RULES_API_BASE_URL` – e.g., `http://host.docker.internal:8003`
- `RULES_API_STUB` – `false` to call real Rules Service
- `RULES_API_TOKEN` – bearer token to call Rules Service; optional if JWT minting enabled
- `RULES_JWT_SECRET` – set to wfmServices `JWT_SECRET_KEY` to auto-mint JWT
- `SCHEDULER_API_BASE_URL` – e.g., `http://host.docker.internal:8004`
- `SCHEDULER_API_STUB` – `false` to call real Scheduler Service
- `SCHEDULER_API_TOKEN` – bearer token for Scheduler Service
- `ORDER_API_BASE_URL` – e.g., `http://host.docker.internal:8008`
- `ORDER_API_TOKEN` – bearer token for Order Service (optional when JWT minting is enabled)

---

## 9) Clean-up

To stop services:
```bash
docker compose -f wfmServices/docker-compose.integrated.yml down
```
To stop intServices:
```bash
docker compose -f intServices/docker-compose.yml down
```

---
## 10) Re-process READY orders and check a report manually

### Mint a token
ACCESS=$(curl -s -S -X POST "http://localhost:8000/auth/token/test" \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"dev-user","username":"dev","tenant_id":"dev-tenant","roles":["admin"],"expires_in_minutes":60}' | jq -r .access_token)

### Create a READY order
ORDER_JSON=$(curl -s -S -X POST "http://localhost:8008/orders" \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{"external_id":"OSM-REPORT-X","source":"OSM","payload":{"externalId":"OSM-REPORT-X","serviceOrderItems":[{"id":"item-1"}]},"status":"ready"}')
ORDER_ID=$(echo "$ORDER_JSON" | jq -r '._id // .id')

### Process READY orders via Rules Service (batch)
curl -s -S -X POST "http://localhost:8003/orders/process-ready" \
  -H "Authorization: Bearer $ACCESS" | jq .

### Get report by order
curl -s -S "http://localhost:8004/reports/orders/$ORDER_ID/jobs-summary" \
  -H "Authorization: Bearer $ACCESS" | jq .


## 11) One-command verification (Make + VS Code Task)

When you just want to sanity-check the full flow quickly, use the automated verifier we added. It mints a dev JWT, checks health, seeds an analyst if needed, ingests the sample OSM order with orchestrate/split/auto_schedule, and lists jobs.

### Option A: Make target

From the `intServices` folder:

```bash
make verify-e2e
```

Environment overrides (optional):

- INT_BASE: default http://localhost:8082
- GATEWAY_BASE: default http://localhost:8000
- RULES_BASE: default http://localhost:8003
- SCHED_BASE: default http://localhost:8004
- API_KEY_NAME: default X-API-Key
- API_KEY: default change-me-please
- TENANT_ID: default dev-tenant
- USER_ID: default dev-user
- USERNAME: default dev
- ROLES_JSON: default ["admin"]
- EXPIRES_MIN: default 60
- WFM_JWT: if set, the script uses it instead of minting a token
- INPUT_JSON: path to OSM input (defaults to references/input-order.json at repo root)

Example with overrides:

```bash
INT_BASE=http://localhost:8082 \
TENANT_ID=my-tenant \
API_KEY=my-api-key \
make verify-e2e
```

On success you should see:
- Health checks output
- Analyst seeding (only if none exist)
- Ingestion summary showing jobs and schedules counts
- Report-by-order summary (if `order_id` is available or via fallback order creation)
- A compact jobs list like:

```json
[
  { "id": "<job_id>", "name": "<name>", "status": "scheduled", "assigned_analyst": "Auto Analyst" }
]
```

If a first job is pending, the script will try to schedule it automatically.

### How to verify via Make

From the `intServices` folder, use these commands end-to-end:

1) Run the end-to-end verifier (creates/uses an order and persists its id to `scripts/.last_order_id`):

```bash
make verify-e2e
```

2) Print the report for the most recent order (uses the saved id):

```bash
make report-last-order
```

3) Print the report for a specific OrderId (summary only):

```bash
make report-order ORDER_ID=<mongo_id>
```

4) Print the full JSON for a specific OrderId (includes jobs list):

```bash
make report-order-full ORDER_ID=<mongo_id>
```

Notes:
- The scripts auto-mint a dev JWT via the API Gateway if `WFM_JWT` isn’t provided.
- Ensure the token’s `tenant_id` matches the tenant that created the jobs; otherwise, counts may be zero.

### Option B: VS Code Tasks

We added tasks in `intServices/.vscode/tasks.json`:
- Verify E2E (mint → seed → ingest → report → list)
- Report by OrderId (scheduler) — prompts for the OrderId and prints the summary

To run it:
1. Open the multi-root workspace.
2. In VS Code, press Cmd+Shift+P → "Run Task" → select the task above.
3. The task runs in a dedicated panel. You can set environment overrides by adding them to your VS Code environment (or via a shell from which you launch VS Code).

Notes:
- Ensure wfmServices are up (docker-compose.integrated.yml) and intServices is running.
- The Verify task runs from the `intServices` folder and calls `scripts/verify_e2e.sh`.
- jq is required (macOS: `brew install jq`).

Troubleshooting quick hits:
- 401/403: Token expired or wrong; re-mint by re-running the task. You can also set WFM_JWT to a known-good token.
- Empty jobs list: Check tenant: the token's tenant must match what you used during ingestion. Ensure at least one active analyst exists.
- 502 from ingestion: Verify RULES_BASE and service availability.
