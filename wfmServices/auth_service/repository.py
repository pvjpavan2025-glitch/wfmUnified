"""
Repository layer for Authentication & Authorization Service.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import motor.motor_asyncio
import structlog
from bson import ObjectId
from .models import User, Role, Permission, Tenant

logger = structlog.get_logger(__name__)


class BaseRepository:
    """Base repository with common operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        self.database = database
    
    def _convert_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string for all ObjectId fields."""
        converted_data = {}
        for key, value in data.items():
            if key == "_id":
                # Special case: convert _id to id
                converted_data["id"] = str(value)
            elif isinstance(value, ObjectId):
                converted_data[key] = str(value)
            elif isinstance(value, dict):
                converted_data[key] = self._convert_id(value)
            elif isinstance(value, list):
                converted_data[key] = [self._convert_id(item) if isinstance(item, dict) else str(item) if isinstance(item, ObjectId) else item for item in value]
            else:
                converted_data[key] = value
        return converted_data
    
    def _prepare_for_db(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for database storage."""
        if "id" in data and data["id"]:
            data["_id"] = ObjectId(data["id"])
            del data["id"]
        return data


class UserRepository(BaseRepository):
    """Repository for user operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        super().__init__(database)
        self.collection = database.users
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        try:
            user_data["created_at"] = datetime.utcnow()
            user_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(user_data)
            user_data["_id"] = result.inserted_id
            
            return self._convert_id(user_data)
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise
    
    async def get_user_by_id(self, user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID and tenant."""
        try:
            user = await self.collection.find_one({
                "_id": ObjectId(user_id),
                "tenant_id": ObjectId(tenant_id)
            })
            
            if user:
                return self._convert_id(user)
            return None
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {str(e)}")
            return None
    
    async def get_user_by_username(self, username: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get user by username and tenant."""
        try:
            # Convert tenant_id string to ObjectId
            tenant_object_id = ObjectId(tenant_id) if isinstance(tenant_id, str) else tenant_id
            
            user = await self.collection.find_one({
                "username": username,
                "tenant_id": tenant_object_id
            })
            
            if user:
                return self._convert_id(user)
            return None
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {str(e)}")
            return None
    
    async def get_user_by_email(self, email: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get user by email and tenant."""
        try:
            # Convert tenant_id string to ObjectId
            tenant_object_id = ObjectId(tenant_id) if isinstance(tenant_id, str) else tenant_id
            
            user = await self.collection.find_one({
                "email": email,
                "tenant_id": tenant_object_id
            })
            
            if user:
                return self._convert_id(user)
            return None
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {str(e)}")
            return None
    
    async def update_user(self, user_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id), "tenant_id": ObjectId(tenant_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_user_by_id(user_id, tenant_id)
            return None
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            return None
    
    async def delete_user(self, user_id: str, tenant_id: str) -> bool:
        """Delete user."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(user_id),
                "tenant_id": ObjectId(tenant_id)
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            return False
    
    async def list_users(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List users for tenant."""
        try:
            cursor = self.collection.find({"tenant_id": ObjectId(tenant_id)}).skip(skip).limit(limit)
            users = await cursor.to_list(length=limit)
            
            return [self._convert_id(user) for user in users]
        except Exception as e:
            logger.error(f"Failed to list users for tenant {tenant_id}: {str(e)}")
            return []
    
    async def update_login_attempts(self, user_id: str, tenant_id: str, failed_attempts: int, locked_until: Optional[datetime] = None) -> bool:
        """Update user login attempts."""
        try:
            update_data = {
                "failed_login_attempts": failed_attempts,
                "updated_at": datetime.utcnow()
            }
            
            if locked_until:
                update_data["locked_until"] = locked_until
            
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id), "tenant_id": ObjectId(tenant_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update login attempts for user {user_id}: {str(e)}")
            return False
    
    async def update_last_login(self, user_id: str, tenant_id: str) -> bool:
        """Update user last login time."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id), "tenant_id": ObjectId(tenant_id)},
                {
                    "$set": {
                        "last_login": datetime.utcnow(),
                        "failed_login_attempts": 0,
                        "locked_until": None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update last login for user {user_id}: {str(e)}")
            return False


class RoleRepository(BaseRepository):
    """Repository for role operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        super().__init__(database)
        self.collection = database.roles
    
    async def create_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new role."""
        try:
            role_data["created_at"] = datetime.utcnow()
            role_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(role_data)
            role_data["_id"] = result.inserted_id
            
            return self._convert_id(role_data)
        except Exception as e:
            logger.error(f"Failed to create role: {str(e)}")
            raise
    
    async def get_role_by_id(self, role_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get role by ID and tenant."""
        try:
            role = await self.collection.find_one({
                "_id": ObjectId(role_id),
                "tenant_id": ObjectId(tenant_id)
            })
            
            if role:
                return self._convert_id(role)
            return None
        except Exception as e:
            logger.error(f"Failed to get role {role_id}: {str(e)}")
            return None
    
    async def update_role(self, role_id: str, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update role."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(role_id), "tenant_id": ObjectId(tenant_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_role_by_id(role_id, tenant_id)
            return None
        except Exception as e:
            logger.error(f"Failed to update role {role_id}: {str(e)}")
            return None
    
    async def delete_role(self, role_id: str, tenant_id: str) -> bool:
        """Delete role."""
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(role_id),
                "tenant_id": ObjectId(tenant_id)
            })
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete role {role_id}: {str(e)}")
            return False
    
    async def list_roles(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List roles for tenant."""
        try:
            cursor = self.collection.find({"tenant_id": ObjectId(tenant_id)}).skip(skip).limit(limit)
            roles = await cursor.to_list(length=limit)
            
            return [self._convert_id(role) for role in roles]
        except Exception as e:
            logger.error(f"Failed to list roles for tenant {tenant_id}: {str(e)}")
            return []
    
    async def get_roles_by_ids(self, role_ids: List[str], tenant_id: str) -> List[Dict[str, Any]]:
        """Get roles by IDs."""
        try:
            object_ids = [ObjectId(role_id) for role_id in role_ids]
            cursor = self.collection.find({
                "_id": {"$in": object_ids},
                "tenant_id": ObjectId(tenant_id)
            })
            
            roles = await cursor.to_list(length=len(role_ids))
            return [self._convert_id(role) for role in roles]
        except Exception as e:
            logger.error(f"Failed to get roles by IDs: {str(e)}")
            return []


class PermissionRepository(BaseRepository):
    """Repository for permission operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        super().__init__(database)
        self.collection = database.permissions
    
    async def create_permission(self, permission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new permission."""
        try:
            permission_data["created_at"] = datetime.utcnow()
            permission_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(permission_data)
            permission_data["_id"] = result.inserted_id
            
            return self._convert_id(permission_data)
        except Exception as e:
            logger.error(f"Failed to create permission: {str(e)}")
            raise
    
    async def get_permission_by_id(self, permission_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get permission by ID and tenant."""
        try:
            permission = await self.collection.find_one({
                "_id": ObjectId(permission_id),
                "tenant_id": ObjectId(tenant_id)
            })
            
            if permission:
                return self._convert_id(permission)
            return None
        except Exception as e:
            logger.error(f"Failed to get permission {permission_id}: {str(e)}")
            return None
    
    async def get_permissions_by_ids(self, permission_ids: List[str], tenant_id: str) -> List[Dict[str, Any]]:
        """Get permissions by IDs."""
        try:
            object_ids = [ObjectId(permission_id) for permission_id in permission_ids]
            cursor = self.collection.find({
                "_id": {"$in": object_ids},
                "tenant_id": ObjectId(tenant_id)
            })
            
            permissions = await cursor.to_list(length=len(permission_ids))
            return [self._convert_id(permission) for permission in permissions]
        except Exception as e:
            logger.error(f"Failed to get permissions by IDs: {str(e)}")
            return []


class TenantRepository(BaseRepository):
    """Repository for tenant operations."""
    
    def __init__(self, database: motor.motor_asyncio.AsyncIOMotorDatabase):
        super().__init__(database)
        self.collection = database.tenants
    
    async def create_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tenant."""
        try:
            tenant_data["created_at"] = datetime.utcnow()
            tenant_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(tenant_data)
            tenant_data["_id"] = result.inserted_id
            
            return self._convert_id(tenant_data)
        except Exception as e:
            logger.error(f"Failed to create tenant: {str(e)}")
            raise
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID."""
        try:
            tenant = await self.collection.find_one({"_id": ObjectId(tenant_id)})
            
            if tenant:
                return self._convert_id(tenant)
            return None
        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {str(e)}")
            return None
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get tenant by domain."""
        try:
            tenant = await self.collection.find_one({"domain": domain})
            
            if tenant:
                return self._convert_id(tenant)
            return None
        except Exception as e:
            logger.error(f"Failed to get tenant by domain {domain}: {str(e)}")
            return None 