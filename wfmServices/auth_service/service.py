"""
Business logic layer for Authentication & Authorization Service.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import structlog
from shared.auth import verify_password, get_password_hash, create_access_token
from .repository import UserRepository, RoleRepository, PermissionRepository, TenantRepository
from .models import UserCreate, UserUpdate, RoleCreate, RoleUpdate, TenantCreate

logger = structlog.get_logger(__name__)


class AuthService:
    """Authentication and authorization service."""
    
    def __init__(self, user_repo: UserRepository, role_repo: RoleRepository, tenant_repo: TenantRepository):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.tenant_repo = tenant_repo
    
    async def authenticate_user(self, username: str, password: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username/password."""
        try:
            # Get user by username and tenant
            user = await self.user_repo.get_user_by_username(username, tenant_id)
            
            if not user:
                logger.warning(f"Authentication failed: user {username} not found in tenant {tenant_id}")
                return None
            
            # Check if user is active
            if user["status"] != "active":
                logger.warning(f"Authentication failed: user {username} is not active")
                return None
            
            # Check if user is locked
            if user.get("locked_until") and user["locked_until"] > datetime.utcnow():
                logger.warning(f"Authentication failed: user {username} is locked")
                return None
            
            # Verify password
            if not verify_password(password, user["password_hash"]):
                # Increment failed login attempts
                failed_attempts = user.get("failed_login_attempts", 0) + 1
                locked_until = None
                
                # Lock account after 5 failed attempts for 30 minutes
                if failed_attempts >= 5:
                    locked_until = datetime.utcnow() + timedelta(minutes=30)
                
                await self.user_repo.update_login_attempts(user["id"], tenant_id, failed_attempts, locked_until)
                
                logger.warning(f"Authentication failed: invalid password for user {username}")
                return None
            
            # Reset failed login attempts on successful login
            await self.user_repo.update_last_login(user["id"], tenant_id)
            
            # Get user roles and permissions
            roles = await self._get_user_roles(user["role_ids"], tenant_id)
            permissions = await self._get_user_permissions(roles, tenant_id)
            
            return {
                "user_id": user["id"],
                "tenant_id": user["tenant_id"],
                "username": user["username"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "roles": [role["name"] for role in roles],
                "permissions": [perm["name"] for perm in permissions]
            }
            
        except Exception as e:
            logger.error(f"Authentication error for user {username}: {str(e)}")
            return None
    
    async def create_user(self, user_data: UserCreate, created_by: str) -> Dict[str, Any]:
        """Create a new user."""
        try:
            # Check if username already exists in tenant
            existing_user = await self.user_repo.get_user_by_username(user_data.username, user_data.tenant_id)
            if existing_user:
                raise ValueError(f"Username {user_data.username} already exists in this tenant")
            
            # Check if email already exists in tenant
            existing_email = await self.user_repo.get_user_by_email(user_data.email, user_data.tenant_id)
            if existing_email:
                raise ValueError(f"Email {user_data.email} already exists in this tenant")
            
            # Hash password
            password_hash = get_password_hash(user_data.password)
            
            # Prepare user data
            user_dict = user_data.dict()
            user_dict["password_hash"] = password_hash
            user_dict["created_by"] = created_by
            user_dict["updated_by"] = created_by
            
            # Remove password from dict
            del user_dict["password"]
            
            # Create user
            user = await self.user_repo.create_user(user_dict)
            
            logger.info(f"User {user_data.username} created successfully in tenant {user_data.tenant_id}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to create user {user_data.username}: {str(e)}")
            raise
    
    async def get_user(self, user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            user = await self.user_repo.get_user_by_id(user_id, tenant_id)
            
            if user:
                # Get user roles and permissions
                roles = await self._get_user_roles(user["role_ids"], tenant_id)
                permissions = await self._get_user_permissions(roles, tenant_id)
                
                user["roles"] = roles
                user["permissions"] = [perm["name"] for perm in permissions]
                
                # Remove sensitive data
                del user["password_hash"]
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {str(e)}")
            return None
    
    async def update_user(self, user_id: str, tenant_id: str, user_data: UserUpdate, updated_by: str) -> Optional[Dict[str, Any]]:
        """Update user."""
        try:
            # Check if user exists
            existing_user = await self.user_repo.get_user_by_id(user_id, tenant_id)
            if not existing_user:
                return None
            
            # Check username uniqueness if being updated
            if user_data.username:
                existing_username = await self.user_repo.get_user_by_username(user_data.username, tenant_id)
                if existing_username and existing_username["id"] != user_id:
                    raise ValueError(f"Username {user_data.username} already exists in this tenant")
            
            # Check email uniqueness if being updated
            if user_data.email:
                existing_email = await self.user_repo.get_user_by_email(user_data.email, tenant_id)
                if existing_email and existing_email["id"] != user_id:
                    raise ValueError(f"Email {user_data.email} already exists in this tenant")
            
            # Prepare update data
            update_data = user_data.dict(exclude_unset=True)
            update_data["updated_by"] = updated_by
            
            # Update user
            user = await self.user_repo.update_user(user_id, tenant_id, update_data)
            
            if user:
                logger.info(f"User {user_id} updated successfully")
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            raise
    
    async def delete_user(self, user_id: str, tenant_id: str) -> bool:
        """Delete user."""
        try:
            success = await self.user_repo.delete_user(user_id, tenant_id)
            
            if success:
                logger.info(f"User {user_id} deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            return False
    
    async def list_users(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List users for tenant."""
        try:
            users = await self.user_repo.list_users(tenant_id, skip, limit)
            
            # Remove sensitive data and add roles/permissions
            for user in users:
                del user["password_hash"]
                
                # Get user roles and permissions
                roles = await self._get_user_roles(user["role_ids"], tenant_id)
                permissions = await self._get_user_permissions(roles, tenant_id)
                
                user["roles"] = roles
                user["permissions"] = [perm["name"] for perm in permissions]
            
            return users
            
        except Exception as e:
            logger.error(f"Failed to list users for tenant {tenant_id}: {str(e)}")
            return []
    
    async def create_access_token_for_user(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token for user."""
        try:
            token_data = {
                "sub": user_data["user_id"],
                "tenant_id": user_data["tenant_id"],
                "username": user_data["username"],
                "email": user_data["email"],
                "roles": user_data["roles"],
                "permissions": user_data["permissions"]
            }
            
            return create_access_token(token_data)
            
        except Exception as e:
            logger.error(f"Failed to create access token for user {user_data['user_id']}: {str(e)}")
            raise
    
    async def _get_user_roles(self, role_ids: List[str], tenant_id: str) -> List[Dict[str, Any]]:
        """Get user roles."""
        if not role_ids:
            return []
        
        try:
            roles = await self.role_repo.get_roles_by_ids(role_ids, tenant_id)
            return [role for role in roles if role["status"] == "active"]
        except Exception as e:
            logger.error(f"Failed to get user roles: {str(e)}")
            return []
    
    async def _get_user_permissions(self, roles: List[Dict[str, Any]], tenant_id: str) -> List[Dict[str, Any]]:
        """Get user permissions from roles."""
        if not roles:
            return []
        
        try:
            # Collect all permission IDs from roles
            permission_ids = []
            for role in roles:
                permission_ids.extend(role.get("permission_ids", []))
            
            # Remove duplicates
            permission_ids = list(set(permission_ids))
            
            if not permission_ids:
                return []
            
            # Get permissions
            permissions = await self._get_permissions_by_ids(permission_ids, tenant_id)
            return permissions
            
        except Exception as e:
            logger.error(f"Failed to get user permissions: {str(e)}")
            return []
    
    async def _get_permissions_by_ids(self, permission_ids: List[str], tenant_id: str) -> List[Dict[str, Any]]:
        """Get permissions by IDs."""
        try:
            permission_repo = PermissionRepository(self.user_repo.database)
            return await permission_repo.get_permissions_by_ids(permission_ids, tenant_id)
        except Exception as e:
            logger.error(f"Failed to get permissions by IDs: {str(e)}")
            return [] 