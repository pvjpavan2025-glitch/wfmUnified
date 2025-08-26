"""BPMN 2.0 XML parser for workflow definitions."""

import uuid
from typing import Dict, List, Any, Optional, Tuple
from lxml import etree
import xmltodict

from ..models.workflow import WorkflowDefinition
from ..models.task import TaskDefinition, TaskType
from ..core.config import settings


class BpmnParser:
    """BPMN 2.0 XML parser with validation and task extraction."""
    
    def __init__(self):
        self.namespaces = {
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
            'dc': 'http://www.omg.org/spec/DD/20100524/DC',
            'di': 'http://www.omg.org/spec/DD/20100524/DI',
        }
    
    def parse_bpmn_xml(self, bpmn_xml: str, name: str, version: str = "1.0.0") -> WorkflowDefinition:
        """Parse BPMN XML and create workflow definition."""
        try:
            # Parse XML
            root = etree.fromstring(bpmn_xml.encode('utf-8'))
            
            # Validate BPMN structure
            self._validate_bpmn_structure(root)
            
            # Extract process information
            process_info = self._extract_process_info(root)
            
            # Extract tasks
            tasks = self._extract_tasks(root)
            
            # Create workflow definition
            workflow_def = WorkflowDefinition(
                name=name,
                version=version,
                bpmn_xml=bpmn_xml,
                bpmn_id=str(uuid.uuid4()),
                process_id=process_info['process_id'],
                is_executable=process_info['is_executable'],
                config=process_info['config']
            )
            
            # Create task definitions
            task_definitions = []
            for task_data in tasks:
                task_def = TaskDefinition(
                    bpmn_id=task_data['bpmn_id'],
                    name=task_data['name'],
                    task_type=task_data['task_type'],
                    properties=task_data['properties'],
                    incoming_flows=task_data['incoming_flows'],
                    outgoing_flows=task_data['outgoing_flows'],
                    script=task_data.get('script'),
                    script_format=task_data.get('script_format'),
                    service_url=task_data.get('service_url'),
                    service_method=task_data.get('service_method'),
                    gateway_expression=task_data.get('gateway_expression'),
                    default_flow=task_data.get('default_flow'),
                    event_definition=task_data.get('event_definition'),
                    timer_expression=task_data.get('timer_expression'),
                    workflow_definition=workflow_def
                )
                task_definitions.append(task_def)
            
            return workflow_def
            
        except Exception as e:
            raise ValueError(f"Failed to parse BPMN XML: {str(e)}")
    
    def _validate_bpmn_structure(self, root: etree._Element) -> None:
        """Validate basic BPMN structure."""
        if root.tag != f"{{{self.namespaces['bpmn']}}}definitions":
            raise ValueError("Invalid BPMN: Root element must be 'definitions'")
        
        # Check for process element
        process_elements = root.findall(f".//{{{self.namespaces['bpmn']}}}process")
        if not process_elements:
            raise ValueError("Invalid BPMN: No process element found")
        
        # Check for executable process
        for process in process_elements:
            is_executable = process.get('isExecutable', 'false').lower() == 'true'
            if not is_executable:
                raise ValueError(f"Process {process.get('id')} is not executable")
    
    def _extract_process_info(self, root: etree._Element) -> Dict[str, Any]:
        """Extract process information from BPMN."""
        process = root.find(f".//{{{self.namespaces['bpmn']}}}process")
        if process is None:
            raise ValueError("No process element found")
        
        return {
            'process_id': process.get('id', ''),
            'is_executable': process.get('isExecutable', 'false').lower() == 'true',
            'config': {
                'process_name': process.get('name', ''),
                'process_type': process.get('processType', 'None'),
            }
        }
    
    def _extract_tasks(self, root: etree._Element) -> List[Dict[str, Any]]:
        """Extract all tasks from BPMN."""
        tasks = []
        
        # Extract different task types
        task_types = [
            ('startEvent', TaskType.START_EVENT),
            ('endEvent', TaskType.END_EVENT),
            ('intermediateCatchEvent', TaskType.INTERMEDIATE_CATCH_EVENT),
            ('intermediateThrowEvent', TaskType.INTERMEDIATE_THROW_EVENT),
            ('userTask', TaskType.USER_TASK),
            ('manualTask', TaskType.MANUAL_TASK),
            ('scriptTask', TaskType.SCRIPT_TASK),
            ('serviceTask', TaskType.SERVICE_TASK),
            ('callActivity', TaskType.CALL_ACTIVITY),
            ('subprocess', TaskType.SUBPROCESS),
            ('exclusiveGateway', TaskType.EXCLUSIVE_GATEWAY),
            ('inclusiveGateway', TaskType.INCLUSIVE_GATEWAY),
            ('parallelGateway', TaskType.PARALLEL_GATEWAY),
            ('eventBasedGateway', TaskType.EVENT_BASED_GATEWAY),
            ('boundaryEvent', TaskType.BOUNDARY_EVENT),
        ]
        
        for element_name, task_type in task_types:
            elements = root.findall(f".//{{{self.namespaces['bpmn']}}}{element_name}")
            for element in elements:
                task_data = self._extract_task_data(element, task_type)
                if task_data:
                    tasks.append(task_data)
        
        return tasks
    
    def _extract_task_data(self, element: etree._Element, task_type: TaskType) -> Optional[Dict[str, Any]]:
        """Extract task data from BPMN element."""
        try:
            bpmn_id = element.get('id', '')
            name = element.get('name', bpmn_id)
            
            # Extract flows
            incoming_flows = self._extract_flows(element, 'incoming')
            outgoing_flows = self._extract_flows(element, 'outgoing')
            
            # Extract properties
            properties = self._extract_properties(element)
            
            # Extract task-specific data
            task_data = self._extract_task_specific_data(element, task_type)
            
            return {
                'bpmn_id': bpmn_id,
                'name': name,
                'task_type': task_type,
                'properties': properties,
                'incoming_flows': incoming_flows,
                'outgoing_flows': outgoing_flows,
                **task_data
            }
            
        except Exception as e:
            # Log error but continue processing other tasks
            print(f"Warning: Failed to extract task data for {element.tag}: {e}")
            return None
    
    def _extract_flows(self, element: etree._Element, flow_type: str) -> List[str]:
        """Extract incoming or outgoing flows."""
        flows = []
        flow_elements = element.findall(f"{{{self.namespaces['bpmn']}}}{flow_type}")
        for flow in flow_elements:
            flow_id = flow.text.strip()
            if flow_id:
                flows.append(flow_id)
        return flows
    
    def _extract_properties(self, element: etree._Element) -> Dict[str, Any]:
        """Extract general properties from BPMN element."""
        properties = {}
        
        # Extract basic attributes
        for attr_name in ['id', 'name', 'default']:
            attr_value = element.get(attr_name)
            if attr_value:
                properties[attr_name] = attr_value
        
        # Extract extension elements
        extension_elements = element.findall(f".//{{{self.namespaces['bpmn']}}}extensionElements")
        for ext_elem in extension_elements:
            # Extract custom properties
            custom_props = ext_elem.findall(".//*[@name]")
            for prop in custom_props:
                prop_name = prop.get('name')
                prop_value = prop.text or prop.get('value', '')
                if prop_name and prop_value:
                    properties[f"ext_{prop_name}"] = prop_value
        
        return properties
    
    def _extract_task_specific_data(self, element: etree._Element, task_type: TaskType) -> Dict[str, Any]:
        """Extract task-specific data based on task type."""
        task_data = {}
        
        if task_type == TaskType.SCRIPT_TASK:
            script_elem = element.find(f"{{{self.namespaces['bpmn']}}}script")
            if script_elem is not None:
                task_data['script'] = script_elem.text or ''
                task_data['script_format'] = script_elem.get('scriptFormat', 'python')
        
        elif task_type == TaskType.SERVICE_TASK:
            # Extract service task configuration
            implementation = element.get('implementation', '')
            if implementation:
                task_data['service_url'] = implementation
                task_data['service_method'] = 'POST'  # Default to POST
        
        elif task_type in [TaskType.EXCLUSIVE_GATEWAY, TaskType.INCLUSIVE_GATEWAY]:
            # Extract gateway expressions
            default_flow = element.get('default')
            if default_flow:
                task_data['default_flow'] = default_flow
            
            # Extract conditional expressions from sequence flows
            task_data['gateway_expression'] = self._extract_gateway_expressions(element)
        
        elif task_type in [TaskType.INTERMEDIATE_CATCH_EVENT, TaskType.BOUNDARY_EVENT]:
            # Extract event definitions
            event_def = self._extract_event_definition(element)
            if event_def:
                task_data['event_definition'] = event_def
        
        return task_data
    
    def _extract_gateway_expressions(self, element: etree._Element) -> Optional[str]:
        """Extract conditional expressions from gateway sequence flows."""
        # This is a simplified extraction - in a full implementation,
        # you'd parse the actual BPMN conditional expressions
        return None
    
    def _extract_event_definition(self, element: etree._Element) -> Optional[Dict[str, Any]]:
        """Extract event definition from BPMN element."""
        event_def = {}
        
        # Check for timer events
        timer_elem = element.find(f"{{{self.namespaces['bpmn']}}}timerEventDefinition")
        if timer_elem is not None:
            time_elem = timer_elem.find(f"{{{self.namespaces['bpmn']}}}timeDuration")
            if time_elem is not None:
                event_def['type'] = 'timer'
                event_def['timer_expression'] = time_elem.text or ''
        
        # Check for message events
        message_elem = element.find(f"{{{self.namespaces['bpmn']}}}messageEventDefinition")
        if message_elem is not None:
            event_def['type'] = 'message'
            message_ref = message_elem.get('messageRef')
            if message_ref:
                event_def['message_ref'] = message_ref
        
        return event_def if event_def else None
    
    def validate_bpmn_file(self, file_path: str) -> bool:
        """Validate BPMN file against schema."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                bpmn_content = f.read()
            
            # Basic XML validation
            etree.fromstring(bpmn_content.encode('utf-8'))
            
            # Parse and validate structure
            self.parse_bpmn_xml(bpmn_content, "validation", "1.0.0")
            
            return True
            
        except Exception as e:
            print(f"BPMN validation failed: {e}")
            return False
