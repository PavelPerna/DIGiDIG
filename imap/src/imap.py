import logging
from fastapi import FastAPI, HTTPException, Header
import aiohttp
from pydantic import BaseModel

# Nastavení logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="IMAP Microservice")

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
    try:
        token = authorization.split("Bearer ")[1]
        if not await verify_user(token):
            logger.error(f"Neplatný token pro uživatele {user_id}")
            raise HTTPException(status_code=401, detail="Neplatný token")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://storage:8002/emails?user_id={user_id}") as response:
                if response.status != 200:
                    logger.error(f"Chyba při načítání e-mailů, HTTP {response.status}")
                    raise HTTPException(status_code=response.status, detail="Chyba při načítání e-mailů")
                emails = await response.json()
                logger.info(f"Načteno {len(emails)} e-mailů pro {user_id}")
                return emails
    except Exception as e:
        logger.error(f"Chyba při načítání e-mailů pro {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chyba: {str(e)}")