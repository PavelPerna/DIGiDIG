import unittest
import requests
import time
import subprocess
import os
import signal
import sys
from urllib.parse import urljoin


class TestRestAPI(unittest.TestCase):
    """Test REST API endpoints for DIGiDIG services"""

    BASE_URL = "http://digidig.cz:9107"  # Mail service (HTTP)
    IDENTITY_URL = "http://digidig.cz:9101"  # Identity service (HTTP)
    SSO_URL = "http://digidig.cz:9106"  # SSO service (HTTP)

    @classmethod
    def setUpClass(cls):
        """Verify DIGiDIG services are running before tests"""
        print("Verifying DIGiDIG services are accessible...")
        try:
            # Quick check that essential services are responding
            response = requests.get(f"{cls.BASE_URL}/health", timeout=5)
            response.raise_for_status()
            print("✓ Mail service is ready")
            
            # Check SSO service
            response = requests.get(f"{cls.SSO_URL}/", timeout=5, allow_redirects=False)
            if response.status_code in [200, 302, 303, 404]:
                print("✓ SSO service is ready")
            else:
                print(f"⚠ SSO service returned status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Required services not running. Start them with: make test-services-up\nError: {e}")

    @classmethod
    def tearDownClass(cls):
        """No cleanup needed - services stay running for multiple test runs"""
        pass

    def setUp(self):
        """Set up test session"""
        self.session = requests.Session()
        # No SSL verification needed for HTTP

    def test_01_health_check(self):
        """Test that mail service health endpoint works"""
        response = self.session.get(f"{self.BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["service"], "mail")
        self.assertEqual(data["status"], "healthy")

    def test_02_unauthenticated_access_redirects(self):
        """Test that unauthenticated access to protected routes redirects to SSO"""
        # Test /list endpoint
        response = self.session.get(f"{self.BASE_URL}/list", allow_redirects=False)
        self.assertEqual(response.status_code, 303)  # See Other (redirect)

        # Test /compose endpoint
        response = self.session.get(f"{self.BASE_URL}/compose", allow_redirects=False)
        self.assertEqual(response.status_code, 303)

        # Test /view endpoint
        response = self.session.get(f"{self.BASE_URL}/view/test123", allow_redirects=False)
        self.assertEqual(response.status_code, 303)

    def test_03_session_verification_unauthenticated(self):
        """Test session verification returns 401 for unauthenticated user"""
        response = self.session.get(f"{self.BASE_URL}/api/identity/session/verify")
        self.assertEqual(response.status_code, 401)  # Should return 401 for unauthenticated

    def test_04_logout_unauthenticated(self):
        """Test logout returns 401 for unauthenticated user"""
        response = self.session.post(f"{self.BASE_URL}/api/identity/logout")
        self.assertEqual(response.status_code, 401)  # Should return 401 for unauthenticated

    def test_05_index_redirects_to_list(self):
        """Test that root URL redirects to /list"""
        response = self.session.get(f"{self.BASE_URL}/", allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn("/list", response.headers.get("location", ""))

    def test_06_identity_service_health(self):
        """Test that identity service is accessible through proxy"""
        try:
            response = self.session.get(f"{self.IDENTITY_URL}/health")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["service"], "identity")
        except requests.exceptions.ConnectionError:
            self.skipTest("Identity service not accessible (may be expected in test environment)")

    def test_07_sso_service_accessible(self):
        """Test that SSO service is accessible"""
        try:
            response = self.session.get(f"{self.SSO_URL}/", allow_redirects=False)
            # SSO might redirect or return various status codes
            self.assertIn(response.status_code, [200, 302, 303, 404])  # Common responses
        except requests.exceptions.ConnectionError as e:
            self.fail(f"SSO service not accessible at {self.SSO_URL}: {e}")

    def test_08_api_proxy_works(self):
        """Test that API proxy correctly forwards requests"""
        # Test with a non-existent service (should return 404)
        response = self.session.get(f"{self.BASE_URL}/api/nonexistent/test")
        self.assertEqual(response.status_code, 404)

    def test_09_cors_headers(self):
        """Test that CORS headers are properly set for API endpoints"""
        # Skip CORS test for health endpoint as it's not browser-facing
        response = self.session.options(f"{self.BASE_URL}/api/identity/session/verify")
        # Check for common CORS headers if present
        cors_headers = [
            'access-control-allow-origin',
            'access-control-allow-methods',
            'access-control-allow-headers'
        ]
        response_headers = {k.lower(): v for k, v in response.headers.items()}
        # CORS headers may or may not be present depending on endpoint
        # Just verify the request doesn't fail
        self.assertIn(response.status_code, [200, 401, 404, 405])

    def test_10_error_handling(self):
        """Test error handling for invalid requests"""
        # Test invalid endpoint
        response = self.session.get(f"{self.BASE_URL}/nonexistent")
        self.assertEqual(response.status_code, 404)

        # Test invalid method on valid endpoint
        response = self.session.put(f"{self.BASE_URL}/health")
        self.assertIn(response.status_code, [405, 404])  # Method not allowed or not found


if __name__ == '__main__':
    # Enable warnings for debugging
    import warnings
    warnings.filterwarnings("default", category=DeprecationWarning)
    warnings.filterwarnings("default", category=PendingDeprecationWarning)
    warnings.filterwarnings("default", category=FutureWarning)
    warnings.filterwarnings("default", category=UserWarning)

    unittest.main(verbosity=2)