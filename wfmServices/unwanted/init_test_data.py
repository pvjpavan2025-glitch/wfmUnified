#!/usr/bin/env python3
"""
Initialize test data in the online database for testing purposes.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from passlib.hash import bcrypt
from datetime import datetime

# Database configuration from env.online
MONGODB_URL = "mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB"
DATABASE_NAME = "wfm"

async def init_database():
    """Initialize database with test data."""
    print("🚀 Initializing WFM Database with Test Data...")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        print("✅ Connected to MongoDB Atlas")
        
        # Create collections if they don't exist
        collections = ["users", "roles", "tenants", "configs", "rules", "jobs", "issues"]
        for collection_name in collections:
            if collection_name not in await db.list_collection_names():
                await db.create_collection(collection_name)
                print(f"✅ Created collection: {collection_name}")
        
        # Create test tenant
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
        
        # Create test role
        role_id = ObjectId()
        role_data = {
            "_id": role_id,
            "name": "admin",
            "description": "Administrator role with full access",
            "tenant_id": tenant_id,
            "permissions": ["*"],
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.roles.update_one(
            {"_id": role_id},
            {"$set": role_data},
            upsert=True
        )
        print(f"✅ Created test role: {role_data['name']}")
        
        # Create test user
        user_data = {
            "_id": ObjectId(),
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": bcrypt.hash("TestPassword123!"),
            "first_name": "Test",
            "last_name": "User",
            "tenant_id": tenant_id,
            "role_ids": [role_id],
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
            "failed_login_attempts": 0
        }
        
        await db.users.update_one(
            {"username": user_data["username"], "tenant_id": tenant_id},
            {"$set": user_data},
            upsert=True
        )
        print(f"✅ Created test user: {user_data['username']}")
        
        # Create test configuration
        config_data = {
            "_id": ObjectId(),
            "key": "test_config",
            "value": "test_value",
            "tenant_id": tenant_id,
            "description": "Test configuration for testing",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.configs.update_one(
            {"key": config_data["key"], "tenant_id": tenant_id},
            {"$set": config_data},
            upsert=True
        )
        print(f"✅ Created test config: {config_data['key']}")
        
        # Create test rule
        rule_data = {
            "_id": ObjectId(),
            "name": "test_rule",
            "description": "Test rule for testing",
            "tenant_id": tenant_id,
            "conditions": {
                "field": "status",
                "operator": "equals",
                "value": "active"
            },
            "actions": {
                "action": "notify",
                "target": "manager"
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.rules.update_one(
            {"name": rule_data["name"], "tenant_id": tenant_id},
            {"$set": rule_data},
            upsert=True
        )
        print(f"✅ Created test rule: {rule_data['name']}")
        
        # Create test job
        job_data = {
            "_id": ObjectId(),
            "name": "test_job",
            "description": "Test job for testing",
            "tenant_id": tenant_id,
            "schedule": "0 9 * * 1-5",  # Weekdays at 9 AM
            "status": "active",
            "last_run": None,
            "next_run": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.jobs.update_one(
            {"name": job_data["name"], "tenant_id": tenant_id},
            {"$set": job_data},
            upsert=True
        )
        print(f"✅ Created test job: {job_data['name']}")
        
        # Create test issue
        issue_data = {
            "_id": ObjectId(),
            "title": "Test Issue",
            "description": "Test issue for testing",
            "tenant_id": tenant_id,
            "priority": "medium",
            "status": "open",
            "assigned_to": None,
            "created_by": user_data["_id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.issues.update_one(
            {"title": issue_data["title"], "tenant_id": tenant_id},
            {"$set": issue_data},
            upsert=True
        )
        print(f"✅ Created test issue: {issue_data['title']}")
        
        print("\n🎉 Database initialization completed successfully!")
        print(f"📊 Test tenant ID: {tenant_id}")
        print(f"👤 Test user: {user_data['username']} / TestPassword123!")
        print(f"🔑 Test role: {role_data['name']}")
        
        # Close connection
        client.close()
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        raise

async def main():
    """Main function."""
    await init_database()

if __name__ == "__main__":
    asyncio.run(main())
