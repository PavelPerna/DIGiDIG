import os
import sys

# Ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Try to import from digidig_core package first, fallback to local digidig
try:
    from digidig_core.service.client import ServiceClient
    from digidig_core.language import I18n
    from digidig_core.config import Config
except ImportError:
    # Fallback to local imports for backward compatibility
    from digidig.models.service.client import ServiceClient
    from digidig.language import I18n
    from digidig.config import Config
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request
import httpx

config = Config.instance()
MAIL_PORT = config.get('services.mail.http_port', 9107)
HOST = config.get('services.mail.external_url', 'localhost')
# External URLs for user-facing redirects (templates)
SSO_URL = config.service_url("sso", ssl=True)
IDENTITY_URL = config.service_url("identity", ssl=True)
STORAGE_URL = config.service_url("storage", ssl=True)


async def check_session(request: Request):
    """Check if user has valid session, return user info or None"""
    access_token = request.cookies.get("access_token")
    
    print(f"[DEBUG] check_session: access_token={'present' if access_token else 'missing'}")
    print(f"[DEBUG] All cookies: {dict(request.cookies)}")
    
    if not access_token:
        return None
    
    try:
        # Use internal service URL for identity service
        identity_url = config.service_internal_url('identity')
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{identity_url}/session/verify",
                cookies={"access_token": access_token}
            )
            print(f"[DEBUG] Identity response status: {response.status_code}")
            if response.status_code == 200:
                user_info = response.json()
                print(f"[DEBUG] User info: {user_info}")
                return user_info if user_info else None
            return None
    except Exception as e:
        print(f"[DEBUG] Session check error: {e}")
        return None


async def get_user_preferences(username: str, access_token: str):
    """Get user preferences from identity service"""
    try:
        # Use internal service URL for identity service
        identity_url = config.service_internal_url('identity')
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{identity_url}/users/{username}/preferences",
                cookies={"access_token": access_token}
            )
            if response.status_code == 200:
                prefs = response.json()
                print(f"[DEBUG] User preferences for {username}: {prefs}")
                return prefs
            else:
                print(f"[DEBUG] Failed to get preferences: {response.status_code} - {response.text}")
                return {"language": "en", "dark_mode": False}  # defaults
    except Exception as e:
        print(f"[DEBUG] Error getting preferences: {e}")
        return {"language": "en", "dark_mode": False}  # defaults


async def get_i18n_for_user(request: Request, user_info):
    """Get i18n instance for user based on their language preference"""
    if not user_info or not user_info.get("username"):
        # No user or no username - use default English
        return I18n("en"), False  # Return tuple: (i18n, dark_mode)
    
    username = user_info["username"]
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        print(f"[DEBUG] No access token for user {username}, using default i18n")
        return I18n("en"), False  # Return tuple: (i18n, dark_mode)
    
    try:
        # Get preferences asynchronously
        prefs = await get_user_preferences(username, access_token)
        language = prefs.get("language", "en")
        dark_mode = prefs.get("dark_mode", False)
        print(f"[DEBUG] Using language {language} and dark_mode {dark_mode} for user {username}")
        return I18n(language), dark_mode
    except Exception as e:
        print(f"[DEBUG] Error getting i18n for user: {e}")
        return I18n("en"), False  # Return tuple: (i18n, dark_mode)


class ClientMail(ServiceClient):
    def __init__(self):
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        super().__init__(
            name='mail',
            description='Mail client for DIGiDIG',
            port=MAIL_PORT,
            mount_lib=True,
            static_dir=static_dir,
            templates_dir=templates_dir
        )
        self.register_routes()

    def _add_client_endpoints(self):
        """Override to add proxy and other endpoints"""
        # Call parent to add proxy and other endpoints
        super()._add_client_endpoints()

    def register_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def mail_index(request: Request):
            # Redirect to /list
            return RedirectResponse(url="/list", status_code=303)
        
        @self.app.get("/list", response_class=HTMLResponse)
        async def mail_list(request: Request):
            # Check session
            user = await check_session(request)
            
            if not user:
                # Not authenticated - redirect to SSO
                return RedirectResponse(url=f"{SSO_URL}/?app=mail", status_code=303)
            
            # Get i18n and dark_mode for user
            i18n, dark_mode = await get_i18n_for_user(request, user)
            
            # User is authenticated - show inbox using layout
            return self.templates.TemplateResponse('layout.html', {
                'request': request,
                'title': 'Inbox',
                'current_page': 'list',
                'user_info': user,
                'identity_url': IDENTITY_URL,
                'service_urls': {
                    'identity': IDENTITY_URL,
                    'sso': SSO_URL,
                    'storage': STORAGE_URL,
                },
                'emails': [],  # Empty for now
                'i18n': i18n,
                'dark_mode': dark_mode
            })
        
        @self.app.get("/view/{email_id}", response_class=HTMLResponse)
        async def mail_view(request: Request, email_id: str):
            # Check session
            user = await check_session(request)
            
            if not user:
                # Not authenticated - redirect to SSO
                return RedirectResponse(url=f"{SSO_URL}/?app=mail", status_code=303)
            
            # Get i18n and dark_mode for user
            i18n, dark_mode = await get_i18n_for_user(request, user)
            
            # User is authenticated - show email view
            return self.templates.TemplateResponse('layout.html', {
                'request': request,
                'title': 'View Email',
                'current_page': 'view',
                'user_info': user,
                'identity_url': IDENTITY_URL,
                'service_urls': {
                    'identity': IDENTITY_URL,
                    'sso': SSO_URL,
                    'storage': STORAGE_URL,
                },
                'email_id': email_id,
                'i18n': i18n,
                'dark_mode': dark_mode
            })

        @self.app.get("/compose", response_class=HTMLResponse)
        async def mail_compose(request: Request):
            # Check session
            user = await check_session(request)
            
            if not user:
                # Not authenticated - redirect to SSO
                return RedirectResponse(url=f"{SSO_URL}/?app=mail", status_code=303)
            
            # Get i18n and dark_mode for user
            i18n, dark_mode = await get_i18n_for_user(request, user)
            
            # Parse query parameters for reply/forward
            reply_to = request.query_params.get('reply')
            forward_from = request.query_params.get('forward')
            
            # User is authenticated - show compose page
            return self.templates.TemplateResponse('layout.html', {
                'request': request,
                'title': 'Compose Email',
                'current_page': 'compose',
                'user_info': user,
                'identity_url': IDENTITY_URL,
                'service_urls': {
                    'identity': IDENTITY_URL,
                    'sso': SSO_URL,
                    'storage': STORAGE_URL,
                },
                'reply_to': reply_to,
                'forward_from': forward_from,
                'i18n': i18n,
                'dark_mode': dark_mode
            })

client = ClientMail()
app = client.get_app()
templates = client.templates


def main():
    """Main entry point for running the mail service"""
    import uvicorn
    
    logger = config.get_logger('mail')
    logger.info(f"Starting Mail Service on 0.0.0.0:{MAIL_PORT}")
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=MAIL_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()