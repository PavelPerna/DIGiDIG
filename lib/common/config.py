"""
Configuration loader for DIGiDIG services
Loads configuration from YAML files with environment-based overrides
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager that loads from YAML files"""
    
    def __init__(self, config_path: Optional[str] = None, env: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to main config file (default: config/config.yaml)
            env: Environment name (dev, test, prod) - loads config.{env}.yaml as override
        """
        self._config: Dict[str, Any] = {}
        
        # Determine config directory
        if config_path:
            self.config_file = Path(config_path)
        else:
            # Default: look for config in project root
            # Try multiple possible locations for config directory
            possible_roots = [
                Path(__file__).parent.parent.parent,  # /app when lib is at /app/lib
                Path(__file__).parent.parent,         # Original location
                Path.cwd(),                           # Current working directory
                Path("/app") if Path("/app").exists() else None,  # Docker container root
            ]
            
            config_file = None
            for root in possible_roots:
                if root is None:
                    continue
                candidate = root / "config" / "config.yaml"
                if candidate.exists():
                    config_file = candidate
                    break
            
            if config_file is None:
                # Fallback to default path
                config_file = Path(__file__).parent.parent / "config" / "config.yaml"
            
            self.config_file = config_file
        
        # Load main config
        self._load_config(self.config_file)
        
        # Load environment-specific override
        env = env or os.getenv("DIGIDIG_ENV", "dev")
        if env != "dev":
            env_config_file = self.config_file.parent / f"config.{env}.yaml"
            if env_config_file.exists():
                self._load_config(env_config_file, override=True)
    
    def _load_config(self, file_path: Path, override: bool = False):
        """Load configuration from YAML file"""
        if not file_path.exists():
            if not override:
                raise FileNotFoundError(f"Configuration file not found: {file_path}")
            return
        
        with open(file_path, 'r') as f:
            loaded_config = yaml.safe_load(f) or {}
        
        if override:
            self._deep_merge(self._config, loaded_config)
        else:
            self._config = loaded_config
    
    def _deep_merge(self, base: dict, override: dict):
        """Deep merge override dict into base dict"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation path
        
        Example:
            config.get("database.postgres.host")  # Returns postgres host
            config.get("services.smtp.rest_url")  # Returns SMTP REST URL
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.get(section, {})
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access: config['database']"""
        return self.get(key)
    
    @property
    def all(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self._config.copy()


# Global config instance (lazy loaded)
_config_instance: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """
    Get global configuration instance
    
    Args:
        reload: Force reload configuration from files
    """
    global _config_instance
    
    if _config_instance is None or reload:
        # If reloading and we have an existing instance, use its config path
        if reload and _config_instance is not None:
            old_config_file = _config_instance.config_file
            _config_instance = Config(config_path=str(old_config_file))
        else:
            _config_instance = Config()
    
    return _config_instance


def load_config(config_path: Optional[str] = None, env: Optional[str] = None) -> Config:
    """
    Load configuration from specific path
    
    Args:
        config_path: Path to config file
        env: Environment name (dev, test, prod)
    """
    return Config(config_path=config_path, env=env)


# Convenience functions for common config access
def get_db_config(db_type: str = "postgres") -> Dict[str, Any]:
    """Get database configuration"""
    return get_config().get(f"database.{db_type}", {})


def get_service_url(service_name: str) -> str:
    """Get service URL by name"""
    return get_config().get(f"services.{service_name}.url", "")


def get_external_service_url(service_name: str) -> str:
    """Get external service URL by name for browser access"""
    # Try external_urls section first (for localhost browser access)
    external_url = get_config().get(f"external_urls.{service_name}")
    if external_url:
        return external_url
    
    # Fallback to internal service URL
    return get_service_url(service_name)


def get_jwt_secret() -> str:
    """Get JWT secret"""
    return get_config().get("security.jwt.secret", "")


def get_admin_credentials() -> Dict[str, str]:
    """Get admin credentials"""
    return {
        "email": get_config().get("security.admin.email", ""),
        "password": get_config().get("security.admin.password", "")
    }
