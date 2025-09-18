#!/usr/bin/env python3
"""Setup image storage directory structure and permissions for dashboard functionality.

This script creates the necessary directory structure for vote image uploads
and sets appropriate permissions for the Cardinal Vote application.
"""

import os
import stat
from pathlib import Path
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_directory_structure() -> bool:
    """Create the image storage directory structure."""
    try:
        # Get base directory (assume this script is in project root/scripts/)
        base_dir = Path(__file__).parent.parent
        uploads_dir = base_dir / "uploads"
        vote_images_dir = uploads_dir / "vote_images"
        temp_uploads_dir = base_dir / "temp_uploads"

        # Create main directories
        directories = [
            uploads_dir,
            vote_images_dir,
            temp_uploads_dir,
        ]

        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            else:
                logger.info(f"Directory already exists: {directory}")

        # Create .gitkeep files to ensure directories are tracked in git
        gitkeep_files = [
            uploads_dir / ".gitkeep",
            vote_images_dir / ".gitkeep",
            temp_uploads_dir / ".gitkeep",
        ]

        for gitkeep_file in gitkeep_files:
            if not gitkeep_file.exists():
                gitkeep_file.touch()
                logger.info(f"Created .gitkeep file: {gitkeep_file}")

        return True

    except Exception as e:
        logger.error(f"Failed to create directory structure: {e}")
        return False


def set_permissions() -> bool:
    """Set appropriate permissions for image storage directories."""
    try:
        base_dir = Path(__file__).parent.parent
        uploads_dir = base_dir / "uploads"
        vote_images_dir = uploads_dir / "vote_images"
        temp_uploads_dir = base_dir / "temp_uploads"

        # Set permissions for directories (755 - owner rwx, group rx, others rx)
        directories = [uploads_dir, vote_images_dir, temp_uploads_dir]

        for directory in directories:
            if directory.exists():
                # Set directory permissions to 755
                os.chmod(directory, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                logger.info(f"Set permissions 755 for directory: {directory}")
            else:
                logger.warning(f"Directory does not exist: {directory}")

        return True

    except Exception as e:
        logger.error(f"Failed to set permissions: {e}")
        return False


def validate_configuration() -> bool:
    """Validate that the image storage configuration is correct."""
    try:
        # Try to import the config to validate settings
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from cardinal_vote.config import settings

        # Validate image upload settings
        required_settings = [
            'VOTE_IMAGE_MAX_SIZE_MB',
            'VOTE_IMAGE_MAX_DIMENSIONS',
            'MAX_VOTE_CHOICES',
            'ALLOWED_UPLOAD_EXTENSIONS',
            'VOTE_IMAGES_DIR',
        ]

        missing_settings = []
        for setting in required_settings:
            if not hasattr(settings, setting):
                missing_settings.append(setting)

        if missing_settings:
            logger.error(f"Missing configuration settings: {missing_settings}")
            return False

        # Validate directory paths
        if not settings.VOTE_IMAGES_DIR.exists():
            logger.error(f"Vote images directory does not exist: {settings.VOTE_IMAGES_DIR}")
            return False

        # Validate file size limits
        if settings.VOTE_IMAGE_MAX_SIZE_MB <= 0:
            logger.error(f"Invalid image size limit: {settings.VOTE_IMAGE_MAX_SIZE_MB}")
            return False

        # Validate dimensions
        width, height = settings.VOTE_IMAGE_MAX_DIMENSIONS
        if width <= 0 or height <= 0:
            logger.error(f"Invalid image dimensions: {settings.VOTE_IMAGE_MAX_DIMENSIONS}")
            return False

        # Validate extensions
        if not settings.ALLOWED_UPLOAD_EXTENSIONS:
            logger.error("No allowed upload extensions configured")
            return False

        logger.info("Configuration validation passed")
        return True

    except ImportError as e:
        logger.error(f"Failed to import configuration: {e}")
        return False
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


def create_test_structure() -> bool:
    """Create test vote image directories for validation."""
    try:
        base_dir = Path(__file__).parent.parent
        vote_images_dir = base_dir / "uploads" / "vote_images"

        # Create a few test vote directories to validate structure
        test_vote_ids = [
            "test-vote-1",
            "test-vote-2",
            "test-vote-3",
        ]

        for vote_id in test_vote_ids:
            test_dir = vote_images_dir / vote_id
            if not test_dir.exists():
                test_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created test vote directory: {test_dir}")

                # Create a README file explaining the structure
                readme_file = test_dir / "README.txt"
                readme_content = f"""Vote Image Directory: {vote_id}

This directory contains uploaded images for vote choices.
Images are stored with the naming convention: {{choice_id}}.{{extension}}

Supported formats: JPEG, PNG, GIF, WebP
Maximum size: 5MB per image
Maximum dimensions: 2048x2048 pixels

Created by setup_image_storage.py script
"""
                readme_file.write_text(readme_content)

        return True

    except Exception as e:
        logger.error(f"Failed to create test structure: {e}")
        return False


def main():
    """Main setup function."""
    logger.info("Starting image storage setup...")

    success_steps = 0
    total_steps = 4

    # Step 1: Create directory structure
    if create_directory_structure():
        logger.info("✓ Directory structure created successfully")
        success_steps += 1
    else:
        logger.error("✗ Failed to create directory structure")

    # Step 2: Set permissions
    if set_permissions():
        logger.info("✓ Permissions set successfully")
        success_steps += 1
    else:
        logger.error("✗ Failed to set permissions")

    # Step 3: Validate configuration
    if validate_configuration():
        logger.info("✓ Configuration validation passed")
        success_steps += 1
    else:
        logger.error("✗ Configuration validation failed")

    # Step 4: Create test structure
    if create_test_structure():
        logger.info("✓ Test structure created successfully")
        success_steps += 1
    else:
        logger.error("✗ Failed to create test structure")

    # Final status
    if success_steps == total_steps:
        logger.info("🎉 Image storage setup completed successfully!")
        logger.info("The application is ready for image upload functionality.")
        return 0
    else:
        logger.error(f"⚠️  Setup completed with {total_steps - success_steps} failures.")
        logger.error("Please check the errors above and resolve them before proceeding.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
