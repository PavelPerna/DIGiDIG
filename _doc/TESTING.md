# DIGiDIG CI/CD Testing Infrastructure

Tento dokument popisuje kompletní testovací infrastrukturu a CI/CD pipeline pro DIGiDIG.

## 📁 Test Organization

All tests have been centralized into the `tests/` directory:

```
tests/
├── unit/                           # Unit tests
│   └── test_config.py             # Configuration loading tests
├── integration/                    # Integration tests
│   ├── test_all_services_config.py     # Comprehensive service configuration tests
│   ├── test_smtp_config_persistence.py # SMTP persistence tests
│   ├── test_admin_service.py           # Admin service tests (moved from admin/tests/)
│   ├── test_identity_integration.py    # Identity service integration tests
│   ├── test_identity_unit.py           # Identity service unit tests
│   └── test_smtp_imap_flow.py          # SMTP/IMAP flow tests
├── run_tests.py                    # Centralized test runner
├── requirements-test.txt           # Test dependencies
└── Dockerfile                      # Test environment
```

## 🚀 Running Tests

### Quick Start

```bash
# Install test dependencies
make test-install

# Run all tests
make test

# Run quick tests only (unit + basic integration)
make test-quick
```

### Test Categories

```bash
# Unit tests only
make test-unit

# Integration tests only
make test-integration

# Configuration tests
make test-config

# Persistence tests
make test-persistence

# Build environment and run tests
make test-build
```

### Using the Test Runner Directly

```bash
cd tests

# Run all tests
python run_tests.py all

# Run specific category
python run_tests.py unit
python run_tests.py integration
python run_tests.py quick
```

## 🧪 Test Types

### 1. Unit Tests
- **Location**: `tests/unit/`
- **Purpose**: Test individual components in isolation
- **Speed**: Fast (< 1 second each)
- **Examples**: Configuration loading, utility functions

### 2. Integration Tests
- **Location**: `tests/integration/`
- **Purpose**: Test service interactions and end-to-end flows
- **Speed**: Slower (few seconds each)
- **Examples**: API endpoints, service communication, data persistence

### 3. Configuration Tests
- **File**: `test_all_services_config.py`
- **Tests**:
  - All services health checks
  - Configuration endpoint accessibility
  - Inter-service communication
  - API documentation availability
  - Volume persistence indicators

### 4. Persistence Tests
- **File**: `test_smtp_config_persistence.py`
- **Tests**:
  - Configuration updates
  - Persistence across service restarts
  - Docker integration

## 📊 Test Reports

Tests generate comprehensive reports:

- **HTML Report**: `reports/pytest_report.html`
- **JSON Report**: `reports/pytest_report.json`
- **Coverage Report**: `htmlcov/index.html`

```bash
# Generate reports directory
make test-reports

# Clean test artifacts
make test-clean
```

## ⚙️ Test Configuration

### pytest Configuration
- **File**: `pyproject.toml`
- **Features**:
  - Coverage reporting
  - HTML and JSON reports
  - Custom markers
  - Filtering warnings

### Test Markers
```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.persistence   # Tests data persistence
@pytest.mark.config        # Tests configuration
@pytest.mark.auth          # Tests authentication
@pytest.mark.email         # Tests email functionality
@pytest.mark.slow          # Slow tests
```

### Running Tests with Markers
```bash
# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run only configuration tests
pytest -m config
```

## 🐳 Docker Integration

### Test Environment
Tests run against services in Docker containers:

```bash
# Ensure services are running
docker compose up -d

# Run tests
make test-build
```

### Service Endpoints
Tests automatically detect services on:
- Identity: http://localhost:8001
- SMTP: http://localhost:8000
- IMAP: http://localhost:8003
- Storage: http://localhost:8002
- Client: http://localhost:8004
- Admin: http://localhost:8005
- APIDocs: http://localhost:8010

## 🔧 Writing New Tests

### Test File Structure
```python
"""
Description of test module.
"""

import pytest
import requests
import logging

logger = logging.getLogger(__name__)

class TestServiceName:
    """Test class for specific service."""
    
    def test_feature_name(self):
        """Test specific feature."""
        # Test implementation
        assert True
        logger.info("✅ Test passed")
```

### Best Practices
1. **Use descriptive test names**: `test_smtp_config_persistence_across_restart`
2. **Add logging**: Help debug failures
3. **Clean up**: Restore original state after tests
4. **Use fixtures**: Share common setup
5. **Mark tests**: Use appropriate pytest markers

### Adding New Service Tests
1. Create test file: `tests/integration/test_new_service.py`
2. Add to test runner: Update `TEST_CATEGORIES` in `run_tests.py`
3. Add service config: Update `SERVICES` in `test_all_services_config.py`

## 🔍 Troubleshooting

### Common Issues

**Services Not Ready**
```bash
# Wait for services
docker compose up -d
sleep 10
make test
```

**Permission Issues**
```bash
# Fix permissions
chmod +x tests/run_tests.py
```

**Import Errors**
```bash
# Install dependencies
make test-install
```

### Debug Mode
```bash
# Run with detailed output
cd tests
python -m pytest -v -s --tb=long integration/test_all_services_config.py
```

### Test Individual Components
```bash
# Test specific service
curl http://localhost:8000/health

# Test configuration endpoint
curl http://localhost:8000/api/config
```

## 📈 Continuous Integration

Tests are integrated into CI/CD pipeline:

- **GitHub Actions**: `.github/workflows/`
- **Automatic Testing**: On pull requests
- **Coverage Reports**: Generated and stored
- **Quality Gates**: Tests must pass for deployment

## 🎯 Test Coverage Goals

- **Unit Tests**: > 80% code coverage
- **Integration Tests**: All API endpoints
- **Configuration Tests**: All services
- **Persistence Tests**: Critical data flows

## 📝 Contributing Tests

When adding new features:

1. **Write tests first** (TDD approach)
2. **Cover happy path and edge cases**
3. **Add integration tests for new endpoints**
4. **Update this documentation**
5. **Ensure tests pass in CI**

## 🏃‍♂️ Performance Testing

For performance tests:
```bash
# Add performance markers
@pytest.mark.performance
def test_high_load():
    pass

# Run performance tests
pytest -m performance
```

---

For questions or issues with testing, please check the logs and ensure all services are running with `docker compose ps`.