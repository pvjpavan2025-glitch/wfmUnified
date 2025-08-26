#!/usr/bin/env python3
"""
Comprehensive endpoint testing script for WFM service with online database.
Tests all endpoints including authorization.
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
AUTH_SERVICE_URL = "http://localhost:8001"
CONFIG_SERVICE_URL = "http://localhost:8002"
RULES_SERVICE_URL = "http://localhost:8003"
SCHEDULER_SERVICE_URL = "http://localhost:8004"
ISSUE_SERVICE_URL = "http://localhost:8005"
ANALYTICS_SERVICE_URL = "http://localhost:8006"

# Test data
TEST_TENANT_ID = "6899f993b9032cd7d152b90c"  # Actual tenant ID from database
TEST_USER_DATA = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPassword123!",
    "first_name": "Test",
    "last_name": "User",
    "tenant_id": TEST_TENANT_ID,
    "status": "active"
}

TEST_CONFIG_DATA = {
    "key": "test_config",
    "value": "test_value",
    "tenant_id": TEST_TENANT_ID,
    "description": "Test configuration"
}

TEST_RULE_DATA = {
    "name": "test_rule",
    "description": "Test rule for testing",
    "tenant_id": TEST_TENANT_ID,
    "conditions": {"field": "status", "operator": "equals", "value": "active"},
    "actions": {"action": "notify", "target": "manager"}
}

TEST_JOB_DATA = {
    "name": "test_job",
    "description": "Test job for testing",
    "tenant_id": TEST_TENANT_ID,
    "schedule": "0 9 * * 1-5",  # Weekdays at 9 AM
    "status": "active"
}

TEST_ISSUE_DATA = {
    "title": "Test Issue",
    "description": "Test issue for testing",
    "tenant_id": TEST_TENANT_ID,
    "priority": "medium",
    "status": "open"
}

class EndpointTester:
    """Comprehensive endpoint tester for WFM service."""
    
    def __init__(self):
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.test_results = []
        
    async def log_test(self, endpoint: str, method: str, success: bool, details: str = ""):
        """Log test result."""
        result = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "success": success,
            "details": details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {method} {endpoint} - {details}")
    
    async def test_health_endpoints(self):
        """Test health check endpoints."""
        print("\n🔍 Testing Health Endpoints...")
        
        async with httpx.AsyncClient() as client:
            # API Gateway health
            try:
                response = await client.get(f"{BASE_URL}/health")
                await self.log_test("/health", "GET", response.status_code == 200, 
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/health", "GET", False, f"Error: {str(e)}")
            
            # Services health
            try:
                response = await client.get(f"{BASE_URL}/health/services")
                await self.log_test("/health/services", "GET", response.status_code == 200,
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/health/services", "GET", False, f"Error: {str(e)}")
            
            # Individual service health checks
            services = [
                ("auth", AUTH_SERVICE_URL),
                ("config", CONFIG_SERVICE_URL),
                ("rules", RULES_SERVICE_URL),
                ("scheduler", SCHEDULER_SERVICE_URL),
                ("issue", ISSUE_SERVICE_URL),
                ("analytics", ANALYTICS_SERVICE_URL)
            ]
            
            for service_name, service_url in services:
                try:
                    response = await client.get(f"{service_url}/health")
                    await self.log_test(f"{service_name}/health", "GET", 
                                      response.status_code == 200,
                                      f"Status: {response.status_code}")
                except Exception as e:
                    await self.log_test(f"{service_name}/health", "GET", False, 
                                      f"Error: {str(e)}")
    
    async def test_auth_endpoints(self):
        """Test authentication endpoints."""
        print("\n🔐 Testing Authentication Endpoints...")
        
        async with httpx.AsyncClient() as client:
            # Test login without valid credentials (should fail)
            try:
                response = await client.post(f"{BASE_URL}/auth/login", json={
                    "username": "nonexistent",
                    "password": "wrong",
                    "tenant_id": TEST_TENANT_ID
                })
                await self.log_test("/auth/login", "POST", response.status_code == 401,
                                  f"Expected 401, got {response.status_code}")
            except Exception as e:
                await self.log_test("/auth/login", "POST", False, f"Error: {str(e)}")
            
            # Test login with valid credentials (if user exists)
            try:
                response = await client.post(f"{BASE_URL}/auth/login", json=TEST_USER_DATA)
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    self.user_id = data.get("user", {}).get("id")
                    await self.log_test("/auth/login", "POST", True, "Login successful")
                else:
                    await self.log_test("/auth/login", "POST", False, 
                                      f"Login failed: {response.status_code}")
            except Exception as e:
                await self.log_test("/auth/login", "POST", False, f"Error: {str(e)}")
            
            # Test token verification
            if self.access_token:
                try:
                    response = await client.post(f"{BASE_URL}/auth/verify", 
                                               headers={"Authorization": f"Bearer {self.access_token}"})
                    await self.log_test("/auth/verify", "POST", response.status_code == 200,
                                      f"Status: {response.status_code}")
                except Exception as e:
                    await self.log_test("/auth/verify", "POST", False, f"Error: {str(e)}")
            else:
                await self.log_test("/auth/verify", "POST", False, "No token available")
    
    async def test_user_endpoints(self):
        """Test user management endpoints."""
        print("\n👥 Testing User Management Endpoints...")
        
        if not self.access_token:
            await self.log_test("/users", "POST", False, "No token available")
            return
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create user
            try:
                response = await client.post(f"{BASE_URL}/users", 
                                           json=TEST_USER_DATA,
                                           headers=headers)
                await self.log_test("/users", "POST", response.status_code in [200, 201, 400],
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/users", "POST", False, f"Error: {str(e)}")
            
            # List users
            try:
                response = await client.get(f"{BASE_URL}/users", headers=headers)
                await self.log_test("/users", "GET", response.status_code == 200,
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/users", "GET", False, f"Error: {str(e)}")
            
            # Get specific user (if we have a user ID)
            if self.user_id:
                try:
                    response = await client.get(f"{BASE_URL}/users/{self.user_id}", 
                                              headers=headers)
                    await self.log_test(f"/users/{self.user_id}", "GET", 
                                      response.status_code in [200, 404],
                                      f"Status: {response.status_code}")
                except Exception as e:
                    await self.log_test(f"/users/{self.user_id}", "GET", False, 
                                      f"Error: {str(e)}")
    
    async def test_config_endpoints(self):
        """Test configuration endpoints."""
        print("\n⚙️ Testing Configuration Endpoints...")
        
        if not self.access_token:
            await self.log_test("/configs", "POST", False, "No token available")
            return
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create config
            try:
                response = await client.post(f"{BASE_URL}/configs", 
                                           json=TEST_CONFIG_DATA,
                                           headers=headers)
                await self.log_test("/configs", "POST", response.status_code in [200, 201, 400],
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/configs", "POST", False, f"Error: {str(e)}")
            
            # List configs
            try:
                response = await client.get(f"{BASE_URL}/configs", headers=headers)
                await self.log_test("/configs", "GET", response.status_code == 200,
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/configs", "GET", False, f"Error: {str(e)}")
    
    async def test_rules_endpoints(self):
        """Test rules endpoints."""
        print("\n📋 Testing Rules Endpoints...")
        
        if not self.access_token:
            await self.log_test("/rules", "POST", False, "No token available")
            return
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create rule
            try:
                response = await client.post(f"{BASE_URL}/rules", 
                                           json=TEST_RULE_DATA,
                                           headers=headers)
                await self.log_test("/rules", "POST", response.status_code in [200, 201, 400],
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/rules", "POST", False, f"Error: {str(e)}")
            
            # List rules
            try:
                response = await client.get(f"{BASE_URL}/rules", headers=headers)
                await self.log_test("/rules", "GET", response.status_code == 200,
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/rules", "GET", False, f"Error: {str(e)}")
            
            # Evaluate rules
            try:
                response = await client.post(f"{BASE_URL}/rules/evaluate", 
                                           json={"data": {"status": "active"}},
                                           headers=headers)
                await self.log_test("/rules/evaluate", "POST", response.status_code in [200, 400],
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/rules/evaluate", "POST", False, f"Error: {str(e)}")
    
    async def test_scheduler_endpoints(self):
        """Test scheduler endpoints."""
        print("\n⏰ Testing Scheduler Endpoints...")
        
        if not self.access_token:
            await self.log_test("/jobs", "POST", False, "No token available")
            return
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create job
            try:
                response = await client.post(f"{BASE_URL}/jobs", 
                                           json=TEST_JOB_DATA,
                                           headers=headers)
                await self.log_test("/jobs", "POST", response.status_code in [200, 201, 400],
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/jobs", "POST", False, f"Error: {str(e)}")
            
            # List jobs
            try:
                response = await client.get(f"{BASE_URL}/jobs", headers=headers)
                await self.log_test("/jobs", "GET", response.status_code == 200,
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/jobs", "GET", False, f"Error: {str(e)}")
    
    async def test_issue_endpoints(self):
        """Test issue endpoints."""
        print("\n🐛 Testing Issue Endpoints...")
        
        if not self.access_token:
            await self.log_test("/issues", "POST", False, "No token available")
            return
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create issue
            try:
                response = await client.post(f"{BASE_URL}/issues", 
                                           json=TEST_ISSUE_DATA,
                                           headers=headers)
                await self.log_test("/issues", "POST", response.status_code in [200, 201, 400],
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/issues", "POST", False, f"Error: {str(e)}")
            
            # List issues
            try:
                response = await client.get(f"{BASE_URL}/issues", headers=headers)
                await self.log_test("/issues", "GET", response.status_code == 200,
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/issues", "GET", False, f"Error: {str(e)}")
    
    async def test_analytics_endpoints(self):
        """Test analytics endpoints."""
        print("\n📊 Testing Analytics Endpoints...")
        
        if not self.access_token:
            await self.log_test("/reports", "GET", False, "No token available")
            return
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # List reports
            try:
                response = await client.get(f"{BASE_URL}/reports", headers=headers)
                await self.log_test("/reports", "GET", response.status_code == 200,
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/reports", "GET", False, f"Error: {str(e)}")
            
            # Get metrics
            try:
                response = await client.get(f"{BASE_URL}/metrics", headers=headers)
                await self.log_test("/metrics", "GET", response.status_code == 200,
                                  f"Status: {response.status_code}")
            except Exception as e:
                await self.log_test("/metrics", "GET", False, f"Error: {str(e)}")
    
    async def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints."""
        print("\n🚫 Testing Unauthorized Access...")
        
        async with httpx.AsyncClient() as client:
            # Try to access protected endpoint without token
            try:
                response = await client.get(f"{BASE_URL}/users")
                await self.log_test("/users (no auth)", "GET", response.status_code == 401,
                                  f"Expected 401, got {response.status_code}")
            except Exception as e:
                await self.log_test("/users (no auth)", "GET", False, f"Error: {str(e)}")
            
            # Try with invalid token
            try:
                response = await client.get(f"{BASE_URL}/users", 
                                          headers={"Authorization": "Bearer invalid_token"})
                await self.log_test("/users (invalid token)", "GET", response.status_code == 401,
                                  f"Expected 401, got {response.status_code}")
            except Exception as e:
                await self.log_test("/users (invalid token)", "GET", False, f"Error: {str(e)}")
    
    async def run_all_tests(self):
        """Run all endpoint tests."""
        print("🚀 Starting Comprehensive Endpoint Testing...")
        print(f"📅 Test started at: {datetime.now().isoformat()}")
        print(f"🌐 Base URL: {BASE_URL}")
        print(f"🔗 Using online database configuration")
        
        start_time = time.time()
        
        # Run all test suites
        await self.test_health_endpoints()
        await self.test_auth_endpoints()
        await self.test_user_endpoints()
        await self.test_config_endpoints()
        await self.test_rules_endpoints()
        await self.test_scheduler_endpoints()
        await self.test_issue_endpoints()
        await self.test_analytics_endpoints()
        await self.test_unauthorized_access()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏱️ Duration: {duration:.2f} seconds")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['method']} {result['endpoint']}: {result['details']}")
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "duration": duration,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: test_results.json")
        print("="*60)

async def main():
    """Main function."""
    tester = EndpointTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
