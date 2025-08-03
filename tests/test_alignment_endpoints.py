import pytest
import os
from fastapi.testclient import TestClient
from app.models import AlignmentStatus

class TestAlignmentEndpoints:
    
    def test_create_alignment_task_success(self, client: TestClient, sample_audio_file, sample_text_file):
        """Test successful creation of alignment task"""
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
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
    
    def test_create_alignment_task_with_wav(self, client: TestClient, sample_wav_file, sample_text_file):
        """Test creation with WAV file"""
        with open(sample_wav_file, "rb") as audio, open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.wav", audio, "audio/wav"),
                    "text_file": ("test.txt", text, "text/plain")
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_audio_filename"] == "test.wav"
    
    def test_create_alignment_task_invalid_audio_format(self, client: TestClient, sample_text_file):
        """Test creation with invalid audio format"""
        with open(sample_text_file, "rb") as text:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.pdf", text, "application/pdf"),
                    "text_file": ("test.txt", text, "text/plain")
                }
            )
        
        assert response.status_code == 400
        assert "Invalid audio file" in response.json()["detail"]
    
    def test_create_alignment_task_invalid_text_format(self, client: TestClient, sample_audio_file):
        """Test creation with invalid text format"""
        with open(sample_audio_file, "rb") as audio:
            response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.pdf", audio, "application/pdf")
                }
            )
        
        assert response.status_code == 400
        assert "Invalid text file" in response.json()["detail"]
    
    def test_get_alignment_tasks(self, client: TestClient, sample_audio_file, sample_text_file):
        """Test getting all alignment tasks"""
        # First create a task
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            create_response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                }
            )
        
        # Then get all tasks
        response = client.get("/alignment/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_alignment_task_by_id(self, client: TestClient, sample_audio_file, sample_text_file):
        """Test getting specific alignment task"""
        # First create a task
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            create_response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                }
            )
        
        task_id = create_response.json()["id"]
        
        # Get the task by ID
        response = client.get(f"/alignment/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["original_audio_filename"] == "test.mp3"
    
    def test_get_nonexistent_alignment_task(self, client: TestClient):
        """Test getting non-existent alignment task"""
        response = client.get("/alignment/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_update_alignment_task(self, client: TestClient, sample_audio_file, sample_text_file):
        """Test updating alignment task"""
        # First create a task
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            create_response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
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
    
    def test_update_nonexistent_alignment_task(self, client: TestClient):
        """Test updating non-existent alignment task"""
        update_data = {"status": AlignmentStatus.COMPLETED.value}
        response = client.put("/alignment/999", json=update_data)
        assert response.status_code == 404
    
    def test_delete_alignment_task(self, client: TestClient, sample_audio_file, sample_text_file):
        """Test deleting alignment task"""
        # First create a task
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            create_response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
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
    
    def test_delete_nonexistent_alignment_task(self, client: TestClient):
        """Test deleting non-existent alignment task"""
        response = client.delete("/alignment/999")
        assert response.status_code == 404
    
    def test_get_tasks_by_status(self, client: TestClient, sample_audio_file, sample_text_file):
        """Test getting tasks by status"""
        # First create a task
        with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
            create_response = client.post(
                "/alignment/",
                files={
                    "audio_file": ("test.mp3", audio, "audio/mpeg"),
                    "text_file": ("test.txt", text, "text/plain")
                }
            )
        
        # Get tasks by status
        response = client.get(f"/alignment/status/{AlignmentStatus.PENDING.value}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(task["status"] == AlignmentStatus.PENDING.value for task in data)
    
    def test_pagination(self, client: TestClient, sample_audio_file, sample_text_file):
        """Test pagination of alignment tasks"""
        # Create multiple tasks
        for i in range(3):
            with open(sample_audio_file, "rb") as audio, open(sample_text_file, "rb") as text:
                client.post(
                    "/alignment/",
                    files={
                        "audio_file": (f"test{i}.mp3", audio, "audio/mpeg"),
                        "text_file": (f"test{i}.txt", text, "text/plain")
                    }
                )
        
        # Test pagination
        response = client.get("/alignment/?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2
