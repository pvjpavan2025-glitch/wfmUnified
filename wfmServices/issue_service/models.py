"""
Data models for Issue Handler Service.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from shared.models import BaseEntity, StatusEnum, PriorityEnum


class IssueCreate(BaseModel):
    """Issue creation model."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = Field(..., description="Issue category")
    priority: PriorityEnum = PriorityEnum.MEDIUM
    assigned_to: Optional[str] = Field(None, description="Assigned analyst ID")
    related_job_id: Optional[str] = Field(None, description="Related job ID")
    tenant_id: str
    status: StatusEnum = StatusEnum.OPEN


class IssueUpdate(BaseModel):
    """Issue update model."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    assigned_to: Optional[str] = None
    related_job_id: Optional[str] = None
    status: Optional[StatusEnum] = None


class IssueResponse(BaseEntity):
    """Issue response model."""
    title: str
    description: Optional[str] = None
    category: str
    priority: PriorityEnum
    assigned_to: Optional[str] = None
    related_job_id: Optional[str] = None
    status: StatusEnum
    resolution_time: Optional[datetime] = None
    sla_breach: bool = Field(default=False)


class Issue(BaseEntity):
    """Issue entity model."""
    title: str
    description: Optional[str] = None
    category: str
    priority: PriorityEnum
    assigned_to: Optional[str] = None
    related_job_id: Optional[str] = None
    status: StatusEnum
    resolution_time: Optional[datetime] = None
    sla_breach: bool = Field(default=False)


class IssueCommentCreate(BaseModel):
    """Issue comment creation model."""
    content: str = Field(..., min_length=1, max_length=1000)
    issue_id: str
    tenant_id: str


class IssueCommentUpdate(BaseModel):
    """Issue comment update model."""
    content: str = Field(..., min_length=1, max_length=1000)


class IssueCommentResponse(BaseEntity):
    """Issue comment response model."""
    content: str
    issue_id: str
    author_id: str
    author_name: str


class IssueComment(BaseEntity):
    """Issue comment entity model."""
    content: str
    issue_id: str
    author_id: str
    author_name: str


class IssueAttachmentCreate(BaseModel):
    """Issue attachment creation model."""
    filename: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., ge=1, description="File size in bytes")
    issue_id: str
    tenant_id: str


class IssueAttachmentResponse(BaseEntity):
    """Issue attachment response model."""
    filename: str
    file_type: str
    file_size: int
    issue_id: str
    download_url: Optional[str] = None


class IssueAttachment(BaseEntity):
    """Issue attachment entity model."""
    filename: str
    file_type: str
    file_size: int
    issue_id: str
    file_path: Optional[str] = None


class IssueEscalationCreate(BaseModel):
    """Issue escalation creation model."""
    reason: str = Field(..., min_length=1, max_length=500)
    escalated_to: str = Field(..., description="Escalated to analyst ID")
    issue_id: str
    tenant_id: str


class IssueEscalationResponse(BaseEntity):
    """Issue escalation response model."""
    reason: str
    escalated_to: str
    escalated_by: str
    issue_id: str
    status: StatusEnum = StatusEnum.ACTIVE


class IssueEscalation(BaseEntity):
    """Issue escalation entity model."""
    reason: str
    escalated_to: str
    escalated_by: str
    issue_id: str
    status: StatusEnum = StatusEnum.ACTIVE


class IssueSLAConfig(BaseModel):
    """Issue SLA configuration model."""
    category: str
    priority: PriorityEnum
    sla_hours: int = Field(..., ge=1)
    escalation_hours: int = Field(..., ge=1)
    tenant_id: str


class IssueSLAConfigResponse(BaseEntity):
    """Issue SLA configuration response model."""
    category: str
    priority: PriorityEnum
    sla_hours: int
    escalation_hours: int


class IssueSLAConfig(BaseEntity):
    """Issue SLA configuration entity model."""
    category: str
    priority: PriorityEnum
    sla_hours: int
    escalation_hours: int 