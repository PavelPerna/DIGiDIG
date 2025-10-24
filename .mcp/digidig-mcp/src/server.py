import json
import random
import aiohttp
import os
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
server = FastMCP("digidig_mcp")

# DIGiDIG service URLs - these would typically come from config
DIGIDIG_SERVICES = {
    "identity": os.getenv("IDENTITY_URL", "http://localhost:8001"),
    "storage": os.getenv("STORAGE_URL", "http://localhost:8002"),
    "smtp": os.getenv("SMTP_URL", "http://localhost:8000"),
    "imap": os.getenv("IMAP_URL", "http://localhost:8003"),
    "client": os.getenv("CLIENT_URL", "http://localhost:8004"),
    "admin": os.getenv("ADMIN_URL", "http://localhost:8005"),
    "apidocs": os.getenv("APIDOCS_URL", "http://localhost:8010")
}

@server.tool()
async def get_weather(location: str) -> str:
    """Get weather for a location.

    Args:
        location: Location to get weather for, e.g., city name, state, or coordinates
    
    """
    if not location:
        return "Location is required."
    
    # mock weather data
    conditions = [ "Sunny", "Rainy", "Cloudy", "Snowy" ]
    weather = {
        "location": location,
        "temperature": f"{random.randint(10, 90)}°F",
        "condition": random.choice(conditions),
    }
    return json.dumps(weather, ensure_ascii=False)

@server.tool()
async def get_digidig_service_health() -> str:
    """Get health status of all DIGiDIG services.
    
    Returns:
        JSON string with health status of each service
    """
    health_status = {}
    
    async with aiohttp.ClientSession() as session:
        for service_name, base_url in DIGIDIG_SERVICES.items():
            try:
                # Try different health endpoints
                health_urls = [
                    f"{base_url}/api/health",
                    f"{base_url}/health", 
                    f"{base_url}/"
                ]
                
                service_healthy = False
                response_data = None
                
                for health_url in health_urls:
                    try:
                        async with session.get(health_url, timeout=5) as response:
                            if response.status == 200:
                                service_healthy = True
                                response_data = await response.json()
                                break
                    except:
                        continue
                
                health_status[service_name] = {
                    "status": "healthy" if service_healthy else "unhealthy",
                    "url": base_url,
                    "details": response_data
                }
                
            except Exception as e:
                health_status[service_name] = {
                    "status": "error",
                    "url": base_url,
                    "error": str(e)
                }
    
    return json.dumps(health_status, indent=2, ensure_ascii=False)

@server.tool()
async def get_digidig_emails(recipient: str = None, limit: int = 10) -> str:
    """Get emails from the DIGiDIG storage service.
    
    Args:
        recipient: Email address to filter by (optional)
        limit: Maximum number of emails to return (default: 10)
    
    Returns:
        JSON string with email list
    """
    try:
        storage_url = DIGIDIG_SERVICES["storage"]
        params = {"limit": limit}
        if recipient:
            params["recipient"] = recipient
            
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{storage_url}/emails", params=params) as response:
                if response.status == 200:
                    emails = await response.json()
                    return json.dumps(emails, indent=2, ensure_ascii=False)
                else:
                    return json.dumps({
                        "error": f"Failed to fetch emails: HTTP {response.status}",
                        "details": await response.text()
                    }, ensure_ascii=False)
                    
    except Exception as e:
        return json.dumps({
            "error": f"Error connecting to storage service: {str(e)}"
        }, ensure_ascii=False)

@server.tool()
async def send_digidig_email(sender: str, recipient: str, subject: str, body: str) -> str:
    """Send an email through the DIGiDIG SMTP service.
    
    Args:
        sender: Email address of sender
        recipient: Email address of recipient  
        subject: Email subject
        body: Email body content
    
    Returns:
        JSON string with send result
    """
    try:
        smtp_url = DIGIDIG_SERVICES["smtp"]
        email_data = {
            "sender": sender,
            "recipient": recipient,
            "subject": subject,
            "body": body
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{smtp_url}/api/send", json=email_data) as response:
                if response.status == 200:
                    result = await response.json()
                    return json.dumps({
                        "status": "success",
                        "message": "Email sent successfully",
                        "details": result
                    }, indent=2, ensure_ascii=False)
                else:
                    return json.dumps({
                        "status": "error", 
                        "message": f"Failed to send email: HTTP {response.status}",
                        "details": await response.text()
                    }, ensure_ascii=False)
                    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error connecting to SMTP service: {str(e)}"
        }, ensure_ascii=False)

@server.tool()
async def get_digidig_users() -> str:
    """Get list of users from the DIGiDIG identity service.
    
    Note: This requires admin authentication token.
    
    Returns:
        JSON string with user list or authentication error
    """
    try:
        identity_url = DIGIDIG_SERVICES["identity"]
        
        # This would need proper authentication in real usage
        # For now, just try to get basic service info
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{identity_url}/api/health") as response:
                if response.status == 200:
                    health_info = await response.json()
                    return json.dumps({
                        "info": "User list requires authentication",
                        "identity_service_status": health_info,
                        "note": "Use /users endpoint with proper JWT token for actual user list"
                    }, indent=2, ensure_ascii=False)
                else:
                    return json.dumps({
                        "error": f"Identity service not available: HTTP {response.status}"
                    }, ensure_ascii=False)
                    
    except Exception as e:
        return json.dumps({
            "error": f"Error connecting to identity service: {str(e)}"
        }, ensure_ascii=False)
