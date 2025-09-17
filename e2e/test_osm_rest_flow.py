"""
End-to-End Test using REST APIs for OSM Order Flow:
OSM XML → XMLToJSONParser → OSMXMLMapper → OSMMapper → Rules Engine → Process Selection → BPMN Execution → Task Creation
"""

import os
import sys
import json
import logging
import asyncio
import httpx
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to Python path
PROJECT_ROOT = str(Path(__file__).parent.parent)
sys.path.insert(0, PROJECT_ROOT)

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

# Test data paths
TEST_DATA_DIR = os.path.join(PROJECT_ROOT, "documentation", "xmls-v1")
TEST_XML_FILE = os.path.join(TEST_DATA_DIR, "OSM_CreateFiberService_Request_Payload.xml")

class TestOSMFlow:
    """End-to-end test for OSM order flow using REST APIs."""
    
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.order_id = None
        self.process_instance_id = None
    
    async def cleanup(self):
        """Clean up test resources."""
        await self.client.aclose()
    
    async def load_test_xml(self) -> str:
        """Load test XML file."""
        with open(TEST_XML_FILE, 'r') as f:
            return f.read()
    
    async def test_osm_flow(self):
        """Test the complete OSM order flow."""
        try:
            # 1. Load test XML
            logger.info("1. Loading test XML...")
            xml_content = await self.load_test_xml()
            
            # 2. Send to Integration Service for XML processing
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
            
            logger.info("✅ End-to-end test completed successfully!")
            logger.info(f"Selected process: {process_id}")
            logger.info(f"Process status: {selected_process.get('status', 'unknown')}")
            
            return {
                "success": True,
                "process_id": process_id,
                "status": status,
                "message": message,
                "selected_process": selected_process,
                "evaluation_result": evaluation_result
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
