import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("STARTING SIMPLE.PY")
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

logger.info("Mounting /lib")
lib_dir = '/app/lib'
if os.path.isdir(lib_dir):
    app.mount('/lib', StaticFiles(directory=lib_dir), name='lib')
    logger.info("Mounted /lib")

@app.get('/health')
async def health():
    return {'status': 'ok'}

@app.get('/test')
async def test():
    return {'message': 'simple test'}

logger.info("Simple app created")