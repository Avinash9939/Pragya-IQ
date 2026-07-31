from datetime import datetime, timezone
import io
import os
import pytest
from app.domain.entities.kpi_result import KpiResult
from app.domain.entities.ml import MlRun, MlPrediction
from app.domain.entities.ai_output import AiOutput
from app.infrastructure.db.repositories.kpi_result_repository import SQLAlchemyKpiResultRepository
from app.infrastructure.db.repositories.ml_repository import SQLAlchemyMlRunRepository, SQLAlchemyMlPredictionRepository
from app.infrastructure.db.repositories.ai_output_repository import SQLAlchemyAiOutputRepository


def get_auth_headers(client, email, password, role):
    # Register User
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role}
    )
    # Login User
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_generate_and_download_report_workflow(client, db_session):
    # 1. Setup owners and tenant A vs tenant B
    headers_a = get_auth_headers(client, "usera@example.com", "password123", "analyst")
    headers_b = get_auth_headers(client, "userb@example.com", "password123", "analyst")
    
    # 2. Upload dataset for User A
    csv_data = "col1,col2\n1,2"
    file_payload = {"file": ("dataset_a.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", headers=headers_a, files=file_payload)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]
    
    # 3. Fit KPI results in DB
    kpi_repo = SQLAlchemyKpiResultRepository(db_session)
    kpi_repo.create(KpiResult(id=None, dataset_id=dataset_id, kpi_type="sales", value_json={"total_revenue": 100000.0, "revenue_growth_percent": 5.0, "average_order_value": 50.0}, computed_at=datetime.now(timezone.utc)))
    kpi_repo.create(KpiResult(id=None, dataset_id=dataset_id, kpi_type="customer", value_json={"total_unique_customers": 100, "customer_lifetime_value_estimate": 500.0, "new_customers": 20, "returning_customers": 80}, computed_at=datetime.now(timezone.utc)))
    kpi_repo.create(KpiResult(id=None, dataset_id=dataset_id, kpi_type="product", value_json={"best_seller_revenue": {"product": "A", "value": 5000.0}, "worst_seller_revenue": {"product": "B", "value": 100.0}}, computed_at=datetime.now(timezone.utc)))
    kpi_repo.create(KpiResult(id=None, dataset_id=dataset_id, kpi_type="region", value_json={"revenue_by_region": {"North": 80000.0, "South": 20000.0}, "regional_growth_percent": {"North": 5.0, "South": 2.0}}, computed_at=datetime.now(timezone.utc)))

    # 4. Insert Fake ML runs
    run_repo = SQLAlchemyMlRunRepository(db_session)
    pred_repo = SQLAlchemyMlPredictionRepository(db_session)
    
    forecast_run = run_repo.create(MlRun(id=None, dataset_id=dataset_id, model_type="xgboost", params_json={"horizon_days": 7}, metrics_json={"rmse": 0.5}, created_at=datetime.now(timezone.utc)))
    pred_repo.create_batch([
        MlPrediction(id=None, ml_run_id=forecast_run.id, entity_ref="2026-07-12", prediction=100.0, shap_values_json={}),
        MlPrediction(id=None, ml_run_id=forecast_run.id, entity_ref="2026-07-13", prediction=110.0, shap_values_json={})
    ])

    churn_run = run_repo.create(MlRun(id=None, dataset_id=dataset_id, model_type="xgboost_churn", params_json={}, metrics_json={}, created_at=datetime.now(timezone.utc)))
    pred_repo.create_batch([
        MlPrediction(id=None, ml_run_id=churn_run.id, entity_ref="Cust1", prediction=0.92, shap_values_json={})
    ])

    anomaly_run = run_repo.create(MlRun(id=None, dataset_id=dataset_id, model_type="isolation_forest", params_json={}, metrics_json={"anomaly_count": 2}, created_at=datetime.now(timezone.utc)))
    pred_repo.create_batch([
        MlPrediction(id=None, ml_run_id=anomaly_run.id, entity_ref="10", prediction=-0.12, shap_values_json={})
    ])

    # 5. Insert Fake AI Summary and Recommendations Cache
    ai_out_repo = SQLAlchemyAiOutputRepository(db_session)
    ai_out_repo.create(AiOutput(id=None, dataset_id=dataset_id, output_type="summary", content_json={"summary": "Fake summary"}, generated_at=datetime.now(timezone.utc)))
    ai_out_repo.create(AiOutput(id=None, dataset_id=dataset_id, output_type="recommendations", content_json={"recommendations": ["Recommendation 1", "Recommendation 2"]}, generated_at=datetime.now(timezone.utc)))

    # 6. Generate Report
    gen_res = client.post(f"/api/v1/reports/{dataset_id}/generate", headers=headers_a)
    assert gen_res.status_code == 200
    report_data = gen_res.json()
    assert report_data["dataset_id"] == dataset_id
    assert "file_path" in report_data
    assert "id" in report_data
    report_id = report_data["id"]

    # Verify report PDF file on disk
    file_path = report_data["file_path"]
    assert os.path.exists(file_path)
    assert os.path.getsize(file_path) > 0
    with open(file_path, "rb") as f:
        magic_bytes = f.read(4)
        assert magic_bytes == b"%PDF"

    # 7. Download PDF report (success)
    dl_res = client.get(f"/api/v1/reports/{report_id}/download", headers=headers_a)
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"
    assert "attachment; filename" in dl_res.headers["content-disposition"]
    # Check downloaded content starts with %PDF
    assert dl_res.content[:4] == b"%PDF"

    # 8. Cross-tenant download (failure: should be 404 per requirements to avoid leak)
    steal_res = client.get(f"/api/v1/reports/{report_id}/download", headers=headers_b)
    assert steal_res.status_code == 404

    # 9. Clean up report file
    try:
        os.remove(file_path)
    except OSError:
        pass
