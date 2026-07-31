import io
import os
import gc
import time
import pytest
from app.domain.entities.user import UserRole
from app.infrastructure.db.models.activity_log_model import ActivityLogModel
from app.infrastructure.db.models.system_setting_model import SystemSettingModel
from app.infrastructure.db.models.user_model import UserModel


def robust_cleanup(file_path: str):
    """Robustly deletes dataset files on Windows to resolve test locks."""
    for _ in range(5):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            break
        except Exception:
            gc.collect()
            time.sleep(0.1)


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


def test_login_failure_logging(client, db_session):
    # Truncate tables for clean assert
    db_session.query(ActivityLogModel).delete()
    db_session.commit()

    # Trigger failed login
    client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@example.com", "password": "wrongpassword"}
    )

    # Fetch logs from DB
    logs = db_session.query(ActivityLogModel).all()
    assert len(logs) >= 1
    # Check that failed login has user_id=None and action="login_failed"
    fail_log = next((l for l in logs if l.action == "login_failed"), None)
    assert fail_log is not None
    assert fail_log.user_id is None


def test_dataset_upload_logging(client, db_session):
    # Setup auth headers
    headers = get_auth_headers(client, "analyst@example.com", "pass123", "analyst")

    db_session.query(ActivityLogModel).delete()
    db_session.commit()

    # Upload dataset
    csv_data = "col1,col2\n1,2"
    file_payload = {"file": ("dataset_test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", headers=headers, files=file_payload)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # Verify log entry in DB
    logs = db_session.query(ActivityLogModel).all()
    upload_log = next((l for l in logs if l.action == "dataset_uploaded"), None)
    assert upload_log is not None
    assert upload_log.user_id is not None
    assert f"dataset_id={dataset_id}" in upload_log.resource

    # Check cleanup path
    from app.infrastructure.db.models.dataset_model import DatasetModel
    dataset_in_db = db_session.query(DatasetModel).filter_by(id=dataset_id).first()
    assert dataset_in_db is not None
    storage_path = dataset_in_db.storage_path
    
    # Try deleting the dataset (DELETE route)
    del_res = client.delete(f"/api/v1/datasets/{dataset_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify log of deletion
    logs = db_session.query(ActivityLogModel).all()
    del_log = next((l for l in logs if l.action == "dataset_deleted"), None)
    assert del_log is not None
    assert del_log.user_id is not None
    assert f"dataset_id={dataset_id}" in del_log.resource

    robust_cleanup(storage_path)


def test_logs_rbac_and_ordering(client, db_session):
    admin_headers = get_auth_headers(client, "admin_test@example.com", "adminpass", "admin")
    viewer_headers = get_auth_headers(client, "viewer_test@example.com", "viewpass", "viewer")

    # Add multiple logs
    db_session.query(ActivityLogModel).delete()
    db_session.commit()

    # Manual insert with different timestamp
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    db_session.add(ActivityLogModel(action="action_1", timestamp=now - datetime.timedelta(minutes=5)))
    db_session.add(ActivityLogModel(action="action_2", timestamp=now))
    db_session.commit()

    # Non-admin access should be forbidden (403)
    non_admin_res = client.get("/api/v1/logs", headers=viewer_headers)
    assert non_admin_res.status_code == 403

    # Admin access should return logs newest first
    admin_res = client.get("/api/v1/logs", headers=admin_headers)
    assert admin_res.status_code == 200
    data = admin_res.json()
    assert len(data) >= 2
    # action_2 (newest) should come first
    assert data[0]["action"] == "action_2"
    assert data[1]["action"] == "action_1"


def test_settings_rbac_and_toggles(client, db_session):
    admin_headers = get_auth_headers(client, "admin_settings@example.com", "pass123", "admin")
    viewer_headers = get_auth_headers(client, "viewer_settings@example.com", "pass123", "viewer")

    # Seed
    db_session.query(SystemSettingModel).delete()
    db_session.add(SystemSettingModel(key="maintenance_mode", value="false"))
    db_session.commit()

    # Viewer can read settings
    get_res = client.get("/api/v1/settings", headers=viewer_headers)
    assert get_res.status_code == 200
    assert get_res.json()["maintenance_mode"] is False

    # Viewer cannot update settings (403)
    put_res = client.put("/api/v1/settings", headers=viewer_headers, json={"maintenance_mode": True})
    assert put_res.status_code == 403

    # Admin can update settings
    put_admin_res = client.put("/api/v1/settings", headers=admin_headers, json={"maintenance_mode": True})
    assert put_admin_res.status_code == 200
    assert put_admin_res.json()["maintenance_mode"] is True

    # Check updated value in DB
    get_res_new = client.get("/api/v1/settings", headers=viewer_headers)
    assert get_res_new.json()["maintenance_mode"] is True


def test_user_role_change_by_admin(client, db_session):
    admin_headers = get_auth_headers(client, "admin_role_updater@example.com", "pass123", "admin")
    viewer_headers = get_auth_headers(client, "viewer_to_change@example.com", "pass123", "viewer")

    # Fetch target user from DB
    target_user = db_session.query(UserModel).filter_by(email="viewer_to_change@example.com").first()
    assert target_user is not None
    assert target_user.role == UserRole.VIEWER

    # Non-admin cannot promote (403)
    put_non_admin = client.put(f"/api/v1/users/{target_user.id}/role", headers=viewer_headers, json={"role": "analyst"})
    assert put_non_admin.status_code == 403

    # Admin can promote user
    put_admin = client.put(f"/api/v1/users/{target_user.id}/role", headers=admin_headers, json={"role": "analyst"})
    assert put_admin.status_code == 200
    assert put_admin.json()["role"] == "analyst"

    # Verify log entry in DB
    logs = db_session.query(ActivityLogModel).all()
    role_change_log = next((l for l in logs if l.action == "user_role_changed"), None)
    assert role_change_log is not None
    assert f"target_user_id={target_user.id}" in role_change_log.resource
