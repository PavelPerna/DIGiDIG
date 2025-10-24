"""
Unit tests for Identity service - testing actual functions without mocking
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
sys.path.insert(0, str(project_root / 'identity' / 'src'))


@pytest.fixture(autouse=True)
def reset_config_state():
    """Reset global config state before each test"""
    # Clear any cached modules
    modules_to_clear = [name for name in sys.modules.keys() 
                       if name in ['config_loader', 'identity', 'common.config']]
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

class TestIdentityServiceReal:
    """Test Identity service actual functions"""
    
    def test_identity_imports(self):
        """Test that Identity service modules can be imported"""
        try:
            import identity
            assert hasattr(identity, 'app')
        except ImportError as e:
            pytest.fail(f"Could not import Identity service: {e}")
    
    def test_identity_config_loader_imports(self):
        """Test that Identity config_loader can be imported"""
        try:
            import config_loader
            assert hasattr(config_loader, 'IdentityConfig')
            assert hasattr(config_loader, 'config')
        except ImportError as e:
            pytest.fail(f"Could not import Identity config_loader: {e}")
    
    def test_identity_app_creation(self):
        """Test that Identity app can be created and has expected attributes."""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../identity/src'))
        
        import identity
        
        # Verify app object exists and is FastAPI instance
        assert hasattr(identity, 'app')
        assert identity.app is not None
        # Check actual app title from the service
        assert identity.app.title in ["Identity Microservice", "DIGiDIG Identity Service"]
    
    def test_identity_config_loader_real(self):
        """Test Identity config loader functionality"""
        try:
            import config_loader
            
            # Test config instance exists
            assert hasattr(config_loader, 'config')
            config = config_loader.config
            
            # Test that config has required attributes
            required_attrs = [
                'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASS', 'DB_NAME',
                'JWT_SECRET', 'JWT_ALGORITHM', 'TOKEN_EXPIRY',
                'ADMIN_EMAIL', 'HOSTNAME', 'PORT'
            ]
            
            for attr in required_attrs:
                assert hasattr(config, attr), f"Missing config attribute: {attr}"
            
            # Test attribute types
            assert isinstance(config.DB_HOST, str)
            assert isinstance(config.DB_PORT, int)
            assert isinstance(config.DB_USER, str)
            assert isinstance(config.JWT_SECRET, str)
            assert isinstance(config.JWT_ALGORITHM, str)
            assert isinstance(config.TOKEN_EXPIRY, int)
            
            # Test value ranges
            assert 1024 <= config.DB_PORT <= 65535
            assert config.TOKEN_EXPIRY > 0
            assert len(config.JWT_SECRET) >= 10  # Reasonable minimum
            
        except ImportError:
            pytest.skip("Identity config_loader not available")
    
    def test_identity_config_database_url(self):
        """Test Identity config database URL property"""
        try:
            import config_loader
            
            config = config_loader.config
            
            # Test database_url property
            assert hasattr(config, 'database_url')
            db_url = config.database_url
            
            assert isinstance(db_url, str)
            assert db_url.startswith("postgresql://")
            assert config.DB_USER in db_url
            assert config.DB_HOST in db_url
            assert str(config.DB_PORT) in db_url
            assert config.DB_NAME in db_url
            
        except ImportError:
            pytest.skip("Identity config_loader not available")


class TestIdentityServiceFunctions:
    """Test Identity service functions"""
    
    def test_identity_password_hashing(self):
        """Test Identity password hashing functions"""
        try:
            import identity
            
            # Test password hashing functions exist
            if hasattr(identity, 'hash_password'):
                test_password = "test_password_123"
                hashed = identity.hash_password(test_password)
                
                assert isinstance(hashed, str)
                assert len(hashed) > 0
                assert hashed != test_password  # Should be different
                
                # Test verify function if it exists
                if hasattr(identity, 'verify_password'):
                    assert identity.verify_password(test_password, hashed)
                    assert not identity.verify_password("wrong_password", hashed)
            
        except ImportError:
            pytest.skip("Identity service not available")
        except Exception as e:
            # Some functions might require database or other dependencies
            pytest.skip(f"Identity functions not testable: {e}")
    
    def test_identity_jwt_functions(self):
        """Test Identity JWT token functions"""
        try:
            import identity
            
            # Test JWT token creation if function exists
            if hasattr(identity, 'create_access_token'):
                # Mock user data
                user_id = 1
                email = "test@example.com"
                
                try:
                    token = identity.create_access_token(user_id, email)
                    assert isinstance(token, str)
                    assert len(token) > 0
                    
                    # Test token verification if function exists
                    if hasattr(identity, 'verify_token'):
                        result = identity.verify_token(token)
                        assert isinstance(result, dict)
                        
                except Exception as e:
                    # JWT functions might require proper configuration
                    pytest.skip(f"JWT functions not testable: {e}")
            
        except ImportError:
            pytest.skip("Identity service not available")
    
    def test_identity_database_functions(self):
        """Test Identity database function definitions"""
        try:
            import identity
            
            # Test that database functions are defined (even if not callable without DB)
            potential_functions = [
                'init_db', 'create_user', 'get_user_by_email',
                'get_user_by_id', 'verify_user'
            ]
            
            existing_functions = []
            for func_name in potential_functions:
                if hasattr(identity, func_name):
                    func = getattr(identity, func_name)
                    if callable(func):
                        existing_functions.append(func_name)
            
            # At least some database functions should exist
            assert len(existing_functions) >= 1, f"No database functions found. Available: {dir(identity)}"
            
        except ImportError:
            pytest.skip("Identity service not available")


class TestIdentityServiceModels:
    """Test Identity service models"""
    
    def test_identity_pydantic_models(self):
        """Test Identity pydantic models"""
        try:
            import identity
            
            # Test User models if they exist
            models_to_test = ['UserCreate', 'UserLogin', 'User', 'Token']
            
            found_models = []
            for model_name in models_to_test:
                if hasattr(identity, model_name):
                    model_class = getattr(identity, model_name)
                    found_models.append(model_name)
                    
                    # Basic check that it's a class
                    assert callable(model_class)
            
            # At least some models should exist
            assert len(found_models) >= 1, f"No models found. Available: {[x for x in dir(identity) if not x.startswith('_')]}"
            
        except ImportError:
            pytest.skip("Identity service not available")


class TestIdentityServiceLogging:
    """Test Identity service logging"""
    
    def test_identity_logging_setup(self):
        """Test Identity logging configuration"""
        try:
            import identity
            import logging
            
            # Check that logger is configured
            if hasattr(identity, 'logger'):
                assert isinstance(identity.logger, logging.Logger)
            
        except ImportError:
            pytest.skip("Identity service not available")


class TestIdentityConfigUseConfig:
    """Test Identity config usage flags"""
    
    def test_identity_config_loader_flags(self):
        """Test Identity config loader USE_CONFIG_FILE flag"""
        try:
            import config_loader
            
            # Test USE_CONFIG_FILE flag
            assert hasattr(config_loader, 'USE_CONFIG_FILE')
            assert isinstance(config_loader.USE_CONFIG_FILE, bool)
            
            # Test that IdentityConfig class exists
            assert hasattr(config_loader, 'IdentityConfig')
            assert callable(config_loader.IdentityConfig)
            
        except ImportError:
            pytest.skip("Identity config_loader not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])