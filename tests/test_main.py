"""Tests for the main application module."""

from fastapi.testclient import TestClient

from toveco_voting.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    """Test the root endpoint returns correct response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to ToVéCo Voting Platform"
    assert "version" in data
    assert data["status"] == "running"


def test_health_check() -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_docs_available() -> None:
    """Test that API documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/redoc")
    assert response.status_code == 200
