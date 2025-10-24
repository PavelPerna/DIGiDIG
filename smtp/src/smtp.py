import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aiohttp
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP, AuthResult
import os
import asyncio
from email.parser import BytesParser
from email.policy import default
from contextlib import asynccontextmanager
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Spouštění SMTP Service...")
    controller = await start_smtp_server()
    try:
        yield
    finally:
        await stop_smtp_server(controller)
        logger.info("SMTP Service ukončen")

app = FastAPI(title="SMTP Microservice", lifespan=lifespan)

# Global state for service management
service_state = {
    "start_time": None,
    "requests_total": 0,
    "requests_successful": 0,
    "requests_failed": 0,
    "last_request_time": None,
    "email_queue": [],
    "controller": None,
    "config": {
        "hostname": os.getenv("SMTP_HOSTNAME", "0.0.0.0"),
        "port": int(os.getenv("SMTP_SERVER_PORT", "2525")),  # SMTP server port (not FastAPI)
        "max_workers": int(os.getenv("SMTP_MAX_WORKERS", "4")),
        "pool_size": int(os.getenv("SMTP_POOL_SIZE", "10")),
        "enabled": True,
        "timeout": int(os.getenv("SMTP_TIMEOUT", "30")),
        "retry_attempts": int(os.getenv("SMTP_RETRY_ATTEMPTS", "3")),
        "retry_delay": int(os.getenv("SMTP_RETRY_DELAY", "2")),
        "auth_required": True,
        "max_message_size": int(os.getenv("SMTP_MAX_MESSAGE_SIZE", "10485760")),
        "queue_size": int(os.getenv("SMTP_QUEUE_SIZE", "100"))
    }
}

# Thread pool for email processing
executor = ThreadPoolExecutor(max_workers=service_state["config"]["max_workers"])

class Email(BaseModel):
    sender: str
    recipient: str
    subject: str
    body: str

class Authenticator:
    """SMTP Authentication handler - callable wrapper for aiosmtpd"""
    def __call__(self, mechanism, login, password):
        """
        Synchronous authentication handler (aiosmtpd requirement).
        Validates credentials against Identity service.
        """
        logger.info(f"SMTP authentication: mechanism={mechanism}, login={login}")
        
        if mechanism not in ("LOGIN", "PLAIN"):
            logger.warning(f"Invalid authentication mechanism: {mechanism}")
            return False
        
        try:
            # Use sync HTTP client to call Identity service
            import requests
            
            # Decode bytes to string if necessary
            if isinstance(login, bytes):
                login = login.decode('utf-8')
            if isinstance(password, bytes):
                password = password.decode('utf-8')
            
            # Validate email format
            if '@' not in login:
                logger.warning(f"Login must be in email format (user@domain): {login}")
                return False
            
            # Call Identity service /login endpoint
            # Identity service accepts email field directly
            response = requests.post(
                "http://identity:8001/login",
                json={
                    "email": login,  # login is already in email format (user@domain)
                    "password": password
                },
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"Authentication successful for {login}")
                return True
            else:
                logger.warning(f"Authentication failed for {login}: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"Identity service timeout for {login}")
            return False
        except Exception as e:
            logger.error(f"Authentication error for {login}: {e}")
            return False

async def is_local_domain(domain: str) -> bool:
    """Check if domain exists in Identity service (local delivery)"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://identity:8001/api/domains/{domain}/exists",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("exists", False)
                return False
    except Exception as e:
        logger.warning(f"Failed to check if domain {domain} is local: {e}")
        # On error, assume external delivery (safer default)
        return False

class EmailHandler:
    async def handle_DATA(self, server, session, envelope):
        logger.info(f"Přijímám e-mail od {envelope.mail_from} pro {envelope.rcpt_tos}")
        service_state["requests_total"] += 1
        service_state["last_request_time"] = datetime.utcnow().isoformat()
        
        try:
            email_data = BytesParser(policy=default).parsebytes(envelope.content)
            recipient = envelope.rcpt_tos[0]
            
            # Check if recipient is local
            recipient_domain = recipient.split("@")[1] if "@" in recipient else None
            is_local = False
            if recipient_domain:
                is_local = await is_local_domain(recipient_domain)
                logger.info(f"Recipient {recipient} - local domain: {is_local}")
            
            # Extract body properly (handle multipart messages)
            body = ""
            if email_data.is_multipart():
                for part in email_data.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                payload = email_data.get_payload()
                if isinstance(payload, bytes):
                    body = payload.decode('utf-8', errors='ignore')
                elif isinstance(payload, str):
                    body = payload
            
            email = Email(
                sender=envelope.mail_from,
                recipient=recipient,
                subject=email_data["subject"] or "",
                body=body or ""
            )
            
            # Add to queue
            if len(service_state["email_queue"]) < service_state["config"]["queue_size"]:
                service_state["email_queue"].append({
                    "sender": email.sender,
                    "recipient": email.recipient,
                    "subject": email.subject,
                    "timestamp": datetime.utcnow().isoformat(),
                    "local_delivery": is_local
                })
            
            # Process email using thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                self._process_email_sync,
                email,
                envelope,
                is_local
            )
            
            if result:
                service_state["requests_successful"] += 1
                return "250 OK"
            else:
                service_state["requests_failed"] += 1
                return "550 Chyba při ukládání e-mailu"
                
        except Exception as e:
            logger.error(f"Chyba při zpracování e-mailu: {str(e)}")
            service_state["requests_failed"] += 1
            return "550 Chyba při zpracování"
    
    def _process_email_sync(self, email: Email, envelope, is_local: bool = False):
        """Synchronous email processing for thread pool"""
        if is_local:
            # Local delivery - store directly
            return self._deliver_local(email)
        else:
            # External delivery - forward to external MTA (not implemented yet)
            logger.info(f"External delivery for {email.recipient} - storing locally for now")
            # TODO: Implement external SMTP relay
            return self._deliver_local(email)
    
    def _deliver_local(self, email: Email):
        """Deliver email to local storage"""
        max_retries = service_state["config"]["retry_attempts"]
        retry_delay = service_state["config"]["retry_delay"]
        
        for attempt in range(max_retries):
            try:
                # Use synchronous HTTP client in thread
                import requests
                response = requests.post(
                    "http://storage:8002/emails",
                    json=email.dict(),
                    timeout=service_state["config"]["timeout"]
                )
                
                if response.status_code != 200:
                    logger.error(f"Chyba při ukládání e-mailu: HTTP {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return False
                    
                logger.info(f"E-mail od {email.sender} pro {email.recipient} úspěšně uložen (lokální doručení)")
                return True
                
            except Exception as e:
                logger.error(f"Chyba při pokusu {attempt + 1}/{max_retries} uložení e-mailu: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        logger.critical(f"Nepodařilo se uložit e-mail po {max_retries} pokusech")
        return False

async def start_smtp_server():
    try:
        config = service_state["config"]
        logger.info(f"Spouštění SMTP serveru na {config['hostname']}:{config['port']}...")
        handler = EmailHandler()
        controller = Controller(
            handler,
            hostname=config["hostname"],
            port=config["port"],
            auth_callback=Authenticator(),
            auth_required=config["auth_required"],
            auth_require_tls=False
        )
        controller.start()
        service_state["controller"] = controller
        service_state["start_time"] = time.time()
        logger.info("SMTP server úspěšně spuštěn")
        return controller
    except Exception as e:
        logger.critical(f"Chyba při spouštění SMTP serveru: {str(e)}")
        raise

async def stop_smtp_server(controller):
    try:
        logger.info("Ukončování SMTP serveru...")
        if controller:
            controller.stop()
        executor.shutdown(wait=True)
        logger.info("SMTP server ukončen")
    except Exception as e:
        logger.error(f"Chyba při ukončování SMTP serveru: {str(e)}")

# REST API Endpoints

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - service_state["start_time"] if service_state["start_time"] else 0
    status = "healthy" if service_state["config"]["enabled"] and service_state["controller"] else "unhealthy"
    
    return {
        "service_name": "smtp",
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime,
        "details": {
            "controller_running": service_state["controller"] is not None,
            "enabled": service_state["config"]["enabled"]
        }
    }

@app.get("/api/config")
async def get_config():
    """Get current SMTP service configuration"""
    return {
        "service_name": "smtp",
        "config": service_state["config"]
    }

@app.put("/api/config")
async def update_config(config: Dict[str, Any]):
    """Update SMTP service configuration"""
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
    """Get SMTP service statistics"""
    uptime = time.time() - service_state["start_time"] if service_state["start_time"] else 0
    
    return {
        "service_name": "smtp",
        "uptime_seconds": uptime,
        "requests_total": service_state["requests_total"],
        "requests_successful": service_state["requests_successful"],
        "requests_failed": service_state["requests_failed"],
        "last_request_time": service_state["last_request_time"],
        "custom_stats": {
            "queue_length": len(service_state["email_queue"]),
            "max_queue_size": service_state["config"]["queue_size"],
            "max_workers": service_state["config"]["max_workers"]
        }
    }

@app.get("/api/smtp/status")
async def get_smtp_status():
    """Get SMTP server status"""
    return {
        "controller_running": service_state["controller"] is not None,
        "hostname": service_state["config"]["hostname"],
        "port": service_state["config"]["port"],
        "auth_required": service_state["config"]["auth_required"],
        "enabled": service_state["config"]["enabled"]
    }

@app.post("/api/send")
async def send_email_rest(email: Email):
    """
    REST API endpoint for sending emails
    Alternative to using SMTP protocol directly
    """
    logger.info(f"REST API: Sending email from {email.sender} to {email.recipient}")
    service_state["requests_total"] += 1
    service_state["last_request_time"] = datetime.utcnow().isoformat()
    
    try:
        # Check if recipient is local
        recipient_domain = email.recipient.split("@")[1] if "@" in email.recipient else None
        is_local = False
        if recipient_domain:
            is_local = await is_local_domain(recipient_domain)
            logger.info(f"Recipient {email.recipient} - local domain: {is_local}")
        
        # Add to queue
        if len(service_state["email_queue"]) < service_state["config"]["queue_size"]:
            service_state["email_queue"].append({
                "sender": email.sender,
                "recipient": email.recipient,
                "subject": email.subject,
                "timestamp": datetime.utcnow().isoformat(),
                "local_delivery": is_local
            })
        
        # Process email using thread pool
        loop = asyncio.get_event_loop()
        
        # Create a simple envelope-like object for thread pool
        class SimpleEnvelope:
            def __init__(self, sender, recipient):
                self.mail_from = sender
                self.rcpt_tos = [recipient]
        
        envelope = SimpleEnvelope(email.sender, email.recipient)
        
        handler = EmailHandler()
        result = await loop.run_in_executor(
            executor,
            handler._process_email_sync,
            email,
            envelope,
            is_local
        )
        
        if result:
            service_state["requests_successful"] += 1
            logger.info(f"REST API: Email sent successfully")
            return {"status": "success", "message": "Email sent"}
        else:
            service_state["requests_failed"] += 1
            logger.error(f"REST API: Failed to send email")
            raise HTTPException(status_code=500, detail="Failed to send email")
            
    except Exception as e:
        service_state["requests_failed"] += 1
        logger.error(f"REST API: Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/smtp/restart")
async def restart_smtp():
    """Restart SMTP server"""
    try:
        logger.info("Restarting SMTP server...")
        if service_state["controller"]:
            await stop_smtp_server(service_state["controller"])
        
        controller = await start_smtp_server()
        service_state["controller"] = controller
        
        return {
            "status": "success",
            "message": "SMTP server restarted"
        }
    except Exception as e:
        logger.error(f"Error restarting SMTP server: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/smtp/queue")
async def get_email_queue():
    """Get email queue status"""
    return {
        "queue_length": len(service_state["email_queue"]),
        "max_queue_size": service_state["config"]["queue_size"],
        "emails": service_state["email_queue"][-10:]  # Last 10 emails
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)