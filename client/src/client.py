from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
import os
from pydantic import BaseModel
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    # Check if already logged in
    user = await get_user_from_token(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    """Authenticate user via identity service"""
    try:
        identity_url = os.getenv("IDENTITY_URL", "http://identity:8001")
        async with aiohttp.ClientSession() as session:
            # Call identity service login endpoint
            async with session.post(
                f"{identity_url}/login",
                json={"email": email, "password": password}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    token = data.get("access_token")
                    
                    if token:
                        # Set token in cookie and redirect to dashboard
                        redirect_response = RedirectResponse(url="/dashboard", status_code=303)
                        redirect_response.set_cookie(
                            key="access_token",
                            value=token,
                            httponly=True,
                            max_age=3600,  # 1 hour
                            samesite="lax"
                        )
                        return redirect_response
                    else:
                        logger.error("No token in response")
                        return templates.TemplateResponse("login.html", {
                            "request": request,
                            "error": "Chyba serveru"
                        })
                else:
                    error_data = await resp.json()
                    error_msg = error_data.get("detail", "Neplatné přihlašovací údaje")
                    logger.warning(f"Login failed: {error_msg}")
                    return templates.TemplateResponse("login.html", {
                        "request": request,
                        "error": error_msg
                    })
    except Exception as e:
        logger.error(f"Login error: {e}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Chyba připojení: {str(e)}"
        })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, error: str = None):
    # Get current user from token
    user = await get_user_from_token(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # Get username from verified token
    username = user.get("username", "user")
    # For email, we need to fetch user details from identity /users endpoint
    # For now, construct email from username (assuming domain)
    user_email = f"{username}@example.com"
    
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
    
    # Get username from verified token and construct sender email
    username = user.get("username", "unknown")
    sender = f"{username}@example.com"
    
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

@app.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookie"""
    redirect_response = RedirectResponse(url="/", status_code=303)
    redirect_response.delete_cookie(key="access_token")
    return redirect_response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)