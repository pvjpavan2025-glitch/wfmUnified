#!/usr/bin/env python3
"""
Comprehensive Authentication and Authorization Test Script
Tests all created users and validates endpoints for different roles.
"""

import asyncio
import httpx
import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Database configuration
MONGODB_URL = "mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB"
DATABASE_NAME = "wfm"

# API endpoints
API_BASE_URL = "http://localhost:8000"
AUTH_SERVICE_URL = "http://localhost:8001"
CONFIG_SERVICE_URL = "http://localhost:8002"
RULES_SERVICE_URL = "http://localhost:8003"
SCHEDULER_SERVICE_URL = "http://localhost:8004"
ISSUE_SERVICE_URL = "http://localhost:8005"
ANALYTICS_SERVICE_URL = "http://localhost:8006"
DASHBOARD_SERVICE_URL = "http://localhost:8007"

class AuthTester:
    """Authentication and Authorization testing class."""
    
    def __init__(self):
        self.tenant_id = None
        self.users = []
        self.test_results = {}
    
    async def get_test_data(self):
        """Get test tenant and users from database."""
        print("📥 Fetching test data from database...")
        
        try:
            client = AsyncIOMotorClient(MONGODB_URL)
            db = client[DATABASE_NAME]
            
            # Get test tenant
            tenant = await db.tenants.find_one({"name": "Test Organization"})
            if not tenant:
                raise Exception("Test tenant not found. Please run reset_and_create_test_data.py first")
            
            self.tenant_id = str(tenant["_id"])
            print(f"✅ Found test tenant: {tenant['name']} (ID: {self.tenant_id})")
            
            # Get all test users
            users_cursor = db.users.find({"tenant_id": ObjectId(self.tenant_id)})
            async for user in users_cursor:
                # Get user roles
                role_names = []
                if user.get('role_ids'):
                    role_cursor = db.roles.find({"_id": {"$in": user['role_ids']}})
                    role_names = [role['name'] async for role in role_cursor]
                
                self.users.append({
                    "username": user["username"],
                    "email": user["email"],
                    "first_name": user["first_name"],
                    "last_name": user["last_name"],
                    "roles": role_names,
                    "status": user["status"]
                })
            
            print(f"✅ Found {len(self.users)} test users")
            for user in self.users:
                print(f"   - {user['username']} ({', '.join(user['roles'])})")
            
            return True
            
        except Exception as e:
            print(f"❌ Error fetching test data: {str(e)}")
            return False
    
    async def test_user_authentication(self, username):
        """Test authentication for a specific user."""
        print(f"\n🔐 Testing authentication for user: {username}")
        
        # Find user data
        user_data = None
        for user in self.users:
            if user["username"] == username:
                user_data = user
                break
        
        if not user_data:
            print(f"❌ User {username} not found in test data")
            return None
        
        # Determine password based on role
        password = "Admin123!" if "admin" in user_data["roles"] else \
                  "Tech123!" if "technician" in user_data["roles"] else \
                  "Vendor123!" if "vendor" in user_data["roles"] else None
        
        if not password:
            print(f"❌ Could not determine password for user {username}")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test login
                login_response = await client.post(
                    f"{API_BASE_URL}/auth/login",
                    json={
                        "username": username,
                        "password": password,
                        "tenant_id": self.tenant_id
                    }
                )
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    token = login_data["access_token"]
                    user_info = login_data["user"]
                    
                    print(f"✅ Login successful for {username}")
                    print(f"   Token: {token[:50]}...")
                    print(f"   User: {user_info['first_name']} {user_info['last_name']}")
                    print(f"   Roles: {user_info.get('roles', [])}")
                    
                    return {
                        "token": token,
                        "user": user_info,
                        "roles": user_data["roles"]
                    }
                else:
                    print(f"❌ Login failed for {username}: {login_response.status_code} - {login_response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Authentication error for {username}: {str(e)}")
            return None
    
    async def test_endpoint_access(self, auth_data, endpoint_name, url, method="GET", data=None):
        """Test access to a specific endpoint."""
        print(f"   Testing {method} {endpoint_name}...")
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = {"Authorization": f"Bearer {auth_data['token']}"}
                
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data or {})
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data or {})
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    print(f"   ❌ Unsupported method: {method}")
                    return False
                
                if response.status_code < 400:
                    print(f"   ✅ {endpoint_name}: {response.status_code}")
                    return True
                elif response.status_code == 401:
                    print(f"   🔒 {endpoint_name}: Authentication failed ({response.status_code})")
                    return False
                elif response.status_code == 403:
                    print(f"   🚫 {endpoint_name}: Authorization denied ({response.status_code})")
                    return False
                elif response.status_code == 404:
                    print(f"   📭 {endpoint_name}: Not found ({response.status_code})")
                    return False
                else:
                    print(f"   ⚠️ {endpoint_name}: {response.status_code} - {response.text[:100]}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ {endpoint_name}: Error - {str(e)}")
            return False
    
    async def test_user_endpoints(self, auth_data):
        """Test all relevant endpoints for a user based on their role."""
        username = auth_data["user"]["username"]
        roles = auth_data["roles"]
        
        print(f"\n🧪 Testing endpoints for {username} (Roles: {', '.join(roles)})")
        
        results = {
            "authentication": [],
            "user_management": [],
            "config_management": [],
            "rules_management": [],
            "scheduler": [],
            "issues": [],
            "analytics": [],
            "dashboard": []
        }
        
        # Authentication endpoints (all users should have access)
        print(f"\n📋 Testing Authentication endpoints:")
        results["authentication"].append(
            await self.test_endpoint_access(auth_data, "Token Verification", f"{API_BASE_URL}/auth/verify", "POST")
        )
        results["authentication"].append(
            await self.test_endpoint_access(auth_data, "Get Current User", f"{AUTH_SERVICE_URL}/users/me")
        )
        
        # User management endpoints (admin should have full access, others limited)
        print(f"\n👥 Testing User Management endpoints:")
        results["user_management"].append(
            await self.test_endpoint_access(auth_data, "List Users", f"{AUTH_SERVICE_URL}/users")
        )
        results["user_management"].append(
            await self.test_endpoint_access(auth_data, "Get User Profile", f"{AUTH_SERVICE_URL}/users/{auth_data['user']['id']}")
        )
        
        if "admin" in roles:
            # Admin-specific endpoints
            results["user_management"].append(
                await self.test_endpoint_access(auth_data, "Create User", f"{AUTH_SERVICE_URL}/users", "POST", {
                    "username": "test_temp_user",
                    "email": "temp@test.com",
                    "password": "TempPass123!",
                    "first_name": "Temp",
                    "last_name": "User",
                    "tenant_id": self.tenant_id,
                    "role_ids": []
                })
            )
        
        # Config management endpoints
        print(f"\n⚙️ Testing Configuration endpoints:")
        results["config_management"].append(
            await self.test_endpoint_access(auth_data, "Get Configs", f"{CONFIG_SERVICE_URL}/configs")
        )
        
        if "admin" in roles:
            results["config_management"].append(
                await self.test_endpoint_access(auth_data, "Create Config", f"{CONFIG_SERVICE_URL}/configs", "POST", {
                    "name": "test_config",
                    "value": "test_value",
                    "description": "Test configuration"
                })
            )
        
        # Rules management endpoints
        print(f"\n📏 Testing Rules endpoints:")
        results["rules_management"].append(
            await self.test_endpoint_access(auth_data, "Get Rules", f"{RULES_SERVICE_URL}/rules")
        )
        
        # Scheduler endpoints
        print(f"\n⏰ Testing Scheduler endpoints:")
        results["scheduler"].append(
            await self.test_endpoint_access(auth_data, "Get Jobs", f"{SCHEDULER_SERVICE_URL}/jobs")
        )
        
        if "technician" in roles or "admin" in roles:
            results["scheduler"].append(
                await self.test_endpoint_access(auth_data, "Get My Jobs", f"{SCHEDULER_SERVICE_URL}/jobs/my")
            )
        
        # Issue management endpoints
        print(f"\n🐛 Testing Issue endpoints:")
        results["issues"].append(
            await self.test_endpoint_access(auth_data, "Get Issues", f"{ISSUE_SERVICE_URL}/issues")
        )
        
        if "technician" in roles or "admin" in roles:
            results["issues"].append(
                await self.test_endpoint_access(auth_data, "Create Issue", f"{ISSUE_SERVICE_URL}/issues", "POST", {
                    "title": "Test Issue",
                    "description": "Test issue description",
                    "priority": "medium"
                })
            )
        
        # Analytics endpoints
        print(f"\n📊 Testing Analytics endpoints:")
        results["analytics"].append(
            await self.test_endpoint_access(auth_data, "Get Analytics", f"{ANALYTICS_SERVICE_URL}/analytics")
        )
        
        # Dashboard endpoints
        print(f"\n📈 Testing Dashboard endpoints:")
        results["dashboard"].append(
            await self.test_endpoint_access(auth_data, "Get Dashboard Metrics", f"{DASHBOARD_SERVICE_URL}/dashboard/metrics")
        )
        
        return results
    
    async def run_comprehensive_test(self):
        """Run comprehensive authentication and authorization tests."""
        print("🧪 Starting Comprehensive Authentication & Authorization Tests")
        print("=" * 80)
        
        # Get test data
        if not await self.get_test_data():
            return
        
        # Test each user type
        test_users = [
            ("admin1", "admin"),
            ("tech1", "technician"),
            ("vendor1", "vendor")
        ]
        
        for username, expected_role in test_users:
            print(f"\n{'='*20} TESTING {username.upper()} ({expected_role.upper()}) {'='*20}")
            
            # Test authentication
            auth_data = await self.test_user_authentication(username)
            if not auth_data:
                continue
            
            # Test endpoints
            endpoint_results = await self.test_user_endpoints(auth_data)
            
            # Store results
            self.test_results[username] = {
                "auth_data": auth_data,
                "endpoint_results": endpoint_results
            }
        
        # Generate summary
        await self.generate_test_summary()
    
    async def generate_test_summary(self):
        """Generate a summary of test results."""
        print(f"\n{'='*80}")
        print("📋 TEST SUMMARY")
        print(f"{'='*80}")
        
        for username, results in self.test_results.items():
            auth_data = results["auth_data"]
            endpoint_results = results["endpoint_results"]
            
            print(f"\n👤 User: {username} ({', '.join(auth_data['roles'])})")
            print(f"   Authentication: ✅ Success")
            
            for category, test_results in endpoint_results.items():
                success_count = sum(1 for result in test_results if result)
                total_count = len(test_results)
                if total_count > 0:
                    status = "✅" if success_count == total_count else "⚠️" if success_count > 0 else "❌"
                    print(f"   {category.replace('_', ' ').title()}: {status} {success_count}/{total_count}")
        
        print(f"\n🎉 Comprehensive testing completed!")
        print(f"📝 Total users tested: {len(self.test_results)}")
        
        # Role-based permissions summary
        print(f"\n📊 ROLE-BASED ACCESS SUMMARY:")
        print(f"   🔴 Admin: Should have access to all endpoints")
        print(f"   🟡 Technician: Should have limited access (jobs, issues, profile)")
        print(f"   🟢 Vendor: Should have basic access (profile, vendor-specific endpoints)")

async def main():
    """Main function."""
    print("🚀 Starting WFM Authentication & Authorization Test Suite")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = AuthTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
