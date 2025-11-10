import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from digidig.models.service.server import ServiceServer
from digidig.config import get_config

config = get_config()
try:
    SMTP_PORT = int(config.get('services.smtp.rest_port', 9100))
except Exception:
    SMTP_PORT = 9100


class ServerSMTP(ServiceServer):
    def __init__(self):
        super().__init__(
            name='smtp',
            description='SMTP microservice (stub)',
            port=SMTP_PORT,
            api_version=None  # Uses /api/ directly
        )
        self.register_routes()

    def register_routes(self):
        @self.app.post('/api/send')
        async def send_email_stub(payload: dict):
            """Send email endpoint"""
            return {'status': 'queued', 'payload': payload}


# Create service instance
smtp_service = ServerSMTP()
app = smtp_service.get_app()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=SMTP_PORT)