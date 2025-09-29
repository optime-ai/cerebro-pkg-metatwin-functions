"""
Configuration module for RabbitMQ integration.

This module manages environment variables for RabbitMQ connection
and event publishing functionality.
"""
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RabbitMQConfig(BaseSettings):
    """
    RabbitMQ configuration from environment variables.
    
    All environment variables use the CRBR_ prefix for namespace isolation.
    """
    
    # Deployment Configuration
    deployment_id: str = "local-dev"
    
    # RabbitMQ Connection Settings
    rabbitmq_hostname: Optional[str] = None
    rabbitmq_port: int = Field(default=5672, ge=1, le=65535)
    rabbitmq_username: Optional[str] = None
    rabbitmq_password: Optional[str] = None
    rabbitmq_vhost: str = "/"
    rabbitmq_exchange: str = "event.exchange"
    
    # Feature Flags
    enable_events: bool = True
    health_check_interval: int = Field(default=60, ge=1, le=3600)  # seconds (1s to 1h)
    
    # Connection Configuration
    connection_timeout: int = Field(default=10, ge=1, le=300)  # seconds (1s to 5min)
    max_retries: int = Field(default=5, ge=0, le=100)
    retry_delay: int = Field(default=5, ge=1, le=60)  # seconds
    
    # Event Routing Keys
    routing_key_deployment_started: str = "routing.event.metatwin-functions.function.deployment.started"
    routing_key_deployment_healthy: str = "routing.event.metatwin-functions.function.deployment.healthy"
    
    model_config = SettingsConfigDict(
        env_prefix="CRBR_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields not defined in the model
    )
    
    def is_rabbitmq_configured(self) -> bool:
        """
        Check if RabbitMQ configuration is complete.
        
        Returns:
            bool: True if all required RabbitMQ settings are provided
        """
        return all([
            self.rabbitmq_hostname,
            self.rabbitmq_username,
            self.rabbitmq_password
        ])
    
    def get_missing_rabbitmq_config(self) -> List[str]:
        """
        Get list of missing RabbitMQ configuration parameters.
        
        Returns:
            List of parameter names that are missing
        """
        missing = []
        if not self.rabbitmq_hostname:
            missing.append("CRBR_RABBITMQ_HOSTNAME")
        if not self.rabbitmq_username:
            missing.append("CRBR_RABBITMQ_USERNAME")
        if not self.rabbitmq_password:
            missing.append("CRBR_RABBITMQ_PASSWORD")
        return missing
    
    def should_enable_events(self) -> bool:
        """
        Determine if event publishing should be enabled.
        
        Returns:
            bool: True if events are enabled and RabbitMQ is configured
        """
        return self.enable_events and self.is_rabbitmq_configured()
    
    def get_rabbitmq_url(self) -> Optional[str]:
        """
        Build RabbitMQ connection URL from configuration.
        
        Returns:
            Optional[str]: AMQP connection URL or None if not configured
        """
        if not self.is_rabbitmq_configured():
            return None
            
        return (
            f"amqp://{self.rabbitmq_username}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_hostname}:{self.rabbitmq_port}"
            f"{self.rabbitmq_vhost}"
        )
    
    def __repr__(self) -> str:
        """Safe string representation without sensitive data."""
        return (
            f"RabbitMQConfig("
            f"deployment_id='{self.deployment_id}', "
            f"hostname='{self.rabbitmq_hostname or 'not set'}', "
            f"port={self.rabbitmq_port}, "
            f"exchange='{self.rabbitmq_exchange}', "
            f"events_enabled={self.enable_events}, "
            f"configured={self.is_rabbitmq_configured()}"
            ")"
        )


# Singleton instance that can be imported and reused
config = RabbitMQConfig()