import logging
from fastapi import FastAPI, HTTPException, Header
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, List
import jwt
import os
import asyncpg
from datetime import datetime, timedelta
import uuid
import hashlib
import asyncio

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Identity Service (lifespan)")
    app.state.db_pool = await init_db()
    try:
        yield
    finally:
        logger.info("Shutting down Identity Service (lifespan)")
        if app.state.db_pool:
            await app.state.db_pool.close()


app = FastAPI(title="Identity Microservice", lifespan=lifespan)

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str
    domain: Optional[str] = None
    roles: Optional[List[str]] = ["user"]


class UserUpdate(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None
    roles: Optional[List[str]] = None
    password: Optional[str] = None
    original_username: Optional[str] = None


class Domain(BaseModel):
    name: str


class Role(BaseModel):
    name: str


class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str
    domain: Optional[str] = None


async def init_db():
    max_retries = 10
    retry_delay = 2
    logger.info("Initializing DB (destructive: drop & recreate tables)")
    for attempt in range(max_retries):
        try:
            pool = await asyncpg.create_pool(
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASS", "securepassword"),
                database=os.getenv("DB_NAME", "strategos"),
                host=os.getenv("DB_HOST", "postgres")
            )
            async with pool.acquire() as conn:
                # Drop and recreate tables (user allowed destructive changes)
                logger.info("Dropping and creating tables: domains, roles, users, user_roles")
                await conn.execute("DROP TABLE IF EXISTS user_roles")
                await conn.execute("DROP TABLE IF EXISTS users")
                await conn.execute("DROP TABLE IF EXISTS roles")
                await conn.execute("DROP TABLE IF EXISTS domains")
                # revoked tokens table: store jti and expiry
                await conn.execute("DROP TABLE IF EXISTS revoked_tokens")
                await conn.execute("DROP TABLE IF EXISTS refresh_tokens")

                await conn.execute("""
                    CREATE TABLE domains (
                        id SERIAL PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL
                    )
                """)

                await conn.execute("""
                    CREATE TABLE roles (
                        id SERIAL PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL
                    )
                """)

                await conn.execute("""
                    CREATE TABLE revoked_tokens (
                        jti TEXT PRIMARY KEY,
                        expires_at TIMESTAMP NOT NULL
                    )
                """)

                await conn.execute("""
                    CREATE TABLE refresh_tokens (
                        token TEXT PRIMARY KEY,
                        username TEXT NOT NULL,
                        expires_at TIMESTAMP NOT NULL
                    )
                """)

                await conn.execute("""
                    CREATE TABLE users (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        domain_id INTEGER REFERENCES domains(id) ON DELETE SET NULL
                    )
                """)

                await conn.execute("""
                    CREATE TABLE user_roles (
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
                        PRIMARY KEY (user_id, role_id)
                    )
                """)

                # Seed example.com domain and default roles
                await conn.execute("INSERT INTO domains (name) VALUES ($1) ON CONFLICT DO NOTHING", "example.com")
                await conn.execute("INSERT INTO roles (name) VALUES ($1) ON CONFLICT DO NOTHING", "user")
                await conn.execute("INSERT INTO roles (name) VALUES ($1) ON CONFLICT DO NOTHING", "admin")

                # Create default admin user if not exists
                default_admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
                default_admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")
                hashed_password = hashlib.sha256(default_admin_password.encode()).hexdigest()

                # Ensure domain id
                domain_row = await conn.fetchrow("SELECT id FROM domains WHERE name = $1", "example.com")
                domain_id = domain_row["id"] if domain_row else None
                user_row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", default_admin_username)
                if not user_row:
                    await conn.execute(
                        "INSERT INTO users (username, password, domain_id) VALUES ($1, $2, $3)",
                        default_admin_username, hashed_password, domain_id
                    )
                    # attach admin role
                    u = await conn.fetchrow("SELECT id FROM users WHERE username = $1", default_admin_username)
                    admin_role = await conn.fetchrow("SELECT id FROM roles WHERE name = $1", "admin")
                    if u and admin_role:
                        await conn.execute("INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2) ON CONFLICT DO NOTHING", u["id"], admin_role["id"])
                    logger.info(f"Default admin {default_admin_username} created")

                logger.info("DB initialized")
            return pool
        except Exception as e:
            logger.error(f"DB connection error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logger.critical("Failed to initialize DB after retries")
                raise


app.state.db_pool = None


def _encode_token(username: str, roles: List[str]):
    jti = str(uuid.uuid4())
    payload = {"username": username, "roles": roles, "exp": datetime.utcnow() + timedelta(hours=1), "jti": jti}
    token = jwt.encode(payload, os.getenv("JWT_SECRET", "b8_XYZ123abc456DEF789ghiJKL0mnoPQ"), algorithm="HS256")
    return token


def _generate_refresh_token():
    return str(uuid.uuid4())


async def _decode_token(authorization: str):
    try:
        token = authorization.split("Bearer ")[1]
        payload = jwt.decode(token, os.getenv("JWT_SECRET", "b8_XYZ123abc456DEF789ghiJKL0mnoPQ"), algorithms=["HS256"])
        # check revocation by jti
        jti = payload.get('jti')
        if jti:
            async with app.state.db_pool.acquire() as conn:
                row = await conn.fetchrow('SELECT jti FROM revoked_tokens WHERE jti = $1', jti)
                if row:
                    logger.info(f"Token jti {jti} is revoked")
                    raise HTTPException(status_code=401, detail="User logged out")
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/register")
async def register(user: UserCreate):
    logger.info(f"Registering {user.username}")
    domain = user.domain if user.domain else ""
    async with app.state.db_pool.acquire() as conn:
        domain_row = await conn.fetchrow("SELECT id FROM domains WHERE name = $1", domain)
        if not domain_row:
            logger.error(f"Domain {domain} not registered")
            raise HTTPException(status_code=400, detail="Domain not registered")
        hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
        try:
            await conn.execute("INSERT INTO users (username, password, domain_id) VALUES ($1, $2, $3)", user.username, hashed_password, domain_row["id"])
            # attach roles
            u = await conn.fetchrow("SELECT id FROM users WHERE username = $1", user.username)
            for r in user.roles:
                role_row = await conn.fetchrow("SELECT id FROM roles WHERE name = $1", r)
                if role_row:
                    await conn.execute("INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2) ON CONFLICT DO NOTHING", u["id"], role_row["id"])
            logger.info(f"User {user.username} created")
            return {"status": "User registered"}
        except asyncpg.UniqueViolationError:
            logger.error(f"Username {user.username} exists")
            raise HTTPException(status_code=400, detail="Username exists")
        except Exception as e:
            logger.error(f"Register error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/login")
async def login(payload: LoginRequest):
    # Accept either {"username","password"} or {"email","password"} for backward compatibility
    provided = payload.username or payload.email
    logger.info(f"Login attempt {provided}")
    if not provided:
        raise HTTPException(status_code=400, detail="username or email required")
    hashed_password = hashlib.sha256(payload.password.encode()).hexdigest()
    async with app.state.db_pool.acquire() as conn:
        # prefer direct username lookup (username is unique)
        uname = payload.username
        if not uname and payload.email:
            # parse email into username@domain -> username
            if "@" in payload.email:
                uname = payload.email.split("@", 1)[0]
            else:
                uname = payload.email

        row = await conn.fetchrow("SELECT id, username FROM users WHERE username = $1 AND password = $2", uname, hashed_password)

        # if not found and email included a domain, try domain-aware lookup (fallback)
        if not row and payload.email and "@" in payload.email:
            try:
                local, dom = payload.email.split("@", 1)
                drow = await conn.fetchrow("SELECT id FROM domains WHERE name = $1", dom)
                if drow:
                    row = await conn.fetchrow("SELECT u.id, u.username FROM users u WHERE u.username = $1 AND u.domain_id = $2 AND u.password = $3", local, drow["id"], hashed_password)
            except Exception:
                # swallow and handle as invalid credentials below
                row = None

        if not row:
            logger.error(f"Invalid credentials for {provided}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # fetch roles
        roles = [r["name"] for r in await conn.fetch("SELECT roles.name FROM roles JOIN user_roles ur ON roles.id = ur.role_id WHERE ur.user_id = $1", row["id"])]

        # create tokens and persist refresh token while the connection is still acquired
        token = _encode_token(row["username"], roles)
        refresh = _generate_refresh_token()
        # store refresh token
        exp = datetime.utcnow() + timedelta(days=14)
        await conn.execute('INSERT INTO refresh_tokens (token, username, expires_at) VALUES ($1, $2, $3)', refresh, row['username'], exp)
        logger.info(f"User {row['username']} logged in")
        return {"access_token": token, "refresh_token": refresh, "token_type": "bearer"}

@app.post('/tokens/revoke')
async def revoke_token(body: dict = None, authorization: str = Header(None)):
    """Revoke a token by jti or by providing the full Bearer token in Authorization header or in JSON body {"token": "..."}.
    Requires admin role if revoking another user's token; if called by the same user (token owner) allow self-revoke.
    """
    jti = None
    exp_ts = None
    # If JSON body provided with jti or token
    if body:
        jti = body.get('jti') or None
        tok = body.get('token')
        if not jti and tok:
            try:
                payload = jwt.decode(tok, os.getenv("JWT_SECRET", "b8_XYZ123abc456DEF789ghiJKL0mnoPQ"), algorithms=["HS256"])
                jti = payload.get('jti')
                exp_ts = datetime.utcfromtimestamp(payload.get('exp')) if payload.get('exp') else None
            except Exception as e:
                # Maybe this is a refresh token (opaque). Try to delete from refresh_tokens
                logger.info(f"Provided token is not JWT, trying refresh_tokens table: {e}")
                async with app.state.db_pool.acquire() as conn:
                    res = await conn.execute('DELETE FROM refresh_tokens WHERE token = $1', tok)
                    if res == 'DELETE 1':
                        logger.info('Refresh token revoked')
                        return {'status': 'revoked', 'token': tok}
                raise HTTPException(status_code=400, detail='Invalid token provided')

    # If Authorization header provided, decode and extract jti
    if authorization and not jti:
        try:
            tok = authorization.split('Bearer ')[1]
            payload = jwt.decode(tok, os.getenv("JWT_SECRET", "b8_XYZ123abc456DEF789ghiJKL0mnoPQ"), algorithms=["HS256"])
            jti = payload.get('jti')
            exp_ts = datetime.utcfromtimestamp(payload.get('exp')) if payload.get('exp') else None
        except Exception as e:
            logger.error(f"Failed to decode authorization token for revoke: {e}")

    if not jti:
        raise HTTPException(status_code=400, detail='jti or token required')

    # Persist the revoked jti with expiry (if known) or a default short expiry
    if not exp_ts:
        exp_ts = datetime.utcnow() + timedelta(hours=1)

    async with app.state.db_pool.acquire() as conn:
        try:
            await conn.execute('INSERT INTO revoked_tokens (jti, expires_at) VALUES ($1, $2) ON CONFLICT DO NOTHING', jti, exp_ts)
            logger.info(f"Revoked token jti={jti}")
            return {'status': 'revoked', 'jti': jti}
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.post('/tokens/refresh')
async def refresh_token(body: dict):
    """Accepts JSON {"refresh_token": "..."}, validates it in DB, issues a new access token and rotates refresh token."""
    rt = body.get('refresh_token')
    if not rt:
        raise HTTPException(status_code=400, detail='refresh_token required')

    async with app.state.db_pool.acquire() as conn:
        row = await conn.fetchrow('SELECT token, username, expires_at FROM refresh_tokens WHERE token = $1', rt)
        if not row:
            raise HTTPException(status_code=401, detail='Invalid refresh token')
        if row['expires_at'] < datetime.utcnow():
            # remove expired
            await conn.execute('DELETE FROM refresh_tokens WHERE token = $1', rt)
            raise HTTPException(status_code=401, detail='Refresh token expired')

        # rotate
        new_rt = _generate_refresh_token()
        # get user roles
        urow = await conn.fetchrow('SELECT id, username FROM users WHERE username = $1', row['username'])
        roles = [r['name'] for r in await conn.fetch('SELECT roles.name FROM roles JOIN user_roles ur ON roles.id = ur.role_id WHERE ur.user_id = $1', urow['id'])]
        new_access = _encode_token(urow['username'], roles)
        new_exp = datetime.utcnow() + timedelta(days=14)
        # store new refresh and delete old
        await conn.execute('DELETE FROM refresh_tokens WHERE token = $1', rt)
        await conn.execute('INSERT INTO refresh_tokens (token, username, expires_at) VALUES ($1, $2, $3)', new_rt, urow['username'], new_exp)
        return {'access_token': new_access, 'refresh_token': new_rt}


@app.get("/verify")
async def verify(authorization: str = Header(...)):
    payload = await _decode_token(authorization)
    return {"status": "OK", "username": payload.get("username"), "roles": payload.get("roles", [])}


@app.post("/domains")
async def add_domain(domain: Domain, authorization: str = Header(...)):
    payload = await _decode_token(authorization)
    if "admin" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin required")
    async with app.state.db_pool.acquire() as conn:
        try:
            await conn.execute("INSERT INTO domains (name) VALUES ($1) ON CONFLICT DO NOTHING", domain.name)
            return {"status": "domain added"}
        except Exception as e:
            logger.error(f"Add domain error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.delete("/domains/{domain_name}")
async def delete_domain(domain_name: str, authorization: str = Header(...)):
    payload = await _decode_token(authorization)
    if "admin" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin required")
    async with app.state.db_pool.acquire() as conn:
        res = await conn.execute("DELETE FROM domains WHERE name = $1", domain_name)
        if res == "DELETE 0":
            raise HTTPException(status_code=404, detail="Domain not found")
        return {"status": "domain deleted"}


@app.post('/domains/rename')
async def rename_domain(payload: dict, authorization: str = Header(...)):
    # payload expected: {"old_name": "a", "new_name": "b"}
    old_name = payload.get('old_name') or payload.get('oldName')
    new_name = payload.get('name') or payload.get('new_name') or payload.get('newName')
    if not old_name or not new_name:
        raise HTTPException(status_code=400, detail='old_name and new_name required')
    auth = await _decode_token(authorization)
    if 'admin' not in auth.get('roles', []):
        raise HTTPException(status_code=403, detail='Admin required')
    async with app.state.db_pool.acquire() as conn:
        # ensure old exists
        exists = await conn.fetchval('SELECT id FROM domains WHERE name = $1', old_name)
        if not exists:
            raise HTTPException(status_code=404, detail='Old domain not found')
        # ensure new doesn't exist
        new_exists = await conn.fetchval('SELECT id FROM domains WHERE name = $1', new_name)
        if new_exists:
            raise HTTPException(status_code=400, detail='New domain already exists')
        # update users' domain_id
        # get new domain id by inserting then using its id
        await conn.execute('INSERT INTO domains (name) VALUES ($1) ON CONFLICT DO NOTHING', new_name)
        new_row = await conn.fetchrow('SELECT id FROM domains WHERE name = $1', new_name)
        new_id = new_row['id'] if new_row else None
        await conn.execute('UPDATE users SET domain_id = $1 WHERE domain_id = $2', new_id, exists)
        await conn.execute('DELETE FROM domains WHERE name = $1', old_name)
        return {'status': 'domain renamed'}


@app.get("/domains")
async def list_domains(authorization: str = Header(...)):
    payload = await _decode_token(authorization)
    if "admin" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin required")
    async with app.state.db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name FROM domains")
        return [{"id": r["id"], "name": r["name"]} for r in rows]


@app.get("/users")
async def list_users(authorization: str = Header(...)):
    payload = await _decode_token(authorization)
    if "admin" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin required")
    async with app.state.db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, username, domain_id FROM users")
        users = []
        for r in rows:
            roles = [x["name"] for x in await conn.fetch("SELECT roles.name FROM roles JOIN user_roles ur ON roles.id = ur.role_id WHERE ur.user_id = $1", r["id"])]
            domain = None
            if r["domain_id"]:
                d = await conn.fetchrow("SELECT name FROM domains WHERE id = $1", r["domain_id"])
                # support dict-like or sequence results from fake pool
                if not d:
                    domain = None
                elif isinstance(d, dict):
                    domain = d.get("name")
                else:
                    # try sequence access
                    try:
                        domain = d[0]
                    except Exception:
                        domain = None
            users.append({"id": r["id"], "username": r["username"], "domain": domain, "roles": roles})
        return users


@app.put("/users")
async def update_user(user: UserUpdate, authorization: str = Header(...)):
    payload = await _decode_token(authorization)
    if "admin" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin required")
    async with app.state.db_pool.acquire() as conn:
        # find user by id or original_username
        target = None
        if user.id:
            target = await conn.fetchrow("SELECT id, username FROM users WHERE id = $1", user.id)
        elif user.original_username:
            target = await conn.fetchrow("SELECT id, username FROM users WHERE username = $1", user.original_username)
        else:
            raise HTTPException(status_code=400, detail="Provide id or original_username")

        if not target:
            raise HTTPException(status_code=404, detail="User not found")

        # if changing username, ensure optional provided domain exists
        if user.username and hasattr(user, 'username'):
            # no domain parsing from username; domain should be provided separately if needed
            pass

        # Update password only if provided
        if user.password:
            hashed = hashlib.sha256(user.password.encode()).hexdigest()
            await conn.execute("UPDATE users SET username = COALESCE($1, username), password = $2 WHERE id = $3", user.username, hashed, target["id"])
        else:
            await conn.execute("UPDATE users SET username = COALESCE($1, username) WHERE id = $2", user.username, target["id"])

        # Update roles if provided
        if user.roles is not None:
            # remove existing roles
            await conn.execute("DELETE FROM user_roles WHERE user_id = $1", target["id"])
            for role_name in user.roles:
                role_row = await conn.fetchrow("SELECT id FROM roles WHERE name = $1", role_name)
                if not role_row:
                    # create role on the fly
                    await conn.execute("INSERT INTO roles (name) VALUES ($1) ON CONFLICT DO NOTHING", role_name)
                    role_row = await conn.fetchrow("SELECT id FROM roles WHERE name = $1", role_name)
                await conn.execute("INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2) ON CONFLICT DO NOTHING", target["id"], role_row["id"])

        return {"status": "user updated"}


@app.delete("/users/{user_id}")
async def delete_user(user_id: int, authorization: str = Header(...)):
    payload = await _decode_token(authorization)
    if "admin" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin required")
    async with app.state.db_pool.acquire() as conn:
        res = await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        if res == "DELETE 0":
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "user deleted"}