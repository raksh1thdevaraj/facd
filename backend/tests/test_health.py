from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    """Verify GET / returns welcome payload and API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["api_v1"] == "/api/v1"


def test_root_health_endpoint(client: TestClient) -> None:
    """Verify GET /health returns valid health check payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert "services" in data
    assert data["services"]["database"] == "connected"
    assert data["services"]["storage"] == "accessible"


def test_api_v1_health_endpoint(client: TestClient) -> None:
    """Verify GET /api/v1/health returns valid health check payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert data["version"] == "0.1.0"
    assert data["services"]["database"] == "connected"


def test_404_not_found(client: TestClient) -> None:
    """Verify non-existent routes return 404."""
    response = client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404
