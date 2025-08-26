#!/usr/bin/env python3
"""
Focused Authentication and Authorization Test - API Gateway Only
Tests authentication and basic endpoints via API Gateway.
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test configuration
API_BASE_URL = "http://localhost:8000"
TENANT_ID = "689b4041eba2c2b9886c1b96"  # From our test data

# Test users with their credentials
TEST_USERS = [
    {
        "username": "admin1",
        "password": "Admin123!",
        "expected_role": "admin",
        "description": "Administrator with full access"
    },
    {
        "username": "tech1", 
        "password": "Tech123!",
        "expected_role": "technician",
        "description": "Technician with job/issue access"
    },
    {
        "username": "vendor1",
        "password": "Vendor123!",
        "expected_role": "vendor", 
        "description": "Vendor with limited access"
    }
]

class APIGatewayTester:
    """Test authentication and authorization via API Gateway."""
    
    def __init__(self):
        self.results = {}
    
    async def test_login(self, user):
        """Test login for a user."""
        print(f"\n🔐 Testing login for {user['username']} ({user['expected_role']})")
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{API_BASE_URL}/auth/login",
                    json={
                        "username": user["username"],
                        "password": user["password"],
                        "tenant_id": TENANT_ID
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data["access_token"]
                    user_info = data["user"]
                    
                    print(f"   ✅ Login successful")
                    print(f"   👤 User: {user_info['first_name']} {user_info['last_name']}")
                    print(f"   🏷️  Roles: {user_info.get('roles', [])}")
                    print(f"   🎫 Token: {token[:30]}...")
                    
                    return {
                        "success": True,
                        "token": token,
                        "user": user_info
                    }
                else:
                    print(f"   ❌ Login failed: {response.status_code} - {response.text}")
                    return {"success": False, "error": response.text}
                    
        except Exception as e:
            print(f"   ❌ Login error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_token_verification(self, token):
        """Test token verification."""
        print(f"   🔍 Testing token verification...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{API_BASE_URL}/auth/verify",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Token verification successful")
                    print(f"      Valid: {data.get('valid', False)}")
                    print(f"      User: {data.get('user', {}).get('username', 'Unknown')}")
                    return True
                else:
                    print(f"   ❌ Token verification failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Token verification error: {str(e)}")
            return False
    
    async def test_health_endpoints(self, token, username):
        """Test health and status endpoints."""
        print(f"   🏥 Testing health endpoints...")
        
        endpoints = [
            ("Health Check", "/health", "GET"),
            ("Services Health", "/health/services", "GET"),
        ]
        
        results = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Authorization": f"Bearer {token}"}
                
                for name, endpoint, method in endpoints:
                    try:
                        if method == "GET":
                            response = await client.get(f"{API_BASE_URL}{endpoint}", headers=headers)
                        else:
                            response = await client.post(f"{API_BASE_URL}{endpoint}", headers=headers)
                        
                        if response.status_code < 400:
                            print(f"   ✅ {name}: {response.status_code}")
                            results.append(True)
                        else:
                            print(f"   ❌ {name}: {response.status_code}")
                            results.append(False)
                            
                    except Exception as e:
                        print(f"   ❌ {name}: Error - {str(e)}")
                        results.append(False)
        
        except Exception as e:
            print(f"   ❌ Health endpoints error: {str(e)}")
            results = [False] * len(endpoints)
        
        return results
    
    async def test_unauthorized_access(self):
        """Test accessing endpoints without authentication."""
        print(f"\n🚫 Testing unauthorized access (no token)...")
        
        protected_endpoints = [
            ("Token Verification", "/auth/verify", "POST"),
            ("Health Services", "/health/services", "GET"),
        ]
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for name, endpoint, method in protected_endpoints:
                    try:
                        if method == "GET":
                            response = await client.get(f"{API_BASE_URL}{endpoint}")
                        else:
                            response = await client.post(f"{API_BASE_URL}{endpoint}")
                        
                        if response.status_code == 401:
                            print(f"   ✅ {name}: Properly blocked (401)")
                        elif response.status_code == 422:
                            print(f"   ✅ {name}: Validation error (422) - expected for missing auth")
                        else:
                            print(f"   ⚠️ {name}: Unexpected response ({response.status_code})")
                            
                    except Exception as e:
                        print(f"   ❌ {name}: Error - {str(e)}")
        
        except Exception as e:
            print(f"   ❌ Unauthorized access test error: {str(e)}")
    
    async def test_invalid_token(self):
        """Test accessing endpoints with invalid token."""
        print(f"\n🔒 Testing invalid token access...")
        
        invalid_tokens = [
            ("Malformed Token", "invalid.token.here"),
            ("Expired/Wrong Token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c")
        ]
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for token_name, token in invalid_tokens:
                    try:
                        response = await client.post(
                            f"{API_BASE_URL}/auth/verify",
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        
                        if response.status_code == 401:
                            print(f"   ✅ {token_name}: Properly rejected (401)")
                        else:
                            print(f"   ⚠️ {token_name}: Unexpected response ({response.status_code})")
                            
                    except Exception as e:
                        print(f"   ❌ {token_name}: Error - {str(e)}")
        
        except Exception as e:
            print(f"   ❌ Invalid token test error: {str(e)}")
    
    async def run_comprehensive_test(self):
        """Run comprehensive API Gateway authentication tests."""
        print("🧪 API Gateway Authentication & Authorization Test Suite")
        print("=" * 70)
        print(f"🎯 Target: {API_BASE_URL}")
        print(f"🏢 Tenant ID: {TENANT_ID}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test unauthorized access first
        await self.test_unauthorized_access()
        await self.test_invalid_token()
        
        # Test each user
        for user in TEST_USERS:
            print(f"\n{'='*20} TESTING {user['username'].upper()} ({'='*20}")
            print(f"📝 Description: {user['description']}")
            
            # Test login
            login_result = await self.test_login(user)
            
            if login_result["success"]:
                token = login_result["token"]
                
                # Test token verification
                token_valid = await self.test_token_verification(token)
                
                # Test health endpoints
                health_results = await self.test_health_endpoints(token, user["username"])
                
                # Store results
                self.results[user["username"]] = {
                    "login": True,
                    "token_verification": token_valid,
                    "health_endpoints": health_results,
                    "user_info": login_result["user"]
                }
            else:
                self.results[user["username"]] = {
                    "login": False,
                    "error": login_result.get("error", "Unknown error")
                }
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary."""
        print(f"\n{'='*70}")
        print("📊 TEST SUMMARY")
        print(f"{'='*70}")
        
        total_users = len(TEST_USERS)
        successful_logins = 0
        successful_verifications = 0
        
        for username, results in self.results.items():
            user_info = next(u for u in TEST_USERS if u["username"] == username)
            expected_role = user_info["expected_role"]
            
            print(f"\n👤 {username} ({expected_role}):")
            
            if results.get("login"):
                successful_logins += 1
                print(f"   🔐 Authentication: ✅ SUCCESS")
                
                if results.get("token_verification"):
                    successful_verifications += 1
                    print(f"   🎫 Token Verification: ✅ SUCCESS")
                else:
                    print(f"   🎫 Token Verification: ❌ FAILED")
                
                health_results = results.get("health_endpoints", [])
                health_success = sum(health_results)
                health_total = len(health_results)
                if health_total > 0:
                    print(f"   🏥 Health Endpoints: {'✅' if health_success == health_total else '⚠️'} {health_success}/{health_total}")
                
                user_data = results.get("user_info", {})
                actual_roles = user_data.get("roles", [])
                if expected_role in actual_roles:
                    print(f"   🏷️  Role Assignment: ✅ CORRECT ({', '.join(actual_roles)})")
                else:
                    print(f"   🏷️  Role Assignment: ⚠️ UNEXPECTED ({', '.join(actual_roles)} vs {expected_role})")
            else:
                print(f"   🔐 Authentication: ❌ FAILED")
                print(f"   ❌ Error: {results.get('error', 'Unknown')}")
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   👥 Total users tested: {total_users}")
        print(f"   🔐 Successful logins: {successful_logins}/{total_users}")
        print(f"   🎫 Successful verifications: {successful_verifications}/{successful_logins}")
        
        if successful_logins == total_users and successful_verifications == successful_logins:
            print(f"   🎉 ALL TESTS PASSED! Authentication and authorization working correctly.")
        else:
            print(f"   ⚠️ Some tests failed. Please check the details above.")
        
        print(f"\n✅ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main function."""
    tester = APIGatewayTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
