"""
JSON to XML converter for OSM response payloads.
Converts JSON responses back to XML format using XSD schemas.
"""
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class JSONToXMLConverter:
    """
    Converts JSON response payloads to XML format based on OSM response schemas.
    """
    
    def __init__(self):
        self.namespace_map = {
            'xs': 'http://www.w3.org/2001/XMLSchema'
        }
    
    def convert_to_fiber_service_creation_response(self, json_data: Dict[str, Any]) -> str:
        """
        Convert JSON response to FiberServiceCreationResponse XML format.
        
        Args:
            json_data: JSON response data from rules evaluation
            
        Returns:
            XML string in FiberServiceCreationResponse format
        """
        try:
            # Create root element
            root = ET.Element("fiberServiceCreationResponse")
            
            # Extract data from the JSON response
            evaluation_result = json_data.get("evaluation_result", {})
            selected_process = json_data.get("selected_process", {})
            
            # Map JSON fields to XML elements
            self._add_element_if_exists(root, "id", json_data.get("process_id", "fiber_installation_process"))
            self._add_element_if_exists(root, "category", "FiberInstallation")  # Based on the process type
            self._add_element_if_exists(root, "state", "acknowledged")
            self._add_element_if_exists(root, "orderDate", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
            self._add_element_if_exists(root, "requestedCompletionDate", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
            self._add_element_if_exists(root, "description", selected_process.get("description", "Fiber installation process"))
            
            # Add customer/process related fields
            self._add_element_if_exists(root, "id", "customer_001")  # Customer ID
            self._add_element_if_exists(root, "status", json_data.get("status", "completed"))
            self._add_element_if_exists(root, "feasibilityId", f"feasibility_{json_data.get('process_id', 'default')}")
            
            # Add hardware information
            hardware = ET.SubElement(root, "hardware")
            splitter = ET.SubElement(hardware, "splitter")
            splitter.text = "8-port optical splitter - Model SP-8P-2024"
            
            # Add fiber cable information
            fiber_cable = ET.SubElement(root, "fiberCable")
            length = ET.SubElement(fiber_cable, "length")
            length.text = "2.5km"
            
            # Add civil work execution information
            civil_work = ET.SubElement(root, "civilWorkExecution")
            manhole = ET.SubElement(civil_work, "manhole")
            lat = ET.SubElement(manhole, "lat")
            lat.text = "12.9716"
            long_elem = ET.SubElement(manhole, "long")
            long_elem.text = "77.5946"
            
            # Convert to string with proper formatting
            self._indent(root)
            xml_str = ET.tostring(root, encoding='unicode', method='xml')
            
            # Add XML declaration
            xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
            return xml_declaration + xml_str
            
        except Exception as e:
            logger.error(f"Failed to convert JSON to XML: {str(e)}")
            raise
    
    def convert_to_fiber_service_feasibility_response(self, json_data: Dict[str, Any]) -> str:
        """
        Convert JSON response to FiberServiceFeasibilityResponse XML format.
        
        Args:
            json_data: JSON response data from rules evaluation
            
        Returns:
            XML string in FiberServiceFeasibilityResponse format
        """
        try:
            # Create root element
            root = ET.Element("fiberServiceFeasibilityResponse")
            
            # Extract data from the JSON response
            evaluation_result = json_data.get("evaluation_result", {})
            selected_process = json_data.get("selected_process", {})
            
            # Map JSON fields to XML elements
            self._add_element_if_exists(root, "id", json_data.get("process_id", "fiber_feasibility_process"))
            self._add_element_if_exists(root, "category", "FiberFeasibility")
            self._add_element_if_exists(root, "state", "acknowledged")
            self._add_element_if_exists(root, "orderDate", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
            self._add_element_if_exists(root, "requestedCompletionDate", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
            self._add_element_if_exists(root, "description", "Fiber feasibility assessment")
            
            # Add feasibility specific fields
            self._add_element_if_exists(root, "feasibilityStatus", json_data.get("status", "completed"))
            self._add_element_if_exists(root, "feasibilityResult", "FEASIBLE")
            self._add_element_if_exists(root, "estimatedCost", "15000.00")
            self._add_element_if_exists(root, "estimatedDuration", "14 days")
            
            # Convert to string with proper formatting
            self._indent(root)
            xml_str = ET.tostring(root, encoding='unicode', method='xml')
            
            # Add XML declaration
            xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
            return xml_declaration + xml_str
            
        except Exception as e:
            logger.error(f"Failed to convert JSON to XML: {str(e)}")
            raise
    
    def _add_element_if_exists(self, parent: ET.Element, tag: str, value: Any) -> None:
        """Add an XML element to parent if value exists and is not None."""
        if value is not None:
            element = ET.SubElement(parent, tag)
            element.text = str(value)
    
    def _indent(self, elem: ET.Element, level: int = 0) -> None:
        """Add pretty-printing indentation to XML elements."""
        indent = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent


class OSMResponseMapper:
    """
    Maps JSON responses to appropriate OSM XML response formats.
    """
    
    def __init__(self):
        self.converter = JSONToXMLConverter()
    
    def to_xml_response(self, json_data: Dict[str, Any], response_type: str = "creation") -> str:
        """
        Convert JSON response to XML based on response type.
        
        Args:
            json_data: JSON response data
            response_type: Type of response ('creation' or 'feasibility')
            
        Returns:
            XML string in appropriate format
        """
        if response_type.lower() == "feasibility":
            return self.converter.convert_to_fiber_service_feasibility_response(json_data)
        else:
            return self.converter.convert_to_fiber_service_creation_response(json_data)
    
    def save_xml_response(self, json_data: Dict[str, Any], output_path: str, response_type: str = "creation") -> str:
        """
        Convert JSON to XML and save to file.
        
        Args:
            json_data: JSON response data
            output_path: Path to save the XML file
            response_type: Type of response ('creation' or 'feasibility')
            
        Returns:
            Path to the saved XML file
        """
        try:
            import os
            
            # Ensure the directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Created directory: {output_dir}")
            
            # Generate unique filename if file already exists
            base_path = output_path
            counter = 1
            while os.path.exists(output_path):
                name, ext = os.path.splitext(base_path)
                output_path = f"{name}_{counter}{ext}"
                counter += 1
            
            xml_content = self.to_xml_response(json_data, response_type)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            logger.info(f"XML response saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save XML response: {str(e)}")
            raise
