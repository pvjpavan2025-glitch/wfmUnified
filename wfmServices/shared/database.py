"""
Database connection management for WFM microservices.
"""
import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as redis
import structlog
from .config import settings

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """Manages database connections for MongoDB and Redis."""
    
    def __init__(self):
        self.mongodb_client: Optional[AsyncIOMotorClient] = None
        self.redis_client: Optional[redis.Redis] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
    
    async def connect_mongodb(self):
        """Connect to MongoDB."""
        try:
            mongo_kwargs = {}
            # Configure TLS if requested
            if settings.database.mongodb_tls:
                mongo_kwargs.update({
                    "tls": True,
                    "tlsCAFile": settings.database.mongodb_tls_ca_file,
                    "tlsAllowInvalidCertificates": settings.database.mongodb_tls_allow_invalid_certificates,
                })
            self.mongodb_client = AsyncIOMotorClient(
                settings.database.mongodb_url,
                **mongo_kwargs,
            )
            self.database = self.mongodb_client[settings.database.database_name]
            
            # Test connection
            await self.mongodb_client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    async def connect_redis(self):
        """Connect to Redis."""
        try:
            self.redis_client = redis.from_url(
                settings.database.redis_url,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    async def get_database(self):
        """Get MongoDB database instance."""
        if self.database is None:
            await self.connect_mongodb()
        return self.database
    
    async def get_redis(self):
        """Get Redis client instance."""
        if self.redis_client is None:
            await self.connect_redis()
        return self.redis_client
    
    async def close(self):
        """Close all database connections."""
        if self.mongodb_client is not None:
            self.mongodb_client.close()
            logger.info("MongoDB connection closed")
        
        if self.redis_client is not None:
            await self.redis_client.close()
            logger.info("Redis connection closed")


# Global database manager instance
db_manager = DatabaseManager()


async def get_database():
    """Get MongoDB database instance."""
    return await db_manager.get_database()


async def get_redis_client():
    """Get Redis client instance."""
    return await db_manager.get_redis()


async def close_database_connections():
    """Close all database connections."""
    await db_manager.close() 