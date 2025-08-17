import pytest
import tempfile
import os
from fastapi import UploadFile
from api.utils import (
    validate_file_extension,
    validate_audio_file,
    validate_text_file,
    save_uploaded_file,
    create_upload_directory,
    ALLOWED_AUDIO_EXTENSIONS,
    ALLOWED_TEXT_EXTENSIONS
)

class TestUtils:
    
    def test_validate_file_extension_valid_audio(self):
        """Test validation of valid audio extensions"""
        assert validate_file_extension("test.mp3", ALLOWED_AUDIO_EXTENSIONS) == True
        assert validate_file_extension("test.wav", ALLOWED_AUDIO_EXTENSIONS) == True
        assert validate_file_extension("TEST.MP3", ALLOWED_AUDIO_EXTENSIONS) == True  # Case insensitive
    
    def test_validate_file_extension_invalid_audio(self):
        """Test validation of invalid audio extensions"""
        assert validate_file_extension("test.pdf", ALLOWED_AUDIO_EXTENSIONS) == False
        assert validate_file_extension("test.txt", ALLOWED_AUDIO_EXTENSIONS) == False
        assert validate_file_extension("test", ALLOWED_AUDIO_EXTENSIONS) == False
    
    def test_validate_file_extension_valid_text(self):
        """Test validation of valid text extensions"""
        assert validate_file_extension("test.txt", ALLOWED_TEXT_EXTENSIONS) == True
        assert validate_file_extension("TEST.TXT", ALLOWED_TEXT_EXTENSIONS) == True
    
    def test_validate_file_extension_invalid_text(self):
        """Test validation of invalid text extensions"""
        assert validate_file_extension("test.pdf", ALLOWED_TEXT_EXTENSIONS) == False
        assert validate_file_extension("test.mp3", ALLOWED_TEXT_EXTENSIONS) == False
    
    def test_validate_file_extension_empty_filename(self):
        """Test validation with empty filename"""
        assert validate_file_extension("", ALLOWED_AUDIO_EXTENSIONS) == False
        assert validate_file_extension(None, ALLOWED_AUDIO_EXTENSIONS) == False
    
    def test_validate_audio_file_valid(self):
        """Test audio file validation with valid files"""
        # Create mock UploadFile objects
        class MockUploadFile:
            def __init__(self, filename):
                self.filename = filename
        
        assert validate_audio_file(MockUploadFile("test.mp3")) == True
        assert validate_audio_file(MockUploadFile("test.wav")) == True
    
    def test_validate_audio_file_invalid(self):
        """Test audio file validation with invalid files"""
        class MockUploadFile:
            def __init__(self, filename):
                self.filename = filename
        
        assert validate_audio_file(MockUploadFile("test.txt")) == False
        assert validate_audio_file(MockUploadFile("test.pdf")) == False
    
    def test_validate_text_file_valid(self):
        """Test text file validation with valid files"""
        class MockUploadFile:
            def __init__(self, filename):
                self.filename = filename
        
        assert validate_text_file(MockUploadFile("test.txt")) == True
    
    def test_validate_text_file_invalid(self):
        """Test text file validation with invalid files"""
        class MockUploadFile:
            def __init__(self, filename):
                self.filename = filename
        
        assert validate_text_file(MockUploadFile("test.mp3")) == False
        assert validate_text_file(MockUploadFile("test.pdf")) == False
    
    def test_create_upload_directory(self):
        """Test creation of upload directory"""
        import shutil
        
        # Clean up if exists
        if os.path.exists("uploads"):
            shutil.rmtree("uploads")
        
        create_upload_directory()
        assert os.path.exists("uploads")
        assert os.path.isdir("uploads")
        
        # Clean up
        shutil.rmtree("uploads")
    
    def test_save_uploaded_file(self):
        """Test saving uploaded file"""
        # Create a mock UploadFile
        class MockFile:
            def __init__(self, content):
                self.content = content
                self.position = 0
            
            def read(self):
                return self.content
        
        class MockUploadFile:
            def __init__(self, filename, content):
                self.filename = filename
                self.file = MockFile(content)
        
        # Test file saving
        test_content = b"test file content"
        mock_file = MockUploadFile("test.mp3", test_content)
        
        file_path = save_uploaded_file(mock_file, "audio")
        
        # Verify file was saved
        assert os.path.exists(file_path)
        assert file_path.startswith("uploads/")
        assert file_path.endswith(".mp3")
        
        # Verify content
        with open(file_path, "rb") as f:
            saved_content = f.read()
        assert saved_content == test_content
        
        # Clean up
        os.remove(file_path)
        if os.path.exists("uploads") and not os.listdir("uploads"):
            os.rmdir("uploads")
