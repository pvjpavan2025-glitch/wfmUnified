#!/usr/bin/env python3
"""
Reset database and create comprehensive test data for WFM system.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from passlib.hash import bcrypt
from datetime import datetime
import httpx
import json

# Database configuration
MONGODB_URL = "mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB"
DATABASE_NAME = "wfm"

# API endpoints
API_BASE_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:8007"

async def reset_database():
    """Reset the database by removing all existing data."""
    print("🗑️  Resetting database...")
    
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        # Delete all collections
        collections_to_clear = ["users", "roles", "tenants", "configs", "rules", "jobs", "issues", "technicians", "orders", "reports", "vendors", "tasks"]
        
        for collection_name in collections_to_clear:
            if collection_name in await db.list_collection_names():
                result = await db[collection_name].delete_many({})
                print(f"✅ Cleared {collection_name}: {result.deleted_count} documents")
        
        print("✅ Database reset complete")
        return db
        
    except Exception as e:
        print(f"❌ Error resetting database: {str(e)}")
        raise

async def create_test_tenant(db):
    """Create a test tenant."""
    print("🏢 Creating test tenant...")
    
    tenant_id = ObjectId()
    tenant_data = {
        "_id": tenant_id,
        "name": "Test Organization",
        "domain": "test.example.com",
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.tenants.update_one(
        {"_id": tenant_id},
        {"$set": tenant_data},
        upsert=True
    )
    
    print(f"✅ Created test tenant: {tenant_data['name']}")
    return tenant_id

async def create_test_roles(db, tenant_id):
    """Create test roles."""
    print("👥 Creating test roles...")
    
    roles_data = [
        {
            "_id": ObjectId(),
            "name": "admin",
            "description": "Administrator role with full access",
            "tenant_id": tenant_id,
            "permissions": ["*"],
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "technician",
            "description": "Technician role for field work",
            "tenant_id": tenant_id,
            "permissions": ["view_jobs", "update_jobs", "view_technicians", "update_profile"],
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": ObjectId(),
            "name": "vendor",
            "description": "Vendor role for supply management",
            "tenant_id": tenant_id,
            "permissions": ["view_orders", "update_orders", "view_vendors", "update_profile"],
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    role_ids = []
    for role_data in roles_data:
        await db.roles.update_one(
            {"_id": role_data["_id"]},
            {"$set": role_data},
            upsert=True
        )
        role_ids.append(role_data["_id"])
        print(f"✅ Created role: {role_data['name']}")
    
    return role_ids

async def create_test_users(db, tenant_id, role_ids):
    """Create 12 test users with different role combinations."""
    print("👤 Creating test users...")
    
    users_data = [
        # Admin users
        {
            "username": "admin1",
            "email": "admin1@test.com",
            "password": "Admin123!",
            "first_name": "Admin",
            "last_name": "One",
            "role_ids": [role_ids[0]],  # admin
            "status": "active"
        },
        {
            "username": "admin2",
            "email": "admin2@test.com",
            "password": "Admin123!",
            "first_name": "Admin",
            "last_name": "Two",
            "role_ids": [role_ids[0]],  # admin
            "status": "active"
        },
        {
            "username": "admin3",
            "email": "admin3@test.com",
            "password": "Admin123!",
            "first_name": "Admin",
            "last_name": "Three",
            "role_ids": [role_ids[0]],  # admin
            "status": "active"
        },
        {
            "username": "admin4",
            "email": "admin4@test.com",
            "password": "Admin123!",
            "first_name": "Admin",
            "last_name": "Four",
            "role_ids": [role_ids[0]],  # admin
            "status": "active"
        },
        
        # Technician users
        {
            "username": "tech1",
            "email": "tech1@test.com",
            "password": "Tech123!",
            "first_name": "Tech",
            "last_name": "One",
            "role_ids": [role_ids[1]],  # technician
            "status": "active"
        },
        {
            "username": "tech2",
            "email": "tech2@test.com",
            "password": "Tech123!",
            "first_name": "Tech",
            "last_name": "Two",
            "role_ids": [role_ids[1]],  # technician
            "status": "active"
        },
        {
            "username": "tech3",
            "email": "tech3@test.com",
            "password": "Tech123!",
            "first_name": "Tech",
            "last_name": "Three",
            "role_ids": [role_ids[1]],  # technician
            "status": "active"
        },
        {
            "username": "tech4",
            "email": "tech4@test.com",
            "password": "Tech123!",
            "first_name": "Tech",
            "last_name": "Four",
            "role_ids": [role_ids[1]],  # technician
            "status": "active"
        },
        
        # Vendor users
        {
            "username": "vendor1",
            "email": "vendor1@test.com",
            "password": "Vendor123!",
            "first_name": "Vendor",
            "last_name": "One",
            "role_ids": [role_ids[2]],  # vendor
            "status": "active"
        },
        {
            "username": "vendor2",
            "email": "vendor2@test.com",
            "password": "Vendor123!",
            "first_name": "Vendor",
            "last_name": "Two",
            "role_ids": [role_ids[2]],  # vendor
            "status": "active"
        },
        {
            "username": "vendor3",
            "email": "vendor3@test.com",
            "password": "Vendor123!",
            "first_name": "Vendor",
            "last_name": "Three",
            "role_ids": [role_ids[2]],  # vendor
            "status": "active"
        },
        {
            "username": "vendor4",
            "email": "vendor4@test.com",
            "password": "Vendor123!",
            "first_name": "Vendor",
            "last_name": "Four",
            "role_ids": [role_ids[2]],  # vendor
            "status": "active"
        }
    ]
    
    created_users = []
    for user_data in users_data:
        # Hash password
        password_hash = bcrypt.hash(user_data["password"])
        
        # Create user document
        user_doc = {
            "_id": ObjectId(),
            "username": user_data["username"],
            "email": user_data["email"],
            "password_hash": password_hash,
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "tenant_id": tenant_id,
            "role_ids": user_data["role_ids"],
            "status": user_data["status"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
            "failed_login_attempts": 0
        }
        
        await db.users.update_one(
            {"username": user_data["username"], "tenant_id": tenant_id},
            {"$set": user_doc},
            upsert=True
        )
        
        created_users.append({
            "username": user_data["username"],
            "password": user_data["password"],
            "role": "admin" if role_ids[0] in user_data["role_ids"] else "technician" if role_ids[1] in user_data["role_ids"] else "vendor"
        })
        
        print(f"✅ Created user: {user_data['username']} ({user_data['first_name']} {user_data['last_name']}) - Role: {created_users[-1]['role']}")
    
    return created_users

async def test_authentication_and_authorization(users, tenant_id):
    """Test authentication and authorization with created users."""
    print("\n🧪 Testing Authentication and Authorization...")
    
    # Test with an admin user
    test_user = users[0]  # admin1
    print(f"\n🔐 Testing with user: {test_user['username']} (Role: {test_user['role']})")
    
    try:
        # Test login
        print("1️⃣ Testing login...")
        async with httpx.AsyncClient() as client:
            login_response = await client.post(
                f"{API_BASE_URL}/auth/login",
                json={
                    "username": test_user["username"],
                    "password": test_user["password"],
                    "tenant_id": str(tenant_id)  # Use the tenant ID we just created
                }
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                token = login_data["access_token"]
                print(f"✅ Login successful! Token: {token[:50]}...")
                
                # Test token verification
                print("2️⃣ Testing token verification...")
                verify_response = await client.post(
                    f"{API_BASE_URL}/auth/verify",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if verify_response.status_code == 200:
                    print("✅ Token verification successful!")
                    verify_data = verify_response.json()
                    print(f"   User: {verify_data['user']['username']}")
                    print(f"   Roles: {verify_data['user']['roles']}")
                else:
                    print(f"❌ Token verification failed: {verify_response.status_code} - {verify_response.text}")
                
                # Test dashboard metrics (should work for admin)
                print("3️⃣ Testing dashboard metrics...")
                dashboard_response = await client.get(
                    f"{DASHBOARD_URL}/dashboard/metrics",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if dashboard_response.status_code == 200:
                    print("✅ Dashboard metrics accessible!")
                else:
                    print(f"❌ Dashboard metrics failed: {dashboard_response.status_code} - {dashboard_response.text}")
                
                # Test user listing (admin should have access)
                print("4️⃣ Testing user listing...")
                users_response = await client.get(
                    f"{API_BASE_URL}/users",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if users_response.status_code == 200:
                    print("✅ User listing accessible!")
                else:
                    print(f"❌ User listing failed: {users_response.status_code} - {users_response.text}")
                
            else:
                print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
                
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

async def main():
    """Main function to reset database and create test data."""
    print("🚀 Starting WFM Database Reset and Test Data Creation...")
    
    try:
        # Reset database
        db = await reset_database()
        
        # Create test tenant
        tenant_id = await create_test_tenant(db)
        
        # Create test roles
        role_ids = await create_test_roles(db, tenant_id)
        
        # Create test users
        users = await create_test_users(db, tenant_id, role_ids)
        
        print(f"\n✅ Successfully created:")
        print(f"   - 1 tenant")
        print(f"   - 3 roles (admin, technician, vendor)")
        print(f"   - 12 users (4 of each role)")
        
        # Test authentication and authorization
        await test_authentication_and_authorization(users, tenant_id)
        
        print(f"\n🎉 Database setup complete! You can now test with any of these users:")
        for user in users:
            print(f"   - {user['username']} (Password: {user['password']}, Role: {user['role']})")
        
    except Exception as e:
        print(f"❌ Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
