#!/usr/bin/env python3
"""
Utility script to create an admin user in the Identity service database.

This script is intended to be called during installation or by an operator.
It reads configuration from the config system with fallback to ENV variables.

Usage (example):
  ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=s3cr3t DB_HOST=postgres python3 scripts/create_admin.py
"""
import os
import sys
import asyncio
import hashlib
import asyncpg

# Add parent directory to path for config_loader import
sys.path.insert(0, '/app/src')

try:
    from config_loader import config
    USE_CONFIG = True
except ImportError:
    USE_CONFIG = False
    print("Warning: Config module not found, using ENV variables")


def get_required_env(key: str) -> str:
    v = os.getenv(key)
    if not v:
        print(f"Missing required env: {key}")
        sys.exit(2)
    return v


async def main():
    if USE_CONFIG:
        admin_password = config.ADMIN_PASSWORD
        admin_email = config.ADMIN_EMAIL
        db_user = config.DB_USER
        db_pass = config.DB_PASS
        db_name = config.DB_NAME
        db_host = config.DB_HOST
    else:
        admin_password = get_required_env("ADMIN_PASSWORD")
        admin_email = get_required_env("ADMIN_EMAIL")
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASS", "securepassword")
        db_name = os.getenv("DB_NAME", "strategos")
        db_host = os.getenv("DB_HOST", "postgres")
    
    # Extract username and domain from ADMIN_EMAIL
    if "@" in admin_email:
        admin_username, admin_domain = admin_email.split("@", 1)
    else:
        admin_username = admin_email
        admin_domain = None

    hashed_password = hashlib.sha256(admin_password.encode()).hexdigest()

    try:
        pool = await asyncpg.create_pool(user=db_user, password=db_pass, database=db_name, host=db_host)
        async with pool.acquire() as conn:
            # ensure domain exists
            domain_id = None
            if admin_domain:
                await conn.execute("INSERT INTO domains (name) VALUES ($1) ON CONFLICT DO NOTHING", admin_domain)
                row = await conn.fetchrow("SELECT id FROM domains WHERE name = $1", admin_domain)
                domain_id = row["id"] if row else None

            await conn.execute(
                "INSERT INTO users (username, password, domain_id) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                admin_username, hashed_password, domain_id
            )
            print(f"Admin user {admin_username}{('@' + admin_domain) if admin_domain else ''} created or already exists.")
        await pool.close()
    except Exception as e:
        print(f"Failed to create admin: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
