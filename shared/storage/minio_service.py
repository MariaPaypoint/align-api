"""
MinIO File Storage Service for alignment API.
"""

import os
import io
from typing import Optional, BinaryIO, List
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv

load_dotenv()


class MinIOService:
    """MinIO service for file storage operations."""
    
    def __init__(self):
        self.endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
        self.access_key = os.getenv('MINIO_ROOT_USER', 'minioadmin')
        self.secret_key = os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin')
        self.secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
        self.bucket_name = 'alignment-storage'
        
        # Initialize MinIO client
        self.client = Minio(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"Error creating bucket: {e}")
    
    def upload_file(self, file_path: str, file_data: BinaryIO, file_size: int, 
                   content_type: str = 'application/octet-stream') -> bool:
        """
        Upload file to MinIO storage.
        
        Args:
            file_path: Path in storage (e.g., "user_123/task_456/audio.wav")
            file_data: File data stream
            file_size: Size of file in bytes
            content_type: MIME type of file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                data=file_data,
                length=file_size,
                content_type=content_type
            )
            return True
        except S3Error as e:
            print(f"Error uploading file {file_path}: {e}")
            return False
    
    def download_file(self, file_path: str) -> Optional[bytes]:
        """
        Download file from MinIO storage.
        
        Args:
            file_path: Path in storage
            
        Returns:
            bytes: File content if successful, None otherwise
        """
        try:
            response = self.client.get_object(self.bucket_name, file_path)
            return response.read()
        except S3Error as e:
            print(f"Error downloading file {file_path}: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from MinIO storage.
        
        Args:
            file_path: Path in storage
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.remove_object(self.bucket_name, file_path)
            return True
        except S3Error as e:
            print(f"Error deleting file {file_path}: {e}")
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            file_path: Path in storage
            
        Returns:
            bool: True if file exists
        """
        try:
            self.client.stat_object(self.bucket_name, file_path)
            return True
        except S3Error:
            return False
    
    def list_files(self, prefix: str = "") -> List[str]:
        """
        List files with given prefix.
        
        Args:
            prefix: Path prefix to filter files
            
        Returns:
            List[str]: List of file paths
        """
        try:
            objects = self.client.list_objects(
                self.bucket_name, 
                prefix=prefix, 
                recursive=True
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing files with prefix {prefix}: {e}")
            return []
    
    def get_file_url(self, file_path: str, expires: int = 3600) -> Optional[str]:
        """
        Get presigned URL for file access.
        
        Args:
            file_path: Path in storage
            expires: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Presigned URL if successful, None otherwise
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                expires=expires
            )
            return url
        except S3Error as e:
            print(f"Error generating URL for {file_path}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test connection to MinIO server.
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Try to list buckets
            list(self.client.list_buckets())
            return True
        except Exception as e:
            print(f"MinIO connection test failed: {e}")
            return False


# Global instance
minio_service = MinIOService()
