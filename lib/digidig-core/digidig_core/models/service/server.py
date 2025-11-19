"""
ServiceServer class - Server-side services with REST APIs or RFC implementations.

Derives from ServiceBase and adds server-specific functionality.
"""
from .base import ServiceBase


class ServiceServer(ServiceBase):
    """
    Server-side service class that provides REST APIs or RFC service implementations.

    This class is used for services that expose APIs to other services or clients.
    Examples: identity, smtp, imap, storage, etc.
    """

    def __init__(self, name: str, description: str = None, port: int = None,
                 api_version: str = None, mount_lib: bool = False, lifespan=None):
        """
        Initialize server service.

        Args:
            name: Service name
            description: Service description
            port: Service port
            api_version: API version prefix (optional, if None uses /api/ directly)
            mount_lib: Whether to mount shared library directory
            lifespan: FastAPI lifespan context manager
        """
        super().__init__(name=name, description=description, port=port, mount_lib=mount_lib, lifespan=lifespan)
        self.api_version = api_version

        # Add API prefix - /api/ or /api/v1/ if version specified
        if api_version:
            self.api_prefix = f"/api/{api_version}"
        else:
            self.api_prefix = "/api"

        # Add server-specific endpoints
        self._add_server_endpoints()

    def _add_server_endpoints(self):
        """Add server-specific endpoints like API documentation, metrics, etc."""

        @self.app.get(f"{self.api_prefix}/status")
        def api_status():
            """API status endpoint"""
            return {
                "service": self.model.name,
                "api_version": self.api_version,
                "status": "operational"
            }

        # API documentation redirect
        @self.app.get("/docs")
        def docs_redirect():
            """Redirect to API documentation"""
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/docs", status_code=302)

    def get_api_url(self, path: str = "") -> str:
        """
        Get full API URL for a given path.

        Args:
            path: API path (without version prefix)

        Returns:
            Full API URL
        """
        return f"{self.api_prefix}/{path.lstrip('/')}"