# DIGiDIG SSO Service

Single Sign-On (SSO) service providing centralized authentication for all DIGiDIG services.

## Installation

### As a Python Package
```bash
pip install -e .
```

### Dependencies
- `digidig-core>=1.0.0` - Shared DIGiDIG infrastructure
- `fastapi>=0.104.0` - Web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `httpx>=0.25.0` - Async HTTP client
- `jinja2>=3.0.0` - Template engine
- `python-multipart>=0.0.6` - Form data handling
- `pydantic>=2.5.0` - Data validation

## Usage

### As a package
```bash
digidig-sso
```

### As a module
```python
from sso.src.sso import main
main()
```

### Configuration
The service uses the DIGiDIG configuration system. Key settings:
- `services.sso.http_port` - Service port (default: 9106)

---

# DIGiDIG SSO Service

## Features

- **Centralized Login**: Single login page for all services
- **Session Management**: Secure JWT token handling
- **Service Redirection**: Seamless redirection after authentication
- **Multi-language Support**: English and Czech localization
- **Security**: Secure cookie handling and trusted redirect validation

## Endpoints

### Authentication
- `GET /` - Login page
- `POST /login` - Process login
- `POST /logout` - Logout and clear session
- `GET /verify` - Verify current session

### API
- `POST /api/language` - Set language preference
- `GET /api/translations` - Get translations
- `GET /health` - Health check

## Configuration

The service uses the centralized configuration system. Key settings:

```yaml
services:
  sso:
    host: sso
    port: 9106
    url: http://sso:9106

security:
  cookie:
    secure: false  # Set to true in production
    samesite: "lax"
```

## Usage

### Redirect to SSO for Authentication

When a service needs authentication, redirect to:

```
http://sso:8006/?redirect_to=<your_service_url>
```

Example from client service:
```python
return RedirectResponse(url=f"http://sso:8006/?redirect_to={request.url}")
```

### Verify Session

Services can verify user sessions by checking the `access_token` cookie:

```python
async def verify_session(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        # Redirect to SSO
        return RedirectResponse(url="http://sso:8006/?redirect_to=" + str(request.url))
    
    # Verify with SSO service
    async with aiohttp.ClientSession() as session:
        async with session.get("http://sso:8006/verify", 
                              cookies={"access_token": token}) as response:
            if response.status == 200:
                return await response.json()
            else:
                # Redirect to SSO
                return RedirectResponse(url="http://sso:8006/?redirect_to=" + str(request.url))
```

## Development

### Local Development

```bash
cd services/sso
pip install -r requirements.txt
cd src
python sso.py
```

Service will be available at http://localhost:8006

### Docker Development

```bash
# Build and run
make build sso
make up sso

# Or rebuild completely
make rebuild sso
```

## Security Considerations

1. **Trusted Redirects**: Only allows redirects to configured DIGiDIG services
2. **Secure Cookies**: Uses httponly, secure, and samesite attributes
3. **Token Validation**: All tokens are validated with the Identity service
4. **CSRF Protection**: Form-based authentication with proper validation

## Integration with Other Services

### Client Service
The client service should redirect unauthenticated users to SSO:

```python
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Skip auth for public endpoints
    if request.url.path in ["/health", "/static"]:
        return await call_next(request)
    
    token = request.cookies.get("access_token")
    if not token:
        redirect_url = urllib.parse.quote(str(request.url))
        return RedirectResponse(url=f"http://sso:8006/?redirect_to={redirect_url}")
    
    # Continue with request
    return await call_next(request)
```

### Admin Service
Similar integration for admin functionality with role-based checks.

## Troubleshooting

### Common Issues

1. **Redirect Loop**: Check that redirect URLs are properly URL-encoded
2. **Cookie Issues**: Ensure cookie settings match between services
3. **Token Validation**: Verify Identity service is running and accessible

### Debugging

Enable debug logging:
```python
logging.getLogger().setLevel(logging.DEBUG)
```

Check service health:
```bash
curl http://localhost:8006/health
```