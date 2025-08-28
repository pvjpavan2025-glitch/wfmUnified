#!/usr/bin/env python3
"""
Test dashboard metrics using API Gateway proxy instead of direct service call.
"""

import asyncio
import httpx

# Configuration
API_BASE_URL = "http://localhost:8000"
TENANT_ID = "689b4041eba2c2b9886c1b96"

async def test_dashboard_via_gateway():
    """Test dashboard metrics via API Gateway."""
    print("🌐 Testing Dashboard Metrics via API Gateway")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Login first
            print("🔐 Logging in...")
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
            print(f"✅ Login successful, token: {token[:30]}...")
            
            # Test if API Gateway has any dashboard routes
            print(f"\n🔍 Testing various endpoints...")
            headers = {"Authorization": f"Bearer {token}"}
            
            test_endpoints = [
                ("Health Check", f"{API_BASE_URL}/health", "GET"),
                ("Services Health", f"{API_BASE_URL}/health/services", "GET"),
                ("Token Verify", f"{API_BASE_URL}/auth/verify", "POST"),
                ("Direct Dashboard Test", "http://localhost:8007/dashboard/metrics-test", "GET"),
                ("Direct Dashboard", "http://localhost:8007/dashboard/metrics", "GET"),
            ]
            
            for name, url, method in test_endpoints:
                try:
                    if method == "GET":
                        if "localhost:8007" not in url:
                            response = await client.get(url, headers=headers)
                        else:
                            response = await client.get(url, headers=headers)
                    else:
                        if "localhost:8007" not in url:
                            response = await client.post(url, headers=headers)
                        else:
                            response = await client.post(url, headers=headers)
                    
                    print(f"   {name}: {response.status_code}")
                    if response.status_code < 400:
                        print(f"      ✅ Success")
                        if "metrics" in url and response.status_code == 200:
                            try:
                                data = response.json()
                                print(f"      📊 Data keys: {list(data.keys())}")
                            except:
                                print(f"      📄 Response: {response.text[:100]}")
                    else:
                        print(f"      ❌ Error: {response.text[:100]}")
                        
                except Exception as e:
                    print(f"   {name}: ❌ Exception - {str(e)}")
                    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def main():
    """Main function."""
    await test_dashboard_via_gateway()

if __name__ == "__main__":
    asyncio.run(main())
