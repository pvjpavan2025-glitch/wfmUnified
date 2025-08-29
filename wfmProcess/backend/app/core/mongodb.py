"""MongoDB connection and database management for BPMN backend."""

import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from ..core.config import settings

# MongoDB client instance
mongodb_client: Optional[AsyncIOMotorClient] = None
mongodb_database: Optional[AsyncIOMotorDatabase] = None


async def init_mongodb() -> None:
    """Initialize MongoDB connection."""
    global mongodb_client, mongodb_database
    
    try:
        # Get MongoDB connection string from settings
        mongodb_url = getattr(settings, 'MONGODB_URL', None)
        
        if not mongodb_url:
            # Fallback to local MongoDB if no URL provided
            mongodb_url = "mongodb://wfmadmin:tsarolabs%4012345%23@wfm-mongodb:27017/wfm?authSource=admin"
        
        # Create MongoDB client
        mongodb_client = AsyncIOMotorClient(
            mongodb_url,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            maxPoolSize=10,
            minPoolSize=1
        )
        
        # Test connection
        await mongodb_client.admin.command('ping')
        
        # Get database
        database_name = getattr(settings, 'MONGODB_DATABASE', 'wfm')
        mongodb_database = mongodb_client[database_name]
        
        # Initialize collections
        await _initialize_collections()
        
        print(f"✅ Connected to MongoDB database: {database_name}")
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error connecting to MongoDB: {e}")
        raise


async def close_mongodb() -> None:
    """Close MongoDB connection."""
    global mongodb_client
    
    if mongodb_client:
        mongodb_client.close()
        print("✅ MongoDB connection closed")


async def _initialize_collections() -> None:
    """Initialize MongoDB collections with proper indexes."""
    if mongodb_database is None:
        return
    
    try:
        # Create collections if they don't exist
        collections = ['processes', 'process_instances', 'templates']
        
        for collection_name in collections:
            if collection_name not in await mongodb_database.list_collection_names():
                await mongodb_database.create_collection(collection_name)
                print(f"✅ Created collection: {collection_name}")
        
        # Create indexes for processes collection
        processes_collection = mongodb_database.processes
        await processes_collection.create_index("name", unique=False)
        await processes_collection.create_index("process_id", unique=True)
        await processes_collection.create_index("category")
        await processes_collection.create_index("tags")
        await processes_collection.create_index("is_active")
        await processes_collection.create_index("created_at")
        await processes_collection.create_index("updated_at")
        
        # Create indexes for process_instances collection
        instances_collection = mongodb_database.process_instances
        await instances_collection.create_index("instance_id", unique=True)
        await instances_collection.create_index("process_id")
        await instances_collection.create_index("status")
        await instances_collection.create_index("started_at")
        await instances_collection.create_index("completed_at")
        await instances_collection.create_index("started_by")
        
        # Create indexes for templates collection
        templates_collection = mongodb_database.templates
        await templates_collection.create_index("name", unique=False)
        await templates_collection.create_index("process_id", unique=True)
        await templates_collection.create_index("category")
        await templates_collection.create_index("tags")
        await templates_collection.create_index("is_public")
        await templates_collection.create_index("is_active")
        await templates_collection.create_index("created_at")
        
        print("✅ MongoDB collections and indexes initialized")
        
    except Exception as e:
        print(f"⚠️ Warning: Failed to initialize MongoDB collections: {e}")


def get_mongodb_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance."""
    if mongodb_database is None:
        raise RuntimeError("MongoDB not connected. Call connect_to_mongodb() first.")
    return mongodb_database


def get_mongodb_client() -> AsyncIOMotorClient:
    """Get MongoDB client instance."""
    if mongodb_client is None:
        raise RuntimeError("MongoDB not connected. Call connect_to_mongodb() first.")
    return mongodb_client


async def health_check() -> dict:
    """Check MongoDB connection health."""
    try:
        if mongodb_client is None:
            return {"status": "disconnected", "error": "Client not initialized"}
        
        # Test connection with ping
        await mongodb_client.admin.command('ping')
        
        # Get database stats
        db_stats = await mongodb_database.command("dbStats")
        
        return {
            "status": "connected",
            "database": mongodb_database.name,
            "collections": db_stats.get("collections", 0),
            "data_size": db_stats.get("dataSize", 0),
            "storage_size": db_stats.get("storageSize", 0)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# Dependency function for FastAPI
async def get_mongodb_db() -> AsyncIOMotorDatabase:
    """Dependency function to get MongoDB database for FastAPI routes."""
    return get_mongodb_database()
