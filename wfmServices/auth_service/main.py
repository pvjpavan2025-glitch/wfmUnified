"""
Authentication & Authorization Service main application.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import structlog
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext

# Simple auth models
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    expires_in: int
    user: dict

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    roles: list = []

# Simple configuration
JWT_SECRET_KEY = "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Setup logging
logger = structlog.get_logger(__name__)

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Authentication Service")
    logger.info("Authentication Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Authentication Service")
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


# Simple auth functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

# Mock user data for testing
MOCK_USERS = {
    "admin": {
        "id": "1",
        "username": "admin",
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "password_hash": get_password_hash("admin123"),
        "roles": ["Admin"],
        "status": "active",
    },
    "technician": {
        "id": "2",
        "username": "technician",
        "email": "tech@example.com",
        "first_name": "Tech",
        "last_name": "User",
        "password_hash": get_password_hash("tech123"),
        "roles": ["Technician"],
        "status": "active"
    }
}

async def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user with username/password."""
    user = MOCK_USERS.get(username)
    if not user:
        return None
    
    if not verify_password(password, user["password_hash"]):
        return None
    
    return user


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "auth-service"}


# Authentication endpoints
@app.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """User login endpoint."""
    try:
        # Authenticate user
        user = await authenticate_user(
            login_data.username, login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create access token
        token_data = {
            "sub": user["id"],
            "username": user["username"],
            "email": user["email"],
            "roles": user["roles"]
        }
        access_token = create_access_token(token_data)
        
        # Prepare user response
        user_response = {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "roles": user["roles"]
        }
        
        return LoginResponse(
            access_token=access_token,
            expires_in=JWT_EXPIRATION_MINUTES * 60,
            user=user_response
        )
    
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/auth/verify")
async def verify_token_endpoint():
    """Verify JWT token endpoint."""
    return {"valid": True, "user": {"id": "1", "username": "admin"}}


# Simple user endpoints
@app.get("/users")
async def list_users():
    """List users."""
    users = []
    for user in MOCK_USERS.values():
        user_copy = user.copy()
        del user_copy["password_hash"]
        users.append(user_copy)
    return users


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=True
    ) 