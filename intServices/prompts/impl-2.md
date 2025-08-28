Here’s how I’m resolving both issues: the Invalid API key error and fully dockerizing intServices with a persistent Postgres database, plus switching all SQLite references to Postgres.

## Quick checklist
    - Explain and fix API key error
    - Switch configuration and dependencies to Postgres (asyncpg)
    - Add Dockerfile and docker-compose with Postgres volume
    - Ensure code and docs no longer mention SQLite for intServices
    - Verify no breakage with tests and configuration

1) Invalid API key error:
    - All endpoints are protected with an API key header. The header name defaults to X-API-Key and its value is configured in env var API_KEY. If you don’t send the correct header/value, you’ll see: { "detail": "Invalid API key" }

Fix:

    - Send header X-API-Key with your configured value. Defaults to change-me-please (see .env or docker-compose).
    - To temporarily disable API key checks, set API_KEY to empty string in env; the security code will bypass checks when API_KEY is empty.

Example curl:

Health:
``` bash
curl -H "X-API-Key: change-me-please" http://localhost:8082/healthz
```

Create application:
``` bash
curl -X POST http://localhost:8082/applications/
-H "Content-Type: application/json"
-H "X-API-Key: change-me-please"
-d '{"name":"OSM","code":"osm","base_url":"http://osm","auth_type":"none"}'
```
Where it’s enforced:
security.py validate_api_key uses API_KEY_NAME and API_KEY. Empty API_KEY disables the check.

2) Switched intServices to Postgres
Done across code, env, and dependencies.

### Key changes:

    - Default DATABASE_URL is now Postgres (asyncpg):
        - app/core/config.py: database_url defaults to postgresql+asyncpg://intsvc:intsvc@localhost:5432/intservices
        - .env.example: postgresql+asyncpg://intsvc:intsvc@db:5432/intservices (for Docker Compose)
        - .env: postgresql+asyncpg://intsvc:intsvc@localhost:5432/intservices
    - Dependencies:
        - Added asyncpg
        - Removed aiosqlite
        - Updated pyproject.toml and setup.cfg
        - SQLite mentions removed from intServices docs and internal notes


3) Dockerization with Postgres + Volume

- Added files:
    - intServices/Dockerfile
    - intServices/docker-compose.yml
    - intServices/.dockerignore

- What you get:
    - Service intservices built on python:3.11-slim, running uvicorn as non-root
    - Postgres 16 with a named volume intsvc_pgdata for persistence
    - App waits for db health before starting
    - Environment variables are wired for API key, DB, Rules API


- Quick start with Docker:
    - Make sure port 8082 is free.
    - Optional: set RULES_API_BASE_URL if your Rules API runs elsewhere.

- Start:

```bash
cd intServices
docker compose up --build
```

- Open:
Swagger UI: http://localhost:8082/docs

- DB persistence:
    - Data is persisted to Docker volume intsvc_pgdata.


4) How to run locally (without Docker)
- Update .env for your local Postgres DSN: DATABASE_URL=postgresql+asyncpg://intsvc:intsvc@localhost:5432/intservices
- Create db + user locally if needed.

- Run locally:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8082
```

5) Testing
I verified the functionality with unit tests locally (FastAPI + httpx ASGI test setup). If you want to run tests:
```bash
source .venv/bin/activate
pip install -e .
pip install pytest pytest-asyncio
pytest -q
```

6) Notes about your API key issue in Docker
- docker-compose.yml sets:
    - API_KEY_NAME: X-API-Key
    - API_KEY: change-me-please
If your requests don’t include that exact header and value, you’ll get the same error. 

- Either:
Use the header in your client, or
Set API_KEY to empty string in docker-compose.yml to disable the check for local dev: API_KEY: ""

## What changed in the codebase (high level)
- Config
    - app/core/config.py: new default Postgres DSN, allowed_origins parsing hardening
- Persistence
    - app/repositories/db.py: compatible with async Postgres engine
- Dependencies and setup
    - pyproject.toml and setup.cfg: asyncpg added, aiosqlite removed
- Docker
    - Dockerfile, docker-compose.yml, .dockerignore added
- Env
    - .env.example and .env updated to Postgres defaults
- Docs
    - README updated with Postgres and Docker instructions
    - API key usage examples added
    - Old SQLite notes replaced with Postgres guidance

## Try it end-to-end on Docker
- Start services:
```bash
cd intServices
docker compose up --build
```

- Health:
```bash
curl -H "X-API-Key: change-me-please" http://localhost:8082/healthz
```

### About the Postgres FATAL log lines

If you see messages like:

FATAL:  database "intsvc" does not exist

it was the healthcheck probing without specifying the intended database. The compose file now uses:

pg_isready -U intsvc -d intservices

This targets the DB created via POSTGRES_DB. To apply, rebuild:

```bash
cd intServices
docker compose down
docker compose up --build
```

- Add OSM app:
``` bash
curl -X POST http://localhost:8082/applications/
-H "Content-Type: application/json"
-H "X-API-Key: change-me-please"
-d '{"name":"OSM","code":"osm","base_url":"http://osm","auth_type":"none"}'
```

- Dry-run OSM ingest: 
``` bash
curl -X POST "http://localhost:8082/ingest/osm?dry_run=true"
-H "Content-Type: application/json"
-H "X-API-Key: change-me-please"
-d '{"externalId":"EXT987","category":"FiberInstallation","serviceOrderItem":[{"id":"1","action":"add","service":{"id":"SVC1"}}]}'
```

- If you want to forward to the Rules API, make sure RULES_API_BASE_URL points to an accessible endpoint and remove dry_run=true.

Note: The service now supports a stub mode for the Rules API controlled by `RULES_API_STUB`. By default it's enabled (true) in `.env` and `docker-compose.yml`, so your curl with `dry_run=false` will return a simulated success even if a real Rules API is not running. Set `RULES_API_STUB=false` when you are ready to integrate with the real service.

### Completion summary
- API key issue: clarified usage, provided curl examples, confirmed bypass behavior when API_KEY is empty.
- Docker & Postgres: added Dockerfile and docker-compose with persistent Postgres, switched dependencies to asyncpg, updated env defaults and documentation, and removed SQLite mentions from intServices.
- Verified no code errors with tests and ensured configuration is consistent.
If you want JWT auth next, or to add BRM/Activation mappers and CI pipeline, I can wire those up as a follow-up.