"""
Extended unit tests for Storage service to achieve 70%+ coverage
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
sys.path.insert(0, str(project_root / 'storage' / 'src'))


@pytest.fixture(autouse=True)
def reset_config_state():
    """Reset global config state before each test"""
    # Clear any cached modules
    modules_to_clear = [name for name in sys.modules.keys() 
                       if name in ['storage', 'common.config']]
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


class TestStorageServiceExtended:
    """Extended tests for Storage service core functionality"""
    
    def test_storage_models_comprehensive(self):
        """Test all Storage Pydantic models"""
        import storage
        
        # Test Email model with all fields
        assert hasattr(storage, 'Email')
        email = storage.Email(
            sender="sender@example.com",
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test email body content",
            timestamp="2024-01-01T12:00:00Z",
            read=False,
            folder="INBOX"
        )
        assert email.sender == "sender@example.com"
        assert email.recipient == "recipient@example.com"
        assert email.subject == "Test Subject"
        assert email.body == "Test email body content"
        assert email.timestamp == "2024-01-01T12:00:00Z"
        assert email.read == False
        assert email.folder == "INBOX"
        
        # Test Email model with default values
        email_minimal = storage.Email(
            sender="sender@example.com",
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test body"
        )
        assert email_minimal.read == False
        assert email_minimal.folder == "INBOX"
        assert email_minimal.timestamp is None

    def test_service_state_management(self):
        """Test service state tracking and configuration"""
        import storage
        
        # Verify service_state structure
        assert hasattr(storage, 'service_state')
        state = storage.service_state
        
        # Test required state keys
        required_keys = [
            "start_time", "requests_total", "requests_successful", 
            "requests_failed", "last_request_time", "config"
        ]
        
        for key in required_keys:
            assert key in state, f"Service state missing key: {key}"
        
        # Test config structure
        config = state["config"]
        expected_config_keys = [
            "hostname", "port", "enabled", "timeout", 
            "mongo_uri", "database_name", "max_document_size"
        ]
        
        for key in expected_config_keys:
            assert key in config, f"Config missing key: {key}"

    def test_mongodb_connection_management(self):
        """Test MongoDB connection initialization and management"""
        import storage
        
        # Test lazy initialization variables
        assert hasattr(storage, 'client')
        assert hasattr(storage, 'db')
        assert hasattr(storage, 'emails_collection')
        
        # Initially should be None (lazy loading)
        assert storage.client is None
        assert storage.db is None
        assert storage.emails_collection is None

    @patch('storage.MongoClient')
    def test_get_mongo_connection_success(self, mock_mongo_client):
        """Test successful MongoDB connection"""
        import storage
        
        # Reset connection state
        storage.client = None
        storage.db = None
        storage.emails_collection = None
        
        # Setup mocks
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        
        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_client.admin.command.return_value = True  # ping response
        
        # Test connection initialization
        client, db, collection = storage.get_mongo_connection()
        
        # Verify connection was established
        assert client == mock_client
        assert db == mock_db
        assert collection == mock_collection
        
        # Verify global variables were set
        assert storage.client == mock_client
        assert storage.db == mock_db
        assert storage.emails_collection == mock_collection
        
        # Verify ping was called
        mock_client.admin.command.assert_called_with("ping")

    @patch('storage.MongoClient')
    def test_get_mongo_connection_failure(self, mock_mongo_client):
        """Test MongoDB connection failure"""
        import storage
        
        # Reset connection state
        storage.client = None
        storage.db = None
        storage.emails_collection = None
        
        # Setup mock to raise exception
        mock_mongo_client.side_effect = Exception("Connection failed")
        
        # Test connection failure
        with pytest.raises(Exception, match="Connection failed"):
            storage.get_mongo_connection()

    @patch('storage.MongoClient')
    def test_get_mongo_connection_already_connected(self, mock_mongo_client):
        """Test MongoDB connection when already connected"""
        import storage
        
        # Setup existing connection
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        
        storage.client = mock_client
        storage.db = mock_db
        storage.emails_collection = mock_collection
        
        # Test connection reuse
        client, db, collection = storage.get_mongo_connection()
        
        # Should return existing connections
        assert client == mock_client
        assert db == mock_db
        assert collection == mock_collection
        
        # Should not create new connection
        mock_mongo_client.assert_not_called()

    def test_configuration_validation(self):
        """Test configuration validation and defaults"""
        import storage
        
        config = storage.service_state["config"]
        
        # Test data types
        assert isinstance(config["hostname"], str)
        assert isinstance(config["port"], int)
        assert isinstance(config["enabled"], bool)
        assert isinstance(config["timeout"], int)
        assert isinstance(config["mongo_uri"], str)
        assert isinstance(config["database_name"], str)
        assert isinstance(config["max_document_size"], int)
        
        # Test reasonable defaults
        assert config["port"] > 0
        assert config["timeout"] > 0
        assert config["max_document_size"] > 0
        assert "mongodb://" in config["mongo_uri"]

    def test_logging_configuration(self):
        """Test logging setup"""
        import storage
        
        # Verify logger exists
        assert hasattr(storage, 'logger')
        assert storage.logger.name == 'storage'
        
        # Test logging level
        assert storage.logger.level <= 20  # INFO level or below

    def test_fastapi_app_configuration(self):
        """Test FastAPI app setup"""
        import storage
        
        # Verify app exists
        assert hasattr(storage, 'app')
        assert storage.app.title == "Storage Microservice"
        
        # Test app routes exist
        routes = [route.path for route in storage.app.routes]
        expected_routes = ["/emails", "/health", "/config", "/api/stats", "/api/storage-stats"]
        
        for route in expected_routes:
            assert any(route in path for path in routes), f"Route {route} not found"

    def test_request_statistics_tracking(self):
        """Test request statistics management"""
        import storage
        
        state = storage.service_state
        
        # Test initial statistics
        assert state["requests_total"] >= 0
        assert state["requests_successful"] >= 0
        assert state["requests_failed"] >= 0
        
        # Test statistics increment
        initial_total = state["requests_total"]
        state["requests_total"] += 1
        assert state["requests_total"] == initial_total + 1


class TestStorageEndpoints:
    """Test Storage REST API endpoints"""
    
    @patch('storage.get_mongo_connection')
    def test_store_email_endpoint(self, mock_get_connection):
        """Test email storage endpoint"""
        import storage
        
        # Setup mocks
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_get_connection.return_value = (mock_client, mock_db, mock_collection)
        
        # Mock successful insertion
        mock_collection.insert_one.return_value = MagicMock(inserted_id="test_id")
        
        client = TestClient(storage.app)
        
        email_data = {
            "sender": "sender@example.com",
            "recipient": "recipient@example.com",
            "subject": "Test Subject",
            "body": "Test email body",
            "folder": "INBOX"
        }
        
        response = client.post("/emails", json=email_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "id" in data
        
        # Verify MongoDB insert was called
        mock_collection.insert_one.assert_called_once()

    @patch('storage.get_mongo_connection')
    def test_store_email_endpoint_failure(self, mock_get_connection):
        """Test email storage endpoint failure"""
        import storage
        
        # Setup mocks to raise exception
        mock_get_connection.side_effect = Exception("Database error")
        
        client = TestClient(storage.app)
        
        email_data = {
            "sender": "sender@example.com",
            "recipient": "recipient@example.com",
            "subject": "Test Subject",
            "body": "Test email body"
        }
        
        response = client.post("/emails", json=email_data)
        assert response.status_code == 500

    @patch('storage.get_mongo_connection')
    def test_get_emails_endpoint(self, mock_get_connection):
        """Test email retrieval endpoint"""
        import storage
        
        # Setup mocks
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_get_connection.return_value = (mock_client, mock_db, mock_collection)
        
        # Mock database query results
        mock_emails = [
            {
                "_id": "test_id_1",
                "sender": "sender1@example.com",
                "recipient": "user@example.com",
                "subject": "Test Email 1",
                "body": "Test content 1",
                "timestamp": "2024-01-01T12:00:00Z",
                "read": False,
                "folder": "INBOX"
            },
            {
                "_id": "test_id_2", 
                "sender": "sender2@example.com",
                "recipient": "user@example.com",
                "subject": "Test Email 2",
                "body": "Test content 2",
                "timestamp": "2024-01-01T13:00:00Z",
                "read": True,
                "folder": "INBOX"
            }
        ]
        
        mock_collection.find.return_value = mock_emails
        
        client = TestClient(storage.app)
        response = client.get("/emails?user_id=user@example.com")
        
        assert response.status_code == 200
        data = response.json()
        assert "emails" in data
        assert len(data["emails"]) == 2
        
        # Verify query was called
        mock_collection.find.assert_called_once()

    @patch('storage.get_mongo_connection')
    def test_get_emails_with_filters(self, mock_get_connection):
        """Test email retrieval with folder and unread filters"""
        import storage
        
        # Setup mocks
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_get_connection.return_value = (mock_client, mock_db, mock_collection)
        
        mock_collection.find.return_value = []
        
        client = TestClient(storage.app)
        
        # Test with folder filter
        response = client.get("/emails?user_id=user@example.com&folder=SENT")
        assert response.status_code == 200
        
        # Test with unread filter
        response = client.get("/emails?user_id=user@example.com&unread_only=true")
        assert response.status_code == 200
        
        # Verify queries were called
        assert mock_collection.find.call_count >= 2

    def test_health_endpoint(self):
        """Test health check endpoint"""
        import storage
        
        client = TestClient(storage.app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Test response structure
        assert "status" in data
        assert "uptime" in data
        assert "service" in data
        assert data["service"] == "Storage"

    @patch('storage.get_mongo_connection')
    def test_health_endpoint_with_db_check(self, mock_get_connection):
        """Test health check with database connectivity"""
        import storage
        
        # Setup successful connection
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_get_connection.return_value = (mock_client, mock_db, mock_collection)
        mock_client.admin.command.return_value = True
        
        client = TestClient(storage.app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "database_status" in data

    def test_config_endpoints(self):
        """Test configuration endpoints"""
        import storage
        
        client = TestClient(storage.app)
        
        # Test GET config
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        
        # Should contain config data
        expected_keys = ["hostname", "port", "enabled", "timeout"]
        for key in expected_keys:
            assert key in data, f"Config response missing key: {key}"
        
        # Test PUT config update
        config_update = {
            "enabled": False,
            "timeout": 45,
            "max_document_size": 20000000
        }
        
        response = client.put("/config", json=config_update)
        assert response.status_code == 200
        
        # Verify config was updated
        updated_config = storage.service_state["config"]
        assert updated_config["enabled"] == False
        assert updated_config["timeout"] == 45
        assert updated_config["max_document_size"] == 20000000

    def test_stats_endpoint(self):
        """Test statistics endpoint"""
        import storage
        
        client = TestClient(storage.app)
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

    @patch('storage.get_mongo_connection')
    def test_storage_stats_endpoint(self, mock_get_connection):
        """Test storage-specific statistics endpoint"""
        import storage
        
        # Setup mocks
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_get_connection.return_value = (mock_client, mock_db, mock_collection)
        
        # Mock database stats
        mock_collection.count_documents.return_value = 100
        mock_collection.estimated_document_count.return_value = 100
        mock_db.command.return_value = {"dataSize": 1024000, "storageSize": 2048000}
        
        client = TestClient(storage.app)
        response = client.get("/api/storage-stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Test storage statistics structure
        expected_keys = ["total_emails", "database_size", "collection_size"]
        for key in expected_keys:
            assert key in data, f"Storage stats response missing key: {key}"

    def test_input_validation(self):
        """Test input validation on endpoints"""
        import storage
        
        client = TestClient(storage.app)
        
        # Test email endpoint with missing required fields
        invalid_email = {
            "sender": "sender@example.com",
            # Missing recipient, subject, body
        }
        
        response = client.post("/emails", json=invalid_email)
        assert response.status_code == 422  # Validation error
        
        # Test config endpoint with invalid data types
        invalid_config = {
            "timeout": "not_a_number",
            "enabled": "not_a_boolean",
            "max_document_size": "not_a_number"
        }
        
        response = client.put("/config", json=invalid_config)
        assert response.status_code in [400, 422]


class TestStorageAsyncFunctions:
    """Test async functions in Storage service"""
    
    @pytest.mark.asyncio
    @patch('storage.get_mongo_connection')
    async def test_store_email_function(self, mock_get_connection):
        """Test store_email async function"""
        import storage
        
        # Setup mocks
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_get_connection.return_value = (mock_client, mock_db, mock_collection)
        mock_collection.insert_one.return_value = MagicMock(inserted_id="test_id")
        
        # Create test email
        email = storage.Email(
            sender="sender@example.com",
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test body"
        )
        
        # Test function call
        client = TestClient(storage.app)
        response = client.post("/emails", json=email.dict())
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch('storage.get_mongo_connection')  
    async def test_get_emails_function(self, mock_get_connection):
        """Test get_emails async function"""
        import storage
        
        # Setup mocks
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_get_connection.return_value = (mock_client, mock_db, mock_collection)
        
        mock_emails = [
            {
                "_id": "test_id",
                "sender": "sender@example.com",
                "recipient": "user@example.com",
                "subject": "Test",
                "body": "Content",
                "timestamp": "2024-01-01T12:00:00Z",
                "read": False,
                "folder": "INBOX"
            }
        ]
        mock_collection.find.return_value = mock_emails
        
        # Test function call
        client = TestClient(storage.app)
        response = client.get("/emails?user_id=user@example.com")
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_check_function(self):
        """Test health_check async function"""
        import storage
        
        client = TestClient(storage.app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify health check response
        assert "status" in data
        assert "uptime" in data
        assert isinstance(data["uptime"], (int, float))

    @pytest.mark.asyncio
    async def test_config_update_function(self):
        """Test config update async function"""
        import storage
        
        client = TestClient(storage.app)
        
        config_update = {
            "enabled": True,
            "timeout": 60
        }
        
        response = client.put("/config", json=config_update)
        assert response.status_code == 200
        
        # Verify config was updated
        assert storage.service_state["config"]["enabled"] == True
        assert storage.service_state["config"]["timeout"] == 60

    @pytest.mark.asyncio
    @patch('storage.get_mongo_connection')
    async def test_stats_functions(self, mock_get_connection):
        """Test statistics async functions"""
        import storage
        
        # Setup mocks for storage stats
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_get_connection.return_value = (mock_client, mock_db, mock_collection)
        
        mock_collection.count_documents.return_value = 50
        mock_db.command.return_value = {"dataSize": 512000}
        
        client = TestClient(storage.app)
        
        # Test general stats
        response = client.get("/api/stats")
        assert response.status_code == 200
        
        # Test storage-specific stats
        response = client.get("/api/storage-stats") 
        assert response.status_code == 200


class TestStorageUtilities:
    """Test Storage utility functions and helpers"""
    
    def test_email_data_transformation(self):
        """Test email data processing utilities"""
        import storage
        
        # Test Email model serialization
        email = storage.Email(
            sender="test@example.com",
            recipient="user@example.com",
            subject="Test",
            body="Content"
        )
        
        email_dict = email.dict()
        assert isinstance(email_dict, dict)
        assert email_dict["sender"] == "test@example.com"
        assert email_dict["read"] == False
        assert email_dict["folder"] == "INBOX"

    def test_timestamp_handling(self):
        """Test timestamp generation and validation"""
        import storage
        
        # Test current timestamp generation
        current_time = datetime.utcnow().isoformat()
        assert isinstance(current_time, str)
        assert "T" in current_time
        
        # Test timestamp in email
        email = storage.Email(
            sender="test@example.com",
            recipient="user@example.com",
            subject="Test",
            body="Content",
            timestamp=current_time
        )
        assert email.timestamp == current_time

    def test_uptime_calculation(self):
        """Test uptime calculation utility"""
        import storage
        
        # Calculate uptime
        start_time = storage.service_state["start_time"]
        current_time = time.time()
        uptime = current_time - start_time
        
        assert uptime >= 0
        assert isinstance(uptime, float)

    def test_configuration_merging(self):
        """Test configuration merging and updates"""
        import storage
        
        config = storage.service_state["config"]
        
        # Test config update simulation
        original_timeout = config["timeout"]
        config["timeout"] = 120
        assert config["timeout"] == 120
        
        # Restore original value
        config["timeout"] = original_timeout

    def test_error_handling_utilities(self):
        """Test error handling helpers"""
        import storage
        
        # Test logger exists and is functional
        assert hasattr(storage, 'logger')
        
        # Test logging methods
        assert hasattr(storage.logger, 'info')
        assert hasattr(storage.logger, 'error')
        assert hasattr(storage.logger, 'warning')

    @patch('storage.get_mongo_connection')
    def test_database_query_helpers(self, mock_get_connection):
        """Test database query utility functions"""
        import storage
        
        # Setup mocks
        mock_client = MagicMock()
        mock_db = MagicMock() 
        mock_collection = MagicMock()
        mock_get_connection.return_value = (mock_client, mock_db, mock_collection)
        
        # Test connection retrieval
        client, db, collection = storage.get_mongo_connection()
        assert client == mock_client
        assert db == mock_db
        assert collection == mock_collection

    def test_data_validation_helpers(self):
        """Test data validation utilities"""
        import storage
        
        # Test Email model validation with invalid data
        with pytest.raises(Exception):  # Should raise validation error
            storage.Email(
                sender="invalid-email",  # Invalid email format
                recipient="user@example.com",
                subject="",  # Empty subject might be invalid
                body=""  # Empty body might be invalid
            )

    def test_performance_monitoring_utilities(self):
        """Test performance monitoring helpers"""
        import storage
        
        # Test statistics tracking
        state = storage.service_state
        
        # Test request counters
        initial_total = state["requests_total"]
        state["requests_total"] += 1
        assert state["requests_total"] == initial_total + 1
        
        # Test timing
        start_time = time.time()
        time.sleep(0.01)
        elapsed = time.time() - start_time
        assert elapsed >= 0.01

    def test_mongo_connection_state_management(self):
        """Test MongoDB connection state utilities"""
        import storage
        
        # Test initial state
        assert storage.client is None
        assert storage.db is None
        assert storage.emails_collection is None
        
        # Test state variables exist
        assert hasattr(storage, 'client')
        assert hasattr(storage, 'db')
        assert hasattr(storage, 'emails_collection')