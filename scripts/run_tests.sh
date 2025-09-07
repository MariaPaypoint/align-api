#!/bin/bash
set -e

echo "Starting test environment..."

# Start all required services
docker compose up -d mysql rabbitmq minio openobserve
docker compose up -d --wait mysql rabbitmq minio

# Run tests
echo "Running tests..."
docker compose build tests
docker compose run --rm tests

# Clean up
echo "Cleaning up test environment..."
docker compose down
