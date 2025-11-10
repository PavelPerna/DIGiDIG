import os
import sys
import logging

# Ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from digidig.config import Config
from digidig.models.service.client import ServiceClient
from digidig.language import I18n
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request

logger = logging.getLogger(__name__)

config = Config.instance()
try:
    PORT = int(config.get('services.test_suite.port', 9108))
except Exception:
    PORT = 9108
HOST = config.get('hostname') or os.getenv('HOSTNAME') or 'localhost'


class ClientTestSuite(ServiceClient):
    def __init__(self):
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        super().__init__(
            name='test-suite',
            description='Test suite for DIGiDIG UI components',
            port=PORT,
            mount_lib=True,
            static_dir=static_dir,
            templates_dir=templates_dir
        )
        self.register_routes()

    def register_routes(self):
        @self.app.get('/health')
        async def health():
            return {'service': 'test-suite', 'status': 'healthy', 'port': PORT}

        @self.app.get('/', response_class=HTMLResponse)
        async def test_suite_index(request: Request):
            # Check authentication server-side
            access_token = request.cookies.get('access_token')
            if access_token:
                # Verify token with identity service
                try:
                    import httpx
                    identity_url = config.get('services.identity.url', 'http://identity:9101')
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f'{identity_url}/verify', headers={
                            'Authorization': f'Bearer {access_token}'
                        })
                        if response.status_code != 200:
                            access_token = None
                except Exception:
                    access_token = None

            if not access_token:
                # Redirect to SSO for authentication
                sso_url = config.get('services.sso.external_url', 'http://localhost:9106')
                current_url = str(request.url)
                redirect_url = f'{sso_url}/?redirect_to={current_url}'
                return RedirectResponse(url=redirect_url, status_code=302)

            # User is authenticated, serve the test suite
            # Determine language from user preferences, then cookies, then defaults
            lang = 'en'  # default

            # First try to get language from user preferences
            try:
                import httpx
                identity_url = config.get('services.identity.url', 'http://identity:9101')
                async with httpx.AsyncClient() as client:
                    response = await client.get(f'{identity_url}/api/user/preferences', headers={
                        'Authorization': f'Bearer {access_token}'
                    })
                    if response.status_code == 200:
                        prefs = response.json()
                        if prefs.get('language') in ['en', 'cs']:
                            lang = prefs['language']
            except Exception:
                pass  # Fall back to cookie/default

            # If no preference set, check language cookie
            if lang == 'en':  # Still default
                cookie_lang = request.cookies.get('language')
                if cookie_lang in ['en', 'cs']:
                    lang = cookie_lang

            # Load translations using i18n system
            i18n = I18n(default_language=lang, service_name='test-suite')
            translation_keys = ['title', 'subtitle', 'authenticated_user', 'checking_auth', 'redirecting_login', 'status_success', 'status_error', 'component_status', 'language_selector', 'dark_mode_switch', 'avatar_dropdown', 'top_pane', 'initializing', 'user_preferences', 'loading_prefs', 'language', 'dark_mode', 'test_results', 'starting_tests']
            translations = {key: i18n.get(key) for key in translation_keys}

            admin_email = config.get('security.admin.email', 'admin@example.com')
            return self.templates.TemplateResponse('components-test.html', {
                'request': request,
                'identity_url': config.get('services.identity.external_url', 'http://localhost:9101'),
                'sso_url': config.get('services.sso.external_url', 'http://localhost:9106'),
                'service_name': 'test-suite',
                'admin_email': admin_email,
                'current_language': lang,
                'translations': translations
            })


client = ClientTestSuite()
app = client.get_app()
templates = client.templates


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=PORT)
