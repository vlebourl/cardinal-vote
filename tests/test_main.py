"""Tests for the main application module."""

import pytest
from fastapi.testclient import TestClient

from src.toveco_voting.main import app


class TestMainApplication:
    """Test class for main application endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        with TestClient(app) as test_client:
            yield test_client

    def test_root_endpoint(self, client):
        """Test the root endpoint returns HTML page."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_results_page(self, client):
        """Test the results endpoint returns HTML page."""
        response = client.get("/results")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "logos_available" in data
        assert "version" in data

    def test_stats_endpoint(self, client):
        """Test the stats endpoint."""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_votes" in data
        assert "total_logos" in data
        assert "voting_scale" in data

    def test_logos_endpoint(self, client):
        """Test the logos endpoint."""
        response = client.get("/api/logos")
        assert response.status_code == 200
        data = response.json()
        assert "logos" in data
        assert "total_count" in data

    def test_docs_available(self, client):
        """Test that API documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200

        response = client.get("/redoc")
        assert response.status_code == 200
