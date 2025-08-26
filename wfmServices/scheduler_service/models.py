"""
Data models for Intelligent Scheduler Service.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from shared.models import BaseEntity, StatusEnum, PriorityEnum


class JobCreate(BaseModel):
    """Job creation model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    tasks: List[str] = Field(..., description="List of task IDs")
    priority: PriorityEnum = PriorityEnum.MEDIUM
    sla_hours: int = Field(default=24, ge=1, description="SLA in hours")
    tenant_id: str
    status: StatusEnum = StatusEnum.PENDING
    # Linkage to Orders: optional order identifier tying jobs to an order
    order_id: Optional[str] = Field(default=None, description="Associated order id")


class JobUpdate(BaseModel):
    """Job update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    tasks: Optional[List[str]] = None
    priority: Optional[PriorityEnum] = None
    sla_hours: Optional[int] = Field(None, ge=1)
    status: Optional[StatusEnum] = None


class JobResponse(BaseEntity):
    """Job response model."""
    name: str
    description: Optional[str] = None
    tasks: List[str]
    priority: PriorityEnum
    sla_hours: int
    status: StatusEnum
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    assigned_analyst: Optional[str] = None
    order_id: Optional[str] = None


class Job(BaseEntity):
    """Job entity model."""
    name: str
    description: Optional[str] = None
    tasks: List[str]
    priority: PriorityEnum
    sla_hours: int
    status: StatusEnum
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    assigned_analyst: Optional[str] = None
    order_id: Optional[str] = None


class AnalystCreate(BaseModel):
    """Analyst creation model."""
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., description="Analyst email")
    skills: List[str] = Field(default=[], description="List of skills")
    availability: Dict[str, Any] = Field(default={}, description="Availability schedule")
    max_concurrent_jobs: int = Field(default=5, ge=1, le=20)
    tenant_id: str
    status: StatusEnum = StatusEnum.ACTIVE


class AnalystUpdate(BaseModel):
    """Analyst update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = None
    skills: Optional[List[str]] = None
    availability: Optional[Dict[str, Any]] = None
    max_concurrent_jobs: Optional[int] = Field(None, ge=1, le=20)
    status: Optional[StatusEnum] = None


class AnalystResponse(BaseEntity):
    """Analyst response model."""
    name: str
    email: str
    skills: List[str]
    availability: Dict[str, Any]
    max_concurrent_jobs: int
    status: StatusEnum
    current_job_count: int = Field(default=0)


class Analyst(BaseEntity):
    """Analyst entity model."""
    name: str
    email: str
    skills: List[str]
    availability: Dict[str, Any]
    max_concurrent_jobs: int
    status: StatusEnum
    current_job_count: int = Field(default=0)


class ScheduleCreate(BaseModel):
    """Schedule creation model."""
    analyst_id: str
    job_id: str
    start_time: datetime
    end_time: datetime
    tenant_id: str


class ScheduleUpdate(BaseModel):
    """Schedule update model."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ScheduleResponse(BaseEntity):
    """Schedule response model."""
    analyst_id: str
    job_id: str
    start_time: datetime
    end_time: datetime
    status: StatusEnum = StatusEnum.ACTIVE


class Schedule(BaseEntity):
    """Schedule entity model."""
    analyst_id: str
    job_id: str
    start_time: datetime
    end_time: datetime
    status: StatusEnum = StatusEnum.ACTIVE


class SchedulingRequest(BaseModel):
    """Scheduling request model."""
    job_id: str
    preferred_analyst_id: Optional[str] = None
    preferred_start_time: Optional[datetime] = None
    priority_override: Optional[PriorityEnum] = None


class SchedulingResponse(BaseModel):
    """Scheduling response model."""
    job_id: str
    analyst_id: str
    start_time: datetime
    end_time: datetime
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    scheduling_reason: str 