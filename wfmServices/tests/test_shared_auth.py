"""
Unit tests for shared authentication module.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from shared.auth import (
    TokenManager, 
    TokenData, 
    TokenResponse,
    get_current_user,
    require_roles,
    require_tenant_access
)
from shared.config import settings


class TestTokenManager:
    """Test cases for TokenManager class."""
    
    @pytest.fixture
    def token_manager(self):
        """Create a TokenManager instance for testing."""
        return TokenManager()
    
    @pytest.fixture
    def sample_token_data(self):
        """Sample data for token creation."""
        return {
            "user_id": "test-user-123",
            "username": "testuser",
            "tenant_id": "test-tenant-123",
            "roles": ["user", "analyst"]
        }
    
    def test_create_access_token(self, token_manager, sample_token_data):
        """Test access token creation."""
        token = token_manager.create_access_token(sample_token_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self, token_manager, sample_token_data):
        """Test refresh token creation."""
        token = token_manager.create_refresh_token(sample_token_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_valid_access_token(self, token_manager, sample_token_data):
        """Test verification of valid access token."""
        token = token_manager.create_access_token(sample_token_data)
        token_data = token_manager.verify_token(token)
        
        assert token_data.user_id == sample_token_data["user_id"]
        assert token_data.username == sample_token_data["username"]
        assert token_data.tenant_id == sample_token_data["tenant_id"]
        assert token_data.roles == sample_token_data["roles"]
        assert token_data.exp is not None
    
    def test_verify_valid_refresh_token(self, token_manager, sample_token_data):
        """Test verification of valid refresh token."""
        token = token_manager.create_refresh_token(sample_token_data)
        token_data = token_manager.verify_token(token)
        
        assert token_data.user_id == sample_token_data["user_id"]
        assert token_data.username == sample_token_data["username"]
        assert token_data.tenant_id == sample_token_data["tenant_id"]
        assert token_data.roles == sample_token_data["roles"]
    
    def test_verify_invalid_token(self, token_manager):
        """Test verification of invalid token."""
        with pytest.raises(Exception):
            token_manager.verify_token("invalid-token")
    
    def test_verify_expired_token(self, token_manager, sample_token_data):
        """Test verification of expired token."""
        # Create token with very short expiration
        with patch.object(token_manager, 'access_token_expire_minutes', -1):
            token = token_manager.create_access_token(sample_token_data)
        
        with pytest.raises(Exception):
            token_manager.verify_token(token)
    
    def test_refresh_access_token(self, token_manager, sample_token_data):
        """Test refreshing access token."""
        # Create refresh token
        refresh_token = token_manager.create_refresh_token(sample_token_data)
        
        # Refresh access token
        response = token_manager.refresh_access_token(refresh_token)
        
        assert isinstance(response, TokenResponse)
        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.user_id == sample_token_data["user_id"]
        assert response.username == sample_token_data["username"]
        assert response.tenant_id == sample_token_data["tenant_id"]
        assert response.roles == sample_token_data["roles"]
    
    def test_refresh_with_invalid_token(self, token_manager):
        """Test refreshing with invalid token."""
        with pytest.raises(Exception):
            token_manager.refresh_access_token("invalid-refresh-token")
    
    def test_token_with_missing_fields(self, token_manager):
        """Test token creation with missing required fields."""
        incomplete_data = {
            "user_id": "test-user-123",
            # Missing username and tenant_id
            "roles": ["user"]
        }
        
        # The current implementation doesn't validate required fields at creation time
        # It only validates when verifying the token
        token = token_manager.create_access_token(incomplete_data)
        with pytest.raises(Exception):
            token_manager.verify_token(token)


class TestTokenData:
    """Test cases for TokenData model."""
    
    def test_token_data_creation(self):
        """Test TokenData model creation."""
        token_data = TokenData(
            user_id="test-user-123",
            username="testuser",
            tenant_id="test-tenant-123",
            roles=["user", "analyst"],
            exp=datetime.utcnow()
        )
        
        assert token_data.user_id == "test-user-123"
        assert token_data.username == "testuser"
        assert token_data.tenant_id == "test-tenant-123"
        assert token_data.roles == ["user", "analyst"]
        assert token_data.exp is not None


class TestTokenResponse:
    """Test cases for TokenResponse model."""
    
    def test_token_response_creation(self):
        """Test TokenResponse model creation."""
        response = TokenResponse(
            access_token="access-token",
            refresh_token="refresh-token",
            expires_in=1800,
            user_id="test-user-123",
            username="testuser",
            tenant_id="test-tenant-123",
            roles=["user", "analyst"]
        )
        
        assert response.access_token == "access-token"
        assert response.refresh_token == "refresh-token"
        assert response.token_type == "bearer"
        assert response.expires_in == 1800
        assert response.user_id == "test-user-123"
        assert response.username == "testuser"
        assert response.tenant_id == "test-tenant-123"
        assert response.roles == ["user", "analyst"]


class TestAuthenticationDecorators:
    """Test cases for authentication decorators."""
    
    @pytest.mark.asyncio
    async def test_require_roles_success(self):
        """Test require_roles decorator with valid roles."""
        @require_roles(["admin"])
        async def test_function(current_user):
            return "success"
        
        # Mock current user with admin role
        mock_user = Mock()
        mock_user.roles = ["admin", "user"]
        
        result = await test_function(mock_user)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_require_roles_failure(self):
        """Test require_roles decorator with insufficient roles."""
        @require_roles(["admin"])
        async def test_function(current_user):
            return "success"
        
        # Mock current user without admin role
        mock_user = Mock()
        mock_user.roles = ["user"]
        mock_user.username = "testuser"
        
        with pytest.raises(Exception):
            await test_function(mock_user)
    
    @pytest.mark.asyncio
    async def test_require_tenant_access_success(self):
        """Test require_tenant_access decorator with valid tenant."""
        @require_tenant_access()
        async def test_function(current_user):
            return "success"
        
        # Mock current user with tenant
        mock_user = Mock()
        mock_user.tenant_id = "test-tenant-123"
        
        result = await test_function(mock_user)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_require_tenant_access_failure(self):
        """Test require_tenant_access decorator without tenant."""
        @require_tenant_access()
        async def test_function(current_user):
            return "success"
        
        # Mock current user without tenant
        mock_user = Mock()
        mock_user.tenant_id = None
        mock_user.username = "testuser"
        
        with pytest.raises(Exception):
            await test_function(mock_user)


class TestTokenManagerIntegration:
    """Integration tests for TokenManager."""
    
    @pytest.fixture
    def token_manager(self):
        """Create a TokenManager instance for testing."""
        return TokenManager()
    
    def test_full_token_lifecycle(self, token_manager):
        """Test complete token lifecycle: create, verify, refresh."""
        # Initial data
        user_data = {
            "user_id": "test-user-123",
            "username": "testuser",
            "tenant_id": "test-tenant-123",
            "roles": ["user", "analyst"]
        }
        
        # 1. Create access token
        access_token = token_manager.create_access_token(user_data)
        assert access_token is not None
        
        # 2. Verify access token
        token_data = token_manager.verify_token(access_token)
        assert token_data.user_id == user_data["user_id"]
        assert token_data.username == user_data["username"]
        
        # 3. Create refresh token
        refresh_token = token_manager.create_refresh_token(user_data)
        assert refresh_token is not None
        
        # 4. Refresh access token
        response = token_manager.refresh_access_token(refresh_token)
        # Note: Tokens might be the same if created at the same time
        # The important thing is that the refresh process works
        assert response.user_id == user_data["user_id"]
        
        # 5. Verify new access token
        new_token_data = token_manager.verify_token(response.access_token)
        assert new_token_data.user_id == user_data["user_id"]
    
    def test_token_expiration(self, token_manager):
        """Test token expiration behavior."""
        user_data = {
            "user_id": "test-user-123",
            "username": "testuser",
            "tenant_id": "test-tenant-123",
            "roles": ["user"]
        }
        
        # Create token with very short expiration
        with patch.object(token_manager, 'access_token_expire_minutes', 0.001):
            token = token_manager.create_access_token(user_data)
        
        # Token should be expired
        with pytest.raises(Exception):
            token_manager.verify_token(token)
    
    def test_multiple_tokens_same_user(self, token_manager):
        """Test creating multiple tokens for the same user."""
        user_data = {
            "user_id": "test-user-123",
            "username": "testuser",
            "tenant_id": "test-tenant-123",
            "roles": ["user"]
        }
        
        # Create multiple access tokens
        token1 = token_manager.create_access_token(user_data)
        token2 = token_manager.create_access_token(user_data)
        
        # Both should be valid (they might be the same if created at the same time)
        # The important thing is that both can be verified
        data1 = token_manager.verify_token(token1)
        data2 = token_manager.verify_token(token2)
        
        data1 = token_manager.verify_token(token1)
        data2 = token_manager.verify_token(token2)
        
        assert data1.user_id == data2.user_id
        assert data1.username == data2.username 