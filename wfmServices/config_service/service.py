"""
Business logic layer for Configuration Service.
"""
from typing import Optional, List, Dict, Any
import json
import structlog
import redis.asyncio as redis
from .repository import ConfigRepository
from .models import ConfigCreate, ConfigUpdate

logger = structlog.get_logger(__name__)


class ConfigService:
    """Configuration service business logic."""
    
    def __init__(self, config_repo: ConfigRepository, redis_client: redis.Redis):
        self.config_repo = config_repo
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5 minutes
    
    async def create_config(self, config_data: ConfigCreate, created_by: str) -> Dict[str, Any]:
        """Create a new configuration."""
        try:
            # Check if config key already exists for tenant and environment
            existing_config = await self.config_repo.get_config_by_key(
                config_data.key, config_data.tenant_id, config_data.environment
            )
            
            if existing_config:
                raise ValueError(f"Configuration key '{config_data.key}' already exists for this tenant and environment")
            
            # Validate value based on type
            self._validate_config_value(config_data.value, config_data.type)
            
            # Prepare config data
            config_dict = config_data.dict()
            config_dict["created_by"] = created_by
            config_dict["updated_by"] = created_by
            
            # Create config
            config = await self.config_repo.create_config(config_dict)
            
            # Invalidate cache
            await self._invalidate_cache(config_data.key, config_data.tenant_id, config_data.environment)
            
            logger.info(f"Configuration '{config_data.key}' created successfully for tenant {config_data.tenant_id}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to create config {config_data.key}: {str(e)}")
            raise
    
    async def get_config(self, config_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration by ID."""
        try:
            config = await self.config_repo.get_config_by_id(config_id, tenant_id)
            
            if config:
                # Convert value based on type
                config["value"] = self._convert_value(config["value"], config["type"])
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to get config {config_id}: {str(e)}")
            return None
    
    async def get_config_by_key(self, key: str, tenant_id: str, environment: str = "default") -> Optional[Dict[str, Any]]:
        """Get configuration by key with caching."""
        try:
            # Try to get from cache first
            cache_key = f"config:{tenant_id}:{environment}:{key}"
            cached_value = await self.redis_client.get(cache_key)
            
            if cached_value:
                logger.debug(f"Config '{key}' retrieved from cache")
                return json.loads(cached_value)
            
            # Get from database
            config = await self.config_repo.get_config_by_key(key, tenant_id, environment)
            
            if config:
                # Convert value based on type
                config["value"] = self._convert_value(config["value"], config["type"])
                
                # Cache the result
                await self.redis_client.setex(
                    cache_key, 
                    self.cache_ttl, 
                    json.dumps(config)
                )
                
                logger.debug(f"Config '{key}' cached")
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to get config by key {key}: {str(e)}")
            return None
    
    async def update_config(self, config_id: str, tenant_id: str, config_data: ConfigUpdate, updated_by: str) -> Optional[Dict[str, Any]]:
        """Update configuration."""
        try:
            # Get existing config
            existing_config = await self.config_repo.get_config_by_id(config_id, tenant_id)
            if not existing_config:
                return None
            
            # Validate value if being updated
            if config_data.value is not None:
                config_type = config_data.type or existing_config["type"]
                self._validate_config_value(config_data.value, config_type)
            
            # Prepare update data
            update_data = config_data.dict(exclude_unset=True)
            update_data["updated_by"] = updated_by
            
            # Update config
            config = await self.config_repo.update_config(config_id, tenant_id, update_data)
            
            if config:
                # Invalidate cache
                await self._invalidate_cache(config["key"], tenant_id, config["environment"])
                
                # Convert value based on type
                config["value"] = self._convert_value(config["value"], config["type"])
                
                logger.info(f"Configuration '{config['key']}' updated successfully")
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to update config {config_id}: {str(e)}")
            raise
    
    async def delete_config(self, config_id: str, tenant_id: str) -> bool:
        """Delete configuration."""
        try:
            # Get config before deletion for cache invalidation
            config = await self.config_repo.get_config_by_id(config_id, tenant_id)
            
            success = await self.config_repo.delete_config(config_id, tenant_id)
            
            if success and config:
                # Invalidate cache
                await self._invalidate_cache(config["key"], tenant_id, config["environment"])
                
                logger.info(f"Configuration '{config['key']}' deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete config {config_id}: {str(e)}")
            return False
    
    async def list_configs(self, tenant_id: str, environment: str = "default", skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List configurations for tenant."""
        try:
            configs = await self.config_repo.list_configs(tenant_id, environment, skip, limit)
            
            # Convert values based on types
            for config in configs:
                config["value"] = self._convert_value(config["value"], config["type"])
            
            return configs
            
        except Exception as e:
            logger.error(f"Failed to list configs for tenant {tenant_id}: {str(e)}")
            return []
    
    async def get_configs_by_keys(self, keys: List[str], tenant_id: str, environment: str = "default") -> List[Dict[str, Any]]:
        """Get multiple configurations by keys."""
        try:
            configs = await self.config_repo.get_configs_by_keys(keys, tenant_id, environment)
            
            # Convert values based on types
            for config in configs:
                config["value"] = self._convert_value(config["value"], config["type"])
            
            return configs
            
        except Exception as e:
            logger.error(f"Failed to get configs by keys: {str(e)}")
            return []
    
    def _validate_config_value(self, value: str, config_type: str) -> None:
        """Validate configuration value based on type."""
        try:
            if config_type == "number":
                float(value)
            elif config_type == "boolean":
                if value.lower() not in ["true", "false", "1", "0"]:
                    raise ValueError("Boolean value must be true/false or 1/0")
            elif config_type == "json":
                json.loads(value)
            # string type doesn't need validation
        except (ValueError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid value for type '{config_type}': {str(e)}")
    
    def _convert_value(self, value: str, config_type: str) -> Any:
        """Convert string value to appropriate type."""
        try:
            if config_type == "number":
                return float(value)
            elif config_type == "boolean":
                return value.lower() in ["true", "1"]
            elif config_type == "json":
                return json.loads(value)
            else:
                return value
        except (ValueError, json.JSONDecodeError):
            # Return original value if conversion fails
            return value
    
    async def _invalidate_cache(self, key: str, tenant_id: str, environment: str) -> None:
        """Invalidate cache for configuration."""
        try:
            cache_key = f"config:{tenant_id}:{environment}:{key}"
            await self.redis_client.delete(cache_key)
            logger.debug(f"Cache invalidated for config '{key}'")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache for config '{key}': {str(e)}") 