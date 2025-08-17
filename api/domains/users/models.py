"""
User domain models.
"""

from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, Numeric, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from api.database import Base


class UserRole(enum.Enum):
    user = "user" 
    admin = "admin"


class FileType(enum.Enum):
    AUDIO = "audio"
    TEXT = "text"
    RESULT = "result"


class SubscriptionType(Base):
    """Subscription types for users."""
    __tablename__ = "subscription_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    total_storage_limit = Column(BigInteger, nullable=False)  # in bytes
    max_concurrent_tasks = Column(Integer, nullable=False)
    price_monthly = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    users = relationship("User", back_populates="subscription_type")


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)
    subscription_type_id = Column(Integer, ForeignKey("subscription_types.id"), nullable=False)
    used_storage = Column(BigInteger, default=0, nullable=False)  # in bytes
    subscription_ends_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    subscription_type = relationship("SubscriptionType", back_populates="users")
    file_metadata = relationship("FileStorageMetadata", back_populates="user")


class FileStorageMetadata(Base):
    """File storage metadata for tracking files in MinIO."""
    __tablename__ = "file_storage_metadata"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("alignment_queue.id"), nullable=True, index=True)
    file_type = Column(Enum(FileType), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)  # Path in MinIO
    file_size = Column(BigInteger, nullable=False)  # in bytes
    mime_type = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0, nullable=False)

    # Relationships  
    user = relationship("User", back_populates="file_metadata")
