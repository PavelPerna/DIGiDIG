"""
Unit tests for lib.common.config module
"""
import pytest
import os
import tempfile
from pathlib import Path
from digidig.config import Config, get_config, load_config


class TestConfig:
    """Test Config class functionality"""

    def test_config_initialization_default(self):
        """Test config initialization with default path"""
        config = Config()
        assert isinstance(config, Config)
        assert config._config is not None

    def test_config_get_value(self):
        """Test getting configuration values"""
        config = Config()

        # Test getting existing value
        db_config = config.get("database.postgres.host")
        assert db_config is not None

        # Test getting non-existing value with default
        default_value = config.get("non.existing.key", "default")
        assert default_value == "default"

    def test_config_get_section(self):
        """Test getting configuration sections"""
        config = Config()
        db_section = config.get_section("database")
        assert isinstance(db_section, dict)
        assert "postgres" in db_section

    def test_config_deep_merge(self):
        """Test deep merge functionality"""
        config = Config()

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


def test_get_config_singleton():
    """Test that get_config returns singleton instance"""
    config1 = get_config()
    config2 = get_config()

    assert config1 is config2


def test_load_config_function():
    """Test load_config convenience function"""
    config = load_config()
    assert isinstance(config, Config)


def test_get_service_url():
    """Test get_service_url convenience function"""
    from digidig.config import get_service_url

    url = get_service_url("identity")
    assert url.startswith("http://")


def test_get_jwt_secret():
    """Test get_jwt_secret convenience function"""
    from digidig.config import get_jwt_secret

    secret = get_jwt_secret()
    assert isinstance(secret, str)
    assert len(secret) > 0


def test_get_admin_credentials():
    """Test get_admin_credentials convenience function"""
    from digidig.config import get_admin_credentials

    creds = get_admin_credentials()
    assert isinstance(creds, dict)
    assert "email" in creds
    assert "password" in creds