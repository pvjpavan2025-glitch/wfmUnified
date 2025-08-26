"""
Data models for Rules Engine Service.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from shared.models import BaseEntity, StatusEnum


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
    steps: List[Dict[str, Any]] = Field(..., description="Process steps")
    dependencies: List[str] = Field(default=[], description="Process dependencies")
    tenant_id: str
    status: StatusEnum = StatusEnum.ACTIVE


class ProcessUpdate(BaseModel):
    """Process update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    dependencies: Optional[List[str]] = None
    status: Optional[StatusEnum] = None


class ProcessResponse(BaseEntity):
    """Process response model."""
    name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]]
    dependencies: List[str]
    status: StatusEnum


class Process(BaseEntity):
    """Process entity model."""
    name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]]
    dependencies: List[str]
    status: StatusEnum


class TaskCreate(BaseModel):
    """Task creation model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    type: str = Field(..., min_length=1, max_length=50)
    requirements: Dict[str, Any] = Field(default={}, description="Task requirements")
    estimated_duration: int = Field(default=0, ge=0, description="Estimated duration in minutes")
    tenant_id: str
    status: StatusEnum = StatusEnum.ACTIVE


class TaskUpdate(BaseModel):
    """Task update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    requirements: Optional[Dict[str, Any]] = None
    estimated_duration: Optional[int] = Field(None, ge=0)
    status: Optional[StatusEnum] = None


class TaskResponse(BaseEntity):
    """Task response model."""
    name: str
    description: Optional[str] = None
    type: str
    requirements: Dict[str, Any]
    estimated_duration: int
    status: StatusEnum


class Task(BaseEntity):
    """Task entity model."""
    name: str
    description: Optional[str] = None
    type: str
    requirements: Dict[str, Any]
    estimated_duration: int
    status: StatusEnum 