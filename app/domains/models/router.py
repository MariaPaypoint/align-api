from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.domains.models.schemas import (
    MFAModelResponse, 
    LanguageResponse, 
    ModelsUpdateResponse
)
from app.domains.models.crud import get_mfa_models, get_languages, get_mfa_models_by_type
from app.domains.models.models import ModelType
from app.domains.models.services.mfa_service import MFAModelService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["models"])

@router.get("/", 
    response_model=List[MFAModelResponse],
    summary="List MFA models",
    description="Retrieve all MFA models with optional language filtering and pagination."
)
def get_models(
    skip: int = 0,
    limit: int = 100,
    language: str = None,
    db: Session = Depends(get_db)
):
    """Get all MFA models with optional language filter and pagination."""
    models = get_mfa_models(db, skip=skip, limit=limit, language_code=language)
    return models

@router.get("/by-type/{model_type}", 
    response_model=List[MFAModelResponse],
    summary="Get models by type",
    description="Retrieve MFA models filtered by type (ACOUSTIC, DICTIONARY, G2P) with optional language filter."
)
def get_models_by_type(
    model_type: ModelType,
    language: str = None,
    db: Session = Depends(get_db)
):
    """Get MFA models filtered by type (ACOUSTIC, DICTIONARY, G2P) with optional language filter."""
    models = get_mfa_models_by_type(db, model_type=model_type, language_code=language)
    return models

@router.get("/languages", 
    response_model=List[LanguageResponse],
    summary="List supported languages",
    description="Retrieve all languages that have available MFA models."
)
def get_supported_languages(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all languages that have available MFA models with pagination."""
    languages = get_languages(db, skip=skip, limit=limit)
    return languages

@router.post("/update", 
    response_model=ModelsUpdateResponse,
    summary="Update models from GitHub",
    description="Fetch and update MFA models from the official GitHub repository.",
    responses={
        200: {"description": "Models updated successfully"},
        500: {"description": "Failed to update models"}
    }
)
async def update_models(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Fetch and update MFA models from the official GitHub repository."""
    try:
        service = MFAModelService()
        updated_models, updated_languages = await service.update_models_from_github(db)
        
        return ModelsUpdateResponse(
            message="Models updated successfully",
            updated_models=updated_models,
            updated_languages=updated_languages
        )
    except Exception as e:
        logger.error(f"Error updating models: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update models: {str(e)}"
        )
