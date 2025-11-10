"""
Unit tests for lib.common.config module
"""
import pytest
import os
import tempfile
from pathlib import Path
from digidig.config import Config


class TestConfig:
    """Test Config class functionality"""

    def test_config_initialization_default(self):
        """Test config initialization with default path"""
        config = Config.instance()
        assert isinstance(config, Config)
        assert config._config is not None

    def test_config_singleton(self):
        """Test singleton pattern"""
        config1 = Config.instance()
        config2 = Config.instance()
        assert config1 is config2

    def test_config_get_value(self):
        """Test getting configuration values"""
        config = Config.instance()

        # Test getting existing value
        db_config = config.get("database.postgres.host")
        assert db_config is not None

        # Test getting non-existing value with default
        default_value = config.get("non.existing.key", "default")
        assert default_value == "default"

    def test_config_get_section(self):
        """Test getting configuration sections"""
        config = Config.instance()
        db_section = config.get_section("database")
        assert isinstance(db_section, dict)
        assert "postgres" in db_section

    def test_config_deep_merge(self):
        """Test deep merge functionality"""
        config = Config.instance()

        base = {"a": {"b": 1, "c": 2}}
        override = {"a": {"b": 3, "d": 4}}

        config._deep_merge(base, override)

        assert base["a"]["b"] == 3  # overridden
        assert base["a"]["c"] == 2  # preserved
        assert base["a"]["d"] == 4  # added

    def test_load_config_with_custom_path(self):
        """Test loading config from custom path"""
        # Create temporary config file
        config_data = """
database:
  postgres:
    host: test_host
    port: 5433
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_data)
            temp_path = f.name

        try:
            config = Config(config_path=temp_path)
            assert config.get("database.postgres.host") == "test_host"
            assert config.get("database.postgres.port") == 5433
        finally:
            os.unlink(temp_path)

    def test_service_methods(self):
        """Test service configuration methods"""
        config = Config.instance()
        
        # Test db_config
        db_cfg = config.db_config("postgres")
        assert isinstance(db_cfg, dict)
        assert "host" in db_cfg
        
        # Test service_url
        url = config.service_url("identity")
        assert url.startswith("http://")
        
        # Test jwt_secret
        secret = config.jwt_secret()
        assert isinstance(secret, str)
        assert len(secret) > 0
        
        # Test admin_credentials
        creds = config.admin_credentials()
        assert isinstance(creds, dict)
        assert "email" in creds
        assert "password" in creds
