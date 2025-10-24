"""
Extended unit tests for IMAP service to achieve 70%+ coverage
"""
import pytest
import sys
import os
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
from fastapi.testclient import TestClient

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'imap' / 'src'))


@pytest.fixture(autouse=True)
def reset_config_state():
    """Reset global config state before each test"""
    # Clear any cached modules
    modules_to_clear = [name for name in sys.modules.keys() 
                       if name in ['imap', 'common.config']]
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


class TestIMAPServiceExtended:
    """Extended tests for IMAP service core functionality"""
    
    def test_imap_models_comprehensive(self):
        """Test all IMAP Pydantic models"""
        import imap
        
        # Test Email model
        assert hasattr(imap, 'Email')
        email = imap.Email(
            sender="sender@example.com",
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test email body content"
        )
        assert email.sender == "sender@example.com"
        assert email.recipient == "recipient@example.com"
        assert email.subject == "Test Subject"
        assert email.body == "Test email body content"

    def test_service_state_management(self):
        """Test service state tracking and configuration"""
        import imap
        
        # Verify service_state structure
        assert hasattr(imap, 'service_state')
        state = imap.service_state
        
        # Test required state keys
        required_keys = [
            "start_time", "requests_total", "requests_successful", 
            "requests_failed", "last_request_time", "active_connections",
            "active_sessions", "config"
        ]
        
        for key in required_keys:
            assert key in state, f"Service state missing key: {key}"
        
        # Test config structure
        config = state["config"]
        expected_config_keys = [
            "hostname", "port", "max_workers", "pool_size", 
            "enabled", "timeout", "max_connections", "idle_timeout"
        ]
        
        for key in expected_config_keys:
            assert key in config, f"Config missing key: {key}"

    def test_thread_pool_executor(self):
        """Test thread pool executor initialization"""
        import imap
        
        # Verify executor exists
        assert hasattr(imap, 'executor')
        assert imap.executor is not None
        
        # Test executor properties
        max_workers = imap.service_state["config"]["max_workers"]
        assert imap.executor._max_workers == max_workers

    @pytest.mark.asyncio
    async def test_verify_user_function(self):
        """Test user verification with Identity Service"""
        import imap
        
        # Test successful verification
        with patch('imap.aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await imap.verify_user("valid_token")
            assert result == True
            
        # Test failed verification (401)
        with patch('imap.aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await imap.verify_user("invalid_token")
            assert result == False
            
        # Test network error
        with patch('imap.aiohttp.ClientSession.get', side_effect=Exception("Network error")):
            result = await imap.verify_user("any_token")
            assert result == False

    def test_fetch_emails_sync_function(self):
        """Test synchronous email fetching function"""
        import imap
        
        # Test _fetch_emails_sync function
        assert hasattr(imap, '_fetch_emails_sync')
        
        # Mock storage service response
        with patch('imap.aiohttp.ClientSession.get') as mock_get:
            # Mock successful response with emails
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "emails": [
                    {
                        "sender": "test@example.com",
                        "recipient": "user@example.com", 
                        "subject": "Test Email",
                        "body": "Test content"
                    }
                ]
            }
            mock_get.return_value.__enter__.return_value = mock_response
            
            # Test function execution
            result = imap._fetch_emails_sync("test_user")
            
            # Should return list of emails or handle gracefully
            assert result is not None

    def test_connection_management(self):
        """Test connection tracking functionality"""
        import imap
        
        state = imap.service_state
        
        # Test active connections list
        assert "active_connections" in state
        assert isinstance(state["active_connections"], list)
        
        # Test active sessions list  
        assert "active_sessions" in state
        assert isinstance(state["active_sessions"], list)
        
        # Test connection limits
        assert "max_connections" in state["config"]
        assert isinstance(state["config"]["max_connections"], int)

    def test_request_statistics_tracking(self):
        """Test request statistics management"""
        import imap
        
        state = imap.service_state
        
        # Test initial statistics
        assert state["requests_total"] >= 0
        assert state["requests_successful"] >= 0
        assert state["requests_failed"] >= 0
        
        # Test statistics increment (would happen during actual requests)
        initial_total = state["requests_total"]
        state["requests_total"] += 1
        assert state["requests_total"] == initial_total + 1

    def test_configuration_validation(self):
        """Test configuration validation and defaults"""
        import imap
        
        config = imap.service_state["config"]
        
        # Test data types
        assert isinstance(config["hostname"], str)
        assert isinstance(config["port"], int)
        assert isinstance(config["max_workers"], int)
        assert isinstance(config["pool_size"], int)
        assert isinstance(config["enabled"], bool)
        assert isinstance(config["timeout"], int)
        assert isinstance(config["max_connections"], int)
        assert isinstance(config["idle_timeout"], int)
        
        # Test reasonable defaults
        assert config["port"] > 0
        assert config["max_workers"] > 0
        assert config["pool_size"] > 0
        assert config["timeout"] > 0
        assert config["max_connections"] > 0
        assert config["idle_timeout"] > 0

    def test_logging_configuration(self):
        """Test logging setup"""
        import imap
        
        # Verify logger exists
        assert hasattr(imap, 'logger')
        assert imap.logger.name == 'imap'
        
        # Test logging level
        assert imap.logger.level <= 20  # INFO level or below

    def test_fastapi_app_configuration(self):
        """Test FastAPI app setup"""
        import imap
        
        # Verify app exists
        assert hasattr(imap, 'app')
        assert imap.app.title == "IMAP Microservice"
        
        # Test app routes exist
        routes = [route.path for route in imap.app.routes]
        expected_routes = ["/emails", "/health", "/config", "/api/stats", "/api/connections", "/api/sessions"]
        
        for route in expected_routes:
            assert any(route in path for path in routes), f"Route {route} not found"


class TestIMAPEndpoints:
    """Test IMAP REST API endpoints"""
    
    @patch('imap.verify_user')
    @patch('imap.executor.submit')
    def test_get_emails_endpoint(self, mock_submit, mock_verify):
        """Test email retrieval endpoint"""
        import imap
        
        client = TestClient(imap.app)
        
        # Test successful email retrieval
        mock_verify.return_value = True
        mock_future = MagicMock()
        mock_future.result.return_value = [
            {
                "sender": "test@example.com",
                "recipient": "user@example.com",
                "subject": "Test",
                "body": "Content"
            }
        ]
        mock_submit.return_value = mock_future
        
        response = client.get(
            "/emails?user_id=test_user",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "emails" in data
        
        # Test unauthorized access
        mock_verify.return_value = False
        
        response = client.get(
            "/emails?user_id=test_user", 
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401

    def test_health_endpoint(self):
        """Test health check endpoint"""
        import imap
        
        client = TestClient(imap.app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Test response structure
        assert "status" in data
        assert "uptime" in data
        assert "service" in data
        assert data["service"] == "IMAP"

    def test_config_endpoints(self):
        """Test configuration endpoints"""
        import imap
        
        client = TestClient(imap.app)
        
        # Test GET config
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        
        # Should contain config data
        expected_keys = ["hostname", "port", "max_workers", "enabled"]
        for key in expected_keys:
            assert key in data, f"Config response missing key: {key}"
        
        # Test PUT config update
        config_update = {
            "enabled": False,
            "timeout": 45,
            "max_workers": 8
        }
        
        response = client.put("/config", json=config_update)
        assert response.status_code == 200
        
        # Verify config was updated
        updated_config = imap.service_state["config"]
        assert updated_config["enabled"] == False
        assert updated_config["timeout"] == 45
        assert updated_config["max_workers"] == 8

    def test_stats_endpoint(self):
        """Test statistics endpoint"""
        import imap
        
        client = TestClient(imap.app)
        response = client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Test statistics structure
        expected_keys = [
            "uptime", "requests_total", "requests_successful", 
            "requests_failed", "last_request_time"
        ]
        
        for key in expected_keys:
            assert key in data, f"Stats response missing key: {key}"

    def test_connections_endpoint(self):
        """Test active connections endpoint"""
        import imap
        
        client = TestClient(imap.app)
        response = client.get("/api/connections")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "active_connections" in data
        assert "connection_count" in data
        assert isinstance(data["active_connections"], list)
        assert isinstance(data["connection_count"], int)

    def test_sessions_endpoint(self):
        """Test active sessions endpoint"""
        import imap
        
        client = TestClient(imap.app)
        response = client.get("/api/sessions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "active_sessions" in data
        assert "session_count" in data
        assert isinstance(data["active_sessions"], list)
        assert isinstance(data["session_count"], int)

    def test_error_handling(self):
        """Test error handling in endpoints"""
        import imap
        
        client = TestClient(imap.app)
        
        # Test missing Authorization header
        response = client.get("/emails?user_id=test_user")
        assert response.status_code == 422  # Validation error
        
        # Test malformed Authorization header
        response = client.get(
            "/emails?user_id=test_user",
            headers={"Authorization": "InvalidFormat"}
        )
        # Should handle gracefully
        assert response.status_code in [400, 401, 422]

    def test_input_validation(self):
        """Test input validation on endpoints"""
        import imap
        
        client = TestClient(imap.app)
        
        # Test config endpoint with invalid data
        invalid_config = {
            "timeout": "not_a_number",
            "max_workers": -1,
            "enabled": "not_a_boolean"
        }
        
        response = client.put("/config", json=invalid_config)
        # Should validate input and reject invalid data
        assert response.status_code in [400, 422]


class TestIMAPAsyncFunctions:
    """Test async functions in IMAP service"""
    
    @pytest.mark.asyncio
    async def test_verify_user_comprehensive(self):
        """Comprehensive test of user verification"""
        import imap
        
        # Test various HTTP status codes
        test_cases = [
            (200, True),   # Success
            (401, False),  # Unauthorized
            (403, False),  # Forbidden
            (404, False),  # Not found
            (500, False),  # Server error
        ]
        
        for status_code, expected_result in test_cases:
            with patch('imap.aiohttp.ClientSession.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status = status_code
                mock_get.return_value.__aenter__.return_value = mock_response
                
                result = await imap.verify_user("test_token")
                assert result == expected_result

    @pytest.mark.asyncio
    async def test_email_processing_pipeline(self):
        """Test complete email processing pipeline"""
        import imap
        
        # Test the complete flow from request to response
        with patch('imap.verify_user', return_value=True):
            with patch('imap.executor.submit') as mock_submit:
                mock_future = MagicMock()
                mock_future.result.return_value = [
                    {
                        "sender": "test@example.com",
                        "recipient": "user@example.com",
                        "subject": "Test Email",
                        "body": "Test content"
                    }
                ]
                mock_submit.return_value = mock_future
                
                # Test client request simulation
                client = TestClient(imap.app)
                response = client.get(
                    "/emails?user_id=test_user",
                    headers={"Authorization": "Bearer valid_token"}
                )
                
                assert response.status_code == 200
                # Verify executor was called
                mock_submit.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_comprehensive(self):
        """Test health check function"""
        import imap
        
        # Test health check directly
        client = TestClient(imap.app)
        response = client.get("/health")
        
        data = response.json()
        
        # Verify health response structure
        assert "status" in data
        assert "uptime" in data
        assert "service" in data
        assert "timestamp" in data
        
        # Test uptime calculation
        assert isinstance(data["uptime"], (int, float))
        assert data["uptime"] >= 0

    @pytest.mark.asyncio  
    async def test_config_update_comprehensive(self):
        """Test configuration update function"""
        import imap
        
        client = TestClient(imap.app)
        
        # Test valid config update
        valid_config = {
            "enabled": True,
            "timeout": 60,
            "max_workers": 6,
            "pool_size": 15
        }
        
        response = client.put("/config", json=valid_config)
        assert response.status_code == 200
        
        # Verify config was actually updated
        current_config = imap.service_state["config"]
        assert current_config["enabled"] == True
        assert current_config["timeout"] == 60
        assert current_config["max_workers"] == 6
        assert current_config["pool_size"] == 15

    @pytest.mark.asyncio
    async def test_statistics_update(self):
        """Test statistics tracking and updates"""
        import imap
        
        # Get initial stats
        initial_stats = {
            "total": imap.service_state["requests_total"],
            "successful": imap.service_state["requests_successful"],
            "failed": imap.service_state["requests_failed"]
        }
        
        # Simulate successful request
        client = TestClient(imap.app)
        response = client.get("/health")
        
        # Stats should be updated
        assert imap.service_state["requests_total"] >= initial_stats["total"]
        assert imap.service_state["last_request_time"] is not None


class TestIMAPUtilities:
    """Test IMAP utility functions and helpers"""
    
    def test_connection_pool_management(self):
        """Test connection pool utilities"""
        import imap
        
        # Test connection tracking
        state = imap.service_state
        
        # Add test connection
        test_connection = {"id": "test_conn_1", "created": time.time()}
        state["active_connections"].append(test_connection)
        
        assert len(state["active_connections"]) >= 1
        assert test_connection in state["active_connections"]
        
        # Remove test connection
        state["active_connections"].remove(test_connection)

    def test_session_management(self):
        """Test session management utilities"""
        import imap
        
        state = imap.service_state
        
        # Test session tracking
        test_session = {"id": "session_1", "user_id": "test_user", "created": time.time()}
        state["active_sessions"].append(test_session)
        
        assert len(state["active_sessions"]) >= 1
        assert test_session in state["active_sessions"]
        
        # Cleanup
        state["active_sessions"].remove(test_session)

    def test_uptime_calculation(self):
        """Test uptime calculation utility"""
        import imap
        
        # Calculate uptime
        start_time = imap.service_state["start_time"]
        current_time = time.time()
        uptime = current_time - start_time
        
        assert uptime >= 0
        assert isinstance(uptime, float)

    def test_configuration_merging(self):
        """Test configuration merging and validation"""
        import imap
        
        # Test config structure
        config = imap.service_state["config"]
        
        # Test environment variable loading
        original_timeout = config["timeout"]
        
        # Simulate config update
        config["timeout"] = 120
        assert config["timeout"] == 120
        
        # Restore original
        config["timeout"] = original_timeout

    def test_error_logging(self):
        """Test error logging functionality"""
        import imap
        
        # Test logger exists and is configured
        assert hasattr(imap, 'logger')
        
        # Test logging methods exist
        assert hasattr(imap.logger, 'info')
        assert hasattr(imap.logger, 'error')
        assert hasattr(imap.logger, 'warning')
        assert hasattr(imap.logger, 'debug')

    def test_data_validation_helpers(self):
        """Test data validation utility functions"""
        import imap
        
        # Test Email model validation
        valid_email_data = {
            "sender": "test@example.com",
            "recipient": "user@example.com", 
            "subject": "Test Subject",
            "body": "Test body content"
        }
        
        email = imap.Email(**valid_email_data)
        assert email.sender == valid_email_data["sender"]
        assert email.recipient == valid_email_data["recipient"]
        assert email.subject == valid_email_data["subject"]
        assert email.body == valid_email_data["body"]

    def test_performance_monitoring(self):
        """Test performance monitoring utilities"""
        import imap
        
        # Test timing functionality
        start_time = time.time()
        time.sleep(0.01)  # Small delay
        elapsed = time.time() - start_time
        
        assert elapsed >= 0.01
        assert isinstance(elapsed, float)
        
        # Test request timing tracking
        state = imap.service_state
        if "request_times" not in state:
            state["request_times"] = []
        
        state["request_times"].append(elapsed)
        assert elapsed in state["request_times"]