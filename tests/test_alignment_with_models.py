import pytest
import os
from fastapi.testclient import TestClient
from api.domains.alignment.models import AlignmentStatus
from api.domains.models.models import ModelType
from api.domains.models.crud import create_mfa_model, create_language
from api.domains.models.schemas import MFAModelCreate, LanguageCreate


class TestAlignmentWithModels:
    """Tests for alignment endpoints with model parameters"""
    
    @pytest.fixture
    def setup_test_models(self, db_session):
        """Create test models for alignment tests"""
        # Create test language
        language = create_language(db_session, LanguageCreate(code="test", name="Test Language"))
        
        # Create test models
        acoustic_model = create_mfa_model(db_session, MFAModelCreate(
            name="test_acoustic",
            model_type=ModelType.ACOUSTIC,
            version="1.0.0",
            language_id=language.id,
            description="Test acoustic model"
        ))
        
        dictionary_model = create_mfa_model(db_session, MFAModelCreate(
            name="test_dictionary",
            model_type=ModelType.DICTIONARY,
            version="1.0.0",
            language_id=language.id,
            description="Test dictionary model"
        ))
        
        g2p_model = create_mfa_model(db_session, MFAModelCreate(
            name="test_g2p",
            model_type=ModelType.G2P,
            version="1.0.0",
            language_id=language.id,
            description="Test G2P model"
        ))
        
        return {
            "language": language,
            "acoustic": acoustic_model,
            "dictionary": dictionary_model,
            "g2p": g2p_model
        }
    
    def test_create_alignment_with_models_success(self, client: TestClient, sample_audio_file, 
                                                sample_text_file, setup_test_models, auth_headers):
        """Test successful creation of alignment task with model parameters"""
        models = setup_test_models
        
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": models["acoustic"].name,
                    "acoustic_model_version": models["acoustic"].version,
                    "dictionary_model_name": models["dictionary"].name,
                    "dictionary_model_version": models["dictionary"].version,
                    "g2p_model_name": models["g2p"].name,
                    "g2p_model_version": models["g2p"].version,
                },
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_audio_filename"] == "test.mp3"
        assert data["original_text_filename"] == "test.txt"
        assert data["status"] == AlignmentStatus.PENDING.value
        
        # Check model parameters
        assert data["acoustic_model"]["name"] == models["acoustic"].name
        assert data["acoustic_model"]["version"] == models["acoustic"].version
        assert data["dictionary_model"]["name"] == models["dictionary"].name
        assert data["dictionary_model"]["version"] == models["dictionary"].version
        assert data["g2p_model"]["name"] == models["g2p"].name
        assert data["g2p_model"]["version"] == models["g2p"].version
        
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_alignment_without_g2p_model(self, client: TestClient, sample_audio_file, 
                                              sample_text_file, setup_test_models, auth_headers):
        """Test creation without optional G2P model"""
        models = setup_test_models
        
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": models["acoustic"].name,
                    "acoustic_model_version": models["acoustic"].version,
                    "dictionary_model_name": models["dictionary"].name,
                    "dictionary_model_version": models["dictionary"].version,
                },
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["g2p_model"] is None
    
    def test_create_alignment_nonexistent_acoustic_model(self, client: TestClient, sample_audio_file, 
                                                       sample_text_file, setup_test_models, auth_headers):
        """Test creation with non-existent acoustic model"""
        models = setup_test_models
        
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": "nonexistent_model",
                    "acoustic_model_version": "1.0.0",
                    "dictionary_model_name": models["dictionary"].name,
                    "dictionary_model_version": models["dictionary"].version,
                },
                headers=auth_headers
            )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_alignment_nonexistent_dictionary_model(self, client: TestClient, sample_audio_file, 
                                                         sample_text_file, setup_test_models, auth_headers):
        """Test creation with non-existent dictionary model"""
        models = setup_test_models
        
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": models["acoustic"].name,
                    "acoustic_model_version": models["acoustic"].version,
                    "dictionary_model_name": "nonexistent_dictionary",
                    "dictionary_model_version": "1.0.0",
                },
                headers=auth_headers
            )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_alignment_models_different_languages(self, client: TestClient, sample_audio_file, 
                                                       sample_text_file, db_session, auth_headers):
        """Test creation with models from different languages"""
        # Create two different languages
        lang1 = create_language(db_session, LanguageCreate(code="en", name="English"))
        lang2 = create_language(db_session, LanguageCreate(code="ru", name="Russian"))
        
        # Create models for different languages
        acoustic_en = create_mfa_model(db_session, MFAModelCreate(
            name="english_acoustic",
            model_type=ModelType.ACOUSTIC,
            version="1.0.0",
            language_id=lang1.id
        ))
        
        dictionary_model_different_lang = create_mfa_model(db_session, MFAModelCreate(
            name="russian_dictionary",
            model_type=ModelType.DICTIONARY,
            version="1.0.0",
            language_id=lang2.id
        ))
        
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": acoustic_en.name,
                    "acoustic_model_version": acoustic_en.version,
                    "dictionary_model_name": dictionary_model_different_lang.name,
                    "dictionary_model_version": dictionary_model_different_lang.version,
                },
                headers=auth_headers
            )
        
        assert response.status_code == 400
        assert "same language" in response.json()["detail"].lower()
    
    def test_create_alignment_missing_required_parameters(self, client: TestClient, sample_audio_file, 
                                                        sample_text_file, auth_headers):
        """Test creation with missing required model parameters"""
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": "test_acoustic",
                    # Missing acoustic_model_version
                    "dictionary_model_name": "test_dictionary",
                    "dictionary_model_version": "1.0.0",
                },
                headers=auth_headers
            )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_alignment_task_with_models(self, client: TestClient, sample_audio_file, 
                                          sample_text_file, setup_test_models, auth_headers):
        """Test getting alignment task with model information"""
        models = setup_test_models
        
        # Create alignment task first
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            create_response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": models["acoustic"].name,
                    "acoustic_model_version": models["acoustic"].version,
                    "dictionary_model_name": models["dictionary"].name,
                    "dictionary_model_version": models["dictionary"].version,
                },
                headers=auth_headers
            )
        
        task_id = create_response.json()["id"]
        
        # Get the task
        response = client.get(f"/alignment/{task_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["acoustic_model"]["name"] == models["acoustic"].name
        assert data["dictionary_model"]["name"] == models["dictionary"].name
    
    def test_get_all_alignment_tasks_with_models(self, client: TestClient, sample_audio_file, 
                                               sample_text_file, setup_test_models, auth_headers):
        """Test getting all alignment tasks with model information"""
        models = setup_test_models
        
        # Create alignment task first
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": models["acoustic"].name,
                    "acoustic_model_version": models["acoustic"].version,
                    "dictionary_model_name": models["dictionary"].name,
                    "dictionary_model_version": models["dictionary"].version,
                },
                headers=auth_headers
            )
        
        # Get all tasks
        response = client.get("/alignment/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0
        task = data[0]
        assert "acoustic_model" in task
        assert "dictionary_model" in task
