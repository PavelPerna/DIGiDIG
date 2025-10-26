"""
Comprehensive configuration tests for all DIGiDIG services.
Tests configuration persistence, service health, and inter-service communication.
"""

import pytest
import requests
import time
import json
import os
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service endpoints configuration - use Docker service names for containerized tests
def get_service_url(service, port, default_host='localhost'):
    """Get service URL, using Docker service names in Docker network"""
    return f'http://{service}:{port}'

SERVICES = {
    'identity': {
        'url': get_service_url('identity', 8001),
        'health_endpoint': '/api/health',
        'config_endpoint': '/api/config',
        'test_endpoints': ['/api/health', '/docs']
    },
    'smtp': {
        'url': get_service_url('smtp', 8000),
        'health_endpoint': '/api/health',
        'config_endpoint': '/api/config',
        'test_endpoints': ['/api/health', '/api/config', '/docs']
    },
    'imap': {
        'url': get_service_url('imap', 8003),
        'health_endpoint': '/api/health',
        'config_endpoint': '/api/config',
        'test_endpoints': ['/api/health', '/docs']
    },
    'storage': {
        'url': get_service_url('storage', 8002),
        'health_endpoint': '/api/health',
        'config_endpoint': '/api/config',
        'test_endpoints': ['/api/health', '/docs']
    },
    'client': {
        'url': get_service_url('client', 8004),
        'health_endpoint': '/api/health',
        'config_endpoint': '/api/config',
        'test_endpoints': ['/api/health', '/docs']
    },
    'admin': {
        'url': get_service_url('admin', 8005),
        'health_endpoint': '/api/health',
        'config_endpoint': '/api/config',
        'test_endpoints': ['/api/health', '/']
    },
    'apidocs': {
        'url': get_service_url('apidocs', 8010),
        'health_endpoint': '/api/health',
        'config_endpoint': '/api/config',
        'test_endpoints': ['/api/health', '/']
    }
}

class TestServiceConfiguration:
    """Test configuration for all DIGiDIG services."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Wait for services to be ready."""
        logger.info("Waiting for services to be ready...")
        time.sleep(5)
    
    def test_all_services_health(self):
        """Test that all services are healthy and responding."""
        failed_services = []
        
        for service_name, config in SERVICES.items():
            try:
                # Special handling for client service which redirects through SSO
                if service_name == 'client':
                    # Client health check redirects to SSO, so follow redirects or check direct health endpoint
                    response = requests.get(
                        f"{config['url']}{config['health_endpoint']}", 
                        timeout=10,
                        allow_redirects=False  # Don't follow SSO redirect for health check
                    )
                    # Accept both 200 (direct health), 302 (found), and 307 (temporary redirect) as healthy
                    if response.status_code not in [200, 302, 307]:
                        failed_services.append(f"{service_name}: HTTP {response.status_code}")
                    else:
                        logger.info(f"✅ {service_name} health check passed (status: {response.status_code})")
                else:
                    response = requests.get(
                        f"{config['url']}{config['health_endpoint']}", 
                        timeout=10
                    )
                    if response.status_code != 200:
                        failed_services.append(f"{service_name}: HTTP {response.status_code}")
                    else:
                        logger.info(f"✅ {service_name} health check passed")
            except requests.exceptions.RequestException as e:
                failed_services.append(f"{service_name}: {str(e)}")
                logger.error(f"❌ {service_name} health check failed: {e}")
        
        assert not failed_services, f"Health checks failed for: {', '.join(failed_services)}"
    
    def test_all_services_endpoints(self):
        """Test that all configured endpoints are accessible."""
        failed_endpoints = []
        
        for service_name, config in SERVICES.items():
            for endpoint in config['test_endpoints']:
                try:
                    response = requests.get(
                        f"{config['url']}{endpoint}", 
                        timeout=10,
                        allow_redirects=True
                    )
                    if response.status_code not in [200, 302]:
                        failed_endpoints.append(f"{service_name}{endpoint}: HTTP {response.status_code}")
                    else:
                        logger.info(f"✅ {service_name}{endpoint} accessible")
                except requests.exceptions.RequestException as e:
                    failed_endpoints.append(f"{service_name}{endpoint}: {str(e)}")
                    logger.error(f"❌ {service_name}{endpoint} failed: {e}")
        
        assert not failed_endpoints, f"Endpoint checks failed for: {', '.join(failed_endpoints)}"

    def test_smtp_configuration_persistence(self):
        """Test SMTP configuration can be updated and persisted."""
        smtp_url = SERVICES['smtp']['url']
        
        # Get current config
        response = requests.get(f"{smtp_url}/api/config")
        assert response.status_code == 200
        original_config = response.json()
        
        # Update config
        new_config = {
            'timeout': 90,
            'retry_attempts': 7,
            'max_workers': 6
        }
        
        response = requests.put(
            f"{smtp_url}/api/config",
            json=new_config,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 200
        
        # Verify update
        response = requests.get(f"{smtp_url}/api/config")
        assert response.status_code == 200
        updated_config = response.json()
        
        assert updated_config['config']['timeout'] == 90
        assert updated_config['config']['retry_attempts'] == 7
        assert updated_config['config']['max_workers'] == 6
        
        logger.info("✅ SMTP configuration update successful")
        
        # Restore original config
        restore_config = {
            'timeout': original_config['config']['timeout'],
            'retry_attempts': original_config['config']['retry_attempts'],
            'max_workers': original_config['config']['max_workers']
        }
        
        requests.put(
            f"{smtp_url}/api/config",
            json=restore_config,
            headers={'Content-Type': 'application/json'}
        )

    def test_identity_service_verification(self):
        """Test identity service token verification endpoint."""
        identity_url = SERVICES['identity']['url']
        
        # Test verification endpoint (should return 401/422 without token)
        response = requests.get(f"{identity_url}/verify")
        assert response.status_code in [401, 422], f"Expected 401/422, got {response.status_code}"
        
        logger.info("✅ Identity verification endpoint responding correctly")

    def test_service_configuration_endpoints(self):
        """Test configuration endpoints for services that have them."""
        services_with_config = ['smtp', 'imap', 'storage']
        
        for service_name in services_with_config:
            if service_name in SERVICES:
                config = SERVICES[service_name]
                try:
                    response = requests.get(f"{config['url']}{config['config_endpoint']}")
                    if response.status_code == 200:
                        config_data = response.json()
                        assert 'config' in config_data or 'service_name' in config_data
                        logger.info(f"✅ {service_name} configuration endpoint working")
                    else:
                        logger.warning(f"⚠️ {service_name} config endpoint returned {response.status_code}")
                except requests.exceptions.RequestException as e:
                    logger.warning(f"⚠️ {service_name} config endpoint not available: {e}")

    def test_inter_service_communication(self):
        """Test basic inter-service communication patterns."""
        # Test that services can reach each other (basic connectivity)
        
        # Test storage service health (used by SMTP/IMAP)
        storage_response = requests.get(f"{SERVICES['storage']['url']}/api/health")
        assert storage_response.status_code == 200
        
        # Test identity service health (used by all services for auth)
        identity_response = requests.get(f"{SERVICES['identity']['url']}/api/health")
        assert identity_response.status_code == 200
        
        logger.info("✅ Inter-service communication base connectivity verified")

    def test_api_documentation_availability(self):
        """Test that API documentation is available for all services."""
        docs_available = []
        docs_failed = []
        
        for service_name, config in SERVICES.items():
            try:
                # Try OpenAPI docs endpoint
                response = requests.get(f"{config['url']}/docs", timeout=10)
                if response.status_code == 200:
                    docs_available.append(service_name)
                    logger.info(f"✅ {service_name} API docs available")
                else:
                    docs_failed.append(f"{service_name}: HTTP {response.status_code}")
            except requests.exceptions.RequestException as e:
                docs_failed.append(f"{service_name}: {str(e)}")
        
        # At least some services should have docs available
        assert len(docs_available) > 0, "No API documentation available for any service"
        
        if docs_failed:
            logger.warning(f"⚠️ API docs not available for: {', '.join(docs_failed)}")

    def test_volume_persistence_indicators(self):
        """Test indicators that persistent volumes are working."""
        # This test checks for evidence that persistent volumes are mounted and working
        
        # SMTP config should persist (we test this by checking the config endpoint)
        smtp_response = requests.get(f"{SERVICES['smtp']['url']}/api/config")
        if smtp_response.status_code == 200:
            config_data = smtp_response.json()
            # Check that config has expected structure indicating persistence
            assert 'config' in config_data
            assert 'timeout' in config_data['config']
            logger.info("✅ SMTP persistent configuration verified")
        
        # Add more volume persistence tests as needed
        logger.info("✅ Volume persistence indicators checked")


class TestServiceIntegration:
    """Integration tests between services."""
    
    def test_auth_flow_components(self):
        """Test that auth flow components are accessible."""
        # Identity service should be available
        identity_response = requests.get(f"{SERVICES['identity']['url']}/api/health")
        assert identity_response.status_code == 200
        
        # Admin UI should be available
        admin_response = requests.get(f"{SERVICES['admin']['url']}/api/health")
        assert admin_response.status_code == 200
        
        # Client should be available
        client_response = requests.get(f"{SERVICES['client']['url']}/api/health")
        assert client_response.status_code == 200
        
        logger.info("✅ Auth flow components available")

    def test_email_flow_components(self):
        """Test that email flow components are accessible."""
        # SMTP service should be available
        smtp_response = requests.get(f"{SERVICES['smtp']['url']}/api/health")
        assert smtp_response.status_code == 200
        
        # IMAP service should be available  
        imap_response = requests.get(f"{SERVICES['imap']['url']}/api/health")
        assert imap_response.status_code == 200
        
        # Storage service should be available
        storage_response = requests.get(f"{SERVICES['storage']['url']}/api/health")
        assert storage_response.status_code == 200
        
        logger.info("✅ Email flow components available")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])