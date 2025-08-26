#!/usr/bin/env python3
"""
Simple script to check what's in the database.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Database configuration
MONGODB_URL = "mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB"
DATABASE_NAME = "wfm"

async def check_database():
    """Check what's in the database."""
    print("🔍 Checking database contents...")
    
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        # Check collections
        collections = await db.list_collection_names()
        print(f"📚 Collections: {collections}")
        
        # Check tenants
        if "tenants" in collections:
            tenants = await db.tenants.find().to_list(length=10)
            print(f"\n🏢 Tenants ({len(tenants)}):")
            for tenant in tenants:
                print(f"   - ID: {tenant['_id']}")
                print(f"     Name: {tenant.get('name', 'N/A')}")
                print(f"     Domain: {tenant.get('domain', 'N/A')}")
                print(f"     Status: {tenant.get('status', 'N/A')}")
        
        # Check users
        if "users" in collections:
            users = await db.users.find().to_list(length=10)
            print(f"\n👤 Users ({len(tenants)}):")
            for user in users:
                print(f"   - ID: {user['_id']}")
                print(f"     Username: {user.get('username', 'N/A')}")
                print(f"     Email: {user.get('email', 'N/A')}")
                print(f"     Tenant ID: {user.get('tenant_id', 'N/A')}")
                print(f"     Status: {user.get('status', 'N/A')}")
        
        # Check roles
        if "roles" in collections:
            roles = await db.roles.find().to_list(length=10)
            print(f"\n👥 Roles ({len(roles)}):")
            for role in roles:
                print(f"   - ID: {role['_id']}")
                print(f"     Name: {role.get('name', 'N/A')}")
                print(f"     Tenant ID: {role.get('tenant_id', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(check_database())
