"""Request handling logic for function execution."""

from typing import Any, Dict, Callable, Optional
import asyncio
import os
from .models import FunctionExecutionRequest, FunctionExecutionResponse
from .logging import get_logger

logger = get_logger()


class FunctionHandler:
    """Handler for function execution requests."""
    
    def __init__(self, function_registry: Dict[str, Callable], timeout: Optional[float] = None):
        """Initialize the handler with a function registry.
        
        Args:
            function_registry: Dictionary mapping function names to callables
            timeout: Optional timeout in seconds (defaults to CRBR_FUNCTIONS_TIMEOUT env or 30s)
        """
        self.function_registry = function_registry
        
        # Get timeout from parameter, environment, or use default (30s)
        # Maximum allowed timeout from environment or 300s (5 minutes)
        default_timeout = float(os.getenv('CRBR_FUNCTIONS_TIMEOUT', '30'))
        max_timeout = float(os.getenv('CRBR_FUNCTIONS_MAX_TIMEOUT', '300'))
        self.timeout = min(timeout or default_timeout, max_timeout)
    
    async def handle_execution(self, request: FunctionExecutionRequest) -> FunctionExecutionResponse:
        """Handle function execution request.
        
        Validates the function exists, executes it with provided arguments,
        and returns a properly formatted response.
        
        Args:
            request: The execution request containing functionName, args, and executionId
            
        Returns:
            FunctionExecutionResponse with success status and result or error
        """
        execution_id = request.executionId
        func_name = request.functionName
        args = request.args
        
        logger.info(
            f"Executing function: {func_name}",
            extra={"execution_id": execution_id, "function_name": func_name}
        )
        
        # Check if function exists
        if func_name not in self.function_registry:
            logger.error(
                f"Function not found: {func_name}",
                extra={
                    "execution_id": execution_id, 
                    "function_name": func_name,
                    "status": "error"
                }
            )
            return FunctionExecutionResponse(
                success=False,
                error=f"Function '{func_name}' not found",
                metadata={"executionId": execution_id}
            )
        
        # Get the function
        func = self.function_registry[func_name]
        
        try:
            # Execute the function with timeout
            logger.debug(
                f"Executing function with timeout: {self.timeout}s",
                extra={"execution_id": execution_id, "function_name": func_name, "timeout": self.timeout}
            )
            
            result = await asyncio.wait_for(func(**args), timeout=self.timeout)
            
            logger.info(
                f"Function completed successfully",
                extra={
                    "execution_id": execution_id, 
                    "function_name": func_name,
                    "status": "success"
                }
            )
            
            return FunctionExecutionResponse(
                success=True,
                result=result,
                metadata={"executionId": execution_id}
            )
        
        except asyncio.TimeoutError:
            # Function execution timed out
            error_msg = f"Function '{func_name}' execution timed out after {self.timeout} seconds"
            logger.error(
                error_msg,
                extra={
                    "execution_id": execution_id, 
                    "function_name": func_name, 
                    "timeout": self.timeout,
                    "status": "timeout"
                }
            )
            
            return FunctionExecutionResponse(
                success=False,
                error=error_msg,
                metadata={"executionId": execution_id}
            )
            
        except TypeError as e:
            # Usually means wrong arguments
            error_msg = f"Invalid arguments for function '{func_name}': {str(e)}"
            logger.error(
                error_msg,
                exc_info=True,
                extra={
                    "execution_id": execution_id, 
                    "function_name": func_name,
                    "status": "error"
                }
            )
            
            return FunctionExecutionResponse(
                success=False,
                error=error_msg,
                metadata={"executionId": execution_id}
            )
            
        except Exception as e:
            # Any other error during execution
            error_msg = f"Function execution failed: {str(e)}"
            logger.error(
                error_msg, 
                exc_info=True,
                extra={
                    "execution_id": execution_id, 
                    "function_name": func_name,
                    "status": "error"
                }
            )
            
            return FunctionExecutionResponse(
                success=False,
                error=error_msg,
                metadata={"executionId": execution_id}
            )