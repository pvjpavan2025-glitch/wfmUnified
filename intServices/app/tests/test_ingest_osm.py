import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_ingest_osm_dry_run():
    headers = {settings.api_key_name: settings.api_key}
    transport = ASGITransport(app=app)
    sample = {
        "externalId": "EXT987",
        "category": "FiberInstallation",
        "serviceOrderItem": [
            {"id": "1", "action": "add", "service": {"id": "SVC1"}}
        ],
    }
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        r = await ac.post("/ingest/osm?dry_run=true", json=sample)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "validated"
        assert "canonical" in data
        assert data["canonical"]["externalId"] == "EXT987"
