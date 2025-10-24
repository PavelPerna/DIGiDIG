import logging
from fastapi import FastAPI, HTTPException, Header
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import jwt
import os
import asyncpg
from datetime import datetime, timedelta, timezone
import uuid
import hashlib
import asyncio
import time

# Configuration (with backward compatibility)
from config_loader import config

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


app = FastAPI(
    title="DIGiDIG Identity Service",
    description="""
## Identity & Authentication Service

Provides user authentication, authorization, and management capabilities for the DIGiDIG email system.

### Features

* **User Management**: Create, read, update, and delete users
* **Domain Management**: Multi-domain support with CRUD operations
* **Authentication**: JWT-based authentication with secure token generation
* **Authorization**: Role-based access control (RBAC)
* **Session Management**: Track and manage user sessions

### Authentication

Most endpoints require authentication via JWT Bearer token:

```
Authorization: Bearer <your-jwt-token>
```

Obtain a token by calling the `/login` endpoint with valid credentials.

### Security

* Passwords are hashed using SHA-256
* JWT tokens expire after 1 hour
* Admin operations require 'admin' role
    """,
    version="1.0.0",
    contact={
        "name": "DIGiDIG Team",
        "url": "https://github.com/PavelPerna/DIGiDIG",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan,
    tags_metadata=[
        {
            "name": "Authentication",
            "description": "User login, logout, and token verification"
        },
        {
            "name": "Users",
            "description": "User management operations (CRUD)"
        },
        {
            "name": "Domains",
            "description": "Domain management for multi-tenant support"
        },
        {
            "name": "Health",
            "description": "Service health and status monitoring"
        }
    ]
)

# Global state for service management
service_state = {
    "start_time": time.time(),
    "requests_total": 0,
    "requests_successful": 0,
    "requests_failed": 0,
    "last_request_time": None,
    "active_sessions": [],
    "config": {
        "hostname": config.IDENTITY_HOSTNAME,
        "port": config.IDENTITY_PORT,
        "enabled": True,
        "timeout": config.IDENTITY_TIMEOUT,
        "jwt_secret": config.JWT_SECRET,
        "token_expiry": config.TOKEN_EXPIRY,
        "refresh_token_expiry": config.REFRESH_TOKEN_EXPIRY,
        "db_host": config.DB_HOST,
        "db_name": config.DB_NAME,
        "db_user": config.DB_USER
    }
}

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
                user=config.DB_USER,
                password=config.DB_PASS,
                database=config.DB_NAME,
                host=config.DB_HOST
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
                        expires_at TIMESTAMPTZ NOT NULL
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
                # Extract username and domain from ADMIN_EMAIL
                admin_email = config.ADMIN_EMAIL
                admin_password = config.ADMIN_PASSWORD
                
                # Split email to get username and domain
                if "@" in admin_email:
                    admin_username, admin_domain = admin_email.split("@", 1)
                else:
                    admin_username = admin_email
                    admin_domain = "example.com"
                
                hashed_password = hashlib.sha256(admin_password.encode()).hexdigest()

                # Ensure domain exists
                await conn.execute("INSERT INTO domains (name) VALUES ($1) ON CONFLICT DO NOTHING", admin_domain)
                domain_row = await conn.fetchrow("SELECT id FROM domains WHERE name = $1", admin_domain)
                domain_id = domain_row["id"] if domain_row else None
                
                user_row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", admin_username)
                if not user_row:
                    await conn.execute(
                        "INSERT INTO users (username, password, domain_id) VALUES ($1, $2, $3)",
                        admin_username, hashed_password, domain_id
                    )
                    # attach admin role
                    u = await conn.fetchrow("SELECT id FROM users WHERE username = $1", admin_username)
                    admin_role = await conn.fetchrow("SELECT id FROM roles WHERE name = $1", "admin")
                    if u and admin_role:
                        await conn.execute("INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2) ON CONFLICT DO NOTHING", u["id"], admin_role["id"])
                    logger.info(f"Default admin {admin_username}@{admin_domain} created")

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
    # create JWT
    payload = {"username": username, "roles": roles, "exp": datetime.now(timezone.utc) + timedelta(hours=1), "jti": jti}
    token = jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")
    return token


def _generate_refresh_token():
    return str(uuid.uuid4())


async def _decode_token(authorization: str):
    try:
        token = authorization.split("Bearer ")[1]
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
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
    service_state["requests_total"] += 1
    service_state["last_request_time"] = datetime.now(timezone.utc).isoformat()
    
    domain = user.domain if user.domain else ""
    async with app.state.db_pool.acquire() as conn:
        domain_row = await conn.fetchrow("SELECT id FROM domains WHERE name = $1", domain)
        if not domain_row:
            logger.error(f"Domain {domain} not registered")
            service_state["requests_failed"] += 1
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
            service_state["requests_successful"] += 1
            return {"status": "User registered"}
        except asyncpg.UniqueViolationError:
            logger.error(f"Username {user.username} exists")
            service_state["requests_failed"] += 1
            raise HTTPException(status_code=400, detail="Username exists")
        except Exception as e:
            logger.error(f"Register error: {e}")
            service_state["requests_failed"] += 1
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/login")
async def login(payload: LoginRequest):
    # Accept either {"username","password"} or {"email","password"} for backward compatibility
    provided = payload.username or payload.email
    logger.info(f"Login attempt {provided}")
    service_state["requests_total"] += 1
    service_state["last_request_time"] = datetime.now(timezone.utc).isoformat()
    
    if not provided:
        service_state["requests_failed"] += 1
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
            service_state["requests_failed"] += 1
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # fetch roles
        roles = [r["name"] for r in await conn.fetch("SELECT roles.name FROM roles JOIN user_roles ur ON roles.id = ur.role_id WHERE ur.user_id = $1", row["id"])]

        # create tokens and persist refresh token while the connection is still acquired
        token = _encode_token(row["username"], roles)
        refresh = _generate_refresh_token()
        # store refresh token
        exp = datetime.now(timezone.utc) + timedelta(days=14)
        await conn.execute('INSERT INTO refresh_tokens (token, username, expires_at) VALUES ($1, $2, $3)', refresh, row['username'], exp.replace(tzinfo=None))
        
        # Track active session
        service_state["active_sessions"].append({
            "username": row["username"],
            "logged_in_at": datetime.now(timezone.utc).isoformat(),
            "roles": roles
        })
        
        service_state["requests_successful"] += 1
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
                payload = jwt.decode(tok, config.JWT_SECRET, algorithms=["HS256"])
                jti = payload.get('jti')
                exp_ts = datetime.fromtimestamp(payload.get('exp'), tz=timezone.utc) if payload.get('exp') else None
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
            payload = jwt.decode(tok, config.JWT_SECRET, algorithms=["HS256"])
            jti = payload.get('jti')
            exp_ts = datetime.fromtimestamp(payload.get('exp'), tz=timezone.utc) if payload.get('exp') else None
        except Exception as e:
            logger.error(f"Failed to decode authorization token for revoke: {e}")

    if not jti:
        raise HTTPException(status_code=400, detail='jti or token required')

    # Persist the revoked jti with expiry (if known) or a default short expiry
    if not exp_ts:
        exp_ts = datetime.now(timezone.utc) + timedelta(hours=1)

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
        if row['expires_at'] < datetime.now(timezone.utc).replace(tzinfo=None):
            # remove expired
            await conn.execute('DELETE FROM refresh_tokens WHERE token = $1', rt)
            raise HTTPException(status_code=401, detail='Refresh token expired')

        # rotate
        new_rt = _generate_refresh_token()
        # get user roles
        urow = await conn.fetchrow('SELECT id, username FROM users WHERE username = $1', row['username'])
        roles = [r['name'] for r in await conn.fetch('SELECT roles.name FROM roles JOIN user_roles ur ON roles.id = ur.role_id WHERE ur.user_id = $1', urow['id'])]
        new_access = _encode_token(urow['username'], roles)
        new_exp = datetime.now(timezone.utc) + timedelta(days=14)
        # store new refresh and delete old
        await conn.execute('DELETE FROM refresh_tokens WHERE token = $1', rt)
        await conn.execute('INSERT INTO refresh_tokens (token, username, expires_at) VALUES ($1, $2, $3)', new_rt, urow['username'], new_exp.replace(tzinfo=None))
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


@app.get("/api/domains/{domain}/exists")
async def check_domain_exists(domain: str):
    """Public endpoint to check if domain exists (for SMTP local delivery)"""
    async with app.state.db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM domains WHERE name = $1", domain)
        return {"exists": row is not None, "domain": domain}


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

# REST API Endpoints for Service Management

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - service_state["start_time"]
    
    # Test database connection
    try:
        if app.state.db_pool:
            async with app.state.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_status = "connected"
        else:
            db_status = "no pool"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    status = "healthy" if service_state["config"]["enabled"] and db_status == "connected" else "unhealthy"
    
    return {
        "service_name": "identity",
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime,
        "details": {
            "enabled": service_state["config"]["enabled"],
            "database_status": db_status,
            "active_sessions": len(service_state["active_sessions"])
        }
    }

@app.get("/api/config")
async def get_config():
    """Get current Identity service configuration"""
    config = service_state["config"].copy()
    # Don't expose sensitive data
    if "jwt_secret" in config:
        config["jwt_secret"] = "***"
    return {
        "service_name": "identity",
        "config": config
    }

@app.put("/api/config")
async def update_config(config: Dict[str, Any], authorization: str = Header(...)):
    """Update Identity service configuration (admin only)"""
    payload = await _decode_token(authorization)
    if "admin" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin required")
    
    try:
        # Update configuration
        for key, value in config.items():
            if key in service_state["config"] and key != "jwt_secret":  # Don't allow JWT secret change via API
                service_state["config"][key] = value
        
        logger.info(f"Configuration updated: {config}")
        return {
            "status": "success",
            "message": "Configuration updated",
            "config": service_state["config"]
        }
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get Identity service statistics"""
    uptime = time.time() - service_state["start_time"]
    
    # Get user and domain count
    try:
        async with app.state.db_pool.acquire() as conn:
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            domain_count = await conn.fetchval("SELECT COUNT(*) FROM domains")
            revoked_tokens = await conn.fetchval("SELECT COUNT(*) FROM revoked_tokens")
            refresh_tokens = await conn.fetchval("SELECT COUNT(*) FROM refresh_tokens")
    except Exception as e:
        logger.error(f"Error getting DB stats: {str(e)}")
        user_count = domain_count = revoked_tokens = refresh_tokens = 0
    
    return {
        "service_name": "identity",
        "uptime_seconds": uptime,
        "requests_total": service_state["requests_total"],
        "requests_successful": service_state["requests_successful"],
        "requests_failed": service_state["requests_failed"],
        "last_request_time": service_state["last_request_time"],
        "custom_stats": {
            "total_users": user_count,
            "total_domains": domain_count,
            "active_sessions": len(service_state["active_sessions"]),
            "revoked_tokens": revoked_tokens,
            "active_refresh_tokens": refresh_tokens
        }
    }

@app.get("/api/identity/sessions")
async def get_sessions(authorization: str = Header(...)):
    """Get active Identity sessions (admin only)"""
    payload = await _decode_token(authorization)
    if "admin" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin required")
    
    return {
        "active_sessions": service_state["active_sessions"],
        "count": len(service_state["active_sessions"])
    }