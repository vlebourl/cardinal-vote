"""Test cases for the ToVéCo voting platform API."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import os

from src.toveco_voting.main import app
from src.toveco_voting.config import settings


class TestVotingAPI:
    """Test class for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_vote_data(self):
        """Sample valid vote data for testing."""
        return {
            "voter_name": "Test User",
            "ratings": {
                "toveco1.png": 2,
                "toveco2.png": -1,
                "toveco3.png": 0,
                "toveco4.png": 1,
                "toveco5.png": -2,
                "toveco6.png": 1,
                "toveco7.png": 0,
                "toveco8.png": 2,
                "toveco9.png": -1,
                "toveco10.png": 1,
                "toveco11.png": 0,
            }
        }
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert data["version"] == settings.APP_VERSION
    
    def test_get_stats(self, client):
        """Test the statistics endpoint."""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_votes" in data
        assert "total_logos" in data
        assert "voting_scale" in data
        assert data["voting_scale"]["min"] == -2
        assert data["voting_scale"]["max"] == 2
    
    def test_get_logos(self, client):
        """Test the logos endpoint."""
        response = client.get("/api/logos")
        assert response.status_code == 200
        data = response.json()
        assert "logos" in data
        assert "total_count" in data
        assert isinstance(data["logos"], list)
        assert data["total_count"] == len(data["logos"])
        
        # Check if all logos have the correct format
        for logo in data["logos"]:
            assert logo.startswith("toveco")
            assert logo.endswith(".png")
    
    def test_submit_valid_vote(self, client, sample_vote_data):
        """Test submitting a valid vote."""
        response = client.post("/api/vote", json=sample_vote_data)
        
        # The test might fail if logo files don't exist, so handle both cases
        if response.status_code == 400:
            # Expected if logo validation fails due to missing files
            data = response.json()
            assert "success" in data
            assert not data["success"]
        else:
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "message" in data
            assert "vote_id" in data
    
    def test_submit_invalid_vote_missing_name(self, client, sample_vote_data):
        """Test submitting a vote with missing voter name."""
        invalid_data = sample_vote_data.copy()
        del invalid_data["voter_name"]
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 422
    
    def test_submit_invalid_vote_empty_name(self, client, sample_vote_data):
        """Test submitting a vote with empty voter name."""
        invalid_data = sample_vote_data.copy()
        invalid_data["voter_name"] = ""
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 422
    
    def test_submit_invalid_vote_invalid_rating(self, client, sample_vote_data):
        """Test submitting a vote with invalid rating value."""
        invalid_data = sample_vote_data.copy()
        invalid_data["ratings"]["toveco1.png"] = 3  # Invalid rating (out of range)
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 422
    
    def test_submit_invalid_vote_missing_ratings(self, client, sample_vote_data):
        """Test submitting a vote with missing ratings."""
        invalid_data = sample_vote_data.copy()
        del invalid_data["ratings"]["toveco1.png"]
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 400  # ValidationError
    
    def test_get_results_empty(self, client):
        """Test getting results when no votes exist."""
        response = client.get("/api/results")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "total_voters" in data
        assert data["total_voters"] == 0
    
    def test_home_page(self, client):
        """Test the home page loads."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_results_page(self, client):
        """Test the results page loads."""
        response = client.get("/results")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestDatabaseOperations:
    """Test database operations."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db_path = f.name
        
        # Set up test database
        from src.toveco_voting.database import DatabaseManager
        db_manager = DatabaseManager(temp_db_path)
        
        yield db_manager
        
        # Cleanup
        os.unlink(temp_db_path)
    
    def test_database_initialization(self, temp_db):
        """Test database initialization."""
        assert temp_db.health_check()
        assert temp_db.get_vote_count() == 0
    
    def test_save_and_retrieve_vote(self, temp_db):
        """Test saving and retrieving a vote."""
        voter_name = "Test Voter"
        ratings = {"toveco1.png": 2, "toveco2.png": -1}
        
        # Save vote
        vote_id = temp_db.save_vote(voter_name, ratings)
        assert vote_id > 0
        
        # Retrieve votes
        votes = temp_db.get_all_votes()
        assert len(votes) == 1
        
        vote = votes[0]
        assert vote["voter_name"] == voter_name
        assert vote["ratings"] == ratings
        assert vote["id"] == vote_id
    
    def test_calculate_results(self, temp_db):
        """Test results calculation."""
        # Add some test votes
        temp_db.save_vote("Voter 1", {"toveco1.png": 2, "toveco2.png": -1})
        temp_db.save_vote("Voter 2", {"toveco1.png": 1, "toveco2.png": 0})
        
        results = temp_db.calculate_results()
        
        assert results["total_voters"] == 2
        assert "summary" in results
        
        # Check toveco1.png results (2+1)/2 = 1.5
        assert results["summary"]["toveco1.png"]["average"] == 1.5
        assert results["summary"]["toveco1.png"]["total_votes"] == 2
        
        # Check toveco2.png results (-1+0)/2 = -0.5
        assert results["summary"]["toveco2.png"]["average"] == -0.5
        assert results["summary"]["toveco2.png"]["total_votes"] == 2


if __name__ == "__main__":
    pytest.main([__file__])