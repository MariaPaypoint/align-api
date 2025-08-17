from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.database import Base
import enum


class AlignmentStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AlignmentQueue(Base):
    __tablename__ = "alignment_queue"

    id = Column(Integer, primary_key=True, index=True)
    audio_file_path = Column(String(500), nullable=False)
    text_file_path = Column(String(500), nullable=False)
    original_audio_filename = Column(String(255), nullable=False)
    original_text_filename = Column(String(255), nullable=False)
    
    # User and task tracking
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    celery_task_id = Column(String(155), nullable=True)
    
    # Model parameters with FK references
    acoustic_model_id = Column(Integer, ForeignKey("mfa_models.id"), nullable=True)
    dictionary_model_id = Column(Integer, ForeignKey("mfa_models.id"), nullable=True)
    g2p_model_id = Column(Integer, ForeignKey("mfa_models.id"), nullable=True)
    
    # Legacy model parameters (for backward compatibility)
    acoustic_model_name = Column(String(255), nullable=False)
    acoustic_model_version = Column(String(50), nullable=False)
    dictionary_model_name = Column(String(255), nullable=False)
    dictionary_model_version = Column(String(50), nullable=False)
    g2p_model_name = Column(String(255), nullable=True)
    g2p_model_version = Column(String(50), nullable=True)
    
    status = Column(Enum(AlignmentStatus), default=AlignmentStatus.PENDING, nullable=False)
    result_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("api.domains.users.models.User")
