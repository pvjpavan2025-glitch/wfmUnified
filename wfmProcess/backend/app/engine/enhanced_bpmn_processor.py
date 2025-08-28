"""
Enhanced BPMN processor with MongoDB integration for process management
"""
import json
import uuid
import asyncio
import logging
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
from ..models.process_models import Process, ProcessCreate, ProcessInstance, ProcessInstanceCreate
from ..services.process_service import ProcessService
from ..core.database import get_db
from ..core.mongodb import get_mongodb_database


class EnhancedBpmnProcessor:
    """Enhanced BPMN processor with MongoDB integration for process management"""
    
    def __init__(self):
        self.parser = BpmnParser()
        self.serializer = BpmnWorkflowSerializer()
        self.active_workflows: Dict[str, BpmnWorkflow] = {}
        self.process_service = ProcessService()
        self.logger = logging.getLogger(__name__)
    
    async def parse_and_save_process(self, bpmn_xml: str, process_data: ProcessCreate) -> Process:
        """Parse BPMN XML, validate it, and save to MongoDB"""
        try:
            # Validate BPMN XML
            validation_result = await self.validate_bpmn(bpmn_xml)
            if not validation_result["valid"]:
                raise WorkflowException(f"Invalid BPMN XML: {validation_result['errors']}")
            
            # Extract process information from BPMN
            process_info = await self._extract_process_info(bpmn_xml)
            
            # Create process document
            process_doc = Process(
                name=process_data.name,
                description=process_data.description,
                bpmn_xml=bpmn_xml,
                process_id=process_info["process_id"],
                version=process_data.version,
                category=process_data.category,
                tags=process_data.tags,
                metadata=process_data.metadata,
                status="active",
                created_by=process_data.created_by,
                tenant_id=process_data.tenant_id,
                **process_info
            )
            
            # Save to MongoDB
            saved_process = await self.process_service.create_process(process_doc)
            
            return saved_process
            
        except Exception as e:
            raise WorkflowException(f"Failed to parse and save process: {str(e)}")
    
    async def _extract_process_info(self, bpmn_xml: str) -> Dict[str, Any]:
        """Extract process information from BPMN XML"""
        try:
            # Parse the BPMN file
            workflow_spec = self.parser.parse_string(bpmn_xml)
            
            # Extract process information
            process_info = {
                "process_id": workflow_spec.name,
                "process_name": workflow_spec.description or workflow_spec.name,
                "task_count": 0,
                "gateway_count": 0,
                "event_count": 0,
                "flow_count": 0,
                "complexity_score": 0,
                "estimated_duration": 0,
                "task_types": [],
                "gateway_types": [],
                "event_types": []
            }
            
            # Analyze tasks and their properties
            for task_spec in workflow_spec.task_specs.values():
                task_info = self._extract_task_info(task_spec)
                
                if task_info["type"] in ["ServiceTask", "UserTask", "ScriptTask", "BusinessRuleTask"]:
                    process_info["task_count"] += 1
                    if task_info["type"] not in process_info["task_types"]:
                        process_info["task_types"].append(task_info["type"])
                elif "Gateway" in task_info["type"]:
                    process_info["gateway_count"] += 1
                    if task_info["type"] not in process_info["gateway_types"]:
                        process_info["gateway_types"].append(task_info["type"])
                elif "Event" in task_info["type"]:
                    process_info["event_count"] += 1
                    if task_info["type"] not in process_info["event_types"]:
                        process_info["event_types"].append(task_info["type"])
            
            # Calculate complexity score
            process_info["complexity_score"] = self._calculate_complexity_score(process_info)
            
            # Estimate duration based on task count and types
            process_info["estimated_duration"] = self._estimate_duration(process_info)
            
            return process_info
            
        except Exception as e:
            raise WorkflowException(f"Failed to extract process info: {str(e)}")
    
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
    
    def _calculate_complexity_score(self, process_info: Dict[str, Any]) -> int:
        """Calculate complexity score based on process characteristics"""
        score = 0
        
        # Base score from task count
        score += process_info["task_count"] * 2
        
        # Add complexity for gateways
        score += process_info["gateway_count"] * 3
        
        # Add complexity for events
        score += process_info["event_count"] * 1
        
        # Bonus complexity for parallel gateways
        if "ParallelGateway" in process_info["gateway_types"]:
            score += 5
        
        # Bonus complexity for inclusive gateways
        if "InclusiveGateway" in process_info["gateway_types"]:
            score += 8
        
        return score
    
    def _estimate_duration(self, process_info: Dict[str, Any]) -> int:
        """Estimate process duration in minutes"""
        # Base duration: 5 minutes per task
        base_duration = process_info["task_count"] * 5
        
        # Add time for gateways (decision making)
        gateway_time = process_info["gateway_count"] * 2
        
        # Add time for events
        event_time = process_info["event_count"] * 1
        
        # Complexity multiplier
        complexity_multiplier = 1 + (process_info["complexity_score"] / 100)
        
        estimated_duration = int((base_duration + gateway_time + event_time) * complexity_multiplier)
        
        return max(estimated_duration, 1)  # Minimum 1 minute
    
    async def create_process_instance(self, process_id: str, input_data: Dict[str, Any] = None) -> ProcessInstance:
        """Create a new process instance from a saved process"""
        try:
            # Get the process from MongoDB
            process = await self.process_service.get_process(process_id)
            if not process:
                raise WorkflowException(f"Process {process_id} not found")
            
            # Create process instance
            instance_data = ProcessInstanceCreate(
                process_id=process_id,
                process_name=process.name,
                process_version=process.version,
                input_data=input_data or {},
                status="running",
                started_by=process.created_by,  # Default to process creator
                tenant_id=process.tenant_id
            )
            
            # Save to MongoDB
            process_instance = await self.process_service.create_process_instance(instance_data)
            
            # Create SpiffWorkflow instance for execution
            workflow_spec = self.parser.parse_string(process.bpmn_xml)
            workflow = BpmnWorkflow(workflow_spec)
            
            # Set initial variables
            if input_data:
                for key, value in input_data.items():
                    workflow.data[key] = value
            
            # Store workflow in memory
            self.active_workflows[process_instance.id] = workflow
            
            return process_instance
            
        except Exception as e:
            raise WorkflowException(f"Failed to create process instance: {str(e)}")
    
    async def execute_process_instance(self, instance_id: str) -> Dict[str, Any]:
        """Execute a process instance"""
        try:
            workflow = self.active_workflows.get(instance_id)
            if not workflow:
                # Load from database if not in memory
                workflow = await self._load_workflow_from_db(instance_id)
            
            if not workflow:
                raise WorkflowException(f"Process instance {instance_id} not found")
            
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
            
            # Update process instance status
            status = "completed" if workflow.is_completed() else "running"
            
            # Update MongoDB
            await self.process_service.update_process_instance(
                instance_id,
                {
                    "status": status,
                    "output_data": dict(workflow.data),
                    "completed_at": datetime.utcnow() if status == "completed" else None
                }
            )
            
            return {
                "instance_id": instance_id,
                "status": status,
                "execution_log": execution_log,
                "output_data": dict(workflow.data),
                "completed": workflow.is_completed()
            }
            
        except Exception as e:
            raise WorkflowException(f"Failed to execute process instance: {str(e)}")
    
    async def _execute_task(self, task: Task, instance_id: str):
        """Execute individual task based on its type"""
        task_type = task.task_spec.__class__.__name__
        
        # Log task execution
        self.logger.info(f"Executing task {task.task_spec.name} of type {task_type}")
        
        # For now, just complete the task
        # In a real implementation, you would handle different task types differently
        if task_type == "ServiceTask":
            # Simulate service call
            await asyncio.sleep(0.1)
        elif task_type == "UserTask":
            # Wait for user input (in real implementation)
            pass
        elif task_type == "ScriptTask":
            # Execute script
            await self._execute_script_task(task)
    
    async def _execute_script_task(self, task: Task):
        """Execute a script task"""
        try:
            script = getattr(task.task_spec, 'script', '')
            script_format = getattr(task.task_spec, 'script_format', 'javascript')
            
            if script_format == 'javascript':
                # Simple JavaScript-like execution (in real implementation, use proper JS engine)
                # For now, just log the script
                self.logger.info(f"Executing script: {script}")
            else:
                self.logger.warning(f"Unsupported script format: {script_format}")
                
        except Exception as e:
            self.logger.error(f"Failed to execute script task: {e}")
    
    async def _load_workflow_from_db(self, instance_id: str) -> Optional[BpmnWorkflow]:
        """Load workflow instance from MongoDB and recreate SpiffWorkflow"""
        try:
            # Get process instance from MongoDB
            process_instance = await self.process_service.get_process_instance(instance_id)
            if not process_instance:
                return None
            
            # Get the process definition
            process = await self.process_service.get_process(process_instance.process_id)
            if not process:
                return None
            
            # Recreate workflow from BPMN XML
            workflow_spec = self.parser.parse_string(process.bpmn_xml)
            workflow = BpmnWorkflow(workflow_spec)
            
            # Restore variables
            if process_instance.input_data:
                for key, value in process_instance.input_data.items():
                    workflow.data[key] = value
            
            # Store in memory
            self.active_workflows[instance_id] = workflow
            
            return workflow
            
        except Exception as e:
            raise WorkflowException(f"Failed to load workflow from database: {str(e)}")
    
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
    
    async def get_process_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get current process instance status"""
        try:
            # Get from MongoDB
            process_instance = await self.process_service.get_process_instance(instance_id)
            if not process_instance:
                raise WorkflowException(f"Process instance {instance_id} not found")
            
            # Get the process definition
            process = await self.process_service.get_process(process_instance.process_id)
            if not process:
                raise WorkflowException(f"Process {process_instance.process_id} not found")
            
            return {
                "instance_id": instance_id,
                "process_name": process.name,
                "process_version": process.version,
                "status": process_instance.status,
                "input_data": process_instance.input_data,
                "output_data": process_instance.output_data,
                "started_at": process_instance.started_at.isoformat(),
                "completed_at": process_instance.completed_at.isoformat() if process_instance.completed_at else None,
                "started_by": process_instance.started_by,
                "tenant_id": process_instance.tenant_id
            }
            
        except Exception as e:
            raise WorkflowException(f"Failed to get process instance status: {str(e)}")
    
    async def list_process_instances(self, process_id: Optional[str] = None, 
                                   status: Optional[str] = None, 
                                   tenant_id: Optional[str] = None) -> List[ProcessInstance]:
        """List process instances with optional filtering"""
        try:
            return await self.process_service.list_process_instances(
                process_id=process_id,
                status=status,
                tenant_id=tenant_id
            )
        except Exception as e:
            raise WorkflowException(f"Failed to list process instances: {str(e)}")
    
    async def delete_process_instance(self, instance_id: str) -> bool:
        """Delete a process instance"""
        try:
            # Remove from memory
            if instance_id in self.active_workflows:
                del self.active_workflows[instance_id]
            
            # Delete from MongoDB
            return await self.process_service.delete_process_instance(instance_id)
            
        except Exception as e:
            raise WorkflowException(f"Failed to delete process instance: {str(e)}")
