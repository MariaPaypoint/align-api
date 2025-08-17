"""
User domain CRUD operations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from .models import User, SubscriptionType, FileStorageMetadata, UserRole
from .schemas import UserCreate, QuotaResponse
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user operations."""

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Create new user with free subscription."""
        # Get free subscription type
        free_subscription = db.query(SubscriptionType).filter(
            SubscriptionType.name == "free"
        ).first()
        
        if not free_subscription:
            raise ValueError("Free subscription type not found")

        # Hash password
        password_hash = get_password_hash(user.password)

        # Create user
        db_user = User(
            email=user.email,
            username=user.username,
            password_hash=password_hash,
            role=UserRole.user,
            subscription_type_id=free_subscription.id,
            used_storage=0
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"Created new user: {user.username} ({user.email})")
        return db_user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user by username and password."""
        user = UserService.get_user_by_username(db, username)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def get_user_quota(db: Session, user_id: int) -> Optional[QuotaResponse]:
        """Get user quota information."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        available_storage = max(0, user.subscription_type.total_storage_limit - user.used_storage)
        
        return QuotaResponse(
            total_storage_limit=user.subscription_type.total_storage_limit,
            used_storage=user.used_storage,
            available_storage=available_storage,
            max_concurrent_tasks=user.subscription_type.max_concurrent_tasks,
            subscription_type=user.subscription_type.display_name,
            subscription_ends_at=user.subscription_ends_at
        )

    @staticmethod
    def update_user_storage(db: Session, user_id: int, storage_change: int):
        """Update user storage usage."""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.used_storage = max(0, user.used_storage + storage_change)
            db.commit()
            logger.info(f"Updated storage for user {user_id}: {storage_change} bytes")

    @staticmethod
    def check_storage_quota(db: Session, user_id: int, required_space: int) -> bool:
        """Check if user has enough storage quota."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        available_space = user.subscription_type.total_storage_limit - user.used_storage
        return available_space >= required_space

    @staticmethod
    def get_user_files(db: Session, user_id: int, file_type: Optional[str] = None) -> List[FileStorageMetadata]:
        """Get user's files, optionally filtered by type."""
        query = db.query(FileStorageMetadata).filter(FileStorageMetadata.user_id == user_id)
        
        if file_type:
            query = query.filter(FileStorageMetadata.file_type == file_type)
        
        return query.order_by(FileStorageMetadata.created_at.desc()).all()

    @staticmethod
    def add_file_metadata(
        db: Session, 
        user_id: int, 
        task_id: Optional[int], 
        file_type: str,
        original_filename: str,
        storage_path: str,
        file_size: int,
        mime_type: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> FileStorageMetadata:
        """Add file metadata record."""
        file_metadata = FileStorageMetadata(
            user_id=user_id,
            task_id=task_id,
            file_type=file_type,
            original_filename=original_filename,
            storage_path=storage_path,
            file_size=file_size,
            mime_type=mime_type,
            expires_at=expires_at
        )
        
        db.add(file_metadata)
        db.commit()
        db.refresh(file_metadata)
        
        return file_metadata

    @staticmethod
    def get_expired_files(db: Session) -> List[FileStorageMetadata]:
        """Get all expired files for cleanup."""
        return db.query(FileStorageMetadata).filter(
            and_(
                FileStorageMetadata.expires_at.is_not(None),
                FileStorageMetadata.expires_at <= datetime.utcnow()
            )
        ).all()
