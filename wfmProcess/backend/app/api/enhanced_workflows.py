"""Enhanced Workflows API router with MongoDB integration for process management."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, File, UploadFile, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..core.database import get_db
from ..models.workflow import WorkflowDefinition, WorkflowInstance
from ..models.process_models import ProcessCreate, ProcessInstanceCreate
from ..core.config import settings
from ..engine.enhanced_bpmn_processor import EnhancedBpmnProcessor

router = APIRouter()
enhanced_bpmn_processor = EnhancedBpmnProcessor()


class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    bpmn_xml: str
    variables: Optional[Dict[str, Any]] = None


class WorkflowExecuteRequest(BaseModel):
    variables: Optional[Dict[str, Any]] = None


class ProcessCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    bpmn_xml: str
    version: str = "1.0.0"
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_by: str = "system"
    tenant_id: str = "default"


class ProcessInstanceCreateRequest(BaseModel):
    process_id: str
    input_data: Optional[Dict[str, Any]] = None
    started_by: Optional[str] = None
    tenant_id: Optional[str] = None


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
        validation_result = await enhanced_bpmn_processor.validate_bpmn(workflow_data.bpmn_xml)
        
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
        process_info = await enhanced_bpmn_processor._extract_process_info(workflow_data.bpmn_xml)
        
        # Create workflow instance
        instance_id = await enhanced_bpmn_processor.create_workflow_instance(
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
        validation_result = await enhanced_bpmn_processor.validate_bpmn(bpmn_content)
        
        # Parse process information
        process_info = None
        if validation_result["valid"]:
            process_info = await enhanced_bpmn_processor._extract_process_info(bpmn_content)
        
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
        instance_id = await enhanced_bpmn_processor.create_workflow_instance(
            bpmn_xml,
            request.variables or {}
        )
        
        # Execute workflow
        execution_result = await enhanced_bpmn_processor.execute_workflow(instance_id)
        
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
        status = await enhanced_bpmn_processor.get_workflow_status(instance_id)
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
        execution_result = await enhanced_bpmn_processor.execute_workflow(instance_id)
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
        validation_result = await enhanced_bpmn_processor.validate_bpmn(bpmn_xml)
        
        # If valid, also parse for detailed information
        if validation_result["valid"]:
            process_info = await enhanced_bpmn_processor._extract_process_info(bpmn_xml)
            validation_result["detailed_analysis"] = process_info
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# New MongoDB-based process management endpoints

@router.post("/processes")
async def create_process(
    process_data: ProcessCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new process from BPMN XML and save to MongoDB."""
    try:
        # Create ProcessCreate object
        process_create = ProcessCreate(
            name=process_data.name,
            description=process_data.description,
            bpmn_xml=process_data.bpmn_xml,
            version=process_data.version,
            category=process_data.category,
            tags=process_data.tags,
            metadata=process_data.metadata,
            created_by=process_data.created_by,
            tenant_id=process_data.tenant_id
        )
        
        # Parse, validate, and save process
        saved_process = await enhanced_bpmn_processor.parse_and_save_process(
            process_data.bpmn_xml,
            process_create
        )
        
        return {
            "message": "Process created successfully",
            "process": saved_process
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/processes")
async def list_processes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List all processes with optional filtering."""
    try:
        processes = await enhanced_bpmn_processor.process_service.list_processes(
            skip=skip,
            limit=limit,
            category=category,
            status=status,
            tenant_id=tenant_id
        )
        
        return {
            "processes": processes,
            "total": len(processes),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/processes/{process_id}")
async def get_process(
    process_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get process by ID."""
    try:
        process = await enhanced_bpmn_processor.process_service.get_process(process_id)
        if not process:
            raise HTTPException(status_code=404, detail="Process not found")
        
        return process
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/processes/{process_id}")
async def update_process(
    process_id: str,
    process_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update process."""
    try:
        updated_process = await enhanced_bpmn_processor.process_service.update_process(
            process_id,
            process_data
        )
        
        return {
            "message": "Process updated successfully",
            "process": updated_process
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/processes/{process_id}")
async def delete_process(
    process_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete process."""
    try:
        success = await enhanced_bpmn_processor.process_service.delete_process(process_id)
        
        if success:
            return {"message": "Process deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Process not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/processes/{process_id}/instances")
async def create_process_instance(
    process_id: str,
    instance_data: ProcessInstanceCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new process instance."""
    try:
        # Create ProcessInstanceCreate object
        instance_create = ProcessInstanceCreate(
            process_id=process_id,
            process_name="",  # Will be filled by the service
            process_version="",  # Will be filled by the service
            input_data=instance_data.input_data or {},
            status="running",
            started_by=instance_data.started_by or "system",
            tenant_id=instance_data.tenant_id or "default"
        )
        
        # Create process instance
        process_instance = await enhanced_bpmn_processor.create_process_instance(
            process_id,
            instance_data.input_data
        )
        
        return {
            "message": "Process instance created successfully",
            "instance": process_instance
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/processes/{process_id}/instances")
async def list_process_instances(
    process_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List process instances for a specific process."""
    try:
        instances = await enhanced_bpmn_processor.list_process_instances(
            process_id=process_id,
            status=status,
            tenant_id=tenant_id
        )
        
        return {
            "instances": instances,
            "total": len(instances),
            "skip": skip,
            "limit": limit,
            "process_id": process_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances/{instance_id}")
async def get_process_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get process instance status and details."""
    try:
        status = await enhanced_bpmn_processor.get_process_instance_status(instance_id)
        return status
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/instances/{instance_id}/execute")
async def execute_process_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Execute an existing process instance."""
    try:
        execution_result = await enhanced_bpmn_processor.execute_process_instance(instance_id)
        return execution_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/instances/{instance_id}")
async def delete_process_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a process instance."""
    try:
        success = await enhanced_bpmn_processor.delete_process_instance(instance_id)
        
        if success:
            return {"message": "Process instance deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Process instance not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/processes/{process_id}/templates")
async def create_template_from_process(
    process_id: str,
    template_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a template from an existing process."""
    try:
        # Get the process
        process = await enhanced_bpmn_processor.process_service.get_process(process_id)
        if not process:
            raise HTTPException(status_code=404, detail="Process not found")
        
        # Create template
        template = await enhanced_bpmn_processor.process_service.template_service.create_template_from_process(
            process,
            template_data
        )
        
        return {
            "message": "Template created successfully",
            "template": template
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List all templates."""
    try:
        templates = await enhanced_bpmn_processor.process_service.template_service.list_templates(
            skip=skip,
            limit=limit,
            category=category,
            tenant_id=tenant_id
        )
        
        return {
            "templates": templates,
            "total": len(templates),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
