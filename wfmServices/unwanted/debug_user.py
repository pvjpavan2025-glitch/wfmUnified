#!/usr/bin/env python3
"""
Debug user authentication issue.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Database configuration
MONGODB_URL = "mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB"
DATABASE_NAME = "wfm"

async def debug_user():
    """Debug user authentication issue."""
    print("🔍 Debugging user authentication issue...")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        print("✅ Connected to MongoDB Atlas")
        
        # Target tenant and user
        tenant_id_str = "6899df7293ed4ce8e63f574d"
        username = "testuser"
        
        print(f"\n🎯 Looking for:")
        print(f"   Username: {username}")
        print(f"   Tenant ID (string): {tenant_id_str}")
        
        # Convert to ObjectId
        tenant_id_obj = ObjectId(tenant_id_str)
        print(f"   Tenant ID (ObjectId): {tenant_id_obj}")
        
        # Check if tenant exists
        tenant = await db.tenants.find_one({"_id": tenant_id_obj})
        if tenant:
            print(f"\n✅ Tenant found:")
            print(f"   ID: {tenant['_id']}")
            print(f"   Name: {tenant.get('name', 'N/A')}")
            print(f"   Domain: {tenant.get('domain', 'N/A')}")
        else:
            print(f"\n❌ Tenant not found with ObjectId: {tenant_id_obj}")
            return
        
        # Check if user exists with exact tenant_id
        user = await db.users.find_one({
            "username": username,
            "tenant_id": tenant_id_obj
        })
        
        if user:
            print(f"\n✅ User found:")
            print(f"   ID: {user['_id']}")
            print(f"   Username: {user.get('username', 'N/A')}")
            print(f"   Email: {user.get('email', 'N/A')}")
            print(f"   Tenant ID: {user.get('tenant_id', 'N/A')}")
            print(f"   Tenant ID type: {type(user.get('tenant_id', 'N/A'))}")
            print(f"   Status: {user.get('status', 'N/A')}")
            print(f"   Has password_hash: {'password_hash' in user}")
        else:
            print(f"\n❌ User not found with exact match")
            
            # Try to find any user with this username
            all_users = await db.users.find({"username": username}).to_list(length=10)
            print(f"\n🔍 All users with username '{username}':")
            for u in all_users:
                print(f"   - ID: {u['_id']}")
                print(f"     Username: {u.get('username', 'N/A')}")
                print(f"     Tenant ID: {u.get('tenant_id', 'N/A')}")
                print(f"     Tenant ID type: {type(u.get('tenant_id', 'N/A'))}")
                print()
        
        # Close connection
        client.close()
        
    except Exception as e:
        print(f"❌ Error debugging user: {str(e)}")
        raise

async def main():
    """Main function."""
    await debug_user()

if __name__ == "__main__":
    asyncio.run(main())
