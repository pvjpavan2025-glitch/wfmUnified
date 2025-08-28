"""
Repository layer for Configuration Service.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import motor.motor_asyncio
import structlog
from bson import ObjectId
from .models import Config

logger = structlog.get_logger(__name__)


class ConfigRepository:
    """Repository for configuration operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.configs
    
    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string."""
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return data
    
    async def create_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new configuration."""
        try:
            config_data["created_at"] = datetime.utcnow()
            config_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(config_data)
            config_data["_id"] = result.inserted_id
            
            return self._convert_id(config_data)
        except Exception as e:
            logger.error(f"Failed to create config: {str(e)}")
            raise
    
    async def get_config_by_id(self, config_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration by ID and tenant."""
        try:
            config = await self.collection.find_one({
                "_id": ObjectId(config_id),
                "tenant_id": tenant_id
            })
            
            if config:
                return self._convert_id(config)
            return None
        except Exception as e:
            logger.error(f"Failed to get config {config_id}: {str(e)}")
            return None
    
    async def get_config_by_key(self, key: str, tenant_id: str, environment: str = "default") -> Optional[Dict[str, Any]]:
        """Get configuration by key, tenant, and environment."""
        try:
            config = await self.collection.find_one({
                "key": key,
                "tenant_id": tenant_id,
                "environment": environment
            })
            
            if config:
                return self._convert_id(config)
            return None
        except Exception as e:
            logger.error(f"Failed to get config by key {key}: {str(e)}")
            return None
    
    async def update_config(self, config_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update configuration."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(config_id), "tenant_id": tenant_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_config_by_id(config_id, tenant_id)
            return None
        except Exception as e:
            logger.error(f"Failed to update config {config_id}: {str(e)}")
            return None
    
    async def delete_config(self, config_id: str, tenant_id: str) -> bool:
        """Delete configuration."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(config_id),
                "tenant_id": tenant_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete config {config_id}: {str(e)}")
            return False
    
    async def list_configs(self, tenant_id: str, environment: str = "default", skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List configurations for tenant and environment."""
        try:
            cursor = self.collection.find({
                "tenant_id": tenant_id,
                "environment": environment
            }).skip(skip).limit(limit)
            
            configs = await cursor.to_list(length=limit)
            return [self._convert_id(config) for config in configs]
        except Exception as e:
            logger.error(f"Failed to list configs for tenant {tenant_id}: {str(e)}")
            return []
    
    async def get_configs_by_keys(self, keys: List[str], tenant_id: str, environment: str = "default") -> List[Dict[str, Any]]:
        """Get multiple configurations by keys."""
        try:
            cursor = self.collection.find({
                "key": {"$in": keys},
                "tenant_id": tenant_id,
                "environment": environment
            })
            
            configs = await cursor.to_list(length=len(keys))
            return [self._convert_id(config) for config in configs]
        except Exception as e:
            logger.error(f"Failed to get configs by keys: {str(e)}")
            return []
    
    async def create_config_version(self, config_id: str, version_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new configuration version."""
        try:
            version_data["created_at"] = datetime.utcnow()
            
            result = await self.database.config_versions.insert_one(version_data)
            version_data["_id"] = result.inserted_id
            
            return self._convert_id(version_data)
        except Exception as e:
            logger.error(f"Failed to create config version: {str(e)}")
            raise
    
    async def get_config_versions(self, config_id: str, tenant_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get configuration versions."""
        try:
            cursor = self.database.config_versions.find({
                "config_id": config_id,
                "tenant_id": tenant_id
            }).sort("version", -1).limit(limit)
            
            versions = await cursor.to_list(length=limit)
            return [self._convert_id(version) for version in versions]
        except Exception as e:
            logger.error(f"Failed to get config versions: {str(e)}")
            return [] 