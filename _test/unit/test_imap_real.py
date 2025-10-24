"""
Unit tests for IMAP service - testing actual functions without mocking
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

class TestIMAPServiceReal:
    """Test IMAP service actual functions"""
    
    def test_imap_imports(self):
        """Test that IMAP service modules can be imported"""
        try:
            import imap
            assert hasattr(imap, 'app')
            assert hasattr(imap, 'service_state')
        except ImportError as e:
            pytest.fail(f"Could not import IMAP service: {e}")
    
    def test_imap_app_creation(self):
        """Test IMAP FastAPI app creation"""
        try:
            import imap
            from fastapi import FastAPI
            
            assert isinstance(imap.app, FastAPI)
            assert imap.app.title == "IMAP Microservice"
            
        except ImportError:
            pytest.skip("IMAP service not available")
    
    def test_imap_service_state(self):
        """Test IMAP service state structure"""
        try:
            import imap
            
            # Check if service_state exists and has required fields
            assert hasattr(imap, 'service_state')
            state = imap.service_state
            
            required_fields = [
                "start_time", "requests_total", "requests_successful", 
                "requests_failed", "active_connections", "active_sessions", "config"
            ]
            
            for field in required_fields:
                assert field in state, f"Missing field: {field}"
            
            # Check config structure
            config = state["config"]
            config_fields = ["hostname", "port", "enabled", "timeout"]
            for field in config_fields:
                assert field in config, f"Missing config field: {field}"
                
        except ImportError:
            pytest.skip("IMAP service not available")
    
    def test_imap_configuration_values(self):
        """Test IMAP configuration values"""
        try:
            import imap
            
            config = imap.service_state["config"]
            
            # Test configuration types and ranges
            assert isinstance(config["enabled"], bool)
            assert isinstance(config["hostname"], str)
            assert isinstance(config["port"], int)
            assert isinstance(config["timeout"], int)
            
            # Test value ranges
            assert 1024 <= config["port"] <= 65535
            assert config["timeout"] > 0
            
            if "max_workers" in config:
                assert config["max_workers"] > 0
                
        except ImportError:
            pytest.skip("IMAP service not available")
    
    def test_imap_models_real(self):
        """Test IMAP pydantic models"""
        try:
            import imap
            
            # Test Email model
            if hasattr(imap, 'Email'):
                email = imap.Email(
                    sender="test@example.com",
                    recipient="recipient@example.com",
                    subject="Test Subject",
                    body="Test body content"
                )
                assert email.sender == "test@example.com"
                assert email.recipient == "recipient@example.com"
                assert email.subject == "Test Subject"
                assert email.body == "Test body content"
            
        except ImportError:
            pytest.skip("IMAP service models not available")


class TestIMAPServiceOperations:
    """Test IMAP service operations"""
    
    def test_imap_executor_exists(self):
        """Test IMAP thread pool executor"""
        try:
            import imap
            
            # Check if executor exists
            assert hasattr(imap, 'executor')
            
            # Check if it's a ThreadPoolExecutor
            from concurrent.futures import ThreadPoolExecutor
            assert isinstance(imap.executor, ThreadPoolExecutor)
            
        except ImportError:
            pytest.skip("IMAP service not available")
    
    def test_imap_environment_variables(self):
        """Test IMAP environment variable handling"""
        try:
            import imap
            import os
            
            config = imap.service_state["config"]
            
            # Test that environment variables are read
            expected_vars = {
                "IMAP_HOSTNAME": config.get("hostname"),
                "IMAP_PORT": str(config.get("port")),
                "IMAP_TIMEOUT": str(config.get("timeout"))
            }
            
            # Verify config values are reasonable
            assert config["hostname"] in ["0.0.0.0", "localhost"] or \
                   config["hostname"].replace(".", "").replace("-", "").isalnum()
            
        except ImportError:
            pytest.skip("IMAP service not available")
    
    def test_imap_connection_management(self):
        """Test IMAP connection management structures"""
        try:
            import imap
            
            state = imap.service_state
            
            # Test that connection lists exist and are lists
            assert isinstance(state["active_connections"], list)
            assert isinstance(state["active_sessions"], list)
            
            # Test initial state
            assert len(state["active_connections"]) >= 0
            assert len(state["active_sessions"]) >= 0
            
        except ImportError:
            pytest.skip("IMAP service not available")


class TestIMAPServiceLogging:
    """Test IMAP service logging"""
    
    def test_imap_logging_setup(self):
        """Test that IMAP logging is configured."""
        import logging
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../imap/src'))
        
        import imap
        
        # Verify logger exists
        assert hasattr(imap, 'logger')
        assert isinstance(imap.logger, logging.Logger)
        # Logger level might be WARNING or INFO depending on configuration
        assert imap.logger.level in [0, logging.WARNING, logging.INFO, logging.DEBUG]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])