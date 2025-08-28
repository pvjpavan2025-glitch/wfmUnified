#!/usr/bin/env python3
"""
Fix email address for test user.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Database configuration
MONGODB_URL = "mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB"
DATABASE_NAME = "wfm"

async def fix_email():
    """Fix email address for test user."""
    print("📧 Fixing email address for test user...")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        print("✅ Connected to MongoDB Atlas")
        
        # Target tenant and user
        tenant_id = "6899df7293ed4ce8e63f574d"
        username = "testuser"
        new_email = "test@wfm.com"
        
        # Update the user's email
        result = await db.users.update_one(
            {
                "username": username,
                "tenant_id": ObjectId(tenant_id)
            },
            {
                "$set": {
                    "email": new_email,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Email updated successfully for user {username}")
            print(f"   New email: {new_email}")
            print(f"   Tenant ID: {tenant_id}")
        else:
            print(f"❌ No user found with username {username} in tenant {tenant_id}")
        
        # Close connection
        client.close()
        
    except Exception as e:
        print(f"❌ Error updating email: {str(e)}")
        raise

async def main():
    """Main function."""
    await fix_email()

if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(main())
