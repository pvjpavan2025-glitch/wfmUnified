#!/usr/bin/env python3
"""
Simple test script for auth service
"""
import asyncio
import httpx
import json

async def test_auth_service():
    """Test the auth service endpoints."""
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("Testing health endpoint...")
        response = await client.get("http://localhost:8000/health")
        print(f"Health response: {response.status_code} - {response.text}")
        
        # Test login endpoint
        print("\nTesting login endpoint...")
        login_data = {
            "username": "admin",
            "password": "admin123",
            "tenant_id": "default"
        }
        response = await client.post(
            "http://localhost:8000/auth/login",
            json=login_data
        )
        print(f"Login response: {response.status_code} - {response.text}")
        
        # Test available endpoints
        print("\nTesting available endpoints...")
        response = await client.get("http://localhost:8000/openapi.json")
        if response.status_code == 200:
            spec = response.json()
            print("Available endpoints:")
            for path in spec.get("paths", {}).keys():
                print(f"  {path}")

if __name__ == "__main__":
    asyncio.run(test_auth_service()) 