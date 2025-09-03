"""
Workflow Execution Service for SpiffWorkflow integration.
"""
import uuid
import json
import asyncio
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from SpiffWorkflow.workflow import Workflow
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.bpmn.parser.BpmnParser import BpmnParser
from SpiffWorkflow.bpmn.serializer.BpmnSerializer import BpmnSerializer
from SpiffWorkflow.exceptions import WorkflowException

from ..models.workflow import WorkflowInstance
from ..core.mongodb import get_mongodb_database


class WorkflowExecutionService:
    """Service for executing workflows using SpiffWorkflow."""
    
    def __init__(self):
        self.db = get_mongodb_database()
        self.workflow_instance_service_url = "http://localhost:8003"  # workflow instance service
        self.active_workflows: Dict[str, BpmnWorkflow] = {}
    
    async def create_and_execute_workflow(
        self,
        bpmn_xml: str,
        workflow_name: str,
        workflow_description: str,
        input_data: Dict[str, Any],
        created_by: str
    ) -> Dict[str, Any]:
        """Create workflow instance and start execution."""
        try:
            # Create workflow instance via workflow instance service
            workflow_instance = await self._create_workflow_instance(
                workflow_name, workflow_description, bpmn_xml, input_data, created_by
            )
            
            # Parse BPMN and create SpiffWorkflow instance
            workflow = await self._create_spiff_workflow(bpmn_xml, input_data)
            
            # Store active workflow
            self.active_workflows[workflow_instance["id"]] = workflow
            
            # Start execution
            execution_result = await self._execute_workflow_steps(
                workflow_instance["id"], workflow
            )
            
            return {
                "workflow_instance_id": workflow_instance["id"],
                "status": "running",
                "message": "Workflow execution started successfully",
                "execution_result": execution_result
            }
            
        except Exception as e:
            # Log error and update workflow instance status
            await self._log_workflow_error(workflow_instance.get("id") if 'workflow_instance' in locals() else None, str(e))
            raise WorkflowException(f"Failed to create and execute workflow: {str(e)}")
    
    async def continue_workflow_execution(
        self,
        workflow_instance_id: str,
        task_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Continue workflow execution after user task completion."""
        try:
            workflow = self.active_workflows.get(workflow_instance_id)
            if not workflow:
                # Try to restore workflow from database
                workflow = await self._restore_workflow(workflow_instance_id)
                if not workflow:
                    raise WorkflowException(f"Workflow instance {workflow_instance_id} not found")
            
            # Update task data if provided
            if task_data:
                ready_tasks = workflow.get_ready_user_tasks()
                for task in ready_tasks:
                    task.data.update(task_data)
                    workflow.complete_task_from_id(task.id)
            
            # Continue execution
            execution_result = await self._execute_workflow_steps(workflow_instance_id, workflow)
            
            return {
                "workflow_instance_id": workflow_instance_id,
                "status": "running" if not workflow.is_completed() else "completed",
                "execution_result": execution_result
            }
            
        except Exception as e:
            await self._log_workflow_error(workflow_instance_id, str(e))
            raise WorkflowException(f"Failed to continue workflow execution: {str(e)}")
    
    async def cancel_workflow(self, workflow_instance_id: str, cancelled_by: str) -> bool:
        """Cancel workflow execution."""
        try:
            # Remove from active workflows
            if workflow_instance_id in self.active_workflows:
                del self.active_workflows[workflow_instance_id]
            
            # Update workflow instance status via service
            await self._update_workflow_instance_status(
                workflow_instance_id, "cancelled", cancelled_by
            )
            
            await self._log_workflow_event(
                workflow_instance_id, "INFO", "Workflow cancelled by user", {"cancelled_by": cancelled_by}
            )
            
            return True
            
        except Exception as e:
            await self._log_workflow_error(workflow_instance_id, str(e))
            return False
    
    async def get_workflow_status(self, workflow_instance_id: str) -> Dict[str, Any]:
        """Get current workflow status and ready tasks."""
        try:
            workflow = self.active_workflows.get(workflow_instance_id)
            if not workflow:
                workflow = await self._restore_workflow(workflow_instance_id)
                if not workflow:
                    return {"status": "not_found", "message": "Workflow instance not found"}
            
            ready_tasks = workflow.get_ready_user_tasks()
            completed_tasks = [task for task in workflow.get_tasks() if task.state == task.COMPLETED]
            
            return {
                "status": "completed" if workflow.is_completed() else "running",
                "is_completed": workflow.is_completed(),
                "ready_tasks": [
                    {
                        "id": task.id,
                        "name": task.task_spec.name,
                        "description": getattr(task.task_spec, 'description', ''),
                        "data": task.data
                    }
                    for task in ready_tasks
                ],
                "completed_tasks": [
                    {
                        "id": task.id,
                        "name": task.task_spec.name,
                        "completed_at": task.last_state_change
                    }
                    for task in completed_tasks
                ],
                "workflow_data": workflow.data
            }
            
        except Exception as e:
            await self._log_workflow_error(workflow_instance_id, str(e))
            return {"status": "error", "message": str(e)}
    
    async def _create_workflow_instance(
        self,
        name: str,
        description: str,
        bpmn_xml: str,
        input_data: Dict[str, Any],
        created_by: str
    ) -> Dict[str, Any]:
        """Create workflow instance via workflow instance service."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.workflow_instance_service_url}/instances",
                json={
                    "name": name,
                    "description": description,
                    "workflow_definition_id": str(uuid.uuid4()),
                    "bpmn_xml": bpmn_xml,
                    "input_data": input_data,
                    "created_by": created_by
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def _create_spiff_workflow(self, bpmn_xml: str, input_data: Dict[str, Any]) -> BpmnWorkflow:
        """Create SpiffWorkflow instance from BPMN XML."""
        try:
            # Parse BPMN XML
            parser = BpmnParser()
            parser.add_bpmn_xml(bpmn_xml)
            
            # Create workflow
            workflow = BpmnWorkflow(parser.get_spec())
            
            # Set initial data
            workflow.data.update(input_data)
            
            return workflow
            
        except Exception as e:
            raise WorkflowException(f"Failed to create SpiffWorkflow: {str(e)}")
    
    async def _execute_workflow_steps(
        self,
        workflow_instance_id: str,
        workflow: BpmnWorkflow
    ) -> Dict[str, Any]:
        """Execute workflow steps until user input is required."""
        try:
            executed_tasks = []
            
            while not workflow.is_completed():
                # Get ready tasks
                ready_tasks = workflow.get_ready_user_tasks()
                
                if ready_tasks:
                    # User tasks require external input, stop execution
                    await self._log_workflow_event(
                        workflow_instance_id,
                        "INFO",
                        f"Workflow paused for user tasks: {[task.task_spec.name for task in ready_tasks]}"
                    )
                    break
                
                # Execute automatic tasks
                automatic_tasks = [task for task in workflow.get_tasks() if task.state == task.READY]
                
                if not automatic_tasks:
                    break
                
                for task in automatic_tasks:
                    try:
                        # Execute task
                        workflow.complete_task_from_id(task.id)
                        executed_tasks.append({
                            "id": task.id,
                            "name": task.task_spec.name,
                            "type": task.task_spec.__class__.__name__,
                            "completed_at": datetime.utcnow().isoformat()
                        })
                        
                        # Update step status
                        await self._update_step_status(
                            workflow_instance_id,
                            task.id,
                            "completed",
                            task.data
                        )
                        
                    except Exception as task_error:
                        # Handle task execution error
                        await self._handle_task_error(
                            workflow_instance_id, task, str(task_error)
                        )
                        raise WorkflowException(f"Task execution failed: {str(task_error)}")
            
            # Save workflow state
            await self._save_workflow_state(workflow_instance_id, workflow)
            
            # Check if workflow is completed
            if workflow.is_completed():
                await self._update_workflow_instance_status(
                    workflow_instance_id, "completed", "system"
                )
                await self._log_workflow_event(
                    workflow_instance_id, "INFO", "Workflow completed successfully"
                )
            
            return {
                "executed_tasks": executed_tasks,
                "is_completed": workflow.is_completed(),
                "ready_user_tasks": [
                    {
                        "id": task.id,
                        "name": task.task_spec.name,
                        "description": getattr(task.task_spec, 'description', '')
                    }
                    for task in workflow.get_ready_user_tasks()
                ]
            }
            
        except Exception as e:
            await self._handle_workflow_error(workflow_instance_id, str(e))
            raise
    
    async def _update_step_status(
        self,
        workflow_instance_id: str,
        step_id: str,
        status: str,
        output_data: Optional[Dict[str, Any]] = None
    ):
        """Update step status via workflow instance service."""
        try:
            async with httpx.AsyncClient() as client:
                await client.put(
                    f"{self.workflow_instance_service_url}/instances/{workflow_instance_id}/steps/{step_id}/status",
                    params={"status": status},
                    json={
                        "output_data": output_data,
                        "error_message": None
                    }
                )
        except Exception as e:
            # Log error but don't fail workflow execution
            await self._log_workflow_error(workflow_instance_id, f"Failed to update step status: {str(e)}")
    
    async def _update_workflow_instance_status(
        self,
        workflow_instance_id: str,
        status: str,
        updated_by: str
    ):
        """Update workflow instance status via workflow instance service."""
        try:
            async with httpx.AsyncClient() as client:
                await client.put(
                    f"{self.workflow_instance_service_url}/instances/{workflow_instance_id}",
                    json={
                        "status": status,
                        "updated_by": updated_by,
                        "completed_at": datetime.utcnow().isoformat() if status in ["completed", "failed", "cancelled"] else None
                    }
                )
        except Exception as e:
            await self._log_workflow_error(workflow_instance_id, f"Failed to update workflow status: {str(e)}")
    
    async def _log_workflow_event(
        self,
        workflow_instance_id: str,
        level: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Log workflow event."""
        # Store in local database for now
        log_entry = {
            "workflow_instance_id": workflow_instance_id,
            "timestamp": datetime.utcnow(),
            "level": level,
            "message": message,
            "data": data or {}
        }
        
        try:
            await self.db.workflow_logs.insert_one(log_entry)
        except Exception as e:
            print(f"Failed to log workflow event: {str(e)}")
    
    async def _log_workflow_error(self, workflow_instance_id: Optional[str], error_message: str):
        """Log workflow error."""
        if workflow_instance_id:
            await self._log_workflow_event(workflow_instance_id, "ERROR", error_message)
            await self._update_workflow_instance_status(workflow_instance_id, "failed", "system")
    
    async def _handle_task_error(self, workflow_instance_id: str, task, error_message: str):
        """Handle task execution error."""
        await self._update_step_status(
            workflow_instance_id,
            task.id,
            "failed",
            None
        )
        
        await self._log_workflow_event(
            workflow_instance_id,
            "ERROR",
            f"Task '{task.task_spec.name}' failed: {error_message}",
            {"task_id": task.id, "task_name": task.task_spec.name}
        )
    
    async def _handle_workflow_error(self, workflow_instance_id: str, error_message: str):
        """Handle workflow execution error."""
        await self._update_workflow_instance_status(workflow_instance_id, "failed", "system")
        await self._log_workflow_event(workflow_instance_id, "ERROR", f"Workflow execution failed: {error_message}")
    
    async def _save_workflow_state(self, workflow_instance_id: str, workflow: BpmnWorkflow):
        """Save workflow state to database."""
        try:
            serializer = BpmnSerializer()
            workflow_state = serializer.serialize_workflow(workflow)
            
            await self.db.workflow_states.update_one(
                {"workflow_instance_id": workflow_instance_id},
                {
                    "$set": {
                        "workflow_instance_id": workflow_instance_id,
                        "state": workflow_state,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
        except Exception as e:
            await self._log_workflow_error(workflow_instance_id, f"Failed to save workflow state: {str(e)}")
    
    async def _restore_workflow(self, workflow_instance_id: str) -> Optional[BpmnWorkflow]:
        """Restore workflow from saved state."""
        try:
            state_doc = await self.db.workflow_states.find_one(
                {"workflow_instance_id": workflow_instance_id}
            )
            
            if not state_doc:
                return None
            
            serializer = BpmnSerializer()
            workflow = serializer.deserialize_workflow(state_doc["state"])
            
            # Add back to active workflows
            self.active_workflows[workflow_instance_id] = workflow
            
            return workflow
            
        except Exception as e:
            await self._log_workflow_error(workflow_instance_id, f"Failed to restore workflow: {str(e)}")
            return None
