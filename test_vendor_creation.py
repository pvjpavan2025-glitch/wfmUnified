#!/usr/bin/env python3
"""
Test script to verify vendor creation with proper ObjectId generation.
This bypasses the auth layer to directly test the repository fix.
"""
import asyncio
import json
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import sys
import os

# Add the wfmServices directory to the path
sys.path.append('/Users/nalinimanduva/Desktop/Latest/wfmUnified/wfmServices')

from vendor_service.models import VendorCreate, VendorCapability
from vendor_service.repository import VendorRepository
from shared.database import db_manager

async def test_vendor_creation():
    """Test vendor creation directly via repository to verify ObjectId generation."""
    
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['workforcedb']
    
    # Create repository
    vendor_repo = VendorRepository(db)
    
    # Create test vendor data
    test_vendor = VendorCreate(
        name="Test Vendor for ObjectId Fix",
        contact_email="test@vendor.com",
        contact_phone="+1234567890",
        address="123 Test Street",
        city="Test City",
        state="TS",
        zip_code="12345",
        country="Test Country",
        capabilities=[
            VendorCapability(
                category="installation",
                skill_level="expert",
                description="Expert installation services"
            )
        ],
        tenant_id="test_tenant_123"
    )
    
    print("Creating test vendor...")
    print(f"Test vendor data: {test_vendor.model_dump()}")
    
    try:
        # Create vendor
        created_vendor = await vendor_repo.create(test_vendor)
        
        print(f"\n✅ SUCCESS: Vendor created successfully!")
        print(f"Vendor ID: {created_vendor.id}")
        print(f"Vendor ID type: {type(created_vendor.id)}")
        print(f"Full vendor data: {created_vendor.model_dump()}")
        
        # Verify the ID is not null
        if created_vendor.id and created_vendor.id != "null":
            print(f"\n🎉 VERIFICATION PASSED: Vendor ID is properly generated and not null!")
            print(f"Generated ID: {created_vendor.id}")
        else:
            print(f"\n❌ VERIFICATION FAILED: Vendor ID is null or empty!")
            return False
            
        # Verify we can retrieve the vendor
        retrieved_vendor = await vendor_repo.get_by_id(created_vendor.id)
        if retrieved_vendor:
            print(f"\n✅ RETRIEVAL SUCCESS: Vendor can be retrieved by ID")
            print(f"Retrieved vendor: {retrieved_vendor.name}")
        else:
            print(f"\n❌ RETRIEVAL FAILED: Could not retrieve vendor by ID")
            return False
            
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to create vendor: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up - remove test vendor
        try:
            if 'created_vendor' in locals() and created_vendor.id:
                await vendor_repo.delete(created_vendor.id)
                print(f"\n🧹 CLEANUP: Test vendor deleted")
        except:
            pass
        client.close()


async def check_existing_null_vendors():
    """Check for any existing vendors with null IDs."""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['workforcedb']
    
    # Check for vendors with null _id
    null_id_vendors = list(db.vendors.find({"_id": None}))
    print(f"Found {len(null_id_vendors)} vendors with null _id")
    
    if null_id_vendors:
        print("Vendors with null _id:")
        for vendor in null_id_vendors:
            print(f"  - {vendor}")
    
    client.close()
    return len(null_id_vendors)


async def main():
    """Main test function."""
    print("=" * 80)
    print("TESTING VENDOR CREATION WITH OBJECTID FIX")
    print("=" * 80)
    
    # Check for existing null vendors
    print("\n1. Checking for existing null ID vendors...")
    null_count = await check_existing_null_vendors()
    
    if null_count > 0:
        print(f"⚠️  Warning: Found {null_count} vendors with null IDs")
    else:
        print("✅ No vendors with null IDs found")
    
    # Test vendor creation
    print("\n2. Testing vendor creation...")
    success = await test_vendor_creation()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 ALL TESTS PASSED! ObjectId generation is working correctly.")
    else:
        print("❌ TESTS FAILED! ObjectId generation still has issues.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
