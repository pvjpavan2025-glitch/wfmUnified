"""Task definition and instance models."""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, DateTime, JSON, Boolean, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class TaskType(str, enum.Enum):
    """BPMN task types."""
    START_EVENT = "start_event"
    END_EVENT = "end_event"
    INTERMEDIATE_EVENT = "intermediate_event"
    USER_TASK = "user_task"
    MANUAL_TASK = "manual_task"
    SCRIPT_TASK = "script_task"
    SERVICE_TASK = "service_task"
    CALL_ACTIVITY = "call_activity"
    SUBPROCESS = "subprocess"
    EXCLUSIVE_GATEWAY = "exclusive_gateway"
    INCLUSIVE_GATEWAY = "inclusive_gateway"
    PARALLEL_GATEWAY = "parallel_gateway"
    EVENT_BASED_GATEWAY = "event_based_gateway"
    BOUNDARY_EVENT = "boundary_event"
    INTERMEDIATE_THROW_EVENT = "intermediate_throw_event"
    INTERMEDIATE_CATCH_EVENT = "intermediate_catch_event"


class TaskStatus(str, enum.Enum):
    """Task execution status."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class TaskDefinition(Base):
    """BPMN task definition model."""
    
    __tablename__ = "task_definitions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bpmn_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType), nullable=False)
    
    # Reference to workflow definition
    workflow_definition_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_definitions.id"), 
        nullable=False
    )
    
    # BPMN properties
    properties: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    incoming_flows: Mapped[list[str]] = mapped_column(JSON, default=list)
    outgoing_flows: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    # Task-specific configuration
    script: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    script_format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    service_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    service_method: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Gateway configuration
    gateway_expression: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_flow: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Event configuration
    event_definition: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    timer_expression: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    workflow_definition: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition", 
        back_populates="task_definitions"
    )
    task_instances: Mapped[list["TaskInstance"]] = relationship(
        "TaskInstance",
        back_populates="task_definition",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<TaskDefinition(id={self.id}, name='{self.name}', type='{self.task_type}')>"


class TaskInstance(Base):
    """Task execution instance model."""
    
    __tablename__ = "task_instances"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    instance_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    # References
    workflow_instance_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_instances.id"), 
        nullable=False
    )
    task_definition_id: Mapped[int] = mapped_column(
        ForeignKey("task_definitions.id"), 
        nullable=False
    )
    
    # State
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    current_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Execution data
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    output_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Control
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    timeout_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    workflow_instance: Mapped["WorkflowInstance"] = relationship(
        "WorkflowInstance", 
        back_populates="task_instances"
    )
    task_definition: Mapped["TaskDefinition"] = relationship(
        "TaskDefinition", 
        back_populates="task_instances"
    )
    execution_logs: Mapped[list["ExecutionLog"]] = relationship(
        "ExecutionLog",
        back_populates="task_instance",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<TaskInstance(id={self.id}, instance_id='{self.instance_id}', status='{self.status}')>"
