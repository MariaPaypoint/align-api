from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class AlignmentStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ModelType(enum.Enum):
    ACOUSTIC = "acoustic"
    G2P = "g2p"
    DICTIONARY = "dictionary"


class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    models = relationship("MFAModel", back_populates="language")


class MFAModel(Base):
    __tablename__ = "mfa_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    model_type = Column(Enum(ModelType), nullable=False)
    version = Column(String(50), nullable=False)
    variant = Column(String(100), nullable=True)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    language = relationship("Language", back_populates="models")

    # Unique constraint for name, type, version combination
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )


class AlignmentQueue(Base):
    __tablename__ = "alignment_queue"

    id = Column(Integer, primary_key=True, index=True)
    audio_file_path = Column(String(500), nullable=False)
    text_file_path = Column(String(500), nullable=False)
    original_audio_filename = Column(String(255), nullable=False)
    original_text_filename = Column(String(255), nullable=False)
    
    # Model parameters
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
