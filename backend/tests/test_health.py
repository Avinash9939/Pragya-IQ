from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """
    Test the root endpoint returns 200 and says welcome.
    """
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert "Welcome" in json_data["message"]

def test_health_endpoint():
    """
    Test that the health check endpoint returns status ok and details.
    """
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "ok"
    assert "app_name" in json_data
    assert "environment" in json_data
