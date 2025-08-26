#!/usr/bin/env python3
"""
Test Script for Online MongoDB Connection
This script tests the connection to the online MongoDB Atlas cluster
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import ssl
from urllib.parse import quote_plus

def test_mongodb_connection():
    """Test connection to online MongoDB Atlas cluster"""
    
    # MongoDB connection details
    username = "wfmadmin"
    password = "tsarolabs@12345#"
    cluster_url = "wfmdb.cvkb04l.mongodb.net"
    database_name = "wfm"
    
    # URL-encode the password to handle special characters
    encoded_password = quote_plus(password)
    
    # Connection string with encoded password
    connection_string = f"mongodb+srv://{username}:{encoded_password}@{cluster_url}/?retryWrites=true&w=majority&appName=wfmDB"
    
    print("🔍 Testing Online MongoDB Connection...")
    print(f"📍 Cluster: {cluster_url}")
    print(f"👤 Username: {username}")
    print(f"🗄️  Database: {database_name}")
    print("")
    
    try:
        # Create MongoDB client with SSL and timeout settings
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=10000,  # 10 second timeout
            ssl=True,
            tlsAllowInvalidCertificates=True,  # For testing purposes
            retryWrites=True,
            w='majority'
        )
        
        # Test connection by listing databases
        print("⏳ Attempting to connect...")
        client.admin.command('ping')
        
        # List available databases
        databases = client.list_database_names()
        print(f"✅ Successfully connected to MongoDB Atlas!")
        print(f"📊 Available databases: {databases}")
        
        # Test specific database access
        if database_name in databases:
            db = client[database_name]
            collections = db.list_collection_names()
            print(f"📁 Collections in '{database_name}': {collections}")
            
            # Test basic operations
            try:
                # Test insert operation
                test_collection = db.test_connection
                result = test_collection.insert_one({"test": "connection", "timestamp": "2025-08-11"})
                print(f"✅ Insert test successful: {result.inserted_id}")
                
                # Test find operation
                doc = test_collection.find_one({"test": "connection"})
                print(f"✅ Find test successful: {doc}")
                
                # Clean up test data
                test_collection.delete_one({"test": "connection"})
                print("✅ Cleanup test successful")
                
            except Exception as e:
                print(f"⚠️  Basic operations test failed: {e}")
        else:
            print(f"⚠️  Database '{database_name}' not found. Available: {databases}")
        
        # Close connection
        client.close()
        print("🔒 Connection closed successfully")
        
    except ConnectionFailure as e:
        print(f"❌ Connection failed: {e}")
        return False
    except ServerSelectionTimeoutError as e:
        print(f"⏰ Server selection timeout: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import pymongo
        print(f"✅ PyMongo version: {pymongo.__version__}")
        return True
    except ImportError:
        print("❌ PyMongo not installed. Run: pip install 'pymongo[srv]'")
        return False

def main():
    """Main function"""
    print("🚀 WFM Online MongoDB Connection Test")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("")
    
    # Test connection
    success = test_mongodb_connection()
    
    print("")
    if success:
        print("🎉 All tests passed! MongoDB connection is working.")
        print("📋 You can now use the online MongoDB in your application.")
    else:
        print("❌ Connection test failed. Please check your configuration.")
        print("📚 See NEXTJS_INTEGRATION_GUIDE.md for troubleshooting.")
    
    print("")
    print("🔗 Connection String (with encoded password):")
    print("mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB")

if __name__ == "__main__":
    main()
