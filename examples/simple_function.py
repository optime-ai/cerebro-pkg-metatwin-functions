"""Example functions demonstrating the usage of @Function decorator."""

import sys
import os
# Add parent directory to path to import functions module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions_core import Function
import asyncio
import random
from typing import List, Dict, Any
from datetime import datetime


@Function(description="Counts all invoices in the system")
async def count_invoices(includePaid: bool) -> int:
    """Count invoices based on payment status.
    
    Args:
        includePaid: If True, includes paid invoices in the count
        
    Returns:
        Number of invoices
    """
    # Simulated business logic
    if includePaid:
        return 42  # Total invoices including paid
    else:
        return 35  # Only unpaid invoices


@Function(description="Calculates sum of two numbers")
async def add_numbers(a: int, b: int) -> int:
    """Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    return a + b


@Function(name="multiply", description="Multiplies two numbers")
async def multiply_numbers(x: float, y: float) -> float:
    """Multiply two numbers.
    
    Args:
        x: First number
        y: Second number
        
    Returns:
        Product of x and y
    """
    return x * y


@Function(description="Generates random user data")
async def generate_user() -> Dict[str, Any]:
    """Generate random user data for testing.
    
    Returns:
        Dictionary with user information
    """
    names = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
    return {
        "id": random.randint(1000, 9999),
        "name": random.choice(names),
        "email": f"{random.choice(names).lower()}@example.com",
        "created_at": datetime.now().isoformat(),
        "is_active": random.choice([True, False])
    }


@Function(description="Calculates statistics for a list of numbers")
async def calculate_stats(numbers: List[float]) -> Dict[str, float]:
    """Calculate basic statistics for a list of numbers.
    
    Args:
        numbers: List of numbers to analyze
        
    Returns:
        Dictionary with min, max, avg, and sum
    """
    if not numbers:
        return {
            "min": 0,
            "max": 0, 
            "avg": 0,
            "sum": 0,
            "count": 0
        }
    
    return {
        "min": min(numbers),
        "max": max(numbers),
        "avg": sum(numbers) / len(numbers),
        "sum": sum(numbers),
        "count": len(numbers)
    }


@Function(description="Simulates a long-running operation")
async def process_data(items: int, delay_ms: int = 100) -> Dict[str, Any]:
    """Simulate processing multiple items with optional delay.
    
    Args:
        items: Number of items to process
        delay_ms: Delay in milliseconds per item (for testing timeouts)
        
    Returns:
        Processing result with statistics
    """
    # Simulate processing delay
    total_delay = (items * delay_ms) / 1000  # Convert to seconds
    await asyncio.sleep(min(total_delay, 2))  # Cap at 2 seconds for demo
    
    return {
        "processed_items": items,
        "delay_per_item_ms": delay_ms,
        "total_time_s": total_delay,
        "status": "completed",
        "timestamp": datetime.now().isoformat()
    }


# Example of a function that will raise an error (for testing error handling)
@Function(description="Division operation that may fail")
async def divide(a: float, b: float) -> float:
    """Divide two numbers.
    
    Args:
        a: Dividend
        b: Divisor
        
    Returns:
        Result of division
        
    Raises:
        ZeroDivisionError: If b is zero
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


@Function(name="slow_operation", description="Simulates a slow operation for timeout testing")
async def slow_operation(duration: float = 35.0) -> str:
    """Simulates a slow operation that may timeout.
    
    Args:
        duration: How long to sleep in seconds (default 35s, which exceeds default 30s timeout)
    
    Returns:
        Success message if completed without timeout
    """
    await asyncio.sleep(duration)
    return f"Operation completed after {duration} seconds"