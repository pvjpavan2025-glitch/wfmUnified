#!/usr/bin/env python3
"""
Test dashboard metrics endpoint with proper authentication.
"""

import asyncio
import httpx
import json

# Configuration
API_BASE_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:8007"
TENANT_ID = "689b4041eba2c2b9886c1b96"

async def test_dashboard_metrics():
    """Test dashboard metrics with proper authentication."""
    print("🧪 Testing Dashboard Metrics Endpoint")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # First, login to get a token
            print("🔐 Logging in to get JWT token...")
            login_response = await client.post(
                f"{API_BASE_URL}/auth/login",
                json={
                    "username": "admin1",
                    "password": "Admin123!",
                    "tenant_id": TENANT_ID
                }
            )
            
            if login_response.status_code != 200:
                print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
                return
            
            login_data = login_response.json()
            token = login_data["access_token"]
            user_info = login_data["user"]
            
            print(f"✅ Login successful!")
            print(f"   User: {user_info['first_name']} {user_info['last_name']}")
            print(f"   Token: {token[:30]}...")
            
            # Test dashboard metrics endpoint
            print(f"\n📊 Testing dashboard metrics endpoint...")
            headers = {"Authorization": f"Bearer {token}"}
            
            metrics_response = await client.get(
                f"{DASHBOARD_URL}/dashboard/metrics",
                headers=headers
            )
            
            print(f"   Status Code: {metrics_response.status_code}")
            
            if metrics_response.status_code == 200:
                metrics_data = metrics_response.json()
                print("✅ Dashboard metrics retrieved successfully!")
                print(f"   📈 Metrics data:")
                print(json.dumps(metrics_data, indent=4))
            else:
                print(f"❌ Dashboard metrics failed: {metrics_response.text}")
            
            # Test recent jobs endpoint too
            print(f"\n📋 Testing recent jobs endpoint...")
            jobs_response = await client.get(
                f"{DASHBOARD_URL}/dashboard/recent-jobs",
                headers=headers
            )
            
            print(f"   Status Code: {jobs_response.status_code}")
            
            if jobs_response.status_code == 200:
                jobs_data = jobs_response.json()
                print("✅ Recent jobs retrieved successfully!")
                print(f"   📋 Jobs count: {len(jobs_data)}")
                if jobs_data:
                    print(f"   Sample job: {json.dumps(jobs_data[0], indent=4)}")
                else:
                    print("   📭 No recent jobs found")
            else:
                print(f"❌ Recent jobs failed: {jobs_response.text}")
                
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

async def main():
    """Main function."""
    await test_dashboard_metrics()

if __name__ == "__main__":
    asyncio.run(main())
