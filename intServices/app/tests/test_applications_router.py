import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.repositories.db import init_db
from app.core.config import settings

@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/healthz")
        assert resp.status_code == 200

@pytest.mark.asyncio
async def test_applications_crud():
    await init_db()
    headers = {settings.api_key_name: settings.api_key}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        # create
        app_payload = {"name": "OSM", "code": "osm", "base_url": "http://osm", "auth_type": "none"}
        r = await ac.post("/applications/", json=app_payload)
        assert r.status_code == 200
        app_id = r.json()["id"]

        # list
        r = await ac.get("/applications/")
        assert r.status_code == 200
        assert len(r.json()) >= 1

        # update
        r = await ac.put(f"/applications/{app_id}", json={"is_active": False})
        assert r.status_code == 200
        assert r.json()["is_active"] is False

        # delete
        r = await ac.delete(f"/applications/{app_id}")
        assert r.status_code == 200
