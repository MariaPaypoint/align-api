"""
User domain Pydantic schemas.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from .models import UserRole


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    username: str
    role: UserRole
    subscription_type_name: str
    used_storage: int
    subscription_ends_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuotaResponse(BaseModel):
    """Schema for user quota information."""
    total_storage_limit: int
    used_storage: int
    available_storage: int
    max_concurrent_tasks: int
    subscription_type: str
    subscription_ends_at: Optional[datetime] = None


class FileMetadataResponse(BaseModel):
    """Schema for file metadata response."""
    id: int
    original_filename: str
    file_type: str
    file_size: int
    mime_type: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int

    model_config = ConfigDict(from_attributes=True)
