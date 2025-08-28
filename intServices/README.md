# Integration Services (intServices)

FastAPI-based integration layer that ingests payloads from external applications (e.g., OSM, BRM, Activation), transforms them into the canonical Rules API payload, and forwards them to the WFM Rules Service.

## Features
- Application registry with CRUD
- Application Endpoint registry with CRUD
- Pluggable transformation engine (per-app adapters + JSON mapping support)
- Example OSM ingestion endpoint
- Security via API keys / bearer tokens (configurable)
- Async HTTP forwarding to Rules API

## Quickstart

1. Create a virtualenv and install deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Configure environment

Copy `.env.example` to `.env` and fill values (defaults to Postgres).

3. Run the server

```bash
uvicorn app.main:app --reload --port 8082
```

Open: http://localhost:8082/docs
### API key header

All endpoints require an API key header unless you clear `API_KEY` in env.

- Header name: `X-API-Key` (configurable via `API_KEY_NAME`)
- Default value: `change-me-please` (set `API_KEY`)

Example:

```bash
curl -H "X-API-Key: change-me-please" http://localhost:8082/healthz
```


## Canonical Rules Payload
The canonical target payload is defined in `app/models/rules.py` and used by mappers. See `references/input-order.json` for a sample source payload from OSM.

## Docker

Run app + Postgres with data persisted in a named volume:

```bash
docker compose up --build
```

Then visit http://localhost:8082/docs

By default, the service runs with `RULES_API_STUB=true` so you can test end-to-end without a live Rules API. To call a real Rules API, set `RULES_API_STUB=false` and configure `RULES_API_BASE_URL` (default http://localhost:8003 for wfmServices rules-service). If `RULES_API_TOKEN` is not set but `rules_jWT_SECRET` is provided, the service will mint a compatible JWT on-the-fly for wfmServices.

### Optional: Create and schedule jobs

You can have the ingestion endpoint create jobs and schedule them via the wfmServices scheduler-service. Use the query flags:

- `create_job=true` to create a job per order (or per item if `split_jobs=true`).
- `schedule_job=true` to immediately schedule the created job(s).
- `split_jobs=true` to create one job per serviceOrderItem.

Examples:

```bash
curl -X POST 'http://localhost:8082/ingest/osm?dry_run=false&create_job=true&schedule_job=true&split_jobs=true' \
	-H 'X-API-Key: change-me-please' -H 'Content-Type: application/json' \
	-d '{"externalId":"ORD-1","description":"Fiber install","serviceOrderItem":[{"id":"ITEM-1"},{"id":"ITEM-2"}]}'
```

When running against real services, set:

- `RULES_API_STUB=false`
- `SCHEDULER_API_STUB=false`
- Provide either `RULES_API_TOKEN` / `SCHEDULER_API_TOKEN` OR set `RULES_JWT_SECRET` to the same as `wfmServices`' `JWT_SECRET_KEY` (intServices will mint JWTs).

## Tests
```bash
pytest
```
