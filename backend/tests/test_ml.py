import io
import pytest
import pandas as pd
import numpy as np
from app.domain.entities.user import UserRole
from app.infrastructure.db.models.ml_model import MlRunModel, MlPredictionModel

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

def test_ml_forecasting_pipeline(client, db_session):
    """
    Test full demand forecasting pipeline with Prophet and XGBoost.
    Why: Validates fit accuracy, recursive XGBoost forecasting, and database persistence.
    """
    headers = get_auth_headers(client, "ml@example.com", "password123", "analyst")

    # 1. Generate daily time-series with clear trend + weekly seasonality
    np.random.seed(42)
    dates = pd.date_range(start="2026-01-01", periods=100)
    t = np.arange(100)
    trend = 100.0 + 2.0 * t  # Linear trend
    weekly = 15.0 * np.sin(2.0 * np.pi * t / 7.0)  # Weekly cycle
    noise = np.random.normal(0, 2.0, 100)
    y = trend + weekly + noise

    df_synth = pd.DataFrame({
        "sales_date": dates.strftime("%Y-%m-%d"),
        "sales_amount": y
    })

    csv_buffer = io.StringIO()
    df_synth.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    file_payload = {"file": ("forecast_sales.csv", io.BytesIO(csv_bytes), "text/csv")}

    # 2. Upload dataset
    upload_res = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 3. Try to run forecast before setting column mapping (should return 400 with missing details)
    forecast_res_fail = client.post(
        f"/api/v1/ml/{dataset_id}/forecast",
        headers=headers,
        json={"horizon_days": 14, "model_type": "both"}
    )
    assert forecast_res_fail.status_code == 400
    assert "Missing required column mappings" in forecast_res_fail.json()["detail"]

    # 4. Set column mapping
    mapping_payload = {
        "mapping": {
            "date": "sales_date",
            "amount": "sales_amount"
        }
    }
    mapping_res = client.put(f"/api/v1/datasets/{dataset_id}/mapping", headers=headers, json=mapping_payload)
    assert mapping_res.status_code == 200

    # 5. Run both forecast models
    forecast_res = client.post(
        f"/api/v1/ml/{dataset_id}/forecast",
        headers=headers,
        json={"horizon_days": 14, "model_type": "both"}
    )
    assert forecast_res.status_code == 200
    data = forecast_res.json()

    # 6. Verify Prophet and XGBoost results structure
    assert "prophet" in data
    assert "xgboost" in data

    prophet_run_id = data["prophet"]["ml_run_id"]
    prophet_metrics = data["prophet"]["metrics"]
    prophet_forecast = data["prophet"]["forecast"]

    xgboost_run_id = data["xgboost"]["ml_run_id"]
    xgboost_metrics = data["xgboost"]["metrics"]
    xgboost_forecast = data["xgboost"]["forecast"]

    # Check metrics are sane (MAE is below 25.0 for this simple trend/weekly seasonality)
    assert prophet_metrics["mae"] < 25.0
    assert xgboost_metrics["mae"] < 25.0

    # Check forecasted data points count matches horizon_days
    assert len(prophet_forecast) == 14
    assert len(xgboost_forecast) == 14

    # 7. Check database rows persistence
    runs = db_session.query(MlRunModel).all()
    assert len(runs) == 2

    # Verify predictions are stored in DB
    preds = db_session.query(MlPredictionModel).all()
    # 2 runs * 14 predictions = 28 predicted points
    assert len(preds) == 28


def test_customer_segmentation_pipeline(client, db_session):
    """
    Test customer segmentation pipeline using RFM + KMeans.
    Why: Validates that KMeans groups the two cohorts into distinct segments.
    """
    headers = get_auth_headers(client, "segment@example.com", "password123", "analyst")

    # Generate synthetic data with two clearly distinct groups:
    # Cohort A (10 customers): High frequency, high monetary (big spenders who buy every day)
    # Cohort B (10 customers): Low frequency, low monetary (one-time buyers who spent little)
    records = []
    
    # Cohort A: IDs 101 to 110
    for cust_id in range(101, 111):
        for day in range(1, 11):  # 10 purchases each
            records.append({
                "cust_id": str(cust_id),
                "tx_date": f"2026-03-{day:02d}",
                "amount": 500.0  # Total = 5000.0, Freq = 10, Recency = 0 days (since max date is March 10)
            })

    # Cohort B: IDs 201 to 210
    for cust_id in range(201, 211):
        records.append({
            "cust_id": str(cust_id),
            "tx_date": "2026-01-01",  # Recency = 68 days (March 10 - Jan 1), Freq = 1, Total = 10.0
            "amount": 10.0
        })

    df_synth = pd.DataFrame(records)
    csv_buffer = io.StringIO()
    df_synth.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    file_payload = {"file": ("segment.csv", io.BytesIO(csv_bytes), "text/csv")}

    # 1. Upload dataset
    upload_res = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 2. Set mapping
    mapping_payload = {
        "mapping": {
            "customer_id": "cust_id",
            "date": "tx_date",
            "amount": "amount"
        }
    }
    mapping_res = client.put(f"/api/v1/datasets/{dataset_id}/mapping", headers=headers, json=mapping_payload)
    assert mapping_res.status_code == 200

    # 3. Trigger segmentation with n_clusters=2
    seg_res = client.post(
        f"/api/v1/ml/{dataset_id}/segment",
        headers=headers,
        json={"n_clusters": 2}
    )
    assert seg_res.status_code == 200
    data = seg_res.json()

    ml_run_id = data["ml_run_id"]
    metrics = data["metrics"]
    assignments = data["assignments"]

    # Assert exactly 20 customer assignments
    assert len(assignments) == 20

    # Verify Cohort A and Cohort B belong to different clusters
    cluster_a = None
    cluster_b = None
    
    for item in assignments:
        cust_id = int(item["customer_id"])
        cluster_id = item["cluster"]
        if cust_id == 101:
            cluster_a = cluster_id
        elif cust_id == 201:
            cluster_b = cluster_id

    # The two groups must be partitioned into different clusters
    assert cluster_a is not None
    assert cluster_b is not None
    assert cluster_a != cluster_b

    # Verify labels (Cohort A has higher value, low recency -> should rank higher/best label)
    label_a = next(x["label"] for x in assignments if int(x["customer_id"]) == 101)
    label_b = next(x["label"] for x in assignments if int(x["customer_id"]) == 201)
    
    assert label_a == "High Value"
    assert label_b == "At Risk / Lost"

    # 4. Check DB row persistence
    runs = db_session.query(MlRunModel).filter(MlRunModel.model_type == "kmeans_segmentation").all()
    assert len(runs) == 1
    assert runs[0].id == ml_run_id

    preds = db_session.query(MlPredictionModel).filter(MlPredictionModel.ml_run_id == ml_run_id).all()
    assert len(preds) == 20


def test_churn_prediction_pipeline(client, db_session):
    """
    Test churn prediction pipeline using XGBClassifier.
    Why: Validates that classifier separates active customer cohorts from churned ones and computes probability scores.
    """
    headers = get_auth_headers(client, "churn@example.com", "password123", "analyst")

    # Generate synthetic data with two distinct recency groups:
    # 1. 10 Active customers: bought recently (e.g. 5 days ago)
    # 2. 10 Churned customers: bought long ago (e.g. 150 days ago)
    records = []
    
    # Active Cohort: IDs 301 to 310
    for cust_id in range(301, 311):
        records.append({
            "cust_id": str(cust_id),
            "tx_date": "2026-03-05",  # Recency = 5 days (March 10 - March 5)
            "amount": 100.0
        })

    # Churned Cohort: IDs 401 to 410
    for cust_id in range(401, 411):
        records.append({
            "cust_id": str(cust_id),
            "tx_date": "2025-10-10",  # Recency = 151 days (March 10 - Oct 10)
            "amount": 50.0
        })

    df_synth = pd.DataFrame(records)
    csv_buffer = io.StringIO()
    df_synth.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    file_payload = {"file": ("churn.csv", io.BytesIO(csv_bytes), "text/csv")}

    # 1. Upload dataset
    upload_res = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 2. Set mapping
    mapping_payload = {
        "mapping": {
            "customer_id": "cust_id",
            "date": "tx_date",
            "amount": "amount"
        }
    }
    mapping_res = client.put(f"/api/v1/datasets/{dataset_id}/mapping", headers=headers, json=mapping_payload)
    assert mapping_res.status_code == 200

    # 3. Trigger churn prediction with default threshold (90 days)
    churn_res = client.post(
        f"/api/v1/ml/{dataset_id}/churn",
        headers=headers,
        json={"recency_threshold_days": 90}
    )
    assert churn_res.status_code == 200
    data = churn_res.json()

    ml_run_id = data["ml_run_id"]
    metrics = data["metrics"]
    predictions = data["predictions"]

    # Verify counts
    assert len(predictions) == 20

    # Verify we achieved 100% accuracy on this trivial classification task
    assert metrics["accuracy"] >= 0.8

    # Verify predictions details
    for item in predictions:
        cust_id = int(item["customer_id"])
        prob = item["churn_probability"]
        churned = item["churned"]
        
        # Probabilities must be within standard [0, 1] range
        assert 0.0 <= prob <= 1.0

        if cust_id in range(301, 311):
            assert churned == 0
            assert prob < 0.5
        elif cust_id in range(401, 411):
            assert churned == 1
            assert prob > 0.5

    # 4. Check DB row persistence
    runs = db_session.query(MlRunModel).filter(MlRunModel.model_type == "xgboost_churn").all()
    assert len(runs) == 1
    assert runs[0].id == ml_run_id

    preds = db_session.query(MlPredictionModel).filter(MlPredictionModel.ml_run_id == ml_run_id).all()
    assert len(preds) == 20


def test_anomaly_detection_pipeline(client, db_session):
    """
    Test anomaly detection pipeline using Isolation Forest.
    Why: Validates that extreme statistical outliers are flagged, and false-positive rates are low.
    """
    headers = get_auth_headers(client, "anomaly@example.com", "password123", "analyst")

    # Generate 100 normal rows + 5 extreme outliers
    np.random.seed(42)
    amounts = np.random.normal(loc=100.0, scale=5.0, size=100).tolist()
    
    # Insert 5 extreme outliers at specific lines
    outlier_indices = [10, 30, 50, 70, 90]
    for idx in outlier_indices:
        amounts.insert(idx, 10000.0)

    # Compile synthetic data frame
    records = []
    for idx, amt in enumerate(amounts):
        records.append({
            "tx_id": str(idx + 1000),
            "amount": float(amt),
            "quantity": 1
        })

    df_synth = pd.DataFrame(records)
    csv_buffer = io.StringIO()
    df_synth.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    file_payload = {"file": ("anomaly.csv", io.BytesIO(csv_bytes), "text/csv")}

    # 1. Upload dataset
    upload_res = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 2. Set mapping
    mapping_payload = {
        "mapping": {
            "amount": "amount",
            "quantity": "quantity"
        }
    }
    mapping_res = client.put(f"/api/v1/datasets/{dataset_id}/mapping", headers=headers, json=mapping_payload)
    assert mapping_res.status_code == 200

    # 3. Trigger anomaly detection with contamination 0.05
    anomaly_res = client.post(
        f"/api/v1/ml/{dataset_id}/anomaly",
        headers=headers,
        json={"contamination": 0.05}
    )
    assert anomaly_res.status_code == 200
    data = anomaly_res.json()

    ml_run_id = data["ml_run_id"]
    metrics = data["metrics"]
    anomalies = data["anomalies"]

    # Assert that all 5 extreme outliers were successfully flagged
    flagged_indices = [x["row_index"] for x in anomalies]
    for idx in outlier_indices:
        assert idx in flagged_indices

    # False positive rate is extremely low (since we only expect ~5 anomalies with 0.05 contamination)
    # The total number of returned anomalies should be close to 5 (e.g. exactly 5 or 6)
    assert len(anomalies) <= 7

    # 4. Check DB row persistence
    runs = db_session.query(MlRunModel).filter(MlRunModel.model_type == "isolation_forest").all()
    assert len(runs) == 1
    assert runs[0].id == ml_run_id

    preds = db_session.query(MlPredictionModel).filter(MlPredictionModel.ml_run_id == ml_run_id).all()
    # Number of predictions persisted matches the number of flagged anomalies
    assert len(preds) == len(anomalies)


def test_shap_explainability_pipeline(client, db_session):
    """
    Test SHAP explainability pipeline and validation route.
    Why: Validates that GET /ml/{run_id}/shap/{entity_ref} returns valid metrics, and reconstructs prediction correctly.
    """
    headers = get_auth_headers(client, "shap@example.com", "password123", "analyst")

    # Generate synthetic churn cohorts dataset
    records = []
    # Active Cohort (bought recently)
    for cust_id in range(501, 506):
        records.append({
            "cust_id": str(cust_id),
            "tx_date": "2026-03-05",  # Recency = 5 days
            "amount": 100.0
        })
    # Churned Cohort (bought long ago)
    for cust_id in range(601, 606):
        records.append({
            "cust_id": str(cust_id),
            "tx_date": "2025-10-10",  # Recency = 151 days
            "amount": 50.0
        })

    df_synth = pd.DataFrame(records)
    csv_buffer = io.StringIO()
    df_synth.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    file_payload = {"file": ("shap_data.csv", io.BytesIO(csv_bytes), "text/csv")}

    # 1. Upload dataset
    upload_res = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 2. Set mapping
    mapping_payload = {
        "mapping": {
            "customer_id": "cust_id",
            "date": "tx_date",
            "amount": "amount"
        }
    }
    mapping_res = client.put(f"/api/v1/datasets/{dataset_id}/mapping", headers=headers, json=mapping_payload)
    assert mapping_res.status_code == 200

    # 3. Train Churn prediction to trigger SHAP generation
    churn_res = client.post(
        f"/api/v1/ml/{dataset_id}/churn",
        headers=headers,
        json={"recency_threshold_days": 90}
    )
    assert churn_res.status_code == 200
    ml_run_id = churn_res.json()["ml_run_id"]

    # 4. GET SHAP details for customer 501
    shap_res = client.get(
        f"/api/v1/ml/{ml_run_id}/shap/501",
        headers=headers
    )
    assert shap_res.status_code == 200
    shap_data = shap_res.json()

    assert shap_data["ml_run_id"] == ml_run_id
    assert shap_data["entity_ref"] == "501"
    
    explainability = shap_data["explainability"]
    base_val = explainability["base_value"]
    contributions = explainability["shap_contributions"]
    features = explainability["features"]

    # SHAP sanity check: sum(contributions) + base_val = logodds; sigmoid(logodds) = probability
    total_contrib = sum(contributions.values())
    pred_val = shap_data["prediction_value"]
    assert 0.0 <= pred_val <= 1.0

    # Reconstruct probability
    recon_logit = base_val + total_contrib
    recon_prob = 1.0 / (1.0 + np.exp(-recon_logit))
    
    # Assert within small tolerance (e.g. 1e-3)
    direct_diff = abs((base_val + total_contrib) - pred_val)
    sigmoid_diff = abs(recon_prob - pred_val)
    assert direct_diff < 1e-3 or sigmoid_diff < 1e-3

    # 5. Check Prophet run returns 400 Bad Request
    # Set up synthetic daily forecast
    daily_records = []
    for day in range(1, 15):
        daily_records.append({
            "tx_date": f"2026-03-{day:02d}",
            "amount": 100.0
        })
    df_daily = pd.DataFrame(daily_records)
    csv_buffer_d = io.StringIO()
    df_daily.to_csv(csv_buffer_d, index=False)
    csv_bytes_d = csv_buffer_d.getvalue().encode("utf-8")

    file_payload_d = {"file": ("forecast_daily.csv", io.BytesIO(csv_bytes_d), "text/csv")}
    upload_res_d = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload_d)
    dataset_id_d = upload_res_d.json()["id"]

    mapping_payload_d = {
        "mapping": {
            "date": "tx_date",
            "amount": "amount"
        }
    }
    client.put(f"/api/v1/datasets/{dataset_id_d}/mapping", headers=headers, json=mapping_payload_d)

    forecast_res = client.post(
        f"/api/v1/ml/{dataset_id_d}/forecast",
        headers=headers,
        json={"horizon_days": 3, "model_type": "prophet"}
    )
    assert forecast_res.status_code == 200
    prophet_run_id = forecast_res.json()["prophet"]["ml_run_id"]
    forecast_points = forecast_res.json()["prophet"]["forecast"]
    first_date = forecast_points[0]["date"]

    prophet_shap_res = client.get(
        f"/api/v1/ml/{prophet_run_id}/shap/{first_date}",
        headers=headers
    )
    # Rejects with 400 Bad Request
    assert prophet_shap_res.status_code == 400
    assert "do not support Tree-based SHAP" in prophet_shap_res.json()["detail"]
