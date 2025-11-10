import os
import sys
import subprocess
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any

app = FastAPI(title="DIGiDIG Services Manager")

SERVICES = {
    "identity": {"name": "identity", "description": "Identity service", "port": 9101, "compose_name": "identity", "make_target": "identity"},
    "smtp": {"name": "smtp", "description": "SMTP service", "port": 9100, "compose_name": "smtp", "make_target": "smtp"},
    "imap": {"name": "imap", "description": "IMAP service", "port": 9103, "compose_name": "imap", "make_target": "imap"},
    "storage": {"name": "storage", "description": "Storage service", "port": 9102, "compose_name": "storage", "make_target": "storage"},
    "admin": {"name": "admin", "description": "Admin service", "port": 9105, "compose_name": "admin", "make_target": "admin"},
    "client": {"name": "client", "description": "Client app", "port": 9104, "compose_name": "client", "make_target": "client", "frontend_url": "/", "user_count": 0},
    "test-suite": {"name": "test-suite", "description": "Test suite", "port": 9108, "compose_name": "test-suite", "make_target": "test-suite"},
    "mail": {"name": "mail", "description": "Mail service", "port": 9107, "compose_name": "mail", "make_target": "mail"},
    "apidocs": {"name": "apidocs", "description": "API Docs service", "port": 9110, "compose_name": "apidocs", "make_target": "apidocs"},
    "sso": {"name": "sso", "description": "SSO service", "port": 9106, "compose_name": "sso", "make_target": "sso"},
}

@app.get("/services")
def list_services() -> List[Dict[str, Any]]:
    return list(SERVICES.values())

@app.post("/services/{service_name}/restart")
def restart_service(service_name: str):
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    # Prefer Makefile target, fallback to docker compose
    target = SERVICES[service_name].get("make_target") or service_name
    try:
        result = subprocess.run(["make", target], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        if result.returncode != 0:
            raise Exception(result.stderr)
        return {"status": "restarted", "output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/services/{service_name}")
def get_service(service_name: str) -> Dict[str, Any]:
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    return SERVICES[service_name]

@app.get("/services/{service_name}/status")
def get_service_status(service_name: str):
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    # Use docker ps to get status
    try:
        result = subprocess.run(["docker", "compose", "ps", service_name], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        return {"output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "healthy", "service": "services", "version": "0.1.0"}
