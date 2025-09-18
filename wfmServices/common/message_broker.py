"""
Message Broker Module for handling different message broker types.
Supports both file-based and JMS-based message handling.
"""
import os
import logging
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class MessageBrokerType(Enum):
    """Supported message broker types."""
    FILE = "file"
    JMS = "jms"

class MessageBrokerConfig:
    """Configuration for message broker."""
    
    def __init__(self):
        self.broker_type = os.getenv("MESSAGE_BROKER_TYPE", "file").lower()
        
        # JMS Configuration
        self.jms_url = os.getenv("JMS_URL", "t3://localhost:7001")
        self.jms_username = os.getenv("JMS_USERNAME", "weblogic")
        self.jms_password = os.getenv("JMS_PASSWORD", "welcome1")
        self.jms_connection_factory = os.getenv("JMS_CONNECTION_FACTORY", "jms/ConnectionFactory")
        self.jms_request_queue = os.getenv("JMS_REQUEST_QUEUE", "jms/OSMRequestQueue")
        self.jms_response_queue = os.getenv("JMS_RESPONSE_QUEUE", "jms/OSMResponseQueue")
        
        # File Configuration
        self.input_dir = os.getenv("INPUT_DIR", "/app/input")
        self.output_dir = os.getenv("OUTPUT_DIR", "/app/output")
        
        # Create directories if they don't exist
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

class MessageBroker:
    """Message broker implementation supporting multiple backends."""
    
    def __init__(self, config: Optional[MessageBrokerConfig] = None):
        self.config = config or MessageBrokerConfig()
        try:
            self.broker_type = MessageBrokerType(self.config.broker_type)
        except ValueError:
            logger.warning(f"Invalid broker type: {self.config.broker_type}. Defaulting to FILE.")
            self.broker_type = MessageBrokerType.FILE
        self.initialized = False

    async def initialize(self):
        """Initialize the message broker connection if needed."""
        if self.broker_type == MessageBrokerType.JMS and not self.initialized:
            await self._initialize_jms()
        self.initialized = True

    async def _initialize_jms(self):
        """Initialize JMS connection."""
        try:
            # JMS initialization code will go here
            # We'll implement this when we have the queue details
            logger.info("Initializing JMS connection...")
            # Simulate connection delay
            await asyncio.sleep(1)
            logger.info("JMS connection initialized (stub implementation)")
        except Exception as e:
            logger.error(f"Failed to initialize JMS: {str(e)}")
            raise

    async def read_message(self) -> Optional[str]:
        """Read a message from the configured source."""
        if self.broker_type == MessageBrokerType.FILE:
            return await self._read_from_file()
        elif self.broker_type == MessageBrokerType.JMS:
            return await self._read_from_jms()
        return None

    async def write_message(self, message: str, filename: Optional[str] = None):
        """Write a message to the configured destination."""
        if self.broker_type == MessageBrokerType.FILE:
            await self._write_to_file(message, filename)
        elif self.broker_type == MessageBrokerType.JMS:
            await self._write_to_jms(message)

    async def _read_from_file(self) -> Optional[str]:
        """Read from file system."""
        try:
            # Get the first XML file in the input directory
            input_dir = Path(self.config.input_dir)
            input_dir.mkdir(parents=True, exist_ok=True)
            
            xml_files = list(input_dir.glob("*.xml"))
            if not xml_files:
                logger.warning(f"No XML files found in {input_dir}")
                return None
                
            with open(xml_files[0], 'r') as f:
                content = f.read()
                logger.info(f"Read {len(content)} bytes from {xml_files[0]}")
                return content
        except Exception as e:
            logger.error(f"Error reading from file: {str(e)}")
            return None

    async def _write_to_file(self, message: str, filename: Optional[str] = None):
        """Write to file system."""
        try:
            output_dir = Path(self.config.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if not filename:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"response_{timestamp}.xml"
                
            output_path = output_dir / filename
            with open(output_path, 'w') as f:
                f.write(message)
            logger.info(f"Message written to {output_path}")
        except Exception as e:
            logger.error(f"Error writing to file: {str(e)}")
            raise

    async def _read_from_jms(self) -> Optional[str]:
        """Read from JMS queue (stub implementation)."""
        logger.info(f"JMS read from {self.config.jms_request_queue} (stub implementation)")
        # TODO: Implement actual JMS reading when queue details are available
        # For now, simulate a delay and return None
        await asyncio.sleep(1)
        return None

    async def _write_to_jms(self, message: str):
        """Write to JMS queue (stub implementation)."""
        logger.info(f"JMS write to {self.config.jms_response_queue} (stub implementation)")
        logger.debug(f"Message content: {message[:200]}...")
        # TODO: Implement actual JMS writing when queue details are available
        await asyncio.sleep(0.5)

    async def close(self):
        """Clean up resources."""
        if self.broker_type == MessageBrokerType.JMS and self.initialized:
            await self._close_jms_connection()

    async def _close_jms_connection(self):
        """Close JMS connection (stub implementation)."""
        logger.info("Closing JMS connection (stub implementation)")
        # TODO: Implement actual JMS connection closing
        await asyncio.sleep(0.5)

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test file-based broker
        os.environ["MESSAGE_BROKER_TYPE"] = "file"
        broker = MessageBroker()
        await broker.initialize()
        
        # Test reading (requires test file in input directory)
        content = await broker.read_message()
        print(f"Read content: {content[:100]}..." if content else "No content read")
        
        # Test writing
        await broker.write_message("<test>Hello, World!</test>", "test_output.xml")
        
        await broker.close()
    
    asyncio.run(test())
