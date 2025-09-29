"""Logging configuration for structured JSON logging."""

import logging
import json
import sys
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pythonjsonlogger import jsonlogger


class CerebroFunctionLogger:
    """Configure structured JSON logging for production environments."""
    
    _configured = False  # Track if logging has been configured
    
    @classmethod
    def setup_logging(
        cls,
        log_level: Optional[str] = None,
        deployment_id: Optional[str] = None
    ) -> logging.Logger:
        """Configure structured JSON logging for the application.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR). 
                      Defaults to environment variable or INFO.
            deployment_id: Deployment identifier for log context.
                         Defaults to environment variable or 'local-dev'.
        
        Returns:
            Configured logger instance
        """
        # Only configure once
        if cls._configured:
            return logging.getLogger('functions')
        
        # Get configuration from environment or use defaults
        log_level = log_level or os.getenv('CRBR_FUNCTIONS_LOG_LEVEL', 'INFO')
        deployment_id = deployment_id or os.getenv('CRBR_DEPLOYMENT_ID', 'local-dev')
        
        # Check if we're in local development mode
        is_local = deployment_id == 'local-dev'
        
        # Configure root logger to ensure all logs are visible
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Choose formatter based on environment
        if is_local:
            # Use simple formatter for local development
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            # Use JSON formatter for production
            formatter = CustomJsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s',
                deployment_id=deployment_id
            )
        
        # Configure the 'functions' parent logger - this will handle all functions.* loggers
        functions_logger = logging.getLogger('functions')
        functions_logger.setLevel(getattr(logging, log_level.upper()))
        functions_logger.handlers = []
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        functions_logger.addHandler(handler)
        functions_logger.propagate = False
        
        # Also configure __main__ logger for the examples/main.py script
        main_logger = logging.getLogger('__main__')
        main_logger.setLevel(getattr(logging, log_level.upper()))
        main_logger.handlers = []
        main_handler = logging.StreamHandler(sys.stdout)
        main_handler.setFormatter(formatter)
        main_logger.addHandler(main_handler)
        main_logger.propagate = False
        
        # Also configure aio_pika logger to see RabbitMQ connection logs
        aio_pika_logger = logging.getLogger('aio_pika')
        aio_pika_logger.setLevel(getattr(logging, log_level.upper()))
        aio_pika_logger.handlers = []
        aio_pika_handler = logging.StreamHandler(sys.stdout)
        aio_pika_handler.setFormatter(formatter)
        aio_pika_logger.addHandler(aio_pika_handler)
        aio_pika_logger.propagate = False
        
        # Configure aiormq logger as well
        aiormq_logger = logging.getLogger('aiormq')
        aiormq_logger.setLevel(getattr(logging, log_level.upper()))
        aiormq_logger.handlers = []
        aiormq_handler = logging.StreamHandler(sys.stdout)
        aiormq_handler.setFormatter(formatter)
        aiormq_logger.addHandler(aiormq_handler)
        aiormq_logger.propagate = False
        
        functions_logger.info(
            f"Logging configured - Level: {log_level}, Deployment: {deployment_id}, Format: {'Simple' if is_local else 'JSON'}"
        )
        
        cls._configured = True  # Mark as configured
        return functions_logger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that adds timestamp and deployment context."""
    
    def __init__(self, *args, deployment_id: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.deployment_id = deployment_id
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        """Add custom fields to each log record.
        
        Args:
            log_record: The log record dict to be output
            record: The original LogRecord
            message_dict: User-supplied message dict
        """
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Add level as string
        log_record['level'] = record.levelname
        
        # Add deployment context
        log_record['deployment_id'] = self.deployment_id
        
        # Add module and function info
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        
        # If there's an execution_id in extra, make it top-level
        if hasattr(record, 'execution_id'):
            log_record['execution_id'] = record.execution_id
        
        # Remove unnecessary fields
        for field in ['levelname', 'funcName', 'pathname', 'lineno']:
            log_record.pop(field, None)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: Logger name. If not provided, uses 'functions'
    
    Returns:
        Logger instance
    """
    # Setup logging if not already configured
    if not CerebroFunctionLogger._configured:
        CerebroFunctionLogger.setup_logging()
    
    # Use the provided name or default to 'functions'
    logger_name = name if name else 'functions'
    
    return logging.getLogger(logger_name)