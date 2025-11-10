"""
Shared JWT utilities for DIGiDIG services
Provides common JWT token validation, creation, and handling logic
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from fastapi import HTTPException, Request, status


def create_jwt_token(
    payload: Dict[str, Any],
    secret: str,
    algorithm: str = "HS256",
    expires_minutes: Optional[int] = None
) -> str:
    """
    Create a JWT token with the given payload
    
    Args:
        payload: Data to encode in the token
        secret: JWT secret key
        algorithm: Encoding algorithm (default: HS256)
        expires_minutes: Token expiration time in minutes
        
    Returns:
        Encoded JWT token string
    """
    token_data = payload.copy()
    
    if expires_minutes:
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
        token_data["exp"] = expire
    
    if "iat" not in token_data:
        token_data["iat"] = datetime.utcnow()
    
    return jwt.encode(token_data, secret, algorithm=algorithm)


def decode_jwt_token(
    token: str,
    secret: str,
    algorithm: str = "HS256",
    verify_exp: bool = True
) -> Dict[str, Any]:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token string
        secret: JWT secret key
        algorithm: Decoding algorithm (default: HS256)
        verify_exp: Whether to verify token expiration
        
    Returns:
        Decoded token payload
        
    Raises:
        jwt.InvalidTokenError: If token is invalid or expired
    """
    options = {"verify_exp": verify_exp}
    return jwt.decode(token, secret, algorithms=[algorithm], options=options)


def validate_jwt_token(
    token: str,
    secret: str,
    algorithm: str = "HS256"
) -> Optional[Dict[str, Any]]:
    """
    Validate JWT token and return payload if valid, None otherwise
    
    Args:
        token: JWT token string
        secret: JWT secret key
        algorithm: Decoding algorithm (default: HS256)
        
    Returns:
        Token payload if valid, None if invalid
    """
    try:
        return decode_jwt_token(token, secret, algorithm)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def extract_token_from_request(request: Request, token_name: str = "access_token") -> Optional[str]:
    """
    Extract JWT token from request cookies or Authorization header
    
    Args:
        request: FastAPI Request object
        token_name: Name of the token cookie (default: access_token)
        
    Returns:
        Token string if found, None otherwise
    """
    # Try to get from cookies first
    token = request.cookies.get(token_name)
    if token:
        return token
    
    # Try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    return None


def require_jwt_auth(secret: str, algorithm: str = "HS256"):
    """
    Decorator to require JWT authentication for FastAPI endpoints
    
    Usage:
        @app.get("/protected")
        @require_jwt_auth(secret="your-secret")
        async def protected_endpoint(request: Request):
            user = request.state.user
            return {"message": f"Hello {user['email']}"}
    
    Args:
        secret: JWT secret key
        algorithm: Decoding algorithm (default: HS256)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            token = extract_token_from_request(request)
            
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authentication token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            payload = validate_jwt_token(token, secret, algorithm)
            
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Store user info in request state for access in the endpoint
            request.state.user = payload
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def create_access_token(
    user_id: str,
    email: str,
    secret: str,
    expires_minutes: int = 30,
    **extra_claims
) -> str:
    """
    Create a standard access token for a user
    
    Args:
        user_id: User ID
        email: User email
        secret: JWT secret key
        expires_minutes: Token expiration (default: 30 minutes)
        **extra_claims: Additional claims to include
        
    Returns:
        JWT access token
    """
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        **extra_claims
    }
    return create_jwt_token(payload, secret, expires_minutes=expires_minutes)


def create_refresh_token(
    user_id: str,
    email: str,
    secret: str,
    expires_days: int = 7,
    **extra_claims
) -> str:
    """
    Create a refresh token for a user
    
    Args:
        user_id: User ID
        email: User email
        secret: JWT secret key
        expires_days: Token expiration (default: 7 days)
        **extra_claims: Additional claims to include
        
    Returns:
        JWT refresh token
    """
    payload = {
        "sub": user_id,
        "email": email,
        "type": "refresh",
        **extra_claims
    }
    return create_jwt_token(payload, secret, expires_minutes=expires_days * 24 * 60)


def verify_refresh_token(
    token: str,
    secret: str,
    algorithm: str = "HS256"
) -> Optional[Dict[str, Any]]:
    """
    Verify a refresh token and return payload if valid
    
    Args:
        token: Refresh token string
        secret: JWT secret key
        algorithm: Decoding algorithm
        
    Returns:
        Token payload if valid and is a refresh token, None otherwise
    """
    payload = validate_jwt_token(token, secret, algorithm)
    
    if payload and payload.get("type") == "refresh":
        return payload
    
    return None
