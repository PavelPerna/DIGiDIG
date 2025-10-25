# Common Module

Shared utilities and configuration management for DIGiDIG services.

## Installation

Add to your service's `requirements.txt`:

```
# Add common module to Python path
-e ../common
```

Or install directly:

```bash
pip install -r common/requirements.txt
```

## Usage

### Configuration Management

```python
from common import get_config, get_db_config, get_service_url

# Get full config object
config = get_config()

# Access nested values
db_host = config.get("database.postgres.host")
jwt_secret = config.get("security.jwt.secret")

# Use convenience functions
db_config = get_db_config("postgres")
storage_url = get_service_url("storage")
```

## Module Structure

```
common/
├── __init__.py         # Public API exports
├── config.py           # Configuration management
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## Dependencies

- PyYAML >= 6.0

## Documentation

See [Configuration Management](../docs/CONFIGURATION.md) for detailed usage guide.
