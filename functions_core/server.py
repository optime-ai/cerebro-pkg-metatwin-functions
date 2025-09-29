"""FunctionServer - Main server class for serving Python functions as HTTP endpoints."""

import sys
import inspect
from typing import Dict, Callable, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio

from .models import FunctionExecutionRequest, FunctionExecutionResponse
from .logging import get_logger, CerebroFunctionLogger
from .handlers import FunctionHandler
from .config import RabbitMQConfig
from .events.publisher import EventPublisher
from .events.health import HealthCheckScheduler
from .events.models import FunctionsDeploymentStartedEvent, FunctionDeploymentStartedPayload
from .metadata_extractor import FunctionMetadataExtractor

# Setup structured logging
CerebroFunctionLogger.setup_logging()
logger = get_logger(__name__)


class FunctionServer:
    """Main server class for serving Python functions as HTTP endpoints."""
    
    def __init__(self) -> None:
        """Initialize FastAPI application and prepare for function registration."""
        # Create FastAPI app
        self.app = FastAPI(
            title="Cerebro MetaTwin Functions",
            description="Function-as-a-Service for Cerebro Platform",
            version="1.0.0"
        )
        
        # Initialize function registry
        self.function_registry: Dict[str, Callable] = {}
        
        # Create handler instance (handler will read timeout from environment)
        self.handler = FunctionHandler(self.function_registry)
        
        # Initialize RabbitMQ components
        self.config = RabbitMQConfig()
        self.event_publisher: Optional[EventPublisher] = None
        self.health_scheduler: Optional[HealthCheckScheduler] = None
        
        # Setup CORS (allows all origins in development)
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add lifecycle event handlers
        self.app.add_event_handler("startup", self._on_startup)
        self.app.add_event_handler("shutdown", self._on_shutdown)
        
        # Create the main /exec endpoint
        self._create_exec_endpoint()
        
        # Create the /ready endpoint
        self._create_ready_endpoint()
        
        # Automatically scan for functions on initialization
        logger.info("Scanning for decorated functions...")
        self.scan_functions()
        
        logger.info(f"FunctionServer initialized (deployment_id: {self.config.deployment_id})")
    
    def scan_functions(self) -> int:
        """Scan all imported modules for functions decorated with @Function.
        
        Returns:
            Number of functions found and registered
        """
        functions_found = 0
        
        # Create a copy of modules to avoid RuntimeError
        modules_to_scan = list(sys.modules.items())
        
        # Iterate through all loaded modules
        for module_name, module in modules_to_scan:
            # Skip built-in modules and None modules
            if module is None or module_name.startswith('_'):
                continue
                
            try:
                # Get all members of the module
                for name, obj in inspect.getmembers(module):
                    # Check if it's a function with our decorator
                    if callable(obj) and hasattr(obj, '_is_cerebro_function'):
                        func_name = getattr(obj, '_cerebro_name', name)
                        
                        # Register the function
                        self.register_function(func_name, obj)
                        functions_found += 1
                        
                        logger.info(f"Registered function: {func_name} from {module_name}")
            except Exception as e:
                # Skip modules that can't be inspected
                continue
        
        logger.info(f"Function scan complete. Found {functions_found} functions")
        return functions_found
    
    def register_function(self, func_name: str, func_callable: Callable) -> None:
        """Register a single function in the registry.
        
        Args:
            func_name: Name to register the function under
            func_callable: The actual function to register
        """
        if func_name in self.function_registry:
            logger.warning(f"Function {func_name} already registered, overwriting")
        
        self.function_registry[func_name] = func_callable
        
        # Store metadata for documentation
        if hasattr(func_callable, '_cerebro_description'):
            logger.debug(f"Function {func_name}: {func_callable._cerebro_description}")
    
    def _create_exec_endpoint(self) -> None:
        """Create the main /exec endpoint that routes to specific functions."""
        
        @self.app.post("/exec", response_model=FunctionExecutionResponse)
        async def execute_function(request: FunctionExecutionRequest) -> FunctionExecutionResponse:
            """Execute a registered function.
            
            This endpoint receives execution requests from the microservice
            and delegates to the FunctionHandler for processing.
            """
            return await self.handler.handle_execution(request)
    
    def _create_ready_endpoint(self) -> None:
        """Create the /ready endpoint for readiness checks."""
        
        @self.app.get("/ready")
        async def ready() -> dict:
            """Readiness check endpoint.
            
            Returns server status and registered functions.
            Function registration and RabbitMQ events are handled automatically on startup.
            
            Returns:
                Dict with server status and function information
            """
            return {
                "status": "ready",
                "deployment_id": self.config.deployment_id,
                "function_count": len(self.function_registry),
                "functions": list(self.function_registry.keys()),
                "rabbitmq_enabled": self.config.enable_events,
                "rabbitmq_connected": self.event_publisher is not None
            }
    
    def start(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """Start the FastAPI server using uvicorn.
        
        Args:
            host: Host to bind to. Defaults to CRBR_FUNCTIONS_HOST env var or 0.0.0.0
            port: Port to bind to. Defaults to CRBR_FUNCTIONS_PORT env var or 8000
        """
        import os
        
        # Get configuration from environment variables or use defaults
        host = host or os.getenv('CRBR_FUNCTIONS_HOST', '0.0.0.0')
        port = port or int(os.getenv('CRBR_FUNCTIONS_PORT', '8000'))
        
        logger.info(f"Starting server on {host}:{port}")
        logger.info(f"Registered functions: {list(self.function_registry.keys())}")
        logger.info(f"Environment: CRBR_DEPLOYMENT_ID={os.getenv('CRBR_DEPLOYMENT_ID', 'local-dev')}")
        
        # Use string format to ensure lifecycle events are triggered
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
    
    async def _on_startup(self) -> None:
        """Handle application startup - connect to RabbitMQ and register functions."""
        import os
        host = os.getenv('CRBR_FUNCTIONS_HOST', '0.0.0.0')
        port = int(os.getenv('CRBR_FUNCTIONS_PORT', '8000'))
        
        logger.info(f"Starting up FunctionServer...")
        logger.info(f"Server available at: http://{host}:{port}")
        logger.info(f"API documentation: http://{host}:{port}/docs")
        
        # Initialize RabbitMQ if configured
        if self.config.enable_events:
            if not self.config.is_rabbitmq_configured():
                missing = self.config.get_missing_rabbitmq_config()
                logger.warning(
                    f"RabbitMQ events enabled but configuration incomplete. "
                    f"Missing parameters: {', '.join(missing)}. "
                    f"Continuing without event publishing."
                )
            else:
                try:
                    # Create event publisher
                    self.event_publisher = EventPublisher(self.config)
                    connected = await self.event_publisher.connect()
                    
                    if connected:
                        logger.info("Connected to RabbitMQ successfully")
                        
                        # Publish deployment started event
                        await self._publish_deployment_started()
                        
                        # Start health check scheduler
                        self.health_scheduler = HealthCheckScheduler(
                            publisher=self.event_publisher,
                            config=self.config,
                            function_registry=self.function_registry
                        )
                        await self.health_scheduler.start()
                        logger.info("Health check scheduler started")
                    else:
                        logger.warning("Failed to connect to RabbitMQ - continuing without events")
                        
                except Exception as e:
                    logger.error(f"Error during RabbitMQ initialization: {e}")
                    logger.warning("Continuing without RabbitMQ event publishing")
        else:
            logger.info("RabbitMQ events disabled or not configured")
            
        logger.info("FunctionServer startup complete")
    
    async def _on_shutdown(self) -> None:
        """Handle application shutdown - cleanup RabbitMQ connections."""
        logger.info("Shutting down FunctionServer...")
        
        # Stop health check scheduler
        if self.health_scheduler:
            await self.health_scheduler.stop()
            logger.info("Health check scheduler stopped")
        
        # Close RabbitMQ connection
        if self.event_publisher:
            await self.event_publisher.close()
            logger.info("RabbitMQ connection closed")
            
        logger.info("FunctionServer shutdown complete")
    
    async def _publish_deployment_started(self) -> None:
        """Publish deployment started event with all registered functions."""
        if not self.event_publisher:
            return
            
        try:
            # Extract function metadata using the extractor
            functions_info = FunctionMetadataExtractor.extract_functions_metadata(
                self.function_registry
            )
            
            if not functions_info:
                logger.warning("No functions to register with RabbitMQ")
                return
            
            # Create deployment started event with proper payload structure
            payload = FunctionDeploymentStartedPayload(
                deploymentId=self.config.deployment_id,
                functions=functions_info
            )
            event = FunctionsDeploymentStartedEvent(payload=payload)
            
            # Publish event
            success = await self.event_publisher.publish_json(
                routing_key=self.config.routing_key_deployment_started,
                data=event
            )
            
            if success:
                logger.info(
                    f"Published deployment started event with {len(functions_info)} functions",
                    extra={
                        "deployment_id": self.config.deployment_id,
                        "function_count": len(functions_info),
                        "function_names": [f.name for f in functions_info]
                    }
                )
            else:
                logger.error("Failed to publish deployment started event")
                
        except Exception as e:
            logger.error(f"Error publishing deployment started event: {e}")