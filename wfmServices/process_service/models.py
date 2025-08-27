"""
Data models for Process Service.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from shared.models import BaseEntity, StatusEnum, PriorityEnum


class ProcessInstanceCreate(BaseModel):
    """Process instance creation model."""
    process_id: str = Field(..., description="ID of the process definition")
    order_id: str = Field(..., description="ID of the order this instance belongs to")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for process execution")
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    tenant_id: str
    status: StatusEnum = StatusEnum.PENDING


class ProcessInstanceUpdate(BaseModel):
    """Process instance update model."""
    status: Optional[StatusEnum] = None
    current_state: Optional[str] = None
    execution_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class ProcessInstanceResponse(BaseEntity):
    """Process instance response model."""
    process_id: str
    order_id: str
    input_data: Dict[str, Any]
    priority: PriorityEnum
    status: StatusEnum
    current_state: Optional[str] = None
    execution_id: Optional[str] = None
    execution_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tasks: List[str] = Field(default_factory=list, description="List of task IDs in this process instance")


class ProcessInstance(BaseEntity):
    """Process instance entity model."""
    process_id: str
    order_id: str
    input_data: Dict[str, Any]
    priority: PriorityEnum
    status: StatusEnum
    current_state: Optional[str] = None
    execution_id: Optional[str] = None
    execution_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tasks: List[str] = Field(default_factory=list, description="List of task IDs in this process instance")


class TaskInstanceCreate(BaseModel):
    """Task instance creation model."""
    task_definition_id: str = Field(..., description="ID of the task definition from BPMN")
    process_instance_id: str = Field(..., description="ID of the process instance")
    bpmn_task_id: str = Field(..., description="Task ID from BPMN diagram")
    name: str = Field(..., min_length=1, max_length=100)
    task_type: str = Field(..., description="Type of task (e.g., user_task, service_task)")
    input_data: Dict[str, Any] = Field(default_factory=dict)
    required_skills: List[str] = Field(default_factory=list)
    estimated_duration_minutes: int = Field(default=60, ge=1)
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    tenant_id: str
    status: StatusEnum = StatusEnum.PENDING


class TaskInstanceUpdate(BaseModel):
    """Task instance update model."""
    status: Optional[StatusEnum] = None
    assigned_technician_id: Optional[str] = None
    assigned_lead_id: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    output_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    error_message: Optional[str] = None


class TaskInstanceResponse(BaseEntity):
    """Task instance response model."""
    task_definition_id: str
    process_instance_id: str
    bpmn_task_id: str
    name: str
    task_type: str
    input_data: Dict[str, Any]
    required_skills: List[str]
    estimated_duration_minutes: int
    priority: PriorityEnum
    status: StatusEnum
    assigned_technician_id: Optional[str] = None
    assigned_lead_id: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    output_data: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    error_message: Optional[str] = None


class TaskInstance(BaseEntity):
    """Task instance entity model."""
    task_definition_id: str
    process_instance_id: str
    bpmn_task_id: str
    name: str
    task_type: str
    input_data: Dict[str, Any]
    required_skills: List[str]
    estimated_duration_minutes: int
    priority: PriorityEnum
    status: StatusEnum
    assigned_technician_id: Optional[str] = None
    assigned_lead_id: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    output_data: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    error_message: Optional[str] = None


class ProcessExecutionRequest(BaseModel):
    """Process execution request model."""
    process_id: str
    order_id: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    auto_assign_tasks: bool = Field(default=True, description="Automatically assign tasks to available technicians")


class ProcessExecutionResponse(BaseModel):
    """Process execution response model."""
    process_instance_id: str
    execution_id: str
    status: StatusEnum
    created_tasks: List[str] = Field(default_factory=list, description="List of task instance IDs created")
    message: str
