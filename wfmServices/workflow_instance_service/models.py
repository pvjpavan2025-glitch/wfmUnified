"""
Workflow Instance Service Models.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class WorkflowInstanceStatus(str, Enum):
    """Workflow instance status enumeration."""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    RESUMED = "resumed"
    TIMEOUT = "timeout"
    ABORTED = "aborted"
    PAUSED = "paused"


class WorkflowStepStatus(str, Enum):
    """Workflow step status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowInstanceCreate(BaseModel):
    """Workflow instance creation model."""
    name: str = Field(..., min_length=1, max_length=255, description="Workflow instance name")
    description: Optional[str] = Field(None, max_length=1000, description="Workflow instance description")
    workflow_definition_id: str = Field(..., description="ID of the workflow definition")
    bpmn_xml: str = Field(..., description="BPMN XML content")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for workflow execution")
    created_by: str = Field(..., description="User who created the instance")


class WorkflowInstanceUpdate(BaseModel):
    """Workflow instance update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[WorkflowInstanceStatus] = None
    current_step: Optional[str] = None
    execution_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class WorkflowStep(BaseModel):
    """Workflow step model."""
    step_id: str = Field(..., description="Unique step identifier")
    name: str = Field(..., description="Step name")
    step_type: str = Field(..., description="Type of step (e.g., user_task, service_task)")
    status: WorkflowStepStatus = Field(default=WorkflowStepStatus.PENDING)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    assigned_to: Optional[str] = None


class WorkflowExecutionLog(BaseModel):
    """Workflow execution log model."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(..., description="Log level (INFO, WARNING, ERROR)")
    message: str = Field(..., description="Log message")
    step_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class WorkflowInstanceResponse(BaseModel):
    """Workflow instance response model."""
    id: str = Field(..., description="Workflow instance ID")
    name: str = Field(..., description="Workflow instance name")
    description: Optional[str] = None
    workflow_definition_id: str
    status: WorkflowInstanceStatus
    current_step: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    execution_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    steps: List[WorkflowStep] = Field(default_factory=list)
    execution_logs: List[WorkflowExecutionLog] = Field(default_factory=list)


class WorkflowInstance(BaseModel):
    """Workflow instance entity model."""
    id: str
    name: str
    description: Optional[str] = None
    workflow_definition_id: str
    bpmn_xml: str
    status: WorkflowInstanceStatus
    current_step: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    execution_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    steps: List[WorkflowStep] = Field(default_factory=list)
    execution_logs: List[WorkflowExecutionLog] = Field(default_factory=list)


class WorkflowExecutionRequest(BaseModel):
    """Workflow execution request model."""
    workflow_instance_id: str = Field(..., description="ID of the workflow instance to execute")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Additional input data")
    auto_start: bool = Field(default=True, description="Automatically start execution")


class WorkflowExecutionResponse(BaseModel):
    """Workflow execution response model."""
    workflow_instance_id: str
    execution_id: str
    status: WorkflowInstanceStatus
    message: str
    started_steps: List[str] = Field(default_factory=list, description="List of step IDs that were started")
