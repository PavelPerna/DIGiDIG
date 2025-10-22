import logging
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import aiohttp
from pydantic import BaseModel

# Nastavení logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Admin Microservice")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class User(BaseModel):
    email: str
    role: str
    password: str = None  # Optional for updates

class Domain(BaseModel):
    name: str
    old_name: str = None  # For rename operations

async def identity_request(session, method, endpoint, data=None, token=None, params=None):
    """Helper function for making requests to identity service"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"http://identity:8001{endpoint}"
    
    async with getattr(session, method.lower())(
        url,
        json=data,
        params=params,
        headers=headers
    ) as response:
        if response.status != 200:
            body = await response.text()
            logger.error(f"Identity service error: {body}")
            raise HTTPException(status_code=response.status, detail=body)
        return await response.json()

async def get_user(token: str):
    logger.info("Ověřování admin uživatele")
    try:
        async with aiohttp.ClientSession() as session:
            result = await identity_request(session, "GET", "/verify", token=token)
            if result["role"] != "admin":
                logger.error(f"Uživatel {result['email']} nemá oprávnění přístupu")
                raise HTTPException(status_code=403, detail="Neautorizovaný přístup")
            return result
    except Exception as e:
        logger.error(f"Chyba při ověřování admin uživatele: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Neplatný token: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, token: str = None):
    logger.info("Načítání admin dashboardu")
    if not token:
        logger.info("Žádný token, přesměrování na login")
        return templates.TemplateResponse("login.html", {"request": request})
    try:
        user = await get_user(token)
        logger.info(f"Admin {user['email']} ověřen")
        async with aiohttp.ClientSession() as session:
            users = await identity_request(session, "GET", "/users", token=token)
            logger.info(f"Načteno {len(users)} uživatelů")
            
            domains = await identity_request(session, "GET", "/domains", token=token)
            logger.info(f"Načteno {len(domains)} domén")
            
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "token": token,
            "users": users,
            "domains": domains
        })
    except Exception as e:
        logger.error(f"Chyba při načítání dashboardu: {str(e)}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Chyba: {str(e)}"
        })

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    logger.info(f"Přihlášení admina: {email}")
    try:
        async with aiohttp.ClientSession() as session:
            result = await identity_request(
                session, 
                "POST", 
                "/login", 
                {"email": email, "password": password, "role": "admin"}
            )
            token = result["access_token"]
            
            users = await identity_request(session, "GET", "/users", token=token)
            logger.info(f"Načteno {len(users)} uživatelů")
            
            domains = await identity_request(session, "GET", "/domains", token=token)
            logger.info(f"Načteno {len(domains)} domén")
            
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "token": token,
                "users": users,
                "domains": domains
            })
    except Exception as e:
        logger.error(f"Chyba při přihlášení admina {email}: {str(e)}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Chyba při přihlášení: {str(e)}"
        })

@app.post("/manage-user")
async def manage_user(
    email: str = Form(...),
    role: str = Form(...),
    password: str = Form(None),
    originalEmail: str = Form(None),
    token: str = Form(...)
):
    operation = "update" if originalEmail else "create"
    target_email = originalEmail if originalEmail else email
    logger.info(f"{operation.capitalize()} uživatele: {target_email}")
    try:
        await get_user(token)
        async with aiohttp.ClientSession() as session:
            data = {
                "email": email,
                "role": role,
            }
            if password:
                data["password"] = password
            if originalEmail:
                data["original_email"] = originalEmail
            
            endpoint = "/users" if originalEmail else "/register"
            method = "PUT" if originalEmail else "POST"
            
            result = await identity_request(session, method, endpoint, data, token)
            logger.info(f"Uživatel {target_email} úspěšně {operation}ován")
            return result
    except Exception as e:
        logger.error(f"Chyba při {operation} uživatele {target_email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chyba: {str(e)}")

@app.post("/manage-domain")
async def manage_domain(
    name: str = Form(...),
    oldName: str = Form(None),
    token: str = Form(...)
):
    operation = "update" if oldName else "create"
    target_name = oldName if oldName else name
    logger.info(f"{operation.capitalize()} domény: {target_name}")
    try:
        await get_user(token)
        async with aiohttp.ClientSession() as session:
            data = {"name": name}
            if oldName:
                data["old_name"] = oldName
            
            method = "PUT" if oldName else "POST"
            result = await identity_request(session, method, "/domains", data, token)
            logger.info(f"Doména {target_name} úspěšně {operation}ována")
            return result
    except Exception as e:
        logger.error(f"Chyba při {operation} domény {target_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chyba: {str(e)}")

@app.post("/delete-domain")
async def delete_domain(domain_name: str = Form(...), token: str = Form(...)):
    logger.info(f"Odstraňování domény: {domain_name}")
    try:
        await get_user(token)
        async with aiohttp.ClientSession() as session:
            result = await identity_request(session, "DELETE", f"/domains/{domain_name}", token=token)
            logger.info(f"Doména {domain_name} úspěšně odstraněna")
            return result
    except Exception as e:
        logger.error(f"Chyba při odstraňování domény {domain_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chyba: {str(e)}")

@app.post("/delete-user")
async def delete_user(email: str = Form(...), token: str = Form(...)):
    logger.info(f"Odstraňování uživatele: {email}")
    try:
        await get_user(token)
        async with aiohttp.ClientSession() as session:
            result = await identity_request(session, "DELETE", f"/users/{email}", token=token)
            logger.info(f"Uživatel {email} úspěšně odstraněn")
            return result
    except Exception as e:
        logger.error(f"Chyba při odstraňování uživatele {email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chyba: {str(e)}")