"""
Data models for Vendor Service.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from shared.models import BaseEntity, StatusEnum, PriorityEnum


class VendorCreate(BaseModel):
    """Vendor creation model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    service_areas: List[str] = Field(default_factory=list)
    tenant_id: str
    status: StatusEnum = StatusEnum.ACTIVE


class VendorUpdate(BaseModel):
    """Vendor update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    capabilities: Optional[List[str]] = None
    service_areas: Optional[List[str]] = None
    status: Optional[StatusEnum] = None


class VendorResponse(BaseEntity):
    """Vendor response model."""
    name: str
    description: Optional[str] = None
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    status: StatusEnum
    capabilities: List[str]
    service_areas: List[str]
    technician_count: int = Field(default=0)
    lead_count: int = Field(default=0)


class Vendor(BaseEntity):
    """Vendor entity model."""
    name: str
    description: Optional[str] = None
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    status: StatusEnum
    capabilities: List[str]
    service_areas: List[str]
    technician_count: int = Field(default=0)
    lead_count: int = Field(default=0)


class TechnicianCreate(BaseModel):
    """Technician creation model."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    vendor_id: str = Field(..., description="ID of the vendor this technician belongs to")
    skills: List[str] = Field(default_factory=list)
    experience_years: int = Field(default=0, ge=0)
    availability: Dict[str, Any] = Field(default_factory=dict)
    max_concurrent_tasks: int = Field(default=3, ge=1, le=10)
    tenant_id: str
    status: StatusEnum = StatusEnum.ACTIVE


class TechnicianUpdate(BaseModel):
    """Technician update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0)
    availability: Optional[Dict[str, Any]] = None
    max_concurrent_tasks: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[StatusEnum] = None


class TechnicianResponse(BaseEntity):
    """Technician response model."""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    vendor_id: str
    skills: List[str]
    experience_years: int
    availability: Dict[str, Any]
    max_concurrent_tasks: int
    current_task_count: int = Field(default=0)
    status: StatusEnum


class Technician(BaseEntity):
    """Technician entity model."""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    vendor_id: str
    skills: List[str]
    experience_years: int
    availability: Dict[str, Any]
    max_concurrent_tasks: int
    current_task_count: int = Field(default=0)
    status: StatusEnum


class LeadCreate(BaseModel):
    """Lead creation model."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    vendor_id: str = Field(..., description="ID of the vendor this lead belongs to")
    managed_technicians: List[str] = Field(default_factory=list, description="List of technician IDs managed by this lead")
    max_managed_technicians: int = Field(default=10, ge=1, le=50)
    tenant_id: str
    status: StatusEnum = StatusEnum.ACTIVE


class LeadUpdate(BaseModel):
    """Lead update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    managed_technicians: Optional[List[str]] = None
    max_managed_technicians: Optional[int] = Field(None, ge=1, le=50)
    status: Optional[StatusEnum] = None


class LeadResponse(BaseEntity):
    """Lead response model."""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    vendor_id: str
    managed_technicians: List[str]
    max_managed_technicians: int
    current_managed_count: int = Field(default=0)
    status: StatusEnum


class Lead(BaseEntity):
    """Lead entity model."""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    vendor_id: str
    managed_technicians: List[str]
    max_managed_technicians: int
    current_managed_count: int = Field(default=0)
    status: StatusEnum


class TaskAssignment(BaseModel):
    """Task assignment model."""
    task_id: str
    technician_id: str
    lead_id: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
