"""
Authentication utilities for WFM microservices.
"""
import jwt
import time
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Token data model."""
    user_id: str
    username: str
    tenant_id: str
    roles: list
    exp: datetime


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    username: str
    tenant_id: str
    roles: list


class TokenManager:
    """Manages JWT token creation, validation, and refresh."""
    
    def __init__(self):
        self.secret_key = settings.security.jwt_secret_key
        self.algorithm = settings.security.jwt_algorithm
        self.access_token_expire_minutes = settings.security.jwt_expiration_minutes
        self.refresh_token_expire_days = 30
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create an access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Created access token for user {data.get('username', 'unknown')}")
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Created refresh token for user {data.get('username', 'unknown')}")
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode a token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_type = payload.get("type")
            
            if token_type not in ["access", "refresh"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            user_id: str = payload.get("user_id")
            username: str = payload.get("username")
            tenant_id: str = payload.get("tenant_id")
            roles: list = payload.get("roles", [])
            exp: datetime = payload.get("exp")
            
            if user_id is None or username is None or tenant_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            return TokenData(
                user_id=user_id,
                username=username,
                tenant_id=tenant_id,
                roles=roles,
                exp=datetime.fromtimestamp(exp)
            )
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh an access token using a refresh token."""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            token_type = payload.get("type")
            
            if token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            user_id: str = payload.get("user_id")
            username: str = payload.get("username")
            tenant_id: str = payload.get("tenant_id")
            roles: list = payload.get("roles", [])
            
            if user_id is None or username is None or tenant_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token payload"
                )
            
            # Create new access token
            access_token_data = {
                "user_id": user_id,
                "username": username,
                "tenant_id": tenant_id,
                "roles": roles
            }
            
            new_access_token = self.create_access_token(access_token_data)
            new_refresh_token = self.create_refresh_token(access_token_data)
            
            logger.info(f"Refreshed tokens for user {username}")
            
            return TokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_in=self.access_token_expire_minutes * 60,
                user_id=user_id,
                username=username,
                tenant_id=tenant_id,
                roles=roles
            )
            
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        except jwt.InvalidTokenError:
            logger.warning("Invalid refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )


# Global token manager instance
token_manager = TokenManager()


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt_rounds = settings.security.bcrypt_rounds
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=salt_rounds)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False


def create_access_token(data: Dict[str, Any]) -> str:
    """Create an access token using the global token manager."""
    return token_manager.create_access_token(data)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """Get current user from token."""
    token = credentials.credentials
    return token_manager.verify_token(token)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_security),
) -> Optional[TokenData]:
    """Get current user from token (optional)."""
    if not credentials:
        return None
    try:
        return token_manager.verify_token(credentials.credentials)
    except HTTPException:
        return None


def require_roles(required_roles: list):
    """Decorator to require specific roles."""
    def decorator(func):
        async def wrapper(current_user: TokenData = Depends(get_current_user), *args, **kwargs):
            user_roles = set(current_user.roles)
            required_roles_set = set(required_roles)
            
            if not user_roles.intersection(required_roles_set):
                logger.warning(f"User {current_user.username} lacks required roles: {required_roles}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(current_user, *args, **kwargs)
        return wrapper
    return decorator


def require_tenant_access():
    """Decorator to require tenant access."""
    def decorator(func):
        async def wrapper(current_user: TokenData = Depends(get_current_user), *args, **kwargs):
            if not current_user.tenant_id:
                logger.warning(f"User {current_user.username} has no tenant access")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tenant access required"
                )
            
            return await func(current_user, *args, **kwargs)
        return wrapper
    return decorator 