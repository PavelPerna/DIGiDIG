import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import os
from datetime import datetime
from typing import Dict, Any, Optional
import time

# Nastavení logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Storage Microservice")

# Global state for service management
service_state = {
    "start_time": time.time(),
    "requests_total": 0,
    "requests_successful": 0,
    "requests_failed": 0,
    "last_request_time": None,
    "config": {
        "hostname": os.getenv("STORAGE_HOSTNAME", "0.0.0.0"),
        "port": int(os.getenv("STORAGE_PORT", "8002")),
        "enabled": True,
        "timeout": int(os.getenv("STORAGE_TIMEOUT", "30")),
        "mongo_uri": os.getenv("MONGO_URI", "mongodb://mongo:27017"),
        "database_name": os.getenv("DB_NAME", "strategos"),
        "max_document_size": int(os.getenv("STORAGE_MAX_DOC_SIZE", "16777216"))
    }
}

class Email(BaseModel):
    sender: str
    recipient: str
    subject: str
    body: str
    timestamp: Optional[str] = None
    read: bool = False
    folder: str = "INBOX"

try:
    logger.info("Připojování k MongoDB...")
    client = MongoClient(service_state["config"]["mongo_uri"], serverSelectionTimeoutMS=10000)
    db = client[service_state["config"]["database_name"]]
    emails_collection = db["emails"]
    
    # Create indexes for efficient querying
    try:
        emails_collection.create_index("recipient")
        emails_collection.create_index([("recipient", 1), ("timestamp", -1)])
        emails_collection.create_index([("recipient", 1), ("read", 1)])
        logger.info("MongoDB indexes created successfully")
    except Exception as idx_error:
        # Indexes may already exist from previous runs
        logger.info(f"Index creation skipped (may already exist): {idx_error}")
    
    client.admin.command("ping")
    logger.info("Úspěšně připojeno k MongoDB")
except Exception as e:
    logger.error(f"Chyba při připojování k MongoDB: {str(e)}")
    raise

@app.post("/emails")
async def store_email(email: Email):
    logger.info(f"Ukládání e-mailu od {email.sender} pro {email.recipient}")
    service_state["requests_total"] += 1
    service_state["last_request_time"] = datetime.utcnow().isoformat()
    
    try:
        # Add timestamp if not provided
        email_dict = email.dict()
        if not email_dict.get("timestamp"):
            email_dict["timestamp"] = datetime.utcnow().isoformat()
        
        emails_collection.insert_one(email_dict)
        service_state["requests_successful"] += 1
        logger.info(f"E-mail od {email.sender} úspěšně uložen")
        return {"status": "E-mail uložen"}
    except Exception as e:
        service_state["requests_failed"] += 1
        logger.error(f"Chyba při ukládání e-mailu: {str(e)}")
        return {"status": "Chyba při ukládání", "error": str(e)}

@app.get("/emails")
async def get_emails(user_id: str, folder: str = "INBOX", unread_only: bool = False):
    logger.info(f"Načítání e-mailů pro uživatele {user_id} (folder={folder}, unread_only={unread_only})")
    service_state["requests_total"] += 1
    service_state["last_request_time"] = datetime.utcnow().isoformat()
    
    try:
        query = {"recipient": user_id, "folder": folder}
        if unread_only:
            query["read"] = False
        
        emails = list(emails_collection.find(query).sort("timestamp", -1))
        service_state["requests_successful"] += 1
        logger.info(f"Načteno {len(emails)} e-mailů pro {user_id}")
        
        return [{
            "sender": e["sender"], 
            "recipient": e["recipient"], 
            "subject": e["subject"], 
            "body": e["body"],
            "timestamp": e.get("timestamp"),
            "read": e.get("read", False),
            "folder": e.get("folder", "INBOX")
        } for e in emails]
    except Exception as e:
        service_state["requests_failed"] += 1
        logger.error(f"Chyba při načítání e-mailů pro {user_id}: {str(e)}")
        return {"status": "Chyba při načítání", "error": str(e)}

# REST API Endpoints

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - service_state["start_time"]
    
    # Test MongoDB connection
    try:
        client.admin.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    status = "healthy" if service_state["config"]["enabled"] and db_status == "connected" else "unhealthy"
    
    return {
        "service_name": "storage",
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime,
        "details": {
            "enabled": service_state["config"]["enabled"],
            "database_status": db_status
        }
    }

@app.get("/api/config")
async def get_config():
    """Get current Storage service configuration"""
    config = service_state["config"].copy()
    # Don't expose sensitive URI in full
    if "mongo_uri" in config:
        config["mongo_uri"] = "***"
    return {
        "service_name": "storage",
        "config": config
    }

@app.put("/api/config")
async def update_config(config: Dict[str, Any]):
    """Update Storage service configuration"""
    try:
        # Update configuration
        for key, value in config.items():
            if key in service_state["config"]:
                service_state["config"][key] = value
        
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
    """Get Storage service statistics"""
    uptime = time.time() - service_state["start_time"]
    
    # Get email count
    try:
        email_count = emails_collection.count_documents({})
        db_stats = db.command("dbstats")
        storage_size = db_stats.get("dataSize", 0)
    except Exception as e:
        logger.error(f"Error getting DB stats: {str(e)}")
        email_count = 0
        storage_size = 0
    
    return {
        "service_name": "storage",
        "uptime_seconds": uptime,
        "requests_total": service_state["requests_total"],
        "requests_successful": service_state["requests_successful"],
        "requests_failed": service_state["requests_failed"],
        "last_request_time": service_state["last_request_time"],
        "custom_stats": {
            "total_emails": email_count,
            "storage_size_bytes": storage_size,
            "database_name": service_state["config"]["database_name"]
        }
    }

@app.get("/api/storage/stats")
async def get_storage_stats():
    """Get detailed storage statistics"""
    try:
        email_count = emails_collection.count_documents({})
        db_stats = db.command("dbstats")
        
        return {
            "total_emails": email_count,
            "database": service_state["config"]["database_name"],
            "collections": db.list_collection_names(),
            "storage_size_bytes": db_stats.get("dataSize", 0),
            "index_size_bytes": db_stats.get("indexSize", 0),
            "total_size_bytes": db_stats.get("storageSize", 0)
        }
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))