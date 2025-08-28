#!/usr/bin/env python3
"""
Setup Script for Online MongoDB Database
This script creates the initial database structure and test data for the WFM system
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from urllib.parse import quote_plus
from datetime import datetime
from bson import ObjectId

def setup_database():
    """Set up the online MongoDB database with initial structure"""
    
    # MongoDB connection details
    username = "wfmadmin"
    password = "tsarolabs@12345#"
    cluster_url = "wfmdb.cvkb04l.mongodb.net"
    database_name = "wfm"
    
    # URL-encode the password to handle special characters
    encoded_password = quote_plus(password)
    
    # Connection string with encoded password
    connection_string = f"mongodb+srv://{username}:{encoded_password}@{cluster_url}/?retryWrites=true&w=majority&appName=wfmDB"
    
    print("🚀 Setting up Online MongoDB Database for WFM System...")
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
        
        # Create or get database
        db = client[database_name]
        print(f"✅ Database '{database_name}' ready")
        
        # Create collections
        collections = ['users', 'roles', 'tenants', 'tasks', 'technicians', 'vendors']
        
        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                print(f"✅ Created collection: {collection_name}")
            else:
                print(f"ℹ️  Collection exists: {collection_name}")
        
        # Create initial tenant with proper ObjectId
        tenants_collection = db.tenants
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
        
        # Check if tenant already exists
        existing_tenant = tenants_collection.find_one({"name": "WFM System"})
        if not existing_tenant:
            result = tenants_collection.insert_one(tenant_data)
            print(f"✅ Created initial tenant: {tenant_data['name']} (ID: {tenant_id})")
        else:
            tenant_id = existing_tenant["_id"]
            print(f"ℹ️  Tenant already exists: {existing_tenant['name']} (ID: {tenant_id})")
        
        # Create initial role with proper ObjectId
        roles_collection = db.roles
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
        
        # Check if role already exists
        existing_role = roles_collection.find_one({"name": "SuperAdmin", "tenant_id": tenant_id})
        if not existing_role:
            result = roles_collection.insert_one(role_data)
            print(f"✅ Created initial role: {role_data['name']} (ID: {role_id})")
        else:
            role_id = existing_role["_id"]
            print(f"ℹ️  Role already exists: {existing_role['name']} (ID: {role_id})")
        
        # Create test user with proper ObjectId
        users_collection = db.users
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
        
        # Check if user already exists
        existing_user = users_collection.find_one({"username": "testuser", "tenant_id": tenant_id})
        if not existing_user:
            result = users_collection.insert_one(user_data)
            print(f"✅ Created test user: {user_data['username']} (ID: {result.inserted_id})")
        else:
            print(f"ℹ️  Test user already exists: {existing_user['username']} (ID: {existing_user['_id']})")
        
        # Create indexes for better performance
        print("📊 Creating database indexes...")
        
        # Users collection indexes
        users_collection.create_index([("username", 1), ("tenant_id", 1)], unique=True)
        users_collection.create_index([("email", 1), ("tenant_id", 1)], unique=True)
        users_collection.create_index([("tenant_id", 1)])
        
        # Roles collection indexes
        roles_collection.create_index([("name", 1), ("tenant_id", 1)], unique=True)
        roles_collection.create_index([("tenant_id", 1)])
        
        # Tenants collection indexes
        tenants_collection.create_index([("domain", 1)], unique=True)
        tenants_collection.create_index([("status", 1)])
        
        print("✅ Database indexes created")
        
        # Show final database status
        print("\n📊 Database Setup Complete!")
        print(f"🗄️  Database: {database_name}")
        print(f"📁 Collections: {db.list_collection_names()}")
        
        # Count documents in each collection
        for collection_name in collections:
            count = db[collection_name].count_documents({})
            print(f"   - {collection_name}: {count} documents")
        
        # Close connection
        client.close()
        print("🔒 Connection closed successfully")
        
        return True, str(tenant_id)
        
    except ConnectionFailure as e:
        print(f"❌ Connection failed: {e}")
        return False, None
    except ServerSelectionTimeoutError as e:
        print(f"⏰ Server selection timeout: {e}")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, None

def main():
    """Main function"""
    print("🚀 WFM Online MongoDB Database Setup")
    print("=" * 50)
    
    # Set up database
    success, tenant_id = setup_database()
    
    print("")
    if success:
        print("🎉 Database setup completed successfully!")
        print("📋 You can now use the online MongoDB with the WFM system.")
        print("")
        print("🔑 Test Credentials:")
        print(f"   - Tenant ID: {tenant_id}")
        print("   - Username: testuser")
        print("   - Password: test123")
        print("")
        print("💾 Save this tenant ID for frontend testing!")
    else:
        print("❌ Database setup failed. Please check the error messages above.")
        print("📚 See ONLINE_MONGODB_SETUP.md for troubleshooting.")

if __name__ == "__main__":
    main()
