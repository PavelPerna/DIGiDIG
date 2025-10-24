"""
API Documentation Service for DIGiDIG

Aggregates OpenAPI specifications from all services and provides:
- Unified Swagger UI
- ReDoc documentation
- Service health monitoring
- API endpoint discovery

Services documented:
- Identity (port 8001): User authentication and authorization
- Storage (port 8002): Email storage and retrieval
- SMTP (port 8003): Email sending
- IMAP (port 8004): Email retrieval protocol
- Client (port 8005): Web client interface
- Admin (port 8006): Administration panel
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiohttp
import os
import logging
from typing import Dict, List, Optional
from pathlib import Path

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="DIGiDIG API Documentation",
    description="Comprehensive API documentation for all DIGiDIG services",
    version="1.0.0",
    docs_url=None,  # We'll provide custom docs
    redoc_url=None
)

# Templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Service configurations
SERVICES = {
    "identity": {
        "name": "Identity Service",
        "description": "User authentication, authorization, domain and user management",
        "url": os.getenv("IDENTITY_URL", "http://identity:8001"),
        "openapi_path": "/openapi.json",
        "icon": "🔐",
        "tags": ["Authentication", "Users", "Domains"]
    },
    "storage": {
        "name": "Storage Service",
        "description": "Email storage, retrieval, and folder management",
        "url": os.getenv("STORAGE_URL", "http://storage:8002"),
        "openapi_path": "/openapi.json",
        "icon": "💾",
        "tags": ["Emails", "Storage", "Folders"]
    },
    "smtp": {
        "name": "SMTP Service",
        "description": "Email sending via SMTP protocol",
        "url": os.getenv("SMTP_URL", "http://smtp:8003"),
        "openapi_path": "/openapi.json",
        "icon": "📤",
        "tags": ["SMTP", "Send Email"]
    },
    "imap": {
        "name": "IMAP Service",
        "description": "Email retrieval via IMAP protocol",
        "url": os.getenv("IMAP_URL", "http://imap:8007"),
        "openapi_path": "/openapi.json",
        "icon": "📥",
        "tags": ["IMAP", "Retrieve Email"]
    },
    "client": {
        "name": "Client Service",
        "description": "Web-based email client interface",
        "url": os.getenv("CLIENT_URL", "http://client:8004"),
        "openapi_path": "/openapi.json",
        "icon": "🌐",
        "tags": ["Web Client", "UI"]
    },
    "admin": {
        "name": "Admin Service",
        "description": "System administration and monitoring",
        "url": os.getenv("ADMIN_URL", "http://admin:8005"),
        "openapi_path": "/openapi.json",
        "icon": "⚙️",
        "tags": ["Administration", "Monitoring", "Services"]
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


async def check_service_health(service_id: str) -> Dict:
    """Check if a service is healthy."""
    service = SERVICES.get(service_id)
    if not service:
        return {"status": "unknown", "message": "Service not found"}
    
    try:
        async with aiohttp.ClientSession() as session:
            # Try to fetch OpenAPI spec as health check
            async with session.get(
                f"{service['url']}{service['openapi_path']}",
                timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                if response.status == 200:
                    return {"status": "healthy", "message": "Service is running"}
                else:
                    return {"status": "unhealthy", "message": f"HTTP {response.status}"}
    except aiohttp.ClientConnectorError:
        return {"status": "unreachable", "message": "Cannot connect to service"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main documentation page with service overview."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "services": SERVICES
    })


@app.get("/api/services", response_class=JSONResponse)
async def list_services():
    """List all available services."""
    return {
        "services": [
            {
                "id": service_id,
                **service_config
            }
            for service_id, service_config in SERVICES.items()
        ]
    }


@app.get("/api/services/{service_id}/spec", response_class=JSONResponse)
async def get_service_spec(service_id: str):
    """Get OpenAPI specification for a specific service."""
    spec = await fetch_openapi_spec(service_id)
    if spec:
        return spec
    else:
        return JSONResponse(
            status_code=404,
            content={"error": "Service not found or spec unavailable"}
        )


@app.get("/api/services/{service_id}/health", response_class=JSONResponse)
async def get_service_health(service_id: str):
    """Get health status of a specific service."""
    health = await check_service_health(service_id)
    return health


@app.get("/api/health", response_class=JSONResponse)
async def get_all_health():
    """Get health status of all services."""
    health_statuses = {}
    
    for service_id in SERVICES.keys():
        health_statuses[service_id] = await check_service_health(service_id)
    
    return {
        "services": health_statuses,
        "overall": "healthy" if all(
            h["status"] == "healthy" for h in health_statuses.values()
        ) else "degraded"
    }


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
        "service_description": service["description"]
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
        "service_description": service["description"]
    })


@app.get("/api/openapi/combined", response_class=JSONResponse)
async def get_combined_openapi():
    """Get combined OpenAPI specification for all services."""
    combined = {
        "openapi": "3.0.0",
        "info": {
            "title": "DIGiDIG Combined API",
            "description": "Combined API documentation for all DIGiDIG services",
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
    uvicorn.run(app, host="0.0.0.0", port=8010)
