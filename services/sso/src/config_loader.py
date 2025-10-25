"""
Simple config loader for SSO service
Loads configuration using the centralized system
"""
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'lib'))

from common.config import get_config as get_global_config

# Load config on import
config = get_global_config()

# Legacy attribute access for compatibility
JWT_SECRET = config.get('security.jwt.secret', 'default-jwt-secret')
IDENTITY_URL = config.get('services.identity.url', 'http://identity:8001')
SSO_URL = config.get('services.sso.url', 'http://sso:8006')

def get_config():
    """Get the configuration object"""
    return config

def get_service_url(service_name):
    """Get URL for a service"""
    return config.get(f'services.{service_name}.url', '')