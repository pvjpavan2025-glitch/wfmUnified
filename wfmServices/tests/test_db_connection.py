#!/usr/bin/env python3
"""
Simple database connection test for WFM service.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis

# Database configuration from env.online
MONGODB_URL = "mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB"
REDIS_URL = "redis://default:kIdJfI3xoLxHiKFnCrkGBYffiDla8Y9h@redis-15514.c56.east-us.azure.redns.redis-cloud.com:15514"
DATABASE_NAME = "wfm"

async def test_mongodb():
    """Test MongoDB connection."""
    try:
        print("🔍 Testing MongoDB connection...")
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Test database access
        collections = await db.list_collection_names()
        print(f"✅ Found {len(collections)} collections: {collections}")
        
        # Test user query
        users = await db.users.find().limit(1).to_list(1)
        if users:
            print(f"✅ Found user: {users[0]['username']}")
        else:
            print("⚠️ No users found")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        return False

async def test_redis():
    """Test Redis connection."""
    try:
        print("🔍 Testing Redis connection...")
        client = redis.from_url(REDIS_URL, decode_responses=True)
        
        # Test connection
        await client.ping()
        print("✅ Redis connection successful")
        
        # Test basic operations
        await client.set("test_key", "test_value")
        value = await client.get("test_key")
        await client.delete("test_key")
        
        if value == "test_value":
            print("✅ Redis read/write operations successful")
        else:
            print("⚠️ Redis read/write operations failed")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        return False

async def main():
    """Main function."""
    print("🚀 Testing WFM Service Database Connections...")
    print("=" * 50)
    
    mongo_success = await test_mongodb()
    print()
    redis_success = await test_redis()
    
    print("\n" + "=" * 50)
    if mongo_success and redis_success:
        print("🎉 All database connections successful!")
        print("✅ Ready to start services and run tests")
    else:
        print("❌ Some database connections failed")
        print("⚠️ Please check your configuration and try again")

if __name__ == "__main__":
    asyncio.run(main())
