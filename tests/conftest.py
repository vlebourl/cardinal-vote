"""Pytest configuration and shared fixtures for the ToVéCo voting platform tests."""

import os
import tempfile

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Set up required environment variables for all tests."""
    # Set required admin environment variables
    os.environ["ADMIN_USERNAME"] = "test_admin"
    os.environ["ADMIN_PASSWORD"] = "test_password_123"
    os.environ["SESSION_SECRET_KEY"] = "test_session_secret_key_for_testing_only"

    # Set other test-specific environment variables
    os.environ["DEBUG"] = "false"
    os.environ["HOST"] = "127.0.0.1"
    os.environ["PORT"] = "8000"

    # Use a test database path
    test_db_path = tempfile.mktemp(suffix=".db")
    os.environ["DATABASE_PATH"] = test_db_path

    yield

    # Cleanup test database file if it exists
    if os.path.exists(test_db_path):
        try:
            os.unlink(test_db_path)
        except OSError:
            pass  # Ignore cleanup errors


@pytest.fixture(scope="function", autouse=True)
def clean_database():
    """Ensure each test starts with a clean database."""
    # Create a unique database path for each test
    test_db_path = tempfile.mktemp(suffix=".db")
    original_db_path = os.environ.get("DATABASE_PATH")

    # Set the test database path
    os.environ["DATABASE_PATH"] = test_db_path

    yield

    # Cleanup after test
    if os.path.exists(test_db_path):
        try:
            os.unlink(test_db_path)
        except OSError:
            pass  # Ignore cleanup errors

    # Restore original database path
    if original_db_path:
        os.environ["DATABASE_PATH"] = original_db_path
