"""Tests for the @Function decorator."""

import pytest
import asyncio
import inspect
from functions_core.decorator import Function


class TestFunctionDecorator:
    """Test suite for the @Function decorator."""
    
    def test_async_function_accepted(self):
        """Test that async functions are properly decorated."""
        @Function(name="test_func", description="Test function")
        async def async_func(x: int) -> int:
            return x * 2
        
        # Check that function is decorated
        assert hasattr(async_func, '_is_cerebro_function')
        assert async_func._is_cerebro_function is True
        assert async_func._cerebro_name == "test_func"
        assert async_func._cerebro_description == "Test function"
        assert isinstance(async_func._cerebro_signature, inspect.Signature)
    
    def test_sync_function_rejected(self):
        """Test that sync functions raise ValueError."""
        with pytest.raises(ValueError) as excinfo:
            @Function(description="This should fail")
            def sync_func():
                return "sync"
        
        assert "must be async" in str(excinfo.value)
        assert "sync_func" in str(excinfo.value)
    
    def test_default_name_used_when_not_provided(self):
        """Test that function.__name__ is used when name not provided."""
        @Function(description="Test")
        async def my_function():
            pass
        
        assert my_function._cerebro_name == "my_function"
    
    def test_empty_description_when_not_provided(self):
        """Test that description defaults to empty string."""
        @Function()
        async def func():
            pass
        
        assert func._cerebro_description == ""
    
    def test_signature_capture(self):
        """Test that function signature is properly captured."""
        @Function()
        async def complex_func(a: int, b: str = "default", *, c: float) -> dict:
            return {}
        
        sig = complex_func._cerebro_signature
        
        # Check parameters are captured
        assert 'a' in sig.parameters
        assert 'b' in sig.parameters
        assert 'c' in sig.parameters
        
        # Check parameter details
        assert sig.parameters['a'].annotation == int
        assert sig.parameters['b'].annotation == str
        assert sig.parameters['b'].default == "default"
        assert sig.parameters['c'].annotation == float
        assert sig.parameters['c'].kind == inspect.Parameter.KEYWORD_ONLY
        
        # Check return type
        assert sig.return_annotation == dict
    
    def test_original_function_preserved(self):
        """Test that the original function is still callable."""
        @Function(name="decorated")
        async def original(x: int) -> int:
            return x + 1
        
        # Function should still be callable
        result = asyncio.run(original(5))
        assert result == 6
    
    def test_multiple_decorations(self):
        """Test that multiple functions can be decorated independently."""
        @Function(name="func1", description="First")
        async def func1():
            return 1
        
        @Function(name="func2", description="Second")
        async def func2():
            return 2
        
        # Check that each has its own metadata
        assert func1._cerebro_name == "func1"
        assert func1._cerebro_description == "First"
        assert func2._cerebro_name == "func2"
        assert func2._cerebro_description == "Second"
        
        # Functions should remain independent
        assert asyncio.run(func1()) == 1
        assert asyncio.run(func2()) == 2
    
    def test_decorator_with_no_arguments(self):
        """Test that decorator works with no arguments."""
        @Function
        async def simple_func():
            return "simple"
        
        assert hasattr(simple_func, '_is_cerebro_function')
        assert simple_func._cerebro_name == "simple_func"
        assert simple_func._cerebro_description == ""
    
    def test_decorator_preserves_docstring(self):
        """Test that decorator preserves function docstring."""
        @Function()
        async def documented():
            """This is a docstring."""
            pass
        
        assert documented.__doc__ == "This is a docstring."
    
    def test_decorator_preserves_function_name(self):
        """Test that __name__ attribute is preserved."""
        @Function(name="custom")
        async def original_name():
            pass
        
        assert original_name.__name__ == "original_name"
        assert original_name._original_name == "original_name"