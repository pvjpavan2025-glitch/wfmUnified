"""
Enhanced BPMN processor with SpiffWorkflow integration
"""
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.bpmn.parser.BpmnParser import BpmnParser
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer
from SpiffWorkflow.task import Task
from SpiffWorkflow.exceptions import WorkflowException

from ..models.workflow import WorkflowInstance
from ..models.task import TaskInstance
from ..core.database import get_db


class BpmnProcessor:
    """Enhanced BPMN processor with advanced features support"""
    
    def __init__(self):
        self.parser = BpmnParser()
        self.serializer = BpmnWorkflowSerializer()
        self.active_workflows: Dict[str, BpmnWorkflow] = {}
    
    async def parse_bpmn(self, bpmn_xml: str) -> Dict[str, Any]:
        """Parse BPMN XML and extract process information"""
        try:
            # Parse the BPMN file
            workflow_spec = self.parser.parse_string(bpmn_xml)
            
            # Extract process information
            process_info = {
                "id": workflow_spec.name,
                "name": workflow_spec.description or workflow_spec.name,
                "tasks": [],
                "gateways": [],
                "events": [],
                "flows": [],
                "transaction_boundaries": [],
                "properties": {}
            }
            
            # Analyze tasks and their properties
            for task_spec in workflow_spec.task_specs.values():
                task_info = self._extract_task_info(task_spec)
                
                if task_info["type"] in ["ServiceTask", "UserTask", "ScriptTask", "BusinessRuleTask"]:
                    process_info["tasks"].append(task_info)
                elif task_info["type"] in ["ExclusiveGateway", "ParallelGateway", "InclusiveGateway"]:
                    process_info["gateways"].append(task_info)
                elif task_info["type"] in ["StartEvent", "EndEvent", "IntermediateEvent"]:
                    process_info["events"].append(task_info)
                
                # Check for transaction boundaries
                if self._is_transaction_boundary(task_spec):
                    process_info["transaction_boundaries"].append({
                        "task_id": task_info["id"],
                        "type": self._get_transaction_type(task_spec),
                        "properties": task_info.get("properties", {})
                    })
            
            return process_info
            
        except Exception as e:
            raise WorkflowException(f"Failed to parse BPMN: {str(e)}")
    
    def _extract_task_info(self, task_spec) -> Dict[str, Any]:
        """Extract detailed task information including custom properties"""
        task_info = {
            "id": task_spec.name,
            "type": task_spec.__class__.__name__,
            "name": getattr(task_spec, 'description', task_spec.name),
            "properties": {}
        }
        
        # Extract task-specific properties
        if hasattr(task_spec, 'extensions'):
            for extension in task_spec.extensions:
                if hasattr(extension, 'name') and hasattr(extension, 'value'):
                    task_info["properties"][extension.name] = extension.value
        
        # Service Task properties
        if task_spec.__class__.__name__ == "ServiceTask":
            task_info["properties"].update({
                "implementation": getattr(task_spec, 'implementation', 'webService'),
                "topic": getattr(task_spec, 'topic', ''),
                "async_before": getattr(task_spec, 'async_before', False),
                "async_after": getattr(task_spec, 'async_after', False)
            })
        
        # User Task properties
        elif task_spec.__class__.__name__ == "UserTask":
            task_info["properties"].update({
                "assignee": getattr(task_spec, 'assignee', ''),
                "candidate_users": getattr(task_spec, 'candidate_users', ''),
                "candidate_groups": getattr(task_spec, 'candidate_groups', ''),
                "due_date": getattr(task_spec, 'due_date', ''),
                "priority": getattr(task_spec, 'priority', '')
            })
        
        # Script Task properties
        elif task_spec.__class__.__name__ == "ScriptTask":
            task_info["properties"].update({
                "script_format": getattr(task_spec, 'script_format', 'javascript'),
                "script": getattr(task_spec, 'script', ''),
                "result_variable": getattr(task_spec, 'result_variable', '')
            })
        
        # Business Rule Task properties
        elif task_spec.__class__.__name__ == "BusinessRuleTask":
            task_info["properties"].update({
                "decision_ref": getattr(task_spec, 'decision_ref', ''),
                "decision_ref_binding": getattr(task_spec, 'decision_ref_binding', 'latest')
            })
        
        return task_info
    
    def _is_transaction_boundary(self, task_spec) -> bool:
        """Check if task represents a transaction boundary"""
        # Transaction boundaries include:
        # - Tasks with async before/after
        # - Service tasks with external implementation
        # - Call activities
        # - Subprocesses
        
        if hasattr(task_spec, 'async_before') and task_spec.async_before:
            return True
        
        if hasattr(task_spec, 'async_after') and task_spec.async_after:
            return True
        
        if (task_spec.__class__.__name__ == "ServiceTask" and 
            getattr(task_spec, 'implementation', '') == 'external'):
            return True
        
        if task_spec.__class__.__name__ in ["CallActivity", "SubProcess"]:
            return True
        
        return False
    
    def _get_transaction_type(self, task_spec) -> str:
        """Get the type of transaction boundary"""
        if hasattr(task_spec, 'async_before') and hasattr(task_spec, 'async_after'):
            if task_spec.async_before and task_spec.async_after:
                return 'async_both'
            elif task_spec.async_before:
                return 'async_before'
            elif task_spec.async_after:
                return 'async_after'
        
        if task_spec.__class__.__name__ == "CallActivity":
            return 'call_activity'
        
        if (task_spec.__class__.__name__ == "ServiceTask" and 
            getattr(task_spec, 'implementation', '') == 'external'):
            return 'external_task'
        
        if task_spec.__class__.__name__ == "SubProcess":
            return 'subprocess'
        
        return 'default'
    
    async def create_workflow_instance(self, bpmn_xml: str, variables: Dict[str, Any] = None) -> str:
        """Create a new workflow instance"""
        try:
            # Parse BPMN and create workflow spec
            workflow_spec = self.parser.parse_string(bpmn_xml)
            
            # Create workflow instance
            workflow = BpmnWorkflow(workflow_spec)
            
            # Set initial variables
            if variables:
                for key, value in variables.items():
                    workflow.data[key] = value
            
            # Generate instance ID
            instance_id = str(uuid.uuid4())
            
            # Store workflow in memory (in production, use persistent storage)
            self.active_workflows[instance_id] = workflow
            
            # Save to database
            async with get_db_session() as session:
                db_instance = WorkflowInstance(
                    id=instance_id,
                    bpmn_xml=bpmn_xml,
                    status="READY",
                    variables=json.dumps(variables or {}),
                    created_at=datetime.utcnow()
                )
                session.add(db_instance)
                await session.commit()
            
            return instance_id
            
        except Exception as e:
            raise WorkflowException(f"Failed to create workflow instance: {str(e)}")
    
    async def execute_workflow(self, instance_id: str) -> Dict[str, Any]:
        """Execute workflow instance"""
        try:
            workflow = self.active_workflows.get(instance_id)
            if not workflow:
                # Load from database if not in memory
                workflow = await self._load_workflow_from_db(instance_id)
            
            if not workflow:
                raise WorkflowException(f"Workflow instance {instance_id} not found")
            
            # Execute workflow
            execution_log = []
            
            while not workflow.is_completed():
                ready_tasks = workflow.get_ready_user_tasks()
                
                if not ready_tasks:
                    # No ready user tasks, try to complete system tasks
                    ready_tasks = [task for task in workflow.get_tasks() 
                                 if task.state == Task.READY and not task.task_spec.manual]
                
                if not ready_tasks:
                    break
                
                for task in ready_tasks:
                    # Log task execution
                    execution_log.append({
                        "task_id": task.task_spec.name,
                        "task_name": task.task_spec.description or task.task_spec.name,
                        "task_type": task.task_spec.__class__.__name__,
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": dict(task.data)
                    })
                    
                    # Execute task based on type
                    await self._execute_task(task, instance_id)
                    
                    # Complete the task
                    workflow.complete_task_from_id(task.id)
            
            # Update workflow status
            status = "COMPLETED" if workflow.is_completed() else "RUNNING"
            
            # Update database
            async with get_db_session() as session:
                db_instance = await session.get(WorkflowInstance, instance_id)
                if db_instance:
                    db_instance.status = status
                    db_instance.variables = json.dumps(dict(workflow.data))
                    db_instance.updated_at = datetime.utcnow()
                    await session.commit()
            
            return {
                "instance_id": instance_id,
                "status": status,
                "execution_log": execution_log,
                "variables": dict(workflow.data),
                "completed": workflow.is_completed()
            }
            
        except Exception as e:
            raise WorkflowException(f"Failed to execute workflow: {str(e)}")
    
    async def _execute_task(self, task: Task, instance_id: str):
        """Execute individual task based on its type"""
        task_type = task.task_spec.__class__.__name__
        
        # Save task instance to database
        async with get_db_session() as session:
            db_task = TaskInstance(
                id=str(uuid.uuid4()),
                workflow_instance_id=instance_id,
                task_id=task.task_spec.name,
                task_name=task.task_spec.description or task.task_spec.name,
                task_type=task_type,
                status="RUNNING",
                variables=json.dumps(dict(task.data)),
                created_at=datetime.utcnow()
            )
            session.add(db_task)
            await session.commit()
            
            # Update task status to completed
            db_task.status = "COMPLETED"
            db_task.completed_at = datetime.utcnow()
            await session.commit()
    
    async def _load_workflow_from_db(self, instance_id: str) -> Optional[BpmnWorkflow]:
        """Load workflow instance from database"""
        try:
            async with get_db_session() as session:
                db_instance = await session.get(WorkflowInstance, instance_id)
                if not db_instance:
                    return None
                
                # Recreate workflow from BPMN XML
                workflow_spec = self.parser.parse_string(db_instance.bpmn_xml)
                workflow = BpmnWorkflow(workflow_spec)
                
                # Restore variables
                if db_instance.variables:
                    variables = json.loads(db_instance.variables)
                    for key, value in variables.items():
                        workflow.data[key] = value
                
                # Store in memory
                self.active_workflows[instance_id] = workflow
                
                return workflow
                
        except Exception as e:
            raise WorkflowException(f"Failed to load workflow from database: {str(e)}")
    
    async def get_workflow_status(self, instance_id: str) -> Dict[str, Any]:
        """Get current workflow status"""
        try:
            async with get_db_session() as session:
                db_instance = await session.get(WorkflowInstance, instance_id)
                if not db_instance:
                    raise WorkflowException(f"Workflow instance {instance_id} not found")
                
                # Get task instances
                task_instances = await session.execute(
                    "SELECT * FROM task_instances WHERE workflow_instance_id = :id",
                    {"id": instance_id}
                )
                
                return {
                    "instance_id": instance_id,
                    "status": db_instance.status,
                    "variables": json.loads(db_instance.variables or "{}"),
                    "created_at": db_instance.created_at.isoformat(),
                    "updated_at": db_instance.updated_at.isoformat() if db_instance.updated_at else None,
                    "tasks": [
                        {
                            "id": task.id,
                            "name": task.task_name,
                            "type": task.task_type,
                            "status": task.status,
                            "created_at": task.created_at.isoformat(),
                            "completed_at": task.completed_at.isoformat() if task.completed_at else None
                        }
                        for task in task_instances
                    ]
                }
                
        except Exception as e:
            raise WorkflowException(f"Failed to get workflow status: {str(e)}")
    
    async def validate_bpmn(self, bpmn_xml: str) -> Dict[str, Any]:
        """Validate BPMN XML and return validation results"""
        try:
            # Parse BPMN to validate structure
            workflow_spec = self.parser.parse_string(bpmn_xml)
            
            validation_results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "process_info": {
                    "id": workflow_spec.name,
                    "name": workflow_spec.description or workflow_spec.name,
                    "task_count": len([spec for spec in workflow_spec.task_specs.values() 
                                    if spec.__class__.__name__ in ["ServiceTask", "UserTask", "ScriptTask"]]),
                    "gateway_count": len([spec for spec in workflow_spec.task_specs.values() 
                                        if "Gateway" in spec.__class__.__name__]),
                    "event_count": len([spec for spec in workflow_spec.task_specs.values() 
                                      if "Event" in spec.__class__.__name__])
                }
            }
            
            # Additional validation checks
            start_events = [spec for spec in workflow_spec.task_specs.values() 
                          if spec.__class__.__name__ == "StartEvent"]
            end_events = [spec for spec in workflow_spec.task_specs.values() 
                        if spec.__class__.__name__ == "EndEvent"]
            
            if not start_events:
                validation_results["warnings"].append("No start event found")
            
            if not end_events:
                validation_results["warnings"].append("No end event found")
            
            if len(start_events) > 1:
                validation_results["warnings"].append("Multiple start events found")
            
            return validation_results
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "process_info": None
            }
