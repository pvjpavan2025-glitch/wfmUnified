import asyncio
import os
import pytest

# Ensure test ENV uses Postgres if available, else fall back to a local file DB for unit tests.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://intsvc:intsvc@localhost:5432/intservices")
os.environ.setdefault("API_KEY", "test-key")

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
