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
    
    async def get_all_rules(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all rules for tenant, regardless of status."""
        try:
            logger.info(f"Getting all rules for tenant: {tenant_id}")
            
            # Log the collection name and connection status
            logger.info(f"Using collection: {self.collection.name}")
            
            # Log the query being executed
            query = {"tenant_id": tenant_id}
            logger.info(f"Executing query: {query}")
            
            # Get the count of matching documents
            count = await self.collection.count_documents(query)
            logger.info(f"Found {count} total rules for tenant {tenant_id}")
            
            # Execute the query
            cursor = self.collection.find(query)
            rules = await cursor.to_list(length=1000)
            
            # Log the number of rules found
            logger.info(f"Retrieved {len(rules)} total rules for tenant {tenant_id}")
            
            # Log the first few rules for debugging
            for i, rule in enumerate(rules[:5], 1):
                logger.info(f"Rule {i}: ID={rule.get('_id')}, Name='{rule.get('name')}', "
                           f"Status='{rule.get('status')}', Category='{rule.get('category')}', "
                           f"Tenant='{rule.get('tenant_id')}'")
            
            # Convert ObjectId to string
            result = [self._convert_id(rule) for rule in rules]
            return result
            
        except Exception as e:
            logger.error(f"Failed to get all rules for tenant {tenant_id}: {str(e)}", exc_info=True)
            return []
            
    async def get_active_rules(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all active rules for tenant."""
        try:
            logger.info(f"[REPOSITORY] Getting active rules for tenant: {tenant_id}")
            
            # Ensure tenant_id is not None or empty
            if not tenant_id or tenant_id == "default":
                tenant_id = "test-tenant"
                logger.warning(f"[REPOSITORY] No tenant_id provided or using default, using: {tenant_id}")
            
            # Log the collection name and connection status
            if not hasattr(self, 'collection'):
                logger.error("[REPOSITORY] Collection not initialized in rules repository")
                return []
                
            logger.info(f"[REPOSITORY] Using collection: {self.collection.name}")
            
            # Log database stats for debugging
            try:
                db_stats = await self.database.command('dbstats')
                logger.info(f"[REPOSITORY] Database stats: {db_stats}")
                
                # List all collections in the database
                collections = await self.database.list_collection_names()
                logger.info(f"[REPOSITORY] Available collections: {collections}")
                
                # Get count of all rules in the collection (for debugging)
                total_rules = await self.collection.count_documents({})
                logger.info(f"[REPOSITORY] Total rules in collection: {total_rules}")
                
                # Get count of rules for this tenant (regardless of status)
                tenant_rule_count = await self.collection.count_documents({"tenant_id": tenant_id})
                logger.info(f"[REPOSITORY] Total rules for tenant {tenant_id}: {tenant_rule_count}")
                
            except Exception as e:
                logger.error(f"[REPOSITORY] Error getting database stats: {str(e)}")
            
            # Log the query being executed
            query = {
                "tenant_id": tenant_id,
                "status": "active"
            }
            logger.info(f"[REPOSITORY] Executing query: {query}")
            
            try:
                # Get the count of matching documents
                count = await self.collection.count_documents(query)
                logger.info(f"[REPOSITORY] Found {count} active rules for tenant {tenant_id}")
                
                # Execute the query
                cursor = self.collection.find(query)
                rules = await cursor.to_list(length=1000)
                
                # Log the number of rules found
                logger.info(f"[REPOSITORY] Retrieved {len(rules)} active rules for tenant {tenant_id}")
                
                # Log the first few rules for debugging
                for i, rule in enumerate(rules[:3], 1):
                    logger.info(f"[REPOSITORY] Rule {i}: ID={rule.get('_id')}, "
                               f"Name='{rule.get('name')}', "
                               f"Status='{rule.get('status')}', "
                               f"Category='{rule.get('category')}', "
                               f"Tenant='{rule.get('tenant_id')}'")
                
                # If no rules found, try to find out why
                if not rules:
                    logger.warning(f"[REPOSITORY] No active rules found for tenant {tenant_id}")
                    
                    # Check if collection is empty
                    total_count = await self.collection.count_documents({})
                    logger.info(f"[REPOSITORY] Total rules in collection: {total_count}")
                    
                    # Check if there are any rules for this tenant (regardless of status)
                    tenant_rules_count = await self.collection.count_documents({"tenant_id": tenant_id})
                    logger.info(f"[REPOSITORY] Total rules for tenant {tenant_id}: {tenant_rules_count}")
                    
                    # Get a sample of rules to see what tenant_ids exist
                    sample = await self.collection.find({}).limit(5).to_list(length=5)
                    for i, rule in enumerate(sample, 1):
                        logger.info(f"[REPOSITORY] Sample rule {i}: Tenant='{rule.get('tenant_id')}', "
                                   f"Status='{rule.get('status')}', Name='{rule.get('name')}'")
                
                # Convert ObjectId to string
                result = [self._convert_id(rule) for rule in rules]
                return result
                
            except Exception as query_error:
                logger.error(f"[REPOSITORY] Query execution failed: {str(query_error)}", exc_info=True)
                return []
            
        except Exception as e:
            logger.error(f"[REPOSITORY] Failed to get active rules for tenant {tenant_id}: {str(e)}", exc_info=True)
            return [] 