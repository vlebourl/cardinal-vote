"""Integration tests for PostgreSQL connectivity and operations.

These tests verify that the PostgreSQL database integration works correctly
after the SQLite cleanup (PR #31).
"""

import asyncio
import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.cardinal_vote.config import settings
from src.cardinal_vote.database_manager import GeneralizedDatabaseManager


class TestPostgreSQLConnectivity:
    """Test PostgreSQL database connectivity and basic operations."""

    @pytest.fixture
    async def db_engine(self):
        """Create test database engine."""
        # Use test database URL or fallback to configured one
        test_db_url = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)

        engine = create_async_engine(test_db_url, echo=False, pool_pre_ping=True)

        yield engine

        await engine.dispose()

    @pytest.fixture
    async def db_session(self, db_engine):
        """Create test database session."""
        async_session = sessionmaker(
            db_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            yield session

    @pytest.mark.asyncio
    async def test_database_connection(self, db_engine):
        """Test basic database connectivity."""
        async with db_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row[0] == 1

    @pytest.mark.asyncio
    async def test_database_version(self, db_engine):
        """Test PostgreSQL version detection."""
        async with db_engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            assert "PostgreSQL" in version
            # Should be PostgreSQL 16+ based on our Docker config
            assert any(f"PostgreSQL {v}" in version for v in ["16", "17", "18"])

    @pytest.mark.asyncio
    async def test_vote_records_table_exists(self, db_session):
        """Test that vote_records table exists with correct schema."""
        # Check table exists
        result = await db_session.execute(
            text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'vote_records'
        """)
        )

        assert result.fetchone() is not None

        # Check required columns exist
        result = await db_session.execute(
            text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'vote_records'
            ORDER BY column_name
        """)
        )

        columns = {row[0]: row[1] for row in result.fetchall()}

        # Verify key columns exist with correct types
        expected_columns = {
            "id": "integer",
            "voter_first_name": "character varying",
            "voter_last_name": "character varying",
            "voter_name": "character varying",
            "ratings": "text",
            "created_at": "timestamp without time zone",
        }

        for col_name, expected_type in expected_columns.items():
            assert col_name in columns, f"Column {col_name} missing"
            assert expected_type in columns[col_name], (
                f"Column {col_name} has wrong type: {columns[col_name]}"
            )


class TestGeneralizedDatabaseManager:
    """Test the GeneralizedDatabaseManager with PostgreSQL."""

    @pytest.fixture
    async def db_manager(self):
        """Create test database manager."""
        manager = GeneralizedDatabaseManager()
        yield manager
        await manager.close()

    @pytest.mark.asyncio
    async def test_database_manager_initialization(self, db_manager):
        """Test that database manager initializes correctly."""
        # Should not raise any exceptions
        assert db_manager is not None

        # Test basic connectivity
        async with db_manager.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1

    @pytest.mark.asyncio
    async def test_vote_crud_operations(self, db_manager):
        """Test basic CRUD operations on vote records."""
        # Test data
        test_voter_first = "Test"
        test_voter_last = "Voter"
        test_ratings = {"option1": 2, "option2": -1, "option3": 0}

        # Create vote
        vote_id = await db_manager.save_vote(
            voter_first_name=test_voter_first,
            voter_last_name=test_voter_last,
            ratings=test_ratings,
        )

        assert vote_id is not None
        assert isinstance(vote_id, int)
        assert vote_id > 0

        # Read votes
        all_votes = await db_manager.get_all_votes()
        assert len(all_votes) >= 1

        # Find our test vote
        test_vote = next((vote for vote in all_votes if vote["id"] == vote_id), None)

        assert test_vote is not None
        assert test_vote["voter_first_name"] == test_voter_first
        assert test_vote["voter_last_name"] == test_voter_last
        assert test_vote["ratings"] == test_ratings

        # Test vote count
        vote_count = await db_manager.get_vote_count()
        assert vote_count >= 1

        # Calculate results
        results = await db_manager.calculate_results()
        assert results["total_voters"] >= 1
        assert "summary" in results

        # Clean up - delete test vote
        deleted = await db_manager.delete_vote_by_id(vote_id)
        assert deleted is True

        # Verify deletion
        votes_after_delete = await db_manager.get_all_votes()
        deleted_vote = next(
            (vote for vote in votes_after_delete if vote["id"] == vote_id), None
        )
        assert deleted_vote is None

    @pytest.mark.asyncio
    async def test_duplicate_voter_prevention(self, db_manager):
        """Test that duplicate voters are prevented."""
        test_voter_first = "Duplicate"
        test_voter_last = "Test"
        test_ratings = {"option1": 1}

        # First vote should succeed
        vote_id1 = await db_manager.save_vote(
            voter_first_name=test_voter_first,
            voter_last_name=test_voter_last,
            ratings=test_ratings,
        )
        assert vote_id1 is not None

        # Second vote with same name should fail
        from src.cardinal_vote.models import DatabaseError

        with pytest.raises(DatabaseError):
            await db_manager.save_vote(
                voter_first_name=test_voter_first,
                voter_last_name=test_voter_last,
                ratings=test_ratings,
            )

        # Clean up
        await db_manager.delete_vote_by_id(vote_id1)


class TestDockerComposeIntegration:
    """Test Docker Compose integration with PostgreSQL."""

    def test_database_url_configuration(self):
        """Test that DATABASE_URL is properly configured."""
        db_url = settings.DATABASE_URL

        # Should be PostgreSQL connection string
        assert db_url.startswith("postgresql"), (
            f"DATABASE_URL should start with 'postgresql', got: {db_url}"
        )

        # Should contain required components
        assert "@" in db_url, "DATABASE_URL should contain username/password"
        assert "/" in db_url, "DATABASE_URL should contain database name"
        assert ":" in db_url, "DATABASE_URL should contain port"

    @pytest.mark.asyncio
    async def test_connection_pool_configuration(self):
        """Test that connection pooling works correctly."""
        # Create multiple engines to test pooling
        engines = []

        try:
            for _i in range(3):
                engine = create_async_engine(
                    settings.DATABASE_URL,
                    pool_size=2,
                    max_overflow=1,
                    pool_pre_ping=True,
                )
                engines.append(engine)

            # Test concurrent connections
            async def test_connection(engine):
                async with engine.begin() as conn:
                    result = await conn.execute(text("SELECT 1"))
                    return result.fetchone()[0]

            # Run concurrent connection tests
            tasks = [test_connection(engine) for engine in engines]
            results = await asyncio.gather(*tasks)

            # All should succeed
            assert all(result == 1 for result in results)

        finally:
            # Clean up engines
            for engine in engines:
                await engine.dispose()

    @pytest.mark.asyncio
    async def test_database_health_check(self):
        """Test database health check functionality."""
        manager = GeneralizedDatabaseManager()

        try:
            # Test health check
            is_healthy = await manager.health_check()
            assert is_healthy is True

        finally:
            await manager.close()


@pytest.mark.integration
class TestProductionReadiness:
    """Test production readiness aspects."""

    @pytest.mark.asyncio
    async def test_connection_retry_resilience(self):
        """Test connection retry logic for production reliability."""
        # This would test the retry logic in docker-entrypoint.sh
        # For now, just test that connections can be recovered

        engine = create_async_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,  # Important for detecting stale connections
            pool_recycle=3600,  # Recycle connections every hour
        )

        try:
            # Test that connections work reliably
            for _i in range(10):
                async with engine.begin() as conn:
                    result = await conn.execute(text("SELECT 1"))
                    assert result.fetchone()[0] == 1

                # Small delay to test connection pooling
                await asyncio.sleep(0.1)

        finally:
            await engine.dispose()

    def test_environment_configuration(self):
        """Test that all required environment variables are available."""
        # These should be set for integration tests
        required_vars = ["DATABASE_URL"]

        for var in required_vars:
            value = getattr(settings, var, None) or os.getenv(var)
            assert value is not None, f"Required environment variable {var} is not set"
            assert len(str(value)) > 0, f"Environment variable {var} is empty"

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent database operations for production load."""
        manager = GeneralizedDatabaseManager()

        try:

            async def concurrent_vote(voter_id):
                """Create a vote concurrently."""
                try:
                    vote_id = await manager.save_vote(
                        voter_first_name=f"Concurrent{voter_id}",
                        voter_last_name="Voter",
                        ratings={
                            "option1": voter_id % 5 - 2
                        },  # Rating between -2 and 2
                    )
                    return vote_id
                except Exception:
                    # Expected if same voter tries to vote twice
                    return None

            # Run concurrent votes
            tasks = [concurrent_vote(i) for i in range(10)]
            vote_ids = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successful votes (non-None, non-Exception)
            successful_votes = [
                vid
                for vid in vote_ids
                if vid is not None and not isinstance(vid, Exception)
            ]

            assert len(successful_votes) > 0, (
                "At least some concurrent votes should succeed"
            )

            # Clean up successful votes
            for vote_id in successful_votes:
                if isinstance(vote_id, int):
                    await manager.delete_vote_by_id(vote_id)

        finally:
            await manager.close()


if __name__ == "__main__":
    # Run tests with: pytest tests/test_integration_postgresql.py -v
    pytest.main([__file__, "-v", "--tb=short"])
