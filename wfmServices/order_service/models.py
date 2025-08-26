"""
Order models for Order Service.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from shared.models import BaseEntity, StatusEnum


class OrderCreate(BaseModel):
    external_id: str = Field(..., description="External order identifier")
    source: str = Field(..., description="Source application e.g., OSM, Activation")
    payload: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[str] = None
    status: StatusEnum = StatusEnum.PENDING


class OrderUpdate(BaseModel):
    status: Optional[StatusEnum] = None
    payload: Optional[Dict[str, Any]] = None


class OrderResponse(BaseEntity):
    external_id: str
    source: str
    payload: Dict[str, Any]
    status: StatusEnum


class Order(BaseEntity):
    external_id: str
    source: str
    payload: Dict[str, Any]
    status: StatusEnum
