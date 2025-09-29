"""Function decorator for marking functions to be served as FaaS endpoints."""

import asyncio
import inspect
from typing import Optional, Callable, Union


def Function(name_or_func: Optional[Union[Callable, str]] = None, *, name: Optional[str] = None, description: Optional[str] = None) -> Union[Callable, Callable[[Callable], Callable]]:
    """Decorator to mark a function for FaaS serving.
    
    Args:
        name_or_func: Either the function (when used without parens) or positional name
        name: Optional custom name (keyword-only argument)
        description: Optional human-readable description
        
    Returns:
        Decorated function with metadata attached
        
    Raises:
        ValueError: If the decorated function is not async
        
    Example:
        @Function(description="Adds two numbers")
        async def add_numbers(a: int, b: int) -> int:
            return a + b
            
        @Function
        async def simple_func():
            return "simple"
    """
    def decorator(func: Callable) -> Callable:
        # Validate function is async
        if not asyncio.iscoroutinefunction(func):
            raise ValueError(
                f"Function '{func.__name__}' must be async. "
                f"Use 'async def {func.__name__}(...)' instead of 'def {func.__name__}(...)'"
            )
        
        # Determine the name
        if callable(name_or_func):
            # Called as @Function without parentheses
            func_name = func.__name__
        else:
            # Called as @Function() or @Function("custom") or @Function(name="custom")
            # Priority: keyword 'name' > positional 'name_or_func' > function name
            func_name = name or name_or_func or func.__name__
        
        # Attach metadata to function
        func._is_cerebro_function = True
        func._cerebro_name = func_name
        func._cerebro_description = description or ""
        func._cerebro_signature = inspect.signature(func)
        
        # Store original function name for debugging
        func._original_name = func.__name__
        
        return func
    
    # Check if called without parentheses (@Function)
    if callable(name_or_func):
        # name_or_func is actually the function being decorated
        return decorator(name_or_func)
    
    # Called with parentheses (@Function() or @Function(name="..."))
    return decorator