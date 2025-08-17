import pytest
import os
from fastapi.testclient import TestClient
from app.domains.alignment.models import AlignmentStatus
from app.domains.models.models import ModelType
from app.domains.models.crud import create_mfa_model, create_language
from app.domains.models.schemas import MFAModelCreate, LanguageCreate

class TestAlignmentEndpoints:
    
    @pytest.fixture
    def setup_test_models(self, db_session):
        """Create test models for alignment tests"""
        # Create test language
        test_language = create_language(db_session, LanguageCreate(code="test", name="Test Language"))
        
        # Create test models
        acoustic_model = create_mfa_model(db_session, MFAModelCreate(
            name="test_acoustic",
            model_type=ModelType.ACOUSTIC,
            version="1.0.0",
            language_id=test_language.id,
            variant="test",
            description="Test acoustic model"
        ))
        
        dictionary_model = create_mfa_model(db_session, MFAModelCreate(
            name="test_dictionary",
            model_type=ModelType.DICTIONARY,
            version="1.0.0",
            language_id=test_language.id,
            variant="test",
            description="Test dictionary model"
        ))
        
        g2p_model = create_mfa_model(db_session, MFAModelCreate(
            name="test_g2p",
            model_type=ModelType.G2P,
            version="1.0.0",
            language_id=test_language.id,
            variant="test",
            description="Test G2P model"
        ))
        
        return {
            "language": test_language,
            "acoustic": acoustic_model,
            "dictionary": dictionary_model,
            "g2p": g2p_model
        }
    
    def test_create_alignment_task_success(self, client: TestClient, sample_audio_file, sample_text_file, setup_test_models):
        """Test successful creation of alignment task"""
        models = setup_test_models
        
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": "test_acoustic",
                    "acoustic_model_version": "1.0.0",
                    "dictionary_model_name": "test_dictionary",
                    "dictionary_model_version": "1.0.0",
                    "g2p_model_name": "",
                    "g2p_model_version": ""
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_audio_filename"] == "test.mp3"
        assert data["original_text_filename"] == "test.txt"
        assert data["status"] == AlignmentStatus.PENDING.value
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_alignment_task_with_wav(self, client: TestClient, sample_wav_file, sample_text_file, setup_test_models):
        """Test creation with WAV file"""
        models = setup_test_models
        
        with open(sample_wav_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.wav", audio, "audio/wav"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": "test_acoustic",
                    "acoustic_model_version": "1.0.0",
                    "dictionary_model_name": "test_dictionary",
                    "dictionary_model_version": "1.0.0",
                    "g2p_model_name": "test_g2p",
                    "g2p_model_version": "1.0.0"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_audio_filename"] == "test.wav"
    
    def test_create_alignment_task_invalid_audio_format(self, client: TestClient, sample_text_file, setup_test_models):
        """Test creation with invalid audio format"""
        models = setup_test_models
        
        with open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.pdf", text, "application/pdf"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": "test_acoustic",
                    "acoustic_model_version": "1.0.0",
                    "dictionary_model_name": "test_dictionary",
                    "dictionary_model_version": "1.0.0",
                    "g2p_model_name": "",
                    "g2p_model_version": ""
                }
            )
        
        assert response.status_code == 400  # API returns 400 for invalid file format
        # Check that it's a validation error related to file format
    
    def test_create_alignment_task_invalid_text_format(self, client: TestClient, sample_audio_file, setup_test_models):
        """Test creation with invalid text format"""
        models = setup_test_models
        
        with open(sample_audio_file, "rb") as audio:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.pdf", audio, "application/pdf")
                },
                data={
                    "acoustic_model_name": "test_acoustic",
                    "acoustic_model_version": "1.0.0",
                    "dictionary_model_name": "test_dictionary",
                    "dictionary_model_version": "1.0.0",
                    "g2p_model_name": "",
                    "g2p_model_version": ""
                }
            )
        
        assert response.status_code == 400  # API returns 400 for invalid file format
        # Check that it's a validation error related to file format
    
    def test_get_alignment_tasks(self, client: TestClient, sample_audio_file, sample_text_file, setup_test_models):
        """Test getting all alignment tasks"""
        models = setup_test_models
        
        # First create a task
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            create_response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": "test_acoustic",
                    "acoustic_model_version": "1.0.0",
                    "dictionary_model_name": "test_dictionary",
                    "dictionary_model_version": "1.0.0",
                    "g2p_model_name": "",
                    "g2p_model_version": ""
                }
            )
        
        # Then get all tasks
        response = client.get("/alignment/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_alignment_task_by_id(self, client: TestClient, sample_audio_file, sample_text_file, setup_test_models):
        """Test getting specific alignment task"""
        models = setup_test_models
        
        # First create a task
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            create_response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": "test_acoustic",
                    "acoustic_model_version": "1.0.0",
                    "dictionary_model_name": "test_dictionary",
                    "dictionary_model_version": "1.0.0",
                    "g2p_model_name": "",
                    "g2p_model_version": ""
                }
            )
        
        task_id = create_response.json()["id"]
        
        # Get the task by ID
        response = client.get(f"/alignment/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["original_audio_filename"] == "test.mp3"
    
    def test_get_nonexistent_alignment_task(self, client: TestClient, setup_test_models):
        """Test getting non-existent alignment task"""
        models = setup_test_models  # Ensure tables are created
        response = client.get("/alignment/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_update_alignment_task(self, client: TestClient, sample_audio_file, sample_text_file, setup_test_models):
        """Test updating alignment task"""
        models = setup_test_models
        
        # First create a task
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            create_response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": "test_acoustic",
                    "acoustic_model_version": "1.0.0",
                    "dictionary_model_name": "test_dictionary",
                    "dictionary_model_version": "1.0.0",
                    "g2p_model_name": "",
                    "g2p_model_version": ""
                }
            )
        
        task_id = create_response.json()["id"]
        
        # Update the task
        update_data = {
            "status": AlignmentStatus.PROCESSING.value,
            "result_path": "/path/to/result.json"
        }
        response = client.put(f"/alignment/{task_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == AlignmentStatus.PROCESSING.value
        assert data["result_path"] == "/path/to/result.json"
    
    def test_update_nonexistent_alignment_task(self, client: TestClient, setup_test_models):
        """Test updating non-existent alignment task"""
        models = setup_test_models  # Ensure tables are created
        update_data = {"status": AlignmentStatus.COMPLETED.value}
        response = client.put("/alignment/999", json=update_data)
        assert response.status_code == 404
    
    def test_delete_alignment_task(self, client: TestClient, sample_audio_file, sample_text_file, setup_test_models):
        """Test deleting alignment task"""
        models = setup_test_models
        
        # First create a task
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            create_response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": "test_acoustic",
                    "acoustic_model_version": "1.0.0",
                    "dictionary_model_name": "test_dictionary",
                    "dictionary_model_version": "1.0.0",
                    "g2p_model_name": "",
                    "g2p_model_version": ""
                }
            )
        
        task_id = create_response.json()["id"]
        
        # Delete the task
        response = client.delete(f"/alignment/{task_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify task is deleted
        get_response = client.get(f"/alignment/{task_id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_alignment_task(self, client: TestClient, setup_test_models):
        """Test deleting non-existent alignment task"""
        models = setup_test_models  # Ensure tables are created
        response = client.delete("/alignment/999")
        assert response.status_code == 404
    
    def test_get_tasks_by_status(self, client: TestClient, sample_audio_file, sample_text_file, setup_test_models):
        """Test getting tasks by status"""
        models = setup_test_models
        
        # First create a task
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            create_response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": "test_acoustic",
                    "acoustic_model_version": "1.0.0",
                    "dictionary_model_name": "test_dictionary",
                    "dictionary_model_version": "1.0.0",
                    "g2p_model_name": "",
                    "g2p_model_version": ""
                }
            )
        
        # Get tasks by status using query parameter
        response = client.get(f"/alignment/?status={AlignmentStatus.PENDING.value}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(task["status"] == AlignmentStatus.PENDING.value for task in data)
    
    def test_pagination(self, client: TestClient, sample_audio_file, sample_text_file, setup_test_models):
        """Test pagination of alignment tasks"""
        models = setup_test_models
        
        # Create multiple tasks
        for i in range(3):
            with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
                client.post(
                    "/alignment/",
                    files={
                        "audio_file": (f"test{i}.mp3", audio, "audio/mpeg"),
                        "text_file": (f"test{i}.txt", text, "text/plain")
                    },
                    data={
                        "acoustic_model_name": "test_acoustic",
                        "acoustic_model_version": "1.0.0",
                        "dictionary_model_name": "test_dictionary",
                        "dictionary_model_version": "1.0.0",
                        "g2p_model_name": "",
                        "g2p_model_version": ""
                    }
                )
        
        # Test pagination
        response = client.get("/alignment/?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2
