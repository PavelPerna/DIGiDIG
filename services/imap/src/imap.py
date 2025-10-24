import logging
from fastapi import FastAPI, HTTPException, Header
import aiohttp
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import time
import os
import asyncio

# Nastavení logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="IMAP Microservice")

# Global state for service management
service_state = {
    "start_time": time.time(),
    "requests_total": 0,
    "requests_successful": 0,
    "requests_failed": 0,
    "last_request_time": None,
    "active_connections": [],
    "active_sessions": [],
    "config": {
        "hostname": os.getenv("IMAP_HOSTNAME", "0.0.0.0"),
        "port": int(os.getenv("IMAP_PORT", "8003")),
        "max_workers": int(os.getenv("IMAP_MAX_WORKERS", "4")),
        "pool_size": int(os.getenv("IMAP_POOL_SIZE", "10")),
        "enabled": True,
        "timeout": int(os.getenv("IMAP_TIMEOUT", "30")),
        "max_connections": int(os.getenv("IMAP_MAX_CONNECTIONS", "50")),
        "idle_timeout": int(os.getenv("IMAP_IDLE_TIMEOUT", "300"))
    }
}

# Thread pool for email fetching
executor = ThreadPoolExecutor(max_workers=service_state["config"]["max_workers"])

class Email(BaseModel):
    sender: str
    recipient: str
    subject: str
    body: str

async def verify_user(token: str) -> bool:
    logger.info("Ověřování uživatele přes Identity Service")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://identity:8001/verify",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status != 200:
                    logger.error(f"Neplatný token, HTTP {response.status}")
                    return False
                logger.info("Token úspěšně ověřen")
                return True
    except Exception as e:
        logger.error(f"Chyba při ověřování uživatele: {str(e)}")
        return False

@app.get("/emails")
async def get_emails(user_id: str, authorization: str = Header(...)):
    logger.info(f"Načítání e-mailů pro uživatele {user_id}")
    service_state["requests_total"] += 1
    service_state["last_request_time"] = datetime.utcnow().isoformat()
    
    try:
        token = authorization.split("Bearer ")[1]
        if not await verify_user(token):
            logger.error(f"Neplatný token pro uživatele {user_id}")
            service_state["requests_failed"] += 1
            raise HTTPException(status_code=401, detail="Neplatný token")
        
        # Track active session
        session_id = f"{user_id}_{int(time.time())}"
        service_state["active_sessions"].append({
            "session_id": session_id,
            "user_id": user_id,
            "started_at": datetime.utcnow().isoformat()
        })
        
        # Use thread pool for fetching emails
        loop = asyncio.get_event_loop()
        emails = await loop.run_in_executor(
            executor,
            _fetch_emails_sync,
            user_id
        )
        
        # Remove session after completion
        service_state["active_sessions"] = [
            s for s in service_state["active_sessions"] 
            if s["session_id"] != session_id
        ]
        
        if emails is not None:
            service_state["requests_successful"] += 1
            logger.info(f"Načteno {len(emails)} e-mailů pro {user_id}")
            return emails
        else:
            service_state["requests_failed"] += 1
            raise HTTPException(status_code=500, detail="Chyba při načítání e-mailů")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chyba při načítání e-mailů pro {user_id}: {str(e)}")
        service_state["requests_failed"] += 1
        raise HTTPException(status_code=500, detail=f"Chyba: {str(e)}")

def _fetch_emails_sync(user_id: str):
    """Synchronous email fetching for thread pool"""
    try:
        import requests
        response = requests.get(
            f"http://storage:8002/emails?user_id={user_id}",
            timeout=service_state["config"]["timeout"]
        )
        
        if response.status_code != 200:
            logger.error(f"Chyba při načítání e-mailů, HTTP {response.status_code}")
            return None
        
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching emails: {str(e)}")
        return None

# REST API Endpoints

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - service_state["start_time"]
    status = "healthy" if service_state["config"]["enabled"] else "unhealthy"
    
    return {
        "service_name": "imap",
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime,
        "details": {
            "enabled": service_state["config"]["enabled"],
            "active_connections": len(service_state["active_connections"]),
            "active_sessions": len(service_state["active_sessions"])
        }
    }

@app.get("/api/config")
async def get_config():
    """Get current IMAP service configuration"""
    return {
        "service_name": "imap",
        "config": service_state["config"]
    }

@app.put("/api/config")
async def update_config(config: Dict[str, Any]):
    """Update IMAP service configuration"""
    try:
        # Update configuration
        for key, value in config.items():
            if key in service_state["config"]:
                service_state["config"][key] = value
        
        # Update thread pool if max_workers changed
        global executor
        if "max_workers" in config:
            executor.shutdown(wait=True)
            executor = ThreadPoolExecutor(max_workers=service_state["config"]["max_workers"])
        
        logger.info(f"Configuration updated: {config}")
        return {
            "status": "success",
            "message": "Configuration updated",
            "config": service_state["config"]
        }
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get IMAP service statistics"""
    uptime = time.time() - service_state["start_time"]
    
    return {
        "service_name": "imap",
        "uptime_seconds": uptime,
        "requests_total": service_state["requests_total"],
        "requests_successful": service_state["requests_successful"],
        "requests_failed": service_state["requests_failed"],
        "last_request_time": service_state["last_request_time"],
        "custom_stats": {
            "active_connections": len(service_state["active_connections"]),
            "active_sessions": len(service_state["active_sessions"]),
            "max_connections": service_state["config"]["max_connections"],
            "max_workers": service_state["config"]["max_workers"]
        }
    }

@app.get("/api/imap/connections")
async def get_connections():
    """Get active IMAP connections"""
    return {
        "active_connections": service_state["active_connections"],
        "count": len(service_state["active_connections"]),
        "max_connections": service_state["config"]["max_connections"]
    }

@app.get("/api/imap/sessions")
async def get_sessions():
    """Get active IMAP sessions"""
    return {
        "active_sessions": service_state["active_sessions"],
        "count": len(service_state["active_sessions"])
    }