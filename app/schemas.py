from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.models import AlignmentStatus, ModelType

class AlignmentQueueBase(BaseModel):
    original_audio_filename: str
    original_text_filename: str

class AlignmentQueueCreate(AlignmentQueueBase):
    pass

class AlignmentQueueUpdate(BaseModel):
    status: Optional[AlignmentStatus] = None
    result_path: Optional[str] = None
    error_message: Optional[str] = None

class AlignmentQueueResponse(AlignmentQueueBase):
    id: int
    audio_file_path: str
    text_file_path: str
    status: AlignmentStatus
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Language schemas
class LanguageBase(BaseModel):
    code: str
    name: str

class LanguageCreate(LanguageBase):
    pass

class LanguageResponse(LanguageBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# MFA Model schemas
class MFAModelBase(BaseModel):
    name: str
    model_type: ModelType
    version: str
    variant: Optional[str] = None
    description: Optional[str] = None

class MFAModelCreate(MFAModelBase):
    language_id: int

class MFAModelResponse(MFAModelBase):
    id: int
    language_id: int
    language: LanguageResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Response for models update
class ModelsUpdateResponse(BaseModel):
    message: str
    updated_models: int
    updated_languages: int
