"""
JMS Worker Service

A background service that continuously monitors a JMS queue for new XML messages,
processes them using the integration service, and sends responses back.
"""

import asyncio
import os
import logging
import signal
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JMSWorker:
    """Background worker for processing JMS messages."""
    
    def __init__(self):
        self.running = False
        self.client = httpx.AsyncClient()
        self.poll_interval = int(os.getenv("JMS_POLL_INTERVAL", "5"))  # seconds
        
        # Service URLs
        self.integration_service_url = os.getenv(
            "INTEGRATION_SERVICE_URL", 
            "http://integration-service:8082"
        )
        self.rules_service_url = os.getenv(
            "RULES_SERVICE_URL",
            "http://rules-service:8003"
        )
        
        # JMS Configuration
        self.jms_config = {
            "url": os.getenv("JMS_URL", "t3://weblogic:7001"),
            "username": os.getenv("JMS_USERNAME", "weblogic"),
            "password": os.getenv("JMS_PASSWORD", "welcome1"),
            "connection_factory": os.getenv("JMS_CONNECTION_FACTORY", "jms/ConnectionFactory"),
            "request_queue": os.getenv("JMS_REQUEST_QUEUE", "jms/OSMRequestQueue"),
            "response_queue": os.getenv("JMS_RESPONSE_QUEUE", "jms/OSMResponseQueue"),
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info("Shutdown signal received, stopping worker...")
        self.running = False
    
    async def connect_to_jms(self):
        """Establish connection to JMS server."""
        # TODO: Implement actual JMS connection
        logger.info(f"Connecting to JMS server at {self.jms_config['url']}...")
        await asyncio.sleep(1)  # Simulate connection delay
        logger.info("Connected to JMS server (stub implementation)")
        return True
    
    async def disconnect_from_jms(self):
        """Disconnect from JMS server."""
        # TODO: Implement actual JMS disconnection
        logger.info("Disconnecting from JMS server...")
        await asyncio.sleep(0.5)
        logger.info("Disconnected from JMS server")
    
    async def get_next_message(self) -> Optional[Dict[str, Any]]:
        """Get the next message from the JMS queue."""
        try:
            # TODO: Implement actual JMS message retrieval
            # For now, we'll simulate receiving a message
            await asyncio.sleep(self.poll_interval)
            
            # Check if we should simulate a message (every 30 seconds for testing)
            if int(datetime.now().timestamp()) % 30 == 0:
                test_xml = """<?xml version="1.0" encoding="UTF-8"?>
                <order>
                    <id>TEST-123</id>
                    <type>FiberInstallation</type>
                    <customer>Test Customer</customer>
                    <timestamp>2025-09-18T12:00:00Z</timestamp>
                </order>"""
                
                return {
                    "message_id": f"msg-{datetime.now().timestamp()}",
                    "correlation_id": f"corr-{datetime.now().timestamp()}",
                    "content": test_xml,
                    "properties": {"test": True}
                }
            return None
            
        except Exception as e:
            logger.error(f"Error receiving message from JMS: {str(e)}")
            return None
    
    async def send_response(self, correlation_id: str, response_xml: str):
        """Send response back to the JMS response queue."""
        try:
            # TODO: Implement actual JMS message sending
            logger.info(f"Sending response to JMS (correlation_id: {correlation_id})")
            logger.debug(f"Response content: {response_xml[:200]}...")
            return True
        except Exception as e:
            logger.error(f"Error sending response to JMS: {str(e)}")
            return False
    
    async def process_message(self, message: Dict[str, Any]):
        """Process a single JMS message."""
        message_id = message.get('message_id', 'unknown')
        correlation_id = message.get('correlation_id', '')
        xml_content = message.get('content', '')
        
        logger.info(f"Processing message {message_id} (correlation_id: {correlation_id})")
        
        try:
            # 1. Send to Integration Service for XML processing
            logger.info("Sending to Integration Service for processing...")
            response = await self.client.post(
                f"{self.integration_service_url}/osm/xml/process",
                content=xml_content,
                headers={"Content-Type": "application/xml"}
            )
            response.raise_for_status()
            rules_data = response.json()
            
            # 2. Process with Rules Service
            logger.info("Sending to Rules Service...")
            response = await self.client.post(
                f"{self.rules_service_url}/rules/evaluate",
                json=rules_data
            )
            response.raise_for_status()
            process_data = response.json()
            
            # 3. Generate response XML (simplified)
            response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <response>
                <status>SUCCESS</status>
                <message_id>{message_id}</message_id>
                <process_id>{process_data.get('process_id', '')}</process_id>
                <timestamp>{datetime.utcnow().isoformat()}</timestamp>
            </response>"""
            
            # 4. Send response back to JMS
            await self.send_response(correlation_id, response_xml)
            logger.info(f"Successfully processed message {message_id}")
            
            return True
            
        except Exception as e:
            error_msg = f"Error processing message {message_id}: {str(e)}"
            logger.error(error_msg)
            
            # Send error response
            error_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <response>
                <status>ERROR</status>
                <message_id>{message_id}</message_id>
                <error>{str(e)}</error>
                <timestamp>{datetime.utcnow().isoformat()}</timestamp>
            </response>"""
            
            await self.send_response(correlation_id, error_xml)
            return False
    
    async def run(self):
        """Main worker loop."""
        self.running = True
        
        try:
            # Connect to JMS
            if not await self.connect_to_jms():
                logger.error("Failed to connect to JMS server")
                return
            
            logger.info("JMS Worker started. Press Ctrl+C to stop.")
            
            # Main processing loop
            while self.running:
                try:
                    # Get next message (non-blocking)
                    message = await self.get_next_message()
                    
                    if message:
                        await self.process_message(message)
                    else:
                        # No messages, wait before polling again
                        await asyncio.sleep(1)
                        
                except asyncio.CancelledError:
                    logger.info("Worker task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in worker loop: {str(e)}")
                    await asyncio.sleep(5)  # Prevent tight loop on errors
                    
        except Exception as e:
            logger.error(f"Fatal error in JMS worker: {str(e)}")
            raise
            
        finally:
            # Cleanup
            await self.disconnect_from_jms()
            await self.client.aclose()
            logger.info("JMS Worker stopped")


async def main():
    """Entry point for the JMS worker."""
    worker = JMSWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
