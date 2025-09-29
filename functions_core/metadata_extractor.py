"""
Function metadata extraction utilities.

This module provides functionality to extract metadata from Python functions
decorated with @Function for registration and documentation purposes.
"""
import inspect
from typing import Dict, Callable, List, Any, Optional, get_type_hints

from .events.models import FunctionInfo, ArgumentInfo
from .logging import get_logger

logger = get_logger(__name__)


class FunctionMetadataExtractor:
    """Extracts metadata from registered functions for event publishing and documentation."""
    
    @staticmethod
    def extract_functions_metadata(registry: Dict[str, Callable]) -> List[FunctionInfo]:
        """
        Extract metadata from all functions in the registry.
        
        Args:
            registry: Dictionary of function name to callable
            
        Returns:
            List of FunctionInfo objects with metadata
        """
        functions_info = []
        
        for func_name, func in registry.items():
            try:
                func_info = FunctionMetadataExtractor.extract_function_info(func_name, func)
                if func_info:
                    functions_info.append(func_info)
                    logger.debug(f"Extracted metadata for function: {func_name}")
            except Exception as e:
                logger.error(f"Error extracting metadata for function {func_name}: {e}")
                continue
        
        return functions_info
    
    @staticmethod
    def extract_function_info(func_name: str, func: Callable) -> Optional[FunctionInfo]:
        """
        Extract metadata from a single function.
        
        Args:
            func_name: Name of the function in the registry
            func: The function callable
            
        Returns:
            FunctionInfo object with metadata or None if extraction fails
        """
        try:
            # Get function signature
            sig = inspect.signature(func)
            
            # Get type hints
            type_hints = get_type_hints(func)
            
            # Extract arguments
            args = FunctionMetadataExtractor._extract_arguments(sig, type_hints)
            
            # Get return type
            return_type = FunctionMetadataExtractor._extract_return_type(type_hints)
            
            # Get description
            description = FunctionMetadataExtractor._extract_description(func)
            
            # Create FunctionInfo
            return FunctionInfo(
                name=func_name,
                description=description,
                args=args,
                returnType=return_type
            )
            
        except Exception as e:
            logger.error(f"Failed to extract info for function {func_name}: {e}")
            return None
    
    @staticmethod
    def _extract_arguments(
        sig: inspect.Signature,
        type_hints: Dict[str, Any]
    ) -> List[ArgumentInfo]:
        """
        Extract argument information from function signature.
        
        Args:
            sig: Function signature
            type_hints: Type hints dictionary
            
        Returns:
            List of ArgumentInfo objects
        """
        args = []
        
        for param_name, param in sig.parameters.items():
            # Skip 'self' parameter if present
            if param_name == 'self':
                continue
            
            # Get type as string
            param_type = "Any"
            if param_name in type_hints:
                param_type = FunctionMetadataExtractor._type_to_string(type_hints[param_name])
            
            # Check if required (no default value)
            required = param.default == inspect.Parameter.empty
            
            # Get description if available
            # TODO: Could parse from docstring in future
            description = None
            
            args.append(ArgumentInfo(
                name=param_name,
                type=param_type,
                required=required,
                description=description
            ))
        
        return args
    
    @staticmethod
    def _extract_return_type(type_hints: Dict[str, Any]) -> str:
        """
        Extract return type from type hints.
        
        Args:
            type_hints: Type hints dictionary
            
        Returns:
            String representation of return type
        """
        if 'return' in type_hints:
            return FunctionMetadataExtractor._type_to_string(type_hints['return'])
        return "Any"
    
    @staticmethod
    def _extract_description(func: Callable) -> str:
        """
        Extract description from function metadata or docstring.
        
        Args:
            func: Function callable
            
        Returns:
            Description string (empty if not available)
        """
        # Try decorator metadata first
        description = getattr(func, '_cerebro_description', '')
        
        # Fall back to docstring if no decorator description
        if not description and func.__doc__:
            description = func.__doc__
        
        # Clean up description - take first line only
        if description:
            description = description.strip().split('\n')[0]
        
        return description or ""
    
    @staticmethod
    def _type_to_string(type_hint: Any) -> str:
        """
        Convert Python type hint to string representation.
        
        Args:
            type_hint: Python type hint
            
        Returns:
            String representation of the type
        """
        if type_hint is None:
            return "None"
        
        # Handle basic types
        if type_hint in (int, str, float, bool, bytes):
            return type_hint.__name__
        
        # Handle NoneType
        if type_hint is type(None):
            return "None"
        
        # Handle Optional, List, Dict etc.
        type_str = str(type_hint)
        
        # Clean up the string representation
        type_str = type_str.replace('typing.', '')
        type_str = type_str.replace('<class ', '').replace('>', '').replace("'", '')
        
        # Handle common typing patterns
        if 'Union[' in type_str and 'None' in type_str:
            # Convert Union[Type, None] to Optional[Type]
            type_str = type_str.replace('Union[', 'Optional[').replace(', None]', ']')
        
        return type_str
    
    @staticmethod
    def get_function_summary(func: Callable) -> Dict[str, Any]:
        """
        Get a human-readable summary of function metadata.
        
        Args:
            func: Function callable
            
        Returns:
            Dictionary with function summary
        """
        try:
            sig = inspect.signature(func)
            type_hints = get_type_hints(func)
            
            return {
                "name": getattr(func, '_cerebro_name', func.__name__),
                "description": FunctionMetadataExtractor._extract_description(func),
                "parameters": {
                    param.name: {
                        "type": FunctionMetadataExtractor._type_to_string(
                            type_hints.get(param.name, Any)
                        ),
                        "required": param.default == inspect.Parameter.empty,
                        "default": None if param.default == inspect.Parameter.empty else str(param.default)
                    }
                    for param in sig.parameters.values()
                    if param.name != 'self'
                },
                "return_type": FunctionMetadataExtractor._extract_return_type(type_hints)
            }
        except Exception as e:
            logger.error(f"Error getting function summary: {e}")
            return {}