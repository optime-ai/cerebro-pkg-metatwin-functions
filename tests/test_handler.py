"""Tests for the FunctionHandler class."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from functions_core.handlers import FunctionHandler
from functions_core.models import FunctionExecutionRequest, FunctionExecutionResponse


class TestFunctionHandler:
    """Test suite for FunctionHandler."""
    
    @pytest.fixture
    def handler(self):
        """Create a handler with mock functions."""
        registry = {
            "test_func": AsyncMock(return_value=42),
            "error_func": AsyncMock(side_effect=ValueError("Test error")),
            "type_error_func": AsyncMock(side_effect=TypeError("Wrong arguments"))
        }
        return FunctionHandler(registry)
    
    @pytest.mark.asyncio
    async def test_successful_execution(self, handler):
        """Test successful function execution."""
        request = FunctionExecutionRequest(
            executionId="test-123",
            functionName="test_func",
            args={"x": 10}
        )
        
        response = await handler.handle_execution(request)
        
        assert response.success is True
        assert response.result == 42
        assert response.error is None
        assert response.metadata["executionId"] == "test-123"
        
        # Check function was called with correct args
        handler.function_registry["test_func"].assert_called_once_with(x=10)
    
    @pytest.mark.asyncio
    async def test_function_not_found(self, handler):
        """Test handling of non-existent function."""
        request = FunctionExecutionRequest(
            executionId="test-404",
            functionName="unknown_func",
            args={}
        )
        
        response = await handler.handle_execution(request)
        
        assert response.success is False
        assert response.result is None
        assert "not found" in response.error
        assert "unknown_func" in response.error
        assert response.metadata["executionId"] == "test-404"
    
    @pytest.mark.asyncio
    async def test_function_execution_error(self, handler):
        """Test handling of function execution errors."""
        request = FunctionExecutionRequest(
            executionId="test-error",
            functionName="error_func",
            args={}
        )
        
        response = await handler.handle_execution(request)
        
        assert response.success is False
        assert response.result is None
        assert "Test error" in response.error
        assert response.metadata["executionId"] == "test-error"
    
    @pytest.mark.asyncio
    async def test_type_error_handling(self, handler):
        """Test handling of TypeError (wrong arguments)."""
        request = FunctionExecutionRequest(
            executionId="test-type",
            functionName="type_error_func",
            args={"wrong": "args"}
        )
        
        response = await handler.handle_execution(request)
        
        assert response.success is False
        assert response.result is None
        assert "Invalid arguments" in response.error
        assert "Wrong arguments" in response.error
        assert response.metadata["executionId"] == "test-type"
    
    @pytest.mark.asyncio
    async def test_empty_args(self, handler):
        """Test function execution with empty args."""
        handler.function_registry["no_args"] = AsyncMock(return_value="success")
        
        request = FunctionExecutionRequest(
            executionId="test-empty",
            functionName="no_args",
            args={}
        )
        
        response = await handler.handle_execution(request)
        
        assert response.success is True
        assert response.result == "success"
        handler.function_registry["no_args"].assert_called_once_with()
    
    @pytest.mark.asyncio
    async def test_complex_result(self, handler):
        """Test function returning complex objects."""
        complex_result = {
            "data": [1, 2, 3],
            "nested": {"key": "value"},
            "number": 42.5
        }
        handler.function_registry["complex"] = AsyncMock(return_value=complex_result)
        
        request = FunctionExecutionRequest(
            executionId="test-complex",
            functionName="complex",
            args={"param": "value"}
        )
        
        response = await handler.handle_execution(request)
        
        assert response.success is True
        assert response.result == complex_result
        assert response.error is None
    
    def test_handler_initialization(self):
        """Test handler initialization with registry."""
        registry = {"func1": Mock(), "func2": Mock()}
        handler = FunctionHandler(registry)
        
        assert handler.function_registry is registry
        assert len(handler.function_registry) == 2
        assert "func1" in handler.function_registry
        assert "func2" in handler.function_registry
    
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that function execution times out properly."""
        async def slow_func():
            """Function that takes too long."""
            await asyncio.sleep(5)  # Sleep for 5 seconds
            return "Should not reach here"
        
        # Create handler with short timeout (0.1 seconds)
        registry = {"slow_func": slow_func}
        handler = FunctionHandler(registry, timeout=0.1)
        
        request = FunctionExecutionRequest(
            executionId="test-timeout",
            functionName="slow_func",
            args={}
        )
        
        response = await handler.handle_execution(request)
        
        assert response.success is False
        assert response.result is None
        assert "timed out" in response.error
        assert "0.1 seconds" in response.error
        assert response.metadata["executionId"] == "test-timeout"
    
    @pytest.mark.asyncio
    async def test_function_completes_before_timeout(self):
        """Test that fast functions complete successfully within timeout."""
        async def fast_func():
            """Function that completes quickly."""
            await asyncio.sleep(0.01)  # Very short delay
            return "Success"
        
        # Create handler with reasonable timeout
        registry = {"fast_func": fast_func}
        handler = FunctionHandler(registry, timeout=1.0)
        
        request = FunctionExecutionRequest(
            executionId="test-fast",
            functionName="fast_func",
            args={}
        )
        
        response = await handler.handle_execution(request)
        
        assert response.success is True
        assert response.result == "Success"
        assert response.error is None