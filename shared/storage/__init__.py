"""
Storage module for shared file operations.
"""

from .minio_service import minio_service, MinIOService

__all__ = ['minio_service', 'MinIOService']
