from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
import os
import sys
from pydantic import BaseModel
import logging

# Add parent directory to path for common imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from common.i18n import init_i18n, get_i18n

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize i18n
i18n = init_i18n(default_language='en', service_name='client')

# Service URLs
IDENTITY_URL = os.getenv("IDENTITY_URL", "http://identity:8001")

app = FastAPI()
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
        # Verify token with identity service
        identity_url = os.getenv("IDENTITY_URL", "http://identity:8001")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{identity_url}/verify",
                headers={"Authorization": f"Bearer {token}"}
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
async def login(request: Request):
    # Check if already logged in
    user = await get_user_from_token(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_post(request: Request):
    """Handle login form submission"""
    try:
        form = await request.form()
        username = form.get("username")
        domain = form.get("domain")
        password = form.get("password")
        
        if not username or not domain or not password:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Všechna pole jsou povinná"
            })
        
        # Construct full email
        email = f"{username}@{domain}"
        
        # Call Identity service /login endpoint
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{IDENTITY_URL}/login",
                json={
                    "username": username,
                    "domain": domain,
                    "password": password
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    access_token = data.get("access_token")
                    
                    # Create redirect response and set cookie
                    redirect = RedirectResponse(url="/dashboard", status_code=303)
                    redirect.set_cookie(
                        key="access_token",
                        value=access_token,
                        httponly=True,
                        max_age=3600,
                        samesite="lax"
                    )
                    return redirect
                else:
                    error_text = await response.text()
                    logger.warning(f"Login failed: {response.status} - {error_text}")
                    return templates.TemplateResponse("login.html", {
                        "request": request,
                        "error": "Neplatné přihlašovací údaje"
                    })
    except Exception as e:
        logger.error(f"Login error: {e}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Chyba při přihlašování"
        })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, error: str = None):
    # Get current user from token
    user = await get_user_from_token(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)