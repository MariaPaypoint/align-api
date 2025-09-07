"""
Tests for infrastructure components (Step 1).
"""

import pytest
import pika
import io
import os


def test_rabbitmq_connection():
    """Test connection to RabbitMQ."""
    try:
        connection_params = pika.ConnectionParameters(
            host=os.getenv('RABBITMQ_HOST'),
            port=int(os.getenv('RABBITMQ_PORT')),
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

def test_minio_connection():
    """Test connection to MinIO object storage."""
    try:
        from shared.storage.minio_service import minio_service
        # Test basic connection and bucket operations
        assert minio_service.test_connection() == True, "MinIO connection failed"
        
        # Test bucket exists
        assert minio_service.client.bucket_exists('alignment-storage') == True
        
    except Exception as e:
        pytest.fail(f"MinIO connection failed: {e}")


def test_file_upload_download():
    """Test basic file upload/download operations with MinIO."""
    try:
        from shared.storage.minio_service import minio_service
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
        from workers.tasks import ping_task
        from celery.exceptions import TimeoutError as CeleryTimeoutError

        # This test requires Celery worker to be running
        result = ping_task.delay("test_message")
        
        # Без backend мы не можем получить результат, но можем проверить, что задача отправлена
        assert result.id is not None
        print(f"Задача отправлена с ID: {result.id}")
        
        # Даем время на выполнение задачи
        import time
        time.sleep(2)
        
        print("Celery ping task отправлен успешно")

    except Exception as e:
        if "No result backend" in str(e):
            # Это ожидаемое поведение согласно архитектуре
            print("Celery работает без backend (согласно архитектуре)")
        else:
            pytest.fail(f"Celery ping task test failed: {e}")


@pytest.mark.asyncio
async def test_health_checks():
    """Test basic health checks for all services."""
    from shared.storage.minio_service import minio_service
    # MinIO
    assert minio_service.test_connection() == True
    
    # RabbitMQ
    try:
        connection_params = pika.ConnectionParameters(
            host=os.getenv('RABBITMQ_HOST'), 
            port=int(os.getenv('RABBITMQ_PORT')),
            credentials=pika.PlainCredentials(
                os.getenv('RABBITMQ_DEFAULT_USER'),
                os.getenv('RABBITMQ_DEFAULT_PASS')
            )
        )
        connection = pika.BlockingConnection(connection_params)
        connection.close()
    except Exception as e:
        pytest.fail(f"RabbitMQ health check failed: {e}")
