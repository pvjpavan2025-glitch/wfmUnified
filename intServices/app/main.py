import os
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .repositories.db import init_db, engine
from sqlalchemy import text
from . import mappers  # noqa: F401  # ensure mapper registration
from .routers import applications, ingest
from .api import osm_xml_endpoint

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    """Initialize application on startup.

    Do not block startup if the database is unavailable. This allows the app to
    respond to liveness probes even when dependencies are not reachable.
    Control behavior via INTSERVICES_SKIP_DB_INIT (default: true).
    """
    skip = os.getenv("INTSERVICES_SKIP_DB_INIT", "true").lower() == "true"
    if skip:
        # Log via simple print to avoid importing logging frameworks here
        print("[startup] INTSERVICES_SKIP_DB_INIT=true -> Skipping DB init at startup")
        return
    try:
        await init_db()
        print("[startup] Database initialization completed")
    except Exception as e:
        # Do not raise; just log and continue so the app stays up
        print(f"[startup] Database initialization failed: {e}")

app.include_router(applications)
app.include_router(ingest)
app.include_router(osm_xml_endpoint.router)

@app.get("/healthz")
async def health():
    """Liveness probe: process is up."""
    return {"status": "ok", "env": settings.env}


@app.get("/ready")
async def readiness():
    """Readiness probe: verify database connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return JSONResponse(content={"db": "ok"}, status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={"db": f"error: {e}"}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
