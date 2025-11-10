import os
import sys

# Ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from digidig.models.service.client import ServiceClient

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
        # Use proxy endpoint - call ourselves, ServiceClient routes to identity
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:{MAIL_PORT}/api/identity/session/verify",
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
                'i18n': {'get': lambda key, default: default}  # Simple i18n placeholder
            })
        
        @self.app.get("/compose", response_class=HTMLResponse)
        async def mail_compose(request: Request):
            # Check session
            user = await check_session(request)
            
            if not user:
                # Not authenticated - redirect to SSO
                return RedirectResponse(url=f"{SSO_URL}/?app=mail", status_code=303)
            
            # User is authenticated - show compose page
            return self.templates.TemplateResponse('layout.html', {
                'request': request,
                'title': 'Compose',
                'current_page': 'compose',
                'user_info': user,
                'identity_url': IDENTITY_URL,
                'service_urls': {
                    'identity': IDENTITY_URL,
                    'sso': SSO_URL,
                    'storage': STORAGE_URL,
                },
                'i18n': {'get': lambda key, default: default}  # Simple i18n placeholder
            })

client = ClientMail()
app = client.get_app()
templates = client.templates

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=MAIL_PORT)