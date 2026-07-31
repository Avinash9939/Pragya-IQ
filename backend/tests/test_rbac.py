import pytest
from app.domain.entities.user import UserRole

def get_auth_headers(client, email, password, role):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role}
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_get_current_user_me_authenticated(client):
    """Test GET /users/me with valid token returns current user details."""
    headers = get_auth_headers(client, "me@example.com", "password123", "viewer")
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["role"] == "viewer"

def test_get_current_user_me_unauthenticated(client):
    """Test GET /users/me with no token returns 401."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

def test_get_users_admin_allowed(client):
    """Test GET /users as admin role returns 200 and all users list."""
    admin_headers = get_auth_headers(client, "admin@example.com", "adminpass", "admin")
    response = client.get("/api/v1/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    # Should contain at least the admin user
    assert len(data) >= 1
    assert any(u["email"] == "admin@example.com" for u in data)

def test_get_users_non_admin_forbidden(client):
    """Test GET /users as analyst/viewer role returns 403."""
    analyst_headers = get_auth_headers(client, "analyst@example.com", "analystpass", "analyst")
    response = client.get("/api/v1/users", headers=analyst_headers)
    assert response.status_code == 403
    assert "operation not permitted" in response.json()["detail"].lower()
