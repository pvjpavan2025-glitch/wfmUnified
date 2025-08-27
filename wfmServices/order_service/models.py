"""
Order models for Order Service.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from shared.models import BaseEntity, StatusEnum, PriorityEnum


class OrderCreate(BaseModel):
    external_id: str = Field(..., description="External order identifier")
    source: str = Field(..., description="Source application e.g., OSM, Activation")
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    description: Optional[str] = None
    customer_id: Optional[str] = None
    requested_completion_date: Optional[datetime] = None
    tenant_id: Optional[str] = None
    status: StatusEnum = StatusEnum.PENDING


class OrderUpdate(BaseModel):
    status: Optional[StatusEnum] = None
    payload: Optional[Dict[str, Any]] = None
    priority: Optional[PriorityEnum] = None
    description: Optional[str] = None
    requested_completion_date: Optional[datetime] = None


class OrderResponse(BaseEntity):
    external_id: str
    source: str
    payload: Dict[str, Any]
    priority: PriorityEnum
    description: Optional[str] = None
    customer_id: Optional[str] = None
    requested_completion_date: Optional[datetime] = None
    status: StatusEnum
    processes: List[str] = Field(default_factory=list, description="List of process IDs associated with this order")
    total_tasks: int = Field(default=0, description="Total number of tasks across all processes")
    completed_tasks: int = Field(default=0, description="Number of completed tasks")


class Order(BaseEntity):
    external_id: str
    source: str
    payload: Dict[str, Any]
    priority: PriorityEnum
    description: Optional[str] = None
    customer_id: Optional[str] = None
    requested_completion_date: Optional[datetime] = None
    status: StatusEnum
    processes: List[str] = Field(default_factory=list, description="List of process IDs associated with this order")
    total_tasks: int = Field(default=0, description="Total number of tasks across all processes")
    completed_tasks: int = Field(default=0, description="Number of completed tasks")
