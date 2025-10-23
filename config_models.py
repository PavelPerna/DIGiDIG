"""
Configuration models for DIGiDIG services
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ServiceConfig(BaseModel):
    """Base configuration for all services"""
    service_name: str
    hostname: str = Field(default="0.0.0.0", description="Service hostname")
    port: int = Field(description="Service port")
    max_workers: int = Field(default=4, description="Maximum number of worker threads")
    pool_size: int = Field(default=10, description="Connection pool size")
    enabled: bool = Field(default=True, description="Service enabled status")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay: int = Field(default=2, description="Delay between retries in seconds")
    custom_config: Optional[Dict[str, Any]] = Field(default=None, description="Service-specific configuration")


class SMTPConfig(ServiceConfig):
    """SMTP service configuration"""
    service_name: str = "smtp"
    port: int = 8000
    auth_required: bool = True
    auth_require_tls: bool = False
    max_message_size: int = Field(default=10485760, description="Max message size in bytes (10MB)")
    queue_size: int = Field(default=100, description="Email queue size")


class IMAPConfig(ServiceConfig):
    """IMAP service configuration"""
    service_name: str = "imap"
    port: int = 8003
    max_connections: int = Field(default=50, description="Maximum concurrent connections")
    idle_timeout: int = Field(default=300, description="Idle connection timeout in seconds")


class StorageConfig(ServiceConfig):
    """Storage service configuration"""
    service_name: str = "storage"
    port: int = 8002
    mongo_uri: str = Field(default="mongodb://mongo:27017", description="MongoDB connection URI")
    database_name: str = Field(default="strategos", description="Database name")
    max_document_size: int = Field(default=16777216, description="Max document size in bytes (16MB)")


class IdentityConfig(ServiceConfig):
    """Identity service configuration"""
    service_name: str = "identity"
    port: int = 8001
    jwt_secret: str = Field(description="JWT secret key")
    token_expiry: int = Field(default=3600, description="Token expiry in seconds")
    refresh_token_expiry: int = Field(default=1209600, description="Refresh token expiry in seconds (14 days)")
    db_host: str = Field(default="postgres", description="PostgreSQL host")
    db_name: str = Field(default="strategos", description="Database name")
    db_user: str = Field(description="Database user")
    db_password: str = Field(description="Database password")


class ServiceStats(BaseModel):
    """Service statistics"""
    service_name: str
    uptime_seconds: float
    requests_total: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    last_request_time: Optional[datetime] = None
    custom_stats: Optional[Dict[str, Any]] = None


class ServiceHealth(BaseModel):
    """Service health status"""
    service_name: str
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
