# GitHub Copilot Instructions for DIGiDIG Project

## ⚠️ CRITICAL RULES - READ FIRST EVERY TIME ⚠️

### 🚨 ABSOLUTE REQUIREMENTS - NEVER VIOLATE THESE:

1. **ALWAYS USE .venv - NEVER SYSTEM PYTHON**
   - ❌ FORBIDDEN: Running any Python command without `.venv` active
   - ❌ FORBIDDEN: Using `python3` or `pip` directly
   - ✅ REQUIRED: Use `.venv/bin/python` and `.venv/bin/pip` explicitly
   - ✅ REQUIRED: Check terminal has `(.venv)` in prompt before running commands
   - ✅ REQUIRED: If terminal lacks .venv, activate it first: `source .venv/bin/activate`

2. **NEVER RUN COMMANDS DIRECTLY ON USER'S MACHINE**
   - ❌ FORBIDDEN: `sudo apt-get install`, `certbot`, manual Docker commands
   - ❌ FORBIDDEN: Any system-level changes outside Makefile
   - ✅ REQUIRED: ALL operations must be in Makefile targets
   - ✅ REQUIRED: Use `make <target>` for all operations
   - ✅ REQUIRED: If functionality doesn't exist in Makefile, ADD IT TO MAKEFILE FIRST

3. **ALWAYS VERIFY YOUR CHANGES IMMEDIATELY**
   - ❌ FORBIDDEN: Making changes without testing them
   - ❌ FORBIDDEN: Assuming something works without verification
   - ✅ REQUIRED: After ANY change, run `make install` or appropriate make target
   - ✅ REQUIRED: Check logs/output to confirm changes work
   - ✅ REQUIRED: Test the feature you just implemented

4. **LET'S ENCRYPT IS PRIORITY - NOT SELF-SIGNED**
   - ❌ FORBIDDEN: Defaulting to self-signed certificates
   - ❌ FORBIDDEN: Ignoring user's repeated requests for Let's Encrypt
   - ✅ REQUIRED: Always attempt Let's Encrypt FIRST in `make install`
   - ✅ REQUIRED: Self-signed is ONLY fallback when Let's Encrypt fails
   - ✅ REQUIRED: Clearly report WHY Let's Encrypt failed if it does

5. **ALWAYS USE CORRECT HOSTNAMES FROM CONFIG**
   - ❌ FORBIDDEN: Hardcoding `localhost` or IP addresses
   - ❌ FORBIDDEN: Ignoring hostname in config.yaml or .env
   - ✅ REQUIRED: Read hostname from config.yaml `external_url` or .env `HOSTNAME`
   - ✅ REQUIRED: Use config values in URLs, not assumptions

6. **COMMUNICATE CLEARLY AND VERIFY UNDERSTANDING**
   - ❌ FORBIDDEN: Making assumptions about what user wants
   - ❌ FORBIDDEN: Repeating same mistakes after correction
   - ✅ REQUIRED: If uncertain, ask clarifying questions
   - ✅ REQUIRED: Acknowledge when you've made an error
   - ✅ REQUIRED: Learn from corrections and don't repeat them

7. **CLIENT SERVICES ARCHITECTURE - UNIFIED API PROXY**
   - ❌ FORBIDDEN: Adding business logic API endpoints to client services
   - ❌ FORBIDDEN: Hardcoding service URLs in JavaScript
   - ✅ REQUIRED: Client services (mail, admin, client, test-suite, apidocs, sso) serve HTML pages ONLY
   - ✅ REQUIRED: ServiceClient base class provides generic `/api/{service}/*` proxy endpoint
   - ✅ REQUIRED: Proxy routes `/api/smtp/*` → `smtp:9100/api/*`, `/api/identity/*` → `identity:9101/api/*`, etc.
   - ✅ REQUIRED: Proxy is needed because HttpOnly cookies don't work cross-origin
   - ✅ REQUIRED: JavaScript MUST call `/api/{service}/endpoint` (e.g., `/api/smtp/send`, `/api/identity/session/verify`)
   - ✅ REQUIRED: All server services use `api_version=None` for `/api/` prefix (not `/api/v1/`)
   - ✅ REQUIRED: All client services MUST have httpx in requirements.txt (for proxy)
   - ✅ REQUIRED: All server services (identity, smtp, storage, imap) MUST have httpx in requirements.txt

8. **MAKEFILE USAGE**
   - ✅ REQUIRED: Use `make refresh <service_name>` for single service rebuild (ONE service at a time)
   - ✅ REQUIRED: Use `make build` for all services rebuild
   - ✅ REQUIRED: Use `make install` for full setup
   - ✅ REQUIRED: Use `make up` to start services
   - ✅ REQUIRED: Docker cache can cause issues - requirements.txt changes need rebuild

9. **SERVICE CLASS-BASED ARCHITECTURE**
   - ❌ FORBIDDEN: Using `app = FastAPI()` directly in service files
   - ❌ FORBIDDEN: Defining routes with `@app.get/post/put/delete` in module scope
   - ✅ REQUIRED: All server services MUST inherit from `ServiceServer` class
   - ✅ REQUIRED: All client services MUST inherit from `ServiceClient` class
   - ✅ REQUIRED: Define routes in `register_routes(self)` method, using `@self.app.get/post/put/delete`
   - ✅ REQUIRED: Create instance: `service = ServerName()` then `app = service.get_app()`
   - ✅ REQUIRED: ServiceBase provides `/health` endpoint automatically (don't redefine unless needed)
   - ✅ REQUIRED: ServiceServer provides `/api/status` endpoint automatically
   - ✅ EXAMPLE:
     ```python
     class ServerSMTP(ServiceServer):
         def __init__(self):
             super().__init__(name='smtp', port=9100, api_version=None)
             self.register_routes()
         
         def register_routes(self):
             @self.app.post('/api/send')
             async def send(payload: dict):
                 return {'status': 'queued'}
     
     smtp_service = ServerSMTP()
     app = smtp_service.get_app()
     ```

### 📋 WORKFLOW CHECKLIST - FOLLOW FOR EVERY TASK:

1. ✅ Check terminal has `.venv` active (look for `(.venv)` in prompt)
2. ✅ Read config.yaml/.env for current settings (hostname, ports, etc.)
3. ✅ Plan changes in Makefile, NOT as direct commands
4. ✅ Make changes to code/config
5. ✅ Test changes with `make install` or appropriate target
6. ✅ Verify logs/output show success
7. ✅ Report results to user with evidence (logs, output)

---

For complete project documentation, see `.github/instructions.md`.
