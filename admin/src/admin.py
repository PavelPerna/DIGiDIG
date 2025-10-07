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

class Domain(BaseModel):
    name: str

async def get_user(token: str):
    logger.info("Ověřování admin uživatele")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://identity:8001/verify",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status != 200 or (await response.json())["role"] != "admin":
                    logger.error(f"Neautorizovaný přístup, HTTP {response.status}")
                    raise HTTPException(status_code=401, detail="Neautorizovaný přístup")
                return await response.json()
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
            async with session.get(
                "http://identity:8001/users",
                headers={"Authorization": f"Bearer {token}"}
            ) as user_response:
                users = await user_response.json() if user_response.status == 200 else []
                logger.info(f"Načteno {len(users)} uživatelů")
            async with session.get(
                "http://identity:8001/domains",
                headers={"Authorization": f"Bearer {token}"}
            ) as domain_response:
                domains = await domain_response.json() if domain_response.status == 200 else []
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
            async with session.post(
                "http://identity:8001/login",
                json={"email": email, "password": password, "role": "admin"}
            ) as response:
                if response.status != 200:
                    logger.error(f"Neplatné přihlašovací údaje pro {email}, HTTP {response.status}")
                    return templates.TemplateResponse("login.html", {
                        "request": request,
                        "error": "Neplatné přihlašovací údaje"
                    })
                data = await response.json()
                logger.info(f"Admin {email} přihlášen, token získán")
                async with session.get(
                    "http://identity:8001/users",
                    headers={"Authorization": f"Bearer {data['access_token']}"}
                ) as user_response:
                    users = await user_response.json() if user_response.status == 200 else []
                    logger.info(f"Načteno {len(users)} uživatelů")
                async with session.get(
                    "http://identity:8001/domains",
                    headers={"Authorization": f"Bearer {data['access_token']}"}
                ) as domain_response:
                    domains = await domain_response.json() if domain_response.status == 200 else []
                    logger.info(f"Načteno {len(domains)} domén")
                return templates.TemplateResponse("dashboard.html", {
                    "request": request,
                    "token": data["access_token"],
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
async def manage_user(user: User, token: str = Form(...)):
    logger.info(f"Správa uživatele: {user.email}")
    try:
        await get_user(token)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://identity:8001/manage-user",
                json=user.dict(),
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status != 200:
                    logger.error(f"Chyba při správě uživatele {user.email}, HTTP {response.status}")
                    raise HTTPException(status_code=response.status, detail="Chyba při správě uživatele")
                logger.info(f"Uživatel {user.email} úspěšně spravován")
                return await response.json()
    except Exception as e:
        logger.error(f"Chyba při správě uživatele {user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chyba: {str(e)}")

@app.post("/manage-domain")
async def manage_domain(domain: Domain, token: str = Form(...)):
    logger.info(f"Přidávání domény: {domain.name}")
    try:
        await get_user(token)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://identity:8001/domains",
                json=domain.dict(),
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status != 200:
                    logger.error(f"Chyba při přidávání domény {domain.name}, HTTP {response.status}")
                    raise HTTPException(status_code=response.status, detail="Chyba při přidávání domény")
                logger.info(f"Doména {domain.name} úspěšně přidána")
                return await response.json()
    except Exception as e:
        logger.error(f"Chyba při přidávání domény {domain.name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chyba: {str(e)}")

@app.post("/delete-domain")
async def delete_domain(domain_name: str = Form(...), token: str = Form(...)):
    logger.info(f"Odstraňování domény: {domain_name}")
    try:
        await get_user(token)
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"http://identity:8001/domains/{domain_name}",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status != 200:
                    logger.error(f"Chyba při odstraňování domény {domain_name}, HTTP {response.status}")
                    raise HTTPException(status_code=response.status, detail="Chyba při odstraňování domény")
                logger.info(f"Doména {domain_name} úspěšně odstraněna")
                return await response.json()
    except Exception as e:
        logger.error(f"Chyba při odstraňování domény {domain_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chyba: {str(e)}")