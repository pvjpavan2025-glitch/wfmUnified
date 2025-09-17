"""
End-to-End Test: OSM XML → Rules Engine → Process Selection → BPMN Execution → Task Creation
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path
PROJECT_ROOT = str(Path(__file__).parent.parent)
sys.path.insert(0, PROJECT_ROOT)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to see all messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_xml_file(file_path: str) -> str:
    """Load XML content from file."""
    with open(file_path, 'r') as f:
        return f.read()

def test_end_to_end_flow(xml_file_path: str, xsd_dir: str = None):
    """
    Test the complete flow from OSM XML to task creation.
    
    Args:
        xml_file_path: Path to the OSM XML file
        xsd_dir: Optional directory containing XSD schemas for validation
    """
    try:
        # 1. Load the XML file
        logger.info("1. Loading XML file...")
        from intServices.app.mappers.xml_parser import OSMXMLMapper, XMLParseError
        from intServices.app.mappers.xml_parser import XMLToJSONParser
        
        # Read the XML file content
        with open(xml_file_path, 'r') as f:
            xml_content = f.read()
        
        logger.debug(f"XML content sample: {xml_content[:200]}...")
        
        # 2. Convert XML to JSON
        logger.info("2. Converting XML to JSON...")
        
        # First try with the standard XML parser
        try:
            xml_mapper = OSMXMLMapper()
            json_data = xml_mapper.xml_to_json(xml_content)
            logger.debug(f"Converted JSON data: {json.dumps(json_data, indent=2)[:500]}...")
        except XMLParseError as e:
            logger.warning(f"Standard XML parsing failed, trying with direct XMLToJSONParser: {str(e)}")
            # Fall back to using XMLToJSONParser directly
            try:
                parser = XMLToJSONParser()
                parsed_data = parser.parse_xml_to_json(xml_content)
                logger.debug(f"Successfully parsed with XMLToJSONParser: {json.dumps(parsed_data, indent=2)[:500]}...")
                # Convert to the expected format for OSMMapper
                if isinstance(parsed_data, dict):
                    json_data = {
                        'id': parsed_data.get('id', ''),
                        'externalId': parsed_data.get('externalId', ''),
                        'priority': parsed_data.get('priority', 5),
                        'category': parsed_data.get('category', ''),
                        'description': parsed_data.get('description', '')
                    }
                else:
                    raise ValueError("Parsed data is not a dictionary")
            except Exception as e:
                logger.error(f"Failed to parse XML with XMLToJSONParser: {str(e)}")
                raise
        
        # 3. Convert to Rules Engine format
        logger.info("3. Converting to Rules Engine format...")
        from intServices.app.mappers.osm import OSMMapper
        osm_mapper = OSMMapper()
        rules_data = osm_mapper.to_rules(json_data)
        
        logger.info("4. Evaluating order with rules engine...")
        from intServices.app.services.rules_client import RulesClient
        from intServices.app.core.config import settings
        import asyncio
        
        # Enable stub mode for testing
        settings.rules_api_stub = True
        
        # Create an async function to run the async code
        async def evaluate_order():
            rules_client = RulesClient()
            evaluation_result = await rules_client.evaluate_order(rules_data)
            return evaluation_result
            
        # Run the async function
        evaluation_result = asyncio.run(evaluate_order())
        
        # Get the process ID from the evaluation result
        process_id = evaluation_result.get('process_id')
        if not process_id:
            raise ValueError("No process_id returned from rules evaluation")
            
        logger.info(f"5. Selected process: {process_id}")
        
        # 6. Start BPMN process
        logger.info("6. Starting BPMN process...")
        from intServices.app.services.process_client import ProcessClient
        process_client = ProcessClient()
        process_instance = process_client.start_process(
            process_id,
            variables=rules_data
        )
        
        # 7. Get tasks
        logger.info("7. Retrieving tasks...")
        tasks = process_client.get_tasks(process_instance['id'])
        
        # 8. Assign and complete tasks
        logger.info("8. Processing tasks...")
        for task in tasks:
            logger.info(f"  - Task {task['id']}: {task['name']} (Status: {task['status']})")
            # Here you would typically assign to a technician and complete the task
            # process_client.complete_task(task['id'], {'status': 'completed'})
        
        logger.info("✅ End-to-end test completed successfully!")
        return {
            'success': True,
            'process_instance': process_instance,
            'tasks': tasks
        }
        
    except Exception as e:
        logger.error(f"❌ End-to-end test failed: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    # Path to your XML file
    xml_file = "documentation/xmls-v1/OSM_CreateFiberService_Request_Payload.xml"
    
    # Optional: Path to XSD directory if you have schemas
    xsd_dir = "documentation/xmls-v1"
    
    # Run the end-to-end test
    result = test_end_to_end_flow(xml_file, xsd_dir)
    print("\nTest Result:")
    print(json.dumps(result, indent=2))