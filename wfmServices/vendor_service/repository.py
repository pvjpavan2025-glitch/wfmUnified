"""
Repository layer for Vendor Service.
"""
from typing import List, Optional
from datetime import datetime
import motor.motor_asyncio
from shared.models import PaginationParams
from .models import Vendor, Technician, Lead


class VendorRepository:
    """Repository for vendor operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.db = database
        self.collection = self.db.vendors
    
    async def create(self, vendor: Vendor) -> Vendor:
        """Create a new vendor."""
        vendor_dict = vendor.model_dump(by_alias=True)
        result = await self.collection.insert_one(vendor_dict)
        vendor.id = str(result.inserted_id)
        return vendor
    
    async def get_by_id(self, vendor_id: str, tenant_id: str) -> Optional[Vendor]:
        """Get vendor by ID."""
        vendor_dict = await self.collection.find_one({
            "_id": vendor_id,
            "tenant_id": tenant_id
        })
        return Vendor(**vendor_dict) if vendor_dict else None
    
    async def get_all(self, tenant_id: str, pagination: PaginationParams) -> List[Vendor]:
        """Get all vendors for a tenant."""
        cursor = self.collection.find({"tenant_id": tenant_id})
        cursor = cursor.skip(pagination.skip).limit(pagination.limit)
        vendors = []
        async for vendor_dict in cursor:
            vendors.append(Vendor(**vendor_dict))
        return vendors
    
    async def update(self, vendor_id: str, tenant_id: str, update_data: dict) -> Optional[Vendor]:
        """Update vendor."""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": vendor_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )
        if result.modified_count:
            return await self.get_by_id(vendor_id, tenant_id)
        return None
    
    async def delete(self, vendor_id: str, tenant_id: str) -> bool:
        """Delete vendor."""
        result = await self.collection.delete_one({
            "_id": vendor_id,
            "tenant_id": tenant_id
        })
        return result.deleted_count > 0


class TechnicianRepository:
    """Repository for technician operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.db = database
        self.collection = self.db.technicians
    
    async def create(self, technician: Technician) -> Technician:
        """Create a new technician."""
        technician_dict = technician.model_dump(by_alias=True)
        result = await self.collection.insert_one(technician_dict)
        technician.id = str(result.inserted_id)
        return technician
    
    async def get_by_id(self, technician_id: str, tenant_id: str) -> Optional[Technician]:
        """Get technician by ID."""
        technician_dict = await self.collection.find_one({
            "_id": technician_id,
            "tenant_id": tenant_id
        })
        return Technician(**technician_dict) if technician_dict else None
    
    async def get_by_vendor(self, vendor_id: str, tenant_id: str) -> List[Technician]:
        """Get all technicians for a vendor."""
        cursor = self.collection.find({
            "vendor_id": vendor_id,
            "tenant_id": tenant_id
        })
        technicians = []
        async for technician_dict in cursor:
            technicians.append(Technician(**technician_dict))
        return technicians
    
    async def get_by_skills(self, skills: List[str], tenant_id: str) -> List[Technician]:
        """Get technicians by required skills."""
        cursor = self.collection.find({
            "skills": {"$in": skills},
            "tenant_id": tenant_id,
            "status": "active"
        })
        technicians = []
        async for technician_dict in cursor:
            technicians.append(Technician(**technician_dict))
        return technicians
    
    async def update(self, technician_id: str, tenant_id: str, update_data: dict) -> Optional[Technician]:
        """Update technician."""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": technician_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )
        if result.modified_count:
            return await self.get_by_id(technician_id, tenant_id)
        return None
    
    async def delete(self, technician_id: str, tenant_id: str) -> bool:
        """Delete technician."""
        result = await self.collection.delete_one({
            "_id": technician_id,
            "tenant_id": tenant_id
        })
        return result.deleted_count > 0


class LeadRepository:
    """Repository for lead operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.db = database
        self.collection = self.db.leads
    
    async def create(self, lead: Lead) -> Lead:
        """Create a new lead."""
        lead_dict = lead.model_dump(by_alias=True)
        result = await self.collection.insert_one(lead_dict)
        lead.id = str(result.inserted_id)
        return lead
    
    async def get_by_id(self, lead_id: str, tenant_id: str) -> Optional[Lead]:
        """Get lead by ID."""
        lead_dict = await self.collection.find_one({
            "_id": lead_id,
            "tenant_id": tenant_id
        })
        return Lead(**lead_dict) if lead_dict else None
    
    async def get_by_vendor(self, vendor_id: str, tenant_id: str) -> List[Lead]:
        """Get all leads for a vendor."""
        cursor = self.collection.find({
            "vendor_id": vendor_id,
            "tenant_id": tenant_id
        })
        leads = []
        async for lead_dict in cursor:
            leads.append(Lead(**lead_dict))
        return leads
    
    async def get_by_technician(self, technician_id: str, tenant_id: str) -> Optional[Lead]:
        """Get lead managing a specific technician."""
        lead_dict = await self.collection.find_one({
            "managed_technicians": technician_id,
            "tenant_id": tenant_id
        })
        return Lead(**lead_dict) if lead_dict else None
    
    async def update(self, lead_id: str, tenant_id: str, update_data: dict) -> Optional[Lead]:
        """Update lead."""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": lead_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )
        if result.modified_count:
            return await self.get_by_id(lead_id, tenant_id)
        return None
    
    async def delete(self, lead_id: str, tenant_id: str) -> bool:
        """Delete lead."""
        result = await self.collection.delete_one({
            "_id": lead_id,
            "tenant_id": tenant_id
        })
        return result.deleted_count > 0
