import pytest
from fastapi.testclient import TestClient
from app.domains.models.models import ModelType
from app.domains.models.crud import create_mfa_model, create_language
from app.domains.models.schemas import MFAModelCreate, LanguageCreate


class TestRussianMFAModels:
    """Tests for Russian MFA models with backward compatibility"""
    
    @pytest.fixture
    def setup_russian_mfa_models(self, db_session):
        """Create Russian MFA models with type suffixes (as they exist in real DB)"""
        # Create Russian language
        russian = create_language(db_session, LanguageCreate(code="russian", name="Russian"))
        
        # Create models with type suffixes (as they exist in real database)
        acoustic_model = create_mfa_model(db_session, MFAModelCreate(
            name="russian_mfa_acoustic",
            model_type=ModelType.ACOUSTIC,
            version="3.1.0",
            language_id=russian.id,
            description="Russian MFA acoustic model"
        ))
        
        dictionary_model = create_mfa_model(db_session, MFAModelCreate(
            name="russian_mfa_dictionary",
            model_type=ModelType.DICTIONARY,
            version="3.1.0",
            language_id=russian.id,
            description="Russian MFA dictionary model"
        ))
        
        g2p_model = create_mfa_model(db_session, MFAModelCreate(
            name="russian_mfa_g2p",
            model_type=ModelType.G2P,
            version="3.1.0",
            language_id=russian.id,
            description="Russian MFA G2P model"
        ))
        
        return {
            "language": russian,
            "acoustic": acoustic_model,
            "dictionary": dictionary_model,
            "g2p": g2p_model
        }
    
    def test_create_alignment_with_russian_mfa_success(self, client: TestClient, sample_audio_file, 
                                                      sample_text_file, setup_russian_mfa_models):
        """Test successful creation of alignment task with Russian MFA models using base names"""
        models = setup_russian_mfa_models
        
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("13.wav", audio, "audio/wav"),
                    "text_file": ("13.txt", text, "text/plain")
                },
                data={
                    # Using base name "russian_mfa" instead of "russian_mfa_acoustic"
                    "acoustic_model_name": "russian_mfa",
                    "acoustic_model_version": "3.1.0",
                    "dictionary_model_name": "russian_mfa",
                    "dictionary_model_version": "3.1.0",
                    # G2P model is optional, so we can skip it or provide empty values
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_audio_filename"] == "13.wav"
        assert data["original_text_filename"] == "13.txt"
        assert data["status"] == "pending"
        
        # Check that models were found and stored correctly
        assert data["acoustic_model"]["name"] == "russian_mfa"
        assert data["acoustic_model"]["version"] == "3.1.0"
        assert data["dictionary_model"]["name"] == "russian_mfa"
        assert data["dictionary_model"]["version"] == "3.1.0"
        assert data["g2p_model"] is None  # No G2P model provided
        
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_alignment_with_russian_mfa_and_g2p(self, client: TestClient, sample_audio_file, 
                                                      sample_text_file, setup_russian_mfa_models):
        """Test creation with Russian MFA models including G2P"""
        models = setup_russian_mfa_models
        
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("13.wav", audio, "audio/wav"),
                    "text_file": ("13.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": "russian_mfa",
                    "acoustic_model_version": "3.1.0",
                    "dictionary_model_name": "russian_mfa",
                    "dictionary_model_version": "3.1.0",
                    "g2p_model_name": "russian_mfa",
                    "g2p_model_version": "3.1.0",
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that all models were found
        assert data["acoustic_model"]["name"] == "russian_mfa"
        assert data["dictionary_model"]["name"] == "russian_mfa"
        assert data["g2p_model"]["name"] == "russian_mfa"
        assert data["g2p_model"]["version"] == "3.1.0"
    
    def test_create_alignment_with_exact_model_names(self, client: TestClient, sample_audio_file, 
                                                    sample_text_file, setup_russian_mfa_models):
        """Test that exact model names still work (backward compatibility)"""
        models = setup_russian_mfa_models
        
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("13.wav", audio, "audio/wav"),
                    "text_file": ("13.txt", text, "text/plain")
                },
                data={
                    # Using exact names from database
                    "acoustic_model_name": "russian_mfa_acoustic",
                    "acoustic_model_version": "3.1.0",
                    "dictionary_model_name": "russian_mfa_dictionary",
                    "dictionary_model_version": "3.1.0",
                    "g2p_model_name": "russian_mfa_g2p",
                    "g2p_model_version": "3.1.0",
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that models were found with exact names
        assert data["acoustic_model"]["name"] == "russian_mfa_acoustic"
        assert data["dictionary_model"]["name"] == "russian_mfa_dictionary"
        assert data["g2p_model"]["name"] == "russian_mfa_g2p"
    
    def test_create_alignment_with_empty_g2p_params(self, client: TestClient, sample_audio_file, 
                                                   sample_text_file, setup_russian_mfa_models):
        """Test creation with empty G2P parameters (as in user's request)"""
        models = setup_russian_mfa_models
        
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("13.wav", audio, "audio/wav"),
                    "text_file": ("13.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": "russian_mfa",
                    "acoustic_model_version": "3.1.0",
                    "dictionary_model_name": "russian_mfa",
                    "dictionary_model_version": "3.1.0",
                    "g2p_model_name": "",  # Empty string
                    "g2p_model_version": "",  # Empty string
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # G2P model should be None when empty strings are provided
        assert data["g2p_model"] is None
    
    def test_create_alignment_nonexistent_version(self, client: TestClient, sample_audio_file, 
                                                 sample_text_file, setup_russian_mfa_models):
        """Test creation with non-existent version"""
        models = setup_russian_mfa_models
        
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("13.wav", audio, "audio/wav"),
                    "text_file": ("13.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": "russian_mfa",
                    "acoustic_model_version": "999.0.0",  # Non-existent version
                    "dictionary_model_name": "russian_mfa",
                    "dictionary_model_version": "3.1.0",
                }
            )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_validate_model_lookup_priority(self, db_session, setup_russian_mfa_models):
        """Test that exact name match has priority over suffix match"""
        from app.domains.alignment.crud import validate_model_exists
        from app.domains.alignment.schemas import ModelParameter
        
        models = setup_russian_mfa_models
        
        # Create a model with exact name "russian_mfa" (without suffix)
        exact_model = create_mfa_model(db_session, MFAModelCreate(
            name="russian_mfa",  # Exact name without suffix
            model_type=ModelType.ACOUSTIC,
            version="3.1.0",
            language_id=models["language"].id,
            description="Exact name model"
        ))
        
        # Test that exact match is found first
        model_param = ModelParameter(name="russian_mfa", version="3.1.0")
        found_model = validate_model_exists(db_session, model_param, ModelType.ACOUSTIC)
        
        # Should find the exact match, not the suffixed one
        assert found_model is not None
        assert found_model.name == "russian_mfa"
        assert found_model.id == exact_model.id  # Should be the exact match, not the suffixed one
