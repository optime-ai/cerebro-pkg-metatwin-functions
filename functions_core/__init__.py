"""Functions - Function-as-a-Service SDK for Cerebro MetaTwin Functions."""

from .decorator import Function
from .server import FunctionServer

__version__ = "1.0.0"
__all__ = ["Function", "FunctionServer"]