"""
Business logic for Vendor Service.
"""
from typing import List, Optional
from datetime import datetime
from shared.models import PaginationParams
from .models import (
    Vendor, VendorCreate, VendorUpdate, VendorResponse,
    Technician, TechnicianCreate, TechnicianUpdate, TechnicianResponse,
    Lead, LeadCreate, LeadUpdate, LeadResponse,
    TaskAssignment
)
from .repository import VendorRepository, TechnicianRepository, LeadRepository


class VendorService:
    """Service for vendor management."""
    
    def __init__(self, vendor_repo: VendorRepository, technician_repo: TechnicianRepository, lead_repo: LeadRepository):
        self.vendor_repo = vendor_repo
        self.technician_repo = technician_repo
        self.lead_repo = lead_repo
    
    async def create_vendor(self, vendor_data: VendorCreate) -> VendorResponse:
        """Create a new vendor."""
        vendor = Vendor(
            **vendor_data.model_dump(),
            technician_count=0,
            lead_count=0
        )
        created_vendor = await self.vendor_repo.create(vendor)
        return VendorResponse(**created_vendor.model_dump())
    
    async def get_vendor(self, vendor_id: str, tenant_id: str) -> Optional[VendorResponse]:
        """Get vendor by ID."""
        vendor = await self.vendor_repo.get_by_id(vendor_id, tenant_id)
        if not vendor:
            return None
        
        # Update counts
        technicians = await self.technician_repo.get_by_vendor(vendor_id, tenant_id)
        leads = await self.lead_repo.get_by_vendor(vendor_id, tenant_id)
        vendor.technician_count = len(technicians)
        vendor.lead_count = len(leads)
        
        return VendorResponse(**vendor.model_dump())
    
    async def get_vendors(self, tenant_id: str, pagination: PaginationParams) -> List[VendorResponse]:
        """Get all vendors for a tenant."""
        vendors = await self.vendor_repo.get_all(tenant_id, pagination)
        vendor_responses = []
        
        for vendor in vendors:
            # Update counts
            technicians = await self.technician_repo.get_by_vendor(vendor.id, tenant_id)
            leads = await self.lead_repo.get_by_vendor(vendor.id, tenant_id)
            vendor.technician_count = len(technicians)
            vendor.lead_count = len(leads)
            vendor_responses.append(VendorResponse(**vendor.model_dump()))
        
        return vendor_responses
    
    async def update_vendor(self, vendor_id: str, tenant_id: str, update_data: VendorUpdate) -> Optional[VendorResponse]:
        """Update vendor."""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        updated_vendor = await self.vendor_repo.update(vendor_id, tenant_id, update_dict)
        return VendorResponse(**updated_vendor.model_dump()) if updated_vendor else None
    
    async def delete_vendor(self, vendor_id: str, tenant_id: str) -> bool:
        """Delete vendor."""
        return await self.vendor_repo.delete(vendor_id, tenant_id)
    
    async def create_technician(self, technician_data: TechnicianCreate) -> TechnicianResponse:
        """Create a new technician."""
        technician = Technician(
            **technician_data.model_dump(),
            current_task_count=0
        )
        created_technician = await self.technician_repo.create(technician)
        
        # Update vendor technician count
        await self.vendor_repo.update(
            technician_data.vendor_id,
            technician_data.tenant_id,
            {"$inc": {"technician_count": 1}}
        )
        
        return TechnicianResponse(**created_technician.model_dump())
    
    async def get_technician(self, technician_id: str, tenant_id: str) -> Optional[TechnicianResponse]:
        """Get technician by ID."""
        technician = await self.technician_repo.get_by_id(technician_id, tenant_id)
        return TechnicianResponse(**technician.model_dump()) if technician else None
    
    async def get_technicians_by_vendor(self, vendor_id: str, tenant_id: str) -> List[TechnicianResponse]:
        """Get all technicians for a vendor."""
        technicians = await self.technician_repo.get_by_vendor(vendor_id, tenant_id)
        return [TechnicianResponse(**tech.model_dump()) for tech in technicians]
    
    async def get_available_technicians(self, required_skills: List[str], tenant_id: str) -> List[TechnicianResponse]:
        """Get available technicians with required skills."""
        technicians = await self.technician_repo.get_by_skills(required_skills, tenant_id)
        # Filter by availability and current task load
        available_technicians = [
            tech for tech in technicians 
            if tech.current_task_count < tech.max_concurrent_tasks and tech.status == "active"
        ]
        return [TechnicianResponse(**tech.model_dump()) for tech in available_technicians]
    
    async def update_technician(self, technician_id: str, tenant_id: str, update_data: TechnicianUpdate) -> Optional[TechnicianResponse]:
        """Update technician."""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        updated_technician = await self.technician_repo.update(technician_id, tenant_id, update_dict)
        return TechnicianResponse(**updated_technician.model_dump()) if updated_technician else None
    
    async def delete_technician(self, technician_id: str, tenant_id: str) -> bool:
        """Delete technician."""
        technician = await self.technician_repo.get_by_id(technician_id, tenant_id)
        if not technician:
            return False
        
        result = await self.technician_repo.delete(technician_id, tenant_id)
        if result:
            # Update vendor technician count
            await self.vendor_repo.update(
                technician.vendor_id,
                tenant_id,
                {"$inc": {"technician_count": -1}}
            )
        return result
    
    async def create_lead(self, lead_data: LeadCreate) -> LeadResponse:
        """Create a new lead."""
        lead = Lead(
            **lead_data.model_dump(),
            current_managed_count=len(lead_data.managed_technicians)
        )
        created_lead = await self.lead_repo.create(lead)
        
        # Update vendor lead count
        await self.vendor_repo.update(
            lead_data.vendor_id,
            lead_data.tenant_id,
            {"$inc": {"lead_count": 1}}
        )
        
        return LeadResponse(**created_lead.model_dump())
    
    async def get_lead(self, lead_id: str, tenant_id: str) -> Optional[LeadResponse]:
        """Get lead by ID."""
        lead = await self.lead_repo.get_by_id(lead_id, tenant_id)
        return LeadResponse(**lead.model_dump()) if lead else None
    
    async def get_leads_by_vendor(self, vendor_id: str, tenant_id: str) -> List[LeadResponse]:
        """Get all leads for a vendor."""
        leads = await self.lead_repo.get_by_vendor(vendor_id, tenant_id)
        return [LeadResponse(**lead.model_dump()) for lead in leads]
    
    async def get_lead_for_technician(self, technician_id: str, tenant_id: str) -> Optional[LeadResponse]:
        """Get the lead managing a specific technician."""
        lead = await self.lead_repo.get_by_technician(technician_id, tenant_id)
        return LeadResponse(**lead.model_dump()) if lead else None
    
    async def update_lead(self, lead_id: str, tenant_id: str, update_data: LeadUpdate) -> Optional[LeadResponse]:
        """Update lead."""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        if "managed_technicians" in update_dict:
            update_dict["current_managed_count"] = len(update_dict["managed_technicians"])
        
        updated_lead = await self.lead_repo.update(lead_id, tenant_id, update_dict)
        return LeadResponse(**updated_lead.model_dump()) if updated_lead else None
    
    async def delete_lead(self, lead_id: str, tenant_id: str) -> bool:
        """Delete lead."""
        lead = await self.lead_repo.get_by_id(lead_id, tenant_id)
        if not lead:
            return False
        
        result = await self.lead_repo.delete(lead_id, tenant_id)
        if result:
            # Update vendor lead count
            await self.vendor_repo.update(
                lead.vendor_id,
                tenant_id,
                {"$inc": {"lead_count": -1}}
            )
        return result
    
    async def assign_task(self, task_id: str, technician_id: str, tenant_id: str) -> Optional[TaskAssignment]:
        """Assign a task to a technician and their lead."""
        # Get technician
        technician = await self.technician_repo.get_by_id(technician_id, tenant_id)
        if not technician or technician.current_task_count >= technician.max_concurrent_tasks:
            return None
        
        # Get lead for this technician
        lead = await self.lead_repo.get_by_technician(technician_id, tenant_id)
        if not lead:
            return None
        
        # Create assignment
        assignment = TaskAssignment(
            task_id=task_id,
            technician_id=technician_id,
            lead_id=lead.id
        )
        
        # Update technician task count
        await self.technician_repo.update(
            technician_id,
            tenant_id,
            {"$inc": {"current_task_count": 1}}
        )
        
        return assignment
    
    async def unassign_task(self, task_id: str, technician_id: str, tenant_id: str) -> bool:
        """Unassign a task from a technician."""
        # Update technician task count
        result = await self.technician_repo.update(
            technician_id,
            tenant_id,
            {"$inc": {"current_task_count": -1}}
        )
        return result is not None
