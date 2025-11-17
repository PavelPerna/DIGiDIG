import os
import sys
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel
from pymongo import MongoClient
from fastapi import HTTPException
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from digidig.models.service.server import ServiceServer
from digidig.config import Config

logger = logging.getLogger(__name__)

config = Config.instance()
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
        'mongo_uri': os.getenv('MONGO_URI', 'mongodb://mongo:9302'),
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
                
                result = emails_collection.insert_one(email_dict)
                service_state['requests_successful'] += 1
                logger.info(f"Email from {email.sender} stored successfully")
                return JSONResponse(
                    content={'status': 'stored', 'id': str(result.inserted_id)},
                    status_code=201
                )
            except Exception as e:
                service_state['requests_failed'] += 1
                logger.error(f"Error storing email: {str(e)}")
                return JSONResponse(
                    content={'status': 'error', 'error': str(e)},
                    status_code=500
                )

        @self.app.get('/api/emails')
        async def list_emails(user_email: Optional[str] = None, limit: int = 50):
            """List emails for a user"""
            logger.info(f"Listing emails for {user_email or 'all users'}")
            service_state['requests_total'] += 1
            service_state['last_request_time'] = datetime.utcnow().isoformat()
            
            try:
                _, _, emails_collection = get_mongo_connection()
                
                # Build query
                query = {}
                if user_email:
                    # Find emails sent TO or FROM this user
                    query = {'$or': [{'recipient': user_email}, {'sender': user_email}]}
                
                # Get emails sorted by timestamp (newest first)
                cursor = emails_collection.find(query).sort('timestamp', -1).limit(limit)
                emails = []
                for doc in cursor:
                    # Convert ObjectId to string
                    doc['_id'] = str(doc['_id'])
                    emails.append(doc)
                
                service_state['requests_successful'] += 1
                logger.info(f"Found {len(emails)} emails")
                return {'emails': emails, 'count': len(emails)}
            except Exception as e:
                service_state['requests_failed'] += 1
                logger.error(f"Error listing emails: {str(e)}")
                return JSONResponse(
                    content={'status': 'error', 'error': str(e)},
                    status_code=500
                )

        @self.app.get('/api/emails/{email_id}')
        async def get_email(email_id: str):
            """Get a single email by ID"""
            logger.info(f"Getting email {email_id}")
            service_state['requests_total'] += 1
            service_state['last_request_time'] = datetime.utcnow().isoformat()
            
            try:
                from bson import ObjectId
                _, _, emails_collection = get_mongo_connection()
                
                email = emails_collection.find_one({'_id': ObjectId(email_id)})
                if not email:
                    raise HTTPException(status_code=404, detail="Email not found")
                
                # Convert ObjectId to string
                email['_id'] = str(email['_id'])
                
                service_state['requests_successful'] += 1
                logger.info(f"Email {email_id} retrieved successfully")
                return email
            except Exception as e:
                service_state['requests_failed'] += 1
                logger.error(f"Error getting email {email_id}: {str(e)}")
                return JSONResponse(
                    content={'status': 'error', 'error': str(e)},
                    status_code=500
                )

        @self.app.put('/api/emails/{email_id}/read')
        async def mark_email_read(email_id: str, read: bool = True):
            """Mark email as read or unread"""
            logger.info(f"Marking email {email_id} as {'read' if read else 'unread'}")
            service_state['requests_total'] += 1
            service_state['last_request_time'] = datetime.utcnow().isoformat()
            
            try:
                from bson import ObjectId
                _, _, emails_collection = get_mongo_connection()
                
                result = emails_collection.update_one(
                    {'_id': ObjectId(email_id)},
                    {'$set': {'read': read}}
                )
                
                if result.matched_count == 0:
                    raise HTTPException(status_code=404, detail="Email not found")
                
                service_state['requests_successful'] += 1
                logger.info(f"Email {email_id} marked as {'read' if read else 'unread'}")
                return {'status': 'success', 'read': read}
            except Exception as e:
                service_state['requests_failed'] += 1
                logger.error(f"Error marking email {email_id}: {str(e)}")
                return JSONResponse(
                    content={'status': 'error', 'error': str(e)},
                    status_code=500
                )

        @self.app.get('/api/emails/unread/count')
        async def get_unread_count(user_email: str):
            """Get count of unread emails for a user"""
            logger.info(f"Getting unread count for {user_email}")
            service_state['requests_total'] += 1
            service_state['last_request_time'] = datetime.utcnow().isoformat()
            
            try:
                _, _, emails_collection = get_mongo_connection()
                
                count = emails_collection.count_documents({
                    'recipient': user_email,
                    'read': False
                })
                
                service_state['requests_successful'] += 1
                logger.info(f"Found {count} unread emails for {user_email}")
                return {'unread_count': count}
            except Exception as e:
                service_state['requests_failed'] += 1
                logger.error(f"Error getting unread count for {user_email}: {str(e)}")
                return JSONResponse(
                    content={'status': 'error', 'error': str(e)},
                    status_code=500
                )

        @self.app.delete('/api/emails/{email_id}')
        async def delete_email(email_id: str):
            """Delete an email"""
            logger.info(f"Deleting email {email_id}")
            service_state['requests_total'] += 1
            service_state['last_request_time'] = datetime.utcnow().isoformat()
            
            try:
                from bson import ObjectId
                _, _, emails_collection = get_mongo_connection()
                
                result = emails_collection.delete_one({'_id': ObjectId(email_id)})
                
                if result.deleted_count == 0:
                    raise HTTPException(status_code=404, detail="Email not found")
                
                service_state['requests_successful'] += 1
                logger.info(f"Email {email_id} deleted successfully")
                return {'status': 'deleted'}
            except Exception as e:
                service_state['requests_failed'] += 1
                logger.error(f"Error deleting email {email_id}: {str(e)}")
                return JSONResponse(
                    content={'status': 'error', 'error': str(e)},
                    status_code=500
                )

        @self.app.post('/api/emails/{email_id}/reply')
        async def reply_to_email(email_id: str, reply_data: Dict[str, Any]):
            """Create a reply to an email"""
            logger.info(f"Creating reply to email {email_id}")
            service_state['requests_total'] += 1
            service_state['last_request_time'] = datetime.utcnow().isoformat()
            
            try:
                from bson import ObjectId
                _, _, emails_collection = get_mongo_connection()
                
                # Get original email
                original = emails_collection.find_one({'_id': ObjectId(email_id)})
                if not original:
                    raise HTTPException(status_code=404, detail="Original email not found")
                
                # Create reply email
                reply_email = {
                    'sender': reply_data['from'],
                    'recipient': original['sender'],
                    'subject': f"Re: {original['subject']}",
                    'body': reply_data['body'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'read': False,
                    'folder': 'INBOX'
                }
                
                result = emails_collection.insert_one(reply_email)
                
                service_state['requests_successful'] += 1
                logger.info(f"Reply to email {email_id} created successfully")
                return JSONResponse(
                    content={'status': 'sent', 'id': str(result.inserted_id)},
                    status_code=201
                )
            except Exception as e:
                service_state['requests_failed'] += 1
                logger.error(f"Error creating reply to email {email_id}: {str(e)}")
                return JSONResponse(
                    content={'status': 'error', 'error': str(e)},
                    status_code=500
                )

        @self.app.post('/api/emails/{email_id}/forward')
        async def forward_email(email_id: str, forward_data: Dict[str, Any]):
            """Forward an email"""
            logger.info(f"Forwarding email {email_id}")
            service_state['requests_total'] += 1
            service_state['last_request_time'] = datetime.utcnow().isoformat()
            
            try:
                from bson import ObjectId
                _, _, emails_collection = get_mongo_connection()
                
                # Get original email
                original = emails_collection.find_one({'_id': ObjectId(email_id)})
                if not original:
                    raise HTTPException(status_code=404, detail="Original email not found")
                
                # Create forwarded email
                forward_body = f"---------- Forwarded message ----------\nFrom: {original['sender']}\nTo: {original['recipient']}\nSubject: {original['subject']}\n\n{original['body']}\n\n{forward_data.get('message', '')}"
                
                forward_email = {
                    'sender': forward_data['from'],
                    'recipient': forward_data['to'],
                    'subject': f"Fwd: {original['subject']}",
                    'body': forward_body,
                    'timestamp': datetime.utcnow().isoformat(),
                    'read': False,
                    'folder': 'INBOX'
                }
                
                result = emails_collection.insert_one(forward_email)
                
                service_state['requests_successful'] += 1
                logger.info(f"Email {email_id} forwarded successfully")
                return JSONResponse(
                    content={'status': 'sent', 'id': str(result.inserted_id)},
                    status_code=201
                )
            except Exception as e:
                service_state['requests_failed'] += 1
                logger.error(f"Error forwarding email {email_id}: {str(e)}")
                return JSONResponse(
                    content={'status': 'error', 'error': str(e)},
                    status_code=500
                )


# Create service instance
storage_service = ServerStorage()
app = storage_service.get_app()
