"""
Pytest configuration and fixtures for DIGiDIG testing.
Handles CI vs local environment differences.
"""

import os
import pytest
import asyncio
from pathlib import Path


def pytest_configure(config):
    """Configure pytest based on environment."""
    # Detect CI environment
    is_ci = any([
        os.getenv('CI') == 'true',
        os.getenv('GITHUB_ACTIONS') == 'true',
        os.getenv('GITLAB_CI') == 'true',
    ])
    
    if is_ci:
        print("🚀 Running in CI environment")
        # Set CI-specific markers
        config.addinivalue_line(
            "markers", "ci: mark test to run in CI environment"
        )
        
        # Ensure reports directory exists
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
    else:
        print("🏠 Running in local development environment")


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment and markers."""
    is_ci = os.getenv('CI') == 'true'
    
    if is_ci:
        # In CI, skip tests marked as 'local'
        skip_local = pytest.mark.skip(reason="Skipped in CI environment")
        for item in items:
            if "local" in item.keywords:
                item.add_marker(skip_local)
    
    # Add timeout to all tests in CI
    if is_ci:
        timeout_marker = pytest.mark.timeout(120)  # 2 minutes per test
        for item in items:
            item.add_marker(timeout_marker)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def ci_environment():
    """Fixture to determine if running in CI."""
    return os.getenv('CI') == 'true'


@pytest.fixture(scope="session")
def service_urls():
    """Service URLs for testing."""
    return {
        'identity': 'http://localhost:8001',
        'smtp': 'http://localhost:8000', 
        'imap': 'http://localhost:8003',
        'storage': 'http://localhost:8002',
        'client': 'http://localhost:8004',
        'admin': 'http://localhost:8005',
        'apidocs': 'http://localhost:8010',
    }


@pytest.fixture(scope="function")
def wait_for_services(ci_environment):
    """Wait for services to be ready before tests."""
    import time
    import requests
    
    if ci_environment:
        # In CI, wait a bit longer for services
        time.sleep(10)
    else:
        time.sleep(2)


@pytest.fixture(scope="session")
def test_config():
    """Test configuration based on environment."""
    is_ci = os.getenv('CI') == 'true'
    
    return {
        'timeout': 30 if is_ci else 10,
        'retries': 5 if is_ci else 3,
        'wait_time': 5 if is_ci else 2,
        'max_failures': 3 if is_ci else 1,
        'verbose': is_ci,
    }


# Pytest markers for different test categories
pytest_markers = [
    "unit: Unit tests (fast, no external dependencies)",
    "integration: Integration tests (require services)",
    "slow: Slow tests (may take >30 seconds)",
    "fast: Fast tests (complete in <5 seconds)", 
    "ci: Tests suitable for CI environment",
    "local: Tests that only work in local development",
    "docker: Tests that require Docker services",
    "persistence: Tests that check data persistence",
    "config: Tests that check configuration",
    "auth: Tests related to authentication",
    "email: Tests related to email functionality",
]