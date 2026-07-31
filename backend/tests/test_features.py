import io
import os
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

def test_feature_engineering_success(client, db_session):
    """Test successful feature engineering over a synthetic CSV dataset."""
    headers = get_auth_headers(client, "engine@example.com", "password123", "analyst")

    # Generate synthetic dataframe:
    # - 1 date col: `date`
    # - 1 low-cardinality category col: `low_card` (vals: A, B)
    # - 1 high-cardinality category col: `high_card` (vals: cat_1 .. cat_20)
    # - 1 numeric col: `value` (vals: 10 .. 200)
    # - 1 identifier: `user_id`
    # Size: 20 rows
    dates = pd.date_range("2026-01-01", periods=20)
    low_card = ["A" if i % 2 == 0 else "B" for i in range(20)]
    high_card = [f"cat_{i}" for i in range(20)]
    values = [float(i * 10) for i in range(20)]
    user_ids = [100 + i for i in range(20)]

    df_synth = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "low_card": low_card,
        "high_card": high_card,
        "value": values,
        "user_id": user_ids
    })

    csv_buffer = io.StringIO()
    df_synth.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    file_payload = {"file": ("synthetic.csv", io.BytesIO(csv_bytes), "text/csv")}

    # 1. Upload dataset
    upload_res = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 2. Try engineer-features before cleaning (should conflict with 409)
    conf_res = client.post(f"/api/v1/datasets/{dataset_id}/engineer-features", headers=headers)
    assert conf_res.status_code == 409

    # 3. Clean dataset to move status to CLEANED
    clean_res = client.post(f"/api/v1/datasets/{dataset_id}/clean", headers=headers)
    assert clean_res.status_code == 200

    # 4. Trigger feature engineering
    feat_res = client.post(f"/api/v1/datasets/{dataset_id}/engineer-features", headers=headers)
    assert feat_res.status_code == 200
    
    summary = feat_res.json()
    
    # Assert date split features added
    assert "date_year" in summary["columns_added"]
    assert "date_is_weekend" in summary["columns_added"]
    assert "low_card_A" in summary["columns_added"]
    assert "low_card_B" in summary["columns_added"]

    # Assert encoding strategy classification
    assert summary["columns_encoded"]["low_card"] == "one-hot"
    assert summary["columns_encoded"]["high_card"] == "label"

    # Assert scaling was done on value column, but NOT on user_id (identifier)
    assert "value" in summary["columns_scaled"]
    assert "user_id" not in summary["columns_scaled"]

    # Assert database model status is now FEATURED
    from app.infrastructure.db.models.dataset_model import DatasetModel
    db_dataset = db_session.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    assert db_dataset.status == "FEATURED"
    assert "_features.csv" in db_dataset.storage_path

    # Read the features file directly from disk and check that the values scaled
    from app.infrastructure.storage.local_storage import LocalStorage
    storage = LocalStorage()
    features_full_path = storage.get_path(db_dataset.storage_path)
    assert os.path.exists(features_full_path)
    df_result = pd.read_csv(features_full_path)

    # The scaled column 'value' must have mean ~0 and std ~1
    assert df_result["value"].mean() == pytest.approx(0.0, abs=1e-7)
    # Verify user_id is unchanged
    assert df_result["user_id"].iloc[0] == 100
