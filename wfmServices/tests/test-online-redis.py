#!/usr/bin/env python3
"""
Test Script for Online Redis Cloud Connection
This script tests the connection to the online Redis Cloud service
"""

import redis
import time

def test_redis_connection():
    """Test connection to online Redis Cloud"""
    
    # Redis Cloud connection details
    host = 'redis-15514.c56.east-us.azure.redns.redis-cloud.com'
    port = 15514
    username = 'default'
    password = 'kIdJfI3xoLxHiKFnCrkGBYffiDla8Y9h'
    
    print("🔍 Testing Online Redis Cloud Connection...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"👤 Username: {username}")
    print("")
    
    try:
        # Create Redis client
        r = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
            username=username,
            password=password,
            socket_connect_timeout=10,
            socket_timeout=10
        )
        
        # Test connection
        print("⏳ Testing connection...")
        r.ping()
        print("✅ Redis connection successful!")
        
        # Test basic operations
        print("🧪 Testing basic operations...")
        
        # Test SET operation
        success = r.set('wfm_test', 'redis_cloud_working')
        if success:
            print("✅ SET operation successful")
        else:
            print("❌ SET operation failed")
        
        # Test GET operation
        result = r.get('wfm_test')
        if result == 'redis_cloud_working':
            print("✅ GET operation successful")
            print(f"   - Retrieved value: {result}")
        else:
            print("❌ GET operation failed")
        
        # Test DELETE operation
        deleted = r.delete('wfm_test')
        if deleted == 1:
            print("✅ DELETE operation successful")
        else:
            print("❌ DELETE operation failed")
        
        # Test list operations
        print("📝 Testing list operations...")
        r.lpush('wfm_test_list', 'item1', 'item2', 'item3')
        list_length = r.llen('wfm_test_list')
        print(f"   - List created with {list_length} items")
        
        # Clean up
        r.delete('wfm_test_list')
        print("✅ Cleanup successful")
        
        # Get Redis info
        info = r.info()
        print(f"📊 Redis Version: {info.get('redis_version', 'Unknown')}")
        print(f"📊 Connected Clients: {info.get('connected_clients', 'Unknown')}")
        print(f"📊 Used Memory: {info.get('used_memory_human', 'Unknown')}")
        
        # Close connection
        r.close()
        print("🔒 Connection closed successfully")
        
        return True
        
    except redis.ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except redis.AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 WFM Online Redis Cloud Connection Test")
    print("=" * 50)
    
    # Test Redis connection
    success = test_redis_connection()
    
    print("")
    if success:
        print("🎉 Redis connection test passed!")
        print("📋 The online Redis Cloud service is working correctly.")
        print("")
        print("🔗 Redis Cloud URL: https://cloud.redis.io/")
        print("📍 Endpoint: redis-15514.c56.east-us.azure.redns.redis-cloud.com:15514")
    else:
        print("❌ Redis connection test failed.")
        print("📚 Check the error messages above for troubleshooting.")

if __name__ == "__main__":
    main()
