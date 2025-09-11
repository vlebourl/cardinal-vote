"""Image processing service for the generalized voting platform."""

import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from PIL import Image

from .config import settings

logger = logging.getLogger(__name__)


class ImageProcessingError(Exception):
    """Exception raised when image processing fails."""


class ImageService:
    """Service for handling image uploads and processing."""

    def __init__(self) -> None:
        """Initialize image service."""
        self.upload_dir = Path(settings.UPLOADS_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
        self.allowed_extensions = settings.ALLOWED_UPLOAD_EXTENSIONS
        self.max_image_dimension = 2048  # Max width/height in pixels
        self.jpeg_quality = 85  # JPEG compression quality

    def _validate_file_extension(self, filename: str) -> bool:
        """Validate file extension."""
        file_extension = Path(filename).suffix.lower()
        return file_extension in self.allowed_extensions

    def _validate_file_size(self, file_size: int) -> bool:
        """Validate file size."""
        return file_size <= self.max_file_size

    def _validate_image_content(self, file_path: Path) -> bool:
        """Validate that file is actually an image by opening it."""
        try:
            with Image.open(file_path) as img:
                img.verify()  # Verify the image is valid
            return True
        except Exception as e:
            logger.warning(f"Image verification failed for {file_path}: {e}")
            return False

    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename while preserving extension."""
        file_extension = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_extension}"

    def _optimize_image(self, input_path: Path, output_path: Path) -> None:
        """Optimize image for web use (resize and compress if needed)."""
        try:
            with Image.open(input_path) as img:
                # Convert RGBA to RGB if necessary (for JPEG)
                if img.mode == "RGBA" and output_path.suffix.lower() in [
                    ".jpg",
                    ".jpeg",
                ]:
                    # Create white background
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(
                        img, mask=img.split()[-1]
                    )  # Use alpha channel as mask
                    img = background

                # Resize if too large
                if (
                    img.width > self.max_image_dimension
                    or img.height > self.max_image_dimension
                ):
                    img.thumbnail(
                        (self.max_image_dimension, self.max_image_dimension),
                        Image.Resampling.LANCZOS,
                    )

                # Save with optimization
                save_kwargs: dict[str, Any] = {"optimize": True}
                if output_path.suffix.lower() in [".jpg", ".jpeg"]:
                    save_kwargs["quality"] = self.jpeg_quality
                    save_kwargs["format"] = "JPEG"
                elif output_path.suffix.lower() == ".png":
                    save_kwargs["format"] = "PNG"
                elif output_path.suffix.lower() == ".webp":
                    save_kwargs["quality"] = self.jpeg_quality
                    save_kwargs["format"] = "WEBP"

                img.save(output_path, **save_kwargs)

        except Exception as e:
            raise ImageProcessingError(f"Failed to optimize image: {e}") from e

    async def upload_image(self, file: UploadFile) -> str:
        """Upload and process an image file.

        Returns the relative filename for storage in database.
        """
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
            )

        # Validate file extension
        if not self._validate_file_extension(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension not allowed. Allowed: {', '.join(self.allowed_extensions)}",
            )

        # Read file content
        try:
            file_content = await file.read()
        except Exception as e:
            logger.error(f"Failed to read uploaded file: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read file"
            ) from e

        # Validate file size
        if not self._validate_file_size(len(file_content)):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB",
            )

        # Generate unique filename
        unique_filename = self._generate_unique_filename(file.filename)
        temp_file_path = self.upload_dir / f"temp_{unique_filename}"
        final_file_path = self.upload_dir / unique_filename

        try:
            # Write temporary file
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(file_content)

            # Validate image content
            if not self._validate_image_content(temp_file_path):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file"
                )

            # Optimize and save final image
            self._optimize_image(temp_file_path, final_file_path)

            # Clean up temporary file
            temp_file_path.unlink(missing_ok=True)

            logger.info(f"Image uploaded successfully: {unique_filename}")
            return unique_filename

        except ImageProcessingError as e:
            # Clean up files
            temp_file_path.unlink(missing_ok=True)
            final_file_path.unlink(missing_ok=True)

            logger.error(f"Image processing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process image",
            ) from e

        except HTTPException:
            # Clean up files
            temp_file_path.unlink(missing_ok=True)
            final_file_path.unlink(missing_ok=True)
            raise

        except Exception as e:
            # Clean up files
            temp_file_path.unlink(missing_ok=True)
            final_file_path.unlink(missing_ok=True)

            logger.error(f"Unexpected error during image upload: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during image upload",
            ) from e

    def delete_image(self, filename: str) -> bool:
        """Delete an image file."""
        try:
            file_path = self.upload_dir / filename
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.info(f"Image deleted successfully: {filename}")
                return True
            else:
                logger.warning(f"Image file not found for deletion: {filename}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete image {filename}: {e}")
            return False

    def get_image_info(self, filename: str) -> dict[str, Any] | None:
        """Get basic information about an image file."""
        try:
            file_path = self.upload_dir / filename
            if not file_path.exists():
                return None

            with Image.open(file_path) as img:
                return {
                    "filename": filename,
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                    "file_size": file_path.stat().st_size,
                }
        except Exception as e:
            logger.error(f"Failed to get image info for {filename}: {e}")
            return None


# Global image service instance
_image_service: ImageService | None = None


def get_image_service() -> ImageService:
    """Get the global image service instance."""
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service
