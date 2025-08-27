"""
Data models for Rules Engine Service.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from shared.models import BaseEntity, StatusEnum, PriorityEnum


class RuleCreate(BaseModel):
    """Rule creation model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=50)
    conditions: Dict[str, Any] = Field(..., description="Rule conditions")
    actions: List[Dict[str, Any]] = Field(..., description="Rule actions")
    priority: int = Field(default=1, ge=1, le=10)
    tenant_id: str
    status: StatusEnum = StatusEnum.ACTIVE


class RuleUpdate(BaseModel):
    """Rule update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[StatusEnum] = None


class RuleResponse(BaseEntity):
    """Rule response model."""
    name: str
    description: Optional[str] = None
    category: str
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    priority: int
    status: StatusEnum


class Rule(BaseEntity):
    """Rule entity model."""
    name: str
    description: Optional[str] = None
    category: str
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    priority: int
    status: StatusEnum


class RuleEvaluationRequest(BaseModel):
    """Rule evaluation request model."""
    data: Dict[str, Any] = Field(..., description="Input data for rule evaluation")
    rule_ids: Optional[List[str]] = None  # Specific rules to evaluate
    category: Optional[str] = None  # Evaluate rules by category
    orchestrate: bool = Field(default=False, description="Whether to orchestrate downstream job creation")
    split_jobs: bool = Field(default=False, description="When orchestrating, create a job per item if possible")
    auto_schedule: bool = Field(default=True, description="Schedule jobs immediately after creation")


class RuleEvaluationResponse(BaseModel):
    """Rule evaluation response model."""
    matched_rules: List[Dict[str, Any]] = Field(default=[], description="Rules that matched")
    executed_actions: List[Dict[str, Any]] = Field(default=[], description="Actions that were executed")
    evaluation_time: float = Field(..., description="Evaluation time in seconds")
    total_rules_evaluated: int = Field(..., description="Total number of rules evaluated")
    jobs: List[Dict[str, Any]] = Field(default=[], description="Jobs created during orchestration")
    schedules: List[Dict[str, Any]] = Field(default=[], description="Schedules created during orchestration")


class ProcessCreate(BaseModel):
    """Process creation model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    order_id: str = Field(..., description="ID of the order this process belongs to")
    bpmn_xml: str = Field(..., description="BPMN diagram XML content")
    bpmn_version: str = Field(default="1.0", description="BPMN version")
    process_definition_key: str = Field(..., description="Unique key for process definition in BPMN engine")
    dependencies: List[str] = Field(default=[], description="Process dependencies (other process IDs)")
    estimated_duration_hours: int = Field(default=1, ge=1, description="Estimated duration in hours")
    tenant_id: str
    status: StatusEnum = StatusEnum.ACTIVE


class ProcessUpdate(BaseModel):
    """Process update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    bpmn_xml: Optional[str] = None
    bpmn_version: Optional[str] = None
    dependencies: Optional[List[str]] = None
    estimated_duration_hours: Optional[int] = Field(None, ge=1)
    status: Optional[StatusEnum] = None


class ProcessResponse(BaseEntity):
    """Process response model."""
    name: str
    description: Optional[str] = None
    order_id: str
    bpmn_xml: str
    bpmn_version: str
    process_definition_key: str
    dependencies: List[str]
    estimated_duration_hours: int
    status: StatusEnum
    tasks: List[str] = Field(default_factory=list, description="List of task IDs in this process")
    current_state: Optional[str] = Field(None, description="Current execution state in BPMN engine")
    execution_id: Optional[str] = Field(None, description="BPMN engine execution ID")


class Process(BaseEntity):
    """Process entity model."""
    name: str
    description: Optional[str] = None
    order_id: str
    bpmn_xml: str
    bpmn_version: str
    process_definition_key: str
    dependencies: List[str]
    estimated_duration_hours: int
    status: StatusEnum
    tasks: List[str] = Field(default_factory=list, description="List of task IDs in this process")
    current_state: Optional[str] = Field(None, description="Current execution state in BPMN engine")
    execution_id: Optional[str] = Field(None, description="BPMN engine execution ID")


class TaskCreate(BaseModel):
    """Task creation model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    process_id: str = Field(..., description="ID of the process this task belongs to")
    task_type: str = Field(..., min_length=1, max_length=50, description="Type of task (e.g., installation, configuration)")
    bpmn_task_id: str = Field(..., description="Task ID from BPMN diagram")
    requirements: Dict[str, Any] = Field(default={}, description="Task requirements and parameters")
    required_skills: List[str] = Field(default_factory=list, description="Skills required for this task")
    estimated_duration_minutes: int = Field(default=60, ge=1, description="Estimated duration in minutes")
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies (other task IDs)")
    tenant_id: str
    status: StatusEnum = StatusEnum.PENDING


class TaskUpdate(BaseModel):
    """Task update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    task_type: Optional[str] = Field(None, min_length=1, max_length=50)
    requirements: Optional[Dict[str, Any]] = None
    required_skills: Optional[List[str]] = None
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    priority: Optional[PriorityEnum] = None
    dependencies: Optional[List[str]] = None
    status: Optional[StatusEnum] = None
    assigned_technician_id: Optional[str] = None
    assigned_lead_id: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None


class TaskResponse(BaseEntity):
    """Task response model."""
    name: str
    description: Optional[str] = None
    process_id: str
    task_type: str
    bpmn_task_id: str
    requirements: Dict[str, Any]
    required_skills: List[str]
    estimated_duration_minutes: int
    priority: PriorityEnum
    dependencies: List[str]
    status: StatusEnum
    assigned_technician_id: Optional[str] = None
    assigned_lead_id: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None


class Task(BaseEntity):
    """Task entity model."""
    name: str
    description: Optional[str] = None
    process_id: str
    task_type: str
    bpmn_task_id: str
    requirements: Dict[str, Any]
    required_skills: List[str]
    estimated_duration_minutes: int
    priority: PriorityEnum
    dependencies: List[str]
    status: StatusEnum
    assigned_technician_id: Optional[str] = None
    assigned_lead_id: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None 