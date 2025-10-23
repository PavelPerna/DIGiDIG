"""
Unit tests for configuration management system
"""
import pytest
import tempfile
import os
from pathlib import Path
import yaml

# Add common to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'common'))

from config import Config, get_config, get_db_config, get_service_url, get_jwt_secret


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory with test configs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "config"
        config_dir.mkdir()
        
        # Create base config
        base_config = {
            "database": {
                "postgres": {
                    "host": "postgres",
                    "port": 5432,
                    "user": "testuser",
                    "password": "testpass",
                    "database": "testdb"
                }
            },
            "security": {
                "jwt": {
                    "secret": "test_secret_123",
                    "algorithm": "HS256"
                }
            },
            "services": {
                "storage": {"url": "http://storage:8002"},
                "smtp": {"rest_url": "http://smtp:8000"}
            }
        }
        
        with open(config_dir / "config.yaml", "w") as f:
            yaml.dump(base_config, f)
        
        # Create test override
        test_override = {
            "database": {
                "postgres": {
                    "host": "test-postgres",
                    "password": "test_override_pass"
                }
            },
            "test": {
                "enabled": True
            }
        }
        
        with open(config_dir / "config.test.yaml", "w") as f:
            yaml.dump(test_override, f)
        
        yield config_dir


def test_config_loads_base_config(temp_config_dir):
    """Test that base config is loaded correctly"""
    config = Config(config_path=temp_config_dir / "config.yaml")
    
    assert config.get("database.postgres.host") == "postgres"
    assert config.get("database.postgres.port") == 5432
    assert config.get("database.postgres.user") == "testuser"
    assert config.get("security.jwt.secret") == "test_secret_123"


def test_config_environment_override(temp_config_dir):
    """Test that environment-specific config overrides base"""
    config = Config(config_path=temp_config_dir / "config.yaml", env="test")
    
    # Overridden values
    assert config.get("database.postgres.host") == "test-postgres"
    assert config.get("database.postgres.password") == "test_override_pass"
    
    # Non-overridden values preserved
    assert config.get("database.postgres.user") == "testuser"
    assert config.get("database.postgres.port") == 5432
    
    # New values from override
    assert config.get("test.enabled") == True


def test_config_get_with_default(temp_config_dir):
    """Test get() with default value"""
    config = Config(config_path=temp_config_dir / "config.yaml")
    
    # Existing key
    assert config.get("database.postgres.host") == "postgres"
    
    # Non-existing key with default
    assert config.get("nonexistent.key", "default_value") == "default_value"
    
    # Non-existing key without default
    assert config.get("nonexistent.key") is None


def test_config_get_section(temp_config_dir):
    """Test getting entire configuration section"""
    config = Config(config_path=temp_config_dir / "config.yaml")
    
    db_section = config.get_section("database.postgres")
    
    assert isinstance(db_section, dict)
    assert db_section["host"] == "postgres"
    assert db_section["port"] == 5432
    assert db_section["user"] == "testuser"


def test_config_dict_access(temp_config_dir):
    """Test dict-like access to config"""
    config = Config(config_path=temp_config_dir / "config.yaml")
    
    # Dict-like access for top-level keys
    assert config["database"] is not None
    assert config["security"] is not None


def test_convenience_functions(temp_config_dir):
    """Test convenience functions for common config access"""
    # Note: These use global config instance, need to test differently
    # or refactor to accept config instance
    pass


def test_deep_merge(temp_config_dir):
    """Test that deep merge works correctly"""
    config = Config(config_path=temp_config_dir / "config.yaml", env="test")
    
    # Check that nested values are merged correctly
    postgres_config = config.get_section("database.postgres")
    
    # Overridden values
    assert postgres_config["host"] == "test-postgres"
    assert postgres_config["password"] == "test_override_pass"
    
    # Preserved values
    assert postgres_config["user"] == "testuser"
    assert postgres_config["port"] == 5432
    assert postgres_config["database"] == "testdb"


def test_config_missing_file():
    """Test behavior when config file doesn't exist"""
    with pytest.raises(FileNotFoundError):
        Config(config_path="/nonexistent/path/config.yaml")


def test_config_all_property(temp_config_dir):
    """Test getting entire configuration"""
    config = Config(config_path=temp_config_dir / "config.yaml")
    
    all_config = config.all
    
    assert isinstance(all_config, dict)
    assert "database" in all_config
    assert "security" in all_config
    assert "services" in all_config


def test_nested_path_access(temp_config_dir):
    """Test deeply nested path access"""
    config = Config(config_path=temp_config_dir / "config.yaml")
    
    # Deep nesting
    assert config.get("services.storage.url") == "http://storage:8002"
    assert config.get("services.smtp.rest_url") == "http://smtp:8000"
    
    # Invalid deep path
    assert config.get("services.nonexistent.url") is None
    assert config.get("services.storage.nonexistent.key", "default") == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
