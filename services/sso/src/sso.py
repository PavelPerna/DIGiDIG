import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from digidig.models.service.client import ServiceClient
from digidig.language import I18n
from digidig.config import Config
from fastapi import Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
import httpx

# SSO service configuration - handles login and redirects to apps
config = Config.instance()
SSO_PORT = int(config.get('services.sso.http_port', 9106))
HOST = config.get('services.sso.external_url', 'localhost')
# External URL for user display in templates
IDENTITY_URL = config.service_url('identity', ssl=True)


async def check_session(request: Request):
    """Check if user has valid session, return user info or None"""
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        return None
    
    try:
        # Use proxy endpoint - call ourselves, ServiceClient routes to identity
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:{SSO_PORT}/api/identity/session/verify",
                cookies={"access_token": access_token}
            )
            if response.status_code == 200:
                user_info = response.json()
                return user_info if user_info else None
            return None
    except Exception as e:
        return None


async def get_user_preferences(username: str, access_token: str):
    """Get user preferences from identity service"""
    try:
        # Use proxy endpoint - call ourselves, ServiceClient routes to identity
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:{SSO_PORT}/api/identity/users/{username}/preferences",
                cookies={"access_token": access_token}
            )
            if response.status_code == 200:
                prefs = response.json()
                return prefs
            else:
                return {"language": "en", "dark_mode": False}  # defaults
    except Exception as e:
        return {"language": "en", "dark_mode": False}  # defaults


async def get_i18n_for_user(request: Request, user_info=None):
    """Get i18n instance for user based on their language preference"""
    # For SSO, we don't have authenticated user yet, so check if there's a session
    if not user_info:
        user_info = await check_session(request)
    
    if not user_info or not user_info.get("username"):
        # No user or no username - use default English
        return I18n("en"), False  # Return tuple: (i18n, dark_mode)
    
    username = user_info["username"]
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        return I18n("en"), False  # Return tuple: (i18n, dark_mode)
    
    try:
        # Get preferences asynchronously
        prefs = await get_user_preferences(username, access_token)
        language = prefs.get("language", "en")
        dark_mode = prefs.get("dark_mode", False)
        return I18n(language), dark_mode
    except Exception as e:
        return I18n("en"), False  # Return tuple: (i18n, dark_mode)


class ClientSSO(ServiceClient):
    def __init__(self):
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        super().__init__(
            name='sso',
            description='SSO Client App',
            port=SSO_PORT,
            mount_lib=True,
            static_dir=static_dir,
            templates_dir=templates_dir
        )
        self.register_routes()

    def register_routes(self):
        @self.app.get('/health')
        async def health():
            return {'service': 'sso', 'status': 'healthy', 'port': SSO_PORT}

        @self.app.get('/')
        async def login_page(request: Request):
            """Serve login page with app parameter to know where to redirect after login"""
            app_name = request.query_params.get('app', 'client')  # Default to client app
            error_msg = request.query_params.get('error', '')
            
            # Get i18n and dark_mode for user (if logged in)
            i18n, dark_mode = await get_i18n_for_user(request)
            
            return self.templates.TemplateResponse('login.html', {
                'request': request,
                'app_name': app_name,
                'error': error_msg,
                'identity_url': IDENTITY_URL,
                'i18n': i18n,
                'dark_mode': dark_mode
            })

        @self.app.post('/login')
        async def handle_login(request: Request, email: str = Form(...), password: str = Form(...)):
            """Handle login form submission, authenticate via Identity, redirect to app"""
            app_name = request.query_params.get('app', 'client')
            
            # Authenticate via Identity service using proxy
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"http://localhost:{SSO_PORT}/api/identity/login",
                        json={"email": email, "password": password}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        access_token = data.get('access_token')
                        
                        # Get app home URL from config
                        app_url = config.service_url(app_name, ssl=True)
                        
                        # Create redirect response and set cookie
                        redirect_response = RedirectResponse(url=app_url, status_code=303)
                        redirect_response.set_cookie(
                            key="access_token",
                            value=access_token,
                            httponly=True,
                            samesite="lax",
                            path="/"
                        )
                        
                        return redirect_response
                    else:
                        # Login failed - redirect back to login with error
                        error_data = response.json()
                        error_msg = error_data.get('detail', 'Authentication failed')
                        return RedirectResponse(
                            url=f"/?app={app_name}&error={error_msg}",
                            status_code=303
                        )
                except Exception as e:
                    # Network or other error
                    return RedirectResponse(
                        url=f"/?app={app_name}&error=Connection error: {str(e)}",
                        status_code=303
                    )


client = ClientSSO()
app = client.get_app()
templates = client.templates


if __name__ == '__main__':
    import uvicorn

    # Check for SSL certificates
    hostname = config.get('hostname') or os.getenv('HOSTNAME') or 'localhost'
    ssl_cert = f'/app/ssl/{hostname}.pem'
    ssl_key = f'/app/ssl/{hostname}-key.pem'

    if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        print(f"Starting SSO service with SSL on 0.0.0.0:{SSO_PORT}")
        uvicorn.run(app, host='0.0.0.0', port=SSO_PORT, ssl_certfile=ssl_cert, ssl_keyfile=ssl_key)
    else:
        print(f"Starting SSO service without SSL on 0.0.0.0:{SSO_PORT} (SSL certificates not found)")
        uvicorn.run(app, host='0.0.0.0', port=SSO_PORT)