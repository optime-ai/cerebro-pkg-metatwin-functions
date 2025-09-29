"""
RabbitMQ event publisher for function registration and health monitoring.

This module provides asynchronous publishing of events to RabbitMQ
with retry logic and connection management.
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import aio_pika
from aio_pika import Connection, Channel, Exchange, Message
from aio_pika.exceptions import AMQPError
from pydantic import BaseModel

from ..config import RabbitMQConfig
from ..logging import get_logger

logger = get_logger(__name__)


class EventPublisher:
    """
    Manages RabbitMQ connection and event publishing.
    
    Features:
    - Automatic connection management
    - Retry logic with exponential backoff
    - Graceful error handling
    - Support for reconnection
    """
    
    def __init__(self, config: RabbitMQConfig):
        """
        Initialize the event publisher.
        
        Args:
            config: RabbitMQ configuration
        """
        self.config = config
        self.connection: Optional[Connection] = None
        self.channel: Optional[Channel] = None
        self.exchange: Optional[Exchange] = None
        self._connected = False
        self._lock = asyncio.Lock()
        
    async def connect(self, max_retries: Optional[int] = None) -> bool:
        """
        Establish connection to RabbitMQ with retry logic.
        
        Args:
            max_retries: Maximum number of retry attempts (default from config)
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        if max_retries is None:
            max_retries = self.config.max_retries
            
        async with self._lock:
            if self._connected:
                logger.debug("Already connected to RabbitMQ")
                return True
            
            if not self.config.is_rabbitmq_configured():
                logger.warning("RabbitMQ not configured, skipping connection")
                return False
            
            retry_count = 0
            delay = self.config.retry_delay
            
            while retry_count < max_retries:
                try:
                    logger.info(
                        f"Attempting to connect to RabbitMQ at {self.config.rabbitmq_hostname}:{self.config.rabbitmq_port} "
                        f"(attempt {retry_count + 1}/{max_retries})"
                    )
                    
                    # Create connection
                    self.connection = await aio_pika.connect_robust(
                        self.config.get_rabbitmq_url(),
                        timeout=self.config.connection_timeout
                    )
                    
                    # Create channel
                    self.channel = await self.connection.channel(on_return_raises=True)
                    
                    # Declare exchange
                    await self._declare_exchange()
                    
                    self._connected = True
                    logger.info(
                        f"Successfully connected to RabbitMQ exchange '{self.config.rabbitmq_exchange}'"
                    )
                    return True
                    
                except (AMQPError, ConnectionError, TimeoutError) as e:
                    retry_count += 1
                    logger.error(
                        f"Failed to connect to RabbitMQ (attempt {retry_count}/{max_retries}): {e}"
                    )
                    
                    if retry_count < max_retries:
                        logger.info(f"Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                        # Exponential backoff with max delay of 60 seconds
                        delay = min(delay * 2, 60)
                    else:
                        logger.error(
                            f"Failed to connect to RabbitMQ after {max_retries} attempts"
                        )
                        
            return False
    
    async def _declare_exchange(self) -> None:
        """
        Declare the exchange for publishing events.
        
        Creates a topic exchange with durable flag set.
        """
        if not self.channel:
            raise RuntimeError("Channel not initialized")
            
        self.exchange = await self.channel.declare_exchange(
            name=self.config.rabbitmq_exchange,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        logger.debug(f"Declared exchange: {self.config.rabbitmq_exchange}")
    
    async def _ensure_connection(self) -> bool:
        """
        Ensure connection is established, reconnecting if necessary.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if self._connected and self.connection and not self.connection.is_closed:
            return True
            
        logger.info("Connection lost, attempting to reconnect...")
        self._connected = False
        return await self.connect()
    
    async def publish_event(
        self,
        routing_key: str,
        event_data: Dict[str, Any]
    ) -> bool:
        """
        Publish an event to RabbitMQ.
        
        Args:
            routing_key: RabbitMQ routing key for the event
            event_data: Event data to publish (will be JSON serialized)
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        # w publish_event – lepsza diagnostyka wyłączonych eventów:
        if not self.config.should_enable_events():
            logger.warning("Event publishing DISABLED by config; message skipped",
                        extra={"routing_key": routing_key, "event_sample": str(event_data)[:200]})
            return False  # lub True, ale przynajmniej WARNING
            
        try:
            # Ensure we're connected
            if not await self._ensure_connection():
                logger.error("Cannot publish event: not connected to RabbitMQ")
                return False
            
            if not self.exchange:
                logger.error("Exchange not initialized")
                return False
            
            # Convert Pydantic models to dict if necessary
            if isinstance(event_data, BaseModel):
                event_data = event_data.model_dump()
            
            # Create message
            message_body = json.dumps(event_data).encode()
            message = Message(
                body=message_body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            # Publish message
            await self.exchange.publish(
                message=message,
                routing_key=routing_key,
                mandatory=True
            )
            
            logger.info(
                f"Published event to RabbitMQ",
                extra={
                    "routing_key": routing_key,
                    "deployment_id": event_data.get("deploymentId", "unknown")
                }
            )
            logger.debug(f"Event data: {event_data}")
            
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to publish event to RabbitMQ: {e}",
                extra={
                    "routing_key": routing_key,
                    "error": str(e)
                }
            )
            # Mark as disconnected to trigger reconnection on next attempt
            self._connected = False
            return False
    
    async def publish_json(
        self,
        routing_key: str,
        data: Any
    ) -> bool:
        """
        Publish a Pydantic model or dict as JSON event.
        
        Args:
            routing_key: RabbitMQ routing key
            data: Pydantic model or dict to publish
            
        Returns:
            bool: True if published successfully
        """
        if isinstance(data, BaseModel):
            event_data = data.model_dump()
        else:
            event_data = data
            
        return await self.publish_event(routing_key, event_data)
    
    async def close(self) -> None:
        """
        Close the RabbitMQ connection gracefully.
        """
        async with self._lock:
            try:
                if self.channel and not self.channel.is_closed:
                    await self.channel.close()
                    logger.debug("Closed RabbitMQ channel")
                    
                if self.connection and not self.connection.is_closed:
                    await self.connection.close()
                    logger.info("Closed RabbitMQ connection")
                    
            except Exception as e:
                logger.error(f"Error closing RabbitMQ connection: {e}")
            finally:
                self.connection = None
                self.channel = None
                self.exchange = None
                self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """
        Check if currently connected to RabbitMQ.
        
        Returns:
            bool: True if connected
        """
        return (
            self._connected
            and self.connection is not None
            and not self.connection.is_closed
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()