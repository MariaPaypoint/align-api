import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from sqlalchemy.orm import Session

from app.main import app
from app.models import Language, MFAModel, ModelType
from app.schemas import LanguageCreate, MFAModelCreate
from app.crud import create_language, create_mfa_model


class TestModelsEndpoints:
    """Test cases for models API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_data(self, db_session: Session):
        """Create sample data for testing"""
        # Create languages
        english = create_language(db_session, LanguageCreate(code="en", name="English"))
        russian = create_language(db_session, LanguageCreate(code="ru", name="Russian"))
        
        # Create models
        models = [
            MFAModelCreate(
                name="english_us_arpa",
                model_type=ModelType.G2P,
                version="2.2.1",
                variant="us_arpa",
                language_id=english.id,
                download_url="https://example.com/en_us.zip",
                description="English US G2P model"
            ),
            MFAModelCreate(
                name="english_india_mfa",
                model_type=ModelType.G2P,
                version="3.0.0",
                variant="india_mfa",
                language_id=english.id,
                download_url="https://example.com/en_in.zip",
                description="English India G2P model"
            ),
            MFAModelCreate(
                name="russian_mfa",
                model_type=ModelType.DICTIONARY,
                version="3.1.0",
                language_id=russian.id,
                download_url="https://example.com/ru_dict.zip",
                description="Russian dictionary model"
            ),
            MFAModelCreate(
                name="english_acoustic",
                model_type=ModelType.ACOUSTIC,
                version="2.0.0",
                language_id=english.id,
                description="English acoustic model"
            )
        ]
        
        created_models = []
        for model_data in models:
            created_models.append(create_mfa_model(db_session, model_data))
        
        return {
            "languages": [english, russian],
            "models": created_models
        }
    
    def test_get_all_models(self, client: TestClient, sample_data):
        """Test GET /models/ endpoint"""
        response = client.get("/models/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 4  # At least our sample models
        
        # Check structure of first model
        if data:
            model = data[0]
            required_fields = ["id", "name", "model_type", "version", "language_id", "language", "created_at", "updated_at"]
            for field in required_fields:
                assert field in model
            
            # Check language relationship
            assert "id" in model["language"]
            assert "code" in model["language"]
            assert "name" in model["language"]
    
    def test_get_models_with_pagination(self, client: TestClient, sample_data):
        """Test GET /models/ with pagination parameters"""
        response = client.get("/models/?skip=1&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 2
    
    def test_get_models_by_type_g2p(self, client: TestClient, sample_data):
        """Test GET /models/by-type/g2p endpoint"""
        response = client.get("/models/by-type/g2p")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should have at least 2 G2P models from sample data
        g2p_models = [m for m in data if m["model_type"] == "g2p"]
        assert len(g2p_models) >= 2
        
        # All returned models should be G2P type
        for model in data:
            assert model["model_type"] == "g2p"
    
    def test_get_models_by_type_dictionary(self, client: TestClient, sample_data):
        """Test GET /models/by-type/dictionary endpoint"""
        response = client.get("/models/by-type/dictionary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should have at least 1 dictionary model from sample data
        dict_models = [m for m in data if m["model_type"] == "dictionary"]
        assert len(dict_models) >= 1
        
        # All returned models should be dictionary type
        for model in data:
            assert model["model_type"] == "dictionary"
    
    def test_get_models_by_type_acoustic(self, client: TestClient, sample_data):
        """Test GET /models/by-type/acoustic endpoint"""
        response = client.get("/models/by-type/acoustic")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should have at least 1 acoustic model from sample data
        acoustic_models = [m for m in data if m["model_type"] == "acoustic"]
        assert len(acoustic_models) >= 1
    
    def test_get_models_by_invalid_type(self, client: TestClient):
        """Test GET /models/by-type/ with invalid type"""
        response = client.get("/models/by-type/invalid")
        
        # Should return 422 for invalid enum value
        assert response.status_code == 422
    
    def test_get_supported_languages(self, client: TestClient, sample_data):
        """Test GET /models/languages endpoint"""
        response = client.get("/models/languages")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 2  # At least English and Russian from sample data
        
        # Check structure
        if data:
            language = data[0]
            required_fields = ["id", "code", "name", "created_at", "updated_at"]
            for field in required_fields:
                assert field in language
        
        # Check that our sample languages are present
        language_codes = [lang["code"] for lang in data]
        assert "en" in language_codes
        assert "ru" in language_codes
    
    def test_get_languages_with_pagination(self, client: TestClient, sample_data):
        """Test GET /models/languages with pagination"""
        response = client.get("/models/languages?skip=0&limit=1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 1
    
    @patch('app.services.mfa_service.MFAModelService.update_models_from_github')
    def test_update_models_success(self, mock_update, client: TestClient):
        """Test POST /models/update endpoint success"""
        # Mock successful update
        mock_update.return_value = (25, 5)  # 25 models, 5 languages
        
        response = client.post("/models/update")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Models updated successfully"
        assert data["updated_models"] == 25
        assert data["updated_languages"] == 5
        
        mock_update.assert_called_once()
    
    @patch('app.services.mfa_service.MFAModelService.update_models_from_github')
    def test_update_models_failure(self, mock_update, client: TestClient):
        """Test POST /models/update endpoint failure"""
        # Mock update failure
        mock_update.side_effect = Exception("GitHub API error")
        
        response = client.post("/models/update")
        
        assert response.status_code == 500
        data = response.json()
        
        assert "Failed to update models" in data["detail"]
        assert "GitHub API error" in data["detail"]
    
    @patch('app.services.mfa_service.MFAModelService.update_models_from_github')
    def test_update_models_no_updates(self, mock_update, client: TestClient):
        """Test POST /models/update when no updates are needed"""
        # Mock no updates needed
        mock_update.return_value = (0, 0)
        
        response = client.post("/models/update")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Models updated successfully"
        assert data["updated_models"] == 0
        assert data["updated_languages"] == 0
    
    def test_models_endpoint_structure(self, client: TestClient, sample_data):
        """Test that model responses have correct structure including variant field"""
        response = client.get("/models/")
        
        assert response.status_code == 200
        data = response.json()
        
        if data:
            model = data[0]
            
            # Check all expected fields are present
            expected_fields = [
                "id", "name", "model_type", "version", "variant", 
                "language_id", "description", 
                "created_at", "updated_at", "language"
            ]
            
            for field in expected_fields:
                assert field in model
            
            # Check types
            assert isinstance(model["id"], int)
            assert isinstance(model["name"], str)
            assert model["model_type"] in ["acoustic", "g2p", "dictionary"]
            assert isinstance(model["version"], str)
            # variant can be None or string
            assert model["variant"] is None or isinstance(model["variant"], str)
            assert isinstance(model["language_id"], int)
            # description can be None or string
            assert model["description"] is None or isinstance(model["description"], str)
            
            # Check language relationship structure
            language = model["language"]
            assert isinstance(language["id"], int)
            assert isinstance(language["code"], str)
            assert isinstance(language["name"], str)
