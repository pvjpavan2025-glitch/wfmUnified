#!/usr/bin/env python3
"""
Debug script for auth service
"""
import asyncio
import httpx
import json

async def debug_auth_service():
    """Debug the auth service."""
    async with httpx.AsyncClient() as client:
        # Test all possible endpoints
        endpoints = [
            "/auth/login",
            "/token",
            "/login",
            "/auth/token",
            "/users",
            "/health"
        ]
        
        for endpoint in endpoints:
            print(f"\nTesting {endpoint}...")
            try:
                response = await client.get(f"http://localhost:8000{endpoint}")
                print(f"GET {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"GET {endpoint}: Error - {e}")
            
            try:
                response = await client.post(f"http://localhost:8000{endpoint}")
                print(f"POST {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"POST {endpoint}: Error - {e}")

if __name__ == "__main__":
    asyncio.run(debug_auth_service()) 