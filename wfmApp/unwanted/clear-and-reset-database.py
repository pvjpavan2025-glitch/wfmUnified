#!/usr/bin/env python3
"""
Clear and Reset Online MongoDB Database
This script clears the existing data and recreates it with proper MongoDB ObjectIds
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from urllib.parse import quote_plus
from datetime import datetime
from bson import ObjectId

def clear_and_reset_database():
    """Clear existing data and recreate with proper ObjectIds"""
    
    # MongoDB connection details
    username = "wfmadmin"
    password = "tsarolabs@12345#"
    cluster_url = "wfmdb.cvkb04l.mongodb.net"
    database_name = "wfm"
    
    # URL-encode the password
    encoded_password = quote_plus(password)
    connection_string = f"mongodb+srv://{username}:{encoded_password}@{cluster_url}/?retryWrites=true&w=majority&appName=wfmDB"
    
    print("🗑️  Clearing and Resetting Online MongoDB Database...")
    print(f"📍 Cluster: {cluster_url}")
    print(f"👤 Username: {username}")
    print(f"🗄️  Database: {database_name}")
    print("")
    
    try:
        # Create MongoDB client
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=10000,
            ssl=True,
            tlsAllowInvalidCertificates=True,
            retryWrites=True,
            w='majority'
        )
        
        # Test connection
        print("⏳ Testing connection...")
        client.admin.command('ping')
        print("✅ Connection successful!")
        
        # Get database
        db = client[database_name]
        
        # Clear all collections
        collections = ['users', 'roles', 'tenants', 'tasks', 'technicians', 'vendors']
        print("🗑️  Clearing existing data...")
        
        for collection_name in collections:
            if collection_name in db.list_collection_names():
                count = db[collection_name].count_documents({})
                db[collection_name].delete_many({})
                print(f"   - Cleared {collection_name}: {count} documents")
            else:
                print(f"   - {collection_name}: No data to clear")
        
        # Create new data with proper ObjectIds
        print("\n🔄 Creating new data with proper ObjectIds...")
        
        # Create tenant
        tenant_id = ObjectId()
        tenant_data = {
            "_id": tenant_id,
            "name": "WFM System",
            "domain": "wfm",
            "status": "active",
            "settings": {
                "timezone": "UTC",
                "date_format": "YYYY-MM-DD",
                "time_format": "HH:mm:ss"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "system",
            "updated_by": "system"
        }
        
        db.tenants.insert_one(tenant_data)
        print(f"✅ Created tenant: {tenant_data['name']} (ID: {tenant_id})")
        
        # Create role
        role_id = ObjectId()
        role_data = {
            "_id": role_id,
            "name": "SuperAdmin",
            "description": "Super Administrator with full access",
            "tenant_id": tenant_id,
            "permission_ids": [],
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "system",
            "updated_by": "system"
        }
        
        db.roles.insert_one(role_data)
        print(f"✅ Created role: {role_data['name']} (ID: {role_id})")
        
        # Create test user
        user_data = {
            "_id": ObjectId(),
            "username": "testuser",
            "email": "test@wfm.local",
            "password_hash": "$2b$12$aVURW/59hs0L8s/Q5yOzy.5YL2B/T0jzFfbjJohSMmJcj2uxR96CG",  # "test123"
            "first_name": "Test",
            "last_name": "User",
            "tenant_id": tenant_id,
            "role_ids": [role_id],
            "status": "active",
            "last_login": None,
            "failed_login_attempts": 0,
            "locked_until": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "system",
            "updated_by": "system"
        }
        
        db.users.insert_one(user_data)
        print(f"✅ Created test user: {user_data['username']} (ID: {user_data['_id']})")
        
        # Create indexes
        print("\n📊 Creating database indexes...")
        
        # Users collection indexes
        db.users.create_index([("username", 1), ("tenant_id", 1)], unique=True)
        db.users.create_index([("email", 1), ("tenant_id", 1)], unique=True)
        db.users.create_index([("tenant_id", 1)])
        
        # Roles collection indexes
        db.roles.create_index([("name", 1), ("tenant_id", 1)], unique=True)
        db.roles.create_index([("tenant_id", 1)])
        
        # Tenants collection indexes
        db.tenants.create_index([("domain", 1)], unique=True)
        db.tenants.create_index([("status", 1)])
        
        print("✅ Database indexes created")
        
        # Show final status
        print("\n📊 Database Reset Complete!")
        print(f"🗄️  Database: {database_name}")
        print(f"📁 Collections: {db.list_collection_names()}")
        
        for collection_name in collections:
            count = db[collection_name].count_documents({})
            print(f"   - {collection_name}: {count} documents")
        
        # Close connection
        client.close()
        print("🔒 Connection closed successfully")
        
        return True, str(tenant_id)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

def main():
    """Main function"""
    print("🚀 WFM Database Clear and Reset")
    print("=" * 50)
    
    # Confirm action
    print("⚠️  This will DELETE ALL existing data and recreate it!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Operation cancelled.")
        return
    
    # Clear and reset database
    success, tenant_id = clear_and_reset_database()
    
    print("")
    if success:
        print("🎉 Database reset completed successfully!")
        print("📋 New test credentials:")
        print(f"   - Tenant ID: {tenant_id}")
        print("   - Username: testuser")
        print("   - Password: test123")
        print("")
        print("💾 Update your frontend with this new tenant ID!")
        print("📝 Update these files:")
        print("   - app/login/page.tsx")
        print("   - test-complete-integration.py")
        print("   - ONLINE_MONGODB_SETUP.md")
    else:
        print("❌ Database reset failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
