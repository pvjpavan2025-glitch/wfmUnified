"""MongoDB models for Process, ProcessInstance, and Template management."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from bson import ObjectId





class ProcessBase(BaseModel):
    """Base process model."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    is_active: bool = Field(default=True)
    version: str = Field(default="1.0.0", max_length=20)


class ProcessCreate(ProcessBase):
    """Model for creating a new process."""
    
    bpmn_xml: str = Field(..., description="BPMN XML content")
    version: str = Field(default="1.0.0", max_length=20)
    category: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_by: str = Field(..., max_length=100)
    tenant_id: str = Field(..., max_length=100)


class ProcessUpdate(BaseModel):
    """Model for updating a process."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    version: Optional[str] = Field(None, max_length=20)
    bpmn_xml: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Process(ProcessBase):
    """Complete process model."""
    
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    bpmn_xml: str = Field(..., description="BPMN XML content")
    process_id: str = Field(..., description="Unique BPMN process ID")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution info
    execution_count: int = Field(default=0)
    last_executed_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, max_length=100)
    updated_by: Optional[str] = Field(None, max_length=100)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "name": "Order Processing Workflow",
                "description": "Automated order processing workflow",
                "category": "Order Management",
                "tags": ["order", "automation", "workflow"],
                "bpmn_xml": "<bpmn:definitions>...</bpmn:definitions>",
                "process_id": "order_processing_001",
                "variables": {"order_id": "string", "priority": "number"},
                "is_active": True,
                "version": "1.0.0"
            }
        }
    }


class ProcessInstanceBase(BaseModel):
    """Base process instance model."""
    
    process_id: str = Field(..., description="Reference to process definition")
    status: str = Field(default="running", description="Instance status")
    priority: int = Field(default=0, description="Execution priority")
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessInstanceCreate(ProcessInstanceBase):
    """Model for creating a new process instance."""
    
    process_name: str = Field(..., description="Process name for reference")
    variables: Dict[str, Any] = Field(default_factory=dict)


class ProcessInstanceUpdate(BaseModel):
    """Model for updating a process instance."""
    
    status: Optional[str] = None
    priority: Optional[int] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ProcessInstance(ProcessInstanceBase):
    """Complete process instance model."""
    
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    instance_id: str = Field(..., description="Unique instance identifier")
    process_name: str = Field(..., description="Process name for reference")
    variables: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution state
    current_state: Dict[str, Any] = Field(default_factory=dict)
    execution_path: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    resumed_at: Optional[datetime] = None
    
    # Performance metrics
    execution_time: Optional[float] = Field(None, description="Total execution time in seconds")
    step_count: int = Field(default=0, description="Number of steps executed")
    
    # User tracking
    started_by: Optional[str] = Field(None, max_length=100)
    completed_by: Optional[str] = Field(None, max_length=100)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "process_id": "order_processing_001",
                "process_name": "Order Processing Workflow",
                "instance_id": "inst_001",
                "status": "running",
                "input_data": {"order_id": "ORD123", "customer_id": "CUST456"},
                "priority": 1
            }
        }
    }


class TemplateBase(BaseModel):
    """Base template model."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    is_public: bool = Field(default=False, description="Whether template is publicly available")
    is_active: bool = Field(default=True)


class TemplateCreate(TemplateBase):
    """Model for creating a new template."""
    
    bpmn_xml: str = Field(..., description="BPMN XML content")
    process_id: str = Field(..., description="Unique BPMN process ID")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_process_id: Optional[str] = Field(None, description="ID of process this template was created from")


class TemplateUpdate(BaseModel):
    """Model for updating a template."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    bpmn_xml: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Template(TemplateBase):
    """Complete template model."""
    
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    bpmn_xml: str = Field(..., description="BPMN XML content")
    process_id: str = Field(..., description="Unique BPMN process ID")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_process_id: Optional[str] = Field(None, description="ID of process this template was created from")
    
    # Usage statistics
    usage_count: int = Field(default=0, description="Number of times template has been used")
    last_used_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, max_length=100)
    updated_by: Optional[str] = Field(None, max_length=100)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "name": "Standard Order Processing",
                "description": "Standard template for order processing workflows",
                "category": "Order Management",
                "tags": ["order", "template", "standard"],
                "bpmn_xml": "<bpmn:definitions>...</bpmn:definitions>",
                "process_id": "order_processing_template",
                "is_public": True,
                "is_active": True
            }
        }
    }


class ProcessSummary(BaseModel):
    """Summary model for process listing."""
    
    id: str = Field(..., alias="_id")
    name: str
    description: Optional[str]
    category: Optional[str]
    status: str = Field(..., description="Process status (active/inactive)")
    version: str
    execution_count: int
    last_executed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }


class ProcessInstanceSummary(BaseModel):
    """Summary model for process instance listing."""
    
    id: str = Field(..., alias="_id")
    instance_id: str
    process_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    execution_time: Optional[float]
    started_by: Optional[str]
    
    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }


class TemplateSummary(BaseModel):
    """Summary model for template listing."""
    
    id: str = Field(..., alias="_id")
    name: str
    description: Optional[str]
    category: Optional[str]
    is_public: bool
    usage_count: int
    last_used_at: Optional[datetime]
    created_at: datetime
    created_by: Optional[str]
    
    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str}
    }
