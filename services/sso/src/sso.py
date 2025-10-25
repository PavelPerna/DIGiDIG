"""
DIGiDIG SSO (Single Sign-On) Service
Provides centralized authentication and login functionality for all DIGiDIG services.
"""
import logging
from fastapi import FastAPI, Request, Form, HTTPException, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import aiohttp
import os
import sys
import urllib.parse
from datetime import datetime, timezone

# Add parent directory to path for common imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from common.config import get_config, get_service_url
from common.i18n import init_i18n

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize i18n
i18n = init_i18n(default_language='en', service_name='sso')

# Get configuration
config = get_config()
IDENTITY_URL = get_service_url('identity')

app = FastAPI(
    title="DIGiDIG SSO Service",
    description="""
## Single Sign-On (SSO) Service

Provides centralized authentication and login functionality for all DIGiDIG services.

### Features

* **Centralized Login**: Single login page for all services
* **Session Management**: Secure session handling with JWT tokens
* **Multi-Service Redirect**: Seamless redirection to requesting services
* **Internationalization**: Multi-language support
* **Security**: Secure cookie handling and CSRF protection
    """,
    version="1.0.0",
    contact={
        "name": "DIGiDIG Team", 
        "url": "https://github.com/PavelPerna/DIGiDIG",
    },
    license_info={
        "name": "MIT",
    },
    tags_metadata=[
        {
            "name": "Authentication",
            "description": "Login, logout, and session management"
        },
        {
            "name": "Redirect",
            "description": "Service redirection after authentication"
        },
        {
            "name": "Health",
            "description": "Service health and status monitoring"
        }
    ]
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Models
class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str
    redirect_url: Optional[str] = None

class SessionInfo(BaseModel):
    username: str
    roles: List[str]
    expires_at: str

# Helper functions
def get_language(request: Request) -> str:
    """Get current language from cookie or default to 'en'"""
    return request.cookies.get("language", "en")

def set_language_cookie(response: Response, lang: str):
    """Set language cookie"""
    if lang in ['cs', 'en']:
        response.set_cookie(
            key="language",
            value=lang,
            max_age=365*24*60*60,  # 1 year
            httponly=True,
            samesite="lax"
        )

async def validate_redirect_url(url: str) -> bool:
    """Validate that redirect URL is to a trusted DIGiDIG service"""
    if not url:
        return False
    
    # Parse URL to check if it's a relative path or trusted domain
    parsed = urllib.parse.urlparse(url)
    
    # Allow relative URLs
    if not parsed.netloc:
        return True
    
    # Get trusted service URLs from config
    trusted_hosts = []
    services = config.get('services', {})
    for service_name, service_config in services.items():
        if isinstance(service_config, dict) and 'host' in service_config:
            trusted_hosts.append(service_config['host'])
            # Also add with port if specified
            if 'port' in service_config:
                trusted_hosts.append(f"{service_config['host']}:{service_config['port']}")
    
    # Check if the host is in our trusted list
    return parsed.netloc in trusted_hosts

async def authenticate_user(username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with identity service"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "username": username_or_email if "@" not in username_or_email else None,
                "email": username_or_email if "@" in username_or_email else None,
                "password": password
            }
            
            async with session.post(f"{IDENTITY_URL}/login", json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Authentication failed: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return None

async def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token with identity service"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{IDENTITY_URL}/verify",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None

# Routes
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request, redirect_to: Optional[str] = None):
    """Display login page"""
    lang = get_language(request)
    i18n.set_language(lang)
    
    # Check if user is already logged in
    token = request.cookies.get("access_token")
    if token:
        user_data = await verify_token(token)
        if user_data:
            # User is already authenticated, redirect if needed
            if redirect_to and await validate_redirect_url(redirect_to):
                return RedirectResponse(url=redirect_to)
            else:
                # Default redirect to client service
                client_url = get_service_url('client')
                return RedirectResponse(url=f"{client_url}/dashboard")
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "redirect_to": redirect_to,
        "current_language": lang,
        "translations": i18n.get_all()
    })

@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    redirect_to: Optional[str] = Form(None)
):
    """Process login form"""
    lang = get_language(request)
    i18n.set_language(lang)
    
    # Authenticate with identity service
    auth_result = await authenticate_user(username, password)
    
    if not auth_result:
        # Login failed
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": i18n.get("login.error.invalid_credentials"),
            "redirect_to": redirect_to,
            "current_language": lang,
            "translations": i18n.get_all()
        }, status_code=401)
    
    # Create response with redirect
    if redirect_to and await validate_redirect_url(redirect_to):
        response = RedirectResponse(url=redirect_to, status_code=302)
    else:
        # Default redirect to client dashboard
        client_url = get_service_url('client')
        response = RedirectResponse(url=f"{client_url}/dashboard", status_code=302)
    
    # Set authentication cookies
    response.set_cookie(
        key="access_token",
        value=auth_result["access_token"],
        max_age=1800,  # 30 minutes
        httponly=True,
        secure=config.get('security.cookie.secure', False),
        samesite=config.get('security.cookie.samesite', 'lax')
    )
    
    if "refresh_token" in auth_result:
        response.set_cookie(
            key="refresh_token",
            value=auth_result["refresh_token"],
            max_age=7*24*60*60,  # 7 days
            httponly=True,
            secure=config.get('security.cookie.secure', False),
            samesite=config.get('security.cookie.samesite', 'lax')
        )
    
    logger.info(f"User {username} logged in successfully")
    return response

@app.post("/logout")
async def logout(request: Request, redirect_to: Optional[str] = None):
    """Logout user and clear session"""
    # Create response
    if redirect_to and await validate_redirect_url(redirect_to):
        response = RedirectResponse(url=redirect_to)
    else:
        response = RedirectResponse(url="/")
    
    # Clear authentication cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    logger.info("User logged out")
    return response

@app.get("/verify")
async def verify_session(request: Request):
    """Verify current session and return user info"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No authentication token")
    
    user_data = await verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user_data

@app.post("/api/language")
async def set_language_endpoint(request: Request, lang: str = Form(...)):
    """Set user language preference"""
    i18n.set_language(lang)
    response = JSONResponse({"success": True, "language": lang})
    set_language_cookie(response, lang)
    return response

@app.get("/api/translations")
async def get_translations(request: Request):
    """Get all translations for current language"""
    lang = get_language(request)
    i18n.set_language(lang)
    return JSONResponse(i18n.get_all())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "sso",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "identity_service": IDENTITY_URL
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)