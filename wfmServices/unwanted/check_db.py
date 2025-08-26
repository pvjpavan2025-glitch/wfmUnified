#!/usr/bin/env python3
"""
Check existing data in the database.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Database configuration
MONGODB_URL = "mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB"
DATABASE_NAME = "wfm"

async def check_database():
    """Check existing data in database."""
    print("🔍 Checking WFM Database for existing data...")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        print("✅ Connected to MongoDB Atlas")
        
        # Check tenants
        print("\n📋 Tenants:")
        tenants = await db.tenants.find().to_list(length=10)
        for tenant in tenants:
            print(f"  - ID: {tenant['_id']}")
            print(f"    Name: {tenant.get('name', 'N/A')}")
            print(f"    Domain: {tenant.get('domain', 'N/A')}")
            print(f"    Status: {tenant.get('status', 'N/A')}")
            print()
        
        # Check users
        print("👤 Users:")
        users = await db.users.find().to_list(length=10)
        for user in users:
            print(f"  - ID: {user['_id']}")
            print(f"    Username: {user.get('username', 'N/A')}")
            print(f"    Email: {user.get('email', 'N/A')}")
            print(f"    Tenant ID: {user.get('tenant_id', 'N/A')}")
            print(f"    Status: {user.get('status', 'N/A')}")
            print()
        
        # Check roles
        print("🔑 Roles:")
        roles = await db.roles.find().to_list(length=10)
        for role in roles:
            print(f"  - ID: {role['_id']}")
            print(f"    Name: {role.get('name', 'N/A')}")
            print(f"    Tenant ID: {role.get('tenant_id', 'N/A')}")
            print(f"    Status: {role.get('status', 'N/A')}")
            print()
        
        # Close connection
        client.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        raise

async def main():
    """Main function."""
    await check_database()

if __name__ == "__main__":
    asyncio.run(main())
