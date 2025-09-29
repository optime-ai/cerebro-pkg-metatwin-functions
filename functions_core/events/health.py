"""
Health check scheduler for periodic status reporting.

This module provides a background task that periodically publishes
health check events to indicate that the deployment and its functions
are healthy and available.
"""
import asyncio
from typing import Dict, Callable, Optional, List
from datetime import datetime

from .publisher import EventPublisher
from .models import FunctionsDeploymentHealthyEvent, FunctionsDeploymentHealthyPayload
from ..config import RabbitMQConfig
from ..logging import get_logger

logger = get_logger(__name__)


class HealthCheckScheduler:
    """
    Manages periodic health check event publishing.
    
    Runs as an asyncio background task and publishes health events
    at configured intervals to indicate service availability.
    """
    
    def __init__(
        self,
        publisher: EventPublisher,
        config: RabbitMQConfig,
        function_registry: Dict[str, Callable]
    ):
        """
        Initialize the health check scheduler.
        
        Args:
            publisher: EventPublisher instance for sending events
            config: RabbitMQ configuration
            function_registry: Dictionary of registered functions
        """
        self.publisher = publisher
        self.config = config
        self.function_registry = function_registry
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._last_health_check: Optional[datetime] = None
        
    async def start(self) -> None:
        """
        Start the health check scheduler.
        
        Creates a background task that publishes health events periodically.
        """
        if self._running:
            logger.warning("Health check scheduler already running")
            return
            
        if not self.config.should_enable_events():
            logger.info("Health check scheduler disabled (events not enabled)")
            return
            
        self._running = True
        self._task = asyncio.create_task(self._health_check_loop())
        logger.info(
            f"Health check scheduler started (interval: {self.config.health_check_interval}s)"
        )
        
    async def stop(self) -> None:
        """
        Stop the health check scheduler gracefully.
        
        Cancels the background task and waits for cleanup.
        """
        if not self._running:
            logger.debug("Health check scheduler not running")
            return
            
        self._running = False
        
        if self._task and not self._task.done():
            logger.info("Stopping health check scheduler...")
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("Health check scheduler stopped")
            
        self._task = None
        
    async def _health_check_loop(self) -> None:
        """
        Main loop for publishing health check events.
        
        Runs continuously until stopped, publishing events at configured intervals.
        """
        logger.debug("Health check loop started")
        
        # Initial delay to allow server startup
        await asyncio.sleep(5)
        
        while self._running:
            try:
                await self._publish_health_event()
                
                # Wait for next interval
                await asyncio.sleep(self.config.health_check_interval)
                
            except asyncio.CancelledError:
                logger.debug("Health check loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                
                # Wait before retrying to avoid rapid failure loops
                await asyncio.sleep(min(self.config.health_check_interval, 30))
                
        logger.debug("Health check loop ended")
        
    async def _publish_health_event(self) -> None:
        """
        Publish a health check event with current function names.
        
        Creates and publishes a FunctionsDeploymentHealthyEvent with
        the list of currently registered functions.
        """
        try:
            # Get list of function names from registry
            function_names = list(self.function_registry.keys())
            
            if not function_names:
                logger.warning("No functions registered, skipping health check event")
                return
            
            # Create health event with proper payload structure
            payload = FunctionsDeploymentHealthyPayload(
                deploymentId=self.config.deployment_id,
                functionNames=function_names
            )
            health_event = FunctionsDeploymentHealthyEvent(payload=payload)
            
            # Publish event
            success = await self.publisher.publish_json(
                routing_key=self.config.routing_key_deployment_healthy,
                data=health_event
            )
            
            if success:
                self._last_health_check = datetime.utcnow()
                logger.debug(
                    f"Published health check event",
                    extra={
                        "deployment_id": self.config.deployment_id,
                        "function_count": len(function_names),
                        "functions": function_names
                    }
                )
            else:
                logger.warning("Failed to publish health check event")
                
        except Exception as e:
            logger.error(f"Error publishing health check event: {e}")
            
    def get_function_names(self) -> List[str]:
        """
        Get the list of registered function names.
        
        Returns:
            List[str]: Names of all registered functions
        """
        return list(self.function_registry.keys())
        
    @property
    def is_running(self) -> bool:
        """
        Check if the scheduler is currently running.
        
        Returns:
            bool: True if scheduler is active
        """
        return self._running and self._task is not None and not self._task.done()
        
    @property
    def last_health_check(self) -> Optional[datetime]:
        """
        Get the timestamp of the last successful health check.
        
        Returns:
            Optional[datetime]: Last health check time or None
        """
        return self._last_health_check
        
    async def trigger_health_check(self) -> None:
        """
        Manually trigger a health check event.
        
        Useful for testing or forcing immediate health reporting.
        """
        if not self._running:
            logger.warning("Cannot trigger health check: scheduler not running")
            return
            
        logger.info("Manually triggering health check event")
        await self._publish_health_event()