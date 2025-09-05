"""Database validation and integrity tests for the ToVéCo voting platform.

This module tests:
- Database schema integrity
- Data validation and constraints
- Transaction handling
- Concurrent access
- Data corruption prevention
- Backup and recovery scenarios
"""

import json
import os
import sqlite3
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from src.toveco_voting.database import DatabaseManager
from src.toveco_voting.models import DatabaseError, VoteRecord


class TestDatabaseSchema:
    """Test database schema integrity and structure."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db_path = f.name

        try:
            db_manager = DatabaseManager(temp_db_path)
            yield db_manager, temp_db_path
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_database_tables_created(self, temp_db):
        """Test that all required tables are created."""
        db_manager, db_path = temp_db

        # Connect directly to database to inspect schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check that votes table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='votes'
        """
        )
        tables = cursor.fetchall()
        assert len(tables) == 1
        assert tables[0][0] == "votes"

        conn.close()

    def test_votes_table_schema(self, temp_db):
        """Test that votes table has correct schema."""
        db_manager, db_path = temp_db

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get table schema
        cursor.execute("PRAGMA table_info(votes)")
        columns = cursor.fetchall()

        # Expected columns: id, voter_name, timestamp, ratings
        column_names = [col[1] for col in columns]
        expected_columns = ["id", "voter_name", "timestamp", "ratings"]

        for col in expected_columns:
            assert col in column_names, f"Missing column: {col}"

        # Check primary key
        pk_columns = [col for col in columns if col[5] == 1]  # pk flag
        assert len(pk_columns) == 1
        assert pk_columns[0][1] == "id"

        conn.close()

    def test_database_file_permissions(self, temp_db):
        """Test database file has appropriate permissions."""
        db_manager, db_path = temp_db

        file_path = Path(db_path)
        assert file_path.exists()
        assert file_path.is_file()

        # Check file is readable and writable
        assert os.access(db_path, os.R_OK)
        assert os.access(db_path, os.W_OK)


class TestDataValidation:
    """Test data validation and constraint enforcement."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db_path = f.name

        try:
            db_manager = DatabaseManager(temp_db_path)
            yield db_manager
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_save_valid_vote(self, temp_db):
        """Test saving a valid vote."""
        voter_name = "Test Voter"
        ratings = {"toveco1.png": 2, "toveco2.png": -1}

        vote_id = temp_db.save_vote(voter_name, ratings)
        assert vote_id > 0

        # Verify vote was saved correctly
        votes = temp_db.get_all_votes()
        assert len(votes) == 1
        assert votes[0]["voter_name"] == voter_name
        assert votes[0]["ratings"] == ratings

    def test_save_vote_empty_name(self, temp_db):
        """Test saving vote with empty voter name."""
        ratings = {"toveco1.png": 1}

        # This should not raise an exception at database level
        # (validation should happen at API level)
        vote_id = temp_db.save_vote("", ratings)
        assert vote_id > 0

    def test_save_vote_long_name(self, temp_db):
        """Test saving vote with very long voter name."""
        long_name = "x" * 1000  # Very long name
        ratings = {"toveco1.png": 1}

        # Database should handle this (SQLite varchar limit is high)
        vote_id = temp_db.save_vote(long_name, ratings)
        assert vote_id > 0

    def test_save_vote_special_characters(self, temp_db):
        """Test saving vote with special characters in name."""
        special_names = [
            "Test User with émojis 🎉",
            "User with 'quotes' and \"double quotes\"",
            "User with <html> & XML chars",
            "Пользователь на русском",
            "用户中文名",
        ]

        for name in special_names:
            ratings = {"toveco1.png": 1}
            vote_id = temp_db.save_vote(name, ratings)
            assert vote_id > 0

            # Verify name is stored correctly
            votes = temp_db.get_all_votes()
            stored_vote = next(v for v in votes if v["id"] == vote_id)
            assert stored_vote["voter_name"] == name

    def test_save_vote_complex_ratings(self, temp_db):
        """Test saving vote with complex ratings structure."""
        voter_name = "Test User"

        # Test various rating scenarios
        test_cases = [
            # All logos with different ratings
            {f"toveco{i}.png": (i % 5) - 2 for i in range(1, 12)},
            # Single logo
            {"toveco1.png": 2},
            # Mixed ratings
            {"toveco1.png": 2, "toveco5.png": -2, "toveco10.png": 0},
        ]

        for ratings in test_cases:
            vote_id = temp_db.save_vote(voter_name, ratings)
            assert vote_id > 0

            # Verify ratings stored correctly
            votes = temp_db.get_all_votes()
            stored_vote = next(v for v in votes if v["id"] == vote_id)
            assert stored_vote["ratings"] == ratings

    def test_ratings_json_serialization(self, temp_db):
        """Test that ratings are properly serialized/deserialized."""
        voter_name = "JSON Test User"

        # Test various data types in ratings
        complex_ratings = {
            "toveco1.png": 2,
            "toveco2.png": -1,
            "toveco3.png": 0,
        }

        vote_id = temp_db.save_vote(voter_name, complex_ratings)

        # Retrieve and verify
        votes = temp_db.get_all_votes()
        stored_vote = next(v for v in votes if v["id"] == vote_id)

        assert stored_vote["ratings"] == complex_ratings
        assert isinstance(stored_vote["ratings"]["toveco1.png"], int)


class TestConcurrentAccess:
    """Test concurrent database access and thread safety."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db_path = f.name

        try:
            db_manager = DatabaseManager(temp_db_path)
            yield db_manager
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_concurrent_vote_submissions(self, temp_db):
        """Test multiple threads submitting votes simultaneously."""

        def submit_vote(thread_id):
            voter_name = f"Concurrent User {thread_id}"
            ratings = {f"toveco{(thread_id % 11) + 1}.png": 1}
            return temp_db.save_vote(voter_name, ratings)

        # Submit votes from multiple threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(submit_vote, i) for i in range(10)]
            vote_ids = [future.result() for future in futures]

        # Verify all votes were saved
        assert len(vote_ids) == 10
        assert len(set(vote_ids)) == 10  # All IDs should be unique

        # Verify count
        assert temp_db.get_vote_count() == 10

    def test_concurrent_read_write(self, temp_db):
        """Test concurrent reads and writes."""
        # Pre-populate with some votes
        for i in range(5):
            temp_db.save_vote(f"Initial User {i}", {"toveco1.png": 1})

        results = []

        def write_votes():
            for i in range(5):
                vote_id = temp_db.save_vote(f"Writer User {i}", {"toveco2.png": 1})
                results.append(("write", vote_id))

        def read_votes():
            for _i in range(3):
                count = temp_db.get_vote_count()
                results.append(("read", count))
                time.sleep(0.1)

        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=2) as executor:
            write_future = executor.submit(write_votes)
            read_future = executor.submit(read_votes)

            write_future.result()
            read_future.result()

        # Verify final state
        final_count = temp_db.get_vote_count()
        assert final_count == 10  # 5 initial + 5 from writer

    def test_database_locking(self, temp_db):
        """Test that database properly handles locking."""

        def long_transaction():
            # Simulate a longer database operation
            temp_db.save_vote("Long Transaction User", {"toveco1.png": 2})
            time.sleep(0.2)
            return temp_db.get_vote_count()

        def quick_transaction():
            return temp_db.save_vote("Quick Transaction User", {"toveco2.png": 1})

        # Run operations concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            long_future = executor.submit(long_transaction)
            quick_future = executor.submit(quick_transaction)

            long_result = long_future.result()
            quick_result = quick_future.result()

        # Both should succeed
        assert long_result >= 1
        assert quick_result > 0


class TestDataIntegrity:
    """Test data integrity and corruption prevention."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db_path = f.name

        try:
            db_manager = DatabaseManager(temp_db_path)
            yield db_manager, temp_db_path
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_transaction_rollback_on_error(self, temp_db):
        """Test that transactions rollback on errors."""
        db_manager, db_path = temp_db

        # Save initial vote
        db_manager.save_vote("Initial User", {"toveco1.png": 1})
        initial_count = db_manager.get_vote_count()

        # Simulate a transaction that should fail
        with pytest.raises(DatabaseError):
            # Force an error by corrupting the session
            with db_manager.get_session() as session:
                # Add a vote
                vote_record = VoteRecord(
                    voter_name="Error User", ratings=json.dumps({"toveco1.png": 1})
                )
                session.add(vote_record)
                session.flush()

                # Force an error
                raise DatabaseError("Simulated error")

        # Count should remain the same (transaction rolled back)
        final_count = db_manager.get_vote_count()
        assert final_count == initial_count

    def test_database_integrity_after_interruption(self, temp_db):
        """Test database integrity after simulated interruption."""
        db_manager, db_path = temp_db

        # Add some votes
        for i in range(5):
            db_manager.save_vote(f"User {i}", {"toveco1.png": i - 2})

        # Verify integrity
        votes = db_manager.get_all_votes()
        assert len(votes) == 5

        # Simulate database reopening (as after interruption)
        new_db_manager = DatabaseManager(db_path)

        # Verify data is still intact
        recovered_votes = new_db_manager.get_all_votes()
        assert len(recovered_votes) == 5

        # Verify we can still add new votes
        new_vote_id = new_db_manager.save_vote("Recovery User", {"toveco2.png": 1})
        assert new_vote_id > 0
        assert new_db_manager.get_vote_count() == 6

    def test_malformed_json_handling(self, temp_db):
        """Test handling of malformed JSON in database."""
        db_manager, db_path = temp_db

        # Manually insert malformed JSON to test recovery
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO votes (voter_name, timestamp, ratings)
                VALUES (?, datetime('now'), ?)
            """,
                ("Malformed User", "invalid json"),
            )
            conn.commit()
        finally:
            conn.close()

        # Database should handle this gracefully
        try:
            db_manager.get_all_votes()
            # Should either skip the malformed record or raise an exception
        except (DatabaseError, json.JSONDecodeError):
            # Expected behavior for malformed data
            pass

    def test_database_size_limits(self, temp_db):
        """Test database behavior with large amounts of data."""
        db_manager, db_path = temp_db

        # Add many votes to test size limits
        large_ratings = {f"toveco{i}.png": 1 for i in range(1, 12)}

        # Add 100 votes with full rating data
        vote_ids = []
        for i in range(100):
            vote_id = db_manager.save_vote(f"Bulk User {i}", large_ratings)
            vote_ids.append(vote_id)

        # Verify all votes were saved
        assert len(vote_ids) == 100
        assert db_manager.get_vote_count() == 100

        # Verify database file size is reasonable
        file_size = os.path.getsize(db_path)
        # Should be less than 10MB for 100 votes
        assert file_size < 10 * 1024 * 1024


class TestResultsCalculation:
    """Test mathematical accuracy of results calculation."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db_path = f.name

        try:
            db_manager = DatabaseManager(temp_db_path)
            yield db_manager
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_results_calculation_accuracy(self, temp_db):
        """Test mathematical accuracy of results calculation."""
        # Add votes with known values for verification
        test_votes = [
            ("User1", {"logo1.png": 2, "logo2.png": -1, "logo3.png": 0}),
            ("User2", {"logo1.png": 1, "logo2.png": 1, "logo3.png": -2}),
            ("User3", {"logo1.png": -1, "logo2.png": 0, "logo3.png": 2}),
        ]

        for voter_name, ratings in test_votes:
            temp_db.save_vote(voter_name, ratings)

        results = temp_db.calculate_results()

        # Verify overall structure
        assert results["total_voters"] == 3

        # Verify logo1.png: (2 + 1 + (-1)) / 3 = 2/3 ≈ 0.67
        logo1_stats = results["summary"]["logo1.png"]
        assert logo1_stats["total_votes"] == 3
        assert logo1_stats["total_score"] == 2
        assert abs(logo1_stats["average"] - 0.67) < 0.01

        # Verify logo2.png: (-1 + 1 + 0) / 3 = 0/3 = 0.0
        logo2_stats = results["summary"]["logo2.png"]
        assert logo2_stats["total_votes"] == 3
        assert logo2_stats["total_score"] == 0
        assert logo2_stats["average"] == 0.0

        # Verify logo3.png: (0 + (-2) + 2) / 3 = 0/3 = 0.0
        logo3_stats = results["summary"]["logo3.png"]
        assert logo3_stats["total_votes"] == 3
        assert logo3_stats["total_score"] == 0
        assert logo3_stats["average"] == 0.0

    def test_ranking_algorithm(self, temp_db):
        """Test ranking algorithm correctness."""
        # Create votes with clear ranking order
        temp_db.save_vote(
            "Ranker",
            {
                "best.png": 2,  # Should rank 1st
                "good.png": 1,  # Should rank 2nd
                "neutral.png": 0,  # Should rank 3rd
                "bad.png": -1,  # Should rank 4th
                "worst.png": -2,  # Should rank 5th
            },
        )

        results = temp_db.calculate_results()
        summary = results["summary"]

        # Verify rankings
        assert summary["best.png"]["ranking"] == 1
        assert summary["good.png"]["ranking"] == 2
        assert summary["neutral.png"]["ranking"] == 3
        assert summary["bad.png"]["ranking"] == 4
        assert summary["worst.png"]["ranking"] == 5

    def test_tied_rankings(self, temp_db):
        """Test ranking behavior with tied scores."""
        # Create votes with tied averages
        temp_db.save_vote("User1", {"logo1.png": 1, "logo2.png": 1})
        temp_db.save_vote("User2", {"logo1.png": 1, "logo2.png": 1})

        results = temp_db.calculate_results()
        summary = results["summary"]

        # Both should have same average
        assert summary["logo1.png"]["average"] == 1.0
        assert summary["logo2.png"]["average"] == 1.0

        # Rankings should be assigned consistently
        rankings = [summary["logo1.png"]["ranking"], summary["logo2.png"]["ranking"]]
        rankings.sort()
        assert rankings == [1, 2]  # One should be 1, other should be 2

    def test_results_with_missing_logos(self, temp_db):
        """Test results calculation when some logos have no votes."""
        # Only vote for some logos
        temp_db.save_vote("Partial User", {"logo1.png": 2, "logo3.png": -1})

        results = temp_db.calculate_results()
        summary = results["summary"]

        # Only voted logos should appear in results
        assert "logo1.png" in summary
        assert "logo3.png" in summary
        assert "logo2.png" not in summary

    def test_large_scale_calculation(self, temp_db):
        """Test results calculation with large number of votes."""
        # Generate many votes
        import random

        logos = [f"logo{i}.png" for i in range(1, 12)]

        for i in range(100):
            ratings = {logo: random.randint(-2, 2) for logo in logos}
            temp_db.save_vote(f"User {i}", ratings)

        # Calculate results
        start_time = time.time()
        results = temp_db.calculate_results()
        calc_time = time.time() - start_time

        # Should complete in reasonable time (< 1 second)
        assert calc_time < 1.0

        # Verify structure
        assert results["total_voters"] == 100
        assert len(results["summary"]) == 11

        # All logos should have 100 votes each
        for logo_stats in results["summary"].values():
            assert logo_stats["total_votes"] == 100


class TestErrorHandling:
    """Test database error handling scenarios."""

    def test_invalid_database_path(self):
        """Test handling of invalid database paths."""
        with pytest.raises((DatabaseError, OSError)):
            DatabaseManager("/invalid/path/database.db")

    def test_readonly_database_path(self):
        """Test handling of read-only database paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory structure
            readonly_dir = os.path.join(temp_dir, "readonly")
            os.makedirs(readonly_dir)

            # Make directory read-only
            os.chmod(readonly_dir, 0o444)

            try:
                with pytest.raises((DatabaseError, OSError, PermissionError)):
                    DatabaseManager(os.path.join(readonly_dir, "test.db"))
            finally:
                # Restore permissions for cleanup
                os.chmod(readonly_dir, 0o755)

    def test_corrupted_database_recovery(self):
        """Test recovery from corrupted database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db_path = f.name

        try:
            # Create initial database
            db_manager = DatabaseManager(temp_db_path)
            db_manager.save_vote("Test User", {"logo1.png": 1})

            # Corrupt the database file
            with open(temp_db_path, "wb") as f:
                f.write(b"corrupted data")

            # Try to create new manager with corrupted file
            with pytest.raises(DatabaseError):
                corrupted_db = DatabaseManager(temp_db_path)
                corrupted_db.health_check()

        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
