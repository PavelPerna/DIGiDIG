# Authentication Flow Implementation

## Overview

The DIGiDIG platform now uses a centralized SSO-based authentication flow where:

1. **Client apps** (admin, client, mail) check session status via Identity service
2. **Unauthenticated users** are redirected to SSO with an app parameter
3. **SSO service** displays login form, authenticates via Identity, and redirects back to the app
4. **Client apps** verify the session and display the appropriate page

## Architecture

```
┌─────────┐      ┌─────────┐      ┌──────────┐
│ Client  │─────▶│   SSO   │─────▶│ Identity │
│  Apps   │◀─────│ Service │◀─────│ Service  │
└─────────┘      └─────────┘      └──────────┘
    │                                    │
    └────────────────────────────────────┘
         Session Verification
```

## Flow Diagram

### 1. Initial Access (Unauthenticated)
```
User → /admin
       ↓
Admin checks session → No access_token cookie
       ↓
Redirect to SSO → http://10.1.1.26:9106/?app=admin
       ↓
SSO displays login form
```

### 2. Login Process
```
User submits credentials
       ↓
SSO → POST to Identity /login with {email, password}
       ↓
Identity authenticates and returns access_token
       ↓
SSO sets access_token cookie
       ↓
SSO redirects to admin URL → http://10.1.1.26:9105/
```

### 3. Authenticated Access
```
User → /admin (with access_token cookie)
       ↓
Admin → Identity /api/session/verify with cookie
       ↓
Identity validates token and returns user info
       ↓
Admin displays dashboard
```

## Implementation Details

### Identity Service (`services/identity/src/identity.py`)

**New Endpoint:** `/api/session/verify`
- **Method:** GET
- **Input:** `access_token` cookie
- **Returns:**
  ```json
  {
    "authenticated": true,
    "username": "admin",
    "roles": ["admin", "user"],
    "is_admin": true
  }
  ```
- **Errors:** 401 if not authenticated or token invalid/expired

### SSO Service (`services/sso/src/sso.py`)

**GET `/`** - Display login form
- **Query Params:**
  - `app` - Name of the requesting application (admin, client, mail)
  - `error` - Optional error message to display
- **Returns:** HTML login form

**POST `/login`** - Handle authentication
- **Query Params:**
  - `app` - Name of the requesting application
- **Form Data:**
  - `email` - User email
  - `password` - User password
- **Success:**
  - Sets `access_token` cookie
  - Redirects to application URL
- **Failure:**
  - Redirects back to login form with error message

### Client Applications

All three client apps (admin, client, mail) implement the same pattern:

**Session Check Function:**
```python
async def check_session(request: Request):
    """Check if user has valid session, return user info or None"""
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        return None
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{IDENTITY_URL}/api/session/verify",
            cookies={"access_token": access_token}
        ) as response:
            if response.status == 200:
                return await response.json()
            return None
```

**Route Protection:**
```python
@app.get('/')
async def index(request: Request):
    user = await check_session(request)
    
    if not user:
        # Redirect to SSO with app parameter
        return RedirectResponse(url=f"{SSO_URL}/?app=admin", status_code=303)
    
    # For admin only: check admin role
    if not user.get('is_admin', False):
        return HTMLResponse("Access Denied", status_code=403)
    
    # Display authenticated page
    return templates.TemplateResponse('dashboard.html', {
        'request': request,
        'user': user
    })
```

## Service URLs

The authentication flow uses the following URLs (configured in `config.yaml`):

- **Identity Service:** `http://10.1.1.26:9101`
- **SSO Service:** `http://10.1.1.26:9106`
- **Admin App:** `http://10.1.1.26:9105`
- **Client App:** `http://10.1.1.26:9104`
- **Mail App:** `http://10.1.1.26:9107`

## Security Features

1. **HttpOnly Cookies:** The `access_token` is stored as an HttpOnly cookie to prevent XSS attacks
2. **SameSite Protection:** Cookie is set with `samesite=lax` to prevent CSRF
3. **Token Validation:** Each request validates the token signature and expiration
4. **Revocation Check:** Identity service checks both `revoked_tokens` and `token_blacklist` tables
5. **Role-Based Access:** Admin service requires `is_admin` flag in user info

## Cookie Configuration

Cookies are set with the following parameters:
```python
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,        # Prevent JavaScript access
    samesite="lax",       # CSRF protection
    path="/"              # Available site-wide
)
```

## Error Handling

### SSO Login Errors
- Invalid credentials → Redirect to login with error message
- Network errors → Redirect to login with connection error
- Identity service down → User sees connection error

### Session Verification Errors
- No cookie → Redirect to SSO
- Expired token → Redirect to SSO
- Invalid token → Redirect to SSO
- Revoked token → Redirect to SSO

### Admin Access Control
- Non-admin user → 403 Access Denied page
- No session → Redirect to SSO with `app=admin`

## Testing the Flow

### 1. Test Unauthenticated Access
```bash
# Should redirect to SSO
curl -i http://10.1.1.26:9105/
```

### 2. Test Login
```bash
# Login via SSO
curl -X POST http://10.1.1.26:9106/login?app=admin \
  -d "email=admin@example.com" \
  -d "password=admin" \
  -c cookies.txt

# Check cookie was set
cat cookies.txt
```

### 3. Test Authenticated Access
```bash
# Access admin with cookie
curl -b cookies.txt http://10.1.1.26:9105/
```

### 4. Test Session Verification
```bash
# Direct call to session verify endpoint
curl -b cookies.txt http://10.1.1.26:9101/api/session/verify
```

## Future Enhancements

1. **Remember Me:** Add optional long-lived refresh token
2. **Logout:** Implement logout endpoint that clears cookie and revokes token
3. **Session Timeout:** Add automatic timeout and re-authentication
4. **Multi-Factor Auth:** Add optional 2FA for admin users
5. **OAuth Integration:** Support social login (Google, GitHub, etc.)
6. **Audit Logging:** Track authentication attempts and access patterns

## Configuration Reference

All service URLs are managed through `config/config.yaml`:

```yaml
services:
  identity:
    http_port: 9101
    http_sslport: 9201
    external_url: 10.1.1.26
    
  sso:
    http_port: 9106
    http_sslport: 9206
    external_url: 10.1.1.26
    
  admin:
    http_port: 9105
    http_sslport: 9205
    external_url: 10.1.1.26
    
  client:
    http_port: 9104
    http_sslport: 9204
    external_url: 10.1.1.26
    
  mail:
    http_port: 9107
    http_sslport: 9207
    external_url: 10.1.1.26
```

The `get_service_url(service_name, ssl=False)` helper function constructs the full URL from this configuration.
