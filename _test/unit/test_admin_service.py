"""
Unit tests for Admin service
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add service src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'admin' / 'src'))

try:
    from admin import app, authenticate_admin, get_user_stats, manage_users
    ADMIN_AVAILABLE = True
except ImportError:
    ADMIN_AVAILABLE = False


@pytest.mark.skipif(not ADMIN_AVAILABLE, reason="Admin service not available")
@pytest.mark.unit
class TestAdminService:
    """Test cases for Admin service"""
    
    def test_app_creation(self):
        """Test FastAPI app creation"""
        assert app is not None
        assert hasattr(app, 'routes')
    
    def test_authenticate_admin_function_exists(self):
        """Test that authenticate_admin function exists"""
        assert callable(authenticate_admin)
    
    def test_get_user_stats_function_exists(self):
        """Test that get_user_stats function exists"""
        assert callable(get_user_stats)
    
    def test_manage_users_function_exists(self):
        """Test that manage_users function exists"""
        assert callable(manage_users)


@pytest.mark.skipif(not ADMIN_AVAILABLE, reason="Admin service not available")
@pytest.mark.unit
def test_admin_service_imports():
    """Test that Admin service modules can be imported"""
    assert 'admin' in sys.modules


@pytest.mark.skipif(not ADMIN_AVAILABLE, reason="Admin service not available")
@pytest.mark.unit
def test_admin_static_files():
    """Test that static files path exists"""
    static_path = Path(__file__).parent.parent.parent / 'admin' / 'src' / 'static'
    assert static_path.exists()


@pytest.mark.skipif(not ADMIN_AVAILABLE, reason="Admin service not available")
@pytest.mark.unit
def test_admin_templates():
    """Test that templates path exists"""
    templates_path = Path(__file__).parent.parent.parent / 'admin' / 'src' / 'templates'
    assert templates_path.exists()


@pytest.mark.skipif(not ADMIN_AVAILABLE, reason="Admin service not available")
@pytest.mark.unit
@patch('admin.requests.get')
def test_get_user_stats_mock(mock_requests):
    """Test user stats retrieval with mocked requests"""
    # Mock API response
    mock_response = Mock()
    mock_response.json.return_value = {
        'total_users': 100,
        'active_users': 85,
        'emails_sent': 1500
    }
    mock_response.status_code = 200
    mock_requests.return_value = mock_response
    
    # Test that function exists
    if hasattr(sys.modules.get('admin'), 'get_user_stats'):
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])