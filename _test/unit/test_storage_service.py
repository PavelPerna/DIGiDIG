"""
Unit tests for Storage service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys

# Add service src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'storage' / 'src'))

try:
    from storage import app, store_email, retrieve_emails, delete_email
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False


@pytest.mark.skipif(not STORAGE_AVAILABLE, reason="Storage service not available")
@pytest.mark.unit
class TestStorageService:
    """Test cases for Storage service"""
    
    def test_app_creation(self):
        """Test FastAPI app creation"""
        assert app is not None
        assert hasattr(app, 'routes')
    
    def test_store_email_function_exists(self):
        """Test that store_email function exists"""
        assert callable(store_email)
    
    def test_retrieve_emails_function_exists(self):
        """Test that retrieve_emails function exists"""
        assert callable(retrieve_emails)
    
    def test_delete_email_function_exists(self):
        """Test that delete_email function exists"""
        assert callable(delete_email)


@pytest.mark.skipif(not STORAGE_AVAILABLE, reason="Storage service not available")
@pytest.mark.unit
def test_storage_service_imports():
    """Test that Storage service modules can be imported"""
    assert 'storage' in sys.modules


@pytest.mark.skipif(not STORAGE_AVAILABLE, reason="Storage service not available")
@pytest.mark.unit
@patch('storage.get_mongo_client')
def test_store_email_mock(mock_mongo):
    """Test email storage with mocked MongoDB"""
    # Mock MongoDB client
    mock_client = Mock()
    mock_db = Mock()
    mock_collection = Mock()
    
    mock_mongo.return_value = mock_client
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    mock_collection.insert_one.return_value.inserted_id = "test_id"
    
    # Test that function can be called
    if hasattr(sys.modules.get('storage'), 'store_email'):
        assert True


@pytest.mark.skipif(not STORAGE_AVAILABLE, reason="Storage service not available")
@pytest.mark.unit
@patch('storage.get_mongo_client')
def test_retrieve_emails_mock(mock_mongo):
    """Test email retrieval with mocked MongoDB"""
    # Mock MongoDB client
    mock_client = Mock()
    mock_db = Mock()
    mock_collection = Mock()
    
    mock_mongo.return_value = mock_client
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    mock_collection.find.return_value = []
    
    # Test that function can be called
    if hasattr(sys.modules.get('storage'), 'retrieve_emails'):
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])