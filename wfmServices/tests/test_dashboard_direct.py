#!/usr/bin/env python3
"""
Direct database test for dashboard metrics to isolate the issue.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import traceback

# Database configuration
MONGODB_URL = "mongodb+srv://wfmadmin:tsarolabs%4012345%23@wfmdb.cvkb04l.mongodb.net/?retryWrites=true&w=majority&appName=wfmDB"
DATABASE_NAME = "wfm"
TENANT_ID = "689b4041eba2c2b9886c1b96"

async def test_dashboard_logic():
    """Test the dashboard logic directly."""
    print("🧪 Testing Dashboard Logic Directly")
    print("=" * 50)
    
    try:
        # Connect to database
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        print("✅ Connected to MongoDB")
        
        # Convert tenant_id to ObjectId
        tenant_object_id = ObjectId(TENANT_ID)
        print(f"🆔 Tenant ID: {TENANT_ID}")
        print(f"🆔 Tenant ObjectId: {tenant_object_id}")
        
        # Check collections
        collections = await db.list_collection_names()
        print(f"📁 Available collections: {collections}")
        
        # Test each metric calculation
        print(f"\n📊 Testing metric calculations...")
        
        # Get active jobs
        if "jobs" in collections:
            print("   Testing active jobs count...")
            active_jobs_pipeline = [
                {"$match": {"tenant_id": tenant_object_id, "status": {"$ne": "completed"}}},
                {"$count": "count"}
            ]
            active_jobs_result = await db.jobs.aggregate(active_jobs_pipeline).to_list(1)
            active_jobs_count = active_jobs_result[0]["count"] if active_jobs_result else 0
            print(f"   ✅ Active jobs: {active_jobs_count}")
        else:
            print("   ⚠️ Jobs collection not found")
            active_jobs_count = 0
        
        # Get technicians
        if "technicians" in collections:
            print("   Testing technicians count...")
            available_technicians_pipeline = [
                {"$match": {"tenant_id": tenant_object_id, "status": "available"}},
                {"$count": "count"}
            ]
            available_technicians_result = await db.technicians.aggregate(available_technicians_pipeline).to_list(1)
            available_technicians_count = available_technicians_result[0]["count"] if available_technicians_result else 0
            print(f"   ✅ Available technicians: {available_technicians_count}")
        else:
            print("   ⚠️ Technicians collection not found")
            available_technicians_count = 0
        
        # Get total jobs
        if "jobs" in collections:
            print("   Testing total jobs count...")
            total_jobs_pipeline = [
                {"$match": {"tenant_id": tenant_object_id}},
                {"$count": "count"}
            ]
            total_jobs_result = await db.jobs.aggregate(total_jobs_pipeline).to_list(1)
            total_jobs_count = total_jobs_result[0]["count"] if total_jobs_result else 0
            print(f"   ✅ Total jobs: {total_jobs_count}")
        else:
            print("   ⚠️ Jobs collection not found")
            total_jobs_count = 0
        
        # Create metrics response
        metrics = {
            "active_jobs": {
                "count": active_jobs_count,
                "change_percentage": 12,
                "change_direction": "up"
            },
            "available_technicians": {
                "count": available_technicians_count,
                "change_percentage": 5,
                "change_direction": "up"
            },
            "scheduled_today": {
                "count": 0,
                "change_percentage": 0,
                "change_direction": "neutral"
            },
            "completion_rate": {
                "percentage": 0,
                "change_percentage": 0,
                "change_direction": "neutral"
            }
        }
        
        print(f"\n✅ Metrics calculated successfully!")
        print(f"📊 Active Jobs: {metrics['active_jobs']['count']}")
        print(f"👥 Available Technicians: {metrics['available_technicians']['count']}")
        
        return metrics
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"📝 Traceback: {traceback.format_exc()}")
        return None

async def main():
    """Main function."""
    await test_dashboard_logic()

if __name__ == "__main__":
    asyncio.run(main())
