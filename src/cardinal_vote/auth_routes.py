"""Authentication routes for the generalized voting platform."""

import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator

from .auth_manager import GeneralizedAuthManager
from .dependencies import (
    AsyncDatabaseSession,
    CurrentUser,
    get_auth_manager,
)
from .input_sanitizer import InputSanitizer
from .models import AccountDeletionLog, DatabaseError

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


class UserProfileUpdate(BaseModel):
    """Model for user profile update request."""

    first_name: str | None = Field(
        None, min_length=1, max_length=100, description="User first name"
    )
    last_name: str | None = Field(
        None, min_length=1, max_length=100, description="User last name"
    )
    email: str | None = Field(None, description="User email address")

    @validator("email")
    def validate_email(cls, v: str | None) -> str | None:
        """Basic email validation."""
        if v is None:
            return v
        v = v.strip().lower()
        if "@" not in v or len(v) < 5:
            raise ValueError("Invalid email address")
        return v

    @validator("first_name", "last_name")
    def validate_names(cls, v: str | None) -> str | None:
        """Name validation."""
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v


class PasswordChangeRequest(BaseModel):
    """Model for password change request."""

    current_password: str = Field(..., description="Current user password")
    new_password: str = Field(..., min_length=8, description="New user password")


class AccountDeletionRequest(BaseModel):
    """Model for account deletion request."""

    current_password: str = Field(
        ..., description="Current user password for verification"
    )
    confirmation: str = Field(..., description="Confirmation text (must be 'DELETE')")
    reason: str | None = Field(
        None, max_length=500, description="Optional deletion reason"
    )

    @validator("confirmation")
    def validate_confirmation(cls, v: str) -> str:
        """Validate confirmation text."""
        if v.strip().upper() != "DELETE":
            raise ValueError("Confirmation must be exactly 'DELETE'")
        return v.strip().upper()

    @validator("reason")
    def validate_reason(cls, v: str | None) -> str | None:
        """Validate and sanitize reason."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


@auth_router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserRegistration,
    request: Request,
    auth_manager: Annotated[GeneralizedAuthManager, Depends(get_auth_manager)],
    session: AsyncDatabaseSession,
) -> TokenResponse:
    """Register a new user account."""
    try:
        # Get client IP for rate limiting
        client_ip = request.client.host if request.client else "unknown"

        # Sanitize input data
        sanitized_email = InputSanitizer.sanitize_email(user_data.email)
        sanitized_first_name = InputSanitizer.sanitize_text(
            user_data.first_name, field_name="first_name"
        )
        sanitized_last_name = InputSanitizer.sanitize_text(
            user_data.last_name, field_name="last_name"
        )

        # Validate sanitized data
        if not sanitized_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format"
            )

        # Validate password length and security (prevent DoS via extremely long passwords)
        sanitized_password = InputSanitizer.sanitize_password(user_data.password)
        if not sanitized_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet security requirements",
            )

        # Create the user (password will be hashed)
        user = await auth_manager.create_user(
            email=sanitized_email,
            password=sanitized_password,  # Password validated and will be hashed
            first_name=sanitized_first_name,
            last_name=sanitized_last_name,
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
    auth_manager: Annotated[GeneralizedAuthManager, Depends(get_auth_manager)],
    session: AsyncDatabaseSession,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> TokenResponse:
    """Login user and return JWT tokens (OAuth2 compatible endpoint)."""
    try:
        # Get client IP for rate limiting
        client_ip = request.client.host if request.client else "unknown"

        # Sanitize email input
        sanitized_email = InputSanitizer.sanitize_email(form_data.username)
        if not sanitized_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # Basic password validation to prevent DoS via extremely long passwords
        if len(form_data.password) > InputSanitizer.MAX_LENGTHS["password"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # Authenticate user
        user = await auth_manager.authenticate_user(
            email=sanitized_email,  # OAuth2 uses 'username' field for email
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
    auth_manager: Annotated[GeneralizedAuthManager, Depends(get_auth_manager)],
    session: AsyncDatabaseSession,
) -> TokenResponse:
    """Login user with JSON data (alternative to OAuth2 form)."""
    try:
        # Get client IP for rate limiting
        client_ip = request.client.host if request.client else "unknown"

        # Sanitize email input
        sanitized_email = InputSanitizer.sanitize_email(user_data.email)
        if not sanitized_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # Basic password validation to prevent DoS via extremely long passwords
        if len(user_data.password) > InputSanitizer.MAX_LENGTHS["password"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # Authenticate user
        user = await auth_manager.authenticate_user(
            email=sanitized_email,
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
        email=current_user.email or "",
        first_name=current_user.first_name or "",
        last_name=current_user.last_name or "",
        is_verified=current_user.is_verified or False,
        is_super_admin=current_user.is_super_admin or False,
        created_at=current_user.created_at.isoformat()
        if current_user.created_at
        else "",
    )


@auth_router.post("/refresh", response_model=dict[str, str])
async def refresh_access_token(
    refresh_token: str,
    auth_manager: Annotated[GeneralizedAuthManager, Depends(get_auth_manager)],
    session: AsyncDatabaseSession,
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
        ) from e


# Password reset and email verification endpoints
class PasswordResetRequest(BaseModel):
    """Model for password reset request."""

    email: str = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Model for password reset confirmation."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")


class EmailVerificationRequest(BaseModel):
    """Model for email verification request."""

    token: str = Field(..., description="Email verification token")


@auth_router.post("/request-password-reset", response_model=MessageResponse)
async def request_password_reset(
    request_data: PasswordResetRequest,
    auth_manager: Annotated[GeneralizedAuthManager, Depends(get_auth_manager)],
    session: AsyncDatabaseSession,
) -> MessageResponse:
    """Request a password reset email."""
    try:
        # Check if user exists
        user = await auth_manager.get_user_by_email(request_data.email, session)
        if not user:
            # Don't reveal if email exists or not for security
            return MessageResponse(
                success=True,
                message="If the email exists, a password reset link has been sent.",
            )

        # Generate password reset token
        reset_token = auth_manager.create_password_reset_token(user)

        # Send password reset email
        from .email_service import get_email_service

        email_service = get_email_service()

        await email_service.send_password_reset_email(
            user.email or "",
            f"{user.first_name or ''} {user.last_name or ''}",
            reset_token,
        )

        return MessageResponse(
            success=True,
            message="If the email exists, a password reset link has been sent.",
        )

    except Exception as e:
        logger.error(f"Error requesting password reset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request",
        ) from e


@auth_router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    auth_manager: Annotated[GeneralizedAuthManager, Depends(get_auth_manager)],
    session: AsyncDatabaseSession,
) -> MessageResponse:
    """Reset user password with valid token."""
    try:
        # Verify password reset token
        payload = auth_manager.verify_password_reset_token(reset_data.token)
        if payload is None or payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token",
            )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token format"
            )

        # Get user and update password
        user_id = UUID(user_id_str)
        user = await auth_manager.get_user_by_id(user_id, session)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Hash and update password
        hashed_password = auth_manager.hash_password(reset_data.new_password)
        await auth_manager.update_user_password(user_id, hashed_password, session)

        return MessageResponse(
            success=True, message="Password has been reset successfully."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password",
        ) from e


@auth_router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verification_data: EmailVerificationRequest,
    auth_manager: Annotated[GeneralizedAuthManager, Depends(get_auth_manager)],
    session: AsyncDatabaseSession,
) -> MessageResponse:
    """Verify user email address."""
    try:
        # Verify email verification token
        payload = auth_manager.verify_email_verification_token(verification_data.token)
        if payload is None or payload.get("type") != "email_verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token format"
            )

        # Get user and mark as verified
        user_id = UUID(user_id_str)
        user = await auth_manager.get_user_by_id(user_id, session)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update user verification status
        await auth_manager.verify_user_email(user_id, session)

        return MessageResponse(
            success=True, message="Email address has been verified successfully."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email",
        ) from e


@auth_router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    request_data: PasswordResetRequest,  # Reuse same model (just needs email)
    auth_manager: Annotated[GeneralizedAuthManager, Depends(get_auth_manager)],
    session: AsyncDatabaseSession,
) -> MessageResponse:
    """Resend email verification."""
    try:
        # Check if user exists
        user = await auth_manager.get_user_by_email(request_data.email, session)
        if not user:
            # Don't reveal if email exists or not for security
            return MessageResponse(
                success=True,
                message="If the email exists and is unverified, a verification link has been sent.",
            )

        # Check if user is already verified
        if user.is_verified:
            return MessageResponse(
                success=True, message="Email address is already verified."
            )

        # Generate verification token
        verification_token = auth_manager.create_email_verification_token(user)

        # Send verification email
        from .email_service import get_email_service

        email_service = get_email_service()

        await email_service.send_verification_email(
            user.email or "",
            f"{user.first_name or ''} {user.last_name or ''}",
            verification_token,
        )

        return MessageResponse(
            success=True,
            message="If the email exists and is unverified, a verification link has been sent.",
        )

    except Exception as e:
        logger.error(f"Error resending verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email",
        ) from e


@auth_router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: CurrentUser,
) -> UserResponse:
    """Get current user profile information."""
    try:
        return UserResponse(
            id=str(current_user.id),
            email=current_user.email or "",
            first_name=current_user.first_name or "",
            last_name=current_user.last_name or "",
            is_verified=current_user.is_verified or False,
            is_super_admin=current_user.is_super_admin or False,
            created_at=current_user.created_at.isoformat()
            if current_user.created_at
            else "",
        )

    except Exception as e:
        logger.error(f"Error retrieving user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile",
        ) from e


@auth_router.put("/profile", response_model=MessageResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: CurrentUser,
    auth_manager: Annotated[GeneralizedAuthManager, Depends(get_auth_manager)],
    session: AsyncDatabaseSession,
) -> MessageResponse:
    """Update user profile information."""
    try:
        # Track if email is being changed
        email_changed = False

        # Update fields that are provided
        if profile_data.first_name is not None:
            sanitized_first_name = InputSanitizer.sanitize_text(
                profile_data.first_name, field_name="first_name"
            )
            current_user.first_name = sanitized_first_name

        if profile_data.last_name is not None:
            sanitized_last_name = InputSanitizer.sanitize_text(
                profile_data.last_name, field_name="last_name"
            )
            current_user.last_name = sanitized_last_name

        if profile_data.email is not None and profile_data.email != current_user.email:
            # Validate and sanitize email
            sanitized_email = InputSanitizer.sanitize_email(profile_data.email)
            if not sanitized_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email format",
                )

            # Check if email is already taken by another user
            existing_user = await auth_manager.get_user_by_email(
                sanitized_email, session
            )
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email address is already in use",
                )

            # Update email and reset verification
            current_user.email = sanitized_email
            current_user.is_verified = False
            email_changed = True

        # Save changes
        await session.commit()

        # Send verification email if email was changed
        if email_changed:
            try:
                # Generate verification token
                verification_token = auth_manager.create_email_verification_token(
                    current_user
                )

                # Send verification email
                from .email_service import get_email_service

                email_service = get_email_service()

                await email_service.send_verification_email(
                    current_user.email or "",
                    current_user.full_name,
                    verification_token,
                )

                return MessageResponse(
                    success=True,
                    message="Profile updated successfully. Please verify your new email address.",
                )
            except Exception as email_error:
                logger.warning(f"Failed to send verification email: {email_error}")
                return MessageResponse(
                    success=True,
                    message="Profile updated successfully. Please request a verification email manually.",
                )

        return MessageResponse(success=True, message="Profile updated successfully")

    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        ) from e


@auth_router.post("/change-password", response_model=MessageResponse)
async def change_user_password(
    password_data: PasswordChangeRequest,
    current_user: CurrentUser,
    auth_manager: Annotated[GeneralizedAuthManager, Depends(get_auth_manager)],
    session: AsyncDatabaseSession,
) -> MessageResponse:
    """Change user password."""
    try:
        # Verify current password
        is_valid = auth_manager.verify_password(
            password_data.current_password, current_user.hashed_password or ""
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Sanitize and validate new password
        sanitized_new_password = InputSanitizer.sanitize_password(
            password_data.new_password
        )
        if not sanitized_new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password does not meet security requirements",
            )

        # Hash new password and update
        new_hashed_password = auth_manager.hash_password(sanitized_new_password)
        current_user.hashed_password = new_hashed_password

        # Save changes
        await session.commit()

        logger.info(f"Password changed for user: {current_user.email}")

        return MessageResponse(success=True, message="Password updated successfully")

    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        ) from e


@auth_router.delete("/account", response_model=MessageResponse)
async def delete_user_account(
    deletion_data: AccountDeletionRequest,
    current_user: CurrentUser,
    request: Request,
    auth_manager: Annotated[GeneralizedAuthManager, Depends(get_auth_manager)],
    session: AsyncDatabaseSession,
) -> MessageResponse:
    """Delete user account and all associated data (GDPR compliant)."""
    try:
        # Prevent super admin account deletion
        if current_user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin accounts cannot be deleted",
            )

        # Verify current password
        if not auth_manager.verify_password(
            deletion_data.current_password, current_user.hashed_password or ""
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Get client information for audit logging
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Collect data summary before deletion for audit purposes
        from sqlalchemy import func, select

        from .models import Vote, VoterResponse

        # Count user's votes and responses
        vote_count_result = await session.execute(
            select(func.count(Vote.id)).where(Vote.creator_id == current_user.id)
        )
        vote_count = vote_count_result.scalar() or 0

        response_count_result = await session.execute(
            select(func.count(VoterResponse.id)).where(
                VoterResponse.vote_id.in_(
                    select(Vote.id).where(Vote.creator_id == current_user.id)
                )
            )
        )
        response_count = response_count_result.scalar() or 0

        data_summary = {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "votes_created": vote_count,
            "responses_received": response_count,
            "account_created": current_user.created_at.isoformat()
            if current_user.created_at
            else None,
            "deletion_reason": deletion_data.reason or "user_requested",
        }

        # Create audit log entry before deletion
        deletion_log = AccountDeletionLog(
            deleted_user_id=current_user.id,
            deleted_user_email=current_user.email,
            deleted_user_name=current_user.full_name,
            deletion_reason="user_requested",
            deleted_by_user_id=None,  # Self-deletion
            ip_address=client_ip,
            user_agent=user_agent,
            data_summary=data_summary,
        )
        session.add(deletion_log)

        # Delete user account (cascade relationships will handle associated data)
        # This includes: votes, vote_options, voter_responses, moderation flags, etc.
        await session.delete(current_user)
        await session.commit()

        logger.info(
            f"Account deleted: {current_user.email} (ID: {current_user.id}) "
            f"from IP: {client_ip}, Reason: {deletion_data.reason or 'user_requested'}"
        )

        return MessageResponse(
            success=True,
            message="Your account and all associated data have been permanently deleted.",
        )

    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account",
        ) from e
