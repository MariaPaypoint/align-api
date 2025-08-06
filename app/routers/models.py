from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import (
    MFAModelResponse, 
    LanguageResponse, 
    ModelsUpdateResponse
)
from app.crud import get_mfa_models, get_languages, get_mfa_models_by_type
from app.models import ModelType
from app.services.mfa_service import MFAModelService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["models"])

@router.get("/", response_model=List[MFAModelResponse])
def get_models(
    skip: int = 0,
    limit: int = 100,
    language: str = None,
    db: Session = Depends(get_db)
):
    """Get all MFA models with optional language filter"""
    models = get_mfa_models(db, skip=skip, limit=limit, language_code=language)
    return models

@router.get("/by-type/{model_type}", response_model=List[MFAModelResponse])
def get_models_by_type(
    model_type: ModelType,
    language: str = None,
    db: Session = Depends(get_db)
):
    """Get MFA models by type with optional language filter"""
    models = get_mfa_models_by_type(db, model_type=model_type, language_code=language)
    return models

@router.get("/languages", response_model=List[LanguageResponse])
def get_supported_languages(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all supported languages"""
    languages = get_languages(db, skip=skip, limit=limit)
    return languages

@router.post("/update", response_model=ModelsUpdateResponse)
async def update_models(
    db: Session = Depends(get_db)
):
    """
    Update MFA models from GitHub repository
    Now uses built-in fallback when GitHub API is unavailable
    """
    logger.info("=== ROUTER: Starting models update ===")
    mfa_service = MFAModelService()
    
    try:
        logger.info("=== ROUTER: Calling mfa_service.update_models_from_github ===")
        updated_models, updated_languages = await mfa_service.update_models_from_github(db)
        
        logger.info(f"=== ROUTER: Models update completed: {updated_models} models, {updated_languages} languages ===")
        
        return ModelsUpdateResponse(
            message="Models updated successfully",
            updated_models=updated_models,
            updated_languages=updated_languages
        )
    
    except Exception as e:
        logger.error(f"=== ROUTER: Error updating models: {e} ===")
        import traceback
        logger.error(f"=== ROUTER: Traceback: {traceback.format_exc()} ===")
        raise HTTPException(status_code=500, detail=f"Failed to update models: {str(e)}")
    finally:
        await mfa_service.close()
