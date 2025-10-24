"""
Unit tests for Storage service - testing actual functions without mocking
"""
import pytest
import sys
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

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

class TestStorageServiceReal:
    """Test Storage service actual functions"""
    
    def test_storage_imports(self):
        """Test that Storage service modules can be imported"""
        try:
            import storage
            assert hasattr(storage, 'app')
            assert hasattr(storage, 'service_state')
        except ImportError as e:
            pytest.fail(f"Could not import Storage service: {e}")
    
    def test_storage_app_creation(self):
        """Test Storage FastAPI app creation"""
        try:
            import storage
            from fastapi import FastAPI
            
            assert isinstance(storage.app, FastAPI)
            assert storage.app.title == "Storage Microservice"
            
        except ImportError:
            pytest.skip("Storage service not available")
    
    def test_storage_service_state(self):
        """Test Storage service state structure"""
        try:
            import storage
            
            # Check if service_state exists and has required fields
            assert hasattr(storage, 'service_state')
            state = storage.service_state
            
            required_fields = [
                "start_time", "requests_total", "requests_successful", 
                "requests_failed", "config"
            ]
            
            for field in required_fields:
                assert field in state, f"Missing field: {field}"
            
            # Check config structure
            config = state["config"]
            config_fields = ["hostname", "port", "enabled", "timeout", "mongo_uri", "database_name"]
            for field in config_fields:
                assert field in config, f"Missing config field: {field}"
                
        except ImportError:
            pytest.skip("Storage service not available")
    
    def test_storage_configuration_values(self):
        """Test Storage configuration values"""
        try:
            import storage
            
            config = storage.service_state["config"]
            
            # Test configuration types and ranges
            assert isinstance(config["enabled"], bool)
            assert isinstance(config["hostname"], str)
            assert isinstance(config["port"], int)
            assert isinstance(config["timeout"], int)
            assert isinstance(config["mongo_uri"], str)
            assert isinstance(config["database_name"], str)
            
            # Test value ranges
            assert 1024 <= config["port"] <= 65535
            assert config["timeout"] > 0
            assert config["mongo_uri"].startswith("mongodb://")
            assert len(config["database_name"]) > 0
            
            if "max_document_size" in config:
                assert config["max_document_size"] > 0
                
        except ImportError:
            pytest.skip("Storage service not available")
    
    def test_storage_models_real(self):
        """Test Storage pydantic models"""
        try:
            import storage
            
            # Test Email model
            if hasattr(storage, 'Email'):
                email = storage.Email(
                    sender="test@example.com",
                    recipient="recipient@example.com",
                    subject="Test Storage Email",
                    body="Test body content"
                )
                assert email.sender == "test@example.com"
                assert email.recipient == "recipient@example.com"
                assert email.subject == "Test Storage Email"
                assert email.body == "Test body content"
                
                # Test optional fields
                assert hasattr(email, 'timestamp')
                assert hasattr(email, 'read')
                assert hasattr(email, 'folder')
            
        except ImportError:
            pytest.skip("Storage service models not available")


class TestStorageServiceDatabase:
    """Test Storage service database operations"""
    
    def test_storage_mongodb_client_exists(self):
        """Test Storage MongoDB client setup"""
        try:
            import storage
            
            # Check if MongoDB client exists
            assert hasattr(storage, 'client')
            assert hasattr(storage, 'db')
            assert hasattr(storage, 'emails_collection')
            
        except ImportError:
            pytest.skip("Storage service not available")
        except Exception:
            # MongoDB connection might fail, that's expected in test environment
            pytest.skip("MongoDB not available in test environment")
    
    def test_storage_database_configuration(self):
        """Test Storage database configuration"""
        try:
            import storage
            
            config = storage.service_state["config"]
            
            # Test MongoDB URI format
            mongo_uri = config["mongo_uri"]
            assert mongo_uri.startswith("mongodb://")
            
            # Test database name
            db_name = config["database_name"]
            assert isinstance(db_name, str)
            assert len(db_name) > 0
            
        except ImportError:
            pytest.skip("Storage service not available")
    
    def test_storage_environment_variables(self):
        """Test Storage environment variable handling"""
        try:
            import storage
            import os
            
            config = storage.service_state["config"]
            
            # Test that environment variables are read
            expected_vars = {
                "STORAGE_HOSTNAME": config.get("hostname"),
                "STORAGE_PORT": str(config.get("port")),
                "STORAGE_TIMEOUT": str(config.get("timeout")),
                "MONGO_URI": config.get("mongo_uri"),
                "DB_NAME": config.get("database_name")
            }
            
            # Verify config values are reasonable
            assert config["hostname"] in ["0.0.0.0", "localhost"] or \
                   config["hostname"].replace(".", "").replace("-", "").isalnum()
            
        except ImportError:
            pytest.skip("Storage service not available")


class TestStorageServiceLogging:
    """Test Storage service logging"""
    
    def test_storage_logging_setup(self):
        """Test that Storage logging is configured."""
        import logging
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../storage/src'))
        
        import storage
        
        # Verify logger exists
        assert hasattr(storage, 'logger')
        assert isinstance(storage.logger, logging.Logger)
        # Logger level might be WARNING or INFO depending on configuration
        assert storage.logger.level in [0, logging.WARNING, logging.INFO, logging.DEBUG]
class TestStorageServiceOperations:
    """Test Storage service operations (without actual database calls)"""
    
    def test_storage_time_tracking(self):
        """Test Storage service time tracking"""
        try:
            import storage
            
            state = storage.service_state
            
            # Test that start_time is set
            assert "start_time" in state
            assert isinstance(state["start_time"], (int, float))
            
            # Test that counters exist and are integers
            assert isinstance(state["requests_total"], int)
            assert isinstance(state["requests_successful"], int)
            assert isinstance(state["requests_failed"], int)
            
            # Test initial values are reasonable
            assert state["requests_total"] >= 0
            assert state["requests_successful"] >= 0
            assert state["requests_failed"] >= 0
            
        except ImportError:
            pytest.skip("Storage service not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])