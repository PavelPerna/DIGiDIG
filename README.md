# DIGiDIG Project

## Security Notes

### Identity Service

The identity service has been updated to remove hardcoded admin credentials and improve security:

1. Admin User Creation
   - No more hardcoded admin credentials in the code
   - Admin user is now created via `identity/scripts/create_admin.py` during installation
   - Required environment variables:
     - `ADMIN_EMAIL` - Email for admin account
     - `ADMIN_PASSWORD` - Password for admin account
   - Example usage:

     ```bash
     ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=secure123 python3 scripts/create_admin.py
     ```

2. JWT Security
   - JWT tokens are used for authentication
   - The secret key can be customized via `JWT_SECRET` environment variable
   - Example in docker-compose.yml:

     ```yaml
     environment:
       - JWT_SECRET=your_secure_secret_here  # Change this in production!
     ```

3. Default Values & Security
   - The system includes fallback values for development, but all sensitive values should be overridden in production:
     - Database credentials
     - JWT secret
     - Admin credentials

### Database Security

1. PostgreSQL
   - Credentials configurable via environment variables:
     - `DB_USER`
     - `DB_PASS`
     - `DB_NAME`
     - `DB_HOST`
   - Default values are for development only

## Installation

These steps will set up the project with secure configuration:

1. Configure environment variables by creating `.env` file:

   ```env
   DB_USER=your_db_user
   DB_PASS=your_db_password
   DB_NAME=your_db_name
   JWT_SECRET=your_jwt_secret
   ADMIN_EMAIL=your_admin@example.com
   ADMIN_PASSWORD=your_secure_admin_password
   ```

1. Run the installation:

   ```bash
   make install
   ```

1. Start the services:

   ```bash
   docker compose up
   ```

## Security Best Practices

1. Always change default credentials in production
2. Use strong passwords and secrets
3. Keep environment variables secure and never commit them to version control
4. Regularly rotate JWT secrets and admin credentials