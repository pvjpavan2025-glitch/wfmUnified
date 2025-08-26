"""Execution logging and state management models."""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, DateTime, JSON, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class LogLevel(str, enum.Enum):
    """Log levels for execution tracking."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ExecutionLog(Base):
    """Workflow execution log model."""
    
    __tablename__ = "execution_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # References
    workflow_instance_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_instances.id"), 
        nullable=False
    )
    task_instance_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("task_instances.id"), 
        nullable=True
    )
    
    # Log details
    level: Mapped[LogLevel] = mapped_column(Enum(LogLevel), nullable=False, default=LogLevel.INFO)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Context
    step_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    execution_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    workflow_instance: Mapped["WorkflowInstance"] = relationship(
        "WorkflowInstance", 
        back_populates="execution_logs"
    )
    task_instance: Mapped[Optional["TaskInstance"]] = relationship(
        "TaskInstance", 
        back_populates="execution_logs"
    )
    
    def __repr__(self) -> str:
        return f"<ExecutionLog(id={self.id}, level='{self.level}', message='{self.message[:50]}...')>"


class ExecutionState(Base):
    """Workflow execution state snapshot model."""
    
    __tablename__ = "execution_states"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # References
    workflow_instance_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_instances.id"), 
        nullable=False
    )
    
    # State snapshot
    state_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    variables: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Execution context
    current_tasks: Mapped[list[str]] = mapped_column(JSON, default=list)
    completed_tasks: Mapped[list[str]] = mapped_column(JSON, default=list)
    pending_tasks: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    # Control flow
    active_tokens: Mapped[list[Dict[str, Any]]] = mapped_column(JSON, default=list)
    flow_control: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    workflow_instance: Mapped["WorkflowInstance"] = relationship(
        "WorkflowInstance", 
        back_populates="execution_states"
    )
    
    def __repr__(self) -> str:
        return f"<ExecutionState(id={self.id}, workflow_instance_id={self.workflow_instance_id})>"
