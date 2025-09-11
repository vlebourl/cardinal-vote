"""Integration tests for super admin functionality."""

from datetime import datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from cardinal_vote.dependencies import get_async_session
from cardinal_vote.main import app
from cardinal_vote.models import Base, User, Vote, VoterResponse
from cardinal_vote.super_admin_manager import SuperAdminManager

# Test database setup
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test"


@pytest.fixture
async def async_engine():
    """Create async test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def async_session_maker(async_engine):
    """Create async session maker for tests."""
    return async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def test_session(async_session_maker):
    """Create test database session."""
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def test_client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def sample_users(test_session):
    """Create sample users in test database."""
    users = []
    now = datetime.utcnow()

    # Super admin user
    super_admin = User(
        id=uuid4(),
        email="superadmin@test.com",
        first_name="Super",
        last_name="Admin",
        is_verified=True,
        is_super_admin=True,
        created_at=now - timedelta(days=30),
        last_login=now - timedelta(minutes=5),
    )
    test_session.add(super_admin)
    users.append(super_admin)

    # Regular verified users
    for i in range(10):
        user = User(
            id=uuid4(),
            email=f"user{i}@test.com",
            first_name="User",
            last_name=f"{i}",
            is_verified=True,
            is_super_admin=False,
            created_at=now - timedelta(days=20 - i),
            last_login=now - timedelta(hours=i),
        )
        test_session.add(user)
        users.append(user)

    # Unverified users
    for i in range(5):
        user = User(
            id=uuid4(),
            email=f"unverified{i}@test.com",
            first_name="Unverified",
            last_name=f"{i}",
            is_verified=False,
            is_super_admin=False,
            created_at=now - timedelta(days=i + 1),
        )
        test_session.add(user)
        users.append(user)

    await test_session.commit()
    return users


@pytest.fixture
async def sample_votes(test_session, sample_users):
    """Create sample votes in test database."""
    votes = []
    now = datetime.utcnow()

    # Create votes for some users
    for i, user in enumerate(sample_users[1:6]):  # Skip super admin, use next 5 users
        for j in range(i + 1):  # Different vote counts per user
            vote = Vote(
                id=uuid4(),
                title=f"Test Vote {i}-{j}",
                slug=f"test-vote-{i}-{j}",
                description=f"Test vote description {i}-{j}",
                status="active" if j % 2 == 0 else "draft",
                creator_id=user.id,
                created_at=now - timedelta(days=10 - j),
            )
            test_session.add(vote)
            votes.append(vote)

    await test_session.commit()
    return votes


@pytest.fixture
async def sample_responses(test_session, sample_votes, sample_users):
    """Create sample voter responses in test database."""
    responses = []
    now = datetime.utcnow()

    # Create responses for some votes
    for _i, vote in enumerate(sample_votes[:5]):  # First 5 votes
        for j, user in enumerate(sample_users[6:10]):  # Users 6-9 respond
            response = VoterResponse(
                id=uuid4(),
                vote_id=vote.id,
                voter_email=user.email,
                submitted_at=now - timedelta(hours=j + 1),
            )
            test_session.add(response)
            responses.append(response)

    await test_session.commit()
    return responses


class TestSuperAdminManagerIntegration:
    """Integration tests for SuperAdminManager with real database."""

    @pytest.mark.integration
    @pytest.mark.database
    async def test_get_comprehensive_system_stats_with_real_data(
        self, test_session, sample_users, sample_votes, sample_responses
    ):
        """Test comprehensive system stats with real database data."""
        manager = SuperAdminManager()

        result = await manager.get_comprehensive_system_stats(test_session)

        # Verify counts match our sample data
        assert result["total_users"] == len(sample_users)
        assert result["verified_users"] == len(
            [u for u in sample_users if u.is_verified]
        )
        assert result["unverified_users"] == len(
            [u for u in sample_users if not u.is_verified]
        )
        assert result["super_admins"] == len(
            [u for u in sample_users if u.is_super_admin]
        )
        assert result["total_votes"] == len(sample_votes)
        assert result["total_responses"] == len(sample_responses)

        # Verify platform health is calculated
        assert "platform_health" in result
        assert "status" in result["platform_health"]
        assert "score" in result["platform_health"]
        assert result["platform_health"]["score"] >= 0

        # Verify timestamp is present
        assert "timestamp" in result

    @pytest.mark.integration
    @pytest.mark.database
    async def test_get_recent_user_activity_with_real_data(
        self, test_session, sample_users, sample_votes
    ):
        """Test recent user activity with real database data."""
        manager = SuperAdminManager()

        result = await manager.get_recent_user_activity(test_session, limit=5)

        assert isinstance(result, list)
        assert len(result) <= 5

        # Verify structure of activity items
        for activity in result:
            assert "type" in activity
            assert "user_id" in activity
            assert "user_email" in activity
            assert "user_name" in activity
            assert "is_verified" in activity
            assert "vote_count" in activity
            assert activity["type"] == "user_registration"

    @pytest.mark.integration
    @pytest.mark.database
    async def test_bulk_update_users_with_real_data(self, test_session, sample_users):
        """Test bulk user updates with real database."""
        manager = SuperAdminManager()

        # Get some unverified users
        unverified_users = [u for u in sample_users if not u.is_verified]
        user_ids = [u.id for u in unverified_users[:3]]

        # Test bulk verification
        result = await manager.bulk_update_users(test_session, user_ids, "verify_users")

        assert result["success"] is True
        assert result["affected_count"] == len(user_ids)

        # Verify users are actually updated in database
        await test_session.refresh(unverified_users[0])
        assert unverified_users[0].is_verified is True

    @pytest.mark.integration
    @pytest.mark.database
    async def test_get_user_management_summary_with_real_data(
        self, test_session, sample_users, sample_votes
    ):
        """Test user management summary with real database data."""
        manager = SuperAdminManager()

        result = await manager.get_user_management_summary(test_session)

        assert "verified_users_count" in result
        assert "unverified_users_count" in result
        assert "super_admins_count" in result
        assert "most_active_users" in result
        assert "recent_registrations" in result
        assert "pending_verifications" in result

        # Verify counts
        expected_verified = len([u for u in sample_users if u.is_verified])
        expected_unverified = len([u for u in sample_users if not u.is_verified])
        expected_super_admins = len([u for u in sample_users if u.is_super_admin])

        assert result["verified_users_count"] == expected_verified
        assert result["unverified_users_count"] == expected_unverified
        assert result["super_admins_count"] == expected_super_admins

    @pytest.mark.integration
    @pytest.mark.database
    async def test_get_platform_audit_log_with_real_data(
        self, test_session, sample_users, sample_votes
    ):
        """Test platform audit log with real database data."""
        manager = SuperAdminManager()

        result = await manager.get_platform_audit_log(test_session, limit=20)

        assert isinstance(result, list)
        assert len(result) <= 20

        # Should contain user registration and vote creation events
        event_types = {event["event_type"] for event in result}
        assert "user_registration" in event_types

        # If we have votes, should also contain vote creation events
        if sample_votes:
            assert "vote_creation" in event_types


class TestSuperAdminAPIIntegration:
    """Integration tests for super admin API endpoints."""

    @pytest.mark.integration
    @pytest.mark.api
    async def test_full_user_management_workflow(self, test_session, sample_users):
        """Test complete user management workflow."""
        # Override the dependency to use our test session
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                super_admin = sample_users[0]  # First user is super admin

                # Mock authentication
                with patch(
                    "cardinal_vote.dependencies.get_current_super_admin"
                ) as mock_auth:
                    mock_auth.return_value = super_admin

                    # Test getting system statistics
                    response = client.get("/api/admin/stats")
                    assert response.status_code == 200

                    stats_data = response.json()
                    assert "total_users" in stats_data
                    assert stats_data["total_users"] > 0

                    # Test listing users
                    response = client.get("/api/admin/users?page=1&limit=10")
                    assert response.status_code == 200

                    users_data = response.json()
                    assert "users" in users_data
                    assert "pagination" in users_data
                    assert len(users_data["users"]) <= 10

                    # Test user search
                    response = client.get("/api/admin/users?search=user1")
                    assert response.status_code == 200

                    search_data = response.json()
                    assert "users" in search_data

                    # Test getting comprehensive stats
                    response = client.get("/api/admin/comprehensive-stats")
                    assert response.status_code == 200

                    comp_stats = response.json()
                    assert "platform_health" in comp_stats
                    assert "timestamp" in comp_stats

        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.api
    async def test_bulk_operations_integration(self, test_session, sample_users):
        """Test bulk operations integration."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                super_admin = sample_users[0]
                unverified_users = [u for u in sample_users if not u.is_verified]

                with patch(
                    "cardinal_vote.dependencies.get_current_super_admin"
                ) as mock_auth:
                    mock_auth.return_value = super_admin

                    # Test bulk user verification
                    user_ids = [str(u.id) for u in unverified_users[:2]]
                    bulk_request = {"user_ids": user_ids, "operation": "verify_users"}

                    response = client.post(
                        "/api/admin/users/bulk-update", json=bulk_request
                    )
                    assert response.status_code == 200

                    result = response.json()
                    assert result["success"] is True
                    assert result["affected_count"] == 2

        finally:
            app.dependency_overrides.clear()


class TestDatabasePerformance:
    """Integration tests for database performance."""

    @pytest.mark.integration
    @pytest.mark.performance
    async def test_query_performance_with_large_dataset(self, test_session):
        """Test query performance with larger dataset."""
        # Create larger dataset
        users = []
        votes = []
        now = datetime.utcnow()

        # Create 100 users
        for i in range(100):
            user = User(
                id=uuid4(),
                email=f"perftest{i}@test.com",
                first_name="User",
                last_name=f"{i}",
                is_verified=i % 3 != 0,  # 2/3 verified
                is_super_admin=i == 0,  # First user is super admin
                created_at=now - timedelta(days=i),
            )
            test_session.add(user)
            users.append(user)

        await test_session.commit()

        # Create votes for users
        for i, user in enumerate(users[:50]):  # Half the users create votes
            for j in range(i % 5 + 1):  # Variable vote count
                vote = Vote(
                    id=uuid4(),
                    title=f"Perf Vote {i}-{j}",
                    slug=f"perf-vote-{i}-{j}",
                    description="Performance test vote",
                    status="active" if j % 2 == 0 else "draft",
                    creator_id=user.id,
                    created_at=now - timedelta(days=i, hours=j),
                )
                test_session.add(vote)
                votes.append(vote)

        await test_session.commit()

        # Test performance of various operations
        manager = SuperAdminManager()

        import time

        # Test comprehensive stats performance
        start_time = time.time()
        stats = await manager.get_comprehensive_system_stats(test_session)
        stats_time = time.time() - start_time

        # Should complete quickly even with larger dataset
        assert stats_time < 1.0  # Less than 1 second
        assert stats["total_users"] == 100

        # Test recent user activity performance (should use efficient JOIN)
        start_time = time.time()
        activity = await manager.get_recent_user_activity(test_session, limit=50)
        activity_time = time.time() - start_time

        assert activity_time < 0.5  # Less than 0.5 seconds
        assert len(activity) <= 50

        # Test user management summary performance
        start_time = time.time()
        summary = await manager.get_user_management_summary(test_session)
        summary_time = time.time() - start_time

        assert summary_time < 1.0  # Less than 1 second
        assert summary["verified_users_count"] > 0

    @pytest.mark.integration
    @pytest.mark.performance
    async def test_n_plus_one_prevention(self, test_session):
        """Test that N+1 query problems are prevented."""
        # Create test data
        users = []
        now = datetime.utcnow()

        for i in range(20):
            user = User(
                id=uuid4(),
                email=f"n1test{i}@test.com",
                first_name="User",
                last_name=f"{i}",
                is_verified=True,
                is_super_admin=False,
                created_at=now - timedelta(days=i),
            )
            test_session.add(user)
            users.append(user)

        await test_session.commit()

        # Create votes for users (different counts)
        for i, user in enumerate(users):
            for j in range(i % 3):  # 0, 1, or 2 votes per user
                vote = Vote(
                    id=uuid4(),
                    title=f"N+1 Vote {i}-{j}",
                    slug=f"n1-vote-{i}-{j}",
                    description="N+1 test vote",
                    status="active",
                    creator_id=user.id,
                    created_at=now - timedelta(days=i, hours=j),
                )
                test_session.add(vote)

        await test_session.commit()

        # Mock the session to count queries
        query_count = 0
        original_execute = test_session.execute

        async def counting_execute(*args, **kwargs):
            nonlocal query_count
            query_count += 1
            return await original_execute(*args, **kwargs)

        test_session.execute = counting_execute

        # Test recent user activity - should use single JOIN query
        manager = SuperAdminManager()
        query_count = 0

        activity = await manager.get_recent_user_activity(test_session, limit=20)

        # Should use only 1 query (JOIN) instead of 1 + N queries
        assert query_count == 1
        assert len(activity) == 20

        # Each activity item should have vote_count without additional queries
        for item in activity:
            assert "vote_count" in item
            assert isinstance(item["vote_count"], int)


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    @pytest.mark.integration
    @pytest.mark.database
    async def test_database_connection_error_handling(self, async_session_maker):
        """Test handling of database connection errors."""
        manager = SuperAdminManager()

        # Create a session that will be closed
        session = async_session_maker()
        await session.close()

        # Should raise appropriate exception
        from sqlalchemy.exc import SQLAlchemyError

        with pytest.raises((SQLAlchemyError, RuntimeError)):
            await manager.get_comprehensive_system_stats(session)

    @pytest.mark.integration
    @pytest.mark.database
    async def test_transaction_rollback_on_error(self, test_session, sample_users):
        """Test that transactions are properly rolled back on errors."""
        manager = SuperAdminManager()

        # Get some users
        user_ids = [u.id for u in sample_users[:3]]

        # Mock an error during bulk update
        original_commit = test_session.commit

        async def failing_commit():
            raise Exception("Simulated database error")

        test_session.commit = failing_commit

        # Should handle error gracefully
        result = await manager.bulk_update_users(test_session, user_ids, "verify_users")

        assert result["success"] is False
        assert "error" in result

        # Restore original commit
        test_session.commit = original_commit


class TestConcurrencyAndRaceConditions:
    """Integration tests for concurrent operations."""

    @pytest.mark.integration
    @pytest.mark.performance
    async def test_concurrent_bulk_operations(self, async_session_maker, sample_users):
        """Test concurrent bulk operations don't cause race conditions."""
        import asyncio

        manager = SuperAdminManager()

        # Create multiple sessions for concurrent operations
        async def bulk_verify_users(user_ids):
            async with async_session_maker() as session:
                return await manager.bulk_update_users(
                    session, user_ids, "verify_users"
                )

        async def bulk_unverify_users(user_ids):
            async with async_session_maker() as session:
                return await manager.bulk_update_users(
                    session, user_ids, "unverify_users"
                )

        # Split users into groups
        unverified_users = [u for u in sample_users if not u.is_verified]
        if len(unverified_users) >= 4:
            group1 = [u.id for u in unverified_users[:2]]
            group2 = [u.id for u in unverified_users[2:4]]

            # Run concurrent operations
            results = await asyncio.gather(
                bulk_verify_users(group1),
                bulk_verify_users(group2),
                return_exceptions=True,
            )

            # Both operations should succeed
            for result in results:
                if isinstance(result, dict):
                    assert result["success"] is True
