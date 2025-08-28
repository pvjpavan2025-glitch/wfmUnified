"""
Business logic for Process Service.
"""
from typing import List, Optional
from datetime import datetime
import httpx
from shared.models import PaginationParams
from .models import (
    ProcessInstance, ProcessInstanceCreate, ProcessInstanceUpdate, ProcessInstanceResponse,
    TaskInstance, TaskInstanceCreate, TaskInstanceUpdate, TaskInstanceResponse,
    ProcessExecutionRequest, ProcessExecutionResponse
)
from .repository import ProcessInstanceRepository, TaskInstanceRepository


class ProcessService:
    """Service for process and task instance management."""
    
    def __init__(self):
        self.process_repo = ProcessInstanceRepository()
        self.task_repo = TaskInstanceRepository()
        self.bpmn_engine_url = "http://localhost:8100"  # wfmProcess service
        self.vendor_service_url = "http://localhost:8007"  # vendor service
    
    async def execute_process(self, request: ProcessExecutionRequest, tenant_id: str) -> ProcessExecutionResponse:
        """Execute a process by creating an instance and starting BPMN execution."""
        # Create process instance
        instance_data = ProcessInstanceCreate(
            process_id=request.process_id,
            order_id=request.order_id,
            input_data=request.input_data,
            priority=request.priority,
            tenant_id=tenant_id
        )
        
        process_instance = ProcessInstance(
            **instance_data.model_dump(),
            started_at=datetime.utcnow()
        )
        
        created_instance = await self.process_repo.create(process_instance)
        
        # Start BPMN execution via wfmProcess service
        try:
            async with httpx.AsyncClient() as client:
                bpmn_response = await client.post(
                    f"{self.bpmn_engine_url}/processes/{request.process_id}/start",
                    json={
                        "process_instance_id": created_instance.id,
                        "input_data": request.input_data,
                        "tenant_id": tenant_id
                    }
                )
                bpmn_data = bpmn_response.json()
                
                # Update instance with execution ID
                await self.process_repo.update(
                    created_instance.id,
                    tenant_id,
                    {
                        "execution_id": bpmn_data.get("execution_id"),
                        "status": "in_progress"
                    }
                )
                
                # Create task instances from BPMN tasks
                created_tasks = []
                for task_data in bpmn_data.get("tasks", []):
                    task_instance = await self.create_task_instance_from_bpmn(
                        created_instance.id,
                        task_data,
                        tenant_id
                    )
                    created_tasks.append(task_instance.id)
                
                # Auto-assign tasks if requested
                if request.auto_assign_tasks:
                    await self.auto_assign_tasks(created_tasks, tenant_id)
                
                return ProcessExecutionResponse(
                    process_instance_id=created_instance.id,
                    execution_id=bpmn_data.get("execution_id"),
                    status="in_progress",
                    created_tasks=created_tasks,
                    message="Process started successfully"
                )
                
        except Exception as e:
            # Update instance status to failed
            await self.process_repo.update(
                created_instance.id,
                tenant_id,
                {
                    "status": "failed",
                    "error_message": str(e)
                }
            )
            raise
    
    async def create_task_instance_from_bpmn(self, process_instance_id: str, task_data: dict, tenant_id: str) -> TaskInstance:
        """Create a task instance from BPMN task data."""
        task_create = TaskInstanceCreate(
            task_definition_id=task_data.get("task_definition_id"),
            process_instance_id=process_instance_id,
            bpmn_task_id=task_data.get("bpmn_task_id"),
            name=task_data.get("name"),
            task_type=task_data.get("task_type", "user_task"),
            input_data=task_data.get("input_data", {}),
            required_skills=task_data.get("required_skills", []),
            estimated_duration_minutes=task_data.get("estimated_duration_minutes", 60),
            priority=task_data.get("priority", "medium"),
            tenant_id=tenant_id
        )
        
        task_instance = TaskInstance(**task_create.model_dump())
        return await self.task_repo.create(task_instance)
    
    async def auto_assign_tasks(self, task_ids: List[str], tenant_id: str):
        """Automatically assign tasks to available technicians."""
        try:
            async with httpx.AsyncClient() as client:
                for task_id in task_ids:
                    task = await self.task_repo.get_by_id(task_id, tenant_id)
                    if not task or task.assigned_technician_id:
                        continue
                    
                    # Get available technicians with required skills
                    response = await client.get(
                        f"{self.vendor_service_url}/technicians/available",
                        params={"skills": task.required_skills}
                    )
                    
                    if response.status_code == 200:
                        technicians = response.json()
                        if technicians:
                            # Assign to first available technician
                            technician = technicians[0]
                            await client.post(
                                f"{self.vendor_service_url}/tasks/{task_id}/assign",
                                params={"technician_id": technician["id"]}
                            )
                            
                            # Update task instance
                            await self.task_repo.update(
                                task_id,
                                tenant_id,
                                {
                                    "assigned_technician_id": technician["id"],
                                    "status": "assigned"
                                }
                            )
        except Exception as e:
            # Log error but don't fail the process
            print(f"Auto-assignment failed: {e}")
    
    async def create_process_instance(self, instance_data: ProcessInstanceCreate) -> ProcessInstanceResponse:
        """Create a new process instance."""
        process_instance = ProcessInstance(**instance_data.model_dump())
        created_instance = await self.process_repo.create(process_instance)
        return ProcessInstanceResponse(**created_instance.model_dump())
    
    async def get_process_instance(self, instance_id: str, tenant_id: str) -> Optional[ProcessInstanceResponse]:
        """Get process instance by ID."""
        instance = await self.process_repo.get_by_id(instance_id, tenant_id)
        if not instance:
            return None
        
        # Get associated tasks
        tasks = await self.task_repo.get_by_process_instance(instance_id, tenant_id)
        instance.tasks = [task.id for task in tasks]
        
        return ProcessInstanceResponse(**instance.model_dump())
    
    async def get_process_instances_by_order(self, order_id: str, tenant_id: str) -> List[ProcessInstanceResponse]:
        """Get all process instances for an order."""
        instances = await self.process_repo.get_by_order(order_id, tenant_id)
        responses = []
        
        for instance in instances:
            # Get associated tasks
            tasks = await self.task_repo.get_by_process_instance(instance.id, tenant_id)
            instance.tasks = [task.id for task in tasks]
            responses.append(ProcessInstanceResponse(**instance.model_dump()))
        
        return responses
    
    async def update_process_instance(self, instance_id: str, tenant_id: str, update_data: ProcessInstanceUpdate) -> Optional[ProcessInstanceResponse]:
        """Update process instance."""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        updated_instance = await self.process_repo.update(instance_id, tenant_id, update_dict)
        return ProcessInstanceResponse(**updated_instance.model_dump()) if updated_instance else None
    
    async def create_task_instance(self, task_data: TaskInstanceCreate) -> TaskInstanceResponse:
        """Create a new task instance."""
        task_instance = TaskInstance(**task_data.model_dump())
        created_task = await self.task_repo.create(task_instance)
        return TaskInstanceResponse(**created_task.model_dump())
    
    async def get_task_instance(self, instance_id: str, tenant_id: str) -> Optional[TaskInstanceResponse]:
        """Get task instance by ID."""
        instance = await self.task_repo.get_by_id(instance_id, tenant_id)
        return TaskInstanceResponse(**instance.model_dump()) if instance else None
    
    async def get_task_instances_by_process(self, process_instance_id: str, tenant_id: str) -> List[TaskInstanceResponse]:
        """Get all task instances for a process instance."""
        instances = await self.task_repo.get_by_process_instance(process_instance_id, tenant_id)
        return [TaskInstanceResponse(**instance.model_dump()) for instance in instances]
    
    async def get_task_instances_by_technician(self, technician_id: str, tenant_id: str) -> List[TaskInstanceResponse]:
        """Get all task instances assigned to a technician."""
        instances = await self.task_repo.get_by_technician(technician_id, tenant_id)
        return [TaskInstanceResponse(**instance.model_dump()) for instance in instances]
    
    async def get_unassigned_tasks(self, tenant_id: str, required_skills: Optional[List[str]] = None) -> List[TaskInstanceResponse]:
        """Get unassigned task instances."""
        instances = await self.task_repo.get_unassigned_tasks(tenant_id, required_skills)
        return [TaskInstanceResponse(**instance.model_dump()) for instance in instances]
    
    async def update_task_instance(self, instance_id: str, tenant_id: str, update_data: TaskInstanceUpdate) -> Optional[TaskInstanceResponse]:
        """Update task instance."""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        updated_instance = await self.task_repo.update(instance_id, tenant_id, update_dict)
        return TaskInstanceResponse(**updated_instance.model_dump()) if updated_instance else None
    
    async def complete_task(self, task_id: str, tenant_id: str, output_data: dict, notes: Optional[str] = None) -> Optional[TaskInstanceResponse]:
        """Complete a task and notify BPMN engine."""
        # Update task instance
        update_data = {
            "status": "completed",
            "actual_end": datetime.utcnow(),
            "output_data": output_data,
            "notes": notes
        }
        
        updated_task = await self.task_repo.update(task_id, tenant_id, update_data)
        if not updated_task:
            return None
        
        # Notify BPMN engine
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.bpmn_engine_url}/tasks/{updated_task.bpmn_task_id}/complete",
                    json={
                        "process_instance_id": updated_task.process_instance_id,
                        "output_data": output_data,
                        "tenant_id": tenant_id
                    }
                )
        except Exception as e:
            print(f"Failed to notify BPMN engine: {e}")
        
        return TaskInstanceResponse(**updated_task.model_dump())
    
    async def cancel_process_instance(self, instance_id: str, tenant_id: str, reason: str) -> bool:
        """Cancel a process instance and all its tasks."""
        # Update process instance
        await self.process_repo.update(
            instance_id,
            tenant_id,
            {
                "status": "cancelled",
                "error_message": reason,
                "completed_at": datetime.utcnow()
            }
        )
        
        # Cancel all associated tasks
        tasks = await self.task_repo.get_by_process_instance(instance_id, tenant_id)
        for task in tasks:
            if task.status not in ["completed", "cancelled"]:
                await self.task_repo.update(
                    task.id,
                    tenant_id,
                    {
                        "status": "cancelled",
                        "error_message": reason
                    }
                )
        
        # Notify BPMN engine
        try:
            async with httpx.AsyncClient() as client:
                process_instance = await self.process_repo.get_by_id(instance_id, tenant_id)
                if process_instance and process_instance.execution_id:
                    await client.post(
                        f"{self.bpmn_engine_url}/executions/{process_instance.execution_id}/cancel",
                        json={"reason": reason, "tenant_id": tenant_id}
                    )
        except Exception as e:
            print(f"Failed to notify BPMN engine: {e}")
        
        return True
