"""Authentication routes for the generalized voting platform."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator

from .auth_manager import GeneralizedAuthManager
from .dependencies import (
    AsyncDatabaseSession,
    CurrentUser,
    get_async_session,
    get_auth_manager,
)
from .models import DatabaseError

logger = logging.getLogger(__name__)

# Create router
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# Pydantic models for API requests/responses
class UserRegistration(BaseModel):
    """Model for user registration request."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    first_name: str = Field(
        ..., min_length=1, max_length=100, description="User first name"
    )
    last_name: str = Field(
        ..., min_length=1, max_length=100, description="User last name"
    )

    @validator("email")
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        v = v.strip().lower()
        if "@" not in v or len(v) < 5:
            raise ValueError("Invalid email address")
        return v

    @validator("password")
    def validate_password(cls, v: str) -> str:
        """Password strength validation."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        # Add more password complexity rules as needed
        return v

    @validator("first_name", "last_name")
    def validate_names(cls, v: str) -> str:
        """Name validation."""
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v


class UserLogin(BaseModel):
    """Model for user login request."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Model for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class UserResponse(BaseModel):
    """Model for user data response."""

    id: str
    email: str
    first_name: str
    last_name: str
    is_verified: bool
    is_super_admin: bool
    created_at: str

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Generic message response."""

    success: bool
    message: str


@auth_router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserRegistration,
    request: Request,
    auth_manager: GeneralizedAuthManager = Depends(get_auth_manager),
    session: AsyncDatabaseSession = Depends(get_async_session),
) -> TokenResponse:
    """Register a new user account."""
    try:
        # Get client IP for rate limiting
        client_ip = request.client.host if request.client else "unknown"

        # Create the user
        user = await auth_manager.create_user(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            session=session,
        )

        # Create JWT tokens
        tokens = auth_manager.create_tokens(user)

        # Prepare user data for response
        user_dict = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_verified": user.is_verified,
            "is_super_admin": user.is_super_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

        logger.info(f"User registered successfully: {user.email} from {client_ip}")

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            user=user_dict,
        )

    except DatabaseError as e:
        logger.warning(f"Registration failed: {e}")
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed"
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error",
        ) from e


@auth_router.post("/token", response_model=TokenResponse)
async def login_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_manager: GeneralizedAuthManager = Depends(get_auth_manager),
    session: AsyncDatabaseSession = Depends(get_async_session),
) -> TokenResponse:
    """Login user and return JWT tokens (OAuth2 compatible endpoint)."""
    try:
        # Get client IP for rate limiting
        client_ip = request.client.host if request.client else "unknown"

        # Authenticate user
        user = await auth_manager.authenticate_user(
            email=form_data.username,  # OAuth2 uses 'username' field for email
            password=form_data.password,
            ip_address=client_ip,
            session=session,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create JWT tokens
        tokens = auth_manager.create_tokens(user)

        # Prepare user data for response
        user_dict = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_verified": user.is_verified,
            "is_super_admin": user.is_super_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            user=user_dict,
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error",
        ) from e


@auth_router.post("/login", response_model=TokenResponse)
async def login_user_json(
    user_data: UserLogin,
    request: Request,
    auth_manager: GeneralizedAuthManager = Depends(get_auth_manager),
    session: AsyncDatabaseSession = Depends(get_async_session),
) -> TokenResponse:
    """Login user with JSON data (alternative to OAuth2 form)."""
    try:
        # Get client IP for rate limiting
        client_ip = request.client.host if request.client else "unknown"

        # Authenticate user
        user = await auth_manager.authenticate_user(
            email=user_data.email,
            password=user_data.password,
            ip_address=client_ip,
            session=session,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Create JWT tokens
        tokens = auth_manager.create_tokens(user)

        # Prepare user data for response
        user_dict = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_verified": user.is_verified,
            "is_super_admin": user.is_super_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            user=user_dict,
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error",
        ) from e


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser) -> UserResponse:
    """Get current authenticated user information."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_verified=current_user.is_verified,
        is_super_admin=current_user.is_super_admin,
        created_at=current_user.created_at.isoformat()
        if current_user.created_at
        else "",
    )


@auth_router.post("/refresh", response_model=dict[str, str])
async def refresh_access_token(
    refresh_token: str,
    auth_manager: GeneralizedAuthManager = Depends(get_auth_manager),
    session: AsyncDatabaseSession = Depends(get_async_session),
) -> dict[str, str]:
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        payload = auth_manager.verify_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Get user ID from refresh token
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Get user from database
        from uuid import UUID

        user_id = UUID(user_id_str)
        user = await auth_manager.get_user_by_id(user_id, session)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        # Create new access token
        user_data = {
            "sub": str(user.id),
            "email": user.email,
            "is_super_admin": user.is_super_admin,
        }
        new_access_token = auth_manager.create_access_token(user_data)

        return {"access_token": new_access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token refresh failed"
        )
