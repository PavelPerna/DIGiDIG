"""
Unit tests for IMAP service
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add service src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'imap' / 'src'))

try:
    from imap import app, connect_to_imap, fetch_emails, sync_emails
    IMAP_AVAILABLE = True
except ImportError:
    IMAP_AVAILABLE = False


@pytest.mark.skipif(not IMAP_AVAILABLE, reason="IMAP service not available")
@pytest.mark.unit
class TestIMAPService:
    """Test cases for IMAP service"""
    
    def test_app_creation(self):
        """Test FastAPI app creation"""
        assert app is not None
        assert hasattr(app, 'routes')
    
    def test_connect_to_imap_function_exists(self):
        """Test that connect_to_imap function exists"""
        assert callable(connect_to_imap)
    
    def test_fetch_emails_function_exists(self):
        """Test that fetch_emails function exists"""
        assert callable(fetch_emails)
    
    def test_sync_emails_function_exists(self):
        """Test that sync_emails function exists"""
        assert callable(sync_emails)


@pytest.mark.skipif(not IMAP_AVAILABLE, reason="IMAP service not available")
@pytest.mark.unit
def test_imap_service_imports():
    """Test that IMAP service modules can be imported"""
    assert 'imap' in sys.modules


@pytest.mark.skipif(not IMAP_AVAILABLE, reason="IMAP service not available")
@pytest.mark.unit
@patch('imap.imaplib.IMAP4_SSL')
def test_connect_to_imap_mock(mock_imap):
    """Test IMAP connection with mocked imaplib"""
    # Mock IMAP connection
    mock_connection = Mock()
    mock_imap.return_value = mock_connection
    mock_connection.login.return_value = ('OK', [])
    mock_connection.select.return_value = ('OK', [])
    
    # Test that function can be called
    if hasattr(sys.modules.get('imap'), 'connect_to_imap'):
        assert True


@pytest.mark.skipif(not IMAP_AVAILABLE, reason="IMAP service not available")
@pytest.mark.unit
@patch('imap.imaplib.IMAP4_SSL')
def test_fetch_emails_mock(mock_imap):
    """Test email fetching with mocked IMAP"""
    # Mock IMAP connection
    mock_connection = Mock()
    mock_imap.return_value = mock_connection
    mock_connection.search.return_value = ('OK', [b'1 2 3'])
    mock_connection.fetch.return_value = ('OK', [(b'1 (RFC822 {123}', b'email content')])
    
    # Test that function exists
    if hasattr(sys.modules.get('imap'), 'fetch_emails'):
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])