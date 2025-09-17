"""
XML Parser utilities for converting XML payloads to JSON format.
Handles OSM XML requests and converts them to structured JSON data.
Supports XSD validation and schema handling.
"""
import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union, Tuple
import json
from datetime import datetime
from lxml import etree as lxml_etree
from pathlib import Path
import logging

# Set up logging
logger = logging.getLogger(__name__)


class XMLParseError(Exception):
    """Custom exception for XML parsing errors."""
    pass


class XMLToJSONParser:
    """
    Converts XML payloads to JSON format with intelligent handling of OSM structures.
    Supports both ServiceOrderInstallationRequest and ServiceOrderFeasibilityRequest.
    Includes XSD validation and schema support.
    """
    
    def __init__(self, xsd_dir: str = None):
        """
        Initialize the XML parser with optional XSD schema directory.
        
        Args:
            xsd_dir: Optional directory path containing XSD schema files
        """
        self.namespace_map = {}
        self.schema_cache = {}
        self.xsd_dir = xsd_dir
        if xsd_dir:
            self._preload_schemas()
    
    def _preload_schemas(self):
        """Preload XSD schemas from the configured directory."""
        if not self.xsd_dir or not os.path.isdir(self.xsd_dir):
            logger.warning(f"XSD directory not found: {self.xsd_dir}")
            return
            
        for xsd_file in Path(self.xsd_dir).glob("*.xsd"):
            try:
                schema = lxml_etree.XMLSchema(file=str(xsd_file))
                self.schema_cache[xsd_file.stem] = schema
                logger.info(f"Loaded XSD schema: {xsd_file.name}")
            except Exception as e:
                logger.error(f"Failed to load XSD schema {xsd_file}: {str(e)}")
    
    def validate_with_xsd(self, xml_content: str, schema_name: str = None) -> Tuple[bool, str]:
        """
        Validate XML against a preloaded XSD schema.
        
        Args:
            xml_content: XML content to validate
            schema_name: Name of the schema to use (without .xsd extension)
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not schema_name or schema_name not in self.schema_cache:
            return False, f"Schema '{schema_name}' not found in cache"
            
        try:
            # Parse XML
            xml_doc = lxml_etree.fromstring(xml_content.encode())
            
            # Validate against schema
            self.schema_cache[schema_name].assertValid(xml_doc)
            return True, "Validation successful"
            
        except lxml_etree.DocumentInvalid as e:
            return False, f"XSD validation failed: {str(e)}"
        except Exception as e:
            return False, f"Error during XSD validation: {str(e)}"
    
    def parse_xml_to_json(self, xml_content: str, validate_xsd: bool = False, schema_name: str = None) -> Dict[str, Any]:
        """
        Parse XML content and convert to JSON structure with optional XSD validation.
        
        Args:
            xml_content: Raw XML string content
            validate_xsd: Whether to validate against XSD schema
            schema_name: Name of the XSD schema to validate against (must be preloaded)
            
        Returns:
            Dict containing the parsed JSON structure
            
        Raises:
            XMLParseError: If XML parsing or validation fails
        """
        try:
            # Remove BOM if present
            xml_content = xml_content.strip()
            if xml_content.startswith('\ufeff'):
                xml_content = xml_content[1:]
            
            # Validate with XSD if requested
            if validate_xsd and schema_name:
                is_valid, message = self.validate_with_xsd(xml_content, schema_name)
                if not is_valid:
                    raise XMLParseError(f"XSD validation failed: {message}")
            
            # Parse XML
            root = ET.fromstring(xml_content)
            return self._element_to_dict(root)
        except ET.ParseError as e:
            raise XMLParseError(f"Failed to parse XML: {str(e)}")
        except Exception as e:
            raise XMLParseError(f"Unexpected error during XML parsing: {str(e)}")
    
    def _element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """
        Convert XML element to dictionary recursively.
        
        Args:
            element: XML Element to convert
            
        Returns:
            Dictionary representation of the element
        """
        result = {}
        
        # Handle attributes
        if element.attrib:
            for key, value in element.attrib.items():
                # Convert attribute names to snake_case and prefix with attr_
                attr_key = f"attr_{self._to_snake_case(key)}"
                result[attr_key] = self._convert_value(value)
        
        # Handle text content
        if element.text and element.text.strip():
            text_content = element.text.strip()
            if len(element) == 0:  # Leaf node
                return self._convert_value(text_content)
            else:
                result['_text'] = self._convert_value(text_content)
        
        # Handle child elements
        children_dict = {}
        for child in element:
            child_key = self._to_snake_case(child.tag)
            child_value = self._element_to_dict(child)
            
            # Handle multiple children with same tag (convert to list)
            if child_key in children_dict:
                if not isinstance(children_dict[child_key], list):
                    children_dict[child_key] = [children_dict[child_key]]
                children_dict[child_key].append(child_value)
            else:
                children_dict[child_key] = child_value
        
        # Handle special OSM structures
        children_dict = self._handle_osm_structures(children_dict)
        
        result.update(children_dict)
        
        return result if result else None
    
    def _handle_osm_structures(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle special OSM XML structures like <item> collections.
        
        Args:
            data: Dictionary to process
            
        Returns:
            Processed dictionary with OSM structures normalized
        """
        # Convert <item> collections to arrays
        for key, value in list(data.items()):
            if isinstance(value, dict) and 'item' in value:
                item_value = value['item']
                if isinstance(item_value, list):
                    data[key] = item_value
                else:
                    data[key] = [item_value]
            elif isinstance(value, dict):
                data[key] = self._handle_osm_structures(value)
            elif isinstance(value, list):
                data[key] = [
                    self._handle_osm_structures(item) if isinstance(item, dict) else item
                    for item in value
                ]
        
        return data
    
    def _convert_value(self, value: str) -> Union[str, int, float, bool]:
        """
        Convert string value to appropriate Python type.
        
        Args:
            value: String value to convert
            
        Returns:
            Converted value with appropriate type
        """
        if not value:
            return value
        
        # Try boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try integer conversion
        try:
            if '.' not in value and 'e' not in value.lower():
                return int(value)
        except ValueError:
            pass
        
        # Try float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _to_snake_case(self, name: str) -> str:
        """
        Convert CamelCase to snake_case.
        
        Args:
            name: CamelCase string
            
        Returns:
            snake_case string
        """
        import re
        # Insert underscore before uppercase letters (except first)
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Insert underscore before uppercase letters preceded by lowercase
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class OSMXMLMapper:
    """
    OSM-specific XML to JSON mapper that converts OSM XML payloads 
    to the JSON format expected by the existing OSM mapper.
    """
    
    def __init__(self):
        self.parser = XMLToJSONParser()
    
    def xml_to_json(self, xml_content: str) -> Dict[str, Any]:
        """
        Convert OSM XML payload to JSON format compatible with OSMMapper.
        
        Args:
            xml_content: Raw XML string from OSM
            
        Returns:
            JSON structure compatible with existing OSM mapper
            
        Raises:
            XMLParseError: If XML parsing or conversion fails
        """
        try:
            # Parse XML to intermediate JSON
            parsed_data = self.parser.parse_xml_to_json(xml_content)
            
            # Determine request type and convert accordingly
            if 'service_order_installation_request' in parsed_data:
                return self._convert_installation_request(parsed_data['service_order_installation_request'])
            elif 'service_order_feasibility_request' in parsed_data:
                return self._convert_feasibility_request(parsed_data['service_order_feasibility_request'])
            else:
                # Try to detect root element
                root_key = next(iter(parsed_data.keys()))
                return self._convert_generic_service_order(parsed_data[root_key])
                
        except Exception as e:
            raise XMLParseError(f"Failed to convert OSM XML to JSON: {str(e)}")
    
    def _convert_installation_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ServiceOrderInstallationRequest to JSON format."""
        return self._convert_service_order_base(data)
    
    def _convert_feasibility_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ServiceOrderFeasibilityRequest to JSON format."""
        return self._convert_service_order_base(data)
    
    def _convert_generic_service_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert generic service order to JSON format."""
        return self._convert_service_order_base(data)
    
    def _convert_service_order_base(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert base service order structure to JSON format expected by OSMMapper.
        
        Args:
            data: Parsed XML data
            
        Returns:
            JSON structure compatible with OSMMapper.to_rules()
        """
        result = {
            "externalId": data.get("external_id"),
            "priority": self._safe_int(data.get("priority"), 5),
            "category": data.get("category"),
            "orderDate": data.get("order_date"),
            "requestedCompletionDate": data.get("requested_completion_date"),
            "description": data.get("description"),
            "relatedParty": self._convert_related_party(data.get("related_party", [])),
            "serviceOrderItem": self._convert_service_order_items(data.get("service_order_item", [])),
            "note": self._convert_notes(data.get("note", [])),
            "orderRelationship": self._convert_order_relationships(data.get("order_relationship", []))
        }
        
        # Add root level fields
        if "id" in data:
            result["id"] = data["id"]
        if "href" in data:
            result["href"] = data["href"]
        if "state" in data:
            result["state"] = data["state"]
        
        return result
    
    def _convert_related_party(self, related_party_data: Union[List, Dict]) -> List[Dict[str, Any]]:
        """Convert relatedParty XML structure to JSON array."""
        if not related_party_data:
            return []
        
        if isinstance(related_party_data, dict):
            related_party_data = [related_party_data]
        
        result = []
        for party in related_party_data:
            if isinstance(party, dict):
                result.append({
                    "id": party.get("id"),
                    "role": party.get("role"),
                    "name": party.get("name"),
                    "referredType": party.get("attr_referred_type")
                })
        
        return result
    
    def _convert_service_order_items(self, items_data: Union[List, Dict]) -> List[Dict[str, Any]]:
        """Convert serviceOrderItem XML structure to JSON array."""
        if not items_data:
            return []
        
        if isinstance(items_data, dict):
            items_data = [items_data]
        
        result = []
        for item in items_data:
            if isinstance(item, dict):
                service_data = item.get("service", {})
                
                converted_item = {
                    "id": item.get("id"),
                    "action": item.get("action", "add"),
                    "service": {
                        "id": service_data.get("id"),
                        "category": service_data.get("category"),
                        "serviceType": service_data.get("service_type"),
                        "serviceSpecification": self._convert_service_specification(
                            service_data.get("service_specification", {})
                        ),
                        "serviceCharacteristic": self._convert_service_characteristics(
                            service_data.get("service_characteristic", [])
                        ),
                        "place": self._convert_places(service_data.get("place", []))
                    }
                }
                result.append(converted_item)
        
        return result
    
    def _convert_service_specification(self, spec_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert serviceSpecification structure."""
        if not spec_data:
            return {}
        
        return {
            "id": spec_data.get("id"),
            "name": spec_data.get("name"),
            "version": spec_data.get("version")
        }
    
    def _convert_service_characteristics(self, chars_data: Union[List, Dict]) -> List[Dict[str, Any]]:
        """Convert serviceCharacteristic XML structure to JSON array."""
        if not chars_data:
            return []
        
        if isinstance(chars_data, dict):
            chars_data = [chars_data]
        
        result = []
        for char in chars_data:
            if isinstance(char, dict):
                result.append({
                    "name": char.get("name"),
                    "value": char.get("value"),
                    "valueType": char.get("value_type")
                })
        
        return result
    
    def _convert_places(self, places_data: Union[List, Dict]) -> List[Dict[str, Any]]:
        """Convert place XML structure to JSON array."""
        if not places_data:
            return []
        
        if isinstance(places_data, dict):
            places_data = [places_data]
        
        result = []
        for place in places_data:
            if isinstance(place, dict):
                geo_location = place.get("geographic_location", {})
                
                converted_place = {
                    "id": place.get("id"),
                    "role": place.get("role"),
                    "type": place.get("attr_type"),
                    "street": place.get("street"),
                    "city": place.get("city"),
                    "postalCode": place.get("postal_code"),
                    "country": place.get("country"),
                    "geographicLocation": {
                        "latitude": geo_location.get("latitude"),
                        "longitude": geo_location.get("longitude")
                    } if geo_location else {}
                }
                result.append(converted_place)
        
        return result
    
    def _convert_notes(self, notes_data: Union[List, Dict]) -> List[Dict[str, Any]]:
        """Convert note XML structure to JSON array."""
        if not notes_data:
            return []
        
        if isinstance(notes_data, dict):
            notes_data = [notes_data]
        
        result = []
        for note in notes_data:
            if isinstance(note, dict):
                result.append({
                    "text": note.get("text"),
                    "date": note.get("date"),
                    "author": note.get("author")
                })
        
        return result
    
    def _convert_order_relationships(self, relationships_data: Union[List, Dict]) -> List[Dict[str, Any]]:
        """Convert orderRelationship XML structure to JSON array."""
        if not relationships_data:
            return []
        
        if isinstance(relationships_data, dict):
            relationships_data = [relationships_data]
        
        result = []
        for rel in relationships_data:
            if isinstance(rel, dict):
                result.append({
                    "id": rel.get("id"),
                    "relationshipType": rel.get("relationship_type"),
                    "href": rel.get("href")
                })
        
        return result
    
    def _safe_int(self, value: Any, default: int = 0) -> int:
        """Safely convert value to integer with fallback."""
        if value is None:
            return default
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
