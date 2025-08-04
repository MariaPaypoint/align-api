import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def client():
    # Create tables
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    # Clean up
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test.db"):
        os.remove("test.db")

@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up tables after each test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_audio_file():
    """Create a sample audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(b"fake audio content")
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def sample_text_file():
    """Create a sample text file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"This is a sample text content for alignment.")
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def sample_wav_file():
    """Create a sample WAV file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(b"fake wav audio content")
        yield f.name
    os.unlink(f.name)
