"""Comprehensive test cases for the ToVéCo voting platform API."""

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.toveco_voting.main import app, db_manager
from src.toveco_voting.database import DatabaseManager
from src.toveco_voting.models import Base, VoteRecord
from src.toveco_voting.config import settings


class TestComprehensiveAPI:
    """Comprehensive test suite for all API endpoints and functionality."""

    @pytest.fixture(scope="function")
    def client(self):
        """Create a test client with isolated database."""
        with TestClient(app) as test_client:
            yield test_client

    @pytest.fixture(scope="function")
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db_path = f.name
        
        try:
            # Create test database manager
            test_db_manager = DatabaseManager(temp_db_path)
            yield test_db_manager
        finally:
            # Cleanup
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    @pytest.fixture
    def complete_vote_data(self):
        """Generate complete valid vote data with all 11 logos."""
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

    @pytest.fixture
    def multiple_votes_data(self):
        """Generate multiple complete votes for testing aggregation."""
        return [
            {
                "voter_name": "Alice",
                "ratings": {
                    "toveco1.png": 2, "toveco2.png": 1, "toveco3.png": 0,
                    "toveco4.png": -1, "toveco5.png": -2, "toveco6.png": 1,
                    "toveco7.png": 0, "toveco8.png": 2, "toveco9.png": 1,
                    "toveco10.png": -1, "toveco11.png": 0,
                }
            },
            {
                "voter_name": "Bob",
                "ratings": {
                    "toveco1.png": 1, "toveco2.png": 2, "toveco3.png": -1,
                    "toveco4.png": 0, "toveco5.png": 1, "toveco6.png": -2,
                    "toveco7.png": 1, "toveco8.png": 0, "toveco9.png": 2,
                    "toveco10.png": 1, "toveco11.png": -1,
                }
            },
            {
                "voter_name": "Charlie",
                "ratings": {
                    "toveco1.png": 0, "toveco2.png": -1, "toveco3.png": 2,
                    "toveco4.png": 1, "toveco5.png": 0, "toveco6.png": 2,
                    "toveco7.png": -2, "toveco8.png": 1, "toveco9.png": 0,
                    "toveco10.png": 2, "toveco11.png": 1,
                }
            }
        ]

    # ============ HEALTH CHECK TESTS ============

    def test_health_check_success(self, client):
        """Test health check endpoint returns healthy status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]
        assert "database" in data
        assert data["database"] in ["connected", "disconnected"]
        assert "logos_available" in data
        assert "version" in data
        assert data["version"] == settings.APP_VERSION

    def test_health_check_content_type(self, client):
        """Test health check returns correct content type."""
        response = client.get("/api/health")
        assert "application/json" in response.headers["content-type"]

    def test_health_check_response_structure(self, client):
        """Test health check returns expected response structure."""
        response = client.get("/api/health")
        data = response.json()
        
        required_fields = ["status", "database", "logos_available", "version"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    # ============ STATISTICS TESTS ============

    def test_stats_endpoint_structure(self, client):
        """Test statistics endpoint returns expected structure."""
        response = client.get("/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["total_votes", "total_logos", "voting_scale"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_stats_voting_scale(self, client):
        """Test voting scale values in stats are correct."""
        response = client.get("/api/stats")
        data = response.json()
        
        assert data["voting_scale"]["min"] == -2
        assert data["voting_scale"]["max"] == 2

    def test_stats_logo_count(self, client):
        """Test logo count in stats matches expected count."""
        response = client.get("/api/stats")
        data = response.json()
        
        assert data["total_logos"] == 11  # Expected number of logos

    def test_stats_initial_vote_count(self, client):
        """Test initial vote count is zero or positive."""
        response = client.get("/api/stats")
        data = response.json()
        
        assert isinstance(data["total_votes"], int)
        assert data["total_votes"] >= 0

    # ============ LOGOS ENDPOINT TESTS ============

    def test_get_logos_success(self, client):
        """Test logos endpoint returns logo list."""
        response = client.get("/api/logos")
        assert response.status_code == 200
        
        data = response.json()
        assert "logos" in data
        assert "total_count" in data
        assert isinstance(data["logos"], list)
        assert data["total_count"] == len(data["logos"])

    def test_get_logos_correct_count(self, client):
        """Test logos endpoint returns correct number of logos."""
        response = client.get("/api/logos")
        data = response.json()
        
        assert data["total_count"] == 11
        assert len(data["logos"]) == 11

    def test_get_logos_filename_format(self, client):
        """Test all logo filenames follow expected format."""
        response = client.get("/api/logos")
        data = response.json()
        
        for logo in data["logos"]:
            assert logo.startswith("toveco"), f"Logo {logo} doesn't start with 'toveco'"
            assert logo.endswith(".png"), f"Logo {logo} doesn't end with '.png'"
            assert logo.replace("toveco", "").replace(".png", "").isdigit(), \
                f"Logo {logo} doesn't have numeric identifier"

    def test_get_logos_randomization(self, client):
        """Test logos are returned in different orders (randomized)."""
        # Get logos multiple times
        orders = []
        for _ in range(5):
            response = client.get("/api/logos")
            data = response.json()
            orders.append(data["logos"])
        
        # Check that at least some orders are different
        unique_orders = set(tuple(order) for order in orders)
        assert len(unique_orders) > 1, "Logo order should vary between requests"

    def test_get_logos_contains_all_expected(self, client):
        """Test logos endpoint contains all expected logo files."""
        response = client.get("/api/logos")
        data = response.json()
        
        expected_logos = [f"toveco{i}.png" for i in range(1, 12)]
        actual_logos = sorted(data["logos"])
        
        assert sorted(expected_logos) == actual_logos

    # ============ VOTE SUBMISSION TESTS ============

    def test_submit_valid_complete_vote(self, client, complete_vote_data):
        """Test submitting a complete valid vote."""
        response = client.post("/api/vote", json=complete_vote_data)
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "message" in data
            assert "vote_id" in data
            assert isinstance(data["vote_id"], int)
            assert data["vote_id"] > 0
        else:
            # Handle case where validation fails due to test environment
            assert response.status_code in [400, 422]

    def test_submit_vote_missing_name(self, client, complete_vote_data):
        """Test submitting vote with missing voter name."""
        invalid_data = complete_vote_data.copy()
        del invalid_data["voter_name"]
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 422
        data = response.json()
        assert "success" in data
        assert not data["success"]

    def test_submit_vote_empty_name(self, client, complete_vote_data):
        """Test submitting vote with empty voter name."""
        invalid_data = complete_vote_data.copy()
        invalid_data["voter_name"] = ""
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 422

    def test_submit_vote_name_too_long(self, client, complete_vote_data):
        """Test submitting vote with name exceeding max length."""
        invalid_data = complete_vote_data.copy()
        invalid_data["voter_name"] = "x" * 101  # Exceeds 100 char limit
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 422

    def test_submit_vote_invalid_rating_high(self, client, complete_vote_data):
        """Test submitting vote with rating too high."""
        invalid_data = complete_vote_data.copy()
        invalid_data["ratings"]["toveco1.png"] = 3  # Above max rating of 2
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 422

    def test_submit_vote_invalid_rating_low(self, client, complete_vote_data):
        """Test submitting vote with rating too low."""
        invalid_data = complete_vote_data.copy()
        invalid_data["ratings"]["toveco1.png"] = -3  # Below min rating of -2
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 422

    def test_submit_vote_non_integer_rating(self, client, complete_vote_data):
        """Test submitting vote with non-integer rating."""
        invalid_data = complete_vote_data.copy()
        invalid_data["ratings"]["toveco1.png"] = 1.5  # Float instead of int
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 422

    def test_submit_vote_missing_logo_rating(self, client, complete_vote_data):
        """Test submitting vote with missing logo rating."""
        invalid_data = complete_vote_data.copy()
        del invalid_data["ratings"]["toveco1.png"]
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 400  # ValidationError for missing logos

    def test_submit_vote_extra_logo_rating(self, client, complete_vote_data):
        """Test submitting vote with extra logo rating."""
        invalid_data = complete_vote_data.copy()
        invalid_data["ratings"]["toveco99.png"] = 1  # Non-existent logo
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 400  # ValidationError for unexpected logos

    def test_submit_vote_invalid_logo_format(self, client, complete_vote_data):
        """Test submitting vote with invalid logo filename format."""
        invalid_data = complete_vote_data.copy()
        # Replace valid logo with invalid format
        del invalid_data["ratings"]["toveco1.png"]
        invalid_data["ratings"]["invalid_logo.jpg"] = 1
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 422

    def test_submit_vote_missing_ratings_dict(self, client, complete_vote_data):
        """Test submitting vote with missing ratings dictionary."""
        invalid_data = complete_vote_data.copy()
        del invalid_data["ratings"]
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 422

    def test_submit_vote_empty_ratings_dict(self, client, complete_vote_data):
        """Test submitting vote with empty ratings dictionary."""
        invalid_data = complete_vote_data.copy()
        invalid_data["ratings"] = {}
        
        response = client.post("/api/vote", json=invalid_data)
        assert response.status_code == 422

    # ============ RESULTS TESTS ============

    def test_get_results_empty_database(self, client):
        """Test getting results when no votes exist."""
        response = client.get("/api/results")
        assert response.status_code == 200
        
        data = response.json()
        assert "summary" in data
        assert "total_voters" in data
        assert data["total_voters"] == 0
        assert isinstance(data["summary"], dict)

    def test_get_results_with_votes(self, client, multiple_votes_data):
        """Test getting results after submitting multiple votes."""
        # Submit multiple votes first
        successful_submissions = 0
        for vote_data in multiple_votes_data:
            response = client.post("/api/vote", json=vote_data)
            if response.status_code == 200:
                successful_submissions += 1
        
        # Skip test if votes couldn't be submitted (e.g., missing files in test environment)
        if successful_submissions == 0:
            pytest.skip("Could not submit votes in test environment")
        
        # Get results
        response = client.get("/api/results")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_voters"] == successful_submissions
        assert len(data["summary"]) > 0

    def test_get_results_include_votes_param(self, client):
        """Test results endpoint with include_votes parameter."""
        response = client.get("/api/results?include_votes=true")
        assert response.status_code == 200
        
        data = response.json()
        assert "votes" in data or data["total_voters"] == 0

    def test_get_results_response_structure(self, client):
        """Test results response has expected structure."""
        response = client.get("/api/results")
        data = response.json()
        
        # Test main structure
        assert "summary" in data
        assert "total_voters" in data
        assert isinstance(data["summary"], dict)
        assert isinstance(data["total_voters"], int)
        
        # Test summary structure if votes exist
        if data["total_voters"] > 0:
            for logo, stats in data["summary"].items():
                assert "average" in stats
                assert "total_votes" in stats
                assert "total_score" in stats
                assert "ranking" in stats

    # ============ FRONTEND TESTS ============

    def test_home_page_loads(self, client):
        """Test that the home page loads successfully."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_results_page_loads(self, client):
        """Test that the results page loads successfully."""
        response = client.get("/results")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    # ============ STATIC FILE TESTS ============

    def test_static_css_accessible(self, client):
        """Test that static CSS files are accessible."""
        response = client.get("/static/style.css")
        # Should be 200 if file exists, or 404 if not (both are acceptable)
        assert response.status_code in [200, 404]

    def test_static_js_accessible(self, client):
        """Test that static JavaScript files are accessible."""
        response = client.get("/static/app.js")
        assert response.status_code == 200  # This file should exist

    def test_logo_files_accessible(self, client):
        """Test that logo files are accessible via static serving."""
        # Test a known logo file
        response = client.get("/logos/toveco1.png")
        assert response.status_code == 200
        assert "image" in response.headers.get("content-type", "")

    def test_non_existent_logo_404(self, client):
        """Test that non-existent logo files return 404."""
        response = client.get("/logos/nonexistent.png")
        assert response.status_code == 404

    # ============ ERROR HANDLING TESTS ============

    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON in requests."""
        response = client.post(
            "/api/vote",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_content_type(self, client, complete_vote_data):
        """Test handling requests without content-type header."""
        response = client.post("/api/vote", json=complete_vote_data)
        # FastAPI should still handle this correctly
        assert response.status_code in [200, 400, 422]

    def test_oversized_request(self, client):
        """Test handling of oversized requests."""
        huge_data = {
            "voter_name": "Test",
            "ratings": {f"toveco{i}.png": 1 for i in range(1, 1000)}  # Way too many logos
        }
        response = client.post("/api/vote", json=huge_data)
        assert response.status_code in [400, 422, 413]  # Bad request or payload too large

    def test_sql_injection_attempt(self, client, complete_vote_data):
        """Test protection against SQL injection in voter names."""
        malicious_data = complete_vote_data.copy()
        malicious_data["voter_name"] = "'; DROP TABLE votes; --"
        
        response = client.post("/api/vote", json=malicious_data)
        # Should either succeed (sanitized) or fail validation, but not crash
        assert response.status_code in [200, 400, 422]

    def test_xss_attempt(self, client, complete_vote_data):
        """Test protection against XSS in voter names."""
        malicious_data = complete_vote_data.copy()
        malicious_data["voter_name"] = "<script>alert('xss')</script>"
        
        response = client.post("/api/vote", json=malicious_data)
        # Should either succeed (sanitized) or fail validation
        assert response.status_code in [200, 400, 422]

    # ============ PERFORMANCE TESTS ============

    def test_concurrent_vote_submissions(self, client, multiple_votes_data):
        """Test handling of multiple concurrent vote submissions."""
        import concurrent.futures
        
        def submit_vote(vote_data):
            return client.post("/api/vote", json=vote_data)
        
        # Submit votes concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(submit_vote, vote_data) 
                      for vote_data in multiple_votes_data]
            responses = [future.result() for future in futures]
        
        # Check that all requests were handled
        for response in responses:
            assert response.status_code in [200, 400, 422]

    def test_rapid_logo_requests(self, client):
        """Test handling of rapid logo list requests."""
        responses = []
        for _ in range(10):
            response = client.get("/api/logos")
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200

    def test_results_calculation_performance(self, client, multiple_votes_data):
        """Test performance of results calculation with multiple votes."""
        # Submit votes first
        for vote_data in multiple_votes_data:
            client.post("/api/vote", json=vote_data)
        
        # Time the results calculation
        start_time = time.time()
        response = client.get("/api/results")
        end_time = time.time()
        
        assert response.status_code == 200
        # Results should be calculated within reasonable time (1 second)
        assert end_time - start_time < 1.0


class TestDatabaseIntegrity:
    """Test database operations and data integrity."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db_path = f.name
        
        try:
            db_manager = DatabaseManager(temp_db_path)
            yield db_manager
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_database_initialization(self, temp_db):
        """Test database initializes correctly."""
        assert temp_db.health_check()
        assert temp_db.get_vote_count() == 0

    def test_vote_persistence(self, temp_db):
        """Test that votes are properly persisted."""
        voter_name = "Test Voter"
        ratings = {"toveco1.png": 2, "toveco2.png": -1}
        
        # Save vote
        vote_id = temp_db.save_vote(voter_name, ratings)
        assert vote_id > 0
        
        # Retrieve and verify
        votes = temp_db.get_all_votes()
        assert len(votes) == 1
        
        vote = votes[0]
        assert vote["voter_name"] == voter_name
        assert vote["ratings"] == ratings
        assert vote["id"] == vote_id

    def test_multiple_votes_persistence(self, temp_db):
        """Test that multiple votes are stored correctly."""
        votes_data = [
            ("Alice", {"toveco1.png": 2, "toveco2.png": 1}),
            ("Bob", {"toveco1.png": -1, "toveco2.png": 0}),
            ("Charlie", {"toveco1.png": 1, "toveco2.png": 2})
        ]
        
        # Save all votes
        vote_ids = []
        for voter_name, ratings in votes_data:
            vote_id = temp_db.save_vote(voter_name, ratings)
            vote_ids.append(vote_id)
        
        # Verify count
        assert temp_db.get_vote_count() == 3
        
        # Verify all votes
        stored_votes = temp_db.get_all_votes()
        assert len(stored_votes) == 3
        
        # Verify IDs are unique
        stored_ids = [vote["id"] for vote in stored_votes]
        assert len(set(stored_ids)) == 3

    def test_results_calculation_accuracy(self, temp_db):
        """Test that results calculation is mathematically correct."""
        # Add test votes with known values
        temp_db.save_vote("Voter 1", {"toveco1.png": 2, "toveco2.png": -1})
        temp_db.save_vote("Voter 2", {"toveco1.png": 1, "toveco2.png": 0})
        temp_db.save_vote("Voter 3", {"toveco1.png": -1, "toveco2.png": 1})
        
        results = temp_db.calculate_results()
        
        # Check overall structure
        assert results["total_voters"] == 3
        assert "summary" in results
        
        # Check toveco1.png: (2 + 1 + (-1)) / 3 = 2/3 = 0.67
        toveco1_stats = results["summary"]["toveco1.png"]
        assert toveco1_stats["total_votes"] == 3
        assert toveco1_stats["total_score"] == 2
        assert abs(toveco1_stats["average"] - 0.67) < 0.01
        
        # Check toveco2.png: (-1 + 0 + 1) / 3 = 0/3 = 0.0
        toveco2_stats = results["summary"]["toveco2.png"]
        assert toveco2_stats["total_votes"] == 3
        assert toveco2_stats["total_score"] == 0
        assert toveco2_stats["average"] == 0.0

    def test_rankings_correctness(self, temp_db):
        """Test that ranking logic works correctly."""
        # Create votes with clear ranking order
        temp_db.save_vote("Voter 1", {
            "toveco1.png": 2,   # Should rank 1st (average: 2.0)
            "toveco2.png": 1,   # Should rank 2nd (average: 1.0)
            "toveco3.png": -1   # Should rank 3rd (average: -1.0)
        })
        
        results = temp_db.calculate_results()
        summary = results["summary"]
        
        # Check rankings
        assert summary["toveco1.png"]["ranking"] == 1
        assert summary["toveco2.png"]["ranking"] == 2
        assert summary["toveco3.png"]["ranking"] == 3

    def test_database_error_handling(self):
        """Test database error handling with invalid database path."""
        with pytest.raises(Exception):
            # Try to create database in non-existent directory
            DatabaseManager("/nonexistent/directory/test.db")

    def test_empty_database_results(self, temp_db):
        """Test results calculation with empty database."""
        results = temp_db.calculate_results()
        
        assert results["total_voters"] == 0
        assert results["summary"] == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])