"""
Process Service FastAPI application.
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from typing import List, Optional
from shared.auth import get_current_user, get_tenant_id
from shared.models import PaginationParams, SuccessResponse, ErrorResponse
from .models import (
    ProcessInstanceCreate, ProcessInstanceUpdate, ProcessInstanceResponse,
    TaskInstanceCreate, TaskInstanceUpdate, TaskInstanceResponse,
    ProcessExecutionRequest, ProcessExecutionResponse
)
from .service import ProcessService

app = FastAPI(
    title="Process Service",
    description="Manages BPMN process and task instances",
    version="1.0.0"
)

process_service = ProcessService()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "process_service"}


# Process execution endpoints
@app.post("/processes/execute", response_model=ProcessExecutionResponse)
async def execute_process(
    request: ProcessExecutionRequest,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Execute a process by creating an instance and starting BPMN execution."""
    return await process_service.execute_process(request, tenant_id)


# Process instance endpoints
@app.post("/process-instances", response_model=ProcessInstanceResponse)
async def create_process_instance(
    instance_data: ProcessInstanceCreate,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Create a new process instance."""
    instance_data.tenant_id = tenant_id
    return await process_service.create_process_instance(instance_data)


@app.get("/process-instances/{instance_id}", response_model=ProcessInstanceResponse)
async def get_process_instance(
    instance_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get process instance by ID."""
    instance = await process_service.get_process_instance(instance_id, tenant_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Process instance not found")
    return instance


@app.get("/orders/{order_id}/process-instances", response_model=List[ProcessInstanceResponse])
async def get_process_instances_by_order(
    order_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get all process instances for an order."""
    return await process_service.get_process_instances_by_order(order_id, tenant_id)


@app.put("/process-instances/{instance_id}", response_model=ProcessInstanceResponse)
async def update_process_instance(
    instance_id: str,
    update_data: ProcessInstanceUpdate,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Update process instance."""
    instance = await process_service.update_process_instance(instance_id, tenant_id, update_data)
    if not instance:
        raise HTTPException(status_code=404, detail="Process instance not found")
    return instance


@app.post("/process-instances/{instance_id}/cancel", response_model=SuccessResponse)
async def cancel_process_instance(
    instance_id: str,
    reason: str = Query(..., description="Reason for cancellation"),
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Cancel a process instance and all its tasks."""
    success = await process_service.cancel_process_instance(instance_id, tenant_id, reason)
    if not success:
        raise HTTPException(status_code=404, detail="Process instance not found")
    return SuccessResponse(message="Process instance cancelled successfully")


# Task instance endpoints
@app.post("/task-instances", response_model=TaskInstanceResponse)
async def create_task_instance(
    task_data: TaskInstanceCreate,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Create a new task instance."""
    task_data.tenant_id = tenant_id
    return await process_service.create_task_instance(task_data)


@app.get("/task-instances/{instance_id}", response_model=TaskInstanceResponse)
async def get_task_instance(
    instance_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get task instance by ID."""
    instance = await process_service.get_task_instance(instance_id, tenant_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Task instance not found")
    return instance


@app.get("/process-instances/{process_instance_id}/task-instances", response_model=List[TaskInstanceResponse])
async def get_task_instances_by_process(
    process_instance_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get all task instances for a process instance."""
    return await process_service.get_task_instances_by_process(process_instance_id, tenant_id)


@app.get("/technicians/{technician_id}/task-instances", response_model=List[TaskInstanceResponse])
async def get_task_instances_by_technician(
    technician_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get all task instances assigned to a technician."""
    return await process_service.get_task_instances_by_technician(technician_id, tenant_id)


@app.get("/task-instances/unassigned", response_model=List[TaskInstanceResponse])
async def get_unassigned_tasks(
    skills: Optional[List[str]] = Query(None, description="Filter by required skills"),
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Get unassigned task instances."""
    return await process_service.get_unassigned_tasks(tenant_id, skills)


@app.put("/task-instances/{instance_id}", response_model=TaskInstanceResponse)
async def update_task_instance(
    instance_id: str,
    update_data: TaskInstanceUpdate,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Update task instance."""
    instance = await process_service.update_task_instance(instance_id, tenant_id, update_data)
    if not instance:
        raise HTTPException(status_code=404, detail="Task instance not found")
    return instance


@app.post("/task-instances/{task_id}/complete", response_model=TaskInstanceResponse)
async def complete_task(
    task_id: str,
    output_data: dict,
    notes: Optional[str] = None,
    tenant_id: str = Depends(get_tenant_id),
    current_user: dict = Depends(get_current_user)
):
    """Complete a task and notify BPMN engine."""
    task = await process_service.complete_task(task_id, tenant_id, output_data, notes)
    if not task:
        raise HTTPException(status_code=404, detail="Task instance not found")
    return task


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
