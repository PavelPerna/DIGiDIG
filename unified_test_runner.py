#!/usr/bin/env python3
"""
Unified Docker Test Runner for DIGiDIG
Consolidates all testing mechanisms into a single Docker-based approach.
"""

import os
import sys
import subprocess
import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DigidigTestRunner:
    """Unified test runner that handles all test scenarios via Docker"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent
        self.network_name = None
        self.docker_env_vars = [
            "-e", "IDENTITY_URL=http://identity:8001",
            "-e", "SMTP_URL=http://smtp:8000", 
            "-e", "IMAP_URL=http://imap:8003",
            "-e", "STORAGE_URL=http://storage:8002",
            "-e", "CLIENT_URL=http://client:8004",
            "-e", "ADMIN_URL=http://admin:8005",
            "-e", "APIDOCS_URL=http://apidocs:8010",
            "-e", "BASE_URL=http://identity:8001",
            "-e", "SMTP_HOST=smtp",
            "-e", "SMTP_PORT=2525",
            "-e", "SMTP_REST_URL=http://smtp:8000",
            "-e", "IMAP_HOST=imap",
            "-e", "IMAP_PORT=143",
        ]
    
    def find_docker_network(self):
        """Find DIGiDIG Docker network"""
        try:
            result = subprocess.run(
                ["docker", "network", "ls", "--format", "{{.Name}}"],
                capture_output=True, text=True, check=True
            )
            networks = result.stdout.strip().split('\n')
            for network in networks:
                if 'digidig' in network.lower():
                    self.network_name = network
                    logger.info(f"Found Docker network: {network}")
                    return network
            
            # Fallback
            self.network_name = "digidig_default"
            logger.warning(f"No DIGiDIG network found, using: {self.network_name}")
            return self.network_name
        except subprocess.CalledProcessError:
            logger.error("Failed to find Docker network")
            return None
    
    def check_services_running(self):
        """Check if DIGiDIG services are running"""
        try:
            result = subprocess.run(
                ["docker", "compose", "ps"],
                capture_output=True, text=True, check=True,
                cwd=self.project_root
            )
            return "Up" in result.stdout
        except subprocess.CalledProcessError:
            return False
    
    def start_services(self):
        """Start DIGiDIG services if not running"""
        if not self.check_services_running():
            logger.info("Starting DIGiDIG services...")
            try:
                subprocess.run(
                    ["docker", "compose", "up", "-d"],
                    check=True, cwd=self.project_root
                )
                logger.info("Waiting for services to start...")
                time.sleep(15)
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to start services: {e}")
                return False
        else:
            logger.info("Services are already running")
            return True
    
    def build_test_container(self):
        """Build the test Docker container"""
        logger.info("Building test container...")
        try:
            subprocess.run([
                "docker", "build", 
                "-f", "_test/Dockerfile", 
                "-t", "digidig-tests", 
                "."
            ], check=True, cwd=self.project_root)
            logger.info("✅ Test container built successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to build test container: {e}")
            return False
    
    def run_docker_tests(self, test_command: list = None):
        """Run tests in Docker container"""
        if not self.find_docker_network():
            logger.error("Cannot find Docker network")
            return False
        
        if not self.build_test_container():
            logger.error("Cannot build test container")
            return False
        
        # Default test command
        if test_command is None:
            test_command = ["pytest", "integration/", "-v", "--tb=short"]
        
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", self.network_name
        ] + self.docker_env_vars + [
            "digidig-tests"
        ] + test_command
        
        logger.info(f"Running: {' '.join(test_command)}")
        
        try:
            result = subprocess.run(docker_cmd, cwd=self.project_root)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            logger.error(f"Docker test execution failed: {e}")
            return False

def main():
    """Main entry point with different test categories"""
    
    if len(sys.argv) < 2:
        print("Usage: python unified_test_runner.py <test_category>")
        print("Categories:")
        print("  quick        - Quick health check")
        print("  config       - Configuration tests")
        print("  unit         - Unit tests")
        print("  unit-core    - Core unit tests (isolated)")
        print("  unit-safe    - Safe unit tests (no service deps)")
        print("  rest-unit    - REST API unit tests")
        print("  rest-integration - REST API integration tests")
        print("  rest-all     - All REST API tests")
        print("  integration  - Integration tests")  
        print("  persistence  - Persistence tests")
        print("  admin        - Admin service tests")
        print("  identity     - Identity service tests")
        print("  flow         - Email flow tests")
        print("  all          - All tests")
        print("  coverage     - Integration tests with coverage")
        print("  services     - Start services only")
        sys.exit(1)
    
    category = sys.argv[1]
    runner = DigidigTestRunner()
    
    # Test category mappings
    test_commands = {
        "quick": [
            "pytest", 
            "integration/test_all_services_config.py::TestServiceConfiguration::test_all_services_health", 
            "-v"
        ],
        "config": [
            "pytest", 
            "integration/test_all_services_config.py", 
            "-v"
        ],
        "unit": [
            "pytest", 
            "unit/test_config.py",
            "unit/test_config_loader.py", 
            "unit/test_i18n.py",
            "unit/test_services_structure.py",
            "-v", "--tb=short"
        ],
        "unit-core": [
            "pytest", 
            "unit/test_config.py",
            "unit/test_config_loader.py",
            "unit/test_config_models.py",
            "unit/test_i18n.py",
            "-v", "--tb=short"
        ],
        "unit-safe": [
            "pytest", 
            "unit/test_config.py",
            "unit/test_config_loader.py",
            "unit/test_config_models.py",
            "unit/test_i18n.py", 
            "unit/test_services_structure.py",
            "-v", "--tb=short"
        ],
        "rest-unit": [
            "pytest", 
            "unit/test_rest_api_unit.py",
            "unit/test_rest_api_comprehensive.py",
            "-v", "--tb=short"
        ],
        "rest-integration": [
            "pytest", 
            "integration/test_rest_api_integration.py",
            "-v", "--tb=short"
        ],
        "rest-all": [
            "pytest", 
            "unit/test_rest_api_unit.py",
            "unit/test_rest_api_comprehensive.py",
            "integration/test_rest_api_integration.py",
            "-v", "--tb=short"
        ],
        "integration": [
            "pytest", 
            "integration/", 
            "-v", "--tb=short"
        ],
        "persistence": [
            "pytest", 
            "integration/test_smtp_config_persistence.py", 
            "-v"
        ],
        "admin": [
            "pytest", 
            "integration/test_admin_service.py", 
            "-v"
        ],
        "identity": [
            "pytest", 
            "integration/test_identity_integration.py",
            "integration/test_identity_unit.py", 
            "-v"
        ],
        "flow": [
            "pytest", 
            "integration/test_smtp_imap_flow.py", 
            "-v"
        ],
        "all": [
            "pytest", 
            ".", 
            "-v", "--tb=short"
        ],
        "coverage": [
            "pytest", 
            "integration/", 
            "--cov=services/", 
            "--cov=lib/",
            "--cov-report=html:/app/_test/htmlcov/", 
            "--cov-report=term-missing",
            "-v", "--tb=short"
        ],
        "coverage-all": [
            "pytest", 
            "unit/", "integration/", 
            "--cov=lib/",
            "--cov-report=html:/app/_test/htmlcov/", 
            "--cov-report=term-missing",
            "-v", "--tb=short"
        ],
    }
    
    if category == "services":
        logger.info("🚀 Starting DIGiDIG services...")
        if runner.start_services():
            logger.info("✅ Services started successfully")
            sys.exit(0)
        else:
            logger.error("❌ Failed to start services")
            sys.exit(1)
    
    if category not in test_commands:
        logger.error(f"Unknown test category: {category}")
        sys.exit(1)
    
    # Ensure services are running
    if not runner.start_services():
        logger.error("Cannot start services")
        sys.exit(1)
    
    # Run tests
    logger.info(f"🧪 Running {category} tests...")
    success = runner.run_docker_tests(test_commands[category])
    
    if success:
        logger.info("✅ Tests completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()