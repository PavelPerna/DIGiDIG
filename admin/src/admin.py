import logging
from fastapi import FastAPI, Request, Form, HTTPException
from typing import Optional
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import json
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import aiohttp
from pydantic import BaseModel
import traceback
import subprocess

# Nastavení logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Admin Microservice")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # Log full traceback for debugging and return JSON error
    tb = traceback.format_exc()
    logger.error(f"Unhandled exception: {exc}\n{tb}")
    # If it's an HTTPException, prefer its status code and detail
    if isinstance(exc, HTTPException):
        detail = exc.detail if getattr(exc, 'detail', None) else str(exc)
        return format_identity_response(status=getattr(exc, 'status_code', None), body=detail)
    # Otherwise return a generic 500 but allow format_identity_response to normalize body
    return format_identity_response(status=500, body={"error": str(exc)})
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class AdminIdentityError(Exception):
    def __init__(self, status: int, body):
        self.status = status
        self.body = body
        super().__init__(f"{status}: {body}")


def format_identity_response(status: int = None, body=None):
    """Normalize identity responses: if body contains an explicit 'status' field, use it; otherwise use provided status.
    Body may be dict/list/str. Returns a JSONResponse with appropriate status code and JSON body.
    """
    # If body is a dict and contains numeric 'status', use it
    code = status or 200
    content = body if body is not None else {}
    if isinstance(content, dict) and 'status' in content:
        try:
            code_candidate = int(content.get('status'))
            code = code_candidate
        except Exception:
            pass
    # If body is a string, try to parse JSON
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
            content = parsed
        except Exception:
            content = {"error": content}
    return JSONResponse(status_code=code, content=content)

class User(BaseModel):
    username: str
    domain: str = None
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
        status = response.status
        # Try to parse JSON body if present, otherwise fall back to text or empty dict
        body = None
        try:
            # some successful responses (e.g. 204 No Content) have no JSON
            if status == 204:
                body = {}
            else:
                # attempt to parse JSON, if it fails we'll read text below
                body = await response.json()
        except Exception:
            try:
                text = await response.text()
                # use text if non-empty, otherwise empty dict
                body = text if text else {}
            except Exception:
                body = {}

        # Treat any 2xx status as success
        if 200 <= status < 300:
            return body

        # Non-2xx -> log and raise AdminIdentityError so callers can return proper status
        logger.error(f"Identity service error (status={status}, type={type(body)}): {body}")
        raise AdminIdentityError(status, body)

async def get_user(token: str):
    logger.info("Ověřování admin uživatele")
    try:
        async with aiohttp.ClientSession() as session:
            result = await identity_request(session, "GET", "/verify", token=token)
            # support both legacy 'role' string and new 'roles' list
            roles = result.get('roles') if isinstance(result.get('roles'), list) else ([result.get('role')] if result.get('role') else [])
            if 'admin' not in roles:
                logger.error(f"Uživatel {result.get('username')} nemá oprávnění přístupu")
                raise HTTPException(status_code=403, detail="Neautorizovaný přístup")
            return result
    except AdminIdentityError as e:
        logger.error(f"Identity error during verify: status={e.status} body={e.body}")
        # propagate identity error to callers so they can return the proper status
        raise
    except Exception as e:
        logger.error(f"Chyba při ověřování admin uživatele: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Neplatný token: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, token: str = None):
    logger.info("Načítání admin dashboardu")
    # prefer cookie-based access_token if present
    if not token:
        token = request.cookies.get('access_token')
    if not token:
        logger.info("Žádný token, přesměrování na login")
        return templates.TemplateResponse("login.html", {"request": request})
    try:
        user = await get_user(token)
        logger.info(f"Admin {user.get('username') or user.get('email')} ověřen")
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
        # If identity indicated a logout (revoked token), show friendly logged-out message
        if isinstance(e, AdminIdentityError):
            try:
                body = e.body if e.body is not None else {}
                message = None
                if isinstance(body, dict) and body.get('detail'):
                    message = body.get('detail')
                elif isinstance(body, str):
                    message = body
                if message and 'logged out' in message.lower():
                    return templates.TemplateResponse("login.html", {"request": request, "error": "User logged out"})
            except Exception:
                pass
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Chyba: {str(e)}"
        })

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    # keep login form named 'email' for UX compatibility; identity accepts email or username
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
            
            # Redirect to dashboard with token in query string (avoid form resubmit on refresh)
            # If client expects JSON, return token JSON instead of redirect (useful for API clients)
            accept = request.headers.get("accept", "")
            if "application/json" in accept:
                # return JSON and set cookies for browser clients
                resp = JSONResponse(status_code=200, content={"access_token": token, "token_type": "bearer"})
                # set httpOnly cookies (short-lived access token and longer refresh token handled by identity if provided)
                resp.set_cookie('access_token', token, httponly=True, secure=False)
                return resp

            # set cookie and redirect
            resp = RedirectResponse(url=f"/?token={token}", status_code=303)
            resp.set_cookie('access_token', token, httponly=True, secure=False)
            return resp
    except Exception as e:
        # If this is an identity error, format and return its status/body for API clients
        if isinstance(e, AdminIdentityError):
            logger.info(f"Identity error during login: status={e.status} body={e.body}")
            # if client expects JSON, return JSONResponse with the identity status
            accept = request.headers.get("accept", "")
            if "application/json" in accept:
                return format_identity_response(status=e.status, body=e.body)
            # otherwise render login page with error
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": f"Chyba při přihlášení: {e.body}"
            })

        logger.error(f"Chyba při přihlášení admina {email}: {str(e)}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Chyba při přihlášení: {str(e)}"
        })


@app.post("/api/login")
async def api_login(request: Request):
    """Programmatic login that returns JSON (access_token) and propagates identity errors."""
    try:
        payload = await request.json()
    except Exception:
        return format_identity_response(status=400, body={"detail": "Invalid JSON payload"})

    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        return format_identity_response(status=400, body={"detail": "Missing email or password"})

    try:
        async with aiohttp.ClientSession() as session:
            result = await identity_request(
                session,
                "POST",
                "/login",
                {"email": email, "password": password, "role": "admin"}
            )
            token = result.get("access_token")
            refresh = result.get("refresh_token")
            if not token:
                return format_identity_response(status=500, body={"detail": "Identity did not return access_token"})
            resp = JSONResponse(status_code=200, content={"access_token": token, "token_type": "bearer"})
            # Set HttpOnly cookies for browser flows (secure flag false in dev; in prod set True)
            resp.set_cookie('access_token', token, httponly=True, secure=False)
            if refresh:
                resp.set_cookie('refresh_token', refresh, httponly=True, secure=False)
            return resp
    except AdminIdentityError as e:
        logger.info(f"Identity error during api login: status={e.status} body={e.body}")
        return format_identity_response(status=e.status, body=e.body)
    except Exception as e:
        logger.exception(f"Error during api login: {str(e)}")
        return format_identity_response(status=500, body={"detail": str(e)})

@app.post("/manage-user")
async def manage_user(
    request: Request,
    username: str = Form(...),
    domain: str = Form(None),
    role: str = Form(...),
    password: str = Form(None),
    originalUsername: str = Form(None),
    id: Optional[int] = Form(None),
    token: str = Form(None)
):
    operation = "update" if (originalUsername or id) else "create"
    target = originalUsername if originalUsername else username
    logger.info(f"{operation.capitalize()} uživatele: {target}")
    try:
        if not token:
            token = request.cookies.get('access_token')
        await get_user(token)
        async with aiohttp.ClientSession() as session:
            data = {
                # identity expects username + optional domain
                "username": username,
                "domain": domain,
                # send roles as list (identity expects roles array)
                "roles": [role],
            }
            if password:
                data["password"] = password
            # prefer numeric id when provided
            if id:
                data["id"] = int(id)
                endpoint = "/users"
                method = "PUT"
            elif originalUsername:
                data["original_username"] = originalUsername
                endpoint = "/users"
                method = "PUT"
            else:
                endpoint = "/register"
                method = "POST"

            result = await identity_request(session, method, endpoint, data, token)
            logger.info(f"Uživatel {target} úspěšně {operation}ován")
            return result
    except AdminIdentityError as e:
        logger.info(f"Identity error while managing user: status={e.status} body={e.body}")
        return format_identity_response(status=e.status, body=e.body)
    except HTTPException as e:
        # propagate HTTPExceptions (e.g. from get_user) back to client with normalized body
        logger.info(f"HTTP error while managing user: status={getattr(e,'status_code',None)} detail={e.detail}")
        return format_identity_response(status=getattr(e, 'status_code', None), body=e.detail)
    except Exception as e:
        logger.exception(f"Chyba při {operation} uživatele {target}: {str(e)}")
        # return normalized JSON response (allow identity-provided status if embedded)
        return format_identity_response(status=500, body={"error": str(e)})

@app.post("/manage-domain")
async def manage_domain(
    request: Request,
    name: str = Form(...),
    oldName: str = Form(None),
    token: str = Form(None)
):
    operation = "update" if oldName else "create"
    target_name = oldName if oldName else name
    logger.info(f"{operation.capitalize()} domény: {target_name}")
    try:
        if not token:
            token = request.cookies.get('access_token')
        await get_user(token)
        async with aiohttp.ClientSession() as session:
            data = {"name": name}
            if oldName:
                data["old_name"] = oldName
            
            if oldName:
                # call rename endpoint
                result = await identity_request(session, "POST", "/domains/rename", {"old_name": oldName, "name": name}, token)
            else:
                result = await identity_request(session, "POST", "/domains", data, token)
            logger.info(f"Doména {target_name} úspěšně {operation}ována")
            return result
    except AdminIdentityError as e:
        logger.info(f"Identity error while managing domain: status={e.status} body={e.body}")
        return format_identity_response(status=e.status, body=e.body)
    except HTTPException as e:
        logger.info(f"HTTP error while managing domain: status={getattr(e,'status_code',None)} detail={e.detail}")
        return format_identity_response(status=getattr(e, 'status_code', None), body=e.detail)
    except Exception as e:
        logger.exception(f"Chyba při {operation} domény {target_name}: {str(e)}")
        return format_identity_response(status=500, body={"error": str(e)})

@app.post("/delete-domain")
async def delete_domain(request: Request, domain_name: str = Form(...), token: str = Form(None)):
    logger.info(f"Odstraňování domény: {domain_name}")
    try:
        if not token:
            token = request.cookies.get('access_token')
        await get_user(token)
        async with aiohttp.ClientSession() as session:
            result = await identity_request(session, "DELETE", f"/domains/{domain_name}", token=token)
            logger.info(f"Doména {domain_name} úspěšně odstraněna")
            return result
    except AdminIdentityError as e:
        logger.info(f"Identity error while deleting domain: status={e.status} body={e.body}")
        return format_identity_response(status=e.status, body=e.body)
    except HTTPException as e:
        logger.info(f"HTTP error while deleting domain: status={getattr(e,'status_code',None)} detail={e.detail}")
        return format_identity_response(status=getattr(e, 'status_code', None), body=e.detail)
    except Exception as e:
        logger.exception(f"Chyba při odstraňování domény {domain_name}: {str(e)}")
        return format_identity_response(status=500, body={"error": str(e)})

@app.post("/delete-user")
async def delete_user(request: Request, username: str = Form(None), domain: str = Form(None), id: Optional[int] = Form(None), token: str = Form(None)):
    target = id if id else (f"{username}@{domain}" if username and domain else username)
    logger.info(f"Odstraňování uživatele: {target}")
    try:
        if not token:
            token = request.cookies.get('access_token')
        await get_user(token)
        async with aiohttp.ClientSession() as session:
            user_id = None
            # prefer explicit numeric id
            if id:
                user_id = int(id)
            elif username and str(username).isdigit():
                user_id = int(username)
            else:
                users = await identity_request(session, "GET", "/users", token=token)
                for u in users:
                    # match by username + domain if domain provided, otherwise by username
                    if domain:
                        if u.get('username') == username and u.get('domain') == domain:
                            user_id = u.get('id')
                            break
                    else:
                        if u.get('username') == username:
                            user_id = u.get('id')
                            break
            if not user_id:
                raise HTTPException(status_code=404, detail="User not found")
            result = await identity_request(session, "DELETE", f"/users/{user_id}", token=token)
            logger.info(f"Uživatel {target} úspěšně odstraněn")
            return result
    except AdminIdentityError as e:
        logger.info(f"Identity error while deleting user: status={e.status} body={e.body}")
        return format_identity_response(status=e.status, body=e.body)
    except HTTPException as e:
        logger.info(f"HTTP error while deleting user: status={getattr(e,'status_code',None)} detail={e.detail}")
        return format_identity_response(status=getattr(e, 'status_code', None), body=e.detail)
    except Exception as e:
        logger.exception(f"Chyba při odstraňování uživatele {target}: {str(e)}")
        return format_identity_response(status=500, body={"error": str(e)})


@app.post("/logout")
async def logout(request: Request):
    """Logout endpoint: clears token cookie (if any) and returns JSON.
    The admin service primarily uses tokens passed in query/form; this endpoint lets the UI notify the server
    and clear any cookie-based token if set by future changes.
    """
    try:
        # Try to revoke the token at identity service if we can find it
        token = None
        # Check cookies
        if request.cookies.get('access_token'):
            token = request.cookies.get('access_token')
        elif request.cookies.get('token'):
            token = request.cookies.get('token')

        # Check form or query for token (legacy flows)
        if not token:
            form = await request.form()
            token = form.get('token') or request.query_params.get('token')

        # if we found an access token, try to revoke it; also check refresh_token cookie for opaque token
        refresh_token = request.cookies.get('refresh_token')
        if token:
            # call identity revoke endpoint with the token in Authorization header
            async with aiohttp.ClientSession() as session:
                try:
                    await identity_request(session, 'POST', '/tokens/revoke', data=None, token=token)
                except AdminIdentityError as e:
                    # If identity returns non-2xx, still proceed to clear cookies but log
                    logger.info(f"Identity revoke returned non-2xx: {e.status} {e.body}")
                except Exception as e:
                    logger.exception(f"Error calling identity revoke: {str(e)}")
        # If there's a refresh token cookie, try to revoke that too (opaque token)
        if refresh_token:
            async with aiohttp.ClientSession() as session:
                try:
                    # send refresh token in JSON body
                    await identity_request(session, 'POST', '/tokens/revoke', data={'token': refresh_token})
                except AdminIdentityError as e:
                    logger.info(f"Identity revoke (refresh) returned non-2xx: {e.status} {e.body}")
                except Exception as e:
                    logger.exception(f"Error calling identity revoke for refresh token: {str(e)}")

        # Return JSON response and clear cookies
        resp = JSONResponse(status_code=200, content={"status": "logged_out"})
        resp.delete_cookie('token')
        resp.delete_cookie('access_token')
        return resp
    except Exception as e:
        logger.exception(f"Error during logout: {str(e)}")
        return format_identity_response(status=500, body={"error": str(e)})


# Service Management Endpoints

SERVICES = {
    "smtp": "http://smtp:8000",
    "imap": "http://imap:8003", 
    "storage": "http://storage:8002",
    "identity": "http://identity:8001"
}

@app.get("/services", response_class=HTMLResponse)
async def services_page(request: Request, token: str = None):
    """Service management page"""
    logger.info("Načítání stránky pro správu služeb")
    if not token:
        token = request.cookies.get('access_token')
    if not token:
        logger.info("Žádný token, přesměrování na login")
        return templates.TemplateResponse("login.html", {"request": request})
    
    try:
        user = await get_user(token)
        logger.info(f"Admin {user.get('username')} přistupuje ke správě služeb")
        
        # Get health status for all services
        services_status = {}
        async with aiohttp.ClientSession() as session:
            for service_name, service_url in SERVICES.items():
                try:
                    async with session.get(f"{service_url}/api/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            services_status[service_name] = await response.json()
                        else:
                            services_status[service_name] = {"status": "unhealthy", "service_name": service_name}
                except Exception as e:
                    logger.error(f"Chyba při získávání zdraví služby {service_name}: {str(e)}")
                    services_status[service_name] = {"status": "unreachable", "service_name": service_name, "error": str(e)}
        
        return templates.TemplateResponse("services.html", {
            "request": request,
            "token": token,
            "services": services_status
        })
    except Exception as e:
        logger.error(f"Chyba při načítání stránky služeb: {str(e)}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Chyba: {str(e)}"
        })

@app.get("/api/services/{service_name}/health")
async def get_service_health(service_name: str, token: str = None):
    """Get health status of a specific service"""
    if service_name not in SERVICES:
        return JSONResponse(status_code=404, content={"error": "Service not found"})
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SERVICES[service_name]}/api/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                return await response.json()
    except Exception as e:
        logger.error(f"Error getting health for {service_name}: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e), "status": "unreachable"})

@app.get("/api/services/{service_name}/stats")
async def get_service_stats(service_name: str, request: Request, token: str = None):
    """Get statistics of a specific service"""
    if not token:
        token = request.cookies.get('access_token')
    try:
        await get_user(token)
    except Exception as e:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    if service_name not in SERVICES:
        return JSONResponse(status_code=404, content={"error": "Service not found"})
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SERVICES[service_name]}/api/stats", timeout=aiohttp.ClientTimeout(total=5)) as response:
                return await response.json()
    except Exception as e:
        logger.error(f"Error getting stats for {service_name}: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/services/{service_name}/config")
async def get_service_config(service_name: str, request: Request, token: str = None):
    """Get configuration of a specific service"""
    if not token:
        token = request.cookies.get('access_token')
    try:
        await get_user(token)
    except Exception as e:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    if service_name not in SERVICES:
        return JSONResponse(status_code=404, content={"error": "Service not found"})
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SERVICES[service_name]}/api/config", timeout=aiohttp.ClientTimeout(total=5)) as response:
                return await response.json()
    except Exception as e:
        logger.error(f"Error getting config for {service_name}: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.put("/api/services/{service_name}/config")
async def update_service_config(service_name: str, request: Request, token: str = Form(None)):
    """Update configuration of a specific service"""
    if not token:
        token = request.cookies.get('access_token')
    try:
        await get_user(token)
    except Exception as e:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    if service_name not in SERVICES:
        return JSONResponse(status_code=404, content={"error": "Service not found"})
    
    try:
        config = await request.json()
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{SERVICES[service_name]}/api/config",
                json=config,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return await response.json()
    except Exception as e:
        logger.error(f"Error updating config for {service_name}: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/services/smtp/restart")
async def restart_smtp_service(request: Request, token: str = Form(None)):
    """Restart SMTP service"""
    if not token:
        token = request.cookies.get('access_token')
    try:
        await get_user(token)
    except Exception as e:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SERVICES['smtp']}/api/smtp/restart",
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                return await response.json()
    except Exception as e:
        logger.error(f"Error restarting SMTP: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/services/{service_name}/restart")
async def restart_service(service_name: str, request: Request, token: str = None):
    """Restart a specific service using docker compose - admin only"""
    if not token:
        token = request.cookies.get('access_token')
    
    # Verify user and check admin role
    try:
        user = await get_user(token)
        
        # Check if user has admin role
        roles = user.get("roles", [])
        if "admin" not in roles:
            logger.warning(f"Non-admin user {user.get('username')} attempted to restart service {service_name}")
            return JSONResponse(status_code=403, content={
                "error": "Forbidden",
                "message": "Admin role required to restart services"
            })
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    # List of valid services
    valid_services = ["identity", "smtp", "imap", "storage", "admin", "client", "postgres", "mongo"]
    
    if service_name not in valid_services:
        return JSONResponse(status_code=404, content={"error": f"Service '{service_name}' not found"})
    
    try:
        logger.info(f"Admin user {user.get('username')} restarting service: {service_name}")
        # Use docker compose restart command
        # docker-compose.yml is mounted at /app/project/
        result = subprocess.run(
            ["docker", "compose", "restart", service_name],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/app/project"  # Project root with docker-compose.yml
        )
        
        if result.returncode == 0:
            logger.info(f"Service {service_name} restarted successfully")
            return JSONResponse(status_code=200, content={
                "status": "success",
                "message": f"Service '{service_name}' restarted successfully",
                "output": result.stdout
            })
        else:
            logger.error(f"Failed to restart {service_name}: {result.stderr}")
            return JSONResponse(status_code=500, content={
                "status": "error",
                "message": f"Failed to restart service '{service_name}'",
                "error": result.stderr
            })
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout restarting {service_name}")
        return JSONResponse(status_code=504, content={
            "status": "error",
            "message": f"Restart timeout for service '{service_name}'"
        })
    except Exception as e:
        logger.error(f"Error restarting {service_name}: {str(e)}")
        return JSONResponse(status_code=500, content={
            "status": "error",
            "message": str(e)
        })