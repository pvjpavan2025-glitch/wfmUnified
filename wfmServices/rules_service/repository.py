"""
Repository layer for Rules Engine Service.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import motor.motor_asyncio
import structlog
from bson import ObjectId
from .models import Rule

logger = structlog.get_logger(__name__)


class RulesRepository:
    """Repository for rules operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.rules
    
    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string."""
        if "_id" in data:
            data["id"] = str(data["_id"])
            del data["_id"]
        return data
    
    async def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new rule."""
        try:
            rule_data["created_at"] = datetime.utcnow()
            rule_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(rule_data)
            rule_data["_id"] = result.inserted_id
            
            return self._convert_id(rule_data)
        except Exception as e:
            logger.error(f"Failed to create rule: {str(e)}")
            raise
    
    async def get_rule_by_id(self, rule_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get rule by ID and tenant."""
        try:
            rule = await self.collection.find_one({
                "_id": ObjectId(rule_id),
                "tenant_id": tenant_id
            })
            
            if rule:
                return self._convert_id(rule)
            return None
        except Exception as e:
            logger.error(f"Failed to get rule {rule_id}: {str(e)}")
            return None
    
    async def get_rule_by_name(self, name: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get rule by name and tenant."""
        try:
            rule = await self.collection.find_one({
                "name": name,
                "tenant_id": tenant_id
            })
            
            if rule:
                return self._convert_id(rule)
            return None
        except Exception as e:
            logger.error(f"Failed to get rule by name {name}: {str(e)}")
            return None
    
    async def update_rule(self, rule_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update rule."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(rule_id), "tenant_id": tenant_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_rule_by_id(rule_id, tenant_id)
            return None
        except Exception as e:
            logger.error(f"Failed to update rule {rule_id}: {str(e)}")
            return None
    
    async def delete_rule(self, rule_id: str, tenant_id: str) -> bool:
        """Delete rule."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(rule_id),
                "tenant_id": tenant_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete rule {rule_id}: {str(e)}")
            return False
    
    async def list_rules(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List rules for tenant."""
        try:
            cursor = self.collection.find({"tenant_id": tenant_id}).skip(skip).limit(limit)
            rules = await cursor.to_list(length=limit)
            
            return [self._convert_id(rule) for rule in rules]
        except Exception as e:
            logger.error(f"Failed to list rules for tenant {tenant_id}: {str(e)}")
            return []
    
    async def get_rules_by_ids(self, rule_ids: List[str], tenant_id: str) -> List[Dict[str, Any]]:
        """Get rules by IDs."""
        try:
            object_ids = [ObjectId(rule_id) for rule_id in rule_ids]
            cursor = self.collection.find({
                "_id": {"$in": object_ids},
                "tenant_id": tenant_id
            })
            
            rules = await cursor.to_list(length=len(rule_ids))
            return [self._convert_id(rule) for rule in rules]
        except Exception as e:
            logger.error(f"Failed to get rules by IDs: {str(e)}")
            return []
    
    async def get_rules_by_category(self, category: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Get rules by category."""
        try:
            cursor = self.collection.find({
                "category": category,
                "tenant_id": tenant_id
            })
            
            rules = await cursor.to_list(length=1000)
            return [self._convert_id(rule) for rule in rules]
        except Exception as e:
            logger.error(f"Failed to get rules by category {category}: {str(e)}")
            return []
    
    async def get_active_rules(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all active rules for tenant."""
        try:
            cursor = self.collection.find({
                "tenant_id": tenant_id,
                "status": "active"
            })
            
            rules = await cursor.to_list(length=1000)
            return [self._convert_id(rule) for rule in rules]
        except Exception as e:
            logger.error(f"Failed to get active rules for tenant {tenant_id}: {str(e)}")
            return [] 