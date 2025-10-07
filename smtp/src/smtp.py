import logging
from fastapi import FastAPI
from pydantic import BaseModel
import aiohttp
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP, AuthResult
import os
import asyncio
from email.parser import BytesParser
from email.policy import default
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SMTP Microservice")

class Email(BaseModel):
    sender: str
    recipient: str
    subject: str
    body: str

async def authenticate(server, session, envelope, mechanism, auth_data):
    logger.info(f"Autentizace SMTP: mechanism={mechanism}, login={auth_data.login}")
    username = os.getenv("SMTP_USER", "admin@example.com")
    password = os.getenv("SMTP_PASS", "admin")
    if mechanism not in ("LOGIN", "PLAIN"):
        logger.warning(f"Neplatný autentizační mechanismus: {mechanism}")
        return AuthResult(success=False)
    result = auth_data.login == username and auth_data.password == password
    logger.info(f"Autentizace {'úspěšná' if result else 'neúspěšná'} pro {auth_data.login}")
    return AuthResult(success=result)

class EmailHandler:
    async def handle_DATA(self, server, session, envelope):
        logger.info(f"Přijímám e-mail od {envelope.mail_from} pro {envelope.rcpt_tos}")
        try:
            email_data = BytesParser(policy=default).parsebytes(envelope.content)
            email = Email(
                sender=envelope.mail_from,
                recipient=envelope.rcpt_tos[0],
                subject=email_data["subject"] or "",
                body=email_data.get_payload() or ""
            )
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            "http://storage:8002/emails",
                            json=email.dict()
                        ) as response:
                            if response.status != 200:
                                logger.error(f"Chyba při ukládání e-mailu: HTTP {response.status}")
                                return "550 Chyba při ukládání e-mailu"
                            logger.info(f"E-mail od {envelope.mail_from} úspěšně uložen")
                            return "250 OK"
                except Exception as e:
                    logger.error(f"Chyba při pokusu {attempt + 1}/{max_retries} uložení e-mailu: {str(e)}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
            logger.critical(f"Nepodařilo se uložit e-mail po {max_retries} pokusech")
            return "550 Chyba při ukládání"
        except Exception as e:
            logger.error(f"Chyba při zpracování e-mailu: {str(e)}")
            return "550 Chyba při zpracování"

async def start_smtp_server():
    try:
        logger.info("Spouštění SMTP serveru na portu 8000...")
        handler = EmailHandler()
        controller = Controller(
            handler,
            hostname="0.0.0.0",
            port=8000,
            auth_callback=authenticate,
            auth_required=True,
            auth_require_tls=False
        )
        controller.start()
        logger.info("SMTP server úspěšně spuštěn")
        return controller
    except Exception as e:
        logger.critical(f"Chyba při spouštění SMTP serveru: {str(e)}")
        raise

async def stop_smtp_server(controller):
    try:
        logger.info("Ukončování SMTP serveru...")
        controller.stop()
        logger.info("SMTP server ukončen")
    except Exception as e:
        logger.error(f"Chyba při ukončování SMTP serveru: {str(e)}")

@asynccontextmanager
async def lifespan(app):
    logger.info("Spouštění SMTP Service...")
    controller = await start_smtp_server()
    try:
        yield
    finally:
        await stop_smtp_server(controller)
        logger.info("SMTP Service ukončen")

app.lifespan = lifespan

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)