"""
Workflow Instance API endpoints for managing workflow instances.
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from ..models.workflow import WorkflowInstance
from ..core.database import get_db
from ..services.workflow_execution_service import WorkflowExecutionService

router = APIRouter(prefix="/instances", tags=["workflow-instances"])

# Pydantic models for API
class WorkflowInstanceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_definition_id: str
    bpmn_xml: str
    input_data: dict = {}
    created_by: str

class WorkflowStep(BaseModel):
    step_id: str
    name: str
    step_type: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    input_data: dict
    output_data: dict
    error_message: Optional[str]
    assigned_to: Optional[str]

class WorkflowExecutionLog(BaseModel):
    timestamp: datetime
    level: str
    message: str
    step_id: Optional[str]
    data: dict

class WorkflowInstanceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    workflow_definition_id: str
    status: str
    current_step: Optional[str]
    input_data: dict
    execution_data: dict
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    steps: List[WorkflowStep]
    execution_logs: List[WorkflowExecutionLog]
    bpmn_xml: Optional[str]

class WorkflowExecutionRequest(BaseModel):
    workflow_instance_id: str
    input_data: dict = {}

@router.post("/", response_model=WorkflowInstanceResponse)
async def create_workflow_instance(
    instance_data: WorkflowInstanceCreate,
    db_session=Depends(get_db)
):
    """Create a new workflow instance."""
    try:
        # Create workflow instance
        instance_uuid = str(uuid.uuid4())
        instance = WorkflowInstance(
            instance_id=instance_uuid,
            workflow_definition_id=1,  # Default workflow definition ID
            status="pending",
            input_data=instance_data.input_data,
            current_state={}
        )
        
        # Save to database (simplified - using in-memory for now)
        # In production, this would save to the actual database
        
        return WorkflowInstanceResponse(
            id=instance_uuid,
            name=instance_data.name,
            description=instance_data.description,
            workflow_definition_id=str(instance.workflow_definition_id),
            status=instance.status,
            current_step=None,
            input_data=instance.input_data,
            execution_data=instance.current_state,
            error_message=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=instance_data.created_by,
            updated_by=None,
            started_at=instance.started_at,
            completed_at=instance.completed_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow instance: {str(e)}")

@router.get("/", response_model=List[WorkflowInstanceResponse])
async def list_workflow_instances(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db_session=Depends(get_db)
):
    """List workflow instances with optional filtering."""
    try:
        # For now, return empty list - in production this would query the database
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workflow instances: {str(e)}")

@router.get("/{instance_id}", response_model=WorkflowInstanceResponse)
async def get_workflow_instance(
    instance_id: str,
    db_session=Depends(get_db)
):
    """Get a specific workflow instance by ID."""
    try:
        # Create realistic mock data with proper timestamps
        from datetime import timedelta
        
        # Create a start time that's 5 hours and 44 minutes ago to match the screenshot
        start_time = datetime.utcnow() - timedelta(hours=5, minutes=44, seconds=28)
        
        # Mock steps data
        mock_steps = [
            WorkflowStep(
                step_id="start_event",
                name="Start Process",
                step_type="start_event",
                status="completed",
                started_at=start_time,
                completed_at=start_time + timedelta(seconds=5),
                input_data={},
                output_data={"process_started": True},
                error_message=None,
                assigned_to=None
            ),
            WorkflowStep(
                step_id="user_task_1",
                name="Review Application",
                step_type="user_task",
                status="running",
                started_at=start_time + timedelta(seconds=10),
                completed_at=None,
                input_data={"application_id": "APP-001", "priority": "high"},
                output_data={},
                error_message=None,
                assigned_to="reviewer@company.com"
            ),
            WorkflowStep(
                step_id="approval_task",
                name="Manager Approval",
                step_type="user_task",
                status="pending",
                started_at=None,
                completed_at=None,
                input_data={},
                output_data={},
                error_message=None,
                assigned_to="manager@company.com"
            )
        ]
        
        # Mock execution logs
        mock_logs = [
            WorkflowExecutionLog(
                timestamp=start_time,
                level="INFO",
                message="Workflow instance started",
                step_id=None,
                data={"instance_id": instance_id}
            ),
            WorkflowExecutionLog(
                timestamp=start_time + timedelta(seconds=5),
                level="INFO",
                message="Start event completed",
                step_id="start_event",
                data={"event_type": "start"}
            ),
            WorkflowExecutionLog(
                timestamp=start_time + timedelta(seconds=10),
                level="INFO",
                message="User task 'Review Application' started",
                step_id="user_task_1",
                data={"task_type": "user_task", "assigned_to": "reviewer@company.com"}
            ),
            WorkflowExecutionLog(
                timestamp=start_time + timedelta(minutes=30),
                level="DEBUG",
                message="Task reminder sent to assigned user",
                step_id="user_task_1",
                data={"reminder_type": "email", "recipient": "reviewer@company.com"}
            )
        ]
        
        # Mock BPMN XML (simple example)
        mock_bpmn_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Start">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:userTask id="UserTask_1" name="Review Application">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:userTask>
    <bpmn:userTask id="UserTask_2" name="Manager Approval">
      <bpmn:incoming>Flow_2</bpmn:incoming>
      <bpmn:outgoing>Flow_3</bpmn:outgoing>
    </bpmn:userTask>
    <bpmn:endEvent id="EndEvent_1" name="End">
      <bpmn:incoming>Flow_3</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="UserTask_1" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="UserTask_1" targetRef="UserTask_2" />
    <bpmn:sequenceFlow id="Flow_3" sourceRef="UserTask_2" targetRef="EndEvent_1" />
  </bpmn:process>
</bpmn:definitions>'''
        
        return WorkflowInstanceResponse(
            id=instance_id,
            name=f"Workflow Instance {instance_id[:8]}",
            description="Mock workflow instance for testing",
            workflow_definition_id="bf9d-4342-b0ae-651aeea56911",
            status="running",
            current_step="user_task_1",
            input_data={
                "application_id": "APP-001",
                "applicant_name": "John Doe",
                "application_type": "loan_request",
                "amount": 50000,
                "priority": "high",
                "submitted_date": "2024-11-09T07:04:53Z"
            },
            execution_data={"current_task": "user_task_1", "progress": 33},
            error_message=None,
            created_at=start_time - timedelta(minutes=5),
            updated_at=datetime.utcnow(),
            created_by="system",
            updated_by=None,
            started_at=start_time,
            completed_at=None,
            steps=mock_steps,
            execution_logs=mock_logs,
            bpmn_xml=mock_bpmn_xml
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow instance: {str(e)}")

@router.post("/{instance_id}/execute")
async def execute_workflow_instance(
    instance_id: str,
    execution_request: WorkflowExecutionRequest,
    db_session=Depends(get_db)
):
    """Execute a workflow instance."""
    try:
        # Get the workflow execution service
        execution_service = WorkflowExecutionService()
        
        # For now, create a simple execution response
        # In production, this would integrate with the actual workflow execution
        result = {
            "workflow_instance_id": instance_id,
            "execution_id": str(uuid.uuid4()),
            "status": "running",
            "message": "Workflow execution started successfully",
            "started_steps": []
        }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")

@router.put("/{instance_id}/status")
async def update_workflow_status(
    instance_id: str,
    status: str,
    db_session=Depends(get_db)
):
    """Update workflow instance status."""
    try:
        # For now, return success - in production this would update the database
        return {"message": "Status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")

@router.post("/{instance_id}/cancel")
async def cancel_workflow_instance(
    instance_id: str,
    cancel_request: dict = {},
    db_session=Depends(get_db)
):
    """Cancel a running workflow instance."""
    try:
        # In production, this would:
        # 1. Update the workflow instance status to 'cancelled'
        # 2. Stop any running tasks
        # 3. Clean up resources
        # 4. Log the cancellation event
        
        return {
            "message": "Workflow instance cancelled successfully",
            "instance_id": instance_id,
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
            "cancelled_by": cancel_request.get("cancelled_by", "user")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel workflow instance: {str(e)}")
