"""
Tests for infrastructure components (Step 1).
"""

import pytest
import pika
import redis
import io
from shared.storage.minio_service import minio_service
from workers.tasks import ping_task


def test_rabbitmq_connection():
    """Test connection to RabbitMQ."""
    try:
        import os
        connection_params = pika.ConnectionParameters(
            host='localhost',
            port=5672,
            credentials=pika.PlainCredentials(
                os.getenv('RABBITMQ_DEFAULT_USER'),
                os.getenv('RABBITMQ_DEFAULT_PASS')
            )
        )
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        
        # Test basic operations
        test_queue = 'test_connection_queue'
        channel.queue_declare(queue=test_queue, durable=False)
        channel.queue_delete(queue=test_queue)
        
        connection.close()
        assert True
    except Exception as e:
        pytest.fail(f"RabbitMQ connection failed: {e}")


def test_redis_connection():
    """Test connection to Redis."""
    try:
        client = redis.Redis(host='localhost', port=6379, db=0)
        client.ping()
        
        # Test basic operations
        client.set('test_key', 'test_value')
        value = client.get('test_key')
        assert value.decode() == 'test_value'
        client.delete('test_key')
        
    except Exception as e:
        pytest.fail(f"Redis connection failed: {e}")


def test_minio_connection():
    """Test connection to MinIO."""
    try:
        # Test connection
        assert minio_service.test_connection() == True, "MinIO connection failed"
        
        # Test bucket exists
        assert minio_service.client.bucket_exists('alignment-storage') == True
        
    except Exception as e:
        pytest.fail(f"MinIO connection failed: {e}")


def test_file_upload_download():
    """Test basic file upload/download operations with MinIO."""
    try:
        # Test data
        test_content = b"Test file content for MinIO"
        test_path = "test/upload_test.txt"
        
        # Upload file
        file_stream = io.BytesIO(test_content)
        success = minio_service.upload_file(
            file_path=test_path,
            file_data=file_stream,
            file_size=len(test_content),
            content_type='text/plain'
        )
        assert success == True, "File upload failed"
        
        # Check file exists
        assert minio_service.file_exists(test_path) == True, "File not found after upload"
        
        # Download file
        downloaded_content = minio_service.download_file(test_path)
        assert downloaded_content == test_content, "Downloaded content doesn't match uploaded"
        
        # Clean up
        minio_service.delete_file(test_path)
        assert minio_service.file_exists(test_path) == False, "File not deleted"
        
    except Exception as e:
        pytest.fail(f"File upload/download test failed: {e}")


def test_celery_ping_task():
    """Test Celery ping task execution."""
    try:
        # This test requires Celery worker to be running
        result = ping_task.delay("test_message")
        
        # Wait for result (with timeout)
        task_result = result.get(timeout=10)
        
        assert task_result['status'] == 'success'
        assert 'test_message' in task_result['message']
        assert 'task_id' in task_result
        assert 'timestamp' in task_result
        
    except Exception as e:
        pytest.fail(f"Celery ping task test failed: {e}")


@pytest.mark.asyncio
async def test_health_checks():
    """Test basic health checks for all services."""
    # MinIO
    assert minio_service.test_connection() == True
    
    # Redis
    try:
        client = redis.Redis(host='localhost', port=6379, db=0)
        client.ping()
    except Exception as e:
        pytest.fail(f"Redis health check failed: {e}")
    
    # RabbitMQ
    try:
        connection_params = pika.ConnectionParameters(
            host='localhost', 
            port=5672,
            credentials=pika.PlainCredentials(
                os.getenv('RABBITMQ_DEFAULT_USER'),
                os.getenv('RABBITMQ_DEFAULT_PASS')
            )
        )
        connection = pika.BlockingConnection(connection_params)
        connection.close()
    except Exception as e:
        pytest.fail(f"RabbitMQ health check failed: {e}")
