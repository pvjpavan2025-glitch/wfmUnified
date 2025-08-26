"""
Data models for Authentication & Authorization Service.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from shared.models import BaseEntity, UserStatus, RoleStatus, TenantStatus


# User Models
class UserCreate(BaseModel):
    """User creation model."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    tenant_id: str
    role_ids: List[str] = Field(default=[])
    status: UserStatus = UserStatus.ACTIVE


class UserUpdate(BaseModel):
    """User update model."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role_ids: Optional[List[str]] = None
    status: Optional[UserStatus] = None


class UserResponse(BaseEntity):
    """User response model."""
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    status: UserStatus
    role_ids: List[str] = Field(default=[])
    roles: List[dict] = Field(default=[])
    permissions: List[str] = Field(default=[])


class User(BaseEntity):
    """User entity model."""
    username: str
    email: EmailStr
    password_hash: str
    first_name: str
    last_name: str
    status: UserStatus
    role_ids: List[str] = Field(default=[])
    last_login: Optional[datetime] = None
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = None


# Role Models
class RoleCreate(BaseModel):
    """Role creation model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    tenant_id: str
    permission_ids: List[str] = Field(default=[])
    status: RoleStatus = RoleStatus.ACTIVE


class RoleUpdate(BaseModel):
    """Role update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    permission_ids: Optional[List[str]] = None
    status: Optional[RoleStatus] = None


class RoleResponse(BaseEntity):
    """Role response model."""
    name: str
    description: Optional[str] = None
    status: RoleStatus
    permission_ids: List[str] = Field(default=[])
    permissions: List[dict] = Field(default=[])


class Role(BaseEntity):
    """Role entity model."""
    name: str
    description: Optional[str] = None
    status: RoleStatus
    permission_ids: List[str] = Field(default=[])


# Permission Models
class PermissionCreate(BaseModel):
    """Permission creation model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    resource: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=50)
    tenant_id: str


class PermissionUpdate(BaseModel):
    """Permission update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    resource: Optional[str] = Field(None, min_length=1, max_length=100)
    action: Optional[str] = Field(None, min_length=1, max_length=50)


class PermissionResponse(BaseEntity):
    """Permission response model."""
    name: str
    description: Optional[str] = None
    resource: str
    action: str


class Permission(BaseEntity):
    """Permission entity model."""
    name: str
    description: Optional[str] = None
    resource: str
    action: str


# Tenant Models
class TenantCreate(BaseModel):
    """Tenant creation model."""
    name: str = Field(..., min_length=1, max_length=100)
    domain: Optional[str] = None
    status: TenantStatus = TenantStatus.ACTIVE
    settings: Optional[dict] = Field(default={})


class TenantUpdate(BaseModel):
    """Tenant update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    domain: Optional[str] = None
    status: Optional[TenantStatus] = None
    settings: Optional[dict] = None


class TenantResponse(BaseEntity):
    """Tenant response model."""
    name: str
    domain: Optional[str] = None
    status: TenantStatus
    settings: dict = Field(default={})


class Tenant(BaseEntity):
    """Tenant entity model."""
    name: str
    domain: Optional[str] = None
    status: TenantStatus
    settings: dict = Field(default={})


# Authentication Models
class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str
    tenant_id: str


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    expires_in: int
    user: UserResponse


class TokenRefreshRequest(BaseModel):
    """Token refresh request model."""
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    """Token refresh response model."""
    access_token: str
    expires_in: int


class PasswordChangeRequest(BaseModel):
    """Password change request model."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr
    tenant_id: str


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation model."""
    token: str
    new_password: str = Field(..., min_length=8) 