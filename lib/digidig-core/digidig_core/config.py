"""
Configuration loader for DIGiDIG services
Loads configuration from YAML files with environment-based overrides

Singleton pattern - use Config.instance() to access configuration
"""
import os
try:
    import yaml
    _yaml_safe_load = yaml.safe_load
except Exception:
    # PyYAML not installed in the environment (possible in minimal containers).
    # Fallback to JSON parsing for simple use-cases so services can still start.
    import json
    def _yaml_safe_load(s):
        txt = s.read() if hasattr(s, 'read') else s
        try:
            return json.loads(txt) if txt and txt.strip() else {}
        except Exception:
            return {}
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """
    Configuration manager singleton that loads from YAML files
    
    Usage:
        config = Config.instance()
        db_config = config.db_config('postgres')
        smtp_url = config.service_url('smtp', ssl=True)
    """
    
    _instance: Optional['Config'] = None
    
    def __init__(self, config_path: Optional[str] = None, env: Optional[str] = None):
        """
        Initialize configuration (internal - use Config.instance() instead)
        
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
                Path(__file__).parent.parent.parent,  # /app when digidig is at /app/digidig
                Path(__file__).parent.parent,         # Project root when digidig is at project/digidig
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
    
    @classmethod
    def instance(cls, reload: bool = False) -> 'Config':
        """
        Get singleton configuration instance
        
        Args:
            reload: Force reload configuration from files
        
        Returns:
            Config singleton instance
        """
        if cls._instance is None or reload:
            if reload and cls._instance is not None:
                old_config_file = cls._instance.config_file
                cls._instance = Config(config_path=str(old_config_file))
            else:
                cls._instance = Config()
        
        return cls._instance
    
    def _load_config(self, file_path: Path, override: bool = False):
        """Load configuration from YAML file"""
        if not file_path.exists():
            if not override:
                raise FileNotFoundError(f"Configuration file not found: {file_path}")
            return
        
        with open(file_path, 'r') as f:
            loaded_config = _yaml_safe_load(f) or {}
        
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
    
    # === Service Configuration Methods ===
    
    def db_config(self, db_type: str = "postgres") -> Dict[str, Any]:
        """Get database configuration"""
        return self.get_section(f"database.{db_type}")
    
    def service_external_domain(self, service_name: str) -> str:
        """Get service external domain"""
        return self.get(f"services.{service_name}.external_url", "digidig.cz")
    
    def service_http_port(self, service_name: str) -> int:
        """Get service HTTP port"""
        if service_name == 'smtp':
            return self.get(f"services.{service_name}.rest_port", 9100)
        elif service_name == 'imap':
            return self.get(f"services.{service_name}.rest_port", 9103)
        else:
            return self.get(f"services.{service_name}.http_port", 9100)
    
    def service_https_port(self, service_name: str) -> int:
        """Get service HTTPS port"""
        if service_name == 'smtp':
            return self.get(f"services.{service_name}.rest_sslport", 9200)
        elif service_name == 'imap':
            return self.get(f"services.{service_name}.rest_sslport", 9203)
        else:
            return self.get(f"services.{service_name}.http_sslport", 9200)
    
    def service_url(self, service_name: str, ssl: bool = False) -> str:
        """Get service URL by name (HTTP or HTTPS) - for external/user-facing URLs"""
        domain = self.service_external_domain(service_name)
        if ssl:
            port = self.service_https_port(service_name)
            return f"https://{domain}:{port}"
        else:
            port = self.service_http_port(service_name)
            return f"http://{domain}:{port}"
    
    def service_internal_url(self, service_name: str) -> str:
        """Get internal service URL for Docker network communication (always HTTP)"""
        port = self.service_http_port(service_name)
        return f"http://{service_name}:{port}"
    
    def service_api_url(self, service_name: str, ssl: bool = True) -> str:
        """
        Get the best URL for API calls to another service.
        
        - If calling from within Docker, use internal Docker service name
        - If calling from outside Docker, use external URL
        
        This allows services to work both in single-server Docker Compose 
        and distributed multi-server setups.
        """
        # Check if we're running in Docker
        in_docker = os.path.exists('/.dockerenv') or os.environ.get('HOSTNAME', '').startswith(('digidig-', 'strategos-'))
        
        if in_docker:
            # Use internal Docker network
            if ssl:
                port = self.service_https_port(service_name)
                return f"https://{service_name}:{port}"
            else:
                port = self.service_http_port(service_name)
                return f"http://{service_name}:{port}"
        else:
            # Use external URL for distributed setup
            return self.service_url(service_name, ssl=ssl)
    
    def smtp_port(self, service_name: str = 'smtp', ssl: bool = False) -> int:
        """Get SMTP port (for SMTP protocol, not REST)"""
        if ssl:
            return self.get(f"services.{service_name}.smtp_sslport", 465)
        else:
            return self.get(f"services.{service_name}.smtp_port", 25)
    
    def imap_port(self, service_name: str = 'imap', ssl: bool = False) -> int:
        """Get IMAP port (for IMAP protocol, not REST)"""
        if ssl:
            return self.get(f"services.{service_name}.imap_sslport", 993)
        else:
            return self.get(f"services.{service_name}.imap_port", 143)
    
    def jwt_secret(self) -> str:
        """Get JWT secret"""
        return self.get("security.jwt.secret", "")
    
    def admin_credentials(self) -> Dict[str, str]:
        """Get admin credentials"""
        return {
            "email": self.get("security.admin.email", ""),
            "password": self.get("security.admin.password", "")
        }
