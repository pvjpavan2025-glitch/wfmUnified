"""
Pytest configuration and fixtures for WFM tests.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from shared.config import settings
from shared.database import get_database, get_redis_client
from shared.auth import TokenManager, TokenData
from shared.logging import setup_logging


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Test settings with in-memory databases."""
    settings.database.mongodb_url = "mongodb://localhost:27017"
    settings.database.redis_url = "redis://localhost:6379"
    settings.database.database_name = "wfm_test"
    settings.security.jwt_secret_key = "test-secret-key"
    settings.logging.log_level = "DEBUG"
    return settings


@pytest.fixture
async def mock_mongodb():
    """Mock MongoDB client."""
    mock_client = AsyncMock()
    mock_db = AsyncMock()
    mock_collection = AsyncMock()
    
    mock_client.get_database.return_value = mock_db
    mock_db.get_collection.return_value = mock_collection
    
    return mock_client, mock_db, mock_collection


@pytest.fixture
async def mock_redis():
    """Mock Redis client."""
    mock_client = AsyncMock()
    return mock_client


@pytest.fixture
def token_manager():
    """Token manager instance for testing."""
    return TokenManager()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "user_id": "test-user-123",
        "username": "testuser",
        "email": "test@example.com",
        "tenant_id": "test-tenant-123",
        "roles": ["user", "analyst"],
        "status": "active"
    }


@pytest.fixture
def sample_token_data(sample_user_data):
    """Sample token data for testing."""
    return TokenData(
        user_id=sample_user_data["user_id"],
        username=sample_user_data["username"],
        tenant_id=sample_user_data["tenant_id"],
        roles=sample_user_data["roles"],
        exp=None  # Will be set by token manager
    )


@pytest.fixture
def auth_headers(token_manager, sample_user_data):
    """Generate authentication headers for testing."""
    token_data = {
        "user_id": sample_user_data["user_id"],
        "username": sample_user_data["username"],
        "tenant_id": sample_user_data["tenant_id"],
        "roles": sample_user_data["roles"]
    }
    access_token = token_manager.create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return Mock()


@pytest.fixture
def mock_tracer():
    """Mock tracer for testing."""
    mock_tracer = Mock()
    mock_span = Mock()
    mock_span_context = Mock()
    
    mock_tracer.start_span.return_value = mock_span_context
    mock_span_context.__enter__ = Mock(return_value=mock_span)
    mock_span_context.__exit__ = Mock(return_value=None)
    
    return mock_tracer, mock_span, mock_span_context


@pytest.fixture
def test_client():
    """Test client for FastAPI applications."""
    def _test_client(app):
        return TestClient(app)
    return _test_client


@pytest.fixture
async def clean_databases():
    """Clean test databases before and after tests."""
    # Setup: Clean databases
    mongodb_client = AsyncIOMotorClient(settings.database.mongodb_url)
    redis_client = redis.from_url(settings.database.redis_url)
    
    # Clean MongoDB
    db = mongodb_client[settings.database.database_name]
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].delete_many({})
    
    # Clean Redis
    await redis_client.flushdb()
    
    yield
    
    # Teardown: Clean databases again
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].delete_many({})
    await redis_client.flushdb()
    
    await mongodb_client.close()
    await redis_client.close()


# Configure logging for tests
setup_logging("test-service") 