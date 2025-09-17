"""
Workflow Instance Service FastAPI application.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from shared.sql_database import init_db, close_db, get_db_session

from .models import (
    WorkflowInstanceCreate,
    WorkflowInstanceUpdate,
    WorkflowInstanceResponse,
    WorkflowInstanceStatus,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse
)
from .service import WorkflowInstanceService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    await init_db()
    logging.info("Database initialized")
    
    yield
    
    # Shutdown: Close database connections
    await close_db()
    logging.info("Database connections closed")


app = FastAPI(
    title="Workflow Instance Service",
    description="Service for managing workflow execution instances",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session

# Dependency to get service instance
async def get_workflow_service(
    db: AsyncSession = Depends(get_db)
) -> WorkflowInstanceService:
    return WorkflowInstanceService(db_session=db)


@app.post("/instances", response_model=WorkflowInstanceResponse)
async def create_workflow_instance(
    instance_data: WorkflowInstanceCreate,
    service: WorkflowInstanceService = Depends(get_workflow_service)
):
    """Create a new workflow instance."""
    return await service.create_workflow_instance(instance_data)


@app.get("/instances/{instance_id}", response_model=WorkflowInstanceResponse)
async def get_workflow_instance(
    instance_id: str,
    service: WorkflowInstanceService = Depends(get_workflow_service)
):
    """Get workflow instance by ID."""
    return await service.get_workflow_instance(instance_id)


@app.get("/instances", response_model=List[WorkflowInstanceResponse])
async def get_workflow_instances(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[WorkflowInstanceStatus] = None,
    created_by: Optional[str] = None,
    service: WorkflowInstanceService = Depends(get_workflow_service)
):
    """Get list of workflow instances with optional filtering."""
    return await service.get_workflow_instances(
        skip=skip,
        limit=limit,
        status=status,
        created_by=created_by
    )


@app.put("/instances/{instance_id}", response_model=WorkflowInstanceResponse)
async def update_workflow_instance(
    instance_id: str,
    update_data: WorkflowInstanceUpdate,
    service: WorkflowInstanceService = Depends(get_workflow_service)
):
    """Update workflow instance."""
    return await service.update_workflow_instance(instance_id, update_data)


@app.post("/instances/{instance_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    instance_id: str,
    execution_request: WorkflowExecutionRequest,
    service: WorkflowInstanceService = Depends(get_workflow_service)
):
    """Execute a workflow instance."""
    execution_request.workflow_instance_id = instance_id
    return await service.execute_workflow(execution_request)


@app.post("/instances/{instance_id}/cancel")
async def cancel_workflow(
    instance_id: str,
    cancelled_by: str = Query(..., description="User who cancelled the workflow"),
    service: WorkflowInstanceService = Depends(get_workflow_service)
):
    """Cancel a running workflow."""
    success = await service.cancel_workflow(instance_id, cancelled_by)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel workflow")
    return {"message": "Workflow cancelled successfully"}


@app.put("/instances/{instance_id}/steps/{step_id}/status")
async def update_step_status(
    instance_id: str,
    step_id: str,
    status: str,
    output_data: Optional[dict] = None,
    error_message: Optional[str] = None,
    service: WorkflowInstanceService = Depends(get_workflow_service)
):
    """Update workflow step status."""
    from .models import WorkflowStepStatus
    
    try:
        step_status = WorkflowStepStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    success = await service.update_step_status(
        instance_id, step_id, step_status, output_data, error_message
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update step status")
    
    return {"message": "Step status updated successfully"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "workflow-instance-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
