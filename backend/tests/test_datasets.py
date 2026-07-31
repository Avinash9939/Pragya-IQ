import io
import pytest
import pandas as pd
from app.domain.entities.user import UserRole
from app.core.config import settings

def get_auth_headers(client, email, password, role):
    # Register
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role}
    )
    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_upload_csv_success(client):
    """Test successful CSV file upload by an Analyst."""
    headers = get_auth_headers(client, "analyst@example.com", "password123", "analyst")
    
    # Tiny CSV data representation
    csv_data = "col1,col2,col3\n1,2,3\n4,5,6"
    file_payload = {"file": ("test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    
    response = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["filename"] == "test.csv"
    assert data["row_count"] == 2
    assert data["column_count"] == 3
    assert data["status"] == "VALIDATED"
    assert "id" in data

def test_upload_excel_success(client):
    """Test successful Excel file upload (.xlsx) by an Admin."""
    headers = get_auth_headers(client, "admin@example.com", "password123", "admin")
    
    # Generate binary Excel content in memory
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_bytes = excel_buffer.getvalue()
    
    file_payload = {
        "file": ("test.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }
    
    response = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["filename"] == "test.xlsx"
    assert data["row_count"] == 3
    assert data["column_count"] == 2
    assert data["status"] == "VALIDATED"

def test_upload_unsupported_file_type_rejected(client):
    """Test rejection of unsupported file extensions like .txt."""
    headers = get_auth_headers(client, "analyst2@example.com", "password123", "analyst")
    
    text_data = "Just some text"
    file_payload = {"file": ("test.txt", io.BytesIO(text_data.encode("utf-8")), "text/plain")}
    
    response = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    assert response.status_code == 400
    assert "file type not supported" in response.json()["detail"].lower()

def test_upload_oversized_file_rejected(client):
    """Test rejection of files exceeding the configured limit."""
    headers = get_auth_headers(client, "analyst3@example.com", "password123", "analyst")
    
    # Save the original limit, and temporarily modify Settings to 1MB
    original_max = settings.max_upload_size_mb
    settings.max_upload_size_mb = 1 # Set to 1MB
    
    try:
        # Create a payload of 1.5MB (more than 1MB)
        large_bytes = b"0" * int(1.5 * 1024 * 1024)
        file_payload = {"file": ("large.csv", io.BytesIO(large_bytes), "text/csv")}
        
        response = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
        assert response.status_code == 413
        assert "file size exceeds maximum limit" in response.json()["detail"].lower()
    finally:
        # Restore settings
        settings.max_upload_size_mb = original_max

def test_upload_unauthorized_user_type_forbidden(client):
    """Test that a Viewer is forbidden from uploading datasets."""
    headers = get_auth_headers(client, "viewer_rbac@example.com", "password123", "viewer")
    
    csv_data = "col1,col2\n1,2"
    file_payload = {"file": ("test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    
    response = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    assert response.status_code == 403

def test_get_dataset_owner_isolation(client):
    """Test user isolation rules: cannot list or retrieve other users' datasets."""
    # Set up user A (analyst) and user B (analyst)
    headers_a = get_auth_headers(client, "usera@example.com", "password123", "analyst")
    headers_b = get_auth_headers(client, "userb@example.com", "password123", "analyst")
    
    # User A uploads a CSV dataset
    csv_data = "col1,col2\n1,2"
    file_payload = {"file": ("dataset_a.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    
    upload_res = client.post("/api/v1/datasets/upload", headers=headers_a, files=file_payload)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]
    
    # 1. User A lists their own datasets, should see dataset_a.csv
    list_a_res = client.get("/api/v1/datasets", headers=headers_a)
    assert list_a_res.status_code == 200
    assert len(list_a_res.json()) == 1
    assert list_a_res.json()[0]["id"] == dataset_id
    
    # 2. User B lists their own datasets, should NOT see dataset_a.csv (should be empty list)
    list_b_res = client.get("/api/v1/datasets", headers=headers_b)
    assert list_b_res.status_code == 200
    assert len(list_b_res.json()) == 0
    
    # 3. User A retrieves their own dataset details by ID, should succeed
    get_a_res = client.get(f"/api/v1/datasets/{dataset_id}", headers=headers_a)
    assert get_a_res.status_code == 200
    assert get_a_res.json()["id"] == dataset_id
    
    # 4. User B retrieves User A's dataset, should fail with 404
    get_b_res = client.get(f"/api/v1/datasets/{dataset_id}", headers=headers_b)
    assert get_b_res.status_code == 404
