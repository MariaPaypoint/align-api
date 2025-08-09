from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.domains.alignment.models import AlignmentStatus


# Model parameter schemas for alignment requests
class ModelParameter(BaseModel):
    name: str
    version: str


class AlignmentQueueBase(BaseModel):
    original_audio_filename: str
    original_text_filename: str


class AlignmentQueueCreate(AlignmentQueueBase):
    acoustic_model: ModelParameter
    dictionary_model: ModelParameter
    g2p_model: Optional[ModelParameter] = None


class AlignmentQueueUpdate(BaseModel):
    status: Optional[AlignmentStatus] = None
    result_path: Optional[str] = None
    error_message: Optional[str] = None


class AlignmentQueueResponse(AlignmentQueueBase):
    id: int
    audio_file_path: str
    text_file_path: str
    acoustic_model: ModelParameter
    dictionary_model: ModelParameter
    g2p_model: Optional[ModelParameter] = None
    status: AlignmentStatus
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_db_model(cls, db_model):
        """Create response from database model"""
        acoustic_model = ModelParameter(
            name=db_model.acoustic_model_name,
            version=db_model.acoustic_model_version
        )
        dictionary_model = ModelParameter(
            name=db_model.dictionary_model_name,
            version=db_model.dictionary_model_version
        )
        g2p_model = None
        if db_model.g2p_model_name and db_model.g2p_model_version:
            g2p_model = ModelParameter(
                name=db_model.g2p_model_name,
                version=db_model.g2p_model_version
            )
        
        return cls(
            id=db_model.id,
            audio_file_path=db_model.audio_file_path,
            text_file_path=db_model.text_file_path,
            original_audio_filename=db_model.original_audio_filename,
            original_text_filename=db_model.original_text_filename,
            acoustic_model=acoustic_model,
            dictionary_model=dictionary_model,
            g2p_model=g2p_model,
            status=db_model.status,
            result_path=db_model.result_path,
            error_message=db_model.error_message,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at
        )
