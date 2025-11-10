"""
ServiceClient class - Client-side services (apps) with basic endpoints.

Derives from ServiceBase and provides basic health/stats endpoints.
Client apps use available REST APIs but don't expose their own APIs.
"""

from typing import Optional
import os
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request, HTTPException
import httpx
from jinja2 import FileSystemLoader, ChoiceLoader
from .base import ServiceBase


class ServiceClient(ServiceBase):
    """
    Client-side service class for web applications.

    This class is used for client applications that serve HTML/CSS/JS interfaces
    and use REST APIs from server services. They provide basic endpoints like
    health checks, stats, and metrics but don't expose complex APIs themselves.

    Examples: admin, mail, client, test-suite
    """

    def __init__(self, name: str, description: str = None, port: int = None,
                 mount_lib: bool = True, static_dir: Optional[str] = None,
                 templates_dir: Optional[str] = None):
        """
        Initialize client service.

        Args:
            name: Service name
            description: Service description
            port: Service port
            mount_lib: Whether to mount shared library directory (default: True for clients)
        """
        super().__init__(name=name, description=description, port=port, mount_lib=mount_lib)

        # Mount static files and templates if provided
        self.templates = None
        if static_dir and os.path.isdir(static_dir):
            # mount under /static
            self.app.mount('/static', StaticFiles(directory=static_dir), name='static')

        if templates_dir and os.path.isdir(templates_dir):
            # Create loader that searches in both templates_dir and shared components
            components_dir = os.path.join(os.path.dirname(__file__), '..', 'components')
            if os.path.isdir(components_dir):
                loader = ChoiceLoader([
                    FileSystemLoader(templates_dir),
                    FileSystemLoader(components_dir)
                ])
                self.templates = Jinja2Templates(directory=templates_dir)
                self.templates.env.loader = loader
            else:
                self.templates = Jinja2Templates(directory=templates_dir)

        # Add client-specific endpoints
        self._add_client_endpoints()

    def _add_client_endpoints(self):
        """Add client-specific endpoints like stats, metrics, and API proxies."""
        from digidig.config import Config
        from fastapi.responses import JSONResponse
        
        config = Config.instance()
        # Map of service names to their internal URLs
        service_urls = {
            'identity': config.service_internal_url('identity'),
            'storage': config.service_internal_url('storage'),
            'smtp': config.service_internal_url('smtp'),
            'imap': config.service_internal_url('imap'),
        }

        @self.app.get("/stats")
        def client_stats():
            """Client application statistics"""
            return {
                "service": self.model.name,
                "type": "client",
                "status": self.model.status,
                "uptime": "unknown"
            }

        @self.app.get("/metrics")
        def client_metrics():
            """Basic client metrics"""
            return {
                "service": self.model.name,
                "active_sessions": 0,
                "memory_usage": "unknown",
                "response_time": "unknown"
            }

        # Generic API proxy for all server services
        @self.app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
        async def proxy_api(service: str, path: str, request: Request):
            """
            Proxy /api/{service}/* to {SERVICE}_INTERNAL_URL/api/*
            Required for same-origin policy - HttpOnly cookies won't be sent cross-origin
            """
            if service not in service_urls:
                raise HTTPException(status_code=404, detail=f"Service '{service}' not found")
            
            # Map to target service with /api/ prefix (all REST APIs are under /api/)
            target_url = f"{service_urls[service]}/api/{path}"
            
            # Forward request
            try:
                async with httpx.AsyncClient() as client:
                    # Get request body if present
                    body = None
                    if request.method in ["POST", "PUT", "PATCH"]:
                        body = await request.body()
                    
                    # Forward headers (especially cookies)
                    headers = dict(request.headers)
                    headers.pop('host', None)  # Remove host header
                    
                    # Extract cookies from request and forward them
                    cookies = dict(request.cookies) if request.cookies else None
                    
                    # Make request to target service
                    response = await client.request(
                        method=request.method,
                        url=target_url,
                        headers=headers,
                        content=body,
                        params=request.query_params,
                        cookies=cookies
                    )
                    
                    # Return response with same status and body
                    return JSONResponse(
                        content=response.json() if response.headers.get('content-type', '').startswith('application/json') else {'data': response.text},
                        status_code=response.status_code
                    )
            except httpx.RequestError as e:
                raise HTTPException(status_code=502, detail=f"Error proxying to {service}: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")
