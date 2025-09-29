"""
Event models for RabbitMQ communication.

These models match the structure expected by the ms-metatwin-functions microservice.
"""
from typing import List, Optional, Any
import uuid
from pydantic import BaseModel, Field


class ArgumentInfo(BaseModel):
    """
    Function argument metadata.
    
    Matches Java's ArgumentInfo class in FunctionDeploymentStartedPayload.
    """
    name: str = Field(..., description="Argument name")
    type: str = Field(..., description="Argument type (e.g., 'str', 'int', 'bool')")
    required: bool = Field(..., description="Whether the argument is required")
    description: Optional[str] = Field(None, description="Argument description")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "includePaid",
                "type": "bool",
                "required": True,
                "description": "Include paid invoices in the count"
            }
        }


class FunctionInfo(BaseModel):
    """
    Function metadata for registration.
    
    Matches Java's FunctionInfo class in FunctionDeploymentStartedPayload.
    """
    name: str = Field(..., description="Function name")
    description: str = Field(..., description="Function description")
    args: List[ArgumentInfo] = Field(default_factory=list, description="Function arguments")
    returnType: str = Field(..., description="Function return type")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "count_invoices",
                "description": "Counts all invoices in the system",
                "args": [
                    {
                        "name": "includePaid",
                        "type": "bool",
                        "required": True,
                        "description": "Include paid invoices"
                    }
                ],
                "returnType": "int"
            }
        }


class FunctionDeploymentStartedPayload(BaseModel):
    """
    Payload for function deployment started event.
    """
    deploymentId: str = Field(..., description="Unique deployment identifier")
    functions: List[FunctionInfo] = Field(..., description="List of available functions")


class FunctionsDeploymentStartedEvent(BaseModel):
    """
    Event sent when deployment starts with functions.
    
    Contains correlationId, payloadType and payload fields to match SystemEvent structure.
    """
    correlationId: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Correlation identifier for event tracking"
    )
    payloadType: str = Field(
        default="FunctionDeploymentStartedPayload",
        description="Jackson payload type for deserialization"
    )
    payload: FunctionDeploymentStartedPayload = Field(..., description="Event payload data")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "correlationId": "550e8400-e29b-41d4-a716-446655440000",
                "payloadType": "FunctionDeploymentStartedPayload",
                "payload": {
                    "deploymentId": "dep-42",
                    "functions": [
                        {
                            "name": "count_invoices",
                            "description": "Counts all invoices",
                            "args": [
                                {
                                    "name": "includePaid",
                                    "type": "bool",
                                    "required": True,
                                    "description": "Include paid invoices"
                                }
                            ],
                            "returnType": "int"
                        }
                    ]
                }
            }
        }


class FunctionsDeploymentHealthyPayload(BaseModel):
    """
    Payload for functions deployment healthy event.
    """
    deploymentId: str = Field(..., description="Unique deployment identifier")
    functionNames: List[str] = Field(..., description="List of available function names")


class FunctionsDeploymentHealthyEvent(BaseModel):
    """
    Periodic health check event.
    
    Contains correlationId, payloadType and payload fields to match SystemEvent structure.
    """
    correlationId: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Correlation identifier for event tracking"
    )
    payloadType: str = Field(
        default="FunctionsDeploymentHealthyPayload",
        description="Jackson payload type for deserialization"
    )
    payload: FunctionsDeploymentHealthyPayload = Field(..., description="Event payload data")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "correlationId": "550e8400-e29b-41d4-a716-446655440001",
                "payloadType": "FunctionsDeploymentHealthyPayload",
                "payload": {
                    "deploymentId": "dep-42",
                    "functionNames": ["A", "B", "C"]
                }
            }
        }