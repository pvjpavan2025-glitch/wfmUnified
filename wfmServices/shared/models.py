"""
Shared data models for WFM microservices.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from enum import Enum


class BaseEntity(BaseModel):
    """Base entity with common fields."""
    id: Optional[str] = Field(None, alias="_id")
    tenant_id: str = Field(..., description="Tenant identifier for multi-tenancy")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    # Pydantic v2 config
    model_config = ConfigDict(populate_by_name=True)


class StatusEnum(str, Enum):
    """Common status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    READY = "ready"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    OPEN = "open"
    CLOSED = "closed"
    PAUSED = "paused"
    BLOCKED = "blocked"


class PriorityEnum(str, Enum):
    """Priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class RoleStatus(str, Enum):
    """Role status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class TenantStatus(str, Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class AuditLog(BaseModel):
    """Audit log entry."""
    action: str
    resource_type: str
    resource_id: str
    user_id: str
    tenant_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    skip: int
    limit: int
    has_more: bool


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Success response model."""
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    service: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: Optional[str] = None
    dependencies: Optional[Dict[str, str]] = None


class User(BaseEntity):
    """User model."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    last_login: Optional[datetime] = None


class Role(BaseEntity):
    """Role model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    status: RoleStatus = Field(default=RoleStatus.ACTIVE)


class Job(BaseEntity):
    """Job model."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    status: StatusEnum = Field(default=StatusEnum.PENDING)
    assigned_analyst_id: Optional[str] = None
    deadline: Optional[datetime] = None
    required_skills: List[str] = Field(default_factory=list)
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None


class Analyst(BaseEntity):
    """Analyst model."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    skills: List[str] = Field(default_factory=list)
    experience_years: int = Field(default=0, ge=0)
    max_jobs: int = Field(default=5, ge=1)
    availability: Dict[str, Any] = Field(default_factory=dict)
    status: StatusEnum = Field(default=StatusEnum.ACTIVE)


class Issue(BaseEntity):
    """Issue model."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    category: str = Field(..., min_length=1, max_length=100)
    assigned_to: Optional[str] = None
    reported_by: str
    job_id: Optional[str] = None
    status: StatusEnum = Field(default=StatusEnum.PENDING)
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None


class Rule(BaseEntity):
    """Rule model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    tag_name: str = Field(..., min_length=1, max_length=50)
    sequence: int = Field(default=0, ge=0)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    status: StatusEnum = Field(default=StatusEnum.ACTIVE)


class Configuration(BaseEntity):
    """Configuration model."""
    key: str = Field(..., min_length=1, max_length=100)
    value: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
    category: str = Field(default="general", min_length=1, max_length=50)
    is_encrypted: bool = Field(default=False)


class Report(BaseEntity):
    """Report model."""
    name: str = Field(..., min_length=1, max_length=100)
    report_type: str = Field(..., min_length=1, max_length=50)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: StatusEnum = Field(default=StatusEnum.PENDING)
    generated_at: Optional[datetime] = None
    file_path: Optional[str] = None


class Vendor(BaseEntity):
    """Vendor model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    status: StatusEnum = Field(default=StatusEnum.ACTIVE)
    capabilities: List[str] = Field(default_factory=list)
    service_areas: List[str] = Field(default_factory=list)


class Technician(BaseEntity):
    """Technician model - belongs to a vendor."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    vendor_id: str = Field(..., description="ID of the vendor this technician belongs to")
    skills: List[str] = Field(default_factory=list)
    experience_years: int = Field(default=0, ge=0)
    availability: Dict[str, Any] = Field(default_factory=dict)
    status: StatusEnum = Field(default=StatusEnum.ACTIVE)
    max_concurrent_tasks: int = Field(default=3, ge=1, le=10)
    current_task_count: int = Field(default=0, ge=0)


class Lead(BaseEntity):
    """Lead/Manager model - manages technicians."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    vendor_id: str = Field(..., description="ID of the vendor this lead belongs to")
    managed_technicians: List[str] = Field(default_factory=list, description="List of technician IDs managed by this lead")
    status: StatusEnum = Field(default=StatusEnum.ACTIVE)
    max_managed_technicians: int = Field(default=10, ge=1, le=50) 