"""
Authentication & Authorization Service main application.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import structlog

from shared.config import settings
from shared.database import db_manager
from shared.logging import setup_logging
from shared.auth import get_current_user
from .service import AuthService
from .repository import UserRepository, RoleRepository, TenantRepository
from .models import (
    UserCreate, UserUpdate, UserResponse, LoginRequest, LoginResponse,
    RoleCreate, RoleUpdate, RoleResponse, TenantCreate, TenantUpdate, TenantResponse
)

# Setup logging
logger = setup_logging("auth-service")

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Authentication Service")
    await db_manager.connect_mongodb()
    # Temporarily disable Redis for testing
    # await db_manager.connect_redis()
    logger.info("Authentication Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Authentication Service")
    await db_manager.close()
    logger.info("Authentication Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="WFM Authentication Service",
    description="Authentication and Authorization service for Workforce Management",
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
async def get_auth_service() -> AuthService:
    """Get authentication service instance."""
    database = await db_manager.get_database()
    user_repo = UserRepository(database)
    role_repo = RoleRepository(database)
    tenant_repo = TenantRepository(database)
    return AuthService(user_repo, role_repo, tenant_repo)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "auth-service"}


# Authentication endpoints
@app.post("/auth/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """User login endpoint."""
    try:
        # Authenticate user
        user_data = await auth_service.authenticate_user(
            login_data.username, login_data.password, login_data.tenant_id
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create access token
        access_token = await auth_service.create_access_token_for_user(user_data)
        
        # Get user details
        user = await auth_service.get_user(user_data["user_id"], user_data["tenant_id"])
        
        return LoginResponse(
            access_token=access_token,
            expires_in=settings.security.jwt_expiration_minutes * 60,
            user=UserResponse(**user)
        )
    
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/auth/verify")
async def verify_token_endpoint(
    current_user: dict = Depends(get_current_user)
):
    """Verify JWT token endpoint."""
    return {"valid": True, "user": current_user}


# User management endpoints
@app.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user)
):
    """Create a new user."""
    try:
        user = await auth_service.create_user(user_data, current_user["user_id"])
        return UserResponse(**user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create user failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user)
):
    """Get user by ID."""
    user = await auth_service.get_user(user_id, current_user["tenant_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse(**user)


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user)
):
    """Update user."""
    user = await auth_service.update_user(user_id, current_user["tenant_id"], user_data, current_user["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse(**user)


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user)
):
    """Delete user."""
    success = await auth_service.delete_user(user_id, current_user["tenant_id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deleted successfully"}


@app.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user)
):
    """List users."""
    users = await auth_service.list_users(current_user["tenant_id"], skip, limit)
    return [UserResponse(**user) for user in users]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "auth_service.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    ) 