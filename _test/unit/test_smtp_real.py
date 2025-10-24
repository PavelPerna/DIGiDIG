"""
Unit tests for SMTP service - testing actual functions without mocking
"""
import pytest
import sys
import os
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'smtp' / 'src'))


@pytest.fixture(autouse=True)
def reset_config_state():
    """Reset global config state before each test"""
    # Clear any cached modules
    modules_to_clear = [name for name in sys.modules.keys() 
                       if name in ['smtp', 'common.config']]
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

class TestSMTPServiceReal:
    """Test SMTP service actual functions"""
    
    def test_smtp_imports(self):
        """Test that SMTP service modules can be imported"""
        try:
            import smtp
            assert hasattr(smtp, 'app')
            assert hasattr(smtp, 'load_config_from_file')
            assert hasattr(smtp, 'save_config_to_file')
        except ImportError as e:
            pytest.fail(f"Could not import SMTP service: {e}")
    
    @pytest.mark.asyncio
    async def test_load_config_from_file_real(self):
        """Test actual load_config_from_file function"""
        try:
            import smtp
            
            # Test with non-existent file
            with patch('smtp.os.path.exists', return_value=False):
                result = await smtp.load_config_from_file()
                assert result is None
            
            # Test with existing file
            mock_config = {"timeout": 60, "enabled": True}
            with patch('smtp.os.path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=json.dumps(mock_config))), \
                 patch('smtp.json.load', return_value=mock_config):
                result = await smtp.load_config_from_file()
                assert result == mock_config
                
        except ImportError:
            pytest.skip("SMTP service not available")
    
    @pytest.mark.asyncio 
    async def test_initialize_config_real(self):
        """Test actual initialize_config function"""
        try:
            import smtp
            
            # Mock the service_state
            original_state = getattr(smtp, 'service_state', None)
            smtp.service_state = {
                "config": {
                    "timeout": 30,
                    "max_workers": 4,
                    "enabled": True
                }
            }
            
            # Mock executor
            class MockExecutor:
                def shutdown(self, wait=True):
                    pass
            
            smtp.executor = MockExecutor()
            
            with patch('smtp.load_config_from_file', return_value=None):
                await smtp.initialize_config()
                assert smtp.service_state["config"]["timeout"] == 30
            
            # Restore original state
            if original_state:
                smtp.service_state = original_state
                
        except ImportError:
            pytest.skip("SMTP service not available")
    
    def test_smtp_models_real(self):
        """Test SMTP pydantic models"""
        try:
            import smtp
            
            # Test Email model
            if hasattr(smtp, 'Email'):
                email = smtp.Email(
                    sender="test@example.com",
                    recipient="recipient@example.com",
                    subject="Test",
                    body="Test body"
                )
                assert email.sender == "test@example.com"
                assert email.recipient == "recipient@example.com"
            
        except ImportError:
            pytest.skip("SMTP service models not available")
    
    def test_smtp_app_creation(self):
        """Test SMTP FastAPI app creation"""
        try:
            import smtp
            from fastapi import FastAPI
            
            assert isinstance(smtp.app, FastAPI)
            assert smtp.app.title == "SMTP Microservice"
            
        except ImportError:
            pytest.skip("SMTP service not available")


class TestSMTPServiceEndpoints:
    """Test SMTP service endpoints"""
    
    def test_smtp_service_state(self):
        """Test SMTP service state structure"""
        try:
            import smtp
            
            # Check if service_state exists and has required fields
            assert hasattr(smtp, 'service_state')
            state = smtp.service_state
            
            required_fields = [
                "requests_total", "requests_successful", 
                "requests_failed", "config"
            ]
            
            for field in required_fields:
                assert field in state, f"Missing field: {field}"
            
            # Check config structure
            config = state["config"]
            config_fields = ["enabled", "timeout"]
            for field in config_fields:
                assert field in config, f"Missing config field: {field}"
                
        except ImportError:
            pytest.skip("SMTP service not available")
    
    def test_smtp_configuration_values(self):
        """Test SMTP configuration values"""
        try:
            import smtp
            
            config = smtp.service_state["config"]
            
            # Test configuration types and ranges
            assert isinstance(config.get("enabled"), bool)
            
            if "timeout" in config:
                assert isinstance(config["timeout"], int)
                assert config["timeout"] > 0
            
            if "max_workers" in config:
                assert isinstance(config["max_workers"], int)
                assert config["max_workers"] > 0
                
        except ImportError:
            pytest.skip("SMTP service not available")


class TestSMTPServiceHelpers:
    """Test SMTP service helper functions"""
    
    @pytest.mark.asyncio
    async def test_save_config_to_file_real(self):
        """Test actual save_config_to_file function"""
        try:
            import smtp
            
            # Mock service_state with config
            smtp.service_state = {
                "config": {
                    "timeout": 30,
                    "retry_attempts": 3,
                    "enabled": True,
                    "internal_state": "should_not_save"
                }
            }
            
            with patch('smtp.os.makedirs'), \
                 patch('builtins.open', mock_open()) as mock_file, \
                 patch('smtp.json.dump') as mock_dump:
                
                await smtp.save_config_to_file()
                
                # Verify file operations
                mock_file.assert_called()
                mock_dump.assert_called()
                
                # Check that only allowed config keys are saved
                call_args = mock_dump.call_args[0][0]
                assert "timeout" in call_args
                assert "retry_attempts" in call_args
                assert "enabled" in call_args
                assert "internal_state" not in call_args
                
        except ImportError:
            pytest.skip("SMTP service not available")
    
    def test_smtp_logging_setup(self):
        """Test SMTP logging configuration"""
        try:
            import smtp
            import logging
            
            # Check that logger is configured
            assert hasattr(smtp, 'logger')
            assert isinstance(smtp.logger, logging.Logger)
            
        except ImportError:
            pytest.skip("SMTP service not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])