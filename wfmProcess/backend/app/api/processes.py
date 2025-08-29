"""Process management API router for BPMN workflows."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse

from ..models.process_models import (
    Process, ProcessCreate, ProcessUpdate, ProcessSummary,
    ProcessInstance, ProcessInstanceCreate, ProcessInstanceUpdate, ProcessInstanceSummary,
    Template, TemplateCreate, TemplateUpdate, TemplateSummary
)
from ..services.process_service import ProcessService, TemplateService
from ..core.mongodb import get_mongodb_db

router = APIRouter(tags=["Process Management"])


# Health Check Route
@router.get("/health")
async def health_check():
    """Health check for process management service."""
    return {
        "status": "healthy",
        "service": "Process Management",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Process Instance Routes (list all)
@router.get("/instances", response_model=List[ProcessInstanceSummary])
async def list_process_instances(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    process_id: Optional[str] = Query(None, description="Filter by process ID"),
    status: Optional[str] = Query(None, description="Filter by instance status"),
    db = Depends(get_mongodb_db)
):
    """List all process instances with filtering and pagination."""
    try:
        process_service = ProcessService(db)
        instances = await process_service.list_process_instances(
            skip=skip,
            limit=limit,
            process_id=process_id,
            status=status
        )
        return instances
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Template Management Routes (list all)
@router.get("/templates", response_model=List[TemplateSummary])
async def list_templates(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db = Depends(get_mongodb_db)
):
    """List all templates with filtering and pagination."""
    try:
        template_service = TemplateService(db)
        templates = await template_service.list_templates(
            skip=skip,
            limit=limit,
            category=category,
            is_public=is_public,
            is_active=is_active
        )
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Process Management Routes
@router.post("/", response_model=Process, status_code=201)
async def create_process(
    process_data: ProcessCreate,
    user_id: str = Query(..., description="User ID creating the process"),
    db = Depends(get_mongodb_db)
):
    """Create a new BPMN process."""
    try:
        process_service = ProcessService(db)
        process = await process_service.create_process(process_data, user_id)
        return process
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ProcessSummary])
async def list_processes(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name, description, or tags"),
    db = Depends(get_mongodb_db)
):
    """List all processes with filtering and pagination."""
    try:
        process_service = ProcessService(db)
        processes = await process_service.list_processes(
            skip=skip,
            limit=limit,
            category=category,
            is_active=is_active,
            search=search
        )
        return processes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{process_id}", response_model=Process)
async def get_process(
    process_id: str = Path(..., description="Process ID or process_id field"),
    db = Depends(get_mongodb_db)
):
    """Get a specific process by ID."""
    try:
        process_service = ProcessService(db)
        process = await process_service.get_process(process_id)
        if not process:
            raise HTTPException(status_code=404, detail="Process not found")
        return process
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{process_id}", response_model=Process)
async def update_process(
    process_id: str = Path(..., description="Process ID or process_id field"),
    update_data: ProcessUpdate = ...,
    user_id: str = Query(..., description="User ID updating the process"),
    db = Depends(get_mongodb_db)
):
    """Update a process."""
    try:
        process_service = ProcessService(db)
        process = await process_service.update_process(process_id, update_data, user_id)
        if not process:
            raise HTTPException(status_code=404, detail="Process not found")
        return process
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{process_id}")
async def delete_process(
    process_id: str = Path(..., description="Process ID or process_id field"),
    db = Depends(get_mongodb_db)
):
    """Delete a process."""
    try:
        process_service = ProcessService(db)
        success = await process_service.delete_process(process_id)
        if not success:
            raise HTTPException(status_code=404, detail="Process not found")
        return {"message": "Process deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Process Instance Routes (specific process)
@router.post("/{process_id}/instances", response_model=ProcessInstance, status_code=201)
async def create_process_instance(
    process_id: str = Path(..., description="Process ID"),
    instance_data: ProcessInstanceCreate = ...,
    user_id: str = Query(..., description="User ID starting the instance"),
    db = Depends(get_mongodb_db)
):
    """Create a new process instance."""
    try:
        # Set the process_id from the path
        instance_data.process_id = process_id
        
        # Get process name for reference
        process_service = ProcessService(db)
        process = await process_service.get_process(process_id)
        if not process:
            raise HTTPException(status_code=404, detail="Process not found")
        
        instance_data.process_name = process.name
        instance = await process_service.create_process_instance(instance_data, user_id)
        return instance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances/{instance_id}", response_model=ProcessInstance)
async def get_process_instance(
    instance_id: str = Path(..., description="Instance ID or instance_id field"),
    db = Depends(get_mongodb_db)
):
    """Get a specific process instance by ID."""
    try:
        process_service = ProcessService(db)
        instance = await process_service.get_process_instance(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Process instance not found")
        return instance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/instances/{instance_id}", response_model=ProcessInstance)
async def update_process_instance(
    instance_id: str = Path(..., description="Instance ID or instance_id field"),
    update_data: ProcessInstanceUpdate = ...,
    db = Depends(get_mongodb_db)
):
    """Update a process instance."""
    try:
        process_service = ProcessService(db)
        instance = await process_service.update_process_instance(instance_id, update_data)
        if not instance:
            raise HTTPException(status_code=404, detail="Process instance not found")
        return instance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/instances/{instance_id}")
async def delete_process_instance(
    instance_id: str = Path(..., description="Instance ID or instance_id field"),
    db = Depends(get_mongodb_db)
):
    """Delete a process instance."""
    try:
        process_service = ProcessService(db)
        success = await process_service.delete_process_instance(instance_id)
        if not success:
            raise HTTPException(status_code=404, detail="Process instance not found")
        return {"message": "Process instance deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instances/{instance_id}/execute")
async def execute_process_instance(
    instance_id: str = Path(..., description="Instance ID or instance_id field"),
    db = Depends(get_mongodb_db)
):
    """Execute a process instance."""
    try:
        process_service = ProcessService(db)
        result = await process_service.execute_process_instance(instance_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Template Management Routes
@router.post("/templates", response_model=Template, status_code=201)
async def create_template(
    template_data: TemplateCreate,
    user_id: str = Query(..., description="User ID creating the template"),
    db = Depends(get_mongodb_db)
):
    """Create a new BPMN template."""
    try:
        template_service = TemplateService(db)
        template = await template_service.create_template(template_data, user_id)
        return template
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{process_id}/templates", response_model=Template, status_code=201)
async def create_template_from_process(
    process_id: str = Path(..., description="Process ID to create template from"),
    template_data: TemplateCreate = ...,
    user_id: str = Query(..., description="User ID creating the template"),
    db = Depends(get_mongodb_db)
):
    """Create a template from an existing process."""
    try:
        template_service = TemplateService(db)
        template = await template_service.create_template_from_process(process_id, template_data, user_id)
        return template
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates/{template_id}", response_model=Template)
async def get_template(
    template_id: str = Path(..., description="Template ID or process_id field"),
    db = Depends(get_mongodb_db)
):
    """Get a specific template by ID."""
    try:
        template_service = TemplateService(db)
        template = await template_service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/templates/{template_id}", response_model=Template)
async def update_template(
    template_id: str = Path(..., description="Template ID or process_id field"),
    update_data: TemplateUpdate = ...,
    user_id: str = Query(..., description="User ID updating the template"),
    db = Depends(get_mongodb_db)
):
    """Update a template."""
    try:
        template_service = TemplateService(db)
        template = await template_service.update_template(template_id, update_data, user_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str = Path(..., description="Template ID or process_id field"),
    db = Depends(get_mongodb_db)
):
    """Delete a template."""
    try:
        template_service = TemplateService(db)
        success = await template_service.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"message": "Template deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
