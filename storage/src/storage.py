import logging
from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
import os

# Nastavení logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Storage Microservice")

class Email(BaseModel):
    sender: str
    recipient: str
    subject: str
    body: str

try:
    logger.info("Připojování k MongoDB...")
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://mongo:27017"), serverSelectionTimeoutMS=10000)
    db = client["strategos"]
    emails_collection = db["emails"]
    client.admin.command("ping")
    logger.info("Úspěšně připojeno k MongoDB")
except Exception as e:
    logger.critical(f"Chyba při připojení k MongoDB: {str(e)}")
    raise

@app.post("/emails")
async def store_email(email: Email):
    logger.info(f"Ukládání e-mailu od {email.sender} pro {email.recipient}")
    try:
        emails_collection.insert_one(email.dict())
        logger.info(f"E-mail od {email.sender} úspěšně uložen")
        return {"status": "E-mail uložen"}
    except Exception as e:
        logger.error(f"Chyba při ukládání e-mailu: {str(e)}")
        return {"status": "Chyba při ukládání", "error": str(e)}

@app.get("/emails")
async def get_emails(user_id: str):
    logger.info(f"Načítání e-mailů pro uživatele {user_id}")
    try:
        emails = list(emails_collection.find({"recipient": user_id}))
        logger.info(f"Načteno {len(emails)} e-mailů pro {user_id}")
        return [{"sender": e["sender"], "recipient": e["recipient"], "subject": e["subject"], "body": e["body"]} for e in emails]
    except Exception as e:
        logger.error(f"Chyba při načítání e-mailů pro {user_id}: {str(e)}")
        return {"status": "Chyba při načítání", "error": str(e)}