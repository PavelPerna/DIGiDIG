# DIGiDIG Core

Shared core infrastructure and base classes for DIGiDIG services.

## Installation

```bash
pip install -e .
```

## Usage

```python
from digidig_core.models.service.server import ServiceServer

# Create a service
service = ServiceServer(
    name="my-service",
    description="My DIGiDIG service",
    port=8080
)

# Get the FastAPI app
app = service.get_app()
```

## Components

- **Service Base Classes**: Common service infrastructure
- **Configuration Management**: Shared configuration utilities
- **Models**: Data models and schemas
- **Utilities**: Common utility functions

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
isort .
```