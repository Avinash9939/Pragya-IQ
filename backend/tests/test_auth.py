import pytest
from app.domain.entities.user import UserRole

def test_register_user_success(client):
    """Test successful user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123", "role": "viewer"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "viewer"
    assert "id" in data
    assert "hashed_password" not in data

def test_register_duplicate_email(client):
    """Test registration with duplicate email returns 409."""
    # First signup
    client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "password123", "role": "viewer"}
    )
    # Second signup
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "differentpass", "role": "viewer"}
    )
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()

def test_login_success(client):
    """Test login with matching credentials returns valid JWT token."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "password123", "role": "viewer"}
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client):
    """Test login with incorrect password returns 401."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "login_bad@example.com", "password": "password123", "role": "viewer"}
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "login_bad@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()
