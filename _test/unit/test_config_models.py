"""
Unit tests for config models (pydantic models)
"""
import pytest
from datetime import datetime
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.config_models import ServiceConfig, SMTPConfig, IMAPConfig, StorageConfig, IdentityConfig, ServiceStats, ServiceHealth


@pytest.mark.unit
def test_service_config_defaults():
    """Test ServiceConfig with default values"""
    config = ServiceConfig(
        service_name="test_service",
        port=8080
    )
    
    assert config.service_name == "test_service"
    assert config.hostname == "0.0.0.0"
    assert config.port == 8080
    assert config.max_workers == 4
    assert config.pool_size == 10
    assert config.enabled == True
    assert config.timeout == 30
    assert config.retry_attempts == 3
    assert config.retry_delay == 2
    assert config.custom_config is None


@pytest.mark.unit
def test_service_config_custom_values():
    """Test ServiceConfig with custom values"""
    custom_data = {"feature_flags": {"new_ui": True}}
    
    config = ServiceConfig(
        service_name="custom_service",
        hostname="localhost",
        port=9000,
        max_workers=8,
        pool_size=20,
        enabled=False,
        timeout=60,
        retry_attempts=5,
        retry_delay=1,
        custom_config=custom_data
    )
    
    assert config.hostname == "localhost"
    assert config.max_workers == 8
    assert config.pool_size == 20
    assert config.enabled == False
    assert config.timeout == 60
    assert config.retry_attempts == 5
    assert config.retry_delay == 1
    assert config.custom_config == custom_data


@pytest.mark.unit
def test_smtp_config_defaults():
    """Test SMTPConfig with default values"""
    config = SMTPConfig()
    
    assert config.service_name == "smtp"
    assert config.port == 8000
    assert config.auth_required == True
    assert config.auth_require_tls == False
    assert config.max_message_size == 10485760  # 10MB
    assert config.queue_size == 100


@pytest.mark.unit
def test_smtp_config_custom():
    """Test SMTPConfig with custom values"""
    config = SMTPConfig(
        hostname="smtp.example.com",
        port=587,
        auth_require_tls=True,
        max_message_size=5242880,  # 5MB
        queue_size=50
    )
    
    assert config.hostname == "smtp.example.com"
    assert config.port == 587
    assert config.auth_require_tls == True
    assert config.max_message_size == 5242880
    assert config.queue_size == 50


@pytest.mark.unit
def test_imap_config():
    """Test IMAPConfig"""
    config = IMAPConfig(
        hostname="imap.example.com",
        port=993,
        max_connections=100,
        idle_timeout=600
    )
    
    assert config.service_name == "imap"
    assert config.hostname == "imap.example.com"
    assert config.port == 993
    assert config.max_connections == 100
    assert config.idle_timeout == 600


@pytest.mark.unit
def test_storage_config():
    """Test StorageConfig"""
    config = StorageConfig(
        mongo_uri="mongodb://localhost:27017",
        database_name="test_db",
        max_document_size=8388608
    )
    
    assert config.service_name == "storage"
    assert config.port == 8002
    assert config.mongo_uri == "mongodb://localhost:27017"
    assert config.database_name == "test_db"
    assert config.max_document_size == 8388608


@pytest.mark.unit
def test_identity_config():
    """Test IdentityConfig"""
    config = IdentityConfig(
        jwt_secret="test_secret_key",
        db_user="test_user",
        db_password="test_pass",
        token_expiry=7200,
        db_host="localhost",
        db_name="test_db"
    )
    
    assert config.service_name == "identity"
    assert config.port == 8001
    assert config.jwt_secret == "test_secret_key"
    assert config.token_expiry == 7200
    assert config.refresh_token_expiry == 1209600  # Default
    assert config.db_host == "localhost"
    assert config.db_name == "test_db"
    assert config.db_user == "test_user"
    assert config.db_password == "test_pass"


@pytest.mark.unit
def test_service_stats():
    """Test ServiceStats model"""
    from datetime import datetime
    
    now = datetime.now()
    stats = ServiceStats(
        service_name="test_service",
        uptime_seconds=3600.5,
        requests_total=1000,
        requests_successful=950,
        requests_failed=50,
        last_request_time=now,
        custom_stats={"memory_usage": "128MB"}
    )
    
    assert stats.service_name == "test_service"
    assert stats.uptime_seconds == 3600.5
    assert stats.requests_total == 1000
    assert stats.requests_successful == 950
    assert stats.requests_failed == 50
    assert stats.last_request_time == now
    assert stats.custom_stats == {"memory_usage": "128MB"}


@pytest.mark.unit
def test_service_stats_defaults():
    """Test ServiceStats with default values"""
    stats = ServiceStats(
        service_name="simple_service",
        uptime_seconds=100.0
    )
    
    assert stats.requests_total == 0
    assert stats.requests_successful == 0
    assert stats.requests_failed == 0
    assert stats.last_request_time is None
    assert stats.custom_stats is None


@pytest.mark.unit
def test_service_health():
    """Test ServiceHealth model"""
    from datetime import datetime
    
    now = datetime.now()
    health = ServiceHealth(
        service_name="test_service",
        status="healthy",
        timestamp=now,
        details={"response_time": "50ms", "db_connection": "ok"}
    )
    
    assert health.service_name == "test_service"
    assert health.status == "healthy"
    assert health.timestamp == now
    assert health.details == {"response_time": "50ms", "db_connection": "ok"}


@pytest.mark.unit
def test_service_health_minimal():
    """Test ServiceHealth with minimal required fields"""
    from datetime import datetime
    
    now = datetime.now()
    health = ServiceHealth(
        service_name="minimal_service",
        status="degraded",
        timestamp=now
    )
    
    assert health.service_name == "minimal_service"
    assert health.status == "degraded"
    assert health.timestamp == now
    assert health.details is None


@pytest.mark.unit
def test_config_validation_errors():
    """Test that pydantic validation works for invalid data"""
    # Test missing required fields - ServiceConfig requires service_name and port
    with pytest.raises(ValueError):
        ServiceConfig(service_name="test")  # Missing port
    
    # Test missing required fields in IdentityConfig
    with pytest.raises(ValueError):
        IdentityConfig(jwt_secret="secret", db_user="user")  # Missing db_password


@pytest.mark.unit
def test_config_model_json_serialization():
    """Test that config models can be serialized to JSON"""
    config = SMTPConfig(
        hostname="test.smtp.com",
        port=587,
        max_message_size=1024000
    )
    
    # Should be able to convert to dict
    config_dict = config.model_dump()
    assert isinstance(config_dict, dict)
    assert config_dict["hostname"] == "test.smtp.com"
    assert config_dict["port"] == 587
    
    # Should be able to convert to JSON string
    json_str = config.model_dump_json()
    assert isinstance(json_str, str)
    assert "test.smtp.com" in json_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])