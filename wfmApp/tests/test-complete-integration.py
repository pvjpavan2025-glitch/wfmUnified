#!/usr/bin/env python3
"""
Complete Integration Test Script for WFM System
This script tests both backend connectivity and frontend integration
"""

import requests
import json
import time
from urllib.parse import quote_plus

def test_backend_health():
    """Test backend service health"""
    print("🔍 Testing Backend Services...")
    
    try:
        # Test API Gateway health
        response = requests.get('http://localhost:8000/health', timeout=10)
        if response.status_code == 200:
            print("✅ API Gateway: Healthy")
            return True
        else:
            print(f"❌ API Gateway: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API Gateway: Connection failed - {e}")
        return False

def test_mongodb_connection():
    """Test online MongoDB connection"""
    print("\n🗄️  Testing Online MongoDB Connection...")
    
    try:
        from pymongo import MongoClient
        
        # MongoDB connection details
        username = "wfmadmin"
        password = "tsarolabs@12345#"
        cluster_url = "wfmdb.cvkb04l.mongodb.net"
        database_name = "wfm"
        
        # URL-encode the password
        encoded_password = quote_plus(password)
        connection_string = f"mongodb+srv://{username}:{encoded_password}@{cluster_url}/?retryWrites=true&w=majority&appName=wfmDB"
        
        # Create MongoDB client
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=10000,
            ssl=True,
            tlsAllowInvalidCertificates=True,
            retryWrites=True,
            w='majority'
        )
        
        # Test connection
        client.admin.command('ping')
        db = client[database_name]
        
        # Check collections
        collections = db.list_collection_names()
        print(f"✅ MongoDB: Connected successfully")
        print(f"📊 Database: {database_name}")
        print(f"📁 Collections: {collections}")
        
        # Check test user
        user = db.users.find_one({"username": "testuser"})
        if user:
            print(f"✅ Test user found: {user['username']}")
            print(f"   - Tenant ID: {user['tenant_id']}")
            print(f"   - Role IDs: {user['role_ids']}")
        else:
            print("❌ Test user not found")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB: Connection failed - {e}")
        return False

def test_frontend_connectivity():
    """Test frontend accessibility"""
    print("\n🌐 Testing Frontend Connectivity...")
    
    try:
        # Test Next.js frontend
        response = requests.get('http://localhost:3001', timeout=10)
        if response.status_code == 200:
            print("✅ Frontend: Accessible at http://localhost:3001")
            return True
        else:
            print(f"❌ Frontend: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend: Connection failed - {e}")
        return False

def test_authentication_flow():
    """Test the complete authentication flow"""
    print("\n🔐 Testing Authentication Flow...")
    
    try:
        # Test login endpoint
        login_data = {
            "username": "testuser",
            "password": "test123",
            "tenant_id": "6899df7293ed4ce8e63f574d"
        }
        
        response = requests.post(
            'http://localhost:8000/auth/login',
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login: Successful")
            print(f"   - Access Token: {data.get('access_token', 'N/A')[:20]}...")
            print(f"   - User: {data.get('user', {}).get('username', 'N/A')}")
            print(f"   - Roles: {data.get('user', {}).get('roles', [])}")
            
            # Test token verification
            token = data.get('access_token')
            if token:
                headers = {'Authorization': f'Bearer {token}'}
                verify_response = requests.post(
                    'http://localhost:8000/auth/verify',
                    headers=headers,
                    timeout=10
                )
                
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    print(f"✅ Token Verification: {verify_data.get('valid', False)}")
                else:
                    print(f"❌ Token Verification: HTTP {verify_response.status_code}")
            
            return True
        else:
            print(f"❌ Login: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Authentication: Request failed - {e}")
        return False

def main():
    """Main test function"""
    print("🚀 WFM Complete Integration Test")
    print("=" * 50)
    
    tests = [
        ("Backend Health", test_backend_health),
        ("MongoDB Connection", test_mongodb_connection),
        ("Frontend Connectivity", test_frontend_connectivity),
        ("Authentication Flow", test_authentication_flow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: Test failed with error - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The WFM system is fully integrated and ready.")
        print("\n📋 Next steps:")
        print("1. Open http://localhost:3001/login in your browser")
        print("2. Use the test credentials:")
        print("   - Tenant ID: 6899df7293ed4ce8e63f574d")
        print("   - Username: testuser")
        print("   - Password: test123")
        print("3. Verify successful login and dashboard access")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
        print("📚 See ONLINE_MONGODB_SETUP.md and NEXTJS_INTEGRATION_GUIDE.md for troubleshooting.")

if __name__ == "__main__":
    main()
