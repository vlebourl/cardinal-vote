"""Integration tests for image upload functionality."""

import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from cardinal_vote.main import app
from tests.test_auth_integration import create_test_user, get_auth_headers


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def temp_upload_dir():
    """Create temporary upload directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_image_file():
    """Create sample image file for testing."""
    # Create a small PNG image
    image = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


@pytest.fixture
def sample_large_image_file():
    """Create large image file for testing size limits."""
    # Create a large PNG image (over 10MB when saved)
    image = Image.new("RGB", (4000, 4000), color="blue")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


class TestImageUploadIntegration:
    """Integration tests for image upload API endpoints."""

    @pytest.mark.asyncio
    async def test_upload_image_success(
        self, client, temp_upload_dir, sample_image_file
    ):
        """Test successful image upload."""
        # Mock settings to use temp directory
        with patch("cardinal_vote.image_service.settings") as mock_settings:
            mock_settings.UPLOADS_DIR = temp_upload_dir
            mock_settings.MAX_FILE_SIZE_MB = 10
            mock_settings.ALLOWED_UPLOAD_EXTENSIONS = {
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
            }

            # Create test user and get auth headers
            user_data = await create_test_user()
            headers = await get_auth_headers(user_data["email"], "testpassword123")

            # Upload image
            response = client.post(
                "/api/votes/images/upload",
                headers=headers,
                files={"file": ("test.png", sample_image_file, "image/png")},
            )

            assert response.status_code == 200

            result = response.json()
            assert result["success"] is True
            assert "filename" in result
            assert "image_info" in result
            assert "url" in result
            assert result["filename"].endswith(".png")
            assert result["url"].startswith("/uploads/")

    def test_upload_image_unauthorized(self, client, sample_image_file):
        """Test image upload without authentication."""
        response = client.post(
            "/api/votes/images/upload",
            files={"file": ("test.png", sample_image_file, "image/png")},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_image_invalid_extension(self, client):
        """Test image upload with invalid file extension."""
        # Create test user and get auth headers
        user_data = await create_test_user()
        headers = await get_auth_headers(user_data["email"], "testpassword123")

        # Try to upload text file
        text_content = BytesIO(b"This is not an image")
        response = client.post(
            "/api/votes/images/upload",
            headers=headers,
            files={"file": ("test.txt", text_content, "text/plain")},
        )

        assert response.status_code == 400
        assert "File extension not allowed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_image_no_file(self, client):
        """Test image upload without file."""
        # Create test user and get auth headers
        user_data = await create_test_user()
        headers = await get_auth_headers(user_data["email"], "testpassword123")

        response = client.post("/api/votes/images/upload", headers=headers, files={})

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_upload_image_file_too_large(self, client, temp_upload_dir):
        """Test image upload with file too large."""
        with patch("cardinal_vote.image_service.settings") as mock_settings:
            mock_settings.UPLOADS_DIR = temp_upload_dir
            mock_settings.MAX_FILE_SIZE_MB = 1  # Set very small limit
            mock_settings.ALLOWED_UPLOAD_EXTENSIONS = {
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
            }

            # Create test user and get auth headers
            user_data = await create_test_user()
            headers = await get_auth_headers(user_data["email"], "testpassword123")

            # Create large file content (2MB)
            large_content = BytesIO(b"x" * (2 * 1024 * 1024))

            response = client.post(
                "/api/votes/images/upload",
                headers=headers,
                files={"file": ("large.png", large_content, "image/png")},
            )

            assert response.status_code == 413
            assert "File too large" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_image_info_success(
        self, client, temp_upload_dir, sample_image_file
    ):
        """Test getting image information."""
        with patch("cardinal_vote.image_service.settings") as mock_settings:
            mock_settings.UPLOADS_DIR = temp_upload_dir
            mock_settings.MAX_FILE_SIZE_MB = 10
            mock_settings.ALLOWED_UPLOAD_EXTENSIONS = {
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
            }

            # Create test user and get auth headers
            user_data = await create_test_user()
            headers = await get_auth_headers(user_data["email"], "testpassword123")

            # First upload an image
            upload_response = client.post(
                "/api/votes/images/upload",
                headers=headers,
                files={"file": ("test.png", sample_image_file, "image/png")},
            )

            assert upload_response.status_code == 200
            filename = upload_response.json()["filename"]

            # Get image info
            info_response = client.get(
                f"/api/votes/images/{filename}/info", headers=headers
            )

            assert info_response.status_code == 200

            result = info_response.json()
            assert result["success"] is True
            assert "image_info" in result
            assert result["image_info"]["filename"] == filename
            assert result["image_info"]["format"] == "PNG"
            assert result["image_info"]["width"] == 100
            assert result["image_info"]["height"] == 100

    @pytest.mark.asyncio
    async def test_get_image_info_not_found(self, client):
        """Test getting info for non-existent image."""
        # Create test user and get auth headers
        user_data = await create_test_user()
        headers = await get_auth_headers(user_data["email"], "testpassword123")

        response = client.get("/api/votes/images/nonexistent.png/info", headers=headers)

        assert response.status_code == 404

    def test_get_image_info_unauthorized(self, client):
        """Test getting image info without authentication."""
        response = client.get("/api/votes/images/test.png/info")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_image_success(
        self, client, temp_upload_dir, sample_image_file
    ):
        """Test successful image deletion."""
        with patch("cardinal_vote.image_service.settings") as mock_settings:
            mock_settings.UPLOADS_DIR = temp_upload_dir
            mock_settings.MAX_FILE_SIZE_MB = 10
            mock_settings.ALLOWED_UPLOAD_EXTENSIONS = {
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
            }

            # Create test user and get auth headers
            user_data = await create_test_user()
            headers = await get_auth_headers(user_data["email"], "testpassword123")

            # First upload an image
            upload_response = client.post(
                "/api/votes/images/upload",
                headers=headers,
                files={"file": ("test.png", sample_image_file, "image/png")},
            )

            assert upload_response.status_code == 200
            filename = upload_response.json()["filename"]

            # Delete image
            delete_response = client.delete(
                f"/api/votes/images/{filename}", headers=headers
            )

            assert delete_response.status_code == 200

            result = delete_response.json()
            assert result["success"] is True
            assert filename in result["message"]

    @pytest.mark.asyncio
    async def test_delete_image_not_found(self, client):
        """Test deletion of non-existent image."""
        # Create test user and get auth headers
        user_data = await create_test_user()
        headers = await get_auth_headers(user_data["email"], "testpassword123")

        response = client.delete("/api/votes/images/nonexistent.png", headers=headers)

        assert response.status_code == 404

    def test_delete_image_unauthorized(self, client):
        """Test image deletion without authentication."""
        response = client.delete("/api/votes/images/test.png")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_image_in_use(
        self, client, temp_upload_dir, sample_image_file
    ):
        """Test deletion of image currently in use by a vote."""
        with patch("cardinal_vote.image_service.settings") as mock_settings:
            mock_settings.UPLOADS_DIR = temp_upload_dir
            mock_settings.MAX_FILE_SIZE_MB = 10
            mock_settings.ALLOWED_UPLOAD_EXTENSIONS = {
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
            }

            # Create test user and get auth headers
            user_data = await create_test_user()
            headers = await get_auth_headers(user_data["email"], "testpassword123")

            # Upload an image
            upload_response = client.post(
                "/api/votes/images/upload",
                headers=headers,
                files={"file": ("test.png", sample_image_file, "image/png")},
            )

            assert upload_response.status_code == 200
            filename = upload_response.json()["filename"]

            # Create a vote with this image
            vote_data = {
                "title": "Test Vote with Image",
                "description": "A test vote",
                "options": [
                    {
                        "title": "Image Option",
                        "content": filename,
                        "option_type": "image",
                        "display_order": 1,
                    }
                ],
            }

            create_vote_response = client.post(
                "/api/votes/", headers=headers, json=vote_data
            )

            assert create_vote_response.status_code == 201

            # Try to delete the image (should fail)
            delete_response = client.delete(
                f"/api/votes/images/{filename}", headers=headers
            )

            assert delete_response.status_code == 409
            assert "Cannot delete image" in delete_response.json()["detail"]


class TestImageUploadSecurity:
    """Security tests for image upload functionality."""

    @pytest.mark.asyncio
    async def test_upload_image_malicious_filename(
        self, client, temp_upload_dir, sample_image_file
    ):
        """Test image upload with potentially malicious filename."""
        with patch("cardinal_vote.image_service.settings") as mock_settings:
            mock_settings.UPLOADS_DIR = temp_upload_dir
            mock_settings.MAX_FILE_SIZE_MB = 10
            mock_settings.ALLOWED_UPLOAD_EXTENSIONS = {
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
            }

            # Create test user and get auth headers
            user_data = await create_test_user()
            headers = await get_auth_headers(user_data["email"], "testpassword123")

            # Try to upload with malicious filename
            response = client.post(
                "/api/votes/images/upload",
                headers=headers,
                files={
                    "file": ("../../../etc/passwd.png", sample_image_file, "image/png")
                },
            )

            assert response.status_code == 200

            result = response.json()
            # Filename should be sanitized to UUID format
            filename = result["filename"]
            assert not filename.startswith("../")
            assert filename.endswith(".png")

    @pytest.mark.asyncio
    async def test_upload_image_fake_extension(self, client, temp_upload_dir):
        """Test upload of non-image file with image extension."""
        with patch("cardinal_vote.image_service.settings") as mock_settings:
            mock_settings.UPLOADS_DIR = temp_upload_dir
            mock_settings.MAX_FILE_SIZE_MB = 10
            mock_settings.ALLOWED_UPLOAD_EXTENSIONS = {
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
            }

            # Create test user and get auth headers
            user_data = await create_test_user()
            headers = await get_auth_headers(user_data["email"], "testpassword123")

            # Try to upload text file with PNG extension
            fake_image = BytesIO(b"This is not an image but has .png extension")

            response = client.post(
                "/api/votes/images/upload",
                headers=headers,
                files={"file": ("fake.png", fake_image, "image/png")},
            )

            # Should fail validation since it's not a real image
            assert response.status_code == 400
            assert "Invalid image file" in response.json()["detail"]
