"""
Admin service integration tests - moved from admin/tests/
Tests admin authentication and user management functionality.
"""

import pytest
import requests
import sys
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_service_url(service, port, default_host='localhost'):
    """Get service URL, preferring Docker service names in containerized environment"""
    if os.getenv('SKIP_COMPOSE') == '1':  # Running in Docker test container
        return f'http://{service}:{port}'
    return f'http://{default_host}:{port}'

ADMIN_URL = get_service_url('admin', 8005)


class TestAdminService:
    """Test admin service functionality."""
    
    def api_login(self, email, password):
        """Helper method for admin login."""
        response = requests.post(
            f"{ADMIN_URL}/api/login", 
            json={"email": email, "password": password}
        )
        return response

    def manage_user(self, token, username, domain="example.com", role="user", password="TempPass1!"):
        """Helper method for user management."""
        data = {
            'username': username,
            'domain': domain,
            'role': role,
            'password': password
        }
        # Send token as cookie (not form data)
        cookies = {'access_token': token}
        response = requests.post(f"{ADMIN_URL}/manage-user", data=data, cookies=cookies)
        return response

    def test_admin_login_success(self):
        """Test successful admin login with seeded credentials."""
        login_resp = self.api_login('admin@example.com', 'admin')
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        response_data = login_resp.json()
        assert 'access_token' in response_data, "Access token not in response"
        
        logger.info("✅ Admin login successful")

    def test_admin_login_failure(self):
        """Test admin login with invalid credentials."""
        login_resp = self.api_login('admin@example.com', 'wrongpassword')
        assert login_resp.status_code != 200, "Login should fail with wrong password"
        
        logger.info("✅ Admin login correctly rejects invalid credentials")

    def test_user_management_flow(self):
        """Test complete user management flow: create, duplicate handling."""
        # Login as admin
        login_resp = self.api_login('admin@example.com', 'admin')
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        token = login_resp.json().get('access_token')
        assert token, "No access token received"
        
        # Create new user
        username = 'itestuser'
        create_resp1 = self.manage_user(token, username)
        logger.info(f"First create: {create_resp1.status_code} - {create_resp1.text}")
        
        # The first create might succeed or fail depending on if user exists
        # What's important is the duplicate handling
        
        # Try to create duplicate user
        create_resp2 = self.manage_user(token, username)
        logger.info(f"Duplicate create: {create_resp2.status_code} - {create_resp2.text}")
        
        # Duplicate creation should return 400
        assert create_resp2.status_code == 400, f"Duplicate user should return 400, got {create_resp2.status_code}"
        
        logger.info("✅ User management flow working correctly")

    def test_admin_health_check(self):
        """Test admin service health endpoint."""
        response = requests.get(f"{ADMIN_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        logger.info("✅ Admin service health check passed")

    def test_admin_dashboard_access(self):
        """Test admin dashboard accessibility."""
        response = requests.get(f"{ADMIN_URL}/", allow_redirects=False)
        # Dashboard might redirect to login, which is expected (302, 307)
        assert response.status_code in [200, 302, 307], f"Dashboard access failed: {response.status_code}"
        
        logger.info("✅ Admin dashboard accessible")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])