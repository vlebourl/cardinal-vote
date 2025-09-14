"""Test authentication integration helpers."""

import uuid
from typing import Any

from fastapi.testclient import TestClient

from cardinal_vote.main import app


def get_test_client() -> TestClient:
    """Get a test client instance."""
    return TestClient(app)


async def create_test_user(
    email: str = None, password: str = "testpassword123"
) -> dict[str, Any]:
    """Create a test user via the registration API."""
    if email is None:
        # Generate unique email for each test
        unique_id = str(uuid.uuid4())[:8]
        email = f"test+{unique_id}@example.com"

    client = get_test_client()

    user_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "password": password,
    }

    response = client.post("/api/auth/register", json=user_data)

    if response.status_code == 201:
        return {
            "email": email,
            "password": password,
            "user_data": response.json()
        }
    else:
        raise Exception(f"Failed to create test user: {response.status_code} - {response.text}")


async def get_auth_headers(email: str, password: str) -> dict[str, str]:
    """Get authentication headers for a user."""
    client = get_test_client()

    login_data = {
        "username": email,  # OAuth2 uses 'username' field for email
        "password": password,
    }

    response = client.post("/api/auth/token", data=login_data)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    else:
        raise Exception(f"Failed to authenticate user: {response.status_code} - {response.text}")


def create_authenticated_client() -> tuple[TestClient, dict[str, str]]:
    """Create a test client with authenticated headers.

    Returns:
        Tuple of (client, headers) where headers contain authentication
    """
    import asyncio

    # Create user and get auth headers
    user_data = asyncio.run(create_test_user())
    headers = asyncio.run(get_auth_headers(user_data["email"], user_data["password"]))

    client = get_test_client()
    return client, headers
