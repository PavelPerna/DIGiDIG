"""
Unit tests for Client service
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add service src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'client' / 'src'))

try:
    from client import app
    from config_loader import load_client_config
    CLIENT_AVAILABLE = True
except ImportError:
    CLIENT_AVAILABLE = False


@pytest.mark.skipif(not CLIENT_AVAILABLE, reason="Client service not available")
@pytest.mark.unit
class TestClientService:
    """Test cases for Client service"""
    
    def test_app_creation(self):
        """Test FastAPI app creation"""
        assert app is not None
        assert hasattr(app, 'routes')
    
    def test_load_client_config(self):
        """Test loading client configuration"""
        with patch('config_loader.get_config') as mock_get_config:
            mock_get_config.return_value = Mock()
            mock_get_config.return_value.get.return_value = {
                'identity_url': 'http://identity:8001',
                'storage_url': 'http://storage:8002'
            }
            
            config = load_client_config()
            assert config is not None


@pytest.mark.skipif(not CLIENT_AVAILABLE, reason="Client service not available")
@pytest.mark.unit
def test_client_service_imports():
    """Test that Client service modules can be imported"""
    assert 'client' in sys.modules


@pytest.mark.skipif(not CLIENT_AVAILABLE, reason="Client service not available")
@pytest.mark.unit
def test_client_static_files():
    """Test that static files path exists"""
    static_path = Path(__file__).parent.parent.parent / 'client' / 'src' / 'static'
    assert static_path.exists()


@pytest.mark.skipif(not CLIENT_AVAILABLE, reason="Client service not available")
@pytest.mark.unit
def test_client_templates():
    """Test that templates path exists"""
    templates_path = Path(__file__).parent.parent.parent / 'client' / 'src' / 'templates'
    assert templates_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])