"""
Configuration Service main application.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
import structlog

from shared.config import settings
from shared.database import db_manager
from shared.logging import setup_logging
from shared.auth import get_current_user
from .service import ConfigService
from .repository import ConfigRepository
from .models import ConfigCreate, ConfigUpdate, ConfigResponse

# Setup logging
logger = setup_logging("config-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Configuration Service")
    await db_manager.connect_mongodb()
    await db_manager.connect_redis()
    logger.info("Configuration Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Configuration Service")
    await db_manager.close()
    logger.info("Configuration Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="WFM Configuration Service",
    description="Configuration management service for Workforce Management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging is now handled by structured logging setup


# Dependency to get service instance
async def get_config_service() -> ConfigService:
    """Get configuration service instance."""
    database = await db_manager.get_database()
    redis_client = await db_manager.get_redis()
    config_repo = ConfigRepository(database)
    return ConfigService(config_repo, redis_client)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "config-service"}


# Configuration endpoints
@app.post("/configs", response_model=ConfigResponse)
async def create_config(
    config_data: ConfigCreate,
    config_service: ConfigService = Depends(get_config_service),
    current_user: dict = Depends(get_current_user)
):
    """Create a new configuration."""
    try:
        config = await config_service.create_config(config_data, current_user["user_id"])
        return ConfigResponse(**config)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create config failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/configs/{config_id}", response_model=ConfigResponse)
async def get_config(
    config_id: str,
    config_service: ConfigService = Depends(get_config_service),
    current_user: dict = Depends(get_current_user)
):
    """Get configuration by ID."""
    config = await config_service.get_config(config_id, current_user["tenant_id"])
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    return ConfigResponse(**config)


@app.put("/configs/{config_id}", response_model=ConfigResponse)
async def update_config(
    config_id: str,
    config_data: ConfigUpdate,
    config_service: ConfigService = Depends(get_config_service),
    current_user: dict = Depends(get_current_user)
):
    """Update configuration."""
    config = await config_service.update_config(
        config_id, current_user["tenant_id"], config_data, current_user["user_id"]
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    return ConfigResponse(**config)


@app.delete("/configs/{config_id}")
async def delete_config(
    config_id: str,
    config_service: ConfigService = Depends(get_config_service),
    current_user: dict = Depends(get_current_user)
):
    """Delete configuration."""
    success = await config_service.delete_config(config_id, current_user["tenant_id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    return {"message": "Configuration deleted successfully"}


@app.get("/configs", response_model=list[ConfigResponse])
async def list_configs(
    skip: int = 0,
    limit: int = 100,
    config_service: ConfigService = Depends(get_config_service),
    current_user: dict = Depends(get_current_user)
):
    """List configurations."""
    configs = await config_service.list_configs(current_user["tenant_id"], skip, limit)
    return [ConfigResponse(**config) for config in configs]


@app.get("/configs/key/{key}")
async def get_config_by_key(
    key: str,
    config_service: ConfigService = Depends(get_config_service),
    current_user: dict = Depends(get_current_user)
):
    """Get configuration by key."""
    config = await config_service.get_config_by_key(key, current_user["tenant_id"])
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    return config


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "config_service.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    ) 