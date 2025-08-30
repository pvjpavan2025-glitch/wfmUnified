"""
Vendor Service FastAPI application.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query
from typing import List, Optional
from shared.auth import get_current_user, TokenData
from shared.models import PaginationParams, SuccessResponse, ErrorResponse
from shared.database import db_manager
from .models import (
    VendorCreate, VendorUpdate, VendorResponse,
    TechnicianCreate, TechnicianUpdate, TechnicianResponse,
    LeadCreate, LeadUpdate, LeadResponse,
    TaskAssignment
)
from .service import VendorService
from .repository import VendorRepository, TechnicianRepository, LeadRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await db_manager.connect_mongodb()
    yield
    # Shutdown
    await db_manager.close()


app = FastAPI(
    title="Vendor Service",
    description="Manages vendors, technicians, and leads",
    version="1.0.0",
    lifespan=lifespan
)


async def get_vendor_service() -> VendorService:
    """Dependency injection for VendorService."""
    database = await db_manager.get_database()
    vendor_repo = VendorRepository(database)
    technician_repo = TechnicianRepository(database)
    lead_repo = LeadRepository(database)
    return VendorService(vendor_repo, technician_repo, lead_repo)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "vendor_service"}


# Vendor endpoints
@app.post("/vendors", response_model=VendorResponse)
async def create_vendor(
    vendor_data: VendorCreate,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Create a new vendor."""
    return await service.create_vendor(vendor_data)


@app.get("/vendors/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: str,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Get vendor by ID."""
    vendor = await service.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@app.get("/vendors", response_model=List[VendorResponse])
async def get_vendors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: TokenData = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Get all vendors."""
    pagination = PaginationParams(skip=skip, limit=limit)
    tenant_id = current_user.tenant_id
    return await service.get_vendors(tenant_id, pagination)


@app.put("/vendors/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: str,
    update_data: VendorUpdate,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Update vendor."""
    vendor = await service.update_vendor(vendor_id, update_data)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@app.delete("/vendors/{vendor_id}", response_model=SuccessResponse)
async def delete_vendor(
    vendor_id: str,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Delete vendor."""
    success = await service.delete_vendor(vendor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return SuccessResponse(message="Vendor deleted successfully")


# Technician endpoints
@app.post("/technicians", response_model=TechnicianResponse)
async def create_technician(
    technician_data: TechnicianCreate,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Create a new technician."""
    return await service.create_technician(technician_data)


@app.get("/technicians/{technician_id}", response_model=TechnicianResponse)
async def get_technician(
    technician_id: str,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Get technician by ID."""
    technician = await service.get_technician(technician_id)
    if not technician:
        raise HTTPException(status_code=404, detail="Technician not found")
    return technician


@app.get("/vendors/{vendor_id}/technicians", response_model=List[TechnicianResponse])
async def get_technicians_by_vendor(
    vendor_id: str,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Get all technicians for a vendor."""
    return await service.get_technicians_by_vendor(vendor_id)


@app.get("/technicians/available", response_model=List[TechnicianResponse])
async def get_available_technicians(
    skills: List[str] = Query(..., description="Required skills"),
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Get available technicians with required skills."""
    return await service.get_available_technicians(skills)


@app.put("/technicians/{technician_id}", response_model=TechnicianResponse)
async def update_technician(
    technician_id: str,
    update_data: TechnicianUpdate,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Update technician."""
    technician = await service.update_technician(technician_id, update_data)
    if not technician:
        raise HTTPException(status_code=404, detail="Technician not found")
    return technician


@app.delete("/technicians/{technician_id}", response_model=SuccessResponse)
async def delete_technician(
    technician_id: str,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Delete technician."""
    success = await service.delete_technician(technician_id)
    if not success:
        raise HTTPException(status_code=404, detail="Technician not found")
    return SuccessResponse(message="Technician deleted successfully")


# Lead endpoints
@app.post("/leads", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Create a new lead."""
    return await service.create_lead(lead_data)


@app.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Get lead by ID."""
    lead = await service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.get("/vendors/{vendor_id}/leads", response_model=List[LeadResponse])
async def get_leads_by_vendor(
    vendor_id: str,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Get all leads for a vendor."""
    return await service.get_leads_by_vendor(vendor_id)


@app.get("/technicians/{technician_id}/lead", response_model=LeadResponse)
async def get_lead_for_technician(
    technician_id: str,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Get the lead managing a specific technician."""
    lead = await service.get_lead_for_technician(technician_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found for technician")
    return lead


@app.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    update_data: LeadUpdate,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Update lead."""
    lead = await service.update_lead(lead_id, update_data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.delete("/leads/{lead_id}", response_model=SuccessResponse)
async def delete_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Delete lead."""
    success = await service.delete_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return SuccessResponse(message="Lead deleted successfully")


# Task assignment endpoints
@app.post("/tasks/{task_id}/assign", response_model=TaskAssignment)
async def assign_task(
    task_id: str,
    technician_id: str,
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Assign a task to a technician and their lead."""
    assignment = await service.assign_task(task_id, technician_id)
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
    current_user: dict = Depends(get_current_user),
    service: VendorService = Depends(get_vendor_service)
):
    """Unassign a task from a technician."""
    success = await service.unassign_task(task_id, technician_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task assignment not found")
    return SuccessResponse(message="Task unassigned successfully")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
