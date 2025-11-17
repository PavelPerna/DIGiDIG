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

# Use config values or defaults
async def main():
    import sys
    sys.path.insert(0, '/app')
    from digidig.config import Config

    config = Config.instance()
    db_config = config.db_config("postgres")

    admin_password = config.get("security.admin.password", "admin")
    admin_email = config.get("security.admin.email", "admin@example.com")
    db_user = db_config["user"]
    db_pass = db_config["password"]
    db_name = db_config["database"]
    db_host = db_config["host"]
    
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
