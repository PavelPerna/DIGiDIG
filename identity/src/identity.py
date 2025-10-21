import logging
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import jwt
import os
import asyncpg
from datetime import datetime, timedelta
import hashlib
import asyncio

# Nastavení logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Identity Microservice")

class User(BaseModel):
    email: str
    password: str
    role: str

class Domain(BaseModel):
    name: str

async def init_db():
    max_retries = 10
    retry_delay = 5  # sekundy
    logger.info("Inicializace databáze...")
    for attempt in range(max_retries):
        try:
            pool = await asyncpg.create_pool(
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASS", "securepassword"),
                database=os.getenv("DB_NAME", "strategos"),
                host=os.getenv("DB_HOST", "postgres")
            )
            async with pool.acquire() as conn:
                logger.info("Vytváření tabulek domains a users...")
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS domains (
                        name TEXT PRIMARY KEY
                    )
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        email TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL
                    )
                """)
                await conn.execute(
                    "INSERT INTO domains (name) VALUES ($1) ON CONFLICT DO NOTHING",
                    "example.com"
                )
                # NOTE: default admin creation moved out of init_db.
                # The system should not create a production admin account with a hardcoded password.
                # Use the provided management script `scripts/create_admin.py` during install/deploy
                # to create an admin user if desired. This keeps initialization safe for production.
                logger.info("Výchozí doména 'example.com' vytvořena. (Admin user creation disabled in init_db)")
            logger.info("Databáze úspěšně inicializována")
            return pool
        except Exception as e:
            logger.error(f"Chyba při připojování k databázi (pokus {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logger.critical("Nepodařilo se připojit k databázi po všech pokusech")
                raise

app.state.db_pool = None

@app.on_event("startup")
async def startup():
    logger.info("Spouštění Identity Service...")
    app.state.db_pool = await init_db()
    logger.info("Identity Service spuštěn")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Ukončování Identity Service...")
    if app.state.db_pool:
        await app.state.db_pool.close()
        logger.info("Databázové připojení uzavřeno")

@app.post("/register")
async def register(user: User):
    logger.info(f"Registrace uživatele: {user.email}")
    domain = user.email.split("@")[1] if "@" in user.email else ""
    async with app.state.db_pool.acquire() as conn:
        domain_exists = await conn.fetchval("SELECT name FROM domains WHERE name = $1", domain)
        if not domain_exists:
            logger.error(f"Doména {domain} není registrována")
            raise HTTPException(status_code=400, detail="Doména není registrována")
        hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
        try:
            await conn.execute(
                "INSERT INTO users (email, password, role) VALUES ($1, $2, $3)",
                user.email, hashed_password, user.role
            )
            logger.info(f"Uživatel {user.email} úspěšně zaregistrován")
            return {"status": "Uživatel zaregistrován"}
        except asyncpg.UniqueViolationError:
            logger.error(f"E-mail {user.email} již existuje")
            raise HTTPException(status_code=400, detail="E-mail již existuje")
        except Exception as e:
            logger.error(f"Chyba při registraci uživatele {user.email}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Chyba při registraci: {str(e)}")

@app.post("/login")
async def login(user: User):
    logger.info(f"Přihlášení uživatele: {user.email}")
    hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
    async with app.state.db_pool.acquire() as conn:
        try:
            result = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1 AND password = $2",
                user.email, hashed_password
            )
            if not result:
                logger.error(f"Neplatné přihlašovací údaje pro {user.email}")
                raise HTTPException(status_code=401, detail="Neplatné přihlašovací údaje")
            token = jwt.encode(
                {"email": user.email, "role": result["role"], "exp": datetime.utcnow() + timedelta(hours=1)},
                os.getenv("JWT_SECRET", "b8_XYZ123abc456DEF789ghiJKL0mnoPQ"),
                algorithm="HS256"
            )
            logger.info(f"Uživatel {user.email} úspěšně přihlášen, token vygenerován")
            return {"access_token": token, "token_type": "bearer"}
        except Exception as e:
            logger.error(f"Chyba při přihlášení uživatele {user.email}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Chyba při přihlášení: {str(e)}")

@app.get("/verify")
async def verify(authorization: str = Header(...)):
    logger.info("Ověřování JWT tokenu")
    try:
        token = authorization.split("Bearer ")[1]
        payload = jwt.decode(token, os.getenv("JWT_SECRET", "b8_XYZ123abc456DEF789ghiJKL0mnoPQ"), algorithms=["HS256"])
        logger.info(f"Token ověřen pro uživatele {payload['email']}")
        return {"status": "OK", "email": payload["email"], "role": payload["role"]}
    except Exception as e:
        logger.error(f"Chyba při ověřování tokenu: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Neplatný token: {str(e)}")

@app.post("/domains")
async def add_domain(domain: Domain, authorization: str = Header(...)):
    logger.info(f"Přidávání domény: {domain.name}")
    try:
        token = authorization.split("Bearer ")[1]
        payload = jwt.decode(token, os.getenv("JWT_SECRET", "b8_XYZ123abc456DEF789ghiJKL0mnoPQ"), algorithms=["HS256"])
        if payload["role"] != "admin":
            logger.error(f"Uživatel {payload['email']} nemá oprávnění přidávat domény")
            raise HTTPException(status_code=403, detail="Pouze admin může přidávat domény")
        async with app.state.db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO domains (name) VALUES ($1) ON CONFLICT DO NOTHING",
                domain.name
            )
            logger.info(f"Doména {domain.name} přidána")
            return {"status": f"Doména {domain.name} přidána"}
    except Exception as e:
        logger.error(f"Chyba při přidávání domény {domain.name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chyba při přidávání domény: {str(e)}")

@app.delete("/domains/{domain_name}")
async def delete_domain(domain_name: str, authorization: str = Header(...)):
    logger.info(f"Odstraňování domény: {domain_name}")
    try:
        token = authorization.split("Bearer ")[1]
        payload = jwt.decode(token, os.getenv("JWT_SECRET", "b8_XYZ123abc456DEF789ghiJKL0mnoPQ"), algorithms=["HS256"])
        if payload["role"] != "admin":
            logger.error(f"Uživatel {payload['email']} nemá oprávnění odstraňovat domény")
            raise HTTPException(status_code=403, detail="Pouze admin může odstraňovat domény")
        async with app.state.db_pool.acquire() as conn:
            result = await conn.execute("DELETE FROM domains WHERE name = $1", domain_name)
            if result == "DELETE 0":
                logger.error(f"Doména {domain_name} nenalezena")
                raise HTTPException(status_code=404, detail="Doména nenalezena")
            logger.info(f"Doména {domain_name} odstraněna")
            return {"status": f"Doména {domain_name} odstraněna"}
    except Exception as e:
        logger.error(f"Chyba při odstraňování domény {domain_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chyba při odstraňování domény: {str(e)}")

@app.get("/domains")
async def list_domains(authorization: str = Header(...)):
    logger.info("Získávání seznamu domén")
    try:
        token = authorization.split("Bearer ")[1]
        payload = jwt.decode(token, os.getenv("JWT_SECRET", "b8_XYZ123abc456DEF789ghiJKL0mnoPQ"), algorithms=["HS256"])
        if payload["role"] != "admin":
            logger.error(f"Uživatel {payload['email']} nemá oprávnění zobrazit domény")
            raise HTTPException(status_code=403, detail="Pouze admin může zobrazit domény")
        async with app.state.db_pool.acquire() as conn:
            domains = await conn.fetch("SELECT name FROM domains")
            logger.info(f"Nalezeno {len(domains)} domén")
            return [{"name": d["name"]} for d in domains]
    except Exception as e:
        logger.error(f"Chyba při získávání domén: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chyba při získávání domén: {str(e)}")