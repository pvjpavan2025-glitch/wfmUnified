"""
Data models for Configuration Service.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from shared.models import BaseEntity


class ConfigCreate(BaseModel):
    """Configuration creation model."""
    key: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1)
    type: str = Field(default="string", description="Data type (string, number, boolean, json)")
    description: Optional[str] = None
    tenant_id: str
    environment: str = Field(default="default", description="Environment (dev, staging, prod)")


class ConfigUpdate(BaseModel):
    """Configuration update model."""
    value: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    environment: Optional[str] = None


class ConfigResponse(BaseEntity):
    """Configuration response model."""
    key: str
    value: str
    type: str
    description: Optional[str] = None
    environment: str


class Config(BaseEntity):
    """Configuration entity model."""
    key: str
    value: str
    type: str
    description: Optional[str] = None
    environment: str


class ConfigTemplate(BaseModel):
    """Configuration template model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    tenant_id: str
    configs: Dict[str, Any] = Field(default={})
    environment: str = Field(default="default")


class ConfigVersion(BaseModel):
    """Configuration version model."""
    config_id: str
    version: int
    value: str
    type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    change_reason: Optional[str] = None 