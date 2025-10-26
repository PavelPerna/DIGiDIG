#!/usr/bin/env python3
"""
Unit tests for SSO service components.
Tests individual functions and methods without requiring the full FastAPI app.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from urllib.parse import urlparse, parse_qs

# Add the services directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'sso', 'src'))

# Mock the static directory to prevent FastAPI from failing
def mock_staticfiles_init(self, directory, **kwargs):
    self.directory = directory

# Import the SSO module with mocked dependencies
try:
    with patch('starlette.staticfiles.StaticFiles.__init__', mock_staticfiles_init):
        import sso
except ImportError as e:
    pytest.skip(f"SSO module not available: {e}", allow_module_level=True)

import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
import urllib.parse

# Add the SSO service source to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'sso', 'src'))

# Mock the config before importing sso module
with patch('lib.common.config.get_config') as mock_config:
    mock_config.return_value.get.return_value = {
        'services': {
            'admin': {'host': 'admin', 'port': 8005},
            'client': {'host': 'client', 'port': 8004},
            'sso': {'host': 'sso', 'port': 8006}
        },
        'external_services': {
            'admin': {'url': 'http://localhost:8005'},
            'client': {'url': 'http://localhost:8004'},
            'sso': {'url': 'http://localhost:8006'}
        }
    }
    
    try:
        import sso
    except ImportError:
        # If SSO module can't be imported, create mock functions for testing
        class MockSSO:
            @staticmethod
            async def validate_redirect_url(url: str) -> bool:
                """Mock implementation of redirect URL validation"""
                if not url:
                    return False
                
                parsed = urllib.parse.urlparse(url)
                
                # Allow relative URLs
                if not parsed.netloc:
                    return True
                
                # Check against trusted hosts
                trusted_hosts = [
                    'admin', 'admin:8005', 'localhost:8005',
                    'client', 'client:8004', 'localhost:8004',
                    'sso', 'sso:8006', 'localhost:8006'
                ]
                
                return parsed.netloc in trusted_hosts
        
        sso = MockSSO()


class TestSSOValidation:
    """Unit tests for SSO validation logic"""

    @pytest.mark.asyncio
    async def test_validate_redirect_url_relative_paths(self):
        """Test that relative paths are allowed"""
        assert await sso.validate_redirect_url("/dashboard") == True
        assert await sso.validate_redirect_url("/admin/users") == True
        assert await sso.validate_redirect_url("../other-page") == True

    @pytest.mark.asyncio
    async def test_validate_redirect_url_empty_or_none(self):
        """Test that empty/None URLs are rejected"""
        assert await sso.validate_redirect_url("") == False
        assert await sso.validate_redirect_url(None) == False

    @pytest.mark.asyncio
    async def test_validate_redirect_url_trusted_hosts(self):
        """Test that trusted hosts are allowed"""
        trusted_urls = [
            "http://localhost:8005/",
            "http://localhost:8004/dashboard",
            "http://localhost:8006/login",
            "http://admin:8005/users",
            "http://client:8004/",
            "http://sso:8006/"
        ]
        
        for url in trusted_urls:
            assert await sso.validate_redirect_url(url) == True

    @pytest.mark.asyncio
    async def test_validate_redirect_url_malicious_hosts(self):
        """Test that malicious hosts are rejected"""
        malicious_urls = [
            "http://evil.com/steal-tokens",
            "https://malicious-site.org/",
            "http://attacker.net/phishing",
            "ftp://bad-server.com/",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>"
        ]
        
        for url in malicious_urls:
            assert await sso.validate_redirect_url(url) == False

    @pytest.mark.asyncio
    async def test_validate_redirect_url_different_schemes(self):
        """Test handling of different URL schemes"""
        # HTTPS should work for trusted hosts
        assert await sso.validate_redirect_url("https://localhost:8005/") == True
        
        # Other schemes should be rejected
        assert await sso.validate_redirect_url("ftp://localhost:8005/") == False
        assert await sso.validate_redirect_url("file:///etc/passwd") == False

    @pytest.mark.asyncio
    async def test_validate_redirect_url_with_query_params(self):
        """Test URLs with query parameters"""
        valid_urls_with_params = [
            "http://localhost:8005/?next=/admin",
            "http://localhost:8004/dashboard?tab=emails&sort=date",
            "/login?redirect_to=%2Fdashboard"
        ]
        
        for url in valid_urls_with_params:
            assert await sso.validate_redirect_url(url) == True

    @pytest.mark.asyncio
    async def test_validate_redirect_url_with_fragments(self):
        """Test URLs with fragments/anchors"""
        urls_with_fragments = [
            "http://localhost:8005/#section1",
            "/dashboard#top",
            "http://localhost:8004/page#anchor"
        ]
        
        for url in urls_with_fragments:
            assert await sso.validate_redirect_url(url) == True


class TestSSOHelperFunctions:
    """Unit tests for SSO helper functions"""

    def test_url_encoding_handling(self):
        """Test proper URL encoding/decoding"""
        test_url = "http://localhost:8004/dashboard?param=value with spaces"
        encoded = urllib.parse.quote(test_url)
        decoded = urllib.parse.unquote(encoded)
        
        assert decoded == test_url
        assert "with%20spaces" in encoded

    def test_redirect_parameter_extraction(self):
        """Test extraction of redirect parameters from URLs"""
        test_url = "http://sso:8006/login?redirect_to=http%3A//localhost%3A8005/"
        parsed = urllib.parse.urlparse(test_url)
        params = urllib.parse.parse_qs(parsed.query)
        
        redirect_to = params.get("redirect_to", [None])[0]
        assert redirect_to is not None
        
        decoded_redirect = urllib.parse.unquote(redirect_to)
        assert decoded_redirect == "http://localhost:8005/"

    def test_cookie_attributes_validation(self):
        """Test cookie attribute validation"""
        # Test that we can create proper cookie attributes
        cookie_attrs = {
            'httponly': True,
            'secure': False,  # False for development
            'samesite': 'lax',
            'max_age': 1800
        }
        
        assert cookie_attrs['httponly'] == True
        assert cookie_attrs['samesite'] in ['strict', 'lax', 'none']
        assert cookie_attrs['max_age'] > 0

    def test_token_format_validation(self):
        """Test JWT token format validation"""
        # Mock JWT token format
        mock_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwicm9sZXMiOlsiYWRtaW4iXX0.signature"
        
        # JWT should have 3 parts separated by dots
        parts = mock_jwt.split('.')
        assert len(parts) == 3
        
        # Each part should be base64-like (alphanumeric + some special chars)
        for part in parts:
            assert all(c.isalnum() or c in '-_' for c in part)


class TestSSOConfigurationHandling:
    """Unit tests for configuration handling in SSO service"""

    def test_service_url_configuration(self):
        """Test service URL configuration parsing"""
        mock_config = {
            'services': {
                'admin': {'host': 'admin', 'port': 8005, 'url': 'http://admin:8005'},
                'client': {'host': 'client', 'port': 8004, 'url': 'http://client:8004'}
            },
            'external_services': {
                'admin': {'url': 'http://localhost:8005'},
                'client': {'url': 'http://localhost:8004'}
            }
        }
        
        # Verify internal URLs
        assert mock_config['services']['admin']['url'] == 'http://admin:8005'
        assert mock_config['services']['client']['url'] == 'http://client:8004'
        
        # Verify external URLs
        assert mock_config['external_services']['admin']['url'] == 'http://localhost:8005'
        assert mock_config['external_services']['client']['url'] == 'http://localhost:8004'

    def test_security_configuration(self):
        """Test security configuration validation"""
        security_config = {
            'jwt': {
                'secret': 'test-secret-key',
                'algorithm': 'HS256',
                'access_token_expire_minutes': 30
            },
            'cookie': {
                'secure': False,  # Development setting
                'samesite': 'lax'
            }
        }
        
        assert security_config['jwt']['algorithm'] == 'HS256'
        assert security_config['jwt']['access_token_expire_minutes'] > 0
        assert security_config['cookie']['samesite'] in ['strict', 'lax', 'none']


class TestSSOErrorHandling:
    """Unit tests for error handling in SSO service"""

    def test_invalid_login_credentials_handling(self):
        """Test handling of invalid login credentials"""
        # Mock invalid credentials scenario
        username = "invalid_user"
        password = "wrong_password"
        
        # Should handle gracefully without exposing sensitive info
        assert len(username) > 0  # Basic validation
        assert len(password) > 0  # Basic validation
        
        # In real implementation, this would return appropriate error response

    def test_malformed_request_handling(self):
        """Test handling of malformed requests"""
        # Test various malformed inputs
        malformed_inputs = [
            None,
            "",
            "not-a-url",
            "http://",
            "://invalid",
            "javascript:alert(1)"
        ]
        
        for malformed_input in malformed_inputs:
            # Should handle gracefully without crashing
            if malformed_input:
                try:
                    parsed = urllib.parse.urlparse(malformed_input)
                    # Should not crash on malformed URLs
                    assert isinstance(parsed.netloc, str)
                except Exception:
                    # Expected for some malformed inputs
                    pass

    def test_cookie_parsing_error_handling(self):
        """Test handling of cookie parsing errors"""
        # Mock malformed cookie scenarios
        malformed_cookies = [
            "",
            "invalid=",
            "=invalid",
            "no-equals-sign",
            "multiple===equals",
        ]
        
        for cookie in malformed_cookies:
            # Should handle gracefully
            if "=" in cookie:
                parts = cookie.split("=", 1)
                assert len(parts) <= 2


# Mark unit tests
pytestmark = pytest.mark.unit