import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Try to import from digidig_core package first, fallback to local digidig
try:
    from digidig_core.service.server import ServiceServer
    from digidig_core.config import Config
except ImportError:
    # Fallback to local imports for backward compatibility
    from digidig.models.service.server import ServiceServer
    from digidig.config import Config
import httpx
from datetime import datetime

config = Config.instance()
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
        async def send_email(payload: dict):
            """Send email endpoint - stores in storage service"""
            # Validate required fields
            required = ['sender', 'recipient', 'subject', 'body']
            missing = [f for f in required if f not in payload]
            if missing:
                return {'status': 'error', 'message': f'Missing fields: {", ".join(missing)}'}, 400
            
            # Prepare email document for storage
            email_doc = {
                'sender': payload['sender'],
                'recipient': payload['recipient'],
                'subject': payload['subject'],
                'body': payload['body'],
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'sent'
            }
            
            try:
                # Store email in storage service
                async with httpx.AsyncClient() as client:
                    storage_url = config.service_internal_url('storage')
                    response = await client.post(
                        f'{storage_url}/api/emails',
                        json=email_doc,
                        timeout=5.0
                    )
                    print(f"Storage response: {response.status_code}, body: {response.text}")
                    if response.status_code in [200, 201]:
                        try:
                            stored = response.json()
                            # Handle both dict and list responses
                            email_id = stored.get('id', 'unknown') if isinstance(stored, dict) else 'unknown'
                            return {'status': 'sent', 'email_id': email_id}
                        except:
                            return {'status': 'sent', 'email_id': 'unknown'}
                    else:
                        return {'status': 'error', 'message': f'Storage failed: {response.status_code}'}, 500
            except Exception as e:
                print(f"Error storing email: {e}")
                return {'status': 'error', 'message': str(e)}, 500


# Create service instance
smtp_service = ServerSMTP()
app = smtp_service.get_app()


def main():
    """Main entry point for running the SMTP service"""
    import uvicorn
    
    logger = config.get_logger('smtp')
    logger.info(f"Starting SMTP Service on 0.0.0.0:{SMTP_PORT}")
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=SMTP_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()