# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Cerebro package template for building MetaTwin functions that integrate with the Cerebro MetaTwin Functions microservice. The project uses a standard Python package structure with setuptools for building and distribution.

**Important**: See `MICROSERVICE_INTEGRATION_SPEC.md` for detailed integration requirements with the Spring Boot microservice.

## Common Development Commands

### Testing
```bash
./run_tests.sh
# Or manually:
export PYTHONPATH=$(pwd)
pytest tests
# Run specific test:
pytest tests/test_file.py::test_function
```

### Building and Publishing
```bash
./build-and-push.sh
# This script will:
# 1. Prompt for version number
# 2. Update version in setup.py
# 3. Build the package using python -m build
# 4. Upload to Google Artifact Registry
```

### Manual Build
```bash
python -m build
```

## Architecture

The codebase follows a standard Python package structure:

- **cerebro_[package name]/**: Main package directory containing the implementation
  - Package name should be replaced with the actual function name
  - All business logic should be implemented here as Python modules
  
- **tests/**: Test directory for pytest-based unit tests
  - Tests should mirror the structure of the main package
  - Use pytest and pytest-mock for testing
  
- **setup.py**: Package configuration defining dependencies and metadata
  - Core dependencies: pandas==2.2.1, pyarrow==15.0.2, numpy==1.26.4
  - Version is updated automatically by build-and-push.sh

## Deployment

The package is deployed to Google Artifact Registry in europe-central2 region. Authentication uses gcloud auth tokens automatically.

## Development Guidelines

- The package template uses placeholder `[package name]` which should be replaced with the actual package name
- Maintain Python 3.x compatibility
- Follow the existing dependency versions specified in setup.py
- Tests are run using pytest with the project root in PYTHONPATH

## Implementation Plans and Guidelines

**CRITICAL**: For current implementation, refer to:
- `IMPLEMENTATION_PLAN.md` - Detailed checklist and structure for Phase I
- `IMPLEMENTATION_GUIDELINES.md` - Critical constraints and rules (NO RabbitMQ in Phase I!)

## MetaTwin Functions Integration

When implementing Python functions for the MetaTwin microservice, the container must:

### 1. HTTP Endpoints
- **Execution Endpoint**: Handle POST requests at `/exec` endpoint
  - Accept `ContainerExecutionRequest` format:
    ```json
    {
      "executionId": "uuid",
      "functionName": "function_to_execute",
      "args": { "key": "value" }
    }
    ```
  - Return `ContainerExecutionResponse` format:
    ```json
    {
      "success": true/false,
      "result": {},
      "error": "error_message_if_failed",
      "metadata": {}
    }
    ```

### 2. Function Registration
- On startup, publish function metadata to RabbitMQ queue: `event.metatwin-functions.function.deployment.started`
- Include function name, description, arguments (with types), and return type
- Read `CRBR_DEPLOYMENT_ID` from environment variable

### 3. Health Monitoring
- Respond to health check requests to avoid being marked UNHEALTHY (5-minute threshold)
- Report healthy status via RabbitMQ: `event.metatwin-functions.function.deployment.healthy`

### 4. Key Requirements
- Container URL pattern: `http://fx-{deploymentId}.cerebro-function.svc.cluster.local/exec`
- Maximum execution timeout: 300 seconds
- Support proper error reporting with `success=false` in responses
- Include execution metadata in responses

### 5. Error Codes
Common validation errors to handle:
- MTF-EXECUTION-002: Function execution timeout
- MTF-EXECUTION-003: Function execution failed
- MTF-EXECUTION-008: Required parameter missing

For complete microservice integration details, see `MICROSERVICE_INTEGRATION_SPEC.md`