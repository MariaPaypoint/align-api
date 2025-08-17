import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from api.domains.alignment.models import AlignmentStatus
from api.domains.models.models import ModelType
from api.domains.models.crud import create_mfa_model, create_language
from api.domains.models.schemas import MFAModelCreate, LanguageCreate
from api.domains.users.models import User, SubscriptionType
from api.domains.users.crud import UserService
from api.domains.users.schemas import UserCreate
from api.domains.auth.security import create_access_token
class TestAlignmentEndpoints:
    
    @pytest.fixture
    def setup_database(self, db_session):
        """Setup test database with models and user like working test"""
        # Create subscription type
        sub_type = SubscriptionType(
            name="free",
            display_name="Free Plan",
            total_storage_limit=100*1024*1024,
            max_concurrent_tasks=1,
            price_monthly=0.00,
            is_active=True
        )
        db_session.add(sub_type)
        db_session.commit()
        
        # Create test user
        test_user = UserService.create_user(db_session, UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        ))
        
        # Create test language and models
        test_language = create_language(db_session, LanguageCreate(code="test", name="Test Language"))
        
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
        
        db_session.commit()
        
        # Create auth token
        token = create_access_token(data={"sub": test_user.username})
        
        return {
            "user": test_user,
            "language": test_language,
            "acoustic": acoustic_model,
            "dictionary": dictionary_model,
            "g2p": g2p_model,
            "token": token,
            "auth_headers": {"Authorization": f"Bearer {token}"}
        }
    
    def test_create_alignment_task_success(self, setup_database, client):
        """Test successful creation of alignment task"""
        test_data = setup_database
        auth_headers = test_data["auth_headers"]
        
        # Create test files
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as audio_file:
            audio_file.write(b"fake audio content")
            audio_path = audio_file.name
            
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as text_file:
            text_file.write(b"fake text content") 
            text_path = text_file.name
        
        try:
            with open(audio_path, "rb") as audio, open(text_path, "rb") as text:
                response = client.post(
                    "/alignment/",
                    files={
                        "audio_file": ("test.mp3", audio, "audio/mpeg"),
                        "text_file": ("test.txt", text, "text/plain")
                    },
                    data={
                        "acoustic_model_name": test_data["acoustic"].name,
                        "acoustic_model_version": test_data["acoustic"].version,
                        "dictionary_model_name": test_data["dictionary"].name,
                        "dictionary_model_version": test_data["dictionary"].version,
                        "g2p_model_name": test_data["g2p"].name,
                        "g2p_model_version": test_data["g2p"].version
                    },
                    headers=auth_headers
                )
        finally:
            os.unlink(audio_path)
            os.unlink(text_path)
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_audio_filename"] == "test.mp3"
        assert data["original_text_filename"] == "test.txt"
        assert data["status"] == AlignmentStatus.PENDING.value
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_alignment_task_with_wav(self, client, sample_wav_file, sample_text_file, setup_database):
        """Test creation with WAV file"""
        test_data = setup_database
        models = test_data
        auth_headers = test_data["auth_headers"]
        
        with open(sample_wav_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.wav", audio, "audio/wav"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": models["acoustic"].name,
                    "acoustic_model_version": models["acoustic"].version,
                    "dictionary_model_name": models["dictionary"].name,
                    "dictionary_model_version": models["dictionary"].version,
                    "g2p_model_name": models["g2p"].name,
                    "g2p_model_version": models["g2p"].version
                },
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_audio_filename"] == "test.wav"
    
    def test_create_alignment_task_invalid_audio_format(self, client, sample_text_file, setup_database):
        """Test creation with invalid audio format"""
        test_data = setup_database
        models = test_data
        auth_headers = test_data["auth_headers"]
        
        with open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.pdf", text, "application/pdf"),
                    "text_file": ("test.txt", text, "text/plain")
                },
                data={
                    "acoustic_model_name": models["acoustic"].name,
                    "acoustic_model_version": models["acoustic"].version,
                    "dictionary_model_name": models["dictionary"].name,
                    "dictionary_model_version": models["dictionary"].version,
                    "g2p_model_name": models["g2p"].name,
                    "g2p_model_version": models["g2p"].version
                },
                headers=auth_headers
            )
        
        assert response.status_code == 400  # API returns 400 for invalid file format
        # Check that it's a validation error related to file format
    
    def test_create_alignment_task_invalid_text_format(self, client, sample_audio_file, setup_database):
        """Test creation with invalid text format"""
        test_data = setup_database
        models = test_data
        auth_headers = test_data["auth_headers"]
        
        with open(sample_audio_file, "rb") as audio:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.pdf", audio, "application/pdf")
                },
                data={
                    "acoustic_model_name": models["acoustic"].name,
                    "acoustic_model_version": models["acoustic"].version,
                    "dictionary_model_name": models["dictionary"].name,
                    "dictionary_model_version": models["dictionary"].version,
                    "g2p_model_name": models["g2p"].name,
                    "g2p_model_version": models["g2p"].version
                },
                headers=auth_headers
            )
        
        assert response.status_code == 400  # API returns 400 for invalid file format
        # Check that it's a validation error related to file format
    
    def test_get_alignment_tasks(self, client, sample_audio_file, sample_text_file, setup_database):
        """Test getting all alignment tasks"""
        test_data = setup_database
        models = test_data
        auth_headers = test_data["auth_headers"]
        
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
                },
                headers=auth_headers
            )
        
        # Then get all tasks
        response = client.get("/alignment/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_alignment_task_by_id(self, client, sample_audio_file, sample_text_file, setup_database):
        """Test getting specific alignment task"""
        test_data = setup_database
        models = test_data
        auth_headers = test_data["auth_headers"]
        
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
                },
                headers=auth_headers
            )
        
        task_id = create_response.json()["id"]
        
        # Get the task by ID
        response = client.get(f"/alignment/{task_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["original_audio_filename"] == "test.mp3"
    
    def test_get_nonexistent_alignment_task(self, client, setup_database):
        """Test getting non-existent alignment task"""
        test_data = setup_database
        models = test_data
        auth_headers = test_data["auth_headers"]  # Ensure tables are created
        response = client.get("/alignment/999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_update_alignment_task(self, client, sample_audio_file, sample_text_file, setup_database):
        """Test updating alignment task"""
        test_data = setup_database
        models = test_data
        auth_headers = test_data["auth_headers"]
        
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
                },
                headers=auth_headers
            )
        
        task_id = create_response.json()["id"]
        
        # Update the task
        update_data = {
            "status": AlignmentStatus.PROCESSING.value,
            "result_path": "/path/to/result.json"
        }
        response = client.put(f"/alignment/{task_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == AlignmentStatus.PROCESSING.value
        assert data["result_path"] == "/path/to/result.json"
    
    def test_update_nonexistent_alignment_task(self, client, setup_database):
        """Test updating non-existent alignment task"""
        test_data = setup_database
        models = test_data
        auth_headers = test_data["auth_headers"]  # Ensure tables are created
        update_data = {"status": AlignmentStatus.COMPLETED.value}
        response = client.put("/alignment/999", json=update_data, headers=auth_headers)
        assert response.status_code == 404
    
    def test_delete_alignment_task(self, client, sample_audio_file, sample_text_file, setup_database):
        """Test deleting alignment task"""
        test_data = setup_database
        models = test_data
        auth_headers = test_data["auth_headers"]
        
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
                },
                headers=auth_headers
            )
        
        task_id = create_response.json()["id"]
        
        # Delete the task
        response = client.delete(f"/alignment/{task_id}", headers=auth_headers)
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify task is deleted
        get_response = client.get(f"/alignment/{task_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_alignment_task(self, client, setup_database):
        """Test deleting non-existent alignment task"""
        test_data = setup_database
        models = test_data
        auth_headers = test_data["auth_headers"]  # Ensure tables are created
        response = client.delete("/alignment/999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_tasks_by_status(self, client, sample_audio_file, sample_text_file, setup_database):
        """Test getting tasks by status"""
        test_data = setup_database
        models = test_data
        auth_headers = test_data["auth_headers"]
        
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
                },
                headers=auth_headers
            )
        
        # Get tasks by status using query parameter
        response = client.get(f"/alignment/?status={AlignmentStatus.PENDING.value}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(task["status"] == AlignmentStatus.PENDING.value for task in data)
    
    def test_pagination(self, client, sample_audio_file, sample_text_file, setup_database):
        """Test pagination of alignment tasks"""
        test_data = setup_database
        models = test_data
        auth_headers = test_data["auth_headers"]
        
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
                    },
                    headers=auth_headers
                )
        
        # Test pagination
        response = client.get("/alignment/?skip=0&limit=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2
