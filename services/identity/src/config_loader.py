"""
Configuration wrapper for Identity Service
Provides backward compatibility during migration from ENV to config files
"""
import os
import logging

# Try to load new config system, fallback to ENV variables
try:
    from lib.common.config import get_config, get_db_config, get_jwt_secret
    USE_CONFIG_FILE = True
    logger = logging.getLogger(__name__)
    logger.info("Using YAML configuration system")
except ImportError:
    USE_CONFIG_FILE = False
    logger = logging.getLogger(__name__)
    logger.warning("Common config module not found, using ENV variables")


class IdentityConfig:
    """Configuration manager with fallback support"""
    
    def __init__(self):
        if USE_CONFIG_FILE:
            self._load_from_config()
        else:
            self._load_from_env()
    
    def _load_from_config(self):
        """Load configuration from YAML files"""
        config = get_config()
        db = get_db_config("postgres")
        
        # Database configuration
        self.DB_HOST = db["host"]
        self.DB_PORT = db["port"]
        self.DB_USER = db["user"]
        self.DB_PASS = db["password"]
        self.DB_NAME = db["database"]
        
        # JWT configuration
        self.JWT_SECRET = get_jwt_secret()
        self.JWT_ALGORITHM = config.get("security.jwt.algorithm", "HS256")
        self.TOKEN_EXPIRY = config.get("security.jwt.access_token_expire_minutes", 30) * 60
        self.REFRESH_TOKEN_EXPIRY = config.get("security.jwt.refresh_token_expire_days", 7) * 86400
        
        # Admin credentials
        admin = config.get_section("security.admin")
        self.ADMIN_EMAIL = admin.get("email", "admin@example.com")
        self.ADMIN_PASSWORD = admin.get("password", "admin")
        
        # Service configuration
        identity_service = config.get_section("services.identity")
        self.HOSTNAME = identity_service.get("host", "0.0.0.0")
        self.PORT = identity_service.get("port", 8001)
        
        # Aliases for backward compatibility
        self.IDENTITY_HOSTNAME = self.HOSTNAME
        self.IDENTITY_PORT = self.PORT
        
        # Timeout and other settings
        self.TIMEOUT = config.get("services.identity.timeout", 30)
        self.IDENTITY_TIMEOUT = self.TIMEOUT
        
        # Cookie configuration
        cookie_config = config.get_section("security.cookie")
        self.COOKIE_SECURE = cookie_config.get("secure", False)
        self.COOKIE_SAMESITE = cookie_config.get("samesite", "lax")
        
        # Logging
        self.LOG_LEVEL = config.get("logging.level", "INFO")
    
    def _load_from_env(self):
        """Fallback: Load configuration from ENV variables"""
        # Database configuration
        self.DB_HOST = os.getenv("DB_HOST", "postgres")
        self.DB_PORT = int(os.getenv("DB_PORT", "5432"))
        self.DB_USER = os.getenv("DB_USER", "strategos")
        self.DB_PASS = os.getenv("DB_PASS", "strategos_password")
        self.DB_NAME = os.getenv("DB_NAME", "strategos_db")
        
        # JWT configuration
        self.JWT_SECRET = os.getenv("JWT_SECRET", "b8_XYZ123abc456DEF789ghiJKL0mnoPQ")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.TOKEN_EXPIRY = int(os.getenv("TOKEN_EXPIRY", "3600"))
        self.REFRESH_TOKEN_EXPIRY = int(os.getenv("REFRESH_TOKEN_EXPIRY", str(7 * 86400)))
        
        # Admin credentials
        self.ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
        self.ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
        
        # Service configuration
        self.HOSTNAME = os.getenv("IDENTITY_HOSTNAME", "0.0.0.0")
        self.PORT = int(os.getenv("IDENTITY_PORT", "8001"))
        self.TIMEOUT = int(os.getenv("IDENTITY_TIMEOUT", "30"))
        
        # Aliases
        self.IDENTITY_HOSTNAME = self.HOSTNAME
        self.IDENTITY_PORT = self.PORT
        self.IDENTITY_TIMEOUT = self.TIMEOUT
        
        # Cookie configuration
        self.COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
        self.COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def database_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


# Global configuration instance
# Skip config loading in test environment to avoid file path issues
if os.getenv("SKIP_COMPOSE") == "1":
    # In test environment, create a minimal config for testing
    class TestConfig:
        def __init__(self):
            # Minimal config for testing
            self.IDENTITY_HOSTNAME = "localhost"
            self.IDENTITY_PORT = 8001
            self.IDENTITY_TIMEOUT = 30
            self.JWT_SECRET = "test_secret_key"
            self.TOKEN_EXPIRY = 3600
            self.REFRESH_TOKEN_EXPIRY = 86400
            self.DB_HOST = "postgres"
            self.DB_NAME = "test_db"
            self.DB_USER = "test_user"
            self.DB_PASS = "test_pass"
            self.ADMIN_EMAIL = "admin@test.com"
            self.ADMIN_PASSWORD = "admin"
        
        def items(self):
            """For compatibility with config iteration"""
            return {
                "hostname": self.IDENTITY_HOSTNAME,
                "port": self.IDENTITY_PORT,
                "timeout": self.IDENTITY_TIMEOUT,
                "jwt_secret": self.JWT_SECRET,
                "token_expiry": self.TOKEN_EXPIRY,
                "refresh_token_expiry": self.REFRESH_TOKEN_EXPIRY,
                "db_host": self.DB_HOST,
                "db_name": self.DB_NAME,
                "db_user": self.DB_USER
            }.items()
    
    config = TestConfig()
else:
    config = IdentityConfig()
