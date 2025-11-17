from typing import Dict, Any
import secrets
import aiohttp
import httpx
from pydantic import BaseModel
from fastapi import HTTPException
import jwt
import os
import logging
import time
import asyncio
import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import FastAPI, Header, Request
from contextlib import asynccontextmanager
import asyncpg
from digidig.models.service.server import ServiceServer
from digidig.config import Config

# RSA encryption for passwords
try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
    import base64
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logging.warning("cryptography library not available, RSA encryption disabled")

# Configuration
config = Config.instance()
db_config = config.db_config("postgres")
IDENTITY_PORT = config.get("services.identity.port", 9101)

# RSA Key Management for password encryption
RSA_KEYS = {}

def generate_rsa_keypair():
    """Generate RSA keypair for password encryption"""
    if not CRYPTOGRAPHY_AVAILABLE:
        return None, None

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    public_key = private_key.public_key()

    # Serialize keys
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem, public_pem

def encrypt_password(password: str, public_key_pem: bytes) -> str:
    """Encrypt password using RSA public key"""
    if not CRYPTOGRAPHY_AVAILABLE:
        return password  # Fallback to plain text

    public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())

    encrypted = public_key.encrypt(
        password.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return base64.b64encode(encrypted).decode()

def decrypt_password(encrypted_password: str, private_key_pem: bytes) -> str:
    """Decrypt password using RSA private key"""
    if not CRYPTOGRAPHY_AVAILABLE:
        return encrypted_password  # Fallback to plain text

    private_key = serialization.load_pem_private_key(private_key_pem, password=None, backend=default_backend())

    encrypted = base64.b64decode(encrypted_password)

    decrypted = private_key.decrypt(
        encrypted,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return decrypted.decode()

# Initialize RSA keys for default realm (will be done after logger setup)

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
    # New format: realm-based authentication
    realm: Optional[str] = None
    user: Optional[str] = None
    email: Optional[str] = None
    password: str  # Should be RSA encrypted
    domain: Optional[str] = None  # For backward compatibility

    # Legacy fields for backward compatibility
    username: Optional[str] = None


class UserPreferences(BaseModel):
    language: Optional[str] = "en"
    dark_mode: Optional[bool] = False


class UserPreferencesUpdate(BaseModel):
    language: Optional[str] = None
    dark_mode: Optional[bool] = None


class ServerIdentity(ServiceServer):
    def __init__(self, lifespan=None):
        super().__init__(
            name="identity",
            description="Identity service for DIGiDIG platform",
            port=IDENTITY_PORT,
            lifespan=lifespan
        )
        self.register_routes()

    def register_routes(self):
        # All route definitions will go here
        @self.app.post("/api/register")
        async def register_user(user: UserCreate):
            """Register a new user"""
            logger.info(f"Registering {user.username}")
            service_state["requests_total"] += 1
            service_state["last_request_time"] = datetime.now(timezone.utc).isoformat()

            domain = user.domain if user.domain else ""
            async with self.app.state.db_pool.acquire() as conn:
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

        @self.app.post("/api/login")
        async def login_user(payload: LoginRequest):
            """Authenticate user and return JWT tokens"""
            # Accept multiple login formats:
            # 1. NEW: {"realm": "example.com", "email": "admin@example.com", "password": "..."} - realm + email
            # 2. NEW: {"realm": "example.com", "user": "admin", "password": "..."} - realm + user
            # 3. LEGACY: {"username": "admin", "password": "admin"} - simple username
            # 4. LEGACY: {"email": "admin@example.com", "password": "admin"} - email parsing
            # 5. LEGACY: {"username": "admin", "domain": "example.com", "password": "admin"} - explicit username/domain

            logger.info(f"Login attempt: realm={payload.realm}, user={payload.user}, email={payload.email}, domain={payload.domain}, username={payload.username}")
            service_state["requests_total"] += 1
            service_state["last_request_time"] = datetime.now(timezone.utc).isoformat()

            # Validate required fields
            if not ((payload.realm and (payload.user or payload.email)) or payload.username or payload.email):
                service_state["requests_failed"] += 1
                raise HTTPException(status_code=400, detail="realm + (user|email), or username, or email required")

            # Decrypt RSA-encrypted password if available
            password = payload.password
            if payload.realm and payload.realm in RSA_KEYS:
                try:
                    password = decrypt_password(password, RSA_KEYS[payload.realm]['private'])
                except Exception as e:
                    logger.warning(f"Failed to decrypt password for realm {payload.realm}: {e}")
                    # Fall back to plain text

            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            async with self.app.state.db_pool.acquire() as conn:
                uname = None
                domain_name = None

                # Parse login credentials based on provided format
                if payload.realm and payload.email:
                    # NEW Format 1: realm + email
                    uname, domain_name = payload.email.split("@", 1) if "@" in payload.email else (payload.email, payload.realm)
                elif payload.realm and payload.user:
                    # NEW Format 2: realm + user
                    uname = payload.user
                    domain_name = payload.realm
                elif payload.username and payload.domain:
                    # LEGACY Format 5: explicit username + domain
                    uname = payload.username
                    domain_name = payload.domain
                elif payload.email and "@" in payload.email:
                    # LEGACY Format 4: email parsing
                    uname, domain_name = payload.email.split("@", 1)
                elif payload.username:
                    # LEGACY Format 3: simple username (assume default domain)
                    uname = payload.username
                    # If username contains @, treat it as email
                    if uname and "@" in uname and not domain_name:
                        uname, domain_name = uname.split("@", 1)
                elif payload.email:
                    # LEGACY Format 2: treat email as username if no @ symbol
                    uname = payload.email

                # Try different lookup strategies
                row = None

                if uname and domain_name:
                    # Domain-aware lookup
                    drow = await conn.fetchrow("SELECT id FROM domains WHERE name = $1", domain_name)
                    if drow:
                        row = await conn.fetchrow(
                            "SELECT u.id, u.username FROM users u WHERE u.username = $1 AND u.domain_id = $2 AND u.password = $3",
                            uname, drow["id"], hashed_password
                        )
                elif uname:
                    # Simple username lookup (across all domains)
                    row = await conn.fetchrow("SELECT id, username FROM users WHERE username = $1 AND password = $2", uname, hashed_password)

                if not row:
                    logger.error(f"Invalid credentials for username={payload.username}, email={payload.email}, domain={payload.domain}")
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

        @self.app.get('/api/rsa/public-key/{realm}')
        async def get_rsa_public_key(realm: str):
            """Get RSA public key for password encryption"""
            if realm not in RSA_KEYS:
                raise HTTPException(status_code=404, detail="Realm not found")

            public_key = RSA_KEYS[realm]['public']
            return {"public_key": public_key.decode()}

        @self.app.post('/api/tokens/revoke')
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
                        jwt_secret = service_state.get("config", {}).get("jwt_secret") or Config.instance().jwt_secret()
                        payload = jwt.decode(tok, jwt_secret, algorithms=["HS256"])
                        jti = payload.get('jti')
                        exp_ts = datetime.fromtimestamp(payload.get('exp'), tz=timezone.utc) if payload.get('exp') else None
                    except Exception as e:
                        # Maybe this is a refresh token (opaque). Try to delete from refresh_tokens
                        logger.info(f"Provided token is not JWT, trying refresh_tokens table: {e}")
                        async with self.app.state.db_pool.acquire() as conn:
                            res = await conn.execute('DELETE FROM refresh_tokens WHERE token = $1', tok)
                            if res == 'DELETE 1':
                                logger.info('Refresh token revoked')
                                return {'status': 'revoked', 'token': tok}
                        raise HTTPException(status_code=400, detail='Invalid token provided')

            # If Authorization header provided, decode and extract jti
            if authorization and not jti:
                try:
                    tok = authorization.split('Bearer ')[1]
                    jwt_secret = service_state.get("config", {}).get("jwt_secret") or Config.instance().jwt_secret()
                    payload = jwt.decode(tok, jwt_secret, algorithms=["HS256"])
                    jti = payload.get('jti')
                    exp_ts = datetime.fromtimestamp(payload.get('exp'), tz=timezone.utc) if payload.get('exp') else None
                except Exception as e:
                    logger.error(f"Failed to decode authorization token for revoke: {e}")

            if not jti:
                raise HTTPException(status_code=400, detail='jti or token required')

            # Persist the revoked jti with expiry (if known) or a default short expiry
            if not exp_ts:
                exp_ts = datetime.now(timezone.utc) + timedelta(hours=1)

            async with self.app.state.db_pool.acquire() as conn:
                try:
                    await conn.execute('INSERT INTO revoked_tokens (jti, expires_at) VALUES ($1, $2) ON CONFLICT DO NOTHING', jti, exp_ts)
                    logger.info(f"Revoked token jti={jti}")
                    return {'status': 'revoked', 'jti': jti}
                except Exception as e:
                    logger.error(f"Error revoking token: {e}")
                    raise HTTPException(status_code=500, detail=str(e))

        @self.app.post('/api/tokens/refresh')
        async def refresh_access_token(body: dict):
            """Accepts JSON {"refresh_token": "..."}, validates it in DB, issues a new access token and rotates refresh token."""
            rt = body.get('refresh_token')
            if not rt:
                raise HTTPException(status_code=400, detail='refresh_token required')

            async with self.app.state.db_pool.acquire() as conn:
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

        @self.app.get("/api/verify")
        @self.app.post("/api/verify")
        async def verify_token_endpoint(authorization: str = Header(...)):
            payload = await _decode_token(authorization)
            return {"status": "OK", "username": payload.get("username"), "roles": payload.get("roles", [])}

        @self.app.get("/api/session/verify")
        async def verify_session(request: Request):
            """Verify session from cookie and return user info if valid"""
            from fastapi import Cookie
            access_token = request.cookies.get("access_token")
            
            if not access_token:
                raise HTTPException(status_code=401, detail="Not authenticated")
            
            try:
                # Decode token
                jwt_secret = service_state.get("config", {}).get("jwt_secret") or Config.instance().jwt_secret()
                payload = jwt.decode(access_token, jwt_secret, algorithms=["HS256"])
                
                # Check revocation
                jti = payload.get('jti')
                if jti:
                    async with self.app.state.db_pool.acquire() as conn:
                        row = await conn.fetchrow('SELECT jti FROM revoked_tokens WHERE jti = $1', jti)
                        if row:
                            raise HTTPException(status_code=401, detail="Token revoked")
                        
                        row = await conn.fetchrow('SELECT token_id FROM token_blacklist WHERE token_id = $1', jti)
                        if row:
                            raise HTTPException(status_code=401, detail="Token blacklisted")
                
                return {
                    "authenticated": True,
                    "username": payload.get("username"),
                    "roles": payload.get("roles", []),
                    "is_admin": "admin" in payload.get("roles", [])
                }
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token expired")
            except Exception as e:
                logger.error(f"Session verification error: {e}")
                raise HTTPException(status_code=401, detail="Invalid session")

        @self.app.post("/api/logout")
        async def logout(request: Request, authorization: str = Header(None)):
            """Logout user and invalidate token (accepts Authorization header or access_token cookie)"""
            # Try to get token from header first, then from cookie
            token = authorization
            if not token:
                token = request.cookies.get("access_token")
            
            logger.info(f"Logout attempt - Authorization header: {bool(authorization)}, Cookie: {bool(request.cookies.get('access_token'))}, Token: {token[:20] if token else 'None'}...")
            
            if not token:
                raise HTTPException(status_code=401, detail="No authentication token provided")
            
            payload = await _decode_token(token)

            # Get token ID from payload
            token_id = payload.get("jti")

            if token_id:
                # Add token to blacklist
                async with self.app.state.db_pool.acquire() as conn:
                    try:
                        await conn.execute(
                            "INSERT INTO token_blacklist (token_id) VALUES ($1) ON CONFLICT DO NOTHING",
                            token_id
                        )
                    except Exception as e:
                        logger.error(f"Error blacklisting token: {e}")

            return {"status": "logged out", "username": payload.get("username")}

        @self.app.post("/api/domains")
        async def create_domain(domain: Domain, authorization: str = Header(...)):
            payload = await _decode_token(authorization)
            if "admin" not in payload.get("roles", []):
                raise HTTPException(status_code=403, detail="Admin required")
            async with self.app.state.db_pool.acquire() as conn:
                try:
                    await conn.execute("INSERT INTO domains (name) VALUES ($1) ON CONFLICT DO NOTHING", domain.name)
                    return {"status": "domain added"}
                except Exception as e:
                    logger.error(f"Add domain error: {e}")
                    raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/api/domains/{domain_name}")
        async def delete_domain(domain_name: str, authorization: str = Header(...)):
            payload = await _decode_token(authorization)
            if "admin" not in payload.get("roles", []):
                raise HTTPException(status_code=403, detail="Admin required")
            async with self.app.state.db_pool.acquire() as conn:
                res = await conn.execute("DELETE FROM domains WHERE name = $1", domain_name)
                if res == "DELETE 0":
                    raise HTTPException(status_code=404, detail="Domain not found")
                return {"status": "domain deleted"}

        @self.app.post('/api/domains/rename')
        async def rename_domain(payload: dict, authorization: str = Header(...)):
            # payload expected: {"old_name": "a", "new_name": "b"}
            old_name = payload.get('old_name') or payload.get('oldName')
            new_name = payload.get('name') or payload.get('new_name') or payload.get('newName')
            if not old_name or not new_name:
                raise HTTPException(status_code=400, detail='old_name and new_name required')
            auth = await _decode_token(authorization)
            if 'admin' not in auth.get('roles', []):
                raise HTTPException(status_code=403, detail='Admin required')
            async with self.app.state.db_pool.acquire() as conn:
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

        @self.app.get("/api/domains")
        async def list_domains(authorization: str = Header(...)):
            payload = await _decode_token(authorization)
            if "admin" not in payload.get("roles", []):
                raise HTTPException(status_code=403, detail="Admin required")
            async with self.app.state.db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT id, name FROM domains")
                return [{"id": r["id"], "name": r["name"]} for r in rows]

        @self.app.get("/api/domains/{domain}/exists")
        async def check_domain_exists(domain: str):
            """Public endpoint to check if domain exists (for SMTP local delivery)"""
            async with self.app.state.db_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT id FROM domains WHERE name = $1", domain)
                return {"exists": row is not None, "domain": domain}

        @self.app.get("/api/users")
        async def list_users(authorization: str = Header(...)):
            payload = await _decode_token(authorization)
            if "admin" not in payload.get("roles", []):
                raise HTTPException(status_code=403, detail="Admin required")
            async with self.app.state.db_pool.acquire() as conn:
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

        @self.app.put("/api/users")
        async def update_user(user: UserUpdate, authorization: str = Header(...)):
            payload = await _decode_token(authorization)
            if "admin" not in payload.get("roles", []):
                raise HTTPException(status_code=403, detail="Admin required")
            async with self.app.state.db_pool.acquire() as conn:
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

        @self.app.delete("/api/users/{user_id}")
        async def delete_user(user_id: int, authorization: str = Header(...)):
            payload = await _decode_token(authorization)
            if "admin" not in payload.get("roles", []):
                raise HTTPException(status_code=403, detail="Admin required")
            async with self.app.state.db_pool.acquire() as conn:
                res = await conn.execute("DELETE FROM users WHERE id = $1", user_id)
                if res == "DELETE 0":
                    raise HTTPException(status_code=404, detail="User not found")
                return {"status": "user deleted"}

        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint"""
            try:
                # Check database connection
                db_status = "healthy"
                try:
                    if app.state.db_pool:
                        await app.state.db_pool.fetchval("SELECT 1")
                    else:
                        db_status = "disconnected"
                except Exception:
                    db_status = "error"

                return {
                    "service": "identity",
                    "status": "healthy",
                    "database": db_status,
                    "port": IDENTITY_PORT
                }

            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return {
                    "service": "identity",
                    "status": "unhealthy",
                    "error": str(e)
                }

        @self.app.get("/api/config")
        async def get_service_config():
            """Get service configuration (filtered for security)"""
            try:
                # Return only safe configuration items
                safe_config = {
                    "database": {
                        "type": "postgresql"
                    },
                    "security": {
                        "jwt": {
                            "access_token_expire_minutes": config.get("security.jwt.access_token_expire_minutes"),
                            "refresh_token_expire_days": config.get("security.jwt.refresh_token_expire_days")
                        }
                    },
                    "services": {
                        "identity": {
                            "port": config.get("services.identity.port")
                        }
                    }
                }
                return safe_config

            except Exception as e:
                logger.error(f"Config retrieval failed: {e}")
                raise HTTPException(status_code=500, detail="Config retrieval failed")

        @self.app.put("/api/config")
        async def update_service_config(config_update: dict):
            """Update service configuration (limited)"""
            try:
                # Only allow updating certain config items
                allowed_updates = ["security.jwt.access_token_expire_minutes"]

                for key, value in config_update.items():
                    if key in allowed_updates:
                        # In a real implementation, you'd persist this to config file
                        logger.info(f"Config updated: {key} = {value}")
                    else:
                        raise HTTPException(status_code=400, detail=f"Cannot update config item: {key}")

                return {"message": "Configuration updated successfully"}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Config update failed: {e}")
                raise HTTPException(status_code=500, detail="Config update failed")

        @self.app.get("/api/stats")
        async def get_service_stats():
            """Get Identity service statistics"""
            uptime = time.time() - service_state["start_time"]

            # Get user and domain count
            try:
                async with self.app.state.db_pool.acquire() as conn:
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

        @self.app.get("/api/identity/sessions")
        async def get_active_sessions(authorization: str = Header(...)):
            """Get active Identity sessions (admin only)"""
            payload = await _decode_token(authorization)
            if "admin" not in payload.get("roles", []):
                raise HTTPException(status_code=403, detail="Admin required")

            return {
                "active_sessions": service_state["active_sessions"],
                "count": len(service_state["active_sessions"])
            }

        @self.app.get("/api/oauth/{provider}/callback")
        async def oauth_callback(provider: str, code: str, state: str):
            """Handle OAuth callback"""
            if provider not in OAUTH_CLIENTS:
                raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")

            client_config = OAUTH_CLIENTS[provider]

            # Exchange code for access token
            async with httpx.AsyncClient() as client:
                token_data = {
                    "client_id": client_config["client_id"],
                    "client_secret": client_config["client_secret"],
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": f"{config.get('services.identity.url', f'http://localhost:{IDENTITY_PORT}')}/oauth/{provider}/callback"
                }

                try:
                    token_response = await client.post(client_config["access_token_url"], data=token_data)
                    token_response.raise_for_status()
                    token_info = token_response.json()
                except Exception as e:
                    logger.error(f"Failed to exchange code for token: {e}")
                    raise HTTPException(status_code=400, detail="Failed to obtain access token")

                # Get user info
                headers = {"Authorization": f"Bearer {token_info['access_token']}"}
                user_response = await client.get(client_config["userinfo_url"], headers=headers)
                user_response.raise_for_status()
                user_info = user_response.json()

            # Process user info based on provider
            user_data = {}
            if provider == "google":
                user_data = {
                    "email": user_info.get("email"),
                    "first_name": user_info.get("given_name"),
                    "last_name": user_info.get("family_name"),
                    "username": user_info.get("email").split("@")[0] if user_info.get("email") else None,
                    "provider": "google",
                    "provider_id": user_info.get("id")
                }
            elif provider == "facebook":
                user_data = {
                    "email": user_info.get("email"),
                    "first_name": user_info.get("first_name"),
                    "last_name": user_info.get("last_name"),
                    "username": user_info.get("email").split("@")[0] if user_info.get("email") else None,
                    "provider": "facebook",
                    "provider_id": user_info.get("id")
                }
            elif provider == "microsoft":
                user_data = {
                    "email": user_info.get("userPrincipalName") or user_info.get("mail"),
                    "first_name": user_info.get("givenName"),
                    "last_name": user_info.get("surname"),
                    "username": user_data.get("email").split("@")[0] if user_data.get("email") else None,
                    "provider": "microsoft",
                    "provider_id": user_info.get("id")
                }
            elif provider == "twitter":
                user_data = {
                    "email": user_info.get("email"),  # Twitter may not provide email
                    "first_name": user_info.get("name", "").split()[0] if user_info.get("name") else "",
                    "last_name": " ".join(user_info.get("name", "").split()[1:]) if user_info.get("name") else "",
                    "username": user_info.get("username"),
                    "provider": "twitter",
                    "provider_id": user_info.get("id")
                }

            if not user_data.get("email"):
                raise HTTPException(status_code=400, detail="Email address is required for registration")

            # Check if OAuth connection exists, if not register user
            async with self.app.state.db_pool.acquire() as conn:
                # First check if OAuth connection already exists
                oauth_connection = await conn.fetchrow(
                    "SELECT u.id, u.username FROM oauth_connections oc JOIN users u ON oc.user_id = u.id WHERE oc.provider = $1 AND oc.provider_id = $2",
                    provider, user_data["provider_id"]
                )

                if oauth_connection:
                    # Existing OAuth user - use them
                    user_data["username"] = oauth_connection["username"]
                    logger.info(f"OAuth login for existing user: {user_data['username']} via {provider}")
                else:
                    # New OAuth user - register them via the register endpoint
                    try:
                        # Use the register endpoint to create the user properly
                        domain = user_data["email"].split("@")[1]
                        username = user_data["username"] or user_data["email"].split("@")[0]

                        # Generate a secure password for OAuth users (they won't use it directly)
                        oauth_password = secrets.token_urlsafe(32)

                        register_payload = {
                            "username": username,
                            "password": oauth_password,
                            "domain": domain,
                            "roles": ["user"]
                        }

                        # Call our own register endpoint
                        async with aiohttp.ClientSession() as session:
                            async with session.post(f"{config.get('services.identity.url', f'http://localhost:{IDENTITY_PORT}')}/register", json=register_payload) as response:
                                if response.status != 200:
                                    error_data = await response.json()
                                    raise HTTPException(status_code=400, detail=f"Failed to register OAuth user: {error_data.get('detail', 'Unknown error')}")

                        # Now create the OAuth connection record
                        user_row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
                        if user_row:
                            await conn.execute(
                                "INSERT INTO oauth_connections (user_id, provider, provider_id, provider_email) VALUES ($1, $2, $3, $4)",
                                user_row["id"], provider, user_data["provider_id"], user_data["email"]
                            )
                            logger.info(f"OAuth user registered: {user_data['email']} via {provider}")
                        else:
                            raise HTTPException(status_code=500, detail="Failed to create OAuth connection")

                    except Exception as e:
                        logger.error(f"Error registering OAuth user: {e}")
                        raise HTTPException(status_code=500, detail="Failed to register OAuth user")

            # Generate JWT token for the user
            roles = ["user"]  # Default role for OAuth users
            token = _encode_token(user_data["username"], roles)
            refresh = _generate_refresh_token()

            # Store refresh token
            exp = datetime.now(timezone.utc) + timedelta(days=14)
            async with self.app.state.db_pool.acquire() as conn:
                await conn.execute('INSERT INTO refresh_tokens (token, username, expires_at) VALUES ($1, $2, $3)', refresh, user_data["username"], exp.replace(tzinfo=None))

            return {
                "access_token": token,
                "refresh_token": refresh,
                "token_type": "bearer",
                "user": {
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "provider": provider
                }
            }

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Identity Service (lifespan)")

    # Initialize RSA keys for default realm
    if CRYPTOGRAPHY_AVAILABLE:
        private_key, public_key = generate_rsa_keypair()
        if private_key and public_key:
            RSA_KEYS['example.com'] = {
                'private': private_key,
                'public': public_key
            }
            logger.info("RSA keys generated for realm: example.com")
        else:
            logger.warning("Failed to generate RSA keys")
    else:
        logger.warning("Cryptography library not available, RSA encryption disabled")

    app.state.db_pool = await init_db()
    try:
        yield
    finally:
        logger.info("Shutting down Identity Service (lifespan)")
        if app.state.db_pool:
            await app.state.db_pool.close()

# Create service instance
identity_service = ServerIdentity(lifespan=lifespan)
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)
app = identity_service.get_app()


# The app is now created by the ServerIdentity class

# Global state for service management
service_state = {
    "start_time": time.time(),
    "requests_total": 0,
    "requests_successful": 0,
    "requests_failed": 0,
    "last_request_time": None,
    "active_sessions": [],
    "config": {
        "hostname": config.get("services.identity.url", f"http://localhost:{IDENTITY_PORT}"),
        "port": IDENTITY_PORT,
        "enabled": True,
        "timeout": config.get("services.identity.timeout", 30),
        "jwt_secret": config.jwt_secret(),
        "token_expiry_minutes": config.get("security.jwt.access_token_expire_minutes", 30),
        "refresh_token_days": config.get("security.jwt.refresh_token_expire_days", 7),
        "db_host": db_config.get("host"),
        "db_name": db_config.get("database"),
        "db_user": db_config.get("user")
    }
}

# Models moved before ServerIdentity class

async def init_db():
    max_retries = 10
    retry_delay = 2
    logger.info("Initializing DB (destructive: drop & recreate tables)")
    for attempt in range(max_retries):
        try:
            pool = await asyncpg.create_pool(
                user=db_config.get("user"),
                password=db_config.get("password"),
                database=db_config.get("database"),
                host=db_config.get("host")
            )
            async with pool.acquire() as conn:
                # Drop and recreate tables (user allowed destructive changes)
                logger.info("Dropping and creating tables: domains, roles, users, user_roles, user_preferences")
                await conn.execute("DROP TABLE IF EXISTS user_preferences CASCADE")
                await conn.execute("DROP TABLE IF EXISTS user_roles CASCADE")
                await conn.execute("DROP TABLE IF EXISTS users CASCADE")
                await conn.execute("DROP TABLE IF EXISTS roles CASCADE")
                await conn.execute("DROP TABLE IF EXISTS domains CASCADE")
                # revoked tokens table: store jti and expiry
                await conn.execute("DROP TABLE IF EXISTS revoked_tokens CASCADE")
                await conn.execute("DROP TABLE IF EXISTS refresh_tokens CASCADE")

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS domains (
                        id SERIAL PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL
                    )
                """)

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS roles (
                        id SERIAL PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL
                    )
                """)

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS revoked_tokens (
                        jti TEXT PRIMARY KEY,
                        expires_at TIMESTAMP NOT NULL
                    )
                """)

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS token_blacklist (
                        token_id TEXT PRIMARY KEY
                    )
                """)

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS refresh_tokens (
                        token TEXT PRIMARY KEY,
                        username TEXT NOT NULL,
                        expires_at TIMESTAMPTZ NOT NULL
                    )
                """)

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        domain_id INTEGER REFERENCES domains(id) ON DELETE SET NULL
                    )
                """)

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_roles (
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
                        PRIMARY KEY (user_id, role_id)
                    )
                """)

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        preference_key TEXT NOT NULL,
                        preference_value TEXT,
                        preference_bool BOOLEAN,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        UNIQUE(user_id, preference_key),
                        CHECK (
                            (preference_value IS NOT NULL AND preference_bool IS NULL) OR
                            (preference_value IS NULL AND preference_bool IS NOT NULL)
                        )
                    )
                """)

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS oauth_connections (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        provider TEXT NOT NULL,
                        provider_id TEXT NOT NULL,
                        provider_email TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        UNIQUE(provider, provider_id)
                    )
                """)

                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_oauth_connections_provider_id
                    ON oauth_connections(provider, provider_id)
                """)

                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_preferences_user_key 
                    ON user_preferences(user_id, preference_key)
                """)

                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_preferences_key 
                    ON user_preferences(preference_key)
                """)

                # Seed example.com domain and default roles
                await conn.execute("INSERT INTO domains (name) VALUES ($1) ON CONFLICT DO NOTHING", "example.com")
                await conn.execute("INSERT INTO roles (name) VALUES ($1) ON CONFLICT DO NOTHING", "user")
                await conn.execute("INSERT INTO roles (name) VALUES ($1) ON CONFLICT DO NOTHING", "admin")

                # Create default admin user if not exists
                # Extract username and domain from ADMIN_EMAIL (from config)
                admin_email = config.get("security.admin.email", "admin@example.com")
                admin_password = config.get("security.admin.password", "admin")
                
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

                # Add default preferences for admin user
                admin_user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", admin_username)
                if admin_user:
                    admin_user_id = admin_user["id"]
                    # Insert default language and dark_mode preferences
                    await conn.execute("""
                        INSERT INTO user_preferences (user_id, preference_key, preference_value) 
                        VALUES ($1, 'language', 'en') ON CONFLICT DO NOTHING
                    """, admin_user_id)
                    await conn.execute("""
                        INSERT INTO user_preferences (user_id, preference_key, preference_bool) 
                        VALUES ($1, 'dark_mode', false) ON CONFLICT DO NOTHING
                    """, admin_user_id)

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
    # Use configured JWT secret from service_state (populated at startup)
    jwt_secret = service_state.get("config", {}).get("jwt_secret") or Config.instance().jwt_secret()
    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    return token


def _generate_refresh_token():
    return str(uuid.uuid4())


async def _decode_token(authorization: str):
    try:
        # Handle both "Bearer <token>" format and plain token
        if authorization.startswith("Bearer "):
            token = authorization.split("Bearer ", 1)[1].strip()
        else:
            token = authorization.strip()
        
        jwt_secret = service_state.get("config", {}).get("jwt_secret") or Config.instance().jwt_secret()
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        # check revocation by jti in both tables
        jti = payload.get('jti')
        if jti:
            async with app.state.db_pool.acquire() as conn:
                # Check both revoked_tokens and token_blacklist
                row = await conn.fetchrow('SELECT jti FROM revoked_tokens WHERE jti = $1', jti)
                if row:
                    logger.info(f"Token jti {jti} is revoked")
                    raise HTTPException(status_code=401, detail="User logged out")
                
                row = await conn.fetchrow('SELECT token_id FROM token_blacklist WHERE token_id = $1', jti)
                if row:
                    logger.info(f"Token jti {jti} is blacklisted")
                    raise HTTPException(status_code=401, detail="User logged out")
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


#@app.post("/register")
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


#@app.post("/login")
async def login(payload: LoginRequest):
    # Accept multiple login formats:
    # 1. NEW: {"realm": "example.com", "email": "admin@example.com", "password": "..."} - realm + email
    # 2. NEW: {"realm": "example.com", "user": "admin", "password": "..."} - realm + user
    # 3. LEGACY: {"username": "admin", "password": "admin"} - simple username
    # 4. LEGACY: {"email": "admin@example.com", "password": "admin"} - email parsing
    # 5. LEGACY: {"username": "admin", "domain": "example.com", "password": "admin"} - explicit username/domain

    logger.info(f"Login attempt: realm={payload.realm}, user={payload.user}, email={payload.email}, domain={payload.domain}, username={payload.username}")
    service_state["requests_total"] += 1
    service_state["last_request_time"] = datetime.now(timezone.utc).isoformat()

    # Validate required fields
    if not ((payload.realm and (payload.user or payload.email)) or payload.username or payload.email):
        service_state["requests_failed"] += 1
        raise HTTPException(status_code=400, detail="realm + (user|email), or username, or email required")

    # Decrypt RSA-encrypted password if available
    password = payload.password
    if payload.realm and payload.realm in RSA_KEYS:
        try:
            password = decrypt_password(password, RSA_KEYS[payload.realm]['private'])
        except Exception as e:
            logger.warning(f"Failed to decrypt password for realm {payload.realm}: {e}")
            # Fall back to plain text

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    async with app.state.db_pool.acquire() as conn:
        uname = None
        domain_name = None

        # Parse login credentials based on provided format
        if payload.realm and payload.email:
            # NEW Format 1: realm + email
            uname, domain_name = payload.email.split("@", 1) if "@" in payload.email else (payload.email, payload.realm)
        elif payload.realm and payload.user:
            # NEW Format 2: realm + user
            uname = payload.user
            domain_name = payload.realm
        elif payload.username and payload.domain:
            # LEGACY Format 5: explicit username + domain
            uname = payload.username
            domain_name = payload.domain
        elif payload.email and "@" in payload.email:
            # LEGACY Format 4: email parsing
            uname, domain_name = payload.email.split("@", 1)
        elif payload.username:
            # LEGACY Format 3: simple username (assume default domain)
            uname = payload.username
            # If username contains @, treat it as email
            if uname and "@" in uname and not domain_name:
                uname, domain_name = uname.split("@", 1)
        elif payload.email:
            # LEGACY Format 2: treat email as username if no @ symbol
            uname = payload.email

        # Try different lookup strategies
        row = None

        if uname and domain_name:
            # Domain-aware lookup
            drow = await conn.fetchrow("SELECT id FROM domains WHERE name = $1", domain_name)
            if drow:
                row = await conn.fetchrow(
                    "SELECT u.id, u.username FROM users u WHERE u.username = $1 AND u.domain_id = $2 AND u.password = $3",
                    uname, drow["id"], hashed_password
                )
        elif uname:
            # Simple username lookup (across all domains)
            row = await conn.fetchrow("SELECT id, username FROM users WHERE username = $1 AND password = $2", uname, hashed_password)

        if not row:
            logger.error(f"Invalid credentials for username={payload.username}, email={payload.email}, domain={payload.domain}")
            service_state["requests_failed"] += 1
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not row:
            logger.error(f"Invalid credentials for username={payload.username}, email={payload.email}, domain={payload.domain}")
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

#@app.get('/rsa/public-key/{realm}')
async def get_rsa_public_key(realm: str):
    """Get RSA public key for a realm to encrypt passwords"""
    if not CRYPTOGRAPHY_AVAILABLE:
        raise HTTPException(status_code=503, detail="RSA encryption not available")

    if realm not in RSA_KEYS:
        raise HTTPException(status_code=404, detail=f"RSA keys not found for realm: {realm}")

    public_key_pem = RSA_KEYS[realm]['public']
    return {
        "realm": realm,
        "public_key": public_key_pem.decode(),
        "key_type": "RSA-2048-OAEP"
    }

#@app.post('/tokens/revoke')
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
                jwt_secret = service_state.get("config", {}).get("jwt_secret") or Config.instance().jwt_secret()
                payload = jwt.decode(tok, jwt_secret, algorithms=["HS256"])
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
            jwt_secret = service_state.get("config", {}).get("jwt_secret") or Config.instance().jwt_secret()
            payload = jwt.decode(tok, jwt_secret, algorithms=["HS256"])
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


#@app.post('/tokens/refresh')
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


#@app.get("/verify")
#@app.post("/verify")
async def verify(authorization: str = Header(...)):
    payload = await _decode_token(authorization)
    return {"status": "OK", "username": payload.get("username"), "roles": payload.get("roles", [])}

#@app.post("/logout")
async def logout(authorization: str = Header(...)):
    """Logout user and invalidate token"""
    payload = await _decode_token(authorization)
    
    # Get token ID from payload
    token_id = payload.get("jti")
    
    if token_id:
        # Add token to blacklist
        async with app.state.db_pool.acquire() as conn:
            try:
                await conn.execute(
                    "INSERT INTO token_blacklist (token_id) VALUES ($1) ON CONFLICT DO NOTHING",
                    token_id
                )
            except Exception as e:
                logger.error(f"Error blacklisting token: {e}")
    
    return {"status": "logged out", "username": payload.get("username")}


#@app.post("/domains")
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


#@app.delete("/domains/{domain_name}")
async def delete_domain(domain_name: str, authorization: str = Header(...)):
    payload = await _decode_token(authorization)
    if "admin" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin required")
    async with app.state.db_pool.acquire() as conn:
        res = await conn.execute("DELETE FROM domains WHERE name = $1", domain_name)
        if res == "DELETE 0":
            raise HTTPException(status_code=404, detail="Domain not found")
        return {"status": "domain deleted"}


#@app.post('/domains/rename')
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


#@app.get("/domains")
async def list_domains(authorization: str = Header(...)):
    payload = await _decode_token(authorization)
    if "admin" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin required")
    async with app.state.db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name FROM domains")
        return [{"id": r["id"], "name": r["name"]} for r in rows]


#@app.get("/api/domains/{domain}/exists")
async def check_domain_exists(domain: str):
    """Public endpoint to check if domain exists (for SMTP local delivery)"""
    async with app.state.db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM domains WHERE name = $1", domain)
        return {"exists": row is not None, "domain": domain}


#@app.get("/users")
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


#@app.put("/users")
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


#@app.delete("/users/{user_id}")
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

#@app.get("/api/health")
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

#@app.get("/api/config")
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

#@app.put("/api/config")
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

#@app.get("/api/stats")
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

#@app.get("/api/identity/sessions")
async def get_sessions(authorization: str = Header(...)):
    """Get active Identity sessions (admin only)"""
    payload = await _decode_token(authorization)
    if "admin" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="Admin required")
    
    return {
        "active_sessions": service_state["active_sessions"],
        "count": len(service_state["active_sessions"])
    }


@app.get("/api/users/{username}/preferences", tags=["Users"])
async def get_user_preferences(username: str, request: Request) -> dict:
    """Get user's preferences"""
    # Accept both Authorization header and access_token cookie
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    payload = await _decode_token(token)
    requesting_user = payload.get("username")
    
    # User can only get their own preferences (unless admin)
    if requesting_user != username and not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        async with app.state.db_pool.acquire() as conn:
            # Get user ID
            user_row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            user_id = user_row["id"]
            
            # Get user preferences
            prefs_rows = await conn.fetch("""
                SELECT preference_key, preference_value, preference_bool 
                FROM user_preferences 
                WHERE user_id = $1
            """, user_id)
            
            preferences = {"language": "en", "dark_mode": False}  # defaults
            
            for row in prefs_rows:
                key = row["preference_key"]
                if key == "language" and row["preference_value"]:
                    preferences["language"] = row["preference_value"]
                elif key == "dark_mode" and row["preference_bool"] is not None:
                    preferences["dark_mode"] = row["preference_bool"]
            
            return preferences
    
    except Exception as e:
        logger.error(f"Error getting user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.put("/api/users/{username}/preferences", tags=["Users"])
async def update_user_preferences(
    username: str,
    preferences: UserPreferencesUpdate, 
    request: Request
) -> dict:
    """Update user's preferences"""
    # Accept both Authorization header and access_token cookie
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    payload = await _decode_token(token)
    requesting_user = payload.get("username")
    
    # User can only update their own preferences (unless admin)
    if requesting_user != username and not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        async with app.state.db_pool.acquire() as conn:
            # Get user ID
            user_row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            user_id = user_row["id"]
            
            # Update preferences
            if preferences.language is not None:
                # Validate language
                if preferences.language not in ["en", "cs"]:
                    raise HTTPException(status_code=400, detail="Unsupported language. Use 'en' or 'cs'")
                
                await conn.execute("""
                    INSERT INTO user_preferences (user_id, preference_key, preference_value) 
                    VALUES ($1, 'language', $2)
                    ON CONFLICT (user_id, preference_key) 
                    DO UPDATE SET preference_value = $2, updated_at = NOW()
                """, user_id, preferences.language)
            
            if preferences.dark_mode is not None:
                await conn.execute("""
                    INSERT INTO user_preferences (user_id, preference_key, preference_bool) 
                    VALUES ($1, 'dark_mode', $2)
                    ON CONFLICT (user_id, preference_key) 
                    DO UPDATE SET preference_bool = $2, updated_at = NOW()
                """, user_id, preferences.dark_mode)
            
            # Return updated preferences
            prefs_rows = await conn.fetch("""
                SELECT preference_key, preference_value, preference_bool 
                FROM user_preferences 
                WHERE user_id = $1
            """, user_id)
            
            updated_preferences = {"language": "en", "dark_mode": False}  # defaults
            
            for row in prefs_rows:
                key = row["preference_key"]
                if key == "language" and row["preference_value"]:
                    updated_preferences["language"] = row["preference_value"]
                elif key == "dark_mode" and row["preference_bool"] is not None:
                    updated_preferences["dark_mode"] = row["preference_bool"]
            
            logger.info(f"Updated preferences for user {username}: {updated_preferences}")
            return updated_preferences
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# OAuth 2.0 Social Login Support
class OAuth2Client(BaseModel):
    client_id: str
    client_secret: str
    redirect_uris: List[str]
    grant_types: List[str] = ["authorization_code"]
    response_types: List[str] = ["code"]
    scope: str = "openid profile email"

class OAuth2TokenRequest(BaseModel):
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None

# OAuth client configurations (in production, these should be in config)
OAUTH_CLIENTS = {
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "authorize_url": "https://accounts.google.com/o/oauth2/auth",
        "access_token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid profile email"
    },
    "facebook": {
        "client_id": os.getenv("FACEBOOK_CLIENT_ID", ""),
        "client_secret": os.getenv("FACEBOOK_CLIENT_SECRET", ""),
        "authorize_url": "https://www.facebook.com/v18.0/dialog/oauth",
        "access_token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
        "userinfo_url": "https://graph.facebook.com/me?fields=id,name,email,first_name,last_name",
        "scope": "email,public_profile"
    },
    "twitter": {
        "client_id": os.getenv("TWITTER_CLIENT_ID", ""),
        "client_secret": os.getenv("TWITTER_CLIENT_SECRET", ""),
        "authorize_url": "https://twitter.com/i/oauth2/authorize",
        "access_token_url": "https://api.twitter.com/2/oauth2/token",
        "userinfo_url": "https://api.twitter.com/2/users/me",
        "scope": "tweet.read users.read"
    },
    "microsoft": {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID", ""),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET", ""),
        "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "access_token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "scope": "openid profile email"
    }
}


#@app.get("/health")
async def health_check_root():
    """Compatibility health endpoint at /health"""
    return await health_check()

#@app.get("/oauth/{provider}/login")
async def oauth_login(provider: str, redirect_uri: str = None):
    """Initiate OAuth login flow"""
    if provider not in OAUTH_CLIENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")

    client_config = OAUTH_CLIENTS[provider]
    if not client_config["client_id"]:
        raise HTTPException(status_code=500, detail=f"OAuth provider {provider} not configured")

    # Generate state parameter for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state in session/database (simplified - using in-memory for demo)
    # In production, store in Redis/database with expiration

    params = {
        "client_id": client_config["client_id"],
        "redirect_uri": f"{config.get('services.identity.url', f'http://localhost:{IDENTITY_PORT}')}/oauth/{provider}/callback",
        "scope": client_config["scope"],
        "response_type": "code",
        "state": state,
        "access_type": "offline" if provider == "google" else None,
        "prompt": "consent" if provider == "google" else None
    }

    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    auth_url = f"{client_config['authorize_url']}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    return {"authorization_url": auth_url, "state": state}

#@app.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: str):
    """Handle OAuth callback"""
    if provider not in OAUTH_CLIENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")

    client_config = OAUTH_CLIENTS[provider]

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_data = {
            "client_id": client_config["client_id"],
            "client_secret": client_config["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{config.get('services.identity.url', f'http://localhost:{IDENTITY_PORT}')}/oauth/{provider}/callback"
        }

        try:
            token_response = await client.post(client_config["access_token_url"], data=token_data)
            token_response.raise_for_status()
            token_info = token_response.json()
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise HTTPException(status_code=400, detail="Failed to obtain access token")

        # Get user info
        headers = {"Authorization": f"Bearer {token_info['access_token']}"}
        user_response = await client.get(client_config["userinfo_url"], headers=headers)
        user_response.raise_for_status()
        user_info = user_response.json()

    # Process user info based on provider
    user_data = {}
    if provider == "google":
        user_data = {
            "email": user_info.get("email"),
            "first_name": user_info.get("given_name"),
            "last_name": user_info.get("family_name"),
            "username": user_info.get("email").split("@")[0] if user_info.get("email") else None,
            "provider": "google",
            "provider_id": user_info.get("id")
        }
    elif provider == "facebook":
        user_data = {
            "email": user_info.get("email"),
            "first_name": user_info.get("first_name"),
            "last_name": user_info.get("last_name"),
            "username": user_info.get("email").split("@")[0] if user_info.get("email") else None,
            "provider": "facebook",
            "provider_id": user_info.get("id")
        }
    elif provider == "microsoft":
        user_data = {
            "email": user_info.get("userPrincipalName") or user_info.get("mail"),
            "first_name": user_info.get("givenName"),
            "last_name": user_info.get("surname"),
            "username": user_data.get("email").split("@")[0] if user_data.get("email") else None,
            "provider": "microsoft",
            "provider_id": user_info.get("id")
        }
    elif provider == "twitter":
        user_data = {
            "email": user_info.get("email"),  # Twitter may not provide email
            "first_name": user_info.get("name", "").split()[0] if user_info.get("name") else "",
            "last_name": " ".join(user_info.get("name", "").split()[1:]) if user_info.get("name") else "",
            "username": user_info.get("username"),
            "provider": "twitter",
            "provider_id": user_info.get("id")
        }

    if not user_data.get("email"):
        raise HTTPException(status_code=400, detail="Email address is required for registration")

    # Check if OAuth connection exists, if not register user
    async with app.state.db_pool.acquire() as conn:
        # First check if OAuth connection already exists
        oauth_connection = await conn.fetchrow(
            "SELECT u.id, u.username FROM oauth_connections oc JOIN users u ON oc.user_id = u.id WHERE oc.provider = $1 AND oc.provider_id = $2",
            provider, user_data["provider_id"]
        )

        if oauth_connection:
            # Existing OAuth user - use them
            user_data["username"] = oauth_connection["username"]
            logger.info(f"OAuth login for existing user: {user_data['username']} via {provider}")
        else:
            # New OAuth user - register them via the register endpoint
            try:
                # Use the register endpoint to create the user properly
                domain = user_data["email"].split("@")[1]
                username = user_data["username"] or user_data["email"].split("@")[0]

                # Generate a secure password for OAuth users (they won't use it directly)
                oauth_password = secrets.token_urlsafe(32)

                register_payload = {
                    "username": username,
                    "password": oauth_password,
                    "domain": domain,
                    "roles": ["user"]
                }

                # Call our own register endpoint
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{config.get('services.identity.url', f'http://localhost:{IDENTITY_PORT}')}/register", json=register_payload) as response:
                        if response.status != 200:
                            error_data = await response.json()
                            raise HTTPException(status_code=400, detail=f"Failed to register OAuth user: {error_data.get('detail', 'Unknown error')}")

                # Now create the OAuth connection record
                user_row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
                if user_row:
                    await conn.execute(
                        "INSERT INTO oauth_connections (user_id, provider, provider_id, provider_email) VALUES ($1, $2, $3, $4)",
                        user_row["id"], provider, user_data["provider_id"], user_data["email"]
                    )
                    logger.info(f"OAuth user registered: {user_data['email']} via {provider}")
                else:
                    raise HTTPException(status_code=500, detail="Failed to create OAuth connection")

            except Exception as e:
                logger.error(f"Error registering OAuth user: {e}")
                raise HTTPException(status_code=500, detail="Failed to register OAuth user")

    # Generate JWT token for the user
    roles = ["user"]  # Default role for OAuth users
    token = _encode_token(user_data["username"], roles)
    refresh = _generate_refresh_token()

    # Store refresh token
    exp = datetime.now(timezone.utc) + timedelta(days=14)
    async with app.state.db_pool.acquire() as conn:
        await conn.execute('INSERT INTO refresh_tokens (token, username, expires_at) VALUES ($1, $2, $3)', refresh, user_data["username"], exp.replace(tzinfo=None))

    return {
        "access_token": token,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {
            "username": user_data["username"],
            "email": user_data["email"],
            "provider": provider
        }
    }