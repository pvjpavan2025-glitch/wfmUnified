#!/usr/bin/env python3
"""
Simple Authentication Service for WFM - Quick Fix
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    expires_in: int
    user: dict

# Create FastAPI app
app = FastAPI(title="WFM Auth Service", version="1.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock users for testing
USERS = {
    "admin": {"password": "admin123", "id": "1", "username": "admin", "email": "admin@example.com", "first_name": "Admin", "last_name": "User", "roles": ["Admin"]},
    "admin1": {"password": "Admin123!", "id": "3", "username": "admin1", "email": "admin1@example.com", "first_name": "Admin", "last_name": "One", "roles": ["Admin"]},
    "technician": {"password": "tech123", "id": "2", "username": "technician", "email": "tech@example.com", "first_name": "Tech", "last_name": "User", "roles": ["Technician"]}
}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "auth-service"}

@app.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    user = USERS.get(login_data.username)
    if not user or user["password"] != login_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create mock token
    token = f"mock-jwt-token-{user['id']}"
    
    user_response = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "roles": user["roles"]
    }
    
    return LoginResponse(
        access_token=token,
        expires_in=1800,
        user=user_response
    )

@app.post("/auth/verify")
async def verify():
    return {"valid": True, "user": {"id": "1", "username": "admin"}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
