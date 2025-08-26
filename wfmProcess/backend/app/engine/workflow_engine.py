"""Main workflow execution engine."""

import uuid
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import networkx as nx

from ..models.workflow import WorkflowDefinition, WorkflowInstance
from ..models.task import TaskDefinition, TaskInstance, TaskStatus, TaskType
from ..models.execution import ExecutionLog, ExecutionState, LogLevel
from ..core.redis_client import redis_client
from .bpmn_parser import BpmnParser
from .script_engine import ScriptEngine, ScriptExecutionError
from ..core.config import settings


class WorkflowExecutionError(Exception):
    """Exception raised during workflow execution."""
    pass


class WorkflowEngine:
    """Main BPMN workflow execution engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bpmn_parser = BpmnParser()
        self.script_engine = ScriptEngine()
        self.active_instances: Dict[str, WorkflowInstance] = {}
        self.execution_graphs: Dict[str, nx.DiGraph] = {}
    
    async def create_workflow_definition(
        self, 
        bpmn_xml: str, 
        name: str, 
        version: str = "1.0.0"
    ) -> WorkflowDefinition:
        """Create a new workflow definition from BPMN XML."""
        try:
            # Parse BPMN XML
            workflow_def = self.bpmn_parser.parse_bpmn_xml(bpmn_xml, name, version)
            
            # Build execution graph
            execution_graph = self._build_execution_graph(workflow_def)
            self.execution_graphs[workflow_def.bpmn_id] = execution_graph
            
            self.logger.info(f"Created workflow definition: {name} v{version}")
            return workflow_def
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow definition: {e}")
            raise WorkflowExecutionError(f"Failed to create workflow definition: {str(e)}")
    
    async def start_workflow(
        self, 
        workflow_definition: WorkflowDefinition, 
        input_data: Optional[Dict[str, Any]] = None,
        instance_id: Optional[str] = None
    ) -> WorkflowInstance:
        """Start a new workflow instance."""
        try:
            # Generate instance ID if not provided
            if not instance_id:
                instance_id = f"{workflow_definition.name}_{uuid.uuid4().hex[:8]}"
            
            # Create workflow instance
            workflow_instance = WorkflowInstance(
                instance_id=instance_id,
                workflow_definition_id=workflow_definition.id,
                input_data=input_data or {},
                current_state=self._get_initial_state(workflow_definition),
                status="running"
            )
            
            # Store instance
            self.active_instances[instance_id] = workflow_instance
            
            # Create initial task instances
            await self._create_initial_tasks(workflow_instance)
            
            # Start execution
            asyncio.create_task(self._execute_workflow(workflow_instance))
            
            self.logger.info(f"Started workflow instance: {instance_id}")
            return workflow_instance
            
        except Exception as e:
            self.logger.error(f"Failed to start workflow: {e}")
            raise WorkflowExecutionError(f"Failed to start workflow: {str(e)}")
    
    async def _execute_workflow(self, workflow_instance: WorkflowInstance) -> None:
        """Execute workflow instance."""
        try:
            while workflow_instance.status == "running":
                # Get ready tasks
                ready_tasks = await self._get_ready_tasks(workflow_instance)
                
                if not ready_tasks:
                    # No ready tasks, check if workflow is complete
                    if await self._is_workflow_complete(workflow_instance):
                        workflow_instance.status = "completed"
                        workflow_instance.completed_at = datetime.utcnow()
                        break
                    else:
                        # Wait for events or timeouts
                        await asyncio.sleep(1)
                        continue
                
                # Execute ready tasks
                execution_tasks = []
                for task_instance in ready_tasks:
                    execution_task = asyncio.create_task(
                        self._execute_task(task_instance)
                    )
                    execution_tasks.append(execution_task)
                
                # Wait for all tasks to complete
                if execution_tasks:
                    await asyncio.gather(*execution_tasks, return_exceptions=True)
                
                # Update workflow state
                await self._update_workflow_state(workflow_instance)
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
            
            self.logger.info(f"Workflow instance {workflow_instance.instance_id} completed with status: {workflow_instance.status}")
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            workflow_instance.status = "failed"
            await self._log_execution_error(workflow_instance, str(e))
    
    async def _execute_task(self, task_instance: TaskInstance) -> None:
        """Execute a single task."""
        try:
            task_instance.status = TaskStatus.RUNNING
            task_instance.started_at = datetime.utcnow()
            
            # Log task start
            await self._log_execution_info(
                task_instance.workflow_instance,
                f"Started task: {task_instance.task_definition.name}",
                task_instance=task_instance
            )
            
            # Execute task based on type
            result = await self._execute_task_by_type(task_instance)
            
            # Mark task as completed
            task_instance.status = TaskStatus.COMPLETED
            task_instance.completed_at = datetime.utcnow()
            
            # Log task completion
            await self._log_execution_info(
                task_instance.workflow_instance,
                f"Completed task: {task_instance.task_definition.name}",
                task_instance=task_instance
            )
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            task_instance.status = TaskStatus.FAILED
            
            # Handle retries
            if task_instance.retry_count < task_instance.max_retries:
                task_instance.retry_count += 1
                task_instance.status = TaskStatus.PENDING
                self.logger.info(f"Retrying task {task_instance.instance_id}, attempt {task_instance.retry_count}")
            else:
                await self._log_execution_error(
                    task_instance.workflow_instance,
                    f"Task {task_instance.task_definition.name} failed after {task_instance.max_retries} retries: {str(e)}",
                    task_instance=task_instance
                )
    
    async def _execute_task_by_type(self, task_instance: TaskInstance) -> Any:
        """Execute task based on its type."""
        task_def = task_instance.task_definition
        
        if task_def.task_type == TaskType.SCRIPT_TASK:
            if task_def.script:
                return await self.script_engine.execute_script(
                    task_instance, 
                    task_def.script,
                    context=task_instance.workflow_instance.current_state
                )
        
        elif task_def.task_type == TaskType.SERVICE_TASK:
            if task_def.service_url:
                return await self._execute_service_task(task_instance)
        
        elif task_def.task_type == TaskType.USER_TASK:
            # User tasks require human interaction
            # In a real implementation, this would create a task for a user
            return {"status": "waiting_for_user"}
        
        elif task_def.task_type == TaskType.MANUAL_TASK:
            # Manual tasks require human intervention
            return {"status": "waiting_for_manual_completion"}
        
        elif task_def.task_type in [TaskType.EXCLUSIVE_GATEWAY, TaskType.INCLUSIVE_GATEWAY]:
            return await self._evaluate_gateway(task_instance)
        
        elif task_def.task_type == TaskType.PARALLEL_GATEWAY:
            # Parallel gateways just pass through
            return {"status": "parallel_gateway_passed"}
        
        elif task_def.task_type == TaskType.START_EVENT:
            return {"status": "start_event_triggered"}
        
        elif task_def.task_type == TaskType.END_EVENT:
            return {"status": "end_event_reached"}
        
        # Default: just pass through
        return {"status": "completed"}
    
    async def _execute_service_task(self, task_instance: TaskInstance) -> Dict[str, Any]:
        """Execute a service task by calling external service."""
        # This is a simplified implementation
        # In a real system, you'd use httpx or similar to make HTTP calls
        task_def = task_instance.task_definition
        
        # Simulate service call
        await asyncio.sleep(0.1)  # Simulate network delay
        
        return {
            "service_url": task_def.service_url,
            "method": task_def.service_method or "POST",
            "status": "service_called",
            "result": f"Service {task_def.service_url} executed successfully"
        }
    
    async def _evaluate_gateway(self, task_instance: TaskInstance) -> Dict[str, Any]:
        """Evaluate gateway conditions and determine next flow."""
        task_def = task_instance.task_definition
        
        if task_def.task_type == TaskType.EXCLUSIVE_GATEWAY:
            # Evaluate conditions on outgoing flows
            next_flow = await self._evaluate_exclusive_gateway(task_instance)
            return {"next_flow": next_flow, "gateway_type": "exclusive"}
        
        elif task_def.task_type == TaskType.INCLUSIVE_GATEWAY:
            # Evaluate conditions on outgoing flows (multiple can be true)
            next_flows = await self._evaluate_inclusive_gateway(task_instance)
            return {"next_flows": next_flows, "gateway_type": "inclusive"}
        
        return {"status": "gateway_evaluated"}
    
    async def _evaluate_exclusive_gateway(self, task_instance: TaskInstance) -> Optional[str]:
        """Evaluate exclusive gateway conditions."""
        task_def = task_instance.task_definition
        
        # Check if there's a default flow
        if task_def.default_flow:
            return task_def.default_flow
        
        # Evaluate conditions on outgoing flows
        # This is a simplified implementation
        # In a real system, you'd parse and evaluate BPMN conditional expressions
        
        return None
    
    async def _evaluate_inclusive_gateway(self, task_instance: TaskInstance) -> List[str]:
        """Evaluate inclusive gateway conditions."""
        # Similar to exclusive gateway but multiple flows can be true
        # This is a simplified implementation
        return []
    
    def _build_execution_graph(self, workflow_def: WorkflowDefinition) -> nx.DiGraph:
        """Build execution graph from workflow definition."""
        graph = nx.DiGraph()
        
        # Add nodes (tasks)
        for task_def in workflow_def.task_definitions:
            graph.add_node(task_def.bpmn_id, task_def=task_def)
        
        # Add edges (flows)
        for task_def in workflow_def.task_definitions:
            for outgoing_flow in task_def.outgoing_flows:
                # Find target task
                target_task = self._find_task_by_flow(workflow_def, outgoing_flow)
                if target_task:
                    graph.add_edge(task_def.bpmn_id, target_task.bpmn_id, flow_id=outgoing_flow)
        
        return graph
    
    def _find_task_by_flow(self, workflow_def: WorkflowDefinition, flow_id: str) -> Optional[TaskDefinition]:
        """Find task definition by flow ID."""
        for task_def in workflow_def.task_definitions:
            if flow_id in task_def.incoming_flows:
                return task_def
        return None
    
    def _get_initial_state(self, workflow_def: WorkflowDefinition) -> Dict[str, Any]:
        """Get initial workflow state."""
        return {
            "workflow_name": workflow_def.name,
            "workflow_version": workflow_def.version,
            "start_time": datetime.utcnow().isoformat(),
            "variables": {},
            "execution_path": []
        }
    
    async def _create_initial_tasks(self, workflow_instance: WorkflowInstance) -> None:
        """Create initial task instances for workflow."""
        workflow_def = workflow_instance.definition
        
        # Find start events
        start_tasks = [
            td for td in workflow_def.task_definitions 
            if td.task_type == TaskType.START_EVENT
        ]
        
        for start_task in start_tasks:
            task_instance = TaskInstance(
                instance_id=f"{workflow_instance.instance_id}_{start_task.bpmn_id}",
                workflow_instance_id=workflow_instance.id,
                task_definition_id=start_task.id,
                status=TaskStatus.READY
            )
            workflow_instance.task_instances.append(task_instance)
    
    async def _get_ready_tasks(self, workflow_instance: WorkflowInstance) -> List[TaskInstance]:
        """Get tasks that are ready for execution."""
        ready_tasks = []
        
        for task_instance in workflow_instance.task_instances:
            if task_instance.status == TaskStatus.READY:
                # Check if all incoming flows are satisfied
                if await self._are_incoming_flows_satisfied(task_instance):
                    ready_tasks.append(task_instance)
        
        return ready_tasks
    
    async def _are_incoming_flows_satisfied(self, task_instance: TaskInstance) -> bool:
        """Check if all incoming flows for a task are satisfied."""
        task_def = task_instance.task_definition
        
        if not task_def.incoming_flows:
            return True  # Start event or no incoming flows
        
        # Check if all incoming tasks are completed
        for flow_id in task_def.incoming_flows:
            source_task = self._find_source_task_by_flow(task_instance.workflow_instance, flow_id)
            if source_task and source_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def _find_source_task_by_flow(self, workflow_instance: WorkflowInstance, flow_id: str) -> Optional[TaskInstance]:
        """Find source task instance by flow ID."""
        for task_instance in workflow_instance.task_instances:
            if flow_id in task_instance.task_definition.outgoing_flows:
                return task_instance
        return None
    
    async def _is_workflow_complete(self, workflow_instance: WorkflowInstance) -> bool:
        """Check if workflow is complete."""
        # Check if all end events are reached
        end_tasks = [
            ti for ti in workflow_instance.task_instances
            if ti.task_definition.task_type == TaskType.END_EVENT
        ]
        
        return all(ti.status == TaskStatus.COMPLETED for ti in end_tasks)
    
    async def _update_workflow_state(self, workflow_instance: WorkflowInstance) -> None:
        """Update workflow execution state."""
        # Create execution state snapshot
        execution_state = ExecutionState(
            workflow_instance_id=workflow_instance.id,
            state_data=workflow_instance.current_state,
            variables=workflow_instance.current_state.get("variables", {}),
            current_tasks=[ti.instance_id for ti in workflow_instance.task_instances if ti.status == TaskStatus.RUNNING],
            completed_tasks=[ti.instance_id for ti in workflow_instance.task_instances if ti.status == TaskStatus.COMPLETED],
            pending_tasks=[ti.instance_id for ti in workflow_instance.task_instances if ti.status == TaskStatus.PENDING],
            active_tokens=[],  # Simplified for now
            flow_control={}    # Simplified for now
        )
        
        workflow_instance.execution_states.append(execution_state)
    
    async def _log_execution_info(
        self, 
        workflow_instance: WorkflowInstance, 
        message: str, 
        task_instance: Optional[TaskInstance] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log execution information."""
        execution_log = ExecutionLog(
            workflow_instance_id=workflow_instance.id,
            task_instance_id=task_instance.id if task_instance else None,
            level=LogLevel.INFO,
            message=message,
            details=details,
            step_name=task_instance.task_definition.name if task_instance else None,
            execution_path=workflow_instance.current_state.get("execution_path", [])
        )
        
        workflow_instance.execution_logs.append(execution_log)
    
    async def _log_execution_error(
        self, 
        workflow_instance: WorkflowInstance, 
        message: str, 
        task_instance: Optional[TaskInstance] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log execution error."""
        execution_log = ExecutionLog(
            workflow_instance_id=workflow_instance.id,
            task_instance_id=task_instance.id if task_instance else None,
            level=LogLevel.ERROR,
            message=message,
            details=details,
            step_name=task_instance.task_definition.name if task_instance else None,
            execution_path=workflow_instance.current_state.get("execution_path", [])
        )
        
        workflow_instance.execution_logs.append(execution_log)
    
    async def get_workflow_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow instance status."""
        if instance_id not in self.active_instances:
            return None
        
        workflow_instance = self.active_instances[instance_id]
        
        return {
            "instance_id": workflow_instance.instance_id,
            "status": workflow_instance.status,
            "started_at": workflow_instance.started_at,
            "completed_at": workflow_instance.completed_at,
            "current_tasks": [
                {
                    "task_id": ti.instance_id,
                    "name": ti.task_definition.name,
                    "status": ti.status.value,
                    "started_at": ti.started_at,
                    "completed_at": ti.completed_at
                }
                for ti in workflow_instance.task_instances
            ],
            "execution_logs": [
                {
                    "level": log.level.value,
                    "message": log.message,
                    "timestamp": log.created_at,
                    "task": log.task_instance_id
                }
                for log in workflow_instance.execution_logs[-10:]  # Last 10 logs
            ]
        }
    
    async def stop_workflow(self, instance_id: str) -> bool:
        """Stop a running workflow instance."""
        if instance_id not in self.active_instances:
            return False
        
        workflow_instance = self.active_instances[instance_id]
        workflow_instance.status = "stopped"
        
        # Stop all running tasks
        for task_instance in workflow_instance.task_instances:
            if task_instance.status == TaskStatus.RUNNING:
                task_instance.status = TaskStatus.CANCELLED
        
        self.logger.info(f"Stopped workflow instance: {instance_id}")
        return True
