"""
Utility functions for XML handling in end-to-end tests.
"""
import os
import tempfile
import xml.etree.ElementTree as ET
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

def load_xml_file(file_path: str) -> str:
    """Load XML content from file."""
    with open(file_path, 'r') as f:
        return f.read()

def create_response_xml(response_data: Dict[str, Any], template_path: str) -> str:
    """
    Create a response XML based on the template and provided data.
    
    Args:
        response_data: Dictionary containing response data
        template_path: Path to the response XML template
        
    Returns:
        str: Generated XML content
    """
    # Load the template
    tree = ET.parse(template_path)
    root = tree.getroot()
    
    # Update fields in the template
    for key, value in response_data.items():
        element = root.find(f".//{key}")
        if element is not None:
            element.text = str(value)
    
    # Convert to string
    return ET.tostring(root, encoding='unicode', method='xml')

def save_response_xml(xml_content: str, output_dir: str = None) -> str:
    """
    Save XML content to a temporary file.
    
    Args:
        xml_content: XML content to save
        output_dir: Directory to save the file (default: system temp directory)
        
    Returns:
        str: Path to the saved file
    """
    if output_dir is None:
        output_dir = tempfile.gettempdir()
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a temporary file with .xml extension
    fd, temp_path = tempfile.mkstemp(suffix='.xml', dir=output_dir)
    
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(xml_content)
        logger.info(f"Saved response XML to: {temp_path}")
        return temp_path
    except Exception as e:
        logger.error(f"Failed to save response XML: {str(e)}")
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise

def json_to_xml_response(json_data: Dict[str, Any], template_path: str, output_dir: str = None) -> str:
    """
    Convert JSON data to XML response using a template.
    
    Args:
        json_data: JSON data to include in the response
        template_path: Path to the XML template
        output_dir: Directory to save the output file (default: system temp directory)
        
    Returns:
        str: Path to the generated XML file
    """
    # Convert the JSON data to a flat dictionary if it's nested
    flat_data = {}
    for key, value in json_data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flat_data[f"{key}_{sub_key}"] = sub_value
        else:
            flat_data[key] = value
    
    # Create the XML from template
    xml_content = create_response_xml(flat_data, template_path)
    
    # Save to file
    return save_response_xml(xml_content, output_dir)
