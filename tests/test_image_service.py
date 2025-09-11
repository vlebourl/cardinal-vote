"""Tests for the image service functionality."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image

from cardinal_vote.image_service import (
    ImageProcessingError,
    ImageService,
    get_image_service,
)


@pytest.fixture
def temp_upload_dir():
    """Create a temporary directory for test uploads."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def image_service(temp_upload_dir):
    """Create an ImageService instance with temporary directory."""
    # Mock the settings to use our temp directory
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
        service = ImageService()
        yield service


@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile for testing."""

    def create_mock_file(
        filename: str, content: bytes, content_type: str = "image/png"
    ):
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = filename
        mock_file.content_type = content_type
        mock_file.read = Mock(return_value=asyncio.create_future())
        mock_file.read.return_value.set_result(content)
        return mock_file

    return create_mock_file


@pytest.fixture
def sample_image_bytes():
    """Create sample image bytes for testing."""
    # Create a small PNG image
    image = Image.new("RGB", (100, 100), color="red")
    import io

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class TestImageService:
    """Test cases for ImageService class."""

    def test_init_creates_upload_directory(self, temp_upload_dir):
        """Test that ImageService creates upload directory."""
        with patch("cardinal_vote.image_service.settings") as mock_settings:
            mock_settings.UPLOADS_DIR = temp_upload_dir / "new_dir"
            mock_settings.MAX_FILE_SIZE_MB = 10
            mock_settings.ALLOWED_UPLOAD_EXTENSIONS = {".png", ".jpg"}

            service = ImageService()
            assert service.upload_dir.exists()
            assert service.max_file_size == 10 * 1024 * 1024

    def test_validate_file_extension_valid(self, image_service):
        """Test file extension validation with valid extensions."""
        assert image_service._validate_file_extension("test.png") is True
        assert image_service._validate_file_extension("test.jpg") is True
        assert image_service._validate_file_extension("test.JPEG") is True
        assert image_service._validate_file_extension("test.gif") is True
        assert image_service._validate_file_extension("test.webp") is True

    def test_validate_file_extension_invalid(self, image_service):
        """Test file extension validation with invalid extensions."""
        assert image_service._validate_file_extension("test.txt") is False
        assert image_service._validate_file_extension("test.pdf") is False
        assert image_service._validate_file_extension("test") is False
        assert image_service._validate_file_extension("test.exe") is False

    def test_validate_file_size_valid(self, image_service):
        """Test file size validation with valid sizes."""
        # 1MB file should be valid (limit is 10MB)
        assert image_service._validate_file_size(1024 * 1024) is True
        assert image_service._validate_file_size(1000) is True

    def test_validate_file_size_invalid(self, image_service):
        """Test file size validation with invalid sizes."""
        # 15MB file should be invalid (limit is 10MB)
        assert image_service._validate_file_size(15 * 1024 * 1024) is False

    def test_generate_unique_filename(self, image_service):
        """Test unique filename generation."""
        filename1 = image_service._generate_unique_filename("test.png")
        filename2 = image_service._generate_unique_filename("test.png")

        # Both should have .png extension
        assert filename1.endswith(".png")
        assert filename2.endswith(".png")

        # Both should be different
        assert filename1 != filename2

        # Both should be valid UUIDs plus extension
        base1 = filename1.replace(".png", "")
        base2 = filename2.replace(".png", "")
        assert UUID(base1)  # Should not raise ValueError
        assert UUID(base2)  # Should not raise ValueError

    @pytest.mark.asyncio
    async def test_upload_image_success(
        self, image_service, mock_upload_file, sample_image_bytes
    ):
        """Test successful image upload."""
        mock_file = mock_upload_file("test.png", sample_image_bytes)

        # Mock image validation and optimization
        with (
            patch.object(image_service, "_validate_image_content", return_value=True),
            patch.object(image_service, "_optimize_image"),
        ):
            filename = await image_service.upload_image(mock_file)

            # Should return a UUID-based filename with correct extension
            assert filename.endswith(".png")
            assert UUID(filename.replace(".png", ""))  # Should be valid UUID

    @pytest.mark.asyncio
    async def test_upload_image_no_filename(self, image_service, sample_image_bytes):
        """Test upload with no filename raises error."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = None

        with pytest.raises(HTTPException) as exc_info:
            await image_service.upload_image(mock_file)

        assert exc_info.value.status_code == 400
        assert "No filename provided" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_image_invalid_extension(
        self, image_service, sample_image_bytes
    ):
        """Test upload with invalid extension raises error."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"

        with pytest.raises(HTTPException) as exc_info:
            await image_service.upload_image(mock_file)

        assert exc_info.value.status_code == 400
        assert "File extension not allowed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_image_file_too_large(self, image_service, mock_upload_file):
        """Test upload with file too large raises error."""
        # Create file larger than 10MB limit
        large_content = b"x" * (15 * 1024 * 1024)
        mock_file = mock_upload_file("test.png", large_content)

        with pytest.raises(HTTPException) as exc_info:
            await image_service.upload_image(mock_file)

        assert exc_info.value.status_code == 413
        assert "File too large" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_image_invalid_content(self, image_service, mock_upload_file):
        """Test upload with invalid image content raises error."""
        mock_file = mock_upload_file("test.png", b"not an image")

        with patch.object(image_service, "_validate_image_content", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await image_service.upload_image(mock_file)

            assert exc_info.value.status_code == 400
            assert "Invalid image file" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_image_processing_error(
        self, image_service, mock_upload_file, sample_image_bytes
    ):
        """Test upload with image processing error."""
        mock_file = mock_upload_file("test.png", sample_image_bytes)

        with (
            patch.object(image_service, "_validate_image_content", return_value=True),
            patch.object(
                image_service,
                "_optimize_image",
                side_effect=ImageProcessingError("Processing failed"),
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await image_service.upload_image(mock_file)

            assert exc_info.value.status_code == 400
            assert "Failed to process image" in str(exc_info.value.detail)

    def test_delete_image_success(self, image_service, temp_upload_dir):
        """Test successful image deletion."""
        # Create a test file
        test_file = temp_upload_dir / "test.png"
        test_file.write_text("test content")

        result = image_service.delete_image("test.png")

        assert result is True
        assert not test_file.exists()

    def test_delete_image_not_found(self, image_service):
        """Test deletion of non-existent image."""
        result = image_service.delete_image("nonexistent.png")
        assert result is False

    def test_get_image_info_success(
        self, image_service, temp_upload_dir, sample_image_bytes
    ):
        """Test getting image information."""
        # Create a real image file
        test_file = temp_upload_dir / "test.png"
        test_file.write_bytes(sample_image_bytes)

        info = image_service.get_image_info("test.png")

        assert info is not None
        assert info["filename"] == "test.png"
        assert info["format"] == "PNG"
        assert info["width"] == 100
        assert info["height"] == 100
        assert info["file_size"] > 0

    def test_get_image_info_not_found(self, image_service):
        """Test getting info for non-existent image."""
        info = image_service.get_image_info("nonexistent.png")
        assert info is None

    def test_validate_image_content_valid(
        self, image_service, temp_upload_dir, sample_image_bytes
    ):
        """Test validation of valid image content."""
        test_file = temp_upload_dir / "test.png"
        test_file.write_bytes(sample_image_bytes)

        result = image_service._validate_image_content(test_file)
        assert result is True

    def test_validate_image_content_invalid(self, image_service, temp_upload_dir):
        """Test validation of invalid image content."""
        test_file = temp_upload_dir / "test.png"
        test_file.write_text("not an image")

        result = image_service._validate_image_content(test_file)
        assert result is False

    def test_optimize_image_resize(self, image_service, temp_upload_dir):
        """Test image optimization with resizing."""
        # Create a large image
        large_image = Image.new("RGB", (3000, 3000), color="blue")
        input_path = temp_upload_dir / "large.png"
        output_path = temp_upload_dir / "optimized.png"
        large_image.save(input_path, format="PNG")

        image_service._optimize_image(input_path, output_path)

        # Check that output exists and is smaller
        assert output_path.exists()
        with Image.open(output_path) as optimized:
            assert optimized.width <= 2048
            assert optimized.height <= 2048

    def test_optimize_image_rgba_to_rgb(self, image_service, temp_upload_dir):
        """Test RGBA to RGB conversion for JPEG."""
        # Create RGBA image
        rgba_image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        input_path = temp_upload_dir / "rgba.png"
        output_path = temp_upload_dir / "rgb.jpg"
        rgba_image.save(input_path, format="PNG")

        image_service._optimize_image(input_path, output_path)

        # Check that output exists and is RGB
        assert output_path.exists()
        with Image.open(output_path) as optimized:
            assert optimized.mode == "RGB"


class TestImageServiceGlobal:
    """Test global image service functions."""

    def test_get_image_service_singleton(self):
        """Test that get_image_service returns the same instance."""
        # Clear any existing instance
        import cardinal_vote.image_service

        cardinal_vote.image_service._image_service = None

        service1 = get_image_service()
        service2 = get_image_service()

        assert service1 is service2


class TestImageProcessingError:
    """Test ImageProcessingError exception."""

    def test_image_processing_error_creation(self):
        """Test creating ImageProcessingError."""
        error = ImageProcessingError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
