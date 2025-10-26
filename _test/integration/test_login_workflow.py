#!/usr/bin/env python3
"""
Comprehensive login workflow integration tests for DIGiDIG authentication system.
Tests the complete SSO authentication flow including login, logout, and redirects.

Tests cover:
1. SSO login page rendering
2. Admin service authentication flow  
3. Client service authentication flow
4. Logout functionality (GET and POST)
5. Session validation and cookie management
6. Redirect URL validation and security
7. Cross-service authentication state
"""

import pytest
import requests
import urllib.parse
from urllib.parse import parse_qs, urlparse
import os
import time
import re

# Service URLs - use Docker service names for Docker network testing
def get_service_url(service, port, default_host='localhost'):
    """Get service URL, using Docker service names for Docker network compatibility"""
    # Use Docker service names for network communication
    return f'http://{service}:{port}'

SSO_URL = get_service_url('sso', 8006)
ADMIN_URL = get_service_url('admin', 8005)
CLIENT_URL = get_service_url('client', 8004)
IDENTITY_URL = get_service_url('identity', 8001)
TIMEOUT = float(os.getenv("INTEGRATION_TIMEOUT", "10"))

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin"


class TestLoginWorkflow:
    """Test suite for complete login workflow"""

    def test_sso_login_page_loads(self):
        """Test that SSO login page loads correctly"""
        response = requests.get(f"{SSO_URL}/", timeout=TIMEOUT)
        assert response.status_code == 200
        assert "DIGiDIG Login" in response.text
        assert '<form method="post" action="/login">' in response.text
        assert 'name="username"' in response.text
        assert 'name="password"' in response.text

    def test_admin_service_authentication_redirect(self):
        """Test that admin service redirects unauthenticated users to SSO"""
        session = requests.Session()
        
        # Try to access admin without authentication
        response = session.get(f"{ADMIN_URL}/", allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        # Should redirect to SSO with correct redirect_to parameter
        location = response.headers.get("Location")
        # Accept both localhost and service name URLs for SSO
        assert (location.startswith("http://localhost:8006/?redirect_to=") or 
                location.startswith("http://sso:8006/?redirect_to="))
        
        # Extract redirect_to parameter
        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        redirect_to = query_params.get("redirect_to", [None])[0]
        assert redirect_to
        
        # Decode and verify redirect URL
        decoded_redirect = urllib.parse.unquote(redirect_to)
        assert decoded_redirect.startswith(ADMIN_URL)

    def test_client_service_authentication_redirect(self):
        """Test that client service redirects unauthenticated users to SSO"""
        session = requests.Session()
        
        # Try to access client without authentication
        response = session.get(f"{CLIENT_URL}/", allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        # Should redirect to SSO with correct redirect_to parameter
        location = response.headers.get("Location")
        assert location.startswith(f"{SSO_URL}/?redirect_to=")
        
        # Extract and verify redirect parameter
        parsed_url = urlparse(location)
        query_params = parse_qs(parsed_url.query)
        redirect_to = query_params.get("redirect_to", [None])[0]
        assert redirect_to
        
        decoded_redirect = urllib.parse.unquote(redirect_to)
        assert "/dashboard" in decoded_redirect

    def test_sso_login_success_with_redirect(self):
        """Test successful SSO login with redirect back to requesting service"""
        session = requests.Session()
        
        # Login via SSO with redirect to admin
        admin_redirect_url = urllib.parse.quote(f"{ADMIN_URL}/")
        login_url = f"{SSO_URL}/login?redirect_to={admin_redirect_url}"
        
        response = session.post(
            login_url,
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            allow_redirects=False,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 302
        
        # Should redirect back to admin service
        location = response.headers.get("Location")
        assert location == f"{ADMIN_URL}/"
        
        # Should set authentication cookies
        cookies = session.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies

    def test_admin_dashboard_access_after_login(self):
        """Test that admin dashboard is accessible after successful login"""
        session = requests.Session()
        
        # Login first
        response = session.post(
            f"{SSO_URL}/login",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            allow_redirects=False,
            timeout=TIMEOUT
        )
        assert response.status_code == 302
        
        # Now access admin dashboard
        response = session.get(f"{ADMIN_URL}/", timeout=TIMEOUT)
        assert response.status_code == 200
        assert "Admin Dashboard" in response.text
        assert "admin" in response.text.lower()

    def test_client_dashboard_access_after_login(self):
        """Test that client dashboard is accessible after successful login"""
        session = requests.Session()
        
        # Login first
        response = session.post(
            f"{SSO_URL}/login",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            allow_redirects=False,
            timeout=TIMEOUT
        )
        assert response.status_code == 302
        
        # Access client root (should redirect to dashboard)
        response = session.get(f"{CLIENT_URL}/", timeout=TIMEOUT)
        assert response.status_code == 200
        assert "Welcome, admin!" in response.text

    def test_cross_service_authentication_sharing(self):
        """Test that authentication is shared between admin and client services"""
        session = requests.Session()
        
        # Login via SSO
        response = session.post(
            f"{SSO_URL}/login",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            allow_redirects=False,
            timeout=TIMEOUT
        )
        assert response.status_code == 302
        
        # Access both services with same session
        admin_response = session.get(f"{ADMIN_URL}/", timeout=TIMEOUT)
        assert admin_response.status_code == 200
        assert "Admin Dashboard" in admin_response.text
        
        client_response = session.get(f"{CLIENT_URL}/dashboard", timeout=TIMEOUT)
        assert client_response.status_code == 200
        assert "Welcome, admin!" in client_response.text

    def test_sso_login_invalid_credentials(self):
        """Test SSO login with invalid credentials"""
        session = requests.Session()
        
        response = session.post(
            f"{SSO_URL}/login",
            data={"username": "invalid", "password": "wrong"},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 401
        assert "invalid" in response.text.lower() or "error" in response.text.lower()

    def test_logout_get_method(self):
        """Test logout functionality using GET method"""
        session = requests.Session()
        
        # Login first
        response = session.post(
            f"{SSO_URL}/login",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=TIMEOUT
        )
        assert response.status_code == 302
        
        # Verify authenticated access works
        response = session.get(f"{CLIENT_URL}/dashboard", timeout=TIMEOUT)
        assert response.status_code == 200
        
        # Logout using GET method
        response = session.get(f"{CLIENT_URL}/logout", allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        # Follow the logout redirect chain
        location = response.headers.get("Location")
        assert f"{SSO_URL}/logout" in location
        
        # Complete logout
        response = session.get(location, allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        # After logout, should not have access to protected resources
        response = session.get(f"{CLIENT_URL}/dashboard", allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307  # Should redirect to login

    def test_logout_post_method(self):
        """Test logout functionality using POST method"""
        session = requests.Session()
        
        # Login first
        response = session.post(
            f"{SSO_URL}/login",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=TIMEOUT
        )
        assert response.status_code == 302
        
        # Verify authenticated access works
        response = session.get(f"{ADMIN_URL}/", timeout=TIMEOUT)
        assert response.status_code == 200
        
        # Logout using POST method
        response = session.post(f"{CLIENT_URL}/logout", allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        # Follow logout redirect to SSO
        location = response.headers.get("Location")
        response = session.post(location, allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        # After logout, should not have access to protected resources
        response = session.get(f"{ADMIN_URL}/", allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307  # Should redirect to login

    def test_session_cookie_management(self):
        """Test that authentication cookies are properly managed"""
        session = requests.Session()
        
        # Before login - no auth cookies
        assert "access_token" not in session.cookies
        assert "refresh_token" not in session.cookies
        
        # Login
        response = session.post(
            f"{SSO_URL}/login",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=TIMEOUT
        )
        assert response.status_code == 302
        
        # After login - should have auth cookies
        assert "access_token" in session.cookies
        assert "refresh_token" in session.cookies
        
        # Cookies should be HttpOnly and have appropriate attributes
        access_token_cookie = None
        for cookie in response.cookies:
            if cookie.name == "access_token":
                access_token_cookie = cookie
                break
        
        assert access_token_cookie is not None
        # Note: requests library doesn't expose HttpOnly flag, but we can verify in headers

    def test_redirect_url_validation(self):
        """Test that redirect URLs are properly validated for security"""
        session = requests.Session()
        
        # Try login with malicious redirect URL
        malicious_url = urllib.parse.quote("http://evil.com/steal-tokens")
        response = session.post(
            f"{SSO_URL}/login?redirect_to={malicious_url}",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            allow_redirects=False,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 302
        
        # Should redirect to safe default location, not malicious URL
        location = response.headers.get("Location")
        assert not location.startswith("http://evil.com")
        assert location.startswith(CLIENT_URL)  # Default redirect

    def test_sso_session_verification(self):
        """Test SSO session verification endpoint"""
        session = requests.Session()
        
        # Login first
        response = session.post(
            f"{SSO_URL}/login",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=TIMEOUT
        )
        assert response.status_code == 302
        
        # Test session verification
        response = session.get(f"{SSO_URL}/verify", timeout=TIMEOUT)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["username"] == TEST_USERNAME
        assert "admin" in user_data.get("roles", [])

    def test_login_with_email(self):
        """Test login using email instead of username"""
        session = requests.Session()
        
        # Try login with email format
        response = session.post(
            f"{SSO_URL}/login",
            data={"username": "admin@example.com", "password": TEST_PASSWORD},
            allow_redirects=False,
            timeout=TIMEOUT
        )
        
        # Should either succeed or fail gracefully depending on identity service config
        assert response.status_code in [200, 302, 401]
        
        if response.status_code == 302:
            # If successful, should have cookies
            assert "access_token" in session.cookies

    def test_concurrent_sessions(self):
        """Test that multiple concurrent sessions work correctly"""
        session1 = requests.Session()
        session2 = requests.Session()
        
        # Login with both sessions
        for session in [session1, session2]:
            response = session.post(
                f"{SSO_URL}/login",
                data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
                timeout=TIMEOUT
            )
            assert response.status_code == 302
        
        # Both sessions should have independent access
        for session in [session1, session2]:
            response = session.get(f"{ADMIN_URL}/", timeout=TIMEOUT)
            assert response.status_code == 200
        
        # Logout one session
        response = session1.get(f"{CLIENT_URL}/logout", timeout=TIMEOUT)
        
        # First session should be logged out
        response = session1.get(f"{ADMIN_URL}/", allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        # Second session should still work
        response = session2.get(f"{ADMIN_URL}/", timeout=TIMEOUT)
        assert response.status_code == 200

    def test_admin_api_login_endpoint(self):
        """Test admin service API login endpoint"""
        response = requests.post(
            f"{ADMIN_URL}/api/login",
            json={"email": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_complete_auth_flow_with_redirects(self):
        """Test complete authentication flow following all redirects"""
        session = requests.Session()
        
        # Start by accessing admin without auth - should redirect to SSO
        response = session.get(f"{ADMIN_URL}/", timeout=TIMEOUT)
        
        # Should end up on login page
        assert response.status_code == 200
        assert "DIGiDIG Login" in response.text
        
        # Login through the form
        response = session.post(
            f"{SSO_URL}/login",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=TIMEOUT
        )
        
        # Should successfully access the originally requested page
        assert response.status_code == 200
        assert "Admin Dashboard" in response.text

    def test_sso_health_check(self):
        """Test SSO service health check endpoint"""
        response = requests.get(f"{SSO_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "sso"

    def test_identity_token_verification(self):
        """Test token verification with identity service"""
        session = requests.Session()
        
        # Login to get token
        response = session.post(
            f"{SSO_URL}/login",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=TIMEOUT
        )
        assert response.status_code == 302
        
        # Extract token from cookie
        access_token = session.cookies.get("access_token")
        assert access_token
        
        # Verify token with identity service
        response = requests.get(
            f"{IDENTITY_URL}/verify",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["username"] == TEST_USERNAME


# Mark all tests in this class as integration tests
pytestmark = pytest.mark.integration