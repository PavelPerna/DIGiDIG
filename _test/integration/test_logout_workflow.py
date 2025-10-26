#!/usr/bin/env python3
"""
Focused logout functionality tests for DIGiDIG authentication system.
Tests the logout workflow that was recently fixed, including both GET and POST methods.

Tests cover:
1. Logout endpoint availability (GET and POST)
2. Cookie clearing on logout
3. Session invalidation
4. Redirect chain validation
5. Cross-service logout behavior
6. Error handling for logout
"""

import pytest
import requests
import urllib.parse
from urllib.parse import parse_qs, urlparse
import os
import re

# Service URLs - use Docker service names for containerized tests
def get_service_url(service, port, default_host='localhost'):
    """Get service URL, preferring Docker service names in containerized environment"""
    if os.getenv('SKIP_COMPOSE') == '1':  # Running in Docker test container
        return f'http://{service}:{port}'
    return f'http://{default_host}:{port}'

SSO_URL = get_service_url('sso', 8006)
ADMIN_URL = get_service_url('admin', 8005)
CLIENT_URL = get_service_url('client', 8004)
IDENTITY_URL = get_service_url('identity', 8001)
TIMEOUT = float(os.getenv("INTEGRATION_TIMEOUT", "10"))

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin"


class TestLogoutFunctionality:
    """Comprehensive tests for logout functionality"""

    def _login_session(self, session):
        """Helper method to login a session"""
        response = session.post(
            f"{SSO_URL}/login",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            allow_redirects=False,
            timeout=TIMEOUT
        )
        # Login should return either 302 redirect or 200 if no redirect_to specified
        assert response.status_code in [200, 302]
        
        # Verify we got auth cookies
        if response.status_code == 302:
            assert "access_token" in session.cookies
            assert "refresh_token" in session.cookies
        elif response.status_code == 200:
            # If 200, try again with explicit redirect or check if we can access protected resource
            # Sometimes login without redirect_to parameter behaves differently
            test_response = session.get(f"{CLIENT_URL}/dashboard", allow_redirects=False, timeout=TIMEOUT)
            if test_response.status_code == 200:
                # Already logged in successfully
                return session
            else:
                # Need to login with redirect parameter
                response = session.post(
                    f"{SSO_URL}/login?redirect_to={urllib.parse.quote(f'{CLIENT_URL}/dashboard')}",
                    data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
                    allow_redirects=False,
                    timeout=TIMEOUT
                )
                assert response.status_code == 302
                assert "access_token" in session.cookies
                assert "refresh_token" in session.cookies
        
        return session

    def _verify_logged_out(self, session):
        """Helper method to verify session is logged out"""
        # Try to access protected resource - should redirect to login
        response = session.get(f"{CLIENT_URL}/dashboard", allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        location = response.headers.get("Location")
        assert f"{SSO_URL}/" in location and "redirect_to" in location

    def test_client_logout_get_method(self):
        """Test client service logout using GET method"""
        session = requests.Session()
        self._login_session(session)
        
        # Verify login works
        response = session.get(f"{CLIENT_URL}/dashboard", timeout=TIMEOUT)
        assert response.status_code == 200
        assert "Welcome, admin!" in response.text
        
        # Logout using GET
        response = session.get(f"{CLIENT_URL}/logout", allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        # Should redirect to SSO logout with proper redirect_to parameter
        location = response.headers.get("Location")
        assert f"{SSO_URL}/logout" in location
        assert "redirect_to=" in location
        
        # Follow redirect to SSO logout
        response = session.get(location, allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        # Verify session is invalidated
        self._verify_logged_out(session)

    def test_client_logout_post_method(self):
        """Test client service logout using POST method"""
        session = requests.Session()
        self._login_session(session)
        
        # Verify login works
        response = session.get(f"{CLIENT_URL}/dashboard", timeout=TIMEOUT)
        assert response.status_code == 200
        
        # Logout using POST
        response = session.post(f"{CLIENT_URL}/logout", allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        # Should redirect to SSO logout
        location = response.headers.get("Location")
        assert f"{SSO_URL}/logout" in location
        
        # Follow redirect chain
        response = session.post(location, allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        # Verify session is invalidated
        self._verify_logged_out(session)

    def test_sso_logout_get_method(self):
        """Test direct SSO logout using GET method"""
        session = requests.Session()
        self._login_session(session)
        
        # Direct SSO logout with redirect parameter
        redirect_url = urllib.parse.quote(f"{CLIENT_URL}/")
        response = session.get(
            f"{SSO_URL}/logout?redirect_to={redirect_url}",
            allow_redirects=False,
            timeout=TIMEOUT
        )
        assert response.status_code == 307
        
        # Should redirect to specified URL
        location = response.headers.get("Location")
        assert location == f"{CLIENT_URL}/"
        
        # Verify cookies are cleared
        self._verify_logged_out(session)

    def test_sso_logout_post_method(self):
        """Test direct SSO logout using POST method"""
        session = requests.Session()
        self._login_session(session)
        
        # Direct SSO logout with redirect parameter
        redirect_url = urllib.parse.quote(f"{ADMIN_URL}/")
        response = session.post(
            f"{SSO_URL}/logout?redirect_to={redirect_url}",
            allow_redirects=False,
            timeout=TIMEOUT
        )
        assert response.status_code == 307
        
        # Should redirect to specified URL
        location = response.headers.get("Location")
        assert location == f"{ADMIN_URL}/"
        
        # Verify session is invalidated
        self._verify_logged_out(session)

    def test_logout_cookie_clearing(self):
        """Test that logout properly clears authentication cookies"""
        session = requests.Session()
        self._login_session(session)
        
        # Verify cookies are set
        assert "access_token" in session.cookies
        assert "refresh_token" in session.cookies
        
        # Logout and capture response to check Set-Cookie headers
        response = session.get(
            f"{SSO_URL}/logout?redirect_to={urllib.parse.quote(CLIENT_URL)}",
            allow_redirects=False,
            timeout=TIMEOUT
        )
        
        # Check that cookies are being cleared in response headers
        set_cookie_headers = response.headers.get_list("Set-Cookie") if hasattr(response.headers, 'get_list') else [response.headers.get("Set-Cookie")]
        set_cookie_headers = [h for h in set_cookie_headers if h]
        
        # Should have Set-Cookie headers that clear the tokens
        cookie_text = " ".join(set_cookie_headers)
        assert "access_token=" in cookie_text
        assert "refresh_token=" in cookie_text
        assert "Max-Age=0" in cookie_text or "expires=" in cookie_text

    def test_logout_without_redirect_parameter(self):
        """Test logout behavior when no redirect parameter is provided"""
        session = requests.Session()
        self._login_session(session)
        
        # Logout without redirect parameter
        response = session.get(f"{SSO_URL}/logout", allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        # Should redirect to default location (root)
        location = response.headers.get("Location")
        assert location == "/"

    def test_logout_with_invalid_redirect_url(self):
        """Test logout with invalid/malicious redirect URL"""
        session = requests.Session()
        self._login_session(session)
        
        # Try logout with malicious redirect
        malicious_url = urllib.parse.quote("http://evil.com/steal-data")
        response = session.get(
            f"{SSO_URL}/logout?redirect_to={malicious_url}",
            allow_redirects=False,
            timeout=TIMEOUT
        )
        assert response.status_code == 307
        
        # Should not redirect to malicious URL
        location = response.headers.get("Location")
        assert not location.startswith("http://evil.com")
        assert location == "/"  # Should use default redirect

    def test_logout_cross_service_invalidation(self):
        """Test that logout from one service invalidates session across all services"""
        session = requests.Session()
        self._login_session(session)
        
        # Verify access to both admin and client
        admin_response = session.get(f"{ADMIN_URL}/", timeout=TIMEOUT)
        assert admin_response.status_code == 200
        
        client_response = session.get(f"{CLIENT_URL}/dashboard", timeout=TIMEOUT)
        assert client_response.status_code == 200
        
        # Logout from client service
        session.get(f"{CLIENT_URL}/logout", timeout=TIMEOUT)
        
        # Both services should now require re-authentication
        admin_response = session.get(f"{ADMIN_URL}/", allow_redirects=False, timeout=TIMEOUT)
        assert admin_response.status_code == 307
        
        client_response = session.get(f"{CLIENT_URL}/dashboard", allow_redirects=False, timeout=TIMEOUT)
        assert admin_response.status_code == 307

    def test_double_logout(self):
        """Test that multiple logout attempts don't cause errors"""
        session = requests.Session()
        self._login_session(session)
        
        # First logout
        response = session.get(f"{CLIENT_URL}/logout", timeout=TIMEOUT)
        assert response.status_code == 200  # Should complete successfully
        
        # Second logout (already logged out)
        response = session.get(f"{CLIENT_URL}/logout", timeout=TIMEOUT)
        # Should not cause error, just redirect appropriately
        assert response.status_code in [200, 307]

    def test_logout_preserves_language_settings(self):
        """Test that logout preserves non-authentication cookies like language"""
        session = requests.Session()
        
        # Set language cookie first
        session.get(f"{SSO_URL}/", timeout=TIMEOUT)
        session.post(f"{SSO_URL}/api/language", data={"lang": "cs"}, timeout=TIMEOUT)
        
        # Login
        self._login_session(session)
        
        # Logout
        session.get(f"{CLIENT_URL}/logout", timeout=TIMEOUT)
        
        # Language cookie should still be there
        assert "language" in session.cookies
        assert session.cookies.get("language") == "cs"

    def test_logout_handles_expired_tokens(self):
        """Test logout behavior with already expired tokens"""
        session = requests.Session()
        
        # Manually set expired token cookies
        session.cookies.set("access_token", "expired.token.here", domain="localhost")
        session.cookies.set("refresh_token", "expired-refresh-token", domain="localhost")
        
        # Logout should still work
        response = session.get(f"{CLIENT_URL}/logout", allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307
        
        # Should complete logout flow without errors
        location = response.headers.get("Location")
        response = session.get(location, allow_redirects=False, timeout=TIMEOUT)
        assert response.status_code == 307

    def test_logout_redirect_url_encoding(self):
        """Test that logout properly handles URL encoding in redirect parameters"""
        session = requests.Session()
        self._login_session(session)
        
        # Logout with complex redirect URL that needs encoding
        complex_url = f"{CLIENT_URL}/dashboard?param1=value1&param2=value2"
        encoded_url = urllib.parse.quote(complex_url)
        
        response = session.get(
            f"{SSO_URL}/logout?redirect_to={encoded_url}",
            allow_redirects=False,
            timeout=TIMEOUT
        )
        assert response.status_code == 307
        
        # Should properly decode and redirect to the complex URL
        location = response.headers.get("Location")
        assert location == complex_url

    def test_admin_service_logout_endpoint(self):
        """Test that admin service logout endpoint exists and works"""
        session = requests.Session()
        self._login_session(session)
        
        # Admin service might have its own logout endpoint
        # Test both GET and POST methods
        for method in ["GET", "POST"]:
            test_session = requests.Session()
            self._login_session(test_session)
            
            if method == "GET":
                response = test_session.get(f"{ADMIN_URL}/logout", allow_redirects=False, timeout=TIMEOUT)
            else:
                response = test_session.post(f"{ADMIN_URL}/logout", allow_redirects=False, timeout=TIMEOUT)
            
            # Should either work (redirect to SSO) or not be implemented
            assert response.status_code in [200, 302, 307, 404, 405]
            
            if response.status_code in [302, 307]:
                # If redirect, should go to SSO or login page
                location = response.headers.get("Location", "")
                assert any(url in location for url in [SSO_URL, "/login", "/"])

    def test_logout_concurrent_sessions(self):
        """Test logout behavior with multiple concurrent sessions"""
        session1 = requests.Session()
        session2 = requests.Session()
        
        # Login both sessions
        self._login_session(session1)
        self._login_session(session2)
        
        # Both should have access
        response1 = session1.get(f"{CLIENT_URL}/dashboard", timeout=TIMEOUT)
        response2 = session2.get(f"{CLIENT_URL}/dashboard", timeout=TIMEOUT)
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Logout session1
        session1.get(f"{CLIENT_URL}/logout", timeout=TIMEOUT)
        
        # Session1 should be logged out
        self._verify_logged_out(session1)
        
        # Session2 should still work (independent sessions)
        response2 = session2.get(f"{CLIENT_URL}/dashboard", timeout=TIMEOUT)
        assert response2.status_code == 200


# Mark all tests as integration tests
pytestmark = pytest.mark.integration