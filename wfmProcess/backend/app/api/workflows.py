"""Enhanced Workflows API router with advanced BPMN features."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..core.database import get_db
from ..models.workflow import WorkflowDefinition, WorkflowInstance
from ..core.config import settings
from ..engine.bpmn_processor import BpmnProcessor

router = APIRouter()
bpmn_processor = BpmnProcessor()


class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    bpmn_xml: str
    variables: Optional[Dict[str, Any]] = None


class WorkflowExecuteRequest(BaseModel):
    variables: Optional[Dict[str, Any]] = None


@router.get("/")
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List all workflow definitions."""
    # This is a placeholder implementation
    # In a real system, you'd query the database
    return {
        "workflows": [],
        "total": 0,
        "skip": skip,
        "limit": limit
    }


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get workflow definition by ID."""
    # This is a placeholder implementation
    # In a real system, you'd query the database
    raise HTTPException(status_code=404, detail="Workflow not found")


@router.post("/")
async def create_workflow(
    workflow_data: WorkflowCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new workflow definition with BPMN validation."""
    try:
        # Validate BPMN XML
        validation_result = await bpmn_processor.validate_bpmn(workflow_data.bpmn_xml)
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Invalid BPMN XML",
                    "errors": validation_result["errors"],
                    "warnings": validation_result["warnings"]
                }
            )
        
        # Parse BPMN to extract process information
        process_info = await bpmn_processor.parse_bpmn(workflow_data.bpmn_xml)
        
        # Create workflow instance
        instance_id = await bpmn_processor.create_workflow_instance(
            workflow_data.bpmn_xml,
            workflow_data.variables or {}
        )
        
        return {
            "message": "Workflow created successfully",
            "instance_id": instance_id,
            "process_info": process_info,
            "validation": validation_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    workflow_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update workflow definition."""
    # This is a placeholder implementation
    # In a real system, you'd update the workflow in the database
    return {
        "message": "Workflow updated successfully",
        "workflow_id": workflow_id
    }


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete workflow definition."""
    # This is a placeholder implementation
    # In a real system, you'd delete the workflow from the database
    return {
        "message": "Workflow deleted successfully",
        "workflow_id": workflow_id
    }


@router.get("/{workflow_id}/instances")
async def list_workflow_instances(
    workflow_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List workflow instances for a specific workflow."""
    # This is a placeholder implementation
    # In a real system, you'd query the database
    return {
        "instances": [],
        "total": 0,
        "skip": skip,
        "limit": limit,
        "workflow_id": workflow_id
    }


@router.post("/upload")
async def upload_bpmn_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload and validate BPMN file."""
    try:
        if not file.filename.endswith('.bpmn'):
            raise HTTPException(status_code=400, detail="File must be a .bpmn file")
        
        # Read file content
        bpmn_xml = await file.read()
        bpmn_content = bpmn_xml.decode('utf-8')
        
        # Validate BPMN
        validation_result = await bpmn_processor.validate_bpmn(bpmn_content)
        
        # Parse process information
        process_info = None
        if validation_result["valid"]:
            process_info = await bpmn_processor.parse_bpmn(bpmn_content)
        
        return {
            "filename": file.filename,
            "validation": validation_result,
            "process_info": process_info,
            "bpmn_xml": bpmn_content
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_workflow(
    request: WorkflowExecuteRequest,
    bpmn_xml: str,
    db: AsyncSession = Depends(get_db)
):
    """Execute a workflow from BPMN XML."""
    try:
        # Create workflow instance
        instance_id = await bpmn_processor.create_workflow_instance(
            bpmn_xml,
            request.variables or {}
        )
        
        # Execute workflow
        execution_result = await bpmn_processor.execute_workflow(instance_id)
        
        return execution_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances/{instance_id}")
async def get_workflow_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get workflow instance status and details."""
    try:
        status = await bpmn_processor.get_workflow_status(instance_id)
        return status
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/instances/{instance_id}/execute")
async def execute_workflow_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Execute an existing workflow instance."""
    try:
        execution_result = await bpmn_processor.execute_workflow(instance_id)
        return execution_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_bpmn(
    bpmn_xml: str,
    db: AsyncSession = Depends(get_db)
):
    """Validate BPMN XML and return detailed analysis."""
    try:
        validation_result = await bpmn_processor.validate_bpmn(bpmn_xml)
        
        # If valid, also parse for detailed information
        if validation_result["valid"]:
            process_info = await bpmn_processor.parse_bpmn(bpmn_xml)
            validation_result["detailed_analysis"] = process_info
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
