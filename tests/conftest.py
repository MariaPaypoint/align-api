import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from api.main import app
from api.database import get_db, Base
from api.domains.users.models import User, SubscriptionType
from api.domains.users.schemas import UserCreate
from api.domains.users.crud import UserService
from api.domains.models.models import Language, MFAModel
from passlib.context import CryptContext
import requests
import pika
from minio import Minio
from tests.test_database_setup import get_test_engine, setup_test_database, get_test_session_factory
from api.domains.auth.security import create_access_token

# Create test database using universal setup
engine = get_test_engine()
TestingSessionLocal = get_test_session_factory(engine)

# Global variable to hold the current test session
_test_db_session = None

def override_get_db():
    # Use the same session as the current test
    if _test_db_session is not None:
        yield _test_db_session
    else:
        # Fallback to creating new session
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    # Client created for each test to match db_session lifecycle
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db_session():
    """Create a clean database session for each test"""
    global _test_db_session
    
    # Setup test database with all tables
    setup_test_database(engine)
    
    session = TestingSessionLocal()
    _test_db_session = session  # Set global session for override_get_db
    
    try:
        yield session
    finally:
        _test_db_session = None  # Clear global session
        session.close()
        # Drop all tables after each test for isolation
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

@pytest.fixture
def test_user(db_session):
    """Create a test user for authentication"""
    # Create subscription type if doesn't exist
    sub_type = db_session.query(SubscriptionType).filter_by(name="free").first()
    if not sub_type:
        sub_type = SubscriptionType(
            name="free",
            display_name="Free Plan",
            total_storage_limit=100*1024*1024,  # 100MB
            max_concurrent_tasks=1
        )
        db_session.add(sub_type)
        db_session.commit()
    
    test_user = UserService.create_user(db_session, UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    ))
    
    return test_user

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers with JWT token"""
    token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}
