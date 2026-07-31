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

def test_kpi_engine_pipeline(client, db_session):
    """Test full KPI pipeline including mapping configurator, invalid errors, and calculations."""
    headers = get_auth_headers(client, "kpi@example.com", "password123", "analyst")

    # Generate synthetic hand-computable dataset
    df_synth = pd.DataFrame({
        "tx_date": ["2026-01-01", "2026-01-02", "2026-06-01", "2026-06-02"],
        "tx_amount": [100.0, 50.0, 200.0, 150.0],
        "cust_id": [1, 2, 3, 1],
        "prod_name": ["widget", "gizmo", "gadget", "widget"],
        "tx_region": ["North", "North", "South", "South"],
        "tx_quantity": [2, 1, 4, 3]
    })

    csv_buffer = io.StringIO()
    df_synth.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    file_payload = {"file": ("kpis.csv", io.BytesIO(csv_bytes), "text/csv")}

    # 1. Upload dataset
    upload_res = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 2. Call GET sales before setting mapping (should return 400 with missing details)
    get_sales_res = client.get(f"/api/v1/kpi/{dataset_id}/sales", headers=headers)
    assert get_sales_res.status_code == 400
    assert "Missing required column mappings" in get_sales_res.json()["detail"]

    # 3. Call PUT mapping with invalid column name (should return 400)
    mapping_payload = {
        "mapping": {
            "date": "tx_date",
            "amount": "tx_amount",
            "customer_id": "cust_id",
            "product": "invalid_column_name", # Does not exist
            "region": "tx_region",
            "quantity": "tx_quantity"
        }
    }
    mapping_res = client.put(f"/api/v1/datasets/{dataset_id}/mapping", headers=headers, json=mapping_payload)
    assert mapping_res.status_code == 400
    assert "does not exist in dataset headers" in mapping_res.json()["detail"]

    # 4. Call PUT mapping with invalid semantic keys (should return 400)
    bad_keys_payload = {
        "mapping": {
            "invalid_semantic_key": "tx_date"
        }
    }
    mapping_res2 = client.put(f"/api/v1/datasets/{dataset_id}/mapping", headers=headers, json=bad_keys_payload)
    assert mapping_res2.status_code == 400
    assert "Invalid mapping semantic keys" in mapping_res2.json()["detail"]

    # 5. Set correct mapping configuration
    valid_payload = {
        "mapping": {
            "date": "tx_date",
            "amount": "tx_amount",
            "customer_id": "cust_id",
            "product": "prod_name",
            "region": "tx_region",
            "quantity": "tx_quantity"
        }
    }
    mapping_res3 = client.put(f"/api/v1/datasets/{dataset_id}/mapping", headers=headers, json=valid_payload)
    assert mapping_res3.status_code == 200

    # 6. Clean dataset first to produce the file on disk (cleaning sets status to CLEANED)
    clean_res = client.post(f"/api/v1/datasets/{dataset_id}/clean", headers=headers)
    assert clean_res.status_code == 200

    # 7. Compute Sales KPIs and assert correctness
    sales_res = client.get(f"/api/v1/kpi/{dataset_id}/sales", headers=headers)
    assert sales_res.status_code == 200
    sales_data = sales_res.json()
    assert sales_data["total_revenue"] == 500.0
    assert sales_data["average_order_value"] == 125.0
    assert sales_data["revenue_growth_percent"] == pytest.approx(133.333, abs=0.01)
    assert sales_data["top_products"]["widget"] == 250.0
    assert sales_data["top_products"]["gadget"] == 200.0

    # 8. Compute Customer KPIs and assert correctness
    cust_res = client.get(f"/api/v1/kpi/{dataset_id}/customer", headers=headers)
    assert cust_res.status_code == 200
    cust_data = cust_res.json()
    assert cust_data["total_unique_customers"] == 3
    assert cust_data["new_customers"] == 1
    assert cust_data["returning_customers"] == 1
    assert cust_data["customer_lifetime_value_estimate"] == pytest.approx(166.667, abs=0.01)

    # 9. Compute Product KPIs and assert correctness
    prod_res = client.get(f"/api/v1/kpi/{dataset_id}/product", headers=headers)
    assert prod_res.status_code == 200
    prod_data = prod_res.json()
    assert prod_data["best_seller_revenue"]["product"] == "widget"
    assert prod_data["best_seller_revenue"]["value"] == 250.0
    assert prod_data["worst_seller_revenue"]["product"] == "gizmo"
    assert prod_data["worst_seller_revenue"]["value"] == 50.0
    assert prod_data["best_seller_quantity"]["product"] == "widget"
    assert prod_data["best_seller_quantity"]["value"] == 5

    # 10. Compute Regional KPIs and assert correctness
    region_res = client.get(f"/api/v1/kpi/{dataset_id}/region", headers=headers)
    assert region_res.status_code == 200
    region_data = region_res.json()
    assert region_data["revenue_by_region"]["North"] == 150.0
    assert region_data["revenue_by_region"]["South"] == 350.0
