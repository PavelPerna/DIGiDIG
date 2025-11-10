import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from digidig.models.service.client import ServiceClient
from digidig.config import get_config, get_service_url, get_service_internal_url
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request
import aiohttp

# Client implemented using ServiceClient pattern
config = get_config()
CLIENT_PORT = config.get('services.client.http_port', 9104)
HOST = config.get('services.client.external_url', 'localhost')
# Internal URLs for API calls (Docker network)
IDENTITY_INTERNAL_URL = get_service_internal_url('identity')
SSO_INTERNAL_URL = get_service_internal_url('sso')
# External URLs for redirects
IDENTITY_EXTERNAL_URL = get_service_url('identity', ssl=True)
SSO_EXTERNAL_URL = get_service_url('sso', ssl=True)


async def check_session(request: Request):
    """Check if user has valid session, return user info or None"""
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        return None
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{IDENTITY_INTERNAL_URL}/api/session/verify",
                cookies={"access_token": access_token}
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except Exception:
        return None


class ClientApp(ServiceClient):
    def __init__(self):
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        super().__init__(
            name='client',
            description='Client UI stub',
            port=CLIENT_PORT,
            mount_lib=True,
            static_dir=static_dir,
            templates_dir=templates_dir
        )
        self.register_routes()

    def register_routes(self):
        @self.app.get('/health')
        async def health():
            return {'service': 'client', 'status': 'healthy', 'port': CLIENT_PORT}

        @self.app.get('/', response_class=HTMLResponse)
        async def index(request: Request):
            # Check session
            user = await check_session(request)
            
            if not user:
                # Not authenticated - redirect to SSO
                return RedirectResponse(url=f"{SSO_EXTERNAL_URL}/?app=client", status_code=303)
            
            # User is authenticated - show home page
            context = {
                'request': request,
                'username': user.get('username', 'Guest'),
                'identity_url': IDENTITY_EXTERNAL_URL,
                'user': user
            }
            return self.templates.TemplateResponse('index.html', context)


client = ClientApp()
app = client.get_app()
templates = client.templates


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=CLIENT_PORT)