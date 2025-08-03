from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models import AlignmentStatus

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
