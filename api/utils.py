import os
import uuid
from fastapi import UploadFile
from typing import Tuple

UPLOAD_DIR = "uploads"
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav"}
ALLOWED_TEXT_EXTENSIONS = {".txt"}

def create_upload_directory():
    """Create upload directory if it doesn't exist"""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
    """Validate file extension"""
    if not filename:
        return False
    extension = os.path.splitext(filename)[1].lower()
    return extension in allowed_extensions

def save_uploaded_file(file: UploadFile, file_type: str) -> str:
    """Save uploaded file and return the file path"""
    create_upload_directory()
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    return file_path

def validate_audio_file(file: UploadFile) -> bool:
    """Validate audio file"""
    return validate_file_extension(file.filename, ALLOWED_AUDIO_EXTENSIONS)

def validate_text_file(file: UploadFile) -> bool:
    """Validate text file"""
    return validate_file_extension(file.filename, ALLOWED_TEXT_EXTENSIONS)
