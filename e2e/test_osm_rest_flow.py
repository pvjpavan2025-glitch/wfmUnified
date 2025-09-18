"""
End-to-End Test using REST APIs for OSM Order Flow:
OSM XML → XMLToJSONParser → OSMXMLMapper → OSMMapper → Rules Engine → Process Selection → BPMN Execution → Task Creation
"""

"""
End-to-End Test using REST APIs for OSM Order Flow:
OSM XML → XMLToJSONParser → OSMXMLMapper → OSMMapper → Rules Engine → Process Selection → BPMN Execution → Task Creation
"""

import os
import sys
import asyncio
import logging
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to Python path
PROJECT_ROOT = str(Path(__file__).parent.parent)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "wfmServices"))

# Import message broker
from common.message_broker import MessageBroker, MessageBrokerConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Service URLs (update these based on your environment)
INTEGRATION_SERVICE_URL = "http://localhost:8082"  # intServices
RULES_SERVICE_URL = "http://localhost:8003"  # wfmServices rules-service
PROCESS_SERVICE_URL = "http://localhost:8008"  # wfmServices process-service

class TestOSMFlow:
    """End-to-end test for OSM order flow using REST APIs."""
    
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.order_id = None
        self.process_instance_id = None
        self.message_broker = MessageBroker(MessageBrokerConfig())
    
    async def initialize(self):
        """Initialize test resources."""
        await self.message_broker.initialize()
    
    async def cleanup(self):
        """Clean up test resources."""
        await self.client.aclose()
        await self.message_broker.close()
    
    async def load_test_xml(self) -> str:
        """Load test XML from configured source."""
        # Try to read from the message broker first
        content = await self.message_broker.read_message()
        
        # If no content from broker, fall back to test file
        if not content:
            test_file = os.path.join(
                PROJECT_ROOT, 
                "documentation", 
                "xmls-v2", 
                "OSM_WFM_CreateFiberService_Request_Payload.xml"
            )
            if os.path.exists(test_file):
                with open(test_file, 'r') as f:
                    content = f.read()
                    logger.info(f"Read {len(content)} bytes from test file")
        
        return content
    
    async def save_response(self, response: str, filename: Optional[str] = None):
        """Save response to the configured destination."""
        await self.message_broker.write_message(response, filename)
        logger.info(f"Response saved successfully")

    async def test_osm_flow(self):
        """Test the complete OSM order flow."""
        try:
            # Initialize message broker
            await self.initialize()
            
            # 1. Load test XML
            logger.info("1. Loading test XML...")
            xml_content = await self.load_test_xml()
            if not xml_content:
                logger.error("No XML content found")
                return False
                
            logger.info(f"Successfully loaded XML content ({len(xml_content)} bytes)")
            logger.info("2. Sending to Integration Service for XML processing...")
            response = await self.client.post(
                f"{INTEGRATION_SERVICE_URL}/osm/xml/process",
                content=xml_content,
                headers={"Content-Type": "application/xml"}
            )
            response.raise_for_status()
            rules_data = response.json()
            logger.info("Successfully converted XML to rules format")
            
            # 3. Send to Rules Engine for process selection
            logger.info("3. Sending to Rules Engine for process selection...")
            response = await self.client.post(
                f"{RULES_SERVICE_URL}/rules/evaluate",
                json={
                    "data": rules_data["data"],  # Extract the data from the response
                    "orchestrate": True,
                    "auto_schedule": True,
                    "tenant_id": "test-tenant"
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer mock-jwt-token-for-development"
                }
            )
            response.raise_for_status()
            evaluation_result = response.json()
            
            process_id = evaluation_result.get("process_id")
            if not process_id:
                raise ValueError("No process_id returned from rules evaluation")
            
            logger.info(f"4. Selected process: {process_id}")
            
            # Check if the task is marked as completed
            status = evaluation_result.get("status")
            message = evaluation_result.get("message")
            selected_process = evaluation_result.get("selected_process", {})
            
            logger.info(f"5. Task status: {status}")
            logger.info(f"6. Message: {message}")
            logger.info(f"7. Selected process details: {selected_process}")
            
            # Validate the response structure
            if status != "completed":
                raise ValueError(f"Expected status 'completed', got '{status}'")
            
            # 8. Convert response to XML and save
            logger.info("8. Converting JSON response to XML...")
            
            # Prepare the complete response data for XML conversion
            complete_response = {
                "success": True,
                "process_id": process_id,
                "status": status,
                "message": message,
                "selected_process": selected_process,
                "evaluation_result": evaluation_result
            }
            
            # Determine response type based on process
            response_type = "feasibility" if "feasibility" in process_id.lower() else "creation"
            
            # Convert to XML using Integration Service
            xml_conversion_response = await self.client.post(
                f"{INTEGRATION_SERVICE_URL}/response/json-to-xml",
                json={
                    "json_data": complete_response,
                    "response_type": response_type,
                    "save_to_file": True,
                    "filename": f"osm_{response_type}_response_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.xml"
                },
                headers={"Content-Type": "application/json"}
            )
            if xml_conversion_response.status_code != 200:
                error_detail = "Unknown error"
                try:
                    error_response = xml_conversion_response.json()
                    error_detail = error_response.get("detail", str(error_response))
                except:
                    error_detail = xml_conversion_response.text
                logger.error(f"XML conversion failed with status {xml_conversion_response.status_code}: {error_detail}")
                raise Exception(f"XML conversion failed: {error_detail}")
            
            xml_result = xml_conversion_response.json()
            
            logger.info(f"9. XML response saved to: {xml_result.get('file_path', 'unknown')}")
            logger.info(f"10. XML content preview: {xml_result.get('xml_content', '')[:200]}...")
            
            logger.info("✅ End-to-end OSM flow completed successfully!")
            logger.info(f"Selected process: {process_id}")
            logger.info(f"Process status: {selected_process.get('status', 'unknown')}")
            logger.info(f"XML response file: {xml_result.get('file_path', 'N/A')}")
            
            return {
                "success": True,
                "process_id": process_id,
                "status": status,
                "message": message,
                "selected_process": selected_process,
                "evaluation_result": evaluation_result,
                "xml_response": {
                    "file_path": xml_result.get("file_path"),
                    "xml_content": xml_result.get("xml_content"),
                    "metadata": xml_result.get("metadata")
                }
            }
            
        except Exception as e:
            logger.error(f"❌ End-to-end test failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
        finally:
            await self.cleanup()


async def main():
    """Run the end-to-end test."""
    test = TestOSMFlow()
    result = await test.test_osm_flow()
    print("\nTest Result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
