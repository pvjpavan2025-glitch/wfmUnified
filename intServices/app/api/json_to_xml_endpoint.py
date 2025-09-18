"""
JSON to XML conversion endpoint for OSM responses.
"""
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from ..mappers.json_to_xml import OSMResponseMapper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/response", tags=["JSON to XML Conversion"])


class JSONToXMLRequest(BaseModel):
    """Request model for JSON to XML conversion."""
    json_data: Dict[str, Any]
    response_type: Optional[str] = "creation"  # 'creation' or 'feasibility'
    save_to_file: Optional[bool] = True
    filename: Optional[str] = None


class JSONToXMLResponse(BaseModel):
    """Response model for JSON to XML conversion."""
    status: str
    message: str
    xml_content: str
    file_path: Optional[str] = None
    metadata: Dict[str, Any]


@router.post("/json-to-xml", response_model=JSONToXMLResponse)
async def convert_json_to_xml(request: JSONToXMLRequest):
    """
    Convert JSON response to OSM XML format.
    
    Args:
        request: JSON to XML conversion request
        
    Returns:
        XML content and file path if saved
    """
    try:
        logger.info(f"Converting JSON to XML - Type: {request.response_type}")
        
        # Initialize the mapper
        mapper = OSMResponseMapper()
        
        # Convert JSON to XML
        xml_content = mapper.to_xml_response(request.json_data, request.response_type)
        
        file_path = None
        if request.save_to_file:
            # Generate filename if not provided
            if not request.filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # Include microseconds for uniqueness
                request.filename = f"osm_{request.response_type}_response_{timestamp}.xml"
            
            # Ensure output directory exists
            output_dir = "/app/output/responses"
            try:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                    logger.info(f"Created output directory: {output_dir}")
            except Exception as e:
                logger.warning(f"Directory creation issue (may already exist): {str(e)}")
            
            # Save to file
            file_path = os.path.join(output_dir, request.filename)
            file_path = mapper.save_xml_response(request.json_data, file_path, request.response_type)
        
        return JSONToXMLResponse(
            status="success",
            message="JSON successfully converted to XML",
            xml_content=xml_content,
            file_path=file_path,
            metadata={
                "response_type": request.response_type,
                "conversion_time": datetime.now().isoformat(),
                "input_size": len(str(request.json_data)),
                "output_size": len(xml_content)
            }
        )
        
    except Exception as e:
        logger.error(f"JSON to XML conversion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert JSON to XML: {str(e)}"
        )


@router.get("/sample-response/{response_type}")
async def get_sample_response(response_type: str):
    """
    Get a sample JSON response for testing XML conversion.
    
    Args:
        response_type: Type of response ('creation' or 'feasibility')
        
    Returns:
        Sample JSON response
    """
    try:
        if response_type.lower() == "feasibility":
            sample_data = {
                "success": True,
                "process_id": "fiber_feasibility_process",
                "status": "completed",
                "message": "Feasibility assessment completed successfully",
                "selected_process": {
                    "process_id": "fiber_feasibility_process",
                    "process_name": "Fiber Feasibility Assessment",
                    "status": "selected",
                    "description": "Process selected for fiber feasibility assessment"
                },
                "evaluation_result": {
                    "matched_rules": [
                        {
                            "rule_id": "feasibility_rule_001",
                            "rule_name": "Fiber Feasibility Rule",
                            "category": "FiberFeasibility",
                            "priority": 5
                        }
                    ],
                    "evaluation_time": 0.05,
                    "total_rules_evaluated": 10
                }
            }
        else:
            sample_data = {
                "success": True,
                "process_id": "fiber_installation_process",
                "status": "completed",
                "message": "Rules evaluation completed successfully",
                "selected_process": {
                    "process_id": "fiber_installation_process",
                    "process_name": "Fiber Installation Process",
                    "status": "selected",
                    "description": "Process selected for fiber installation order"
                },
                "evaluation_result": {
                    "matched_rules": [
                        {
                            "rule_id": "installation_rule_001",
                            "rule_name": "Fiber Installation Rule",
                            "category": "FiberInstallation",
                            "priority": 5
                        }
                    ],
                    "evaluation_time": 0.092,
                    "total_rules_evaluated": 25
                }
            }
        
        return JSONResponse(content=sample_data)
        
    except Exception as e:
        logger.error(f"Failed to generate sample response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sample response: {str(e)}"
        )
