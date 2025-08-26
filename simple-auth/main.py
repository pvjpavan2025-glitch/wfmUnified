"""
Simplified Authentication Service for WFM Testing
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
import hashlib

app = FastAPI(title="Simple Auth Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory user store for testing
USERS = {
    "admin1": {
        "user_id": "689b86506707fa5d44d5bf81",
        "username": "admin1",
        "password": "Admin123!",  # In production, this would be hashed
        "roles": ["admin"],
        "email": "admin@wfm.com"
    }
}

JWT_SECRET = "wfmv4-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    expires_in: int
    user: dict

class TokenVerifyResponse(BaseModel):
    valid: bool
    user: dict

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "simple-auth-service"}

@app.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Simple login endpoint."""
    try:
        # Check if user exists
        user = USERS.get(login_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password (in production, use proper hashing)
        if user["password"] != login_data.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create JWT token
        payload = {
            "user_id": user["user_id"],
            "username": user["username"],
            "roles": user["roles"],
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            "type": "access"
        }
        
        access_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return LoginResponse(
            access_token=access_token,
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user={
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"],
                "roles": user["roles"]
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/auth/verify", response_model=TokenVerifyResponse)
async def verify_token(token: str = None):
    """Verify JWT token endpoint."""
    try:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token required"
            )
        
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        return TokenVerifyResponse(
            valid=True,
            user={
                "user_id": payload["user_id"],
                "username": payload["username"],
                "roles": payload["roles"]
            }
        )
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
