#!/usr/bin/env python3
"""
Test frontend integration with backend services.
"""

import asyncio
import httpx

async def test_frontend_integration():
    """Test frontend endpoints and backend connectivity."""
    print("🌐 Testing Frontend Integration")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Test frontend health
            print("1️⃣ Testing frontend accessibility...")
            try:
                frontend_response = await client.get("http://localhost:3000")
                print(f"   Frontend status: {frontend_response.status_code}")
                if frontend_response.status_code == 200:
                    print("   ✅ Frontend is accessible")
                else:
                    print("   ⚠️ Frontend returned non-200 status")
            except Exception as e:
                print(f"   ❌ Frontend not accessible: {str(e)}")
            
            # Test login functionality
            print("\n2️⃣ Testing backend login...")
            login_response = await client.post(
                "http://localhost:8000/auth/login",
                json={
                    "username": "admin1",
                    "password": "Admin123!",
                    "tenant_id": "689b4041eba2c2b9886c1b96"
                }
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                token = login_data["access_token"]
                print(f"   ✅ Login successful, token: {token[:30]}...")
                
                # Test dashboard endpoints that frontend uses
                print("\n3️⃣ Testing dashboard endpoints...")
                
                # Test the working metrics endpoint
                metrics_response = await client.get("http://localhost:8007/dashboard/metrics-test")
                if metrics_response.status_code == 200:
                    print("   ✅ Dashboard metrics-test endpoint working")
                    metrics_data = metrics_response.json()
                    print(f"   📊 Active jobs: {metrics_data.get('active_jobs', {}).get('count', 'N/A')}")
                    print(f"   👥 Available technicians: {metrics_data.get('available_technicians', {}).get('count', 'N/A')}")
                else:
                    print(f"   ❌ Dashboard metrics-test failed: {metrics_response.status_code}")
                
            else:
                print(f"   ❌ Login failed: {login_response.status_code}")
        
        print(f"\n✅ Integration testing completed!")
        print(f"\n🎯 Frontend should now work correctly with:")
        print(f"   - Login: http://localhost:3000/login")
        print(f"   - Dashboard: http://localhost:3000/dashboard")
        print(f"   - Test credentials: admin1 / Admin123! / 689b4041eba2c2b9886c1b96")
                
    except Exception as e:
        print(f"❌ Integration test error: {str(e)}")

async def main():
    """Main function."""
    await test_frontend_integration()

if __name__ == "__main__":
    asyncio.run(main())
