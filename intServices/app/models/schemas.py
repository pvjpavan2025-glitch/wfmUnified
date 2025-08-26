from typing import Optional
from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    name: str
    code: str
    base_url: Optional[str] = None
    auth_type: Optional[str] = "none"
    is_active: bool = True


class ApplicationUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    auth_type: Optional[str] = None
    is_active: Optional[bool] = None


class EndpointCreate(BaseModel):
    name: str
    path: str
    method: str = "POST"
    mapping_name: Optional[str] = None
    description: Optional[str] = None


class EndpointUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    mapping_name: Optional[str] = None
    description: Optional[str] = None
