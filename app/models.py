from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func
from app.database import Base
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
    status = Column(Enum(AlignmentStatus), default=AlignmentStatus.PENDING, nullable=False)
    result_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
