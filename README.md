# Cerebro MetaTwin Functions

Function-as-a-Service (FaaS) SDK for the Cerebro MetaTwin platform. This library allows you to easily create and deploy Python functions that can be executed remotely via HTTP endpoints.

## Features

- 🚀 **Simple decorator-based function registration** - Just use `@Function` to mark your functions
- ⚡ **Async-first design** - All functions must be async for optimal performance
- 🔒 **Built-in timeout handling** - Configurable timeouts with sensible defaults
- 📝 **Structured JSON logging** - Production-ready logging with execution tracking
- 🎯 **Type hints and validation** - Full type safety with Pydantic models
- 🛡️ **Graceful error handling** - Comprehensive error responses with stack traces
- 📊 **FastAPI integration** - Modern, fast web framework with automatic API documentation
- 🐰 **RabbitMQ integration** - Event-driven architecture with automatic function registration
- 💚 **Health monitoring** - Periodic health check events for container orchestration
- 🔄 **Graceful degradation** - Works without RabbitMQ if not configured

## Installation

### From Nexus Repository

```bash
# Install from Nexus with PyPI as secondary source for dependencies
pip install cerebro-pkg-metatwin-functions \
  --index-url https://nexus.optime-test-011.cerebro.optime.ai/repository/pypi-default/simple \
  --extra-index-url https://pypi.org/simple
```

Or add to `requirements.txt`:
```
--index-url https://pypi.org/simple
--extra-index-url https://nexus.optime-test-011.cerebro.optime.ai/repository/pypi-default/simple
cerebro-pkg-metatwin-functions==0.0.1
```

### From Source (Development)

```bash
git clone https://github.com/optime-ai/cerebro-pkg-metatwin-functions.git
cd cerebro-pkg-metatwin-functions
pip install -e .
```

**Note:** The package installs as `functions_core` module, not `cerebro_lib_metatwin_functions`.

## Quick Start

### 1. Create your functions

```python
from functions_core import Function  # Note: imports from 'functions_core', not 'cerebro_lib_metatwin_functions'

@Function(name="add_numbers", description="Adds two numbers together")
async def add_numbers(a: int, b: int) -> int:
    """Add two numbers and return the result."""
    return a + b

@Function(description="Multiply two numbers")
async def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y

@Function  # Minimal decorator usage
async def echo(message: str) -> str:
    return f"Echo: {message}"
```

### 2. Start the server

```python
from functions_core import FunctionServer

if __name__ == "__main__":
    server = FunctionServer()
    server.start()  # Starts on http://localhost:8000
```

### 3. Call your functions

```bash
curl -X POST http://localhost:8000/exec \
  -H "Content-Type: application/json" \
  -d '{
    "executionId": "unique-id-123",
    "functionName": "add_numbers",
    "args": {"a": 5, "b": 3}
  }'
```

Response:
```json
{
  "success": true,
  "result": 8,
  "error": null,
  "metadata": {
    "executionId": "unique-id-123"
  }
}
```

## Advanced Usage

### Custom Function Names

By default, the function name is taken from the Python function name. You can override this:

```python
@Function(name="calculate_sum", description="Calculates the sum of two numbers")
async def my_addition_function(a: int, b: int) -> int:
    return a + b
```

### Error Handling

Functions can raise exceptions which will be gracefully handled:

```python
@Function(name="divide")
async def divide_numbers(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero!")
    return a / b
```

Error response:
```json
{
  "success": false,
  "result": null,
  "error": "Function execution failed: Cannot divide by zero!",
  "metadata": {
    "executionId": "test-123"
  }
}
```

### Complex Return Types

Functions can return complex data structures:

```python
from typing import Dict, List, Any
from datetime import datetime

@Function(name="get_user_data")
async def get_user_data(user_id: int) -> Dict[str, Any]:
    return {
        "id": user_id,
        "name": "John Doe",
        "email": "john@example.com",
        "created_at": datetime.now().isoformat(),
        "tags": ["premium", "verified"],
        "metadata": {
            "last_login": "2024-01-01T10:00:00Z",
            "preferences": {"theme": "dark"}
        }
    }
```

### Long-Running Operations

Functions have a configurable timeout (default 30s, max 300s):

```python
import asyncio

@Function(name="process_data")
async def process_large_dataset(items: int) -> Dict[str, Any]:
    # Simulate processing
    await asyncio.sleep(2)  
    
    return {
        "processed_items": items,
        "status": "completed"
    }
```

## Configuration

### Environment Variables

Environment variables can be configured in different ways depending on your deployment:

#### Local Development
Create a `.env` file in your project root for local testing:

```bash
# Install python-dotenv for .env support
pip install python-dotenv
```

Then in your `main.py`:
```python
from dotenv import load_dotenv
load_dotenv()  # Load .env file

from functions_core import FunctionServer

if __name__ == "__main__":
    server = FunctionServer()
    server.start()
```

#### Production (Kubernetes/Knative)
In production, environment variables are set in the Knative Service manifest:

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: my-function
spec:
  template:
    spec:
      containers:
        - image: my-function-image
          env:
            - name: CRBR_DEPLOYMENT_ID
              value: "prod-function-123"
            - name: CRBR_RABBITMQ_HOSTNAME
              value: "rabbitmq.cerebro.svc.cluster.local"
            - name: CRBR_RABBITMQ_USERNAME
              valueFrom:
                secretKeyRef:
                  name: rabbitmq-credentials
                  key: username
            - name: CRBR_RABBITMQ_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: rabbitmq-credentials
                  key: password
            - name: CRBR_FUNCTIONS_PORT
              value: "8080"  # Knative default
```

**Important:** The `.env` file is only for local development. In production, all configuration comes from the Kubernetes manifest.

### Core Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CRBR_DEPLOYMENT_ID` | `local-dev` | Deployment identifier |
| `CRBR_FUNCTIONS_HOST` | `0.0.0.0` | Host to bind the server to |
| `CRBR_FUNCTIONS_PORT` | `8000` | Port to bind the server to |
| `CRBR_FUNCTIONS_TIMEOUT` | `30` | Default function execution timeout (seconds) |
| `CRBR_FUNCTIONS_MAX_TIMEOUT` | `300` | Maximum allowed timeout (seconds) |
| `CRBR_FUNCTIONS_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CRBR_UVICORN_LOG_LEVEL` | `INFO` | Uvicorn server log level |

### RabbitMQ Configuration (Phase II)

| Variable | Default | Description |
|----------|---------|-------------|
| `CRBR_RABBITMQ_HOSTNAME` | - | RabbitMQ hostname |
| `CRBR_RABBITMQ_PORT` | `5672` | RabbitMQ port |
| `CRBR_RABBITMQ_USERNAME` | - | RabbitMQ username |
| `CRBR_RABBITMQ_PASSWORD` | - | RabbitMQ password |
| `CRBR_RABBITMQ_VHOST` | `/` | RabbitMQ virtual host |
| `CRBR_RABBITMQ_EXCHANGE` | `event.exchange` | Exchange name for events |
| `CRBR_ENABLE_EVENTS` | `true` | Enable RabbitMQ event publishing |
| `CRBR_HEALTH_CHECK_INTERVAL` | `60` | Health check interval (seconds) |

Example `.env` file:
```bash
# Deployment
CRBR_DEPLOYMENT_ID=local-dev

# Server
CRBR_FUNCTIONS_HOST=0.0.0.0
CRBR_FUNCTIONS_PORT=8000
CRBR_FUNCTIONS_LOG_LEVEL=INFO
CRBR_FUNCTIONS_TIMEOUT=30

# RabbitMQ (optional - for event publishing)
CRBR_RABBITMQ_HOSTNAME=localhost
CRBR_RABBITMQ_PORT=5672
CRBR_RABBITMQ_USERNAME=cerebro
CRBR_RABBITMQ_PASSWORD=cerebro123
CRBR_RABBITMQ_EXCHANGE=event.exchange
CRBR_ENABLE_EVENTS=true
```

## API Reference

### Endpoints

#### Function Execution
All functions are called via POST to `/exec` endpoint:

```json
{
  "executionId": "string",  // Unique identifier for this execution
  "functionName": "string", // Name of the function to execute
  "args": {}                // Arguments to pass to the function
}
```

#### Readiness Check
The `/ready` endpoint provides server status and function information:

```bash
curl -X GET http://localhost:8000/ready
```

Response:
```json
{
  "status": "ready",
  "deployment_id": "local-dev",
  "function_count": 3,
  "functions": ["add_numbers", "multiply", "echo"],
  "rabbitmq_enabled": true,
  "rabbitmq_connected": true
}
```

**Note:** Function registration and RabbitMQ event publishing (`FunctionDeploymentStartedEvent`) happen automatically during server startup. The `/ready` endpoint only reports the current status.

### Function Execution Response Format

All function execution responses follow this structure:

```json
{
  "success": true|false,      // Whether execution was successful
  "result": any,               // Function return value (if success)
  "error": "string|null",      // Error message (if failed)
  "metadata": {                // Additional metadata
    "executionId": "string"
  }
}
```

### HTTP Status Codes

- `200 OK` - Request processed (check `success` field for execution status)
- `422 Unprocessable Entity` - Invalid request format
- `500 Internal Server Error` - Server error

## Logging

The library uses structured JSON logging suitable for production environments:

```json
{
  "timestamp": "2024-01-01T10:00:00.000Z",
  "level": "INFO",
  "message": "Function completed successfully",
  "execution_id": "test-123",
  "function_name": "add_numbers",
  "status": "success",
  "deployment_id": "prod-1"
}
```

Error logs include full stack traces for debugging:

```json
{
  "timestamp": "2024-01-01T10:00:01.000Z",
  "level": "ERROR",
  "message": "Function execution failed: Division by zero",
  "exc_info": "Traceback (most recent call last):\n  ...",
  "execution_id": "test-456",
  "function_name": "divide",
  "status": "error"
}
```

## RabbitMQ Integration

The library automatically publishes events to RabbitMQ when configured:

### Events Published

1. **FunctionsDeploymentStartedEvent** - Published on server startup
   - Contains all registered functions with metadata
   - Routing key: `routing.event.metatwin-functions.function.deployment.started`

2. **FunctionsDeploymentHealthyEvent** - Published periodically (default 60s)
   - Contains list of available function names
   - Routing key: `routing.event.metatwin-functions.function.deployment.healthy`

### Local RabbitMQ Setup

For local development, use the provided Docker Compose:

```bash
cd rabbitmq-docker/
docker-compose up -d

# Access RabbitMQ Management UI
# URL: http://localhost:15672
# Username: cerebro
# Password: cerebro123
```

### Event Structure Example

```json
{
  "deploymentId": "local-dev",
  "functions": [
    {
      "name": "add_numbers",
      "description": "Adds two numbers",
      "args": [
        {"name": "a", "type": "int", "required": true},
        {"name": "b", "type": "int", "required": true}
      ],
      "returnType": "int"
    }
  ]
}
```

## Testing

Run the test suite:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=functions

# Run specific test file
pytest tests/test_handler.py
```

## Examples

Full examples are available in the `examples/` directory:

```bash
cd examples/

# View example functions
cat simple_function.py

# Run the example server
python main.py

# Test with curl (in another terminal)
curl -X POST http://localhost:8000/exec \
  -H "Content-Type: application/json" \
  -d '{"functionName": "count_invoices", "executionId": "test-1", "args": {"includePaid": true}}'
```

## Development

### Project Structure

```
cerebro-pkg-metatwin-functions/
├── functions/              # Main package
│   ├── __init__.py        # Package exports
│   ├── decorator.py       # @Function decorator
│   ├── models.py          # Pydantic models
│   ├── server.py          # FastAPI server
│   ├── handlers.py        # Request handling
│   └── logging.py         # Logging configuration
├── tests/                 # Test suite
│   ├── test_decorator.py  # Decorator tests
│   ├── test_handler.py    # Handler tests
│   └── test_integration.py # End-to-end tests
├── examples/              # Usage examples
│   ├── simple_function.py # Example functions
│   └── main.py           # Example server
└── setup.py              # Package configuration
```

### Building and Publishing

#### Building the Package

```bash
# Build distribution packages
python -m build
```

#### Publishing to Nexus

Use the provided script:
```bash
./build-and-push.sh
# This will:
# 1. Prompt for version number
# 2. Update version in setup.py
# 3. Build the package
# 4. Prompt for Nexus credentials
# 5. Upload to Nexus repository
```

Or manually:
```bash
# Build
python -m build

# Upload to Nexus
twine upload --repository-url https://nexus.optime-test-011.cerebro.optime.ai/repository/pypi-default/ dist/*
```

## Requirements

- Python 3.9+
- FastAPI 0.100.0+
- Pydantic 2.0.0+
- Uvicorn 0.23.0+
- python-json-logger 2.0.0+

## License

MIT License - see LICENSE file for details.

## Support

For issues and feature requests, please visit: https://github.com/optime-ai/cerebro-pkg-metatwin-functions/issues

## Deployment

### Docker Container

Create a `Dockerfile` for your functions:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install the SDK from Nexus
RUN pip install cerebro-pkg-metatwin-functions \
  --index-url https://nexus.optime-test-011.cerebro.optime.ai/repository/pypi-default/simple \
  --extra-index-url https://pypi.org/simple

# Copy your function files
COPY my_functions.py .
COPY main.py .

# Knative expects port 8080
ENV CRBR_FUNCTIONS_PORT=8080

CMD ["python", "main.py"]
```

### Knative Deployment

Functions are deployed to Kubernetes using Knative by the `cerebro-ms-metatwin-functions` microservice. The deployment template is defined and managed by that microservice and may change over time.

Example Knative template structure (subject to change):

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: fx-{{DEPLOYMENT_ID}}
  namespace: cerebro-functions
  labels:
    deployment-id: {{DEPLOYMENT_ID}}
    component: metatwin-function
    managed-by: cerebro-ms-metatwin-functions
spec:
  template:
    spec:
      containers:
        - image: {{IMAGE}}
          env:
            - name: CRBR_DEPLOYMENT_ID
              value: "{{DEPLOYMENT_ID}}"
            - name: CRBR_FUNCTIONS_PORT
              value: "8080"
            # Additional environment variables configured by the microservice
```

**Note:** The exact Knative Service specification is controlled by the `cerebro-ms-metatwin-functions` microservice. Refer to that microservice's documentation for the current template and deployment configuration.

The function will typically be accessible at:
```
http://fx-{{DEPLOYMENT_ID}}.cerebro-function.svc.cluster.local/exec
```

## Roadmap

### Phase I (Completed ✅):
- ✅ Core function serving via HTTP
- ✅ Async function support  
- ✅ Timeout handling
- ✅ Structured logging
- ✅ Error handling with stack traces

### Phase II (Completed ✅):
- ✅ RabbitMQ integration for event publishing
- ✅ Automatic function registration on startup
- ✅ Health check events (periodic)
- ✅ Graceful degradation when RabbitMQ unavailable
- ✅ Configuration via environment variables
- ✅ Retry logic with exponential backoff

### Phase III (Future 🔜):
- 🔜 Function versioning
- 🔜 Metrics and monitoring (Prometheus)
- 🔜 Authentication and authorization
- 🔜 Rate limiting
- 🔜 Function scheduling
- 🔜 WebSocket support for real-time updates