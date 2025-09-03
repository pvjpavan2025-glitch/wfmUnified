"""
Workflow Instance Service for business logic operations.
"""
import uuid
import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException

from .models import (
    WorkflowInstance,
    WorkflowInstanceCreate,
    WorkflowInstanceUpdate,
    WorkflowInstanceResponse,
    WorkflowInstanceStatus,
    WorkflowStep,
    WorkflowStepStatus,
    WorkflowExecutionLog,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse
)
from .repository import WorkflowInstanceRepository


class WorkflowInstanceService:
    """Service for workflow instance business logic."""
    
    def __init__(self):
        self.repository = WorkflowInstanceRepository()
        self.spiff_workflow_url = "http://localhost:8002"  # wfmProcess service URL
    
    async def create_workflow_instance(
        self, 
        instance_data: WorkflowInstanceCreate
    ) -> WorkflowInstanceResponse:
        """Create a new workflow instance."""
        try:
            # Create the instance
            instance = await self.repository.create_instance(instance_data)
            
            # Log creation
            log_entry = WorkflowExecutionLog(
                level="INFO",
                message=f"Workflow instance '{instance.name}' created successfully",
                data={"created_by": instance_data.created_by}
            )
            await self.repository.add_execution_log(instance.id, log_entry)
            
            return self._to_response_model(instance)
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create workflow instance: {str(e)}"
            )
    
    async def get_workflow_instance(self, instance_id: str) -> WorkflowInstanceResponse:
        """Get workflow instance by ID."""
        instance = await self.repository.get_instance_by_id(instance_id)
        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow instance {instance_id} not found"
            )
        
        return self._to_response_model(instance)
    
    async def get_workflow_instances(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[WorkflowInstanceStatus] = None,
        created_by: Optional[str] = None
    ) -> List[WorkflowInstanceResponse]:
        """Get list of workflow instances."""
        instances = await self.repository.get_instances(
            skip=skip,
            limit=limit,
            status=status,
            created_by=created_by
        )
        
        return [self._to_response_model(instance) for instance in instances]
    
    async def update_workflow_instance(
        self,
        instance_id: str,
        update_data: WorkflowInstanceUpdate
    ) -> WorkflowInstanceResponse:
        """Update workflow instance."""
        instance = await self.repository.update_instance(instance_id, update_data)
        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow instance {instance_id} not found"
            )
        
        # Log update
        log_entry = WorkflowExecutionLog(
            level="INFO",
            message=f"Workflow instance updated",
            data={"updated_by": update_data.updated_by, "changes": update_data.dict(exclude_unset=True)}
        )
        await self.repository.add_execution_log(instance_id, log_entry)
        
        return self._to_response_model(instance)
    
    async def execute_workflow(
        self,
        execution_request: WorkflowExecutionRequest
    ) -> WorkflowExecutionResponse:
        """Execute a workflow instance using SpiffWorkflow."""
        instance_id = execution_request.workflow_instance_id
        
        try:
            # Get the workflow instance
            instance = await self.repository.get_instance_by_id(instance_id)
            if not instance:
                raise HTTPException(
                    status_code=404,
                    detail=f"Workflow instance {instance_id} not found"
                )
            
            # Update status to running
            await self.repository.update_instance(
                instance_id,
                WorkflowInstanceUpdate(
                    status=WorkflowInstanceStatus.RUNNING,
                    updated_by="system"
                )
            )
            
            # Log execution start
            log_entry = WorkflowExecutionLog(
                level="INFO",
                message="Workflow execution started",
                data={"input_data": execution_request.input_data}
            )
            await self.repository.add_execution_log(instance_id, log_entry)
            
            # Execute workflow using SpiffWorkflow
            execution_id = str(uuid.uuid4())
            started_steps = await self._execute_with_spiffworkflow(
                instance, 
                execution_request.input_data,
                execution_id
            )
            
            return WorkflowExecutionResponse(
                workflow_instance_id=instance_id,
                execution_id=execution_id,
                status=WorkflowInstanceStatus.RUNNING,
                message="Workflow execution started successfully",
                started_steps=started_steps
            )
            
        except Exception as e:
            # Update status to failed
            await self.repository.update_instance(
                instance_id,
                WorkflowInstanceUpdate(
                    status=WorkflowInstanceStatus.FAILED,
                    error_message=str(e),
                    updated_by="system"
                )
            )
            
            # Log error
            log_entry = WorkflowExecutionLog(
                level="ERROR",
                message=f"Workflow execution failed: {str(e)}",
                data={"error": str(e)}
            )
            await self.repository.add_execution_log(instance_id, log_entry)
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to execute workflow: {str(e)}"
            )
    
    async def update_step_status(
        self,
        instance_id: str,
        step_id: str,
        status: WorkflowStepStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update workflow step status."""
        try:
            success = await self.repository.update_step_status(
                instance_id, step_id, status.value, output_data, error_message
            )
            
            if success:
                # Log step status change
                log_entry = WorkflowExecutionLog(
                    level="INFO" if status != WorkflowStepStatus.FAILED else "ERROR",
                    message=f"Step {step_id} status changed to {status.value}",
                    step_id=step_id,
                    data={"output_data": output_data, "error_message": error_message}
                )
                await self.repository.add_execution_log(instance_id, log_entry)
                
                # Check if workflow is complete
                await self._check_workflow_completion(instance_id)
            
            return success
            
        except Exception as e:
            # Log error
            log_entry = WorkflowExecutionLog(
                level="ERROR",
                message=f"Failed to update step status: {str(e)}",
                step_id=step_id,
                data={"error": str(e)}
            )
            await self.repository.add_execution_log(instance_id, log_entry)
            return False
    
    async def cancel_workflow(self, instance_id: str, cancelled_by: str) -> bool:
        """Cancel a running workflow."""
        try:
            instance = await self.repository.update_instance(
                instance_id,
                WorkflowInstanceUpdate(
                    status=WorkflowInstanceStatus.CANCELLED,
                    updated_by=cancelled_by,
                    completed_at=datetime.utcnow()
                )
            )
            
            if instance:
                # Log cancellation
                log_entry = WorkflowExecutionLog(
                    level="INFO",
                    message="Workflow cancelled by user",
                    data={"cancelled_by": cancelled_by}
                )
                await self.repository.add_execution_log(instance_id, log_entry)
                
                # Cancel in SpiffWorkflow
                await self._cancel_in_spiffworkflow(instance_id)
                
                return True
            
            return False
            
        except Exception as e:
            # Log error
            log_entry = WorkflowExecutionLog(
                level="ERROR",
                message=f"Failed to cancel workflow: {str(e)}",
                data={"error": str(e)}
            )
            await self.repository.add_execution_log(instance_id, log_entry)
            return False
    
    async def _execute_with_spiffworkflow(
        self,
        instance: WorkflowInstance,
        input_data: Dict[str, Any],
        execution_id: str
    ) -> List[str]:
        """Execute workflow using SpiffWorkflow engine."""
        # This is where we integrate with the SpiffWorkflow engine
        # For now, this is a placeholder implementation
        
        # Parse BPMN to extract steps
        steps = self._parse_bpmn_steps(instance.bpmn_xml)
        
        # Update instance with steps
        instance.steps = steps
        await self.repository.update_instance(
            instance.id,
            WorkflowInstanceUpdate(execution_data={"execution_id": execution_id})
        )
        
        # Start first step(s)
        started_steps = []
        for step in steps:
            if step.step_type == "startEvent":
                step.status = WorkflowStepStatus.RUNNING
                step.started_at = datetime.utcnow()
                started_steps.append(step.step_id)
        
        return started_steps
    
    async def _parse_bpmn_steps(self, bpmn_xml: str) -> List[WorkflowStep]:
        """Parse BPMN XML to extract workflow steps."""
        # This is a simplified parser - in reality, you'd use a proper BPMN parser
        # For now, return some sample steps
        return [
            WorkflowStep(
                step_id="start_1",
                name="Start Process",
                step_type="startEvent",
                status=WorkflowStepStatus.PENDING
            ),
            WorkflowStep(
                step_id="task_1",
                name="Process Task",
                step_type="userTask",
                status=WorkflowStepStatus.PENDING
            ),
            WorkflowStep(
                step_id="end_1",
                name="End Process",
                step_type="endEvent",
                status=WorkflowStepStatus.PENDING
            )
        ]
    
    async def _check_workflow_completion(self, instance_id: str) -> None:
        """Check if workflow is complete and update status."""
        instance = await self.repository.get_instance_by_id(instance_id)
        if not instance:
            return
        
        # Check if all steps are completed or failed
        all_completed = all(
            step.status in [WorkflowStepStatus.COMPLETED, WorkflowStepStatus.SKIPPED]
            for step in instance.steps
        )
        
        any_failed = any(
            step.status == WorkflowStepStatus.FAILED
            for step in instance.steps
        )
        
        if any_failed:
            await self.repository.update_instance(
                instance_id,
                WorkflowInstanceUpdate(
                    status=WorkflowInstanceStatus.FAILED,
                    completed_at=datetime.utcnow(),
                    updated_by="system"
                )
            )
        elif all_completed:
            await self.repository.update_instance(
                instance_id,
                WorkflowInstanceUpdate(
                    status=WorkflowInstanceStatus.COMPLETED,
                    completed_at=datetime.utcnow(),
                    updated_by="system"
                )
            )
    
    async def _cancel_in_spiffworkflow(self, instance_id: str) -> None:
        """Cancel workflow execution in SpiffWorkflow engine."""
        # Integration with SpiffWorkflow to cancel execution
        # This is a placeholder for the actual implementation
        pass
    
    def _to_response_model(self, instance: WorkflowInstance) -> WorkflowInstanceResponse:
        """Convert WorkflowInstance to WorkflowInstanceResponse."""
        return WorkflowInstanceResponse(
            id=instance.id,
            name=instance.name,
            description=instance.description,
            workflow_definition_id=instance.workflow_definition_id,
            status=instance.status,
            current_step=instance.current_step,
            input_data=instance.input_data,
            execution_data=instance.execution_data,
            error_message=instance.error_message,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
            created_by=instance.created_by,
            updated_by=instance.updated_by,
            started_at=instance.started_at,
            completed_at=instance.completed_at,
            steps=instance.steps,
            execution_logs=instance.execution_logs
        )
