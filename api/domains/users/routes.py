"""
User management routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from api.database import get_db
from api.domains.users.models import User
from api.domains.users.schemas import QuotaResponse, FileMetadataResponse
from api.domains.users.crud import UserService
from api.domains.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/quota", response_model=QuotaResponse)
async def get_user_quota(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's quota information."""
    quota = UserService.get_user_quota(db, current_user.id)
    if not quota:
        raise HTTPException(status_code=404, detail="User quota not found")
    return quota


@router.get("/files", response_model=List[FileMetadataResponse])
async def get_user_files(
    file_type: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's files."""
    files = UserService.get_user_files(db, current_user.id, file_type)
    
    return [
        FileMetadataResponse(
            id=file.id,
            original_filename=file.original_filename,
            file_type=file.file_type.value,
            file_size=file.file_size,
            mime_type=file.mime_type,
            created_at=file.created_at,
            expires_at=file.expires_at,
            access_count=file.access_count
        ) for file in files
    ]
