"""Workflow definition and instance models."""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, DateTime, JSON, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..core.database import Base


class WorkflowDefinition(Base):
    """BPMN workflow definition model."""
    
    __tablename__ = "workflow_definitions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # BPMN XML content
    bpmn_xml: Mapped[str] = mapped_column(Text, nullable=False)
    bpmn_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    
    # Metadata
    process_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_executable: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Configuration
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
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
    instances: Mapped[list["WorkflowInstance"]] = relationship(
        "WorkflowInstance", 
        back_populates="definition",
        cascade="all, delete-orphan"
    )
    task_definitions: Mapped[list["TaskDefinition"]] = relationship(
        "TaskDefinition",
        back_populates="workflow_definition",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<WorkflowDefinition(id={self.id}, name='{self.name}', version='{self.version}')>"


class WorkflowInstance(Base):
    """Workflow execution instance model."""
    
    __tablename__ = "workflow_instances"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    instance_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    # Reference to definition
    workflow_definition_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_definitions.id"), 
        nullable=False
    )
    
    # State
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running")
    current_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Execution data
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    output_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Control
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    definition: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition", 
        back_populates="instances"
    )
    task_instances: Mapped[list["TaskInstance"]] = relationship(
        "TaskInstance",
        back_populates="workflow_instance",
        cascade="all, delete-orphan"
    )
    execution_logs: Mapped[list["ExecutionLog"]] = relationship(
        "ExecutionLog",
        back_populates="workflow_instance",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<WorkflowInstance(id={self.id}, instance_id='{self.instance_id}', status='{self.status}')>"
