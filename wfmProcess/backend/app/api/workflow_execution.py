"""
Workflow Execution API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, Optional
from pydantic import BaseModel

from ..services.workflow_execution_service import WorkflowExecutionService


router = APIRouter(prefix="/workflow-execution", tags=["workflow-execution"])


class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution."""
    bpmn_xml: str
    workflow_name: str
    workflow_description: Optional[str] = None
    input_data: Dict[str, Any] = {}
    created_by: str


class WorkflowContinueRequest(BaseModel):
    """Request model for continuing workflow execution."""
    task_data: Optional[Dict[str, Any]] = None


def get_workflow_execution_service() -> WorkflowExecutionService:
    """Dependency to get workflow execution service."""
    return WorkflowExecutionService()


@router.post("/execute")
async def execute_workflow(
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks,
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    """Execute a BPMN workflow."""
    try:
        result = await service.create_and_execute_workflow(
            bpmn_xml=request.bpmn_xml,
            workflow_name=request.workflow_name,
            workflow_description=request.workflow_description or "",
            input_data=request.input_data,
            created_by=request.created_by
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instances/{workflow_instance_id}/continue")
async def continue_workflow(
    workflow_instance_id: str,
    request: WorkflowContinueRequest,
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    """Continue workflow execution after user task completion."""
    try:
        result = await service.continue_workflow_execution(
            workflow_instance_id=workflow_instance_id,
            task_data=request.task_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instances/{workflow_instance_id}/cancel")
async def cancel_workflow(
    workflow_instance_id: str,
    cancelled_by: str,
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    """Cancel workflow execution."""
    try:
        success = await service.cancel_workflow(workflow_instance_id, cancelled_by)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel workflow")
        return {"message": "Workflow cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances/{workflow_instance_id}/status")
async def get_workflow_status(
    workflow_instance_id: str,
    service: WorkflowExecutionService = Depends(get_workflow_execution_service)
):
    """Get workflow execution status and ready tasks."""
    try:
        status = await service.get_workflow_status(workflow_instance_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
