from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
import os
import sys
from pydantic import BaseModel
import logging
import urllib.parse
from datetime import datetime, timezone

# Add parent directory to path for common imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from lib.common.config import get_config, get_service_url
from lib.common.i18n import init_i18n, get_i18n

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize i18n
i18n = init_i18n(default_language='en', service_name='client')

# Get configuration
config = get_config()
IDENTITY_URL = get_service_url('identity')
SSO_URL = get_service_url('sso')

app = FastAPI(
    title="DIGiDIG Client Service",
    description="Email client interface for DIGiDIG system",
    version="1.0.0"
)

# Authentication middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Middleware to handle authentication for protected routes"""
    # Public routes that don't require authentication
    public_paths = ["/health", "/static", "/api/translations", "/api/language"]
    
    # Check if this is a public path
    is_public = any(request.url.path.startswith(path) for path in public_paths)
    
    if not is_public and request.url.path not in ["/", "/login", "/logout"]:
        # Check authentication
        user = await get_user_from_token(request)
        if not user:
            # Redirect to SSO for authentication
            redirect_url = urllib.parse.quote(str(request.url))
            return RedirectResponse(url=f"{SSO_URL}/?redirect_to={redirect_url}", status_code=307)
    
    response = await call_next(request)
    return response

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class Email(BaseModel):
    sender: str
    recipient: str
    subject: str
    body: str

async def get_user_from_token(request: Request):
    """Extract user info from JWT token in cookie"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    try:
        # Verify token with SSO service
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{SSO_URL}/verify",
                cookies={"access_token": token}
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    return user_data
                else:
                    logger.warning(f"Token validation failed: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        return None

async def require_auth(request: Request):
    """Require authentication, redirect to SSO if not authenticated"""
    user = await get_user_from_token(request)
    if not user:
        # Create redirect URL to SSO with current URL as return destination
        redirect_url = urllib.parse.quote(str(request.url))
        sso_login_url = f"{SSO_URL}/?redirect_to={redirect_url}"
        raise HTTPException(status_code=307, headers={"Location": sso_login_url})
    return user

async def get_session(request: Request):
    """Get current user session or redirect to login"""
    user = await get_user_from_token(request)
    if not user:
        return None
    return user

def get_language(request: Request) -> str:
    """Get current language from cookie or default to 'en'"""
    return request.cookies.get("language", "en")

def set_language(response: Response, lang: str):
    """Set language cookie"""
    if lang in ['cs', 'en']:
        response.set_cookie(
            key="language",
            value=lang,
            max_age=365*24*60*60,  # 1 year
            httponly=True,
            samesite="lax"
        )

@app.post("/api/language")
async def set_language_endpoint(request: Request, lang: str = Form(...)):
    """Set user language preference"""
    i18n.set_language(lang)
    response = JSONResponse({"success": True, "language": lang})
    set_language(response, lang)
    return response

@app.get("/api/translations")
async def get_translations(request: Request):
    """Get all translations for current language"""
    lang = get_language(request)
    i18n.set_language(lang)
    return JSONResponse(i18n.get_all())

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - redirect to dashboard if authenticated, otherwise to SSO"""
    user = await get_user_from_token(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
        # Redirect to SSO for authentication
        redirect_url = urllib.parse.quote(str(request.url).replace('/', '/dashboard'))
        return RedirectResponse(url=f"{SSO_URL}/?redirect_to={redirect_url}", status_code=307)

@app.get("/login", response_class=HTMLResponse)
async def login_redirect(request: Request):
    """Legacy login endpoint - redirect to SSO"""
    redirect_url = urllib.parse.quote(str(request.url).replace('/login', '/dashboard'))
    return RedirectResponse(url=f"{SSO_URL}/?redirect_to={redirect_url}", status_code=307)

@app.post("/logout")
async def logout(request: Request):
    """Logout endpoint - redirect to SSO logout"""
    redirect_url = urllib.parse.quote(str(request.url).replace('/logout', '/'))
    return RedirectResponse(url=f"{SSO_URL}/logout?redirect_to={redirect_url}", status_code=307)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, error: str = None):
    """Main dashboard - requires authentication"""
    try:
        user = await require_auth(request)
    except HTTPException as e:
        # Redirect to SSO
        return RedirectResponse(url=e.headers["Location"], status_code=307)
    
    # Get username and domain from verified token
    username = user.get("username", "user")
    domain = user.get("domain", "example.com")
    user_email = f"{username}@{domain}"
    
    # Fetch emails from Storage service
    emails = []
    try:
        async with aiohttp.ClientSession() as http_session:
            storage_url = os.getenv("STORAGE_URL", "http://storage:8002")
            async with http_session.get(
                f"{storage_url}/emails",
                params={"user_id": user_email}
            ) as response:
                if response.status == 200:
                    emails = await response.json()
                else:
                    logger.warning(f"Failed to fetch emails: {response.status}")
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
    
    # Process error parameter
    error_message = None
    if error == "send_failed":
        error_message = "Nepodařilo se odeslat e-mail"
    elif error == "connection_failed":
        error_message = "Chyba připojení k SMTP serveru"
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "username": username,
        "emails": emails,
        "error": error_message
    })

@app.post("/send", response_class=HTMLResponse)
async def send_email(request: Request, recipient: str = Form(...), subject: str = Form(...), body: str = Form(...)):
    # Get current user from token
    user = await get_user_from_token(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # Get username and domain from verified token and construct sender email
    username = user.get("username", "unknown")
    domain = user.get("domain", "example.com")
    sender = f"{username}@{domain}"
    
    email = Email(sender=sender, recipient=recipient, subject=subject, body=body)
    
    try:
        async with aiohttp.ClientSession() as http_session:
            smtp_url = os.getenv("SMTP_URL", "http://smtp:8000")
            async with http_session.post(f"{smtp_url}/api/send", json=email.dict()) as response:
                if response.status == 200:
                    return RedirectResponse(url="/dashboard", status_code=303)
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send email: {response.status} - {error_text}")
                    return RedirectResponse(url="/dashboard?error=send_failed", status_code=303)
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return RedirectResponse(url="/dashboard?error=connection_failed", status_code=303)

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "client",
        "version": "1.0.0",
        "dependencies": {
            "identity": IDENTITY_URL
        }
    }

@app.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookie"""
    redirect_response = RedirectResponse(url="/", status_code=303)
    redirect_response.delete_cookie(key="access_token")
    return redirect_response

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "client",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)