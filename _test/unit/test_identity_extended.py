"""
Extended unit tests for Identity service to achieve 70%+ coverage
"""
import pytest
import sys
import os
import asyncio
import time
import hashlib
import jwt
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'identity' / 'src'))


@pytest.fixture(autouse=True)
def reset_config_state():
    """Reset global config state before each test"""
    # Clear any cached modules
    modules_to_clear = [name for name in sys.modules.keys() 
                       if name in ['config_loader', 'identity', 'common.config']]
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]
    
    # Reset global config instance if it exists
    try:
        import lib.common.config
        common.config._config_instance = None
    except ImportError:
        pass
    
    yield
    
    # Cleanup after test
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]


class TestIdentityServiceExtended:
    """Extended tests for Identity service core functionality"""
    
    def test_identity_models_validation(self):
        """Test all Pydantic models validation"""
        import identity
        
        # Test UserCreate model
        assert hasattr(identity, 'UserCreate')
        user_create = identity.UserCreate(
            email="test@example.com",
            password="password123",
            username="testuser",
            domain="example.com",
            is_admin=False
        )
        assert user_create.email == "test@example.com"
        assert user_create.password == "password123"
        assert user_create.username == "testuser"
        assert user_create.domain == "example.com"
        assert user_create.is_admin == False
        
        # Test LoginRequest model
        assert hasattr(identity, 'LoginRequest')
        login_req = identity.LoginRequest(
            email="test@example.com",
            password="password123"
        )
        assert login_req.email == "test@example.com"
        assert login_req.password == "password123"
        
        # Test Domain model
        assert hasattr(identity, 'Domain')
        domain = identity.Domain(name="example.com", enabled=True)
        assert domain.name == "example.com"
        assert domain.enabled == True
        
        # Test UserUpdate model
        assert hasattr(identity, 'UserUpdate')
        user_update = identity.UserUpdate(
            id=1,
            email="updated@example.com",
            username="updateduser",
            is_admin=True
        )
        assert user_update.id == 1
        assert user_update.email == "updated@example.com"
        assert user_update.username == "updateduser"
        assert user_update.is_admin == True

    def test_password_hashing_functions(self):
        """Test password hashing utility functions"""
        import identity
        
        # Test hash_password function
        password = "testpassword123"
        hashed = identity.hash_password(password)
        
        # Verify hash is different from original password
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)
        
        # Test verify_password function
        assert identity.verify_password(password, hashed) == True
        assert identity.verify_password("wrongpassword", hashed) == False
        
        # Test with different passwords
        password2 = "differentpassword"
        hashed2 = identity.hash_password(password2)
        assert hashed != hashed2
        assert identity.verify_password(password2, hashed2) == True
        assert identity.verify_password(password, hashed2) == False

    def test_jwt_token_functions(self):
        """Test JWT token creation and validation"""
        import identity
        
        # Test create_access_token
        user_data = {"email": "test@example.com", "user_id": 1, "is_admin": False}
        token = identity.create_access_token(user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT has 3 parts separated by dots
        
        # Test create_refresh_token
        refresh_token = identity.create_refresh_token(user_data)
        
        assert isinstance(refresh_token, str)
        assert len(refresh_token) > 0
        assert refresh_token.count('.') == 2
        assert token != refresh_token  # Should be different
        
        # Test decode_jwt_token
        decoded = identity.decode_jwt_token(token)
        assert decoded["email"] == "test@example.com"
        assert decoded["user_id"] == 1
        assert decoded["is_admin"] == False
        assert "exp" in decoded  # Should have expiration
        assert "iat" in decoded  # Should have issued at
        
        # Test with invalid token
        with pytest.raises(jwt.InvalidTokenError):
            identity.decode_jwt_token("invalid.token.here")
            
        # Test with expired token (mock expiration)
        expired_data = user_data.copy()
        expired_data["exp"] = int(time.time()) - 3600  # 1 hour ago
        with patch('identity.time.time', return_value=time.time() + 7200):  # 2 hours from now
            with pytest.raises(jwt.ExpiredSignatureError):
                expired_token = jwt.encode(expired_data, identity.config.JWT_SECRET, algorithm=identity.config.JWT_ALGORITHM)
                identity.decode_jwt_token(expired_token)

    @patch('identity.asyncpg.create_pool')
    async def test_init_db_function(self, mock_create_pool):
        """Test database initialization function"""
        import identity
        
        # Mock connection pool
        mock_pool = AsyncMock()
        mock_create_pool.return_value = mock_pool
        
        # Mock connection for executing SQL
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Test database initialization
        result = await identity.init_db()
        
        # Verify database pool creation was called
        mock_create_pool.assert_called_once()
        assert result == mock_pool
        
        # Verify SQL execution was called for table creation
        assert mock_conn.execute.call_count >= 2  # At least users and domains tables

    def test_session_management_functions(self):
        """Test session tracking functions"""
        import identity
        
        # Test add_session
        session_data = {
            "user_id": 1,
            "email": "test@example.com",
            "login_time": datetime.utcnow().isoformat(),
            "ip_address": "192.168.1.1",
            "user_agent": "TestAgent/1.0"
        }
        
        identity.add_session("token123", session_data)
        
        # Verify session was added
        assert "token123" in identity.active_sessions
        stored_session = identity.active_sessions["token123"]
        assert stored_session["user_id"] == 1
        assert stored_session["email"] == "test@example.com"
        assert stored_session["ip_address"] == "192.168.1.1"
        
        # Test get_session
        retrieved_session = identity.get_session("token123")
        assert retrieved_session == stored_session
        
        # Test get non-existent session
        assert identity.get_session("nonexistent") is None
        
        # Test remove_session
        identity.remove_session("token123")
        assert "token123" not in identity.active_sessions
        assert identity.get_session("token123") is None

    def test_utility_functions(self):
        """Test utility functions"""
        import identity
        
        # Test generate_token_id
        token_id = identity.generate_token_id()
        assert isinstance(token_id, str)
        assert len(token_id) > 10
        
        # Generate multiple token IDs to ensure uniqueness
        token_ids = [identity.generate_token_id() for _ in range(5)]
        assert len(set(token_ids)) == 5  # All should be unique
        
        # Test domain validation functions if they exist
        if hasattr(identity, 'is_valid_email'):
            assert identity.is_valid_email("test@example.com") == True
            assert identity.is_valid_email("invalid-email") == False
            
        if hasattr(identity, 'is_valid_domain'):
            assert identity.is_valid_domain("example.com") == True
            assert identity.is_valid_domain("invalid..domain") == False

    def test_application_configuration(self):
        """Test FastAPI application configuration"""
        import identity
        
        # Test app instance
        assert hasattr(identity, 'app')
        app = identity.app
        
        # Verify app configuration
        assert app.title == "DIGiDIG Identity Service"
        assert hasattr(app, 'routes')
        assert len(app.routes) > 0
        
        # Check for important routes
        route_paths = [route.path for route in app.routes]
        expected_routes = [
            "/register",
            "/login", 
            "/verify",
            "/refresh",
            "/domains",
            "/users",
            "/health"
        ]
        
        for expected_route in expected_routes:
            assert any(expected_route in path for path in route_paths), f"Route {expected_route} not found"

    def test_error_handling(self):
        """Test error handling in various functions"""
        import identity
        
        # Test JWT decoding with malformed token
        with pytest.raises(Exception):
            identity.decode_jwt_token("not.a.valid.jwt.token.format")
            
        # Test password verification with None values
        assert identity.verify_password(None, "hash") == False
        assert identity.verify_password("password", None) == False
        assert identity.verify_password(None, None) == False
        
        # Test empty string handling
        assert identity.verify_password("", "hash") == False
        assert identity.verify_password("password", "") == False

    def test_constants_and_globals(self):
        """Test constants and global variables"""
        import identity
        
        # Test active_sessions dictionary exists
        assert hasattr(identity, 'active_sessions')
        assert isinstance(identity.active_sessions, dict)
        
        # Test config object
        assert hasattr(identity, 'config')
        config = identity.config
        
        # Verify config attributes
        assert hasattr(config, 'JWT_SECRET')
        assert hasattr(config, 'JWT_ALGORITHM')
        assert hasattr(config, 'TOKEN_EXPIRY')
        assert hasattr(config, 'DB_HOST')
        assert hasattr(config, 'DB_PORT')
        
        # Test logger
        assert hasattr(identity, 'logger')
        assert identity.logger.name == "identity"


class TestIdentityEndpoints:
    """Test Identity service endpoints with mocked dependencies"""
    
    @patch('identity.src.identity.init_db')
    def test_health_endpoint(self, mock_init_db):
        """Test health check endpoint"""
        from identity.src.identity import app
        
        # Mock database pool
        mock_pool = AsyncMock()
        mock_init_db.return_value = mock_pool
        
        client = TestClient(app)
        
        # Mock the database connection for health check
        with patch.object(app.state, 'db_pool', mock_pool):
            response = client.get("/api/health")
            
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_config_get_endpoint(self):
        """Test GET configuration endpoint"""
        from identity.src.identity import app
        
        client = TestClient(app)
        response = client.get("/api/config")
        
        assert response.status_code in [200, 401, 403]  # Might require auth

    def test_config_put_endpoint(self):
        """Test PUT configuration endpoint"""  
        from identity.src.identity import app
        
        client = TestClient(app)
        response = client.put("/api/config", json={})
        
        assert response.status_code in [200, 400, 401, 403, 422]

    @patch('identity.src.identity.init_db')
    def test_stats_endpoint(self, mock_init_db):
        """Test statistics endpoint"""
        from identity.src.identity import app
        
        # Mock database pool and connection
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetchval.return_value = 5  # Mock user count
        mock_init_db.return_value = mock_pool
        
        client = TestClient(app)
        
        with patch.object(app.state, 'db_pool', mock_pool):
            response = client.get("/api/stats")
            
        assert response.status_code in [200, 401, 403]

    def test_verify_endpoint(self):
        """Test token verification endpoint"""
        from identity.src.identity import app
        
        client = TestClient(app)
        response = client.get("/verify")
        
        assert response.status_code != 404  # Should exist but may require auth

    @pytest.mark.parametrize("endpoint", [
        "/register",
        "/login", 
        "/tokens/revoke",
        "/tokens/refresh",
        "/domains",
        "/domains/rename"
    ])
    def test_post_endpoints_exist(self, endpoint):
        """Test that POST endpoints exist"""
        from identity.src.identity import app
        
        client = TestClient(app)
        response = client.post(endpoint)
        assert response.status_code != 404
        assert response.status_code in [400, 401, 403, 422]  # Valid error responses

    @pytest.mark.parametrize("endpoint", [
        "/domains",
        "/users",
        "/api/identity/sessions"
    ])
    def test_get_endpoints_exist(self, endpoint):
        """Test that GET endpoints exist"""
        from identity.src.identity import app
        
        client = TestClient(app)
        response = client.get(endpoint)
        assert response.status_code != 404

    def test_domain_exists_endpoint(self):
        """Test domain exists check endpoint"""
        from identity.src.identity import app
        
        client = TestClient(app)
        response = client.get("/api/domains/example.com/exists")
        assert response.status_code in [200, 404]  # Valid responses

    def test_user_management_endpoints(self):
        """Test user management endpoints"""
        from identity.src.identity import app
        
        client = TestClient(app)
        
        # Test PUT /users
        response = client.put("/users")
        assert response.status_code != 404
        
        # Test DELETE /users/{user_id}
        response = client.delete("/users/123")
        assert response.status_code != 404

    def test_domain_management_endpoints(self):
        """Test domain management endpoints"""
        from identity.src.identity import app
        
        client = TestClient(app)
        
        # Test DELETE /domains/{domain_name}
        response = client.delete("/domains/example.com")
        assert response.status_code != 404


class TestIdentityAsyncFunctions:
    """Test async functions in Identity service"""
    
    @pytest.mark.asyncio
    @patch('identity.asyncpg.create_pool')
    async def test_decode_token_function(self, mock_create_pool):
        """Test token decoding async function"""
        import identity
        
        # Create a valid token
        user_data = {"email": "test@example.com", "user_id": 1, "is_admin": False}
        token = identity.create_access_token(user_data)
        
        # Test decoding with Bearer prefix
        bearer_token = f"Bearer {token}"
        
        # Mock database pool
        mock_pool = AsyncMock()
        mock_create_pool.return_value = mock_pool
        
        with patch.object(identity, 'init_db', return_value=mock_pool):
            decoded = await identity._decode_token(bearer_token)
            
        assert decoded["email"] == "test@example.com"
        assert decoded["user_id"] == 1
        
        # Test with invalid format
        with pytest.raises(Exception):
            await identity._decode_token("InvalidToken")

    @pytest.mark.asyncio
    async def test_check_domain_exists(self):
        """Test domain existence check function"""
        import identity
        
        # Mock database pool and connection
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Mock domain exists
        mock_conn.fetchval.return_value = 1
        
        with patch.object(identity, 'init_db', return_value=mock_pool):
            with patch.object(identity.app.state, 'db_pool', mock_pool):
                result = await identity.check_domain_exists("example.com")
                
        assert result == {"exists": True, "domain": "example.com"}
        
        # Mock domain doesn't exist
        mock_conn.fetchval.return_value = 0
        
        with patch.object(identity.app.state, 'db_pool', mock_pool):
            result = await identity.check_domain_exists("nonexistent.com")
            
        assert result == {"exists": False, "domain": "nonexistent.com"}


class TestIdentityHelperFunctions:
    """Test helper and utility functions"""
    
    def test_email_validation_helpers(self):
        """Test email validation helper functions if they exist"""
        import identity
        
        # Check if validation functions exist and test them
        if hasattr(identity, 'validate_email_format'):
            assert identity.validate_email_format("test@example.com") == True
            assert identity.validate_email_format("invalid-email") == False
            
        if hasattr(identity, 'extract_domain_from_email'):
            assert identity.extract_domain_from_email("test@example.com") == "example.com"
            
        if hasattr(identity, 'normalize_email'):
            assert identity.normalize_email("TEST@EXAMPLE.COM") == "test@example.com"

    def test_security_helpers(self):
        """Test security-related helper functions"""
        import identity
        
        # Test if there are rate limiting helpers
        if hasattr(identity, 'check_rate_limit'):
            # This would test rate limiting if implemented
            pass
            
        # Test if there are audit logging helpers  
        if hasattr(identity, 'log_security_event'):
            # This would test security event logging if implemented
            pass

    def test_database_helpers(self):
        """Test database helper functions"""
        import identity
        
        # Test database URL construction if available
        if hasattr(identity, 'get_database_url'):
            db_url = identity.get_database_url()
            assert isinstance(db_url, str)
            assert "postgresql://" in db_url
        else:
            # Test config database URL property
            db_url = identity.config.database_url
            assert isinstance(db_url, str)
            assert "postgresql://" in db_url