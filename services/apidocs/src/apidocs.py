"""
API Documentation Service for DIGiDIG

Aggregates OpenAPI specifications from all backend REST API services and provides:
- Unified Swagger UI
- ReDoc documentation
- Service health monitoring
- API endpoint discovery

Backend REST API services documented (all endpoints under /api/):
- Identity (port 9101): User authentication and authorization (/api/register, /api/login, /api/users/*, etc.)
- Storage (port 9102): Email storage and retrieval (/api/emails, etc.)
- SMTP (port 9100): Email sending (/api/send)
- IMAP (port 9103): Email retrieval protocol (/api/emails, /api/config, /api/stats)

Client services (mail, admin, client, sso, test-suite) provide web interfaces and proxy API calls via:
/api/{service}/{path} → {service}:port/api/{path}

Note: All REST API endpoints follow the structure /api/{resource}/{id}/{sub-resource}
See _doc/API-ENDPOINTS.md for complete endpoint reference.
"""
import sys
import os

from fastapi import FastAPI, Request
sys.path.insert(0, '/app')
from digidig.models.service.client import ServiceClient
from digidig.config import Config
from fastapi.responses import HTMLResponse, JSONResponse
import aiohttp
import logging
from typing import Dict, Optional
from pathlib import Path

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration
config = Config.instance()
try:
    APIDOCS_PORT = int(os.getenv("APIDOCS_PORT", 9110))
except Exception:
    APIDOCS_PORT = 9110


class ClientApidocs(ServiceClient):
    def __init__(self):
        static_dir = str(Path(__file__).parent / "static")
        templates_dir = str(Path(__file__).parent / "templates")
        super().__init__(
            name="apidocs",
            description="API Documentation Service for DIGiDIG",
            port=APIDOCS_PORT,
            static_dir=static_dir,
            templates_dir=templates_dir
        )
        self.register_routes()

    def register_routes(self):
        # nothing extra to register here; existing module-level routes will attach to `app`
        return


client = ClientApidocs()
app = client.get_app()
templates = client.templates

# Service configurations
SERVICES = {
    "identity": {
        "name": "Identity Service",
        "description": "User authentication, authorization, domain and user management",
        "url": os.getenv("IDENTITY_URL", "http://identity:9101"),
        "openapi_path": "/openapi.json",
        "icon": "🔐",
        "tags": ["Authentication", "Users", "Domains"]
    },
    "storage": {
        "name": "Storage Service",
        "description": "Email storage, retrieval, and folder management",
        "url": os.getenv("STORAGE_URL", "http://storage:9102"),
        "openapi_path": "/openapi.json",
        "icon": "💾",
        "tags": ["Emails", "Storage", "Folders"]
    },
    "smtp": {
        "name": "SMTP Service",
        "description": "Email sending via SMTP protocol",
        "url": os.getenv("SMTP_URL", "http://smtp:9100"),
        "openapi_path": "/openapi.json",
        "icon": "📤",
        "tags": ["SMTP", "Send Email"]
    },
    "imap": {
        "name": "IMAP Service",
        "description": "Email retrieval via IMAP protocol",
        "url": os.getenv("IMAP_URL", "http://imap:9103"),
        "openapi_path": "/openapi.json",
        "icon": "📥",
        "tags": ["IMAP", "Retrieve Email"]
    }
    ,
    "services": {
        "name": "Services Manager",
        "description": "REST API to manage, restart, and monitor all DIGiDIG services.",
        "url": os.getenv("SERVICES_URL", "http://services:9120"),
        "openapi_path": "/openapi.json",
        "icon": "🛠️",
        "tags": ["Management", "Monitoring", "Restart"]
    }
}


async def fetch_openapi_spec(service_id: str) -> Optional[Dict]:
    """Fetch OpenAPI specification from a service."""
    service = SERVICES.get(service_id)
    if not service:
        return None
    
    url = f"{service['url']}{service['openapi_path']}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    spec = await response.json()
                    logger.info(f"Fetched OpenAPI spec from {service_id}")
                    return spec
                else:
                    logger.warning(f"Failed to fetch OpenAPI spec from {service_id}: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error fetching OpenAPI spec from {service_id}: {e}")
        return None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main documentation page with service overview."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "services": SERVICES
    })














@app.get('/health', response_class=JSONResponse)
async def health():
    """Top-level health endpoint used by docker-compose and basic probes."""
    return {'service': 'apidocs', 'status': 'healthy', 'port': APIDOCS_PORT}


@app.get("/docs/{service_id}", response_class=HTMLResponse)
async def service_docs(request: Request, service_id: str):
    """Show Swagger UI for a specific service."""
    if service_id not in SERVICES:
        return HTMLResponse("<h1>Service not found</h1>", status_code=404)
    
    service = SERVICES[service_id]
    
    return templates.TemplateResponse("swagger.html", {
        "request": request,
        "service_id": service_id,
        "service_name": service["name"],
        "service_description": service["description"],
        "service_url": service["url"]
    })


@app.get("/redoc/{service_id}", response_class=HTMLResponse)
async def service_redoc(request: Request, service_id: str):
    """Show ReDoc for a specific service."""
    if service_id not in SERVICES:
        return HTMLResponse("<h1>Service not found</h1>", status_code=404)
    
    service = SERVICES[service_id]
    
    return templates.TemplateResponse("redoc.html", {
        "request": request,
        "service_id": service_id,
        "service_name": service["name"],
        "service_description": service["description"],
        "service_url": service["url"]
    })


@app.get("/api/openapi/combined", response_class=JSONResponse)
async def get_combined_openapi():
    """Get combined OpenAPI specification for all services."""
    combined = {
        "openapi": "3.0.0",
        "info": {
            "title": "DIGiDIG Combined REST API",
            "description": "Combined REST API documentation for all DIGiDIG backend services. All endpoints under /api/ prefix. See _doc/API-ENDPOINTS.md for details.",
            "version": "1.0.0"
        },
        "servers": [],
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {}
        },
        "tags": []
    }
    
    # Fetch specs from all services
    for service_id, service_config in SERVICES.items():
        spec = await fetch_openapi_spec(service_id)
        if not spec:
            continue
        
        # Add server
        combined["servers"].append({
            "url": service_config["url"],
            "description": service_config["name"]
        })
        
        # Merge paths with service prefix
        if "paths" in spec:
            for path, methods in spec["paths"].items():
                prefixed_path = f"/{service_id}{path}"
                combined["paths"][prefixed_path] = methods
        
        # Merge components
        if "components" in spec:
            if "schemas" in spec["components"]:
                for schema_name, schema_def in spec["components"]["schemas"].items():
                    prefixed_name = f"{service_id}_{schema_name}"
                    combined["components"]["schemas"][prefixed_name] = schema_def
            
            if "securitySchemes" in spec["components"]:
                combined["components"]["securitySchemes"].update(
                    spec["components"]["securitySchemes"]
                )
        
        # Merge tags
        if "tags" in spec:
            for tag in spec["tags"]:
                tag["name"] = f"{service_id}:{tag['name']}"
                combined["tags"].append(tag)
    
    return combined


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=APIDOCS_PORT)
