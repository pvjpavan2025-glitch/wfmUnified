#!/usr/bin/env python3
"""
Test JWT token compatibility between API Gateway and Dashboard Service.
"""

import asyncio
import httpx
import jwt
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
TENANT_ID = "689b4041eba2c2b9886c1b96"

async def test_jwt_compatibility():
    """Test JWT token compatibility."""
    print("🔐 Testing JWT Token Compatibility")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Get token from API Gateway
            print("1️⃣ Getting token from API Gateway...")
            login_response = await client.post(
                f"{API_BASE_URL}/auth/login",
                json={
                    "username": "admin1",
                    "password": "Admin123!",
                    "tenant_id": TENANT_ID
                }
            )
            
            if login_response.status_code != 200:
                print(f"❌ Login failed: {login_response.status_code}")
                return
            
            login_data = login_response.json()
            token = login_data["access_token"]
            print(f"✅ Got token: {token[:30]}...")
            
            # Try to decode the token with different possible secrets
            print(f"\n2️⃣ Testing token decoding with different secrets...")
            
            possible_secrets = [
                "your-super-secret-jwt-key-change-in-production",  # Default from config
                "wfmv4-super-secret-jwt-key-change-in-production",  # From env.online
                os.environ.get("JWT_SECRET_KEY", ""),  # From environment
            ]
            
            for i, secret in enumerate(possible_secrets, 1):
                if not secret:
                    continue
                    
                print(f"   Testing secret {i}: {secret[:20]}...")
                try:
                    decoded = jwt.decode(token, secret, algorithms=["HS256"])
                    print(f"   ✅ SUCCESS with secret {i}!")
                    print(f"      User ID: {decoded.get('user_id')}")
                    print(f"      Username: {decoded.get('username')}")
                    print(f"      Tenant ID: {decoded.get('tenant_id')}")
                    print(f"      Roles: {decoded.get('roles')}")
                    break
                except jwt.InvalidTokenError as e:
                    print(f"   ❌ Failed with secret {i}: {str(e)}")
            else:
                print("   ❌ No valid secret found!")
            
            # Test token verification with API Gateway
            print(f"\n3️⃣ Testing token verification with API Gateway...")
            verify_response = await client.post(
                f"{API_BASE_URL}/auth/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if verify_response.status_code == 200:
                print("✅ API Gateway accepts the token")
                verify_data = verify_response.json()
                print(f"   User: {verify_data.get('user', {}).get('username')}")
            else:
                print(f"❌ API Gateway rejects the token: {verify_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def main():
    """Main function."""
    await test_jwt_compatibility()

if __name__ == "__main__":
    asyncio.run(main())
