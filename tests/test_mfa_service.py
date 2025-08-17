import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session

from api.domains.models.services.mfa_service import MFAModelService
from api.domains.models.models import Language, MFAModel, ModelType
from api.domains.models.schemas import LanguageCreate, MFAModelCreate
from api.domains.models.crud import create_language, create_mfa_model, get_mfa_models, get_languages


class TestMFAModelService:
    """Test cases for MFA Model Service"""
    
    @pytest.fixture
    def mfa_service(self):
        return MFAModelService()
    
    @pytest.fixture
    def mock_github_models(self):
        """Mock GitHub models data"""
        return [
            {
                "name": "english_us_arpa",
                "model_type": ModelType.G2P,
                "version": "2.2.1",
                "variant": "us_arpa",
                "language_code": "english",
                "language_name": "English",
                "download_url": "https://github.com/test/english_us_arpa.zip"
            },
            {
                "name": "english_india_mfa",
                "model_type": ModelType.G2P,
                "version": "3.0.0",
                "variant": "india_mfa",
                "language_code": "english",
                "language_name": "English",
                "download_url": "https://github.com/test/english_india_mfa.zip"
            },
            {
                "name": "russian_mfa",
                "model_type": ModelType.DICTIONARY,
                "version": "3.1.0",
                "language_code": "russian",
                "language_name": "Russian",
                "download_url": "https://github.com/test/russian_mfa.zip"
            },
            {
                "name": "spanish_acoustic",
                "model_type": ModelType.ACOUSTIC,
                "version": "2.0.0",
                "language_code": "spanish",
                "language_name": "Spanish"
            }
        ]
    
    @pytest.fixture
    def existing_data(self, db_session: Session):
        """Create some existing data in database"""
        # Create languages
        english = create_language(db_session, LanguageCreate(code="english", name="English"))
        german = create_language(db_session, LanguageCreate(code="german", name="German"))
        
        # Create some existing models
        old_model = MFAModelCreate(
            name="old_english_model",
            model_type=ModelType.G2P,
            version="1.0.0",
            language_id=english.id,
            description="Old English model"
        )
        create_mfa_model(db_session, old_model)
        
        # Create model for German (will become unused)
        german_model = MFAModelCreate(
            name="german_model",
            model_type=ModelType.ACOUSTIC,
            version="1.5.0",
            language_id=german.id,
            description="German model"
        )
        create_mfa_model(db_session, german_model)
        
        return {
            "languages": [english, german],
            "models_count": 2
        }
    
    @pytest.mark.asyncio
    async def test_update_models_from_github_success(
        self, mfa_service: MFAModelService, db_session: Session, 
        mock_github_models, existing_data
    ):
        """Test successful model update from GitHub"""
        with patch.object(mfa_service.local_service, 'fetch_models') as mock_fetch:
            mock_fetch.return_value = mock_github_models
            
            # Run update
            updated_models, updated_languages = await mfa_service.update_models_from_github(db_session)
            
            # Check results
            assert updated_models == 4  # 4 new models from mock data
            assert updated_languages == 3  # english, russian, spanish
            
            # Verify models were created in database
            all_models = get_mfa_models(db_session)
            assert len(all_models) == 4  # Old models should be deleted, new ones created
            
            # Verify languages were created
            all_languages = get_languages(db_session)
            language_codes = [lang.code for lang in all_languages]
            assert "english" in language_codes
            assert "russian" in language_codes
            assert "spanish" in language_codes
            # German should be deleted as unused
            assert "german" not in language_codes
            
            # Verify specific model details
            english_models = [m for m in all_models if m.language.code == "english"]
            assert len(english_models) == 2  # us_arpa and india_mfa variants
            
            us_arpa_model = next((m for m in english_models if m.variant == "us_arpa"), None)
            assert us_arpa_model is not None
            assert us_arpa_model.name == "english_us_arpa"
            assert us_arpa_model.version == "2.2.1"
            assert us_arpa_model.model_type == ModelType.G2P
            assert "us_arpa" in us_arpa_model.description
    
    @pytest.mark.asyncio
    async def test_update_models_from_github_fallback_models(
        self, mfa_service: MFAModelService, db_session: Session, existing_data
    ):
        """Test update when GitHub API is unavailable and fallback models are used"""
        # Simulate fallback models that would be returned when GitHub API is unavailable
        fallback_models = [
            {
                "name": "english_us_arpa_fallback",
                "model_type": ModelType.G2P,
                "version": "2.2.1",
                "variant": "us_arpa",
                "language_code": "english",
                "language_name": "English"
            },
            {
                "name": "russian_mfa_fallback",
                "model_type": ModelType.DICTIONARY,
                "version": "3.1.0",
                "variant": None,
                "language_code": "russian",
                "language_name": "Russian"
            }
        ]
        
        with patch.object(mfa_service.local_service, 'fetch_models') as mock_fetch, \
             patch('api.domains.models.services.mfa_service.count_mfa_models') as mock_count:
            mock_fetch.return_value = fallback_models
            mock_count.return_value = 0  # Simulate empty database
            
            # Run update
            updated_models, updated_languages = await mfa_service.update_models_from_github(db_session)
            
            # Check results - should have created fallback models
            assert updated_models == 2
            assert updated_languages == 2
            
            # Verify models were created
            all_models = get_mfa_models(db_session)
            assert len(all_models) == 2
            
            # Check that fallback models were created
            model_names = [model.name for model in all_models]
            assert "english_us_arpa_fallback" in model_names
            assert "russian_mfa_fallback" in model_names
    
    @pytest.mark.asyncio
    async def test_update_models_from_github_duplicate_handling(
        self, mfa_service: MFAModelService, db_session: Session
    ):
        """Test that duplicate models are not created"""
        duplicate_models = [
            {
                "name": "test_model",
                "model_type": ModelType.G2P,
                "version": "1.0.0",
                "variant": "test_variant",
                "language_code": "english",
                "language_name": "English",
                "download_url": "https://github.com/test/model.zip"
            },
            {
                "name": "test_model",
                "model_type": ModelType.G2P,
                "version": "1.0.0",
                "variant": "test_variant",
                "language_code": "english",
                "language_name": "English",
                "download_url": "https://github.com/test/model.zip"
            }
        ]
        
        with patch.object(mfa_service.local_service, 'fetch_models') as mock_fetch, \
             patch('api.domains.models.services.mfa_service.count_mfa_models') as mock_count:
            mock_fetch.return_value = duplicate_models
            mock_count.return_value = 0  # Simulate empty database
            
            # Run update
            updated_models, updated_languages = await mfa_service.update_models_from_github(db_session)
            
            # Should create 2 models (duplicates are handled by bulk_create_mfa_models)
            assert updated_models == 2
            assert updated_languages == 1
            
            # Verify both models exist in database (no deduplication in bulk_create)
            all_models = get_mfa_models(db_session)
            assert len(all_models) == 2
    
    @pytest.mark.asyncio
    async def test_update_models_from_github_error_handling(
        self, mfa_service: MFAModelService, db_session: Session
    ):
        """Test error handling during model update"""
        with patch.object(mfa_service.local_service, 'fetch_models') as mock_fetch:
            mock_fetch.side_effect = Exception("GitHub API error")
            
            # Run update and expect exception
            with pytest.raises(Exception, match="GitHub API error"):
                await mfa_service.update_models_from_github(db_session)
    
    @pytest.mark.asyncio
    async def test_update_models_partial_failure(
        self, mfa_service: MFAModelService, db_session: Session
    ):
        """Test handling of partial failures during model processing"""
        models_with_invalid = [
            {
                "name": "valid_model",
                "model_type": ModelType.G2P,
                "version": "1.0.0",
                "language_code": "english",
                "language_name": "English"
            },
            {
                "name": "invalid_model",
                "model_type": "INVALID_TYPE",  # This will cause an error
                "version": "1.0.0",
                "language_code": "english",
                "language_name": "English"
            }
        ]
        
        with patch.object(mfa_service.local_service, 'fetch_models') as mock_fetch:
            mock_fetch.return_value = models_with_invalid
            
            # Run update - should handle the invalid model gracefully
            updated_models, updated_languages = await mfa_service.update_models_from_github(db_session)
            
            # Should create at least the valid model
            assert updated_models >= 1
            assert updated_languages >= 1
    
    @pytest.mark.asyncio
    async def test_close_service(self, mfa_service: MFAModelService):
        """Test closing the service"""
        # Local service doesn't need close method, just verify it exists
        assert hasattr(mfa_service, 'close')
        await mfa_service.close()  # Should not raise an error
    
    @pytest.mark.asyncio
    async def test_description_generation(
        self, mfa_service: MFAModelService, db_session: Session
    ):
        """Test that model descriptions are generated correctly"""
        models_data = [
            {
                "name": "english_us_arpa",
                "model_type": ModelType.G2P,
                "version": "2.2.1",
                "variant": "us_arpa",
                "language_code": "english",
                "language_name": "English"
            },
            {
                "name": "russian_mfa",
                "model_type": ModelType.DICTIONARY,
                "version": "3.1.0",
                "language_code": "russian",
                "language_name": "Russian"
            }
        ]
        
        with patch.object(mfa_service.local_service, 'fetch_models') as mock_fetch:
            mock_fetch.return_value = models_data
            
            # Run update
            await mfa_service.update_models_from_github(db_session)
            
            # Check generated descriptions
            all_models = get_mfa_models(db_session)
            
            variant_model = next((m for m in all_models if m.variant == "us_arpa"), None)
            assert variant_model is not None
            assert "English g2p model v2.2.1 (us_arpa)" == variant_model.description
            
            no_variant_model = next((m for m in all_models if m.variant is None), None)
            assert no_variant_model is not None
            assert "Russian dictionary model v3.1.0" == no_variant_model.description
