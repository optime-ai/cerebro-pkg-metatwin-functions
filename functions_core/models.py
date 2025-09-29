"""Pydantic models for request and response handling."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class FunctionExecutionRequest(BaseModel):
    """Request model for function execution.
    
    Matches the ContainerExecutionRequest format from microservice spec.
    """
    executionId: str = Field(..., description="Unique execution ID for tracing")
    functionName: str = Field(..., description="Name of the function to execute")
    args: Dict[str, Any] = Field(default_factory=dict, description="Function arguments")


class FunctionExecutionResponse(BaseModel):
    """Response model sent back to the microservice.
    
    This is the actual format expected by ms-metatwin-functions.
    Used for both successful executions and errors.
    
    Examples:
        Success response:
            FunctionExecutionResponse(success=True, result=42, metadata={})
        
        Error response:
            FunctionExecutionResponse(success=False, error="Function not found", metadata={})
    """
    success: bool = Field(..., description="Execution success flag")
    result: Optional[Any] = Field(None, description="Function return value (when success=True)")
    error: Optional[str] = Field(None, description="Error message (when success=False)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")