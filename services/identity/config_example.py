"""
Example: Using new configuration system in Identity service

Replace hardcoded values and ENV variables with config file
"""

# OLD WAY (with ENV variables):
# import os
# DB_HOST = os.getenv("DB_HOST", "postgres")
# DB_USER = os.getenv("DB_USER", "strategos")
# JWT_SECRET = os.getenv("JWT_SECRET", "default_secret")

# NEW WAY (with config file):
import subprocess
import sys
import os

from digidig.config import get_config, get_db_config, get_jwt_secret

config = get_config()

# Get database configuration
db_config = get_db_config("postgres")
DB_HOST = db_config["host"]
DB_PORT = db_config["port"]
DB_USER = db_config["user"]
DB_PASS = db_config["password"]
DB_NAME = db_config["database"]

# Get JWT configuration
JWT_SECRET = get_jwt_secret()
JWT_ALGORITHM = config.get("security.jwt.algorithm", "HS256")
ACCESS_TOKEN_EXPIRE = config.get("security.jwt.access_token_expire_minutes", 30)
REFRESH_TOKEN_EXPIRE = config.get("security.jwt.refresh_token_expire_days", 7)

# Get service URLs
STORAGE_URL = config.get("services.storage.url")
SMTP_URL = config.get("services.smtp.rest_url")

# Database connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
