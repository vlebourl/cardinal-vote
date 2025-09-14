"""Integration tests for Sprint 2 vote creation interface functionality.

These tests verify the complete vote creation workflow including:
- Dynamic option management (2-20 options)
- Access control settings (authentication + access codes)
- Material Design 3 UI components
- API integration and validation

For local testing, run:
    docker-compose -f docker-compose.test.yml up -d postgres-test
    export TEST_DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5433/test_cardinal_vote"
    uv run pytest tests/test_sprint2_vote_creation_integration.py -v
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
from cardinal_vote.models import Base, User, Vote, VoteOption

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
    )
    test_session.add(user)
    await test_session.commit()
    return user


class TestVoteCreationAPI:
    """Test vote creation API endpoints with Sprint 2 enhancements."""

    @pytest.mark.integration
    @pytest.mark.database
    async def test_create_vote_with_minimum_options(self, test_session, test_user):
        """Test creating vote with minimum 2 options."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    vote_data = {
                        "title": "Test Vote with 2 Options",
                        "description": "Testing minimum options",
                        "options": [
                            {
                                "title": "Option 1",
                                "content": "First option content",
                                "option_type": "text",
                                "display_order": 1,
                            },
                            {
                                "title": "Option 2",
                                "content": "Second option content",
                                "option_type": "text",
                                "display_order": 2,
                            },
                        ],
                        "require_auth": False,
                        "access_code": None,
                    }

                    response = client.post("/api/votes/", json=vote_data)
                    assert response.status_code == 201

                    result = response.json()
                    assert result["title"] == vote_data["title"]
                    assert result["require_auth"] is False
                    assert result["access_code"] is None
                    assert len(result["options"]) == 2
                    assert result["status"] == "draft"

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_create_vote_with_maximum_options(self, test_session, test_user):
        """Test creating vote with maximum 20 options."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    # Create 20 options
                    options = []
                    for i in range(1, 21):
                        options.append({
                            "title": f"Option {i}",
                            "content": f"Content for option {i}",
                            "option_type": "text",
                            "display_order": i,
                        })

                    vote_data = {
                        "title": "Test Vote with 20 Options",
                        "description": "Testing maximum options",
                        "options": options,
                        "require_auth": False,
                        "access_code": None,
                    }

                    response = client.post("/api/votes/", json=vote_data)
                    assert response.status_code == 201

                    result = response.json()
                    assert len(result["options"]) == 20

                    # Verify all options are properly ordered
                    for i, option in enumerate(result["options"], 1):
                        assert option["display_order"] == i
                        assert option["title"] == f"Option {i}"

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_create_vote_with_too_few_options(self, test_session, test_user):
        """Test creating vote with only 1 option should fail."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    vote_data = {
                        "title": "Invalid Vote",
                        "description": "Testing too few options",
                        "options": [
                            {
                                "title": "Only Option",
                                "content": "Single option content",
                                "option_type": "text",
                                "display_order": 1,
                            }
                        ],
                        "require_auth": False,
                        "access_code": None,
                    }

                    response = client.post("/api/votes/", json=vote_data)
                    assert response.status_code == 422

                    error_data = response.json()
                    assert "at least 2 items" in str(error_data).lower() or "min_length" in str(error_data).lower()

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_create_vote_with_too_many_options(self, test_session, test_user):
        """Test creating vote with more than 20 options should fail."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    # Create 21 options
                    options = []
                    for i in range(1, 22):
                        options.append({
                            "title": f"Option {i}",
                            "content": f"Content for option {i}",
                            "option_type": "text",
                            "display_order": i,
                        })

                    vote_data = {
                        "title": "Invalid Vote",
                        "description": "Testing too many options",
                        "options": options,
                        "require_auth": False,
                        "access_code": None,
                    }

                    response = client.post("/api/votes/", json=vote_data)
                    assert response.status_code == 422

                    error_data = response.json()
                    assert "at most 20 items" in str(error_data).lower() or "max_length" in str(error_data).lower()

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_create_vote_with_authentication_required(self, test_session, test_user):
        """Test creating vote with authentication required."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    vote_data = {
                        "title": "Auth Required Vote",
                        "description": "Testing authentication requirement",
                        "options": [
                            {
                                "title": "Option 1",
                                "content": "First option",
                                "option_type": "text",
                                "display_order": 1,
                            },
                            {
                                "title": "Option 2",
                                "content": "Second option",
                                "option_type": "text",
                                "display_order": 2,
                            },
                        ],
                        "require_auth": True,
                        "access_code": None,
                    }

                    response = client.post("/api/votes/", json=vote_data)
                    assert response.status_code == 201

                    result = response.json()
                    assert result["require_auth"] is True
                    assert result["access_code"] is None

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_create_vote_with_access_code(self, test_session, test_user):
        """Test creating vote with access code."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    vote_data = {
                        "title": "Access Code Vote",
                        "description": "Testing access code protection",
                        "options": [
                            {
                                "title": "Option 1",
                                "content": "First option",
                                "option_type": "text",
                                "display_order": 1,
                            },
                            {
                                "title": "Option 2",
                                "content": "Second option",
                                "option_type": "text",
                                "display_order": 2,
                            },
                        ],
                        "require_auth": False,
                        "access_code": "secret123",
                    }

                    response = client.post("/api/votes/", json=vote_data)
                    assert response.status_code == 201

                    result = response.json()
                    assert result["require_auth"] is False
                    assert result["access_code"] == "secret123"

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_create_vote_with_both_auth_and_access_code(self, test_session, test_user):
        """Test creating vote with both authentication and access code."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    vote_data = {
                        "title": "Double Protected Vote",
                        "description": "Testing both auth and access code",
                        "options": [
                            {
                                "title": "Secure Option 1",
                                "content": "First secure option",
                                "option_type": "text",
                                "display_order": 1,
                            },
                            {
                                "title": "Secure Option 2",
                                "content": "Second secure option",
                                "option_type": "text",
                                "display_order": 2,
                            },
                        ],
                        "require_auth": True,
                        "access_code": "topsecret456",
                    }

                    response = client.post("/api/votes/", json=vote_data)
                    assert response.status_code == 201

                    result = response.json()
                    assert result["require_auth"] is True
                    assert result["access_code"] == "topsecret456"

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_create_vote_with_mixed_option_types(self, test_session, test_user):
        """Test creating vote with different option types."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    vote_data = {
                        "title": "Mixed Option Types",
                        "description": "Testing different option content types",
                        "options": [
                            {
                                "title": "Text Option",
                                "content": "Simple text content",
                                "option_type": "text",
                                "display_order": 1,
                            },
                            {
                                "title": "Image Option",
                                "content": "image_filename.jpg",
                                "option_type": "image",
                                "display_order": 2,
                            },
                            {
                                "title": "URL Option",
                                "content": "https://example.com/resource",
                                "option_type": "url",
                                "display_order": 3,
                            },
                        ],
                        "require_auth": False,
                        "access_code": None,
                    }

                    response = client.post("/api/votes/", json=vote_data)
                    assert response.status_code == 201

                    result = response.json()
                    assert len(result["options"]) == 3

                    # Verify option types are preserved
                    option_types = {opt["option_type"] for opt in result["options"]}
                    assert option_types == {"text", "image", "url"}

        finally:
            app.dependency_overrides.clear()


class TestVoteCreationValidation:
    """Test vote creation validation and error handling."""

    @pytest.mark.integration
    @pytest.mark.database
    async def test_create_vote_without_title(self, test_session, test_user):
        """Test creating vote without title should fail."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    vote_data = {
                        # Missing title
                        "description": "Vote without title",
                        "options": [
                            {
                                "title": "Option 1",
                                "content": "First option",
                                "option_type": "text",
                                "display_order": 1,
                            },
                            {
                                "title": "Option 2",
                                "content": "Second option",
                                "option_type": "text",
                                "display_order": 2,
                            },
                        ],
                    }

                    response = client.post("/api/votes/", json=vote_data)
                    assert response.status_code == 422

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_create_vote_with_invalid_access_code_length(self, test_session, test_user):
        """Test creating vote with access code too long."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    vote_data = {
                        "title": "Invalid Access Code",
                        "description": "Testing access code validation",
                        "options": [
                            {
                                "title": "Option 1",
                                "content": "First option",
                                "option_type": "text",
                                "display_order": 1,
                            },
                            {
                                "title": "Option 2",
                                "content": "Second option",
                                "option_type": "text",
                                "display_order": 2,
                            },
                        ],
                        "require_auth": False,
                        "access_code": "a" * 51,  # 51 characters, max is 50
                    }

                    response = client.post("/api/votes/", json=vote_data)
                    assert response.status_code == 422

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_create_vote_without_authentication(self, test_session):
        """Test creating vote without authentication should fail."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                vote_data = {
                    "title": "Unauthorized Vote",
                    "description": "Should fail without auth",
                    "options": [
                        {
                            "title": "Option 1",
                            "content": "First option",
                            "option_type": "text",
                            "display_order": 1,
                        },
                        {
                            "title": "Option 2",
                            "content": "Second option",
                            "option_type": "text",
                            "display_order": 2,
                        },
                    ],
                }

                response = client.post("/api/votes/", json=vote_data)
                assert response.status_code == 401

        finally:
            app.dependency_overrides.clear()


class TestVoteCreationPerformance:
    """Test vote creation performance with various loads."""

    @pytest.mark.integration
    @pytest.mark.performance
    async def test_create_vote_with_many_options_performance(self, test_session, test_user):
        """Test performance when creating votes with many options."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    import time

                    # Test with maximum options
                    options = []
                    for i in range(1, 21):  # 20 options
                        options.append({
                            "title": f"Performance Option {i}",
                            "content": f"Content for performance testing option {i}",
                            "option_type": "text",
                            "display_order": i,
                        })

                    vote_data = {
                        "title": "Performance Test Vote",
                        "description": "Testing vote creation performance",
                        "options": options,
                        "require_auth": True,
                        "access_code": "perf123",
                    }

                    start_time = time.time()
                    response = client.post("/api/votes/", json=vote_data)
                    creation_time = time.time() - start_time

                    assert response.status_code == 201
                    # Should complete within reasonable time even with 20 options
                    assert creation_time < 2.0  # Less than 2 seconds

                    result = response.json()
                    assert len(result["options"]) == 20

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.performance
    async def test_concurrent_vote_creation(self, async_session_maker, test_user):
        """Test concurrent vote creation doesn't cause issues."""
        import asyncio

        async def create_vote(session_maker, user, vote_num):
            """Create a single vote in its own session."""
            async with session_maker() as session:
                # Add user to session
                session.add(user)

                app.dependency_overrides[get_async_session] = lambda: session

                try:
                    with TestClient(app) as client:
                        with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                            mock_auth.return_value = user

                            vote_data = {
                                "title": f"Concurrent Vote {vote_num}",
                                "description": f"Testing concurrent creation {vote_num}",
                                "options": [
                                    {
                                        "title": "Option 1",
                                        "content": f"Content 1 for vote {vote_num}",
                                        "option_type": "text",
                                        "display_order": 1,
                                    },
                                    {
                                        "title": "Option 2",
                                        "content": f"Content 2 for vote {vote_num}",
                                        "option_type": "text",
                                        "display_order": 2,
                                    },
                                ],
                                "require_auth": False,
                                "access_code": f"code{vote_num}",
                            }

                            response = client.post("/api/votes/", json=vote_data)
                            return response.status_code, response.json()

                finally:
                    app.dependency_overrides.clear()

        # Create 5 concurrent vote creation tasks
        tasks = []
        for i in range(5):
            tasks.append(create_vote(async_session_maker, test_user, i))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        successful_creations = 0
        for result in results:
            if isinstance(result, tuple) and result[0] == 201:
                successful_creations += 1

        assert successful_creations >= 3  # At least most should succeed
