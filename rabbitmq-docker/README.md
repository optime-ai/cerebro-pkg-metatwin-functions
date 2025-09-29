# RabbitMQ Docker Setup

This directory contains configuration for running RabbitMQ locally for testing Cerebro MetaTwin Functions.

## Quick Start

```bash
# Start RabbitMQ
docker-compose up -d

# Stop RabbitMQ
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Access

- **RabbitMQ Management UI**: http://localhost:15672
- **Username**: `cerebro`
- **Password**: `cerebro123`
- **AMQP Port**: 5672

## Configuration Files

- `docker-compose.yml` - Docker Compose configuration for RabbitMQ
- `definitions.json` - RabbitMQ definitions (exchanges, queues, bindings)

## Event Routing

The setup creates:
- Exchange: `event.exchange` (topic type)
- Queues:
  - `event.metatwin-functions.function.deployment.started`
  - `event.metatwin-functions.function.deployment.healthy`
- Bindings with routing keys:
  - `routing.event.metatwin-functions.function.deployment.started.#`
  - `routing.event.metatwin-functions.function.deployment.healthy.#`

## Environment Variables

Configure your `.env` file in the project root:

```bash
CRBR_RABBITMQ_HOSTNAME=localhost
CRBR_RABBITMQ_PORT=5672
CRBR_RABBITMQ_USERNAME=cerebro
CRBR_RABBITMQ_PASSWORD=cerebro123
CRBR_RABBITMQ_VHOST=/
CRBR_RABBITMQ_EXCHANGE=event.exchange
```