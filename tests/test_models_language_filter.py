import pytest
from fastapi.testclient import TestClient
from app.domains.models.models import ModelType
from app.domains.models.crud import create_mfa_model, create_language
from app.domains.models.schemas import MFAModelCreate, LanguageCreate


class TestModelsLanguageFilter:
    """Tests for models endpoints with language filtering"""
    
    @pytest.fixture
    def setup_multilang_models(self, db_session):
        """Create test models for multiple languages"""
        # Create languages
        english = create_language(db_session, LanguageCreate(code="english", name="English"))
        russian = create_language(db_session, LanguageCreate(code="russian", name="Russian"))
        spanish = create_language(db_session, LanguageCreate(code="spanish", name="Spanish"))
        
        # Create English models
        en_acoustic = create_mfa_model(db_session, MFAModelCreate(
            name="english_acoustic",
            model_type=ModelType.ACOUSTIC,
            version="2.0.0",
            language_id=english.id,
            description="English acoustic model"
        ))
        
        en_dictionary = create_mfa_model(db_session, MFAModelCreate(
            name="english_dictionary",
            model_type=ModelType.DICTIONARY,
            version="2.0.0",
            language_id=english.id,
            description="English dictionary"
        ))
        
        en_g2p = create_mfa_model(db_session, MFAModelCreate(
            name="english_g2p",
            model_type=ModelType.G2P,
            version="2.0.0",
            language_id=english.id,
            description="English G2P model"
        ))
        
        # Create Russian models
        ru_acoustic = create_mfa_model(db_session, MFAModelCreate(
            name="russian_acoustic",
            model_type=ModelType.ACOUSTIC,
            version="1.5.0",
            language_id=russian.id,
            description="Russian acoustic model"
        ))
        
        ru_dictionary = create_mfa_model(db_session, MFAModelCreate(
            name="russian_dictionary",
            model_type=ModelType.DICTIONARY,
            version="1.5.0",
            language_id=russian.id,
            description="Russian dictionary"
        ))
        
        # Create Spanish models
        es_acoustic = create_mfa_model(db_session, MFAModelCreate(
            name="spanish_acoustic",
            model_type=ModelType.ACOUSTIC,
            version="1.0.0",
            language_id=spanish.id,
            description="Spanish acoustic model"
        ))
        
        return {
            "languages": {"english": english, "russian": russian, "spanish": spanish},
            "english_models": [en_acoustic, en_dictionary, en_g2p],
            "russian_models": [ru_acoustic, ru_dictionary],
            "spanish_models": [es_acoustic]
        }
    
    def test_get_all_models_no_filter(self, client: TestClient, setup_multilang_models):
        """Test getting all models without language filter"""
        response = client.get("/models/")
        assert response.status_code == 200
        
        models = response.json()
        assert len(models) >= 6  # At least 6 models from setup
        
        # Check that we have models from different languages
        languages = {model["language"]["code"] for model in models}
        assert "english" in languages
        assert "russian" in languages
        assert "spanish" in languages
    
    def test_get_models_filter_by_english(self, client: TestClient, setup_multilang_models):
        """Test getting models filtered by English language"""
        response = client.get("/models/?language=english")
        assert response.status_code == 200
        
        models = response.json()
        assert len(models) == 3  # 3 English models
        
        # All models should be English
        for model in models:
            assert model["language"]["code"] == "english"
        
        # Check model types
        model_types = {model["model_type"] for model in models}
        assert "acoustic" in model_types
        assert "dictionary" in model_types
        assert "g2p" in model_types
    
    def test_get_models_filter_by_russian(self, client: TestClient, setup_multilang_models):
        """Test getting models filtered by Russian language"""
        response = client.get("/models/?language=russian")
        assert response.status_code == 200
        
        models = response.json()
        assert len(models) == 2  # 2 Russian models
        
        # All models should be Russian
        for model in models:
            assert model["language"]["code"] == "russian"
    
    def test_get_models_filter_by_nonexistent_language(self, client: TestClient, setup_multilang_models):
        """Test getting models filtered by non-existent language"""
        response = client.get("/models/?language=nonexistent")
        assert response.status_code == 200
        
        models = response.json()
        assert len(models) == 0
    
    def test_get_models_by_type_no_filter(self, client: TestClient, setup_multilang_models):
        """Test getting models by type without language filter"""
        response = client.get("/models/by-type/acoustic")
        assert response.status_code == 200
        
        models = response.json()
        assert len(models) == 3  # 3 acoustic models (English, Russian, Spanish)
        
        # All models should be acoustic
        for model in models:
            assert model["model_type"] == "acoustic"
        
        # Check that we have models from different languages
        languages = {model["language"]["code"] for model in models}
        assert "english" in languages
        assert "russian" in languages
        assert "spanish" in languages
    
    def test_get_acoustic_models_filter_by_english(self, client: TestClient, setup_multilang_models):
        """Test getting acoustic models filtered by English language"""
        response = client.get("/models/by-type/acoustic?language=english")
        assert response.status_code == 200
        
        models = response.json()
        assert len(models) == 1  # 1 English acoustic model
        
        model = models[0]
        assert model["model_type"] == "acoustic"
        assert model["language"]["code"] == "english"
        assert model["name"] == "english_acoustic"
    
    def test_get_dictionary_models_filter_by_russian(self, client: TestClient, setup_multilang_models):
        """Test getting dictionary models filtered by Russian language"""
        response = client.get("/models/by-type/dictionary?language=russian")
        assert response.status_code == 200
        
        models = response.json()
        assert len(models) == 1  # 1 Russian dictionary model
        
        model = models[0]
        assert model["model_type"] == "dictionary"
        assert model["language"]["code"] == "russian"
        assert model["name"] == "russian_dictionary"
    
    def test_get_g2p_models_filter_by_spanish(self, client: TestClient, setup_multilang_models):
        """Test getting G2P models filtered by Spanish language"""
        response = client.get("/models/by-type/g2p?language=spanish")
        assert response.status_code == 200
        
        models = response.json()
        assert len(models) == 0  # No Spanish G2P models
    
    def test_get_models_with_pagination_and_language_filter(self, client: TestClient, setup_multilang_models):
        """Test getting models with pagination and language filter"""
        response = client.get("/models/?language=english&limit=2")
        assert response.status_code == 200
        
        models = response.json()
        assert len(models) == 2  # Limited to 2 models
        
        # All models should be English
        for model in models:
            assert model["language"]["code"] == "english"
    
    def test_get_models_case_sensitivity(self, client: TestClient, setup_multilang_models):
        """Test language filter case sensitivity"""
        # Test with different case
        response = client.get("/models/?language=English")
        assert response.status_code == 200
        
        models = response.json()
        # Should return empty if case sensitive, or 3 if case insensitive
        # Assuming case sensitive for now
        assert len(models) == 0
    
    def test_invalid_model_type_with_language_filter(self, client: TestClient, setup_multilang_models):
        """Test invalid model type with language filter"""
        response = client.get("/models/by-type/invalid?language=english")
        assert response.status_code == 422  # Validation error for invalid enum value
