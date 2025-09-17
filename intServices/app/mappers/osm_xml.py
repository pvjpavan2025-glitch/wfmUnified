"""
OSM XML Mapper - Enhanced mapper that handles XML input from OSM systems.
This mapper acts as a bridge between XML payloads and the existing OSM JSON mapper.
Supports XSD validation and schema handling.
"""
import os
from typing import Any, Dict, Optional
from pathlib import Path
from .base import Mapper, registry
from .xml_parser import OSMXMLMapper, XMLParseError, XMLToJSONParser
from .osm import OSMMapper
import logging

logger = logging.getLogger(__name__)


class OSMXMLToRulesMapper(Mapper):
    """
    Enhanced OSM mapper that accepts XML input and converts it to rules engine format.
    
    This mapper provides a two-stage conversion:
    1. XML -> JSON (using OSMXMLMapper)
    2. JSON -> Rules Engine Format (using existing OSMMapper)
    
    Supports XSD validation and schema handling for XML inputs.
    """
    
    def __init__(self, xsd_dir: Optional[str] = None):
        """
        Initialize the OSM XML mapper with optional XSD schema directory.
        
        Args:
            xsd_dir: Optional directory path containing XSD schema files for validation
        """
        self.xsd_dir = xsd_dir
        self.json_mapper = OSMMapper()
        
        # Initialize XML parser with XSD support if directory is provided
        if xsd_dir and os.path.isdir(xsd_dir):
            logger.info(f"Initializing XML mapper with XSD directory: {xsd_dir}")
            self.xml_parser = XMLToJSONParser(xsd_dir=xsd_dir)
            self.xml_mapper = OSMXMLMapper()
            # Override the parser in the mapper with our configured one
            self.xml_mapper.parser = self.xml_parser
        else:
            logger.warning("No valid XSD directory provided, XSD validation will be disabled")
            self.xml_parser = XMLToJSONParser()
            self.xml_mapper = OSMXMLMapper()
            # Override the parser in the mapper with our configured one
            self.xml_mapper.parser = self.xml_parser
    
    def to_rules(self, payload: Dict[str, Any], validate_xsd: bool = False, 
                 schema_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert OSM payload to rules engine format with optional XSD validation.
        
        Supports both XML string input and JSON dict input for backward compatibility.
        
        Args:
            payload: Either XML string content or JSON dictionary
            validate_xsd: Whether to validate XML against XSD schema
            schema_name: Name of the XSD schema to validate against (must be preloaded)
            
        Returns:
            Dictionary formatted for rules engine consumption
            
        Raises:
            XMLParseError: If XML parsing or validation fails
            ValueError: If payload format is not supported or schema not found
        """
        try:
            # Check if payload contains XML content
            if isinstance(payload, dict) and 'xml_content' in payload:
                # Handle XML content wrapped in dictionary
                xml_content = payload['xml_content']
                # Validate with XSD if requested
                if validate_xsd and schema_name:
                    is_valid, message = self.xml_parser.validate_with_xsd(xml_content, schema_name)
                    if not is_valid:
                        raise XMLParseError(f"XSD validation failed: {message}")
                json_payload = self.xml_mapper.xml_to_json(xml_content)
            elif isinstance(payload, str):
                # Handle raw XML string
                # Validate with XSD if requested
                if validate_xsd and schema_name:
                    is_valid, message = self.xml_parser.validate_with_xsd(payload, schema_name)
                    if not is_valid:
                        raise XMLParseError(f"XSD validation failed: {message}")
                json_payload = self.xml_mapper.xml_to_json(payload)
            elif isinstance(payload, dict):
                # Handle existing JSON format (backward compatibility)
                json_payload = payload
            else:
                raise ValueError(f"Unsupported payload type: {type(payload)}")
            
            # Convert JSON to rules engine format using existing mapper
            return self.json_mapper.to_rules(json_payload)
            
        except XMLParseError as e:
            raise XMLParseError(f"OSM XML parsing failed: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to convert OSM payload to rules format: {str(e)}")
    
    def xml_to_json(self, xml_content: str) -> Dict[str, Any]:
        """
        Convert XML content to JSON format (intermediate step).
        
        Args:
            xml_content: Raw XML string from OSM
            
        Returns:
            JSON dictionary compatible with existing OSM mapper
        """
        return self.xml_mapper.xml_to_json(xml_content)
    
    def validate_xml_structure(self, xml_content: str) -> bool:
        """
        Validate if XML content has expected OSM structure.
        
        Args:
            xml_content: Raw XML string to validate
            
        Returns:
            True if XML structure is valid for OSM processing
        """
        try:
            json_data = self.xml_mapper.xml_to_json(xml_content)
            
            # Check for required OSM fields
            required_fields = ['category', 'orderDate']
            has_required = any(field in json_data for field in required_fields)
            
            # Check for OSM-specific structures
            has_service_items = 'serviceOrderItem' in json_data
            
            return has_required or has_service_items
            
        except Exception:
            return False


# Register the enhanced XML-capable mapper
registry.register("osm_xml", OSMXMLToRulesMapper())

# Keep backward compatibility by also registering as "osm" if needed
# Note: This would override the existing OSM mapper
# registry.register("osm", OSMXMLToRulesMapper())
