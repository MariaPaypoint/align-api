from sqlalchemy.orm import Session
from typing import Tuple
from app.domains.models.services.local_mfa_service import LocalMFAService
from app.domains.models.crud import (
    get_or_create_language, 
    get_or_create_languages_bulk,
    create_mfa_model, 
    bulk_create_mfa_models,
    get_mfa_model_by_name_type_version,
    delete_all_mfa_models,
    delete_unused_languages,
    count_mfa_models
)
from app.domains.models.schemas import MFAModelCreate
import logging

logger = logging.getLogger(__name__)

class MFAModelService:
    """Service for managing MFA models"""
    
    def __init__(self):
        self.local_service = LocalMFAService()
    
    async def update_models_from_github(self, db: Session) -> Tuple[int, int]:
        """
        Update MFA models from GitHub repository
        Returns tuple of (updated_models_count, updated_languages_count)
        """
        try:
            # Fetch models from local repository (includes git pull)
            logger.info("=== MFA SERVICE: Starting update_models_from_github ===")
            logger.info("=== MFA SERVICE: Calling local_service.fetch_models ===")
            local_models = await self.local_service.fetch_models()
            logger.info(f"=== MFA SERVICE: Got {len(local_models)} models from local repository ===")
            
            if not local_models:
                logger.warning("=== MFA SERVICE: No models found in local repository ===")
                return 0, 0
            
            # Check if we already have models in database
            existing_models_count = count_mfa_models(db)
            logger.info(f"=== MFA SERVICE: Found {existing_models_count} existing models in database ===")
            
            # If we already have the same number of models, skip update
            if existing_models_count == len(local_models):
                logger.info("=== MFA SERVICE: Database already has same number of models, skipping update ===")
                return 0, 0
            
            # Clear existing models and unused languages
            logger.info("=== MFA SERVICE: Clearing existing models ===")
            deleted_models = delete_all_mfa_models(db)
            deleted_languages = delete_unused_languages(db)
            logger.info(f"=== MFA SERVICE: Deleted {deleted_models} models and {deleted_languages} languages ===")
            
            
            # Extract unique languages first
            unique_languages = {}
            for model_data in local_models:
                code = model_data["language_code"]
                name = model_data["language_name"]
                unique_languages[code] = {'code': code, 'name': name}
            
            # Bulk create/get all languages
            logger.info(f"=== MFA SERVICE: Creating {len(unique_languages)} languages ===")
            language_map = get_or_create_languages_bulk(db, list(unique_languages.values()))
            
            # Prepare all models
            models_to_create = []
            logger.info(f"=== MFA SERVICE: Preparing {len(local_models)} models ===")
            
            for i, model_data in enumerate(local_models):
                if i % 100 == 0:  # Log progress every 100 models
                    logger.info(f"=== MFA SERVICE: Preparing model {i+1}/{len(local_models)} ===")
                try:
                    # Get language from our map
                    language = language_map[model_data["language_code"]]
                    
                    # Create description with variant info if available
                    variant_info = f" ({model_data['variant']})" if model_data.get('variant') else ""
                    description = f"{model_data['language_name']} {model_data['model_type'].value} model v{model_data['version']}{variant_info}"
                    
                    model_create = MFAModelCreate(
                        name=model_data["name"],
                        model_type=model_data["model_type"],
                        version=model_data["version"],
                        variant=model_data.get("variant"),
                        language_id=language.id,
                        description=description
                    )
                    
                    models_to_create.append(model_create)
                    
                except Exception as e:
                    logger.error(f"Error processing model {model_data}: {e}")
                    continue
            
            # Bulk create all models
            logger.info(f"=== MFA SERVICE: Bulk creating {len(models_to_create)} models ===")
            created_models = bulk_create_mfa_models(db, models_to_create)
            
            logger.info(f"Successfully updated {created_models} models for {len(unique_languages)} languages")
            return created_models, len(unique_languages)
            
        except Exception as e:
            logger.error(f"Error updating models from GitHub: {e}")
            raise
        finally:
            # Local service doesn't need cleanup
            pass
    
    async def close(self):
        """Close the service and cleanup resources"""
        # Local service doesn't need cleanup
        pass
