import io
import pytest
import pandas as pd
from app.domain.entities.user import UserRole
from app.core.config import settings

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

def test_clean_dataset_success(client, db_session):
    """Test successful data cleaning of a custom CSV layout."""
    headers = get_auth_headers(client, "cleaner@example.com", "password123", "analyst")

    # Generate mock CSV with:
    # - 1 duplicate row (row 2 is exact duplicate of row 1)
    # - 1 row with >50% missing values (row 4 has: col1=empty, col2=empty, col3=9)
    # - 1 missing value filled with median/mode (row 3 has: col1=5, col2=empty, col3=10)
    # - Additional unique normal rows to bound IQR for outlier detection
    # - 1 outlier (row 8 has col1=500, whereas others are ~5)
    # Total input: 8 rows
    csv_data = """col1,col2,col3
5,A,10
5,A,10
5,,10
,,9
5,B,10
5,C,10
5,D,10
500,E,10
"""
    file_payload = {"file": ("toclean.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    
    # 1. Upload the dataset
    upload_res = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 2. Trigger automated cleaning endpoint
    clean_res = client.post(f"/api/v1/datasets/{dataset_id}/clean", headers=headers)
    assert clean_res.status_code == 200
    
    summary = clean_res.json()
    # Check shape summary details
    assert summary["rows_before"] == 8
    # Row 4 dropped (>50% missing) -> 7 rows remaining
    # Row 2 and Row 3 removed (Row 2 is duplicate, Row 3 becomes duplicate after imputation) -> 5 rows remaining
    assert summary["rows_after"] == 5
    assert summary["duplicates_removed"] == 2
    
    # Check missing values counts report
    assert summary["missing_value_counts"]["col2"] == 2
    
    # Verify outlier count (col1 has 500 which is outlier)
    assert summary["outliers_flagged"]["col1"] == 1
    
    # Verify data quality score and grade calculations
    assert summary["quality_score"] == 87.5
    assert summary["grade"] == "B"
    assert summary["quality_label"] == "Good"
    assert summary["missing_percentage"] == 12.5
    assert summary["duplicate_percentage"] == 12.5
    assert summary["penalty_breakdown"] == {
        "missing_percentage": 12.5,
        "duplicate_percentage": 12.5
    }
    
    # Check dataset retrieve status changed to CLEANED
    get_res = client.get(f"/api/v1/datasets/{dataset_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "CLEANED"
    
    # Verify the database model directly since storage_path is excluded from DatasetOut schema
    from app.infrastructure.db.models.dataset_model import DatasetModel
    db_dataset = db_session.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    assert db_dataset is not None
    assert "_cleaned.csv" in db_dataset.storage_path

def test_clean_dataset_not_owned_rejected(client):
    """Test cleaning a dataset owned by another user is rejected with 404."""
    headers_a = get_auth_headers(client, "clean_a@example.com", "password123", "analyst")
    headers_b = get_auth_headers(client, "clean_b@example.com", "password123", "analyst")
    
    csv_data = "col1,col2\n1,2\n3,4"
    file_payload = {"file": ("owner.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    
    # User A uploads dataset
    res_upload = client.post("/api/v1/datasets/upload", headers=headers_a, files=file_payload)
    dataset_id = res_upload.json()["id"]
    
    # User B triggers clean on User A's dataset, should fail with 404
    res_clean = client.post(f"/api/v1/datasets/{dataset_id}/clean", headers=headers_b)
    assert res_clean.status_code == 404

def test_clean_already_cleaned_dataset_reruns(client):
    """Test cleaning an already cleaned dataset behaves sensibly by running successfully again."""
    headers = get_auth_headers(client, "clean_twice@example.com", "password123", "analyst")
    
    csv_data = "col1,col2\n1,2\n1,2"
    file_payload = {"file": ("twice.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    
    # Upload
    res_upload = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    dataset_id = res_upload.json()["id"]
    
    # First cleaning
    res_clean_1 = client.post(f"/api/v1/datasets/{dataset_id}/clean", headers=headers)
    assert res_clean_1.status_code == 200
    assert res_clean_1.json()["duplicates_removed"] == 1
    
    # Second cleaning (using the already cleaned file)
    res_clean_2 = client.post(f"/api/v1/datasets/{dataset_id}/clean", headers=headers)
    assert res_clean_2.status_code == 200
    assert res_clean_2.json()["duplicates_removed"] == 0
