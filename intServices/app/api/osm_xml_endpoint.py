"""
OSM XML API Endpoint - Handles XML payloads from OSM systems.
Provides REST endpoints for processing OSM XML requests.
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Any, Dict
import logging
from ..mappers.osm_xml import OSMXMLToRulesMapper
from ..mappers.xml_parser import XMLParseError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/osm", tags=["osm-xml"])

# Initialize the XML mapper
osm_xml_mapper = OSMXMLToRulesMapper()


@router.post("/xml/process")
async def process_osm_xml(request: Request) -> Dict[str, Any]:
    """
    Process OSM XML payload and convert to rules engine format.
    
    Accepts raw XML content in request body and returns JSON formatted for rules engine.
    
    Returns:
        Dict containing the converted payload and processing metadata
        
    Raises:
        HTTPException: If XML processing fails
    """
    try:
        # Read raw XML content from request body
        xml_content = await request.body()
        xml_string = xml_content.decode('utf-8')
        
        logger.info(f"Received OSM XML payload, size: {len(xml_string)} bytes")
        
        # Validate XML structure
        if not osm_xml_mapper.validate_xml_structure(xml_string):
            logger.warning("Invalid OSM XML structure detected")
            raise HTTPException(
                status_code=400, 
                detail="Invalid OSM XML structure. Expected ServiceOrder request format."
            )
        
        # Convert XML to rules engine format
        rules_payload = osm_xml_mapper.to_rules(xml_string)
        
        logger.info(f"Successfully converted OSM XML to rules format")
        
        return {
            "status": "success",
            "message": "OSM XML processed successfully",
            "data": rules_payload,
            "metadata": {
                "input_type": "xml",
                "source_system": "osm",
                "processed_at": "2024-11-09T18:53:39+05:30"
            }
        }
        
    except XMLParseError as e:
        logger.error(f"XML parsing error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"XML parsing failed: {str(e)}")
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid XML encoding. Expected UTF-8.")
    except Exception as e:
        logger.error(f"Unexpected error processing OSM XML: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/xml/validate")
async def validate_osm_xml(request: Request) -> Dict[str, Any]:
    """
    Validate OSM XML payload structure without processing.
    
    Returns validation results and structure analysis.
    
    Returns:
        Dict containing validation results and detected structure info
    """
    try:
        # Read raw XML content
        xml_content = await request.body()
        xml_string = xml_content.decode('utf-8')
        
        logger.info(f"Validating OSM XML payload, size: {len(xml_string)} bytes")
        
        # Validate structure
        is_valid = osm_xml_mapper.validate_xml_structure(xml_string)
        
        # Try to convert to JSON for structure analysis
        structure_info = {}
        try:
            json_data = osm_xml_mapper.xml_to_json(xml_string)
            structure_info = {
                "root_elements": list(json_data.keys()),
                "has_service_order_items": "serviceOrderItem" in json_data,
                "has_related_party": "relatedParty" in json_data,
                "category": json_data.get("category"),
                "order_date": json_data.get("orderDate")
            }
        except Exception as e:
            structure_info["parse_error"] = str(e)
        
        return {
            "status": "validation_complete",
            "is_valid": is_valid,
            "structure_info": structure_info,
            "metadata": {
                "input_size_bytes": len(xml_string),
                "validated_at": "2024-11-09T18:53:39+05:30"
            }
        }
        
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error during validation: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid XML encoding. Expected UTF-8.")
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.post("/xml/convert")
async def convert_xml_to_json(request: Request) -> Dict[str, Any]:
    """
    Convert OSM XML to JSON format (intermediate conversion).
    
    Useful for debugging and testing the XML-to-JSON conversion step.
    
    Returns:
        Dict containing the converted JSON payload
    """
    try:
        # Read raw XML content
        xml_content = await request.body()
        xml_string = xml_content.decode('utf-8')
        
        logger.info(f"Converting OSM XML to JSON, size: {len(xml_string)} bytes")
        
        # Convert XML to JSON
        json_payload = osm_xml_mapper.xml_to_json(xml_string)
        
        return {
            "status": "conversion_success",
            "message": "XML converted to JSON successfully",
            "json_data": json_payload,
            "metadata": {
                "input_type": "xml",
                "output_type": "json",
                "converted_at": "2024-11-09T18:53:39+05:30"
            }
        }
        
    except XMLParseError as e:
        logger.error(f"XML conversion error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"XML conversion failed: {str(e)}")
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error during conversion: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid XML encoding. Expected UTF-8.")
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")


@router.get("/xml/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for OSM XML processing service.
    
    Returns:
        Dict containing service health status
    """
    return {
        "status": "healthy",
        "service": "osm_xml_processor",
        "version": "1.0.0",
        "capabilities": [
            "xml_to_json_conversion",
            "xml_to_rules_conversion", 
            "xml_validation",
            "osm_service_order_processing"
        ],
        "supported_formats": [
            "ServiceOrderInstallationRequest",
            "ServiceOrderFeasibilityRequest"
        ]
    }
