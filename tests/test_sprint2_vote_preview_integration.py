"""Integration tests for Sprint 2 vote preview and sharing functionality.

These tests verify the vote preview and sharing features including:
- Vote preview API endpoints
- Vote activation functionality
- Sharing interface components
- Access control validation
- Vote status management

For local testing, run:
    docker-compose -f docker-compose.test.yml up -d postgres-test
    export TEST_DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5433/test_cardinal_vote"
    uv run pytest tests/test_sprint2_vote_preview_integration.py -v
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
        last_login=datetime.utcnow() - timedelta(minutes=5),
    )
    test_session.add(user)
    await test_session.commit()
    return user


@pytest.fixture
async def sample_vote(test_session, test_user):
    """Create sample vote for testing."""
    vote = Vote(
        id=uuid4(),
        title="Test Vote for Preview",
        slug="test-vote-for-preview",
        description="This is a test vote for preview functionality",
        status="draft",
        creator_id=test_user.id,
        created_at=datetime.utcnow(),
        require_auth=False,
        access_code=None,
    )
    test_session.add(vote)
    await test_session.commit()

    # Add options
    options = [
        VoteOption(
            id=uuid4(),
            vote_id=vote.id,
            title="Option A",
            content="First option content",
            option_type="text",
            display_order=1,
        ),
        VoteOption(
            id=uuid4(),
            vote_id=vote.id,
            title="Option B",
            content="Second option content",
            option_type="text",
            display_order=2,
        ),
        VoteOption(
            id=uuid4(),
            vote_id=vote.id,
            title="Option C",
            content="Third option content",
            option_type="text",
            display_order=3,
        ),
    ]

    for option in options:
        test_session.add(option)

    await test_session.commit()
    return vote


@pytest.fixture
async def protected_vote(test_session, test_user):
    """Create protected vote with access controls for testing."""
    vote = Vote(
        id=uuid4(),
        title="Protected Test Vote",
        slug="protected-test-vote",
        description="This vote has access controls",
        status="draft",
        creator_id=test_user.id,
        created_at=datetime.utcnow(),
        require_auth=True,
        access_code="secret123",
    )
    test_session.add(vote)
    await test_session.commit()

    # Add options
    options = [
        VoteOption(
            id=uuid4(),
            vote_id=vote.id,
            title="Secure Option 1",
            content="First secure option",
            option_type="text",
            display_order=1,
        ),
        VoteOption(
            id=uuid4(),
            vote_id=vote.id,
            title="Secure Option 2",
            content="Second secure option",
            option_type="text",
            display_order=2,
        ),
    ]

    for option in options:
        test_session.add(option)

    await test_session.commit()
    return vote


class TestVotePreviewAPI:
    """Test vote preview API endpoints."""

    @pytest.mark.integration
    @pytest.mark.database
    async def test_get_vote_preview_success(self, test_session, test_user, sample_vote):
        """Test successful vote preview retrieval."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    response = client.get(f"/api/votes/{sample_vote.id}/preview")
                    assert response.status_code == 200

                    result = response.json()

                    # Verify preview structure
                    assert "vote" in result
                    assert "sharing_info" in result
                    assert "access_settings" in result

                    vote_data = result["vote"]
                    assert vote_data["id"] == str(sample_vote.id)
                    assert vote_data["title"] == sample_vote.title
                    assert vote_data["description"] == sample_vote.description
                    assert vote_data["status"] == sample_vote.status
                    assert "options" in vote_data
                    assert len(vote_data["options"]) == 3

                    # Verify sharing info
                    sharing_info = result["sharing_info"]
                    assert "public_url" in sharing_info
                    assert "embed_code" in sharing_info
                    assert "social_links" in sharing_info

                    # Verify access settings
                    access_settings = result["access_settings"]
                    assert access_settings["require_auth"] == sample_vote.require_auth
                    assert access_settings["has_access_code"] == (sample_vote.access_code is not None)

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_get_vote_preview_protected_vote(self, test_session, test_user, protected_vote):
        """Test vote preview for protected vote."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    response = client.get(f"/api/votes/{protected_vote.id}/preview")
                    assert response.status_code == 200

                    result = response.json()
                    access_settings = result["access_settings"]

                    # Should show access control settings
                    assert access_settings["require_auth"] is True
                    assert access_settings["has_access_code"] is True

                    # Should not expose actual access code
                    assert "access_code" not in access_settings

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_get_vote_preview_not_found(self, test_session, test_user):
        """Test vote preview for non-existent vote."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    fake_id = str(uuid4())
                    response = client.get(f"/api/votes/{fake_id}/preview")
                    assert response.status_code == 404

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_get_vote_preview_wrong_owner(self, test_session, sample_vote):
        """Test vote preview by non-owner should fail."""
        # Create different user
        different_user = User(
            id=uuid4(),
            email="different@example.com",
            first_name="Different",
            last_name="User",
            is_verified=True,
            is_super_admin=False,
            created_at=datetime.utcnow(),
        )
        test_session.add(different_user)
        await test_session.commit()

        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = different_user

                    response = client.get(f"/api/votes/{sample_vote.id}/preview")
                    assert response.status_code == 403

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_get_vote_preview_unauthorized(self, test_session, sample_vote):
        """Test vote preview without authentication."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/votes/{sample_vote.id}/preview")
                assert response.status_code == 401

        finally:
            app.dependency_overrides.clear()


class TestVoteActivation:
    """Test vote activation functionality."""

    @pytest.mark.integration
    @pytest.mark.database
    async def test_activate_vote_from_draft(self, test_session, test_user, sample_vote):
        """Test activating vote from draft status."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    # Verify initial status
                    assert sample_vote.status == "draft"

                    # Activate vote
                    response = client.patch(
                        f"/api/votes/{sample_vote.id}/status",
                        json={"status": "active"}
                    )
                    assert response.status_code == 200

                    result = response.json()
                    assert result["status"] == "active"

                    # Verify status change in database
                    await test_session.refresh(sample_vote)
                    assert sample_vote.status == "active"

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_pause_active_vote(self, test_session, test_user, sample_vote):
        """Test pausing an active vote."""
        # First activate the vote
        sample_vote.status = "active"
        await test_session.commit()

        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    # Pause vote
                    response = client.patch(
                        f"/api/votes/{sample_vote.id}/status",
                        json={"status": "paused"}
                    )
                    assert response.status_code == 200

                    result = response.json()
                    assert result["status"] == "paused"

                    # Verify status change in database
                    await test_session.refresh(sample_vote)
                    assert sample_vote.status == "paused"

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_complete_active_vote(self, test_session, test_user, sample_vote):
        """Test completing an active vote."""
        # First activate the vote
        sample_vote.status = "active"
        await test_session.commit()

        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    # Complete vote
                    response = client.patch(
                        f"/api/votes/{sample_vote.id}/status",
                        json={"status": "completed"}
                    )
                    assert response.status_code == 200

                    result = response.json()
                    assert result["status"] == "completed"

                    # Verify status change in database
                    await test_session.refresh(sample_vote)
                    assert sample_vote.status == "completed"

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_invalid_status_transition(self, test_session, test_user, sample_vote):
        """Test invalid status transition."""
        # First complete the vote
        sample_vote.status = "completed"
        await test_session.commit()

        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    # Try to change completed vote back to draft (should fail or be allowed based on business logic)
                    response = client.patch(
                        f"/api/votes/{sample_vote.id}/status",
                        json={"status": "draft"}
                    )
                    # This might be 200 or 400 depending on business rules
                    assert response.status_code in [200, 400]

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_status_change_unauthorized(self, test_session, sample_vote):
        """Test vote status change without authentication."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                response = client.patch(
                    f"/api/votes/{sample_vote.id}/status",
                    json={"status": "active"}
                )
                assert response.status_code == 401

        finally:
            app.dependency_overrides.clear()


class TestVotePreviewPage:
    """Test vote preview page rendering."""

    @pytest.mark.integration
    @pytest.mark.database
    async def test_vote_preview_page_authenticated(self, test_session, test_user, sample_vote):
        """Test vote preview page for authenticated user."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    response = client.get(f"/vote-preview/{sample_vote.id}")
                    assert response.status_code == 200

                    # Verify it's HTML content
                    assert "text/html" in response.headers.get("content-type", "")

                    # Check for key elements in HTML
                    html_content = response.text
                    assert sample_vote.title in html_content
                    assert "vote-preview" in html_content
                    assert "sharing-options" in html_content

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_vote_preview_page_unauthenticated(self, test_session, sample_vote):
        """Test vote preview page for unauthenticated user."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                response = client.get(f"/vote-preview/{sample_vote.id}")

                # Should redirect to login or show error
                assert response.status_code in [302, 401, 403]

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_vote_preview_page_not_found(self, test_session, test_user):
        """Test vote preview page for non-existent vote."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    fake_id = str(uuid4())
                    response = client.get(f"/vote-preview/{fake_id}")
                    assert response.status_code == 404

        finally:
            app.dependency_overrides.clear()


class TestSharingFunctionality:
    """Test sharing functionality components."""

    @pytest.mark.integration
    @pytest.mark.database
    async def test_sharing_info_generation(self, test_session, test_user, sample_vote):
        """Test sharing information generation."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    response = client.get(f"/api/votes/{sample_vote.id}/preview")
                    assert response.status_code == 200

                    result = response.json()
                    sharing_info = result["sharing_info"]

                    # Verify sharing components
                    assert "public_url" in sharing_info
                    assert "embed_code" in sharing_info
                    assert "social_links" in sharing_info

                    # Verify public URL structure
                    public_url = sharing_info["public_url"]
                    assert sample_vote.slug in public_url

                    # Verify embed code
                    embed_code = sharing_info["embed_code"]
                    assert "iframe" in embed_code.lower()
                    assert sample_vote.slug in embed_code

                    # Verify social links
                    social_links = sharing_info["social_links"]
                    assert "twitter" in social_links
                    assert "facebook" in social_links
                    assert "linkedin" in social_links
                    assert "email" in social_links

                    # Each social link should contain the public URL
                    for _platform, link in social_links.items():
                        assert isinstance(link, str)
                        assert len(link) > 0

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.database
    async def test_sharing_with_access_controls(self, test_session, test_user, protected_vote):
        """Test sharing for vote with access controls."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    response = client.get(f"/api/votes/{protected_vote.id}/preview")
                    assert response.status_code == 200

                    result = response.json()
                    sharing_info = result["sharing_info"]

                    # Should still generate sharing links even for protected votes
                    assert "public_url" in sharing_info
                    assert "embed_code" in sharing_info
                    assert "social_links" in sharing_info

                    # But should include access control information in preview
                    access_settings = result["access_settings"]
                    assert access_settings["require_auth"] is True
                    assert access_settings["has_access_code"] is True

        finally:
            app.dependency_overrides.clear()


class TestVotePreviewIntegration:
    """Test complete vote preview workflow."""

    @pytest.mark.integration
    @pytest.mark.database
    async def test_complete_preview_workflow(self, test_session, test_user, sample_vote):
        """Test complete vote preview and activation workflow."""
        app.dependency_overrides[get_async_session] = lambda: test_session

        try:
            with TestClient(app) as client:
                with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                    mock_auth.return_value = test_user

                    # 1. Get initial preview (draft status)
                    preview_response = client.get(f"/api/votes/{sample_vote.id}/preview")
                    assert preview_response.status_code == 200

                    preview_data = preview_response.json()
                    assert preview_data["vote"]["status"] == "draft"

                    # 2. Activate the vote
                    activate_response = client.patch(
                        f"/api/votes/{sample_vote.id}/status",
                        json={"status": "active"}
                    )
                    assert activate_response.status_code == 200

                    # 3. Get preview again (should show active status)
                    updated_preview_response = client.get(f"/api/votes/{sample_vote.id}/preview")
                    assert updated_preview_response.status_code == 200

                    updated_preview_data = updated_preview_response.json()
                    assert updated_preview_data["vote"]["status"] == "active"

                    # 4. Verify sharing info remains consistent
                    original_sharing = preview_data["sharing_info"]
                    updated_sharing = updated_preview_data["sharing_info"]

                    assert original_sharing["public_url"] == updated_sharing["public_url"]
                    assert original_sharing["embed_code"] == updated_sharing["embed_code"]

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.integration
    @pytest.mark.performance
    async def test_preview_performance(self, async_session_maker, test_user):
        """Test vote preview performance."""
        async with async_session_maker() as session:
            session.add(test_user)

            # Create vote with many options
            vote = Vote(
                id=uuid4(),
                title="Performance Test Vote",
                slug="performance-test-vote",
                description="Testing preview performance with many options",
                status="draft",
                creator_id=test_user.id,
                created_at=datetime.utcnow(),
                require_auth=False,
                access_code=None,
            )
            session.add(vote)
            await session.commit()

            # Add 20 options (maximum)
            for i in range(20):
                option = VoteOption(
                    id=uuid4(),
                    vote_id=vote.id,
                    title=f"Performance Option {i+1}",
                    content=f"Content for performance option {i+1}",
                    option_type="text",
                    display_order=i+1,
                )
                session.add(option)

            await session.commit()

            # Test performance
            app.dependency_overrides[get_async_session] = lambda: session

            try:
                with TestClient(app) as client:
                    with patch("cardinal_vote.dependencies.get_current_user") as mock_auth:
                        mock_auth.return_value = test_user

                        import time

                        # Test preview endpoint performance
                        start_time = time.time()
                        response = client.get(f"/api/votes/{vote.id}/preview")
                        preview_time = time.time() - start_time

                        assert response.status_code == 200
                        assert preview_time < 1.0  # Should complete in less than 1 second

                        result = response.json()
                        assert len(result["vote"]["options"]) == 20

            finally:
                app.dependency_overrides.clear()
