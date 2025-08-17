import pytest
from fastapi.testclient import TestClient
from api.domains.models.models import ModelType
from api.domains.models.crud import create_mfa_model, create_language
from api.domains.models.schemas import MFAModelCreate, LanguageCreate


class TestUserRequestSuccess:
    """Test that reproduces the exact user request that should now succeed"""
    
    @pytest.fixture
    def setup_real_russian_models(self, db_session):
        """Create Russian MFA models exactly as they exist in the real database"""
        # Create Russian language if it doesn't exist
        from api.domains.models.models import Language
        russian = db_session.query(Language).filter_by(code="russian").first()
        if not russian:
            russian = create_language(db_session, LanguageCreate(code="russian", name="Russian"))
        
        # Create models with exact names from real database (check if exists first)
        from api.domains.models.models import MFAModel
        
        acoustic_model = db_session.query(MFAModel).filter_by(
            name="russian_mfa_acoustic", version="3.1.0"
        ).first()
        if not acoustic_model:
            acoustic_model = create_mfa_model(db_session, MFAModelCreate(
                name="russian_mfa_acoustic",
                model_type=ModelType.ACOUSTIC,
                version="3.1.0",
                language_id=russian.id,
                variant="mfa",
                description="Russian acoustic model v3.1.0 (mfa)"
            ))
        
        dictionary_model = db_session.query(MFAModel).filter_by(
            name="russian_mfa_dictionary", version="3.1.0"
        ).first()
        if not dictionary_model:
            dictionary_model = create_mfa_model(db_session, MFAModelCreate(
                name="russian_mfa_dictionary",
                model_type=ModelType.DICTIONARY,
                version="3.1.0",
                language_id=russian.id,
                variant="mfa",
                description="Russian dictionary model v3.1.0 (mfa)"
            ))
        
        g2p_model = db_session.query(MFAModel).filter_by(
            name="russian_mfa_g2p", version="3.1.0"
        ).first()
        if not g2p_model:
            g2p_model = create_mfa_model(db_session, MFAModelCreate(
                name="russian_mfa_g2p",
                model_type=ModelType.G2P,
                version="3.1.0",
                language_id=russian.id,
                variant="mfa",
                description="Russian g2p model v3.1.0 (mfa)"
            ))
        
        # Commit changes to ensure models are saved
        db_session.commit()
        
        return {
            "language": russian,
            "acoustic": acoustic_model,
            "dictionary": dictionary_model,
            "g2p": g2p_model
        }
    
    def test_exact_user_request_success(self, client: TestClient, sample_audio_file, 
                                       sample_text_file, setup_real_russian_models, auth_headers):
        """Test the exact request that user made - should now succeed"""
        models = setup_real_russian_models
        
        # Create files with exact names from user request
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("13.wav", audio, "audio/wav"),
                    "text_file": ("13.txt", text, "text/plain")
                },
                data={
                    # Exact parameters from user's curl request
                    "acoustic_model_name": "russian_mfa",
                    "acoustic_model_version": "3.1.0",
                    "dictionary_model_name": "russian_mfa",
                    "dictionary_model_version": "3.1.0",
                    "g2p_model_name": "",  # Empty string as in user's request
                    "g2p_model_version": "",  # Empty string as in user's request
                },
                headers=auth_headers
            )
        
        # Should succeed now (before the fix it would fail with "not found")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify response structure
        assert data["original_audio_filename"] == "13.wav"
        assert data["original_text_filename"] == "13.txt"
        assert data["status"] == "pending"
        
        # Verify models were found and mapped correctly
        assert data["acoustic_model"]["name"] == "russian_mfa"
        assert data["acoustic_model"]["version"] == "3.1.0"
        assert data["dictionary_model"]["name"] == "russian_mfa"
        assert data["dictionary_model"]["version"] == "3.1.0"
        
        # G2P model should be None because empty strings were provided
        assert data["g2p_model"] is None
        
        # Verify other fields
        assert "id" in data
        assert "audio_file_path" in data
        assert "text_file_path" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["result_path"] is None
        assert data["error_message"] is None
    
    def test_user_request_with_g2p_success(self, client: TestClient, sample_audio_file, 
                                          sample_text_file, setup_real_russian_models, auth_headers):
        """Test user request with G2P model included"""
        models = setup_real_russian_models
        
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
                    "g2p_model_name": "russian_mfa",  # Now with G2P
                    "g2p_model_version": "3.1.0",
                },
                headers=auth_headers
            )
        
        assert response.status_code == 200
        
        data = response.json()
        
        # All three models should be present
        assert data["acoustic_model"]["name"] == "russian_mfa"
        assert data["dictionary_model"]["name"] == "russian_mfa"
        assert data["g2p_model"]["name"] == "russian_mfa"
        assert data["g2p_model"]["version"] == "3.1.0"
    
    def test_backward_compatibility_exact_names(self, client: TestClient, sample_audio_file, 
                                               sample_text_file, setup_real_russian_models, auth_headers):
        """Test that exact database names still work (backward compatibility)"""
        models = setup_real_russian_models
        
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
                },
                headers=auth_headers
            )
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Should return exact names when exact names are used
        assert data["acoustic_model"]["name"] == "russian_mfa_acoustic"
        assert data["dictionary_model"]["name"] == "russian_mfa_dictionary"
        assert data["g2p_model"]["name"] == "russian_mfa_g2p"
