#!/usr/bin/env python3
"""
Initialize sample data for WFM system including orders, jobs, technicians, etc.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from passlib.hash import bcrypt
from datetime import datetime, timedelta
import random

# Database configuration
MONGODB_URL = "mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB"
DATABASE_NAME = "wfm"

async def init_sample_data():
    """Initialize database with comprehensive sample data."""
    print("🚀 Initializing WFM Database with Sample Data...")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        print("✅ Connected to MongoDB Atlas")
        
        # Create collections if they don't exist
        collections = ["users", "roles", "tenants", "orders", "jobs", "technicians", "vendors", "reports"]
        for collection_name in collections:
            if collection_name not in await db.list_collection_names():
                await db.create_collection(collection_name)
                print(f"✅ Created collection: {collection_name}")
        
        # Get existing tenant and role
        tenant = await db.tenants.find_one({"domain": "wfm"})
        if not tenant:
            print("❌ Tenant not found. Please run init_test_data.py first.")
            return
        
        tenant_id = tenant["_id"]
        role = await db.roles.find_one({"tenant_id": tenant_id})
        if not role:
            print("❌ Role not found. Please run init_test_data.py first.")
            return
        
        print(f"✅ Using tenant: {tenant['name']} (ID: {tenant_id})")
        print(f"✅ Using role: {role['name']} (ID: {role['_id']})")
        
        # Create sample technicians
        technicians_data = [
            {
                "_id": ObjectId(),
                "name": "Jacob Wilson",
                "email": "jacob.wilson@wfm.com",
                "phone": "+1-555-0101",
                "specialization": "Fiber Installation",
                "status": "available",
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "name": "Sarah Miller",
                "email": "sarah.miller@wfm.com",
                "phone": "+1-555-0102",
                "specialization": "Cable Laying",
                "status": "available",
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "name": "Brian Harris",
                "email": "brian.harris@wfm.com",
                "phone": "+1-555-0103",
                "specialization": "Splicing Work",
                "status": "available",
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "name": "Emily Davis",
                "email": "emily.davis@wfm.com",
                "phone": "+1-555-0104",
                "specialization": "Network Testing",
                "status": "available",
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "name": "Michael Chen",
                "email": "michael.chen@wfm.com",
                "phone": "+1-555-0105",
                "specialization": "Equipment Installation",
                "status": "available",
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        for tech in technicians_data:
            await db.technicians.update_one(
                {"email": tech["email"], "tenant_id": tenant_id},
                {"$set": tech},
                upsert=True
            )
        print(f"✅ Created {len(technicians_data)} technicians")
        
        # Create sample orders
        orders_data = [
            {
                "_id": ObjectId(),
                "order_number": "ORD-001",
                "customer_name": "TechCorp Solutions",
                "customer_email": "orders@techcorp.com",
                "customer_phone": "+1-555-1001",
                "priority": "high",
                "status": "active",
                "total_amount": 2500.00,
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "order_number": "ORD-002",
                "customer_name": "NetConnect Industries",
                "customer_email": "service@netconnect.com",
                "customer_phone": "+1-555-1002",
                "priority": "medium",
                "status": "active",
                "total_amount": 1800.00,
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "order_number": "ORD-003",
                "customer_name": "FiberTech Systems",
                "customer_email": "support@fibertech.com",
                "customer_phone": "+1-555-1003",
                "priority": "low",
                "status": "active",
                "total_amount": 1200.00,
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        for order in orders_data:
            await db.orders.update_one(
                {"order_number": order["order_number"], "tenant_id": tenant_id},
                {"$set": order},
                upsert=True
            )
        print(f"✅ Created {len(orders_data)} orders")
        
        # Create sample jobs (tasks within orders)
        jobs_data = [
            {
                "_id": ObjectId(),
                "job_number": "JOB-001",
                "order_id": orders_data[0]["_id"],
                "description": "Fiber Installation",
                "location": "125 Oak St, Cedar Park, TX",
                "priority": "high",
                "status": "in_progress",
                "progress": 50,
                "assigned_to": technicians_data[0]["_id"],
                "technician_name": "Jacob Wilson",
                "due_date": datetime.utcnow() + timedelta(days=3),
                "estimated_hours": 8,
                "actual_hours": 4,
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "job_number": "JOB-002",
                "order_id": orders_data[1]["_id"],
                "description": "Cable Laying",
                "location": "464 Maple Ave, Lakewood, TX",
                "priority": "medium",
                "status": "pending",
                "progress": 75,
                "assigned_to": technicians_data[1]["_id"],
                "technician_name": "Sarah Miller",
                "due_date": datetime.utcnow() + timedelta(days=8),
                "estimated_hours": 6,
                "actual_hours": 4.5,
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "job_number": "JOB-003",
                "order_id": orders_data[2]["_id"],
                "description": "Splicing Work",
                "location": "4 Paintapple Ave, Mountains, TX",
                "priority": "low",
                "status": "completed",
                "progress": 100,
                "assigned_to": technicians_data[2]["_id"],
                "technician_name": "Brian Harris",
                "due_date": datetime.utcnow() + timedelta(days=11),
                "estimated_hours": 4,
                "actual_hours": 4,
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "job_number": "JOB-004",
                "order_id": orders_data[0]["_id"],
                "description": "Network Testing",
                "location": "789 Pine Rd, Austin, TX",
                "priority": "high",
                "status": "scheduled",
                "progress": 0,
                "assigned_to": technicians_data[3]["_id"],
                "technician_name": "Emily Davis",
                "due_date": datetime.utcnow() + timedelta(days=1),
                "estimated_hours": 3,
                "actual_hours": 0,
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "job_number": "JOB-005",
                "order_id": orders_data[1]["_id"],
                "description": "Equipment Setup",
                "location": "789 Pine Rd, Austin, TX",
                "priority": "medium",
                "status": "scheduled",
                "progress": 0,
                "assigned_to": technicians_data[4]["_id"],
                "technician_name": "Michael Chen",
                "due_date": datetime.utcnow() + timedelta(days=2),
                "estimated_hours": 5,
                "actual_hours": 0,
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        for job in jobs_data:
            await db.jobs.update_one(
                {"job_number": job["job_number"], "tenant_id": tenant_id},
                {"$set": job},
                upsert=True
            )
        print(f"✅ Created {len(jobs_data)} jobs")
        
        # Create sample vendors
        vendors_data = [
            {
                "_id": ObjectId(),
                "name": "FiberMax Supplies",
                "email": "sales@fibermax.com",
                "phone": "+1-555-2001",
                "specialization": "Fiber Optic Equipment",
                "status": "active",
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "name": "CablePro Solutions",
                "email": "info@cablepro.com",
                "phone": "+1-555-2002",
                "specialization": "Cable and Wiring",
                "status": "active",
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        for vendor in vendors_data:
            await db.vendors.update_one(
                {"email": vendor["email"], "tenant_id": tenant_id},
                {"$set": vendor},
                upsert=True
            )
        print(f"✅ Created {len(vendors_data)} vendors")
        
        print("\n🎉 Sample data initialization completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Orders: {len(orders_data)}")
        print(f"   - Jobs: {len(jobs_data)}")
        print(f"   - Technicians: {len(technicians_data)}")
        print(f"   - Vendors: {len(vendors_data)}")
        
        # Close connection
        client.close()
        
    except Exception as e:
        print(f"❌ Error initializing sample data: {str(e)}")
        raise

async def main():
    """Main function."""
    await init_sample_data()

if __name__ == "__main__":
    asyncio.run(main())
