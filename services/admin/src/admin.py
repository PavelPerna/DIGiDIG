import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from digidig.models.service.client import ServiceClient
from digidig.config import get_config, get_service_url
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request
import httpx

# Admin client implemented using ServiceClient pattern (matches mail client)
config = get_config()
ADMIN_PORT = int(config.get('services.admin.http_port', 9105))
HOST = config.get('services.admin.external_url', 'localhost')
# External URLs for user-facing redirects
IDENTITY_URL = get_service_url('identity')
SSO_URL = get_service_url('sso')



async def check_session(request: Request):
    """Check if user has valid session, return user info or None"""
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        return None
    
    try:
        # Use proxy endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:{ADMIN_PORT}/api/identity/session/verify",
                cookies={"access_token": access_token}
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception:
        return None


class ClientAdmin(ServiceClient):
    def __init__(self):
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        super().__init__(
            name='admin',
            description='Admin service (stub)',
            port=ADMIN_PORT,
            mount_lib=True,
            static_dir=static_dir,
            templates_dir=templates_dir
        )
        self.register_routes()

    def register_routes(self):
        @self.app.get('/health')
        async def health():
            return {'service': 'admin', 'status': 'healthy', 'port': ADMIN_PORT}

        @self.app.get('/', response_class=HTMLResponse)
        async def admin_index(request: Request):
            # Check session
            user = await check_session(request)
            
            if not user:
                # Not authenticated - redirect to SSO
                return RedirectResponse(url=f"{SSO_URL}/?app=admin", status_code=303)
            
            # Check if user is admin
            if not user.get('is_admin', False):
                return HTMLResponse(content="<h1>Access Denied</h1><p>Admin role required</p>", status_code=403)
            
            # User is authenticated and is admin - show dashboard
            return self.templates.TemplateResponse('dashboard.html', {
                'request': request,
                'identity_url': IDENTITY_URL,
                'user': user
            })


client = ClientAdmin()
app = client.get_app()
templates = client.templates


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=ADMIN_PORT)

