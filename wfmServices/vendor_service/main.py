"""
Vendor Service FastAPI application.
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from typing import List, Optional
from shared.auth import get_current_user, get_tenant_id
from shared.models import PaginationParams, SuccessResponse, ErrorResponse
from .models import (
    VendorCreate, VendorUpdate, VendorResponse,
    TechnicianCreate, TechnicianUpdate, TechnicianResponse,
    LeadCreate, LeadUpdate, LeadResponse,
    TaskAssignment
)
from .service import VendorService

app = FastAPI(
    title="Vendor Service",
    description="Manages vendors, technicians, and leads",
    version="1.0.0"
)

vendor_service = VendorService()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "vendor_service"}


# Vendor endpoints
@app.post("/vendors", response_model=VendorResponse)
async def create_vendor(
    vendor_data: VendorCreate,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Create a new vendor."""
    vendor_data.tenant_id = tenant_id
    return await vendor_service.create_vendor(vendor_data)


@app.get("/vendors/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get vendor by ID."""
    vendor = await vendor_service.get_vendor(vendor_id, tenant_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@app.get("/vendors", response_model=List[VendorResponse])
async def get_vendors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get all vendors."""
    pagination = PaginationParams(skip=skip, limit=limit)
    return await vendor_service.get_vendors(tenant_id, pagination)


@app.put("/vendors/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: str,
    update_data: VendorUpdate,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Update vendor."""
    vendor = await vendor_service.update_vendor(vendor_id, tenant_id, update_data)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@app.delete("/vendors/{vendor_id}", response_model=SuccessResponse)
async def delete_vendor(
    vendor_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Delete vendor."""
    success = await vendor_service.delete_vendor(vendor_id, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return SuccessResponse(message="Vendor deleted successfully")


# Technician endpoints
@app.post("/technicians", response_model=TechnicianResponse)
async def create_technician(
    technician_data: TechnicianCreate,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Create a new technician."""
    technician_data.tenant_id = tenant_id
    return await vendor_service.create_technician(technician_data)


@app.get("/technicians/{technician_id}", response_model=TechnicianResponse)
async def get_technician(
    technician_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get technician by ID."""
    technician = await vendor_service.get_technician(technician_id, tenant_id)
    if not technician:
        raise HTTPException(status_code=404, detail="Technician not found")
    return technician


@app.get("/vendors/{vendor_id}/technicians", response_model=List[TechnicianResponse])
async def get_technicians_by_vendor(
    vendor_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get all technicians for a vendor."""
    return await vendor_service.get_technicians_by_vendor(vendor_id, tenant_id)


@app.get("/technicians/available", response_model=List[TechnicianResponse])
async def get_available_technicians(
    skills: List[str] = Query(..., description="Required skills"),
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get available technicians with required skills."""
    return await vendor_service.get_available_technicians(skills, tenant_id)


@app.put("/technicians/{technician_id}", response_model=TechnicianResponse)
async def update_technician(
    technician_id: str,
    update_data: TechnicianUpdate,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Update technician."""
    technician = await vendor_service.update_technician(technician_id, tenant_id, update_data)
    if not technician:
        raise HTTPException(status_code=404, detail="Technician not found")
    return technician


@app.delete("/technicians/{technician_id}", response_model=SuccessResponse)
async def delete_technician(
    technician_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Delete technician."""
    success = await vendor_service.delete_technician(technician_id, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Technician not found")
    return SuccessResponse(message="Technician deleted successfully")


# Lead endpoints
@app.post("/leads", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Create a new lead."""
    lead_data.tenant_id = tenant_id
    return await vendor_service.create_lead(lead_data)


@app.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get lead by ID."""
    lead = await vendor_service.get_lead(lead_id, tenant_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.get("/vendors/{vendor_id}/leads", response_model=List[LeadResponse])
async def get_leads_by_vendor(
    vendor_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get all leads for a vendor."""
    return await vendor_service.get_leads_by_vendor(vendor_id, tenant_id)


@app.get("/technicians/{technician_id}/lead", response_model=LeadResponse)
async def get_lead_for_technician(
    technician_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get the lead managing a specific technician."""
    lead = await vendor_service.get_lead_for_technician(technician_id, tenant_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found for technician")
    return lead


@app.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    update_data: LeadUpdate,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Update lead."""
    lead = await vendor_service.update_lead(lead_id, tenant_id, update_data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.delete("/leads/{lead_id}", response_model=SuccessResponse)
async def delete_lead(
    lead_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Delete lead."""
    success = await vendor_service.delete_lead(lead_id, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return SuccessResponse(message="Lead deleted successfully")


# Task assignment endpoints
@app.post("/tasks/{task_id}/assign", response_model=TaskAssignment)
async def assign_task(
    task_id: str,
    technician_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Assign a task to a technician and their lead."""
    assignment = await vendor_service.assign_task(task_id, technician_id, tenant_id)
    if not assignment:
        raise HTTPException(
            status_code=400, 
            detail="Cannot assign task - technician not available or no lead found"
        )
    return assignment


@app.delete("/tasks/{task_id}/unassign", response_model=SuccessResponse)
async def unassign_task(
    task_id: str,
    technician_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Unassign a task from a technician."""
    success = await vendor_service.unassign_task(task_id, technician_id, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task assignment not found")
    return SuccessResponse(message="Task unassigned successfully")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
