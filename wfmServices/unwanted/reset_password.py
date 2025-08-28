#!/usr/bin/env python3
"""
Reset password for test user.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.hash import bcrypt

# Database configuration
MONGODB_URL = "mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB"
DATABASE_NAME = "wfm"

async def reset_password():
    """Reset password for test user."""
    print("🔐 Resetting password for test user...")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        print("✅ Connected to MongoDB Atlas")
        
        # Target tenant and user
        tenant_id = "6899df7293ed4ce8e63f574d"
        username = "testuser"
        new_password = "test123"
        
        # Hash the new password
        password_hash = bcrypt.hash(new_password)
        
        # Update the user's password
        result = await db.users.update_one(
            {
                "username": username,
                "tenant_id": ObjectId(tenant_id)
            },
            {
                "$set": {
                    "password_hash": password_hash,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Password reset successfully for user {username}")
            print(f"   New password: {new_password}")
            print(f"   Tenant ID: {tenant_id}")
        else:
            print(f"❌ No user found with username {username} in tenant {tenant_id}")
        
        # Close connection
        client.close()
        
    except Exception as e:
        print(f"❌ Error resetting password: {str(e)}")
        raise

async def main():
    """Main function."""
    await reset_password()

if __name__ == "__main__":
    from datetime import datetime
    from bson import ObjectId
    asyncio.run(main())
