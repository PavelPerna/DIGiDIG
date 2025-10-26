"""
SMTP Configuration Persistence Tests - moved from root directory
Tests SMTP configuration persistence across service restarts with Docker integration.
"""

import pytest
import requests
import json
import time
import subprocess
import logging
import os
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_service_url(service, port, default_host='localhost'):
    """Get service URL, preferring Docker service names in containerized environment"""
    if os.getenv('SKIP_COMPOSE') == '1':  # Running in Docker test container
        return f'http://{service}:{port}'
    return f'http://{default_host}:{port}'

SMTP_URL = get_service_url('smtp', 8000)
COMPOSE_PATH = "/home/pavel/DIGiDIG"


class TestSMTPConfigPersistence:
    """Test SMTP configuration persistence across service restarts."""
    
    def test_smtp_config_get(self):
        """Test getting SMTP configuration."""
        response = requests.get(f"{SMTP_URL}/api/config")
        assert response.status_code == 200, f"Error getting config: {response.status_code}"
        
        config_data = response.json()
        assert 'config' in config_data, "Response should contain 'config' key"
        assert 'service_name' in config_data, "Response should contain 'service_name' key"
        
        logger.info("✅ SMTP configuration retrieval successful")

    def test_smtp_config_update(self):
        """Test updating SMTP configuration."""
        # Get original config
        response = requests.get(f"{SMTP_URL}/api/config")
        assert response.status_code == 200
        original_config = response.json()
        
        # Update config with new values
        new_config = {
            "retry_attempts": 5,  # Changed from default 3
            "timeout": 60,        # Changed from default 30
            "max_workers": 8      # Changed from default 4
        }
        
        response = requests.put(f"{SMTP_URL}/api/config", json=new_config)
        assert response.status_code == 200, f"Error updating config: {response.status_code} - {response.text}"
        
        # Verify the changes are applied
        response = requests.get(f"{SMTP_URL}/api/config")
        assert response.status_code == 200
        
        updated_config = response.json()
        config_data = updated_config.get("config", {})
        
        assert config_data.get("retry_attempts") == 5, f"Expected retry_attempts=5, got {config_data.get('retry_attempts')}"
        assert config_data.get("timeout") == 60, f"Expected timeout=60, got {config_data.get('timeout')}"
        assert config_data.get("max_workers") == 8, f"Expected max_workers=8, got {config_data.get('max_workers')}"
        
        logger.info("✅ SMTP configuration update successful")
        
        # Restore original config for cleanup
        restore_config = {
            "retry_attempts": original_config["config"]["retry_attempts"],
            "timeout": original_config["config"]["timeout"],
            "max_workers": original_config["config"]["max_workers"]
        }
        requests.put(f"{SMTP_URL}/api/config", json=restore_config)

    def test_smtp_config_persistence_across_restart(self):
        """Test that SMTP configuration persists across service restarts."""
        # Skip this test in Docker test environment since we can't restart services
        if os.environ.get("SKIP_COMPOSE"):
            pytest.skip("Skipping restart test in Docker test environment")
            
        # Get original config
        response = requests.get(f"{SMTP_URL}/api/config")
        assert response.status_code == 200
        original_config = response.json()

        # Update config with test values
        test_config = {
            "retry_attempts": 7,  # Unique test value
            "timeout": 90,        # Unique test value
            "max_workers": 6      # Unique test value
        }

        logger.info(f"Updating config to test values: {test_config}")
        response = requests.put(f"{SMTP_URL}/api/config", json=test_config)
        assert response.status_code == 200, f"Error updating config: {response.status_code} - {response.text}"

        # Verify update was applied
        response = requests.get(f"{SMTP_URL}/api/config")
        assert response.status_code == 200
        config_data = response.json().get("config", {})
        assert config_data.get("retry_attempts") == 7
        assert config_data.get("timeout") == 90
        assert config_data.get("max_workers") == 6

        logger.info("✅ Test configuration applied, restarting service...")

        # Restart SMTP service
        self._restart_smtp_service()        # Wait for service to be ready
        self._wait_for_service_ready()
        
        # Check if configuration persisted
        logger.info("Checking if configuration persisted after restart...")
        response = requests.get(f"{SMTP_URL}/api/config")
        assert response.status_code == 200, f"Error getting config after restart: {response.status_code}"
        
        persisted_config = response.json()
        config_data = persisted_config.get("config", {})
        
        # Verify persistence
        assert config_data.get("retry_attempts") == 7, f"Expected retry_attempts=7, got {config_data.get('retry_attempts')}"
        assert config_data.get("timeout") == 90, f"Expected timeout=90, got {config_data.get('timeout')}"
        assert config_data.get("max_workers") == 6, f"Expected max_workers=6, got {config_data.get('max_workers')}"
        
        logger.info("✅ Configuration successfully persisted after restart!")
        
        # Restore original config
        restore_config = {
            "retry_attempts": original_config["config"]["retry_attempts"],
            "timeout": original_config["config"]["timeout"],
            "max_workers": original_config["config"]["max_workers"]
        }
        response = requests.put(f"{SMTP_URL}/api/config", json=restore_config)
        logger.info("✅ Original configuration restored")

    def _restart_smtp_service(self):
        """Helper method to restart SMTP service."""
        # Stop SMTP service
        result = subprocess.run(
            ["docker", "compose", "stop", "smtp"],
            cwd=COMPOSE_PATH,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to stop SMTP service: {result.stderr}"
        
        # Wait a bit
        time.sleep(2)
        
        # Start SMTP service
        result = subprocess.run(
            ["docker", "compose", "up", "smtp", "-d"],
            cwd=COMPOSE_PATH,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to start SMTP service: {result.stderr}"

    def _wait_for_service_ready(self, max_retries=30, delay=1):
        """Helper method to wait for SMTP service to be ready."""
        logger.info("Waiting for SMTP service to be ready...")
        
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{SMTP_URL}/api/health", timeout=5)
                if response.status_code == 200:
                    logger.info(f"SMTP service ready after {attempt + 1} attempts")
                    return
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(delay)
        
        raise TimeoutError(f"SMTP service not ready after {max_retries} attempts")

    def test_smtp_health_check(self):
        """Test SMTP service health endpoint."""
        response = requests.get(f"{SMTP_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        logger.info("✅ SMTP health check passed")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])