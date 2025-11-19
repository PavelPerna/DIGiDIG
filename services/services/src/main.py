import os
import sys
import subprocess
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Try to import from digidig_core package first, fallback to local digidig
try:
    from digidig_core.config import Config
except ImportError:
    # Fallback to local imports for backward compatibility
    from digidig.config import Config

from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any

app = FastAPI(title="DIGiDIG Services Manager")

config = Config.instance()

def get_services_config():
    """Get services configuration from config system"""
    services_config = {}
    
    # Define all known services
    service_names = ['identity', 'smtp', 'imap', 'storage', 'mail', 'sso', 'services']
    
    for service_name in service_names:
        try:
            port = config.service_http_port(service_name)
            services_config[service_name] = {
                "name": service_name,
                "description": f"{service_name.title()} service",
                "port": port,
                "compose_name": service_name,
                "make_target": service_name
            }
        except:
            # Fallback to hardcoded values if config fails
            port_map = {
                'identity': 9101, 'smtp': 9100, 'imap': 9103, 'storage': 9102,
                'mail': 9107, 'sso': 9106, 'services': 9120
            }
            services_config[service_name] = {
                "name": service_name,
                "description": f"{service_name.title()} service",
                "port": port_map.get(service_name, 9100),
                "compose_name": service_name,
                "make_target": service_name
            }
    
    return services_config

SERVICES = get_services_config()

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


def main():
    """Main entry point for running the services manager"""
    import uvicorn
    
    port = config.get('services.services.http_port', 9120)
    print(f"Starting Services Manager on 0.0.0.0:{port}")
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
