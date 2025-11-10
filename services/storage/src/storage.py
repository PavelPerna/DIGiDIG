import os
import sys
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel
from pymongo import MongoClient
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from digidig.models.service.server import ServiceServer
from digidig.config import get_config

logger = logging.getLogger(__name__)

config = get_config()
HOST = config.get('hostname') or os.getenv('HOSTNAME') or 'localhost'
try:
    STORAGE_PORT = int(config.get('services.storage.port', 9102))
except Exception:
    STORAGE_PORT = 9102

# Global state for service management
service_state = {
    'start_time': time.time(),
    'requests_total': 0,
    'requests_successful': 0,
    'requests_failed': 0,
    'last_request_time': None,
    'config': {
        'hostname': os.getenv('STORAGE_HOSTNAME', '0.0.0.0'),
        'port': int(os.getenv('STORAGE_PORT', '8002')),
        'enabled': True,
        'timeout': int(os.getenv('STORAGE_TIMEOUT', '30')),
        'mongo_uri': os.getenv('MONGO_URI', 'mongodb://mongo:27017'),
        'database_name': os.getenv('DB_NAME', 'strategos'),
        'max_document_size': int(os.getenv('STORAGE_MAX_DOC_SIZE', '16777216'))
    }
}


class Email(BaseModel):
    sender: str
    recipient: str
    subject: str
    body: str
    timestamp: Optional[str] = None
    read: bool = False
    folder: str = 'INBOX'


# Global variables for MongoDB connection (lazy initialized)
client = None
db = None
emails_collection = None


def get_mongo_connection():
    """Initialize MongoDB connection if not already done"""
    global client, db, emails_collection
    
    if client is None:
        try:
            logger.info('Connecting to MongoDB...')
            client = MongoClient(service_state['config']['mongo_uri'], serverSelectionTimeoutMS=10000)
            db = client[service_state['config']['database_name']]
            emails_collection = db['emails']
            
            # Create indexes for efficient querying
            try:
                emails_collection.create_index('recipient')
                emails_collection.create_index([('recipient', 1), ('timestamp', -1)])
                emails_collection.create_index([('recipient', 1), ('read', 1)])
                logger.info('MongoDB indexes created successfully')
            except Exception as idx_error:
                logger.info(f'Index creation skipped (may already exist): {idx_error}')
            
            client.admin.command('ping')
            logger.info('Successfully connected to MongoDB')
        except Exception as e:
            logger.error(f'Error connecting to MongoDB: {str(e)}')
            raise
    
    return client, db, emails_collection


class ServerStorage(ServiceServer):
    def __init__(self):
        super().__init__(
            name='storage',
            description='Storage microservice for DIGiDIG platform',
            port=STORAGE_PORT,
            api_version=None
        )
        self.register_routes()

    def register_routes(self):
        @self.app.post('/api/emails')
        async def store_email(email: Email):
            logger.info(f"Storing email from {email.sender} to {email.recipient}")
            service_state['requests_total'] += 1
            service_state['last_request_time'] = datetime.utcnow().isoformat()
            
            try:
                _, _, emails_collection = get_mongo_connection()
                email_dict = email.dict()
                if not email_dict.get('timestamp'):
                    email_dict['timestamp'] = datetime.utcnow().isoformat()
                
                emails_collection.insert_one(email_dict)
                service_state['requests_successful'] += 1
                logger.info(f"Email from {email.sender} stored successfully")
                return {'status': 'Email stored'}
            except Exception as e:
                service_state['requests_failed'] += 1
                logger.error(f"Error storing email: {str(e)}")
                return {'status': 'error', 'error': str(e)}

        @self.app.get('/api/health')
        async def health_check():
            uptime = time.time() - service_state['start_time']
            
            # Test MongoDB connection
            try:
                client.admin.command('ping')
                db_status = 'connected'
            except Exception as e:
                db_status = f'disconnected: {str(e)}'
            
            status = 'healthy' if service_state['config']['enabled'] and db_status == 'connected' else 'unhealthy'
            
            return {
                'service_name': 'storage',
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': uptime,
                'details': {
                    'enabled': service_state['config']['enabled'],
                    'database_status': db_status
                }
            }


# Create service instance
storage_service = ServerStorage()
app = storage_service.get_app()
