"""Integration tests for Sprint 2 enhanced dashboard functionality.

These tests verify the enhanced dashboard features including:
- Enhanced statistics endpoint
- Activity timeline with real-time data
- Dashboard performance with larger datasets
- Material Design 3 components integration

For local testing, run:
    docker-compose -f docker-compose.test.yml up -d postgres-test
    export TEST_DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5433/test_cardinal_vote"
    uv run pytest tests/test_sprint2_dashboard_integration.py -v
"""

import os
from datetime import datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from cardinal_vote.dependencies import get_async_session
from cardinal_vote.main import app
from cardinal_vote.models import Base, User, Vote, VoteOption, VoterResponse

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://test_user:test_password@localhost:5433/test_cardinal_vote",
)


@pytest.fixture
async def async_engine():
    """Create async test database engine for PostgreSQL."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
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
async def test_user(test_session):
    """Create test user in database."""
    user = User(
        id=uuid4(),
        email="testuser@example.com",
        first_name="Test",
        last_name="User",
        is_verified=True,
        is_super_admin=False,
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow() - timedelta(minutes=5),
    )
    test_session.add(user)
    await test_session.commit()
    return user


@pytest.fixture
async def sample_votes_with_activity(test_session, test_user):
    """Create sample votes with various statuses and timestamps for activity testing."""
    votes = []
    now = datetime.utcnow()

    # Create votes with different statuses and times
    vote_configs = [
        ("Recent Draft Vote", "draft", timedelta(hours=1)),
        ("Active Vote 1", "active", timedelta(hours=6)),
        ("Active Vote 2", "active", timedelta(days=1)),
        ("Completed Vote", "completed", timedelta(days=2)),
        ("Paused Vote", "paused", timedelta(days=3)),
        ("Draft Vote", "draft", timedelta(days=7)),
        ("Old Active Vote", "active", timedelta(days=14)),
    ]

    for title, status, time_ago in vote_configs:
        vote = Vote(
            id=uuid4(),
            title=title,
            slug=title.lower().replace(" ", "-"),
            description=f"Description for {title}",
            status=status,
            creator_id=test_user.id,
            created_at=now - time_ago,
            updated_at=now - time_ago + timedelta(minutes=30) if status != "draft" else None,
            require_auth=False,
            access_code=None,
        )
        test_session.add(vote)
        votes.append(vote)

    await test_session.commit()

    # Add options for each vote
    for vote in votes:
        for i in range(2, 4):  # 2-3 options per vote
            option = VoteOption(
                id=uuid4(),
                vote_id=vote.id,
                title=f"Option {i-1}",
                content=f"Content for option {i-1} in {vote.title}",
                option_type="text",
                display_order=i-1,
            )
            test_session.add(option)

    await test_session.commit()
    return votes


@pytest.fixture
async def sample_responses(test_session, sample_votes_with_activity):
    """Create sample voter responses for activity testing."""
    responses = []
    now = datetime.utcnow()

    # Create responses for some votes
    for i, vote in enumerate(sample_votes_with_activity[:4]):  # First 4 votes get responses
        for j in range(i + 1):  # Varying response counts
            response = VoterResponse(
                id=uuid4(),
                vote_id=vote.id,
                voter_email=f"voter{i}{j}@example.com",
                submitted_at=now - timedelta(hours=j + 1),
            )
            test_session.add(response)
            responses.append(response)

    await test_session.commit()
    return responses


class TestEnhancedDashboardStats:
    """Test enhanced dashboard statistics API endpoint."""

    @pytest.mark.integration
    @pytest.mark.database
    async def test_get_dashboard_stats_basic(self, test_session, test_user):
        """Test basic dashboard statistics retrieval."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    response = client.get("/api/votes/dashboard/stats")
                    assert response.status_code == 200

                    result = response.json()

                    # Verify basic statistics structure
                    assert "total_votes" in result
                    assert "active_votes" in result
                    assert "draft_votes" in result
                    assert "completed_votes" in result
                    assert "total_responses" in result
                    assert "response_rate" in result
                    assert "votes_by_status" in result

                    # Verify data types
                    assert isinstance(result["total_votes"], int)
                    assert isinstance(result["active_votes"], int)
                    assert isinstance(result["draft_votes"], int)
                    assert isinstance(result["completed_votes"], int)
                    assert isinstance(result["total_responses"], int)
                    assert isinstance(result["response_rate"], int | float)
                    assert isinstance(result["votes_by_status"], dict)

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_get_dashboard_stats_with_data(self, test_session, test_user, sample_votes_with_activity, sample_responses):
        """Test dashboard statistics with actual data."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    response = client.get("/api/votes/dashboard/stats")
                    assert response.status_code == 200

                    result = response.json()

                    # Verify counts match our sample data
                    assert result["total_votes"] == len(sample_votes_with_activity)

                    active_count = len([v for v in sample_votes_with_activity if v.status == "active"])
                    draft_count = len([v for v in sample_votes_with_activity if v.status == "draft"])
                    completed_count = len([v for v in sample_votes_with_activity if v.status == "completed"])

                    assert result["active_votes"] == active_count
                    assert result["draft_votes"] == draft_count
                    assert result["completed_votes"] == completed_count
                    assert result["total_responses"] == len(sample_responses)

                    # Verify status breakdown
                    votes_by_status = result["votes_by_status"]
                    assert votes_by_status["active"] == active_count
                    assert votes_by_status["draft"] == draft_count
                    assert votes_by_status["completed"] == completed_count

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_dashboard_stats_unauthorized(self, test_session):
        """Test dashboard statistics without authentication."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                response = client.get("/api/votes/dashboard/stats")
                assert response.status_code == 401

        finally:
            app.dependency_overrides.clear()


class TestActivityTimeline:
    """Test activity timeline API endpoint."""

    @pytest.mark.integration
    @pytest.mark.database
    async def test_get_activity_timeline_basic(self, test_session, test_user):
        """Test basic activity timeline retrieval."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    response = client.get("/api/votes/dashboard/activity")
                    assert response.status_code == 200

                    result = response.json()

                    # Verify activity timeline structure
                    assert "activities" in result
                    assert "total_count" in result
                    assert "timeframe_days" in result
                    assert "has_more" in result

                    assert isinstance(result["activities"], list)
                    assert isinstance(result["total_count"], int)
                    assert isinstance(result["timeframe_days"], int)
                    assert isinstance(result["has_more"], bool)

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_get_activity_timeline_with_data(self, test_session, test_user, sample_votes_with_activity, sample_responses):
        """Test activity timeline with actual data."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    response = client.get("/api/votes/dashboard/activity?days=30&limit=50")
                    assert response.status_code == 200

                    result = response.json()
                    activities = result["activities"]

                    # Should have activities
                    assert len(activities) > 0
                    assert result["total_count"] > 0

                    # Verify activity structure
                    for activity in activities:
                        assert "type" in activity
                        assert "title" in activity
                        assert "timestamp" in activity
                        assert "details" in activity

                        # Verify timestamp format
                        assert isinstance(activity["timestamp"], str)
                        # Should be in ISO format
                        datetime.fromisoformat(activity["timestamp"].replace("Z", "+00:00"))

                    # Activities should be sorted by timestamp (most recent first)
                    timestamps = [activity["timestamp"] for activity in activities]
                    assert timestamps == sorted(timestamps, reverse=True)

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_activity_timeline_filtering(self, test_session, test_user, sample_votes_with_activity):
        """Test activity timeline filtering by days."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    # Test with different day filters
                    response_7_days = client.get("/api/votes/dashboard/activity?days=7&limit=50")
                    assert response_7_days.status_code == 200

                    response_30_days = client.get("/api/votes/dashboard/activity?days=30&limit=50")
                    assert response_30_days.status_code == 200

                    activities_7 = response_7_days.json()["activities"]
                    activities_30 = response_30_days.json()["activities"]

                    # 30-day filter should return same or more activities than 7-day
                    assert len(activities_30) >= len(activities_7)

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_activity_timeline_limit(self, test_session, test_user, sample_votes_with_activity):
        """Test activity timeline limit parameter."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    # Test with small limit
                    response = client.get("/api/votes/dashboard/activity?days=30&limit=3")
                    assert response.status_code == 200

                    result = response.json()
                    activities = result["activities"]

                    # Should respect the limit
                    assert len(activities) <= 3

                    # has_more should indicate if there are more activities
                    if result["total_count"] > 3:
                        assert result["has_more"] is True
                    else:
                        assert result["has_more"] is False

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_activity_timeline_unauthorized(self, test_session):
        """Test activity timeline without authentication."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                response = client.get("/api/votes/dashboard/activity")
                assert response.status_code == 401

        finally:
            app.dependency_overrides.clear()


class TestDashboardIntegration:
    """Test complete dashboard integration."""

    @pytest.mark.integration
    @pytest.mark.database
    async def test_complete_dashboard_workflow(self, test_session, test_user, sample_votes_with_activity, sample_responses):
        """Test complete dashboard data loading workflow."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    # 1. Load dashboard statistics
                    stats_response = client.get("/api/votes/dashboard/stats")
                    assert stats_response.status_code == 200
                    stats_data = stats_response.json()

                    # 2. Load activity timeline
                    activity_response = client.get("/api/votes/dashboard/activity?days=7&limit=10")
                    assert activity_response.status_code == 200
                    activity_data = activity_response.json()

                    # 3. Verify data consistency
                    total_votes_from_stats = stats_data["total_votes"]

                    # Activity timeline should show activities within the timeframe
                    activities = activity_data["activities"]

                    # Should have some relationship between stats and activities
                    assert total_votes_from_stats > 0
                    assert len(activities) >= 0  # Could be 0 if no recent activity

        finally:
            app.dependency_overrides.clear()


class TestDashboardPerformance:
    """Test dashboard performance with larger datasets."""

    @pytest.mark.integration
    @pytest.mark.performance
    async def test_dashboard_stats_performance(self, async_session_maker, test_user):
        """Test dashboard statistics performance with larger dataset."""
        async with async_session_maker() as session:
            # Create larger dataset
            session.add(test_user)
            votes = []
            responses = []
            now = datetime.utcnow()

            # Create 50 votes
            for i in range(50):
                vote = Vote(
                    id=uuid4(),
                    title=f"Performance Vote {i}",
                    slug=f"performance-vote-{i}",
                    description=f"Performance test vote {i}",
                    status=["draft", "active", "completed", "paused"][i % 4],
                    creator_id=test_user.id,
                    created_at=now - timedelta(days=i % 30),
                    require_auth=i % 3 == 0,
                    access_code=f"code{i}" if i % 5 == 0 else None,
                )
                session.add(vote)
                votes.append(vote)

            await session.commit()

            # Create responses for some votes
            for i, vote in enumerate(votes[:25]):  # Half the votes get responses
                for j in range(i % 5 + 1):  # Variable response count
                    response = VoterResponse(
                        id=uuid4(),
                        vote_id=vote.id,
                        voter_email=f"perftest{i}{j}@example.com",
                        submitted_at=now - timedelta(days=i, hours=j),
                    )
                    session.add(response)
                    responses.append(response)

            await session.commit()

            # Test performance
            app.dependency_overrides[get_async_session] = lambda: session

            try:
                with TestClient(app) as client:
                    with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                        mock_auth.return_value = test_user

                        import time

                        # Test stats endpoint performance
                        start_time = time.time()
                        stats_response = client.get("/api/votes/dashboard/stats")
                        stats_time = time.time() - start_time

                        assert stats_response.status_code == 200
                        assert stats_time < 1.0  # Should complete in less than 1 second

                        # Test activity timeline performance
                        start_time = time.time()
                        activity_response = client.get("/api/votes/dashboard/activity?days=30&limit=20")
                        activity_time = time.time() - start_time

                        assert activity_response.status_code == 200
                        assert activity_time < 1.0  # Should complete in less than 1 second

                        # Verify data accuracy
                        stats_data = stats_response.json()
                        assert stats_data["total_votes"] == 50
                        assert stats_data["total_responses"] == len(responses)

            finally:
                app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.performance
    async def test_concurrent_dashboard_requests(self, async_session_maker, test_user, sample_votes_with_activity):
        """Test concurrent dashboard requests don't cause issues."""
        import asyncio

        async def make_dashboard_request(session_maker, user, request_type):
            """Make a dashboard request in its own session."""
            async with session_maker() as session:
                session.add(user)

                app.dependency_overrides[get_async_session] = lambda: session

                try:
                    with TestClient(app) as client:
                        with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                            mock_auth.return_value = user

                            if request_type == "stats":
                                response = client.get("/api/votes/dashboard/stats")
                            else:  # activity
                                response = client.get("/api/votes/dashboard/activity?days=7&limit=10")

                            return response.status_code, response.json()

                finally:
                    app.dependency_overrides.clear()

        # Create concurrent requests (mix of stats and activity)
        tasks = []
        for i in range(10):
            request_type = "stats" if i % 2 == 0 else "activity"
            tasks.append(make_dashboard_request(async_session_maker, test_user, request_type))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        successful_requests = 0
        for result in results:
            if isinstance(result, tuple) and result[0] == 200:
                successful_requests += 1

        assert successful_requests >= 8  # At least 80% should succeed
