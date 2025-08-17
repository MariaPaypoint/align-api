"""
Tests for user system (Step 2).
"""

import pytest
from api.domains.users.models import User, SubscriptionType
from api.domains.users.crud import UserService
from api.domains.auth.security import get_password_hash

@pytest.fixture
def setup_database(db_session):
    """Setup test database with sample data."""
    # Create subscription types
    free_sub = db_session.query(SubscriptionType).filter(SubscriptionType.name == "free").first()
    if not free_sub:
        free_sub = SubscriptionType(
            name="free",
            display_name="Free",
            total_storage_limit=1073741824,  # 1GB
            max_concurrent_tasks=1,
            price_monthly=0.00,
            is_active=True
        )
        db_session.add(free_sub)
        
    basic_sub = db_session.query(SubscriptionType).filter(SubscriptionType.name == "basic").first()
    if not basic_sub:
        basic_sub = SubscriptionType(
            name="basic",
            display_name="Basic",
            total_storage_limit=10737418240,  # 10GB
            max_concurrent_tasks=3,
            price_monthly=9.99,
            is_active=True
        )
        db_session.add(basic_sub)
    
    db_session.commit()
    yield


def test_user_registration(setup_database, client):
    """Test user registration."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert data["role"] == "user"
    assert data["subscription_type_name"] == "Free"
    assert data["used_storage"] == 0
    assert data["is_active"] == True


def test_user_registration_duplicate_email(setup_database, client):
    """Test user registration with duplicate email."""
    user_data = {
        "email": "duplicate@example.com",
        "username": "user1",
        "password": "testpassword123"
    }
    
    # First registration
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    
    # Duplicate email registration
    user_data["username"] = "user2"
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_user_registration_duplicate_username(setup_database, client):
    """Test user registration with duplicate username."""
    user_data = {
        "email": "user1@example.com",
        "username": "duplicateuser",
        "password": "testpassword123"
    }
    
    # First registration
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    
    # Duplicate username registration
    user_data["email"] = "user2@example.com"
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]


def test_user_login(setup_database, client):
    """Test user login."""
    # First register a user
    user_data = {
        "email": "login@example.com",
        "username": "loginuser",
        "password": "testpassword123"
    }
    
    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code == 200
    
    # Now login
    login_data = {
        "username": "loginuser",
        "password": "testpassword123"
    }
    
    response = client.post("/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_user_login_invalid_credentials(setup_database, client):
    """Test user login with invalid credentials."""
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword"
    }
    
    response = client.post("/auth/login", json=login_data)
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_protected_endpoint_without_token(setup_database, client):
    """Test protected endpoint without authentication token."""
    response = client.get("/auth/me")
    
    assert response.status_code == 403
    assert "Not authenticated" in response.json()["detail"]


def test_protected_endpoint_with_token(setup_database, client):
    """Test protected endpoint with valid token."""
    # Register and login
    user_data = {
        "email": "protected@example.com",
        "username": "protecteduser",
        "password": "testpassword123"
    }
    
    client.post("/auth/register", json=user_data)
    
    login_response = client.post("/auth/login", json={
        "username": "protecteduser",
        "password": "testpassword123"
    })
    
    token = login_response.json()["access_token"]
    
    # Access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "protecteduser"
    assert data["email"] == "protected@example.com"


def test_quota_limits(setup_database, client):
    """Test user quota information."""
    # Register and login
    user_data = {
        "email": "quota@example.com",
        "username": "quotauser",
        "password": "testpassword123"
    }
    
    client.post("/auth/register", json=user_data)
    
    login_response = client.post("/auth/login", json={
        "username": "quotauser",
        "password": "testpassword123"
    })
    
    token = login_response.json()["access_token"]
    
    # Get quota information
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/quota", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_storage_limit"] == 1073741824  # 1GB for free plan
    assert data["used_storage"] == 0
    assert data["available_storage"] == 1073741824
    assert data["max_concurrent_tasks"] == 1
    assert data["subscription_type"] == "Free"


def test_protected_alignment_endpoint(setup_database, client):
    """Test that alignment endpoints require authentication."""
    # Try to access alignment endpoint without token
    response = client.get("/alignment/")
    
    assert response.status_code == 403


def test_user_service_methods(setup_database, db_session):
    """Test UserService methods directly."""
    db = db_session
    
    # Test user creation
    from api.domains.users.schemas import UserCreate
    user_create = UserCreate(
        email="service@example.com",
        username="serviceuser",
        password="testpassword123"
    )
    
    user = UserService.create_user(db, user_create)
    assert user.email == "service@example.com"
    assert user.username == "serviceuser"
    assert user.subscription_type.name == "free"
    
    # Test user authentication
    auth_user = UserService.authenticate_user(db, "serviceuser", "testpassword123")
    assert auth_user is not None
    assert auth_user.id == user.id
    
    # Test wrong password
    wrong_auth = UserService.authenticate_user(db, "serviceuser", "wrongpassword")
    assert wrong_auth is None
    
    # Test quota check
    quota = UserService.get_user_quota(db, user.id)
    assert quota is not None
    assert quota.total_storage_limit == 1073741824
    
    # Test storage quota check
    has_quota = UserService.check_storage_quota(db, user.id, 1000000)  # 1MB
    assert has_quota == True
    
    no_quota = UserService.check_storage_quota(db, user.id, 2000000000)  # 2GB
    assert no_quota == False


def test_jwt_token_expiration(setup_database, client):
    """Test JWT token with invalid/expired format."""
    headers = {"Authorization": "Bearer invalid.token.here"}
    response = client.get("/auth/me", headers=headers)
    
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]
