"""JWT authentication system for the generalized voting platform."""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from .config import settings
from .models import DatabaseError, User

logger = logging.getLogger(__name__)


class GeneralizedAuthManager:
    """Manages JWT authentication and user management for the generalized platform."""

    def __init__(self) -> None:
        """Initialize the generalized authentication manager."""
        # Use the same bcrypt context as AdminAuthManager for consistency
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._login_attempts: dict[str, list[datetime]] = {}

        # JWT configuration - use environment variables with fallbacks
        self.jwt_secret_key = getattr(
            settings, "JWT_SECRET_KEY", "jwt_secret_key_change_in_production"
        )
        self.jwt_algorithm = getattr(settings, "JWT_ALGORITHM", "HS256")
        self.jwt_access_token_expire_minutes = getattr(
            settings, "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30
        )

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt (same pattern as AdminAuthManager)."""
        salt = bcrypt.gensalt()
        hashed_bytes: bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed_bytes.decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash (same pattern as AdminAuthManager)."""
        try:
            result: bool = bcrypt.checkpw(
                password.encode("utf-8"), hashed.encode("utf-8")
            )
            return result
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def _check_rate_limit(self, ip_address: str) -> bool:
        """Check if the IP address has exceeded login attempt rate limit."""
        now = datetime.utcnow()
        cutoff = now - timedelta(
            minutes=getattr(settings, "LOGIN_ATTEMPT_WINDOW_MINUTES", 15)
        )

        if ip_address not in self._login_attempts:
            self._login_attempts[ip_address] = []

        # Remove old attempts
        self._login_attempts[ip_address] = [
            attempt for attempt in self._login_attempts[ip_address] if attempt > cutoff
        ]

        # Check if under limit
        max_attempts = getattr(settings, "MAX_LOGIN_ATTEMPTS", 5)
        return len(self._login_attempts[ip_address]) < max_attempts

    def _record_login_attempt(self, ip_address: str) -> None:
        """Record a failed login attempt."""
        if ip_address not in self._login_attempts:
            self._login_attempts[ip_address] = []

        self._login_attempts[ip_address].append(datetime.utcnow())

    def create_access_token(
        self, data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """Create JWT access token with user data."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.jwt_access_token_expire_minutes
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, self.jwt_secret_key, algorithm=self.jwt_algorithm
        )
        return str(encoded_jwt)

    def create_refresh_token(self, data: dict[str, Any]) -> str:
        """Create JWT refresh token with longer expiration."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)  # Refresh tokens last 7 days
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode, self.jwt_secret_key, algorithm=self.jwt_algorithm
        )
        return str(encoded_jwt)

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token, self.jwt_secret_key, algorithms=[self.jwt_algorithm]
            )
            return dict(payload) if payload else None
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None

    async def authenticate_user(
        self, email: str, password: str, ip_address: str, session: AsyncSession
    ) -> User | None:
        """
        Authenticate a user and return User object if successful.
        Follows the same pattern as AdminAuthManager.authenticate_user
        """
        try:
            # Check rate limiting
            if not self._check_rate_limit(ip_address):
                logger.warning(f"Rate limit exceeded for IP: {ip_address}")
                return None

            # Find user by email (case-insensitive)
            result = await session.execute(
                select(User).where(User.email == email.lower().strip())
            )
            user = result.scalar_one_or_none()

            if (
                not user
                or not user.hashed_password
                or not self.verify_password(password, user.hashed_password)
            ):
                self._record_login_attempt(ip_address)
                logger.warning(f"Failed login attempt for {email} from {ip_address}")
                return None

            # Update user's last login
            user.last_login = datetime.utcnow()
            await session.commit()

            logger.info(f"Successful login for {email} from {ip_address}")
            return user

        except SQLAlchemyError as e:
            logger.error(f"Authentication error: {e}")
            await session.rollback()
            return None

    async def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        session: AsyncSession,
    ) -> User:
        """Create a new user account."""
        try:
            # Check if user already exists
            result = await session.execute(
                select(User).where(User.email == email.lower().strip())
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                raise DatabaseError(f"User with email {email} already exists")

            # Create new user
            hashed_password = self.hash_password(password)
            user = User(
                email=email.lower().strip(),
                hashed_password=hashed_password,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                is_verified=False,  # Email verification will be handled separately
                is_super_admin=False,
            )

            session.add(user)
            await session.commit()
            await session.refresh(user)

            logger.info(f"User created successfully: {email}")
            return user

        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Failed to create user {email}: {e}")
            raise DatabaseError(f"Failed to create user: {e}") from e

    async def get_user_by_id(self, user_id: UUID, session: AsyncSession) -> User | None:
        """Get user by ID."""
        try:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None

    async def get_user_by_email(self, email: str, session: AsyncSession) -> User | None:
        """Get user by email."""
        try:
            result = await session.execute(
                select(User).where(User.email == email.lower().strip())
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None

    def create_tokens(self, user: User) -> dict[str, str]:
        """Create both access and refresh tokens for a user."""
        user_data = {
            "sub": str(user.id),
            "email": user.email,
            "is_super_admin": user.is_super_admin,
        }

        access_token = self.create_access_token(user_data)
        refresh_token = self.create_refresh_token({"sub": str(user.id)})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def set_session_context(
        self, user_id: UUID, is_super_admin: bool, session: AsyncSession
    ) -> None:
        """Set PostgreSQL session context for Row-Level Security."""
        try:
            await session.execute(
                text("SELECT set_session_context(:user_id, :is_super_admin)"),
                {"user_id": str(user_id), "is_super_admin": is_super_admin},
            )
        except SQLAlchemyError as e:
            logger.error(f"Failed to set session context: {e}")
            # Don't raise - this is not critical for basic operation

    def create_password_reset_token(self, user: User) -> str:
        """Create a password reset token for a user."""
        token_data = {
            "sub": str(user.id),
            "type": "password_reset",
            "iat": datetime.utcnow().timestamp(),
        }
        # Password reset tokens expire in 1 hour
        expires = timedelta(hours=1)
        return self.create_access_token(token_data, expires_delta=expires)

    def verify_password_reset_token(self, token: str) -> dict[str, Any] | None:
        """Verify a password reset token and return user data if valid."""
        payload = self.verify_token(token)
        if not payload:
            return None

        # Verify it's a password reset token
        if payload.get("type") != "password_reset":
            logger.warning("Invalid token type for password reset")
            return None

        return payload

    def create_email_verification_token(self, user: User) -> str:
        """Create an email verification token for a user."""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "type": "email_verification",
            "iat": datetime.utcnow().timestamp(),
        }
        # Email verification tokens expire in 24 hours
        expires = timedelta(hours=24)
        return self.create_access_token(token_data, expires_delta=expires)

    def verify_email_verification_token(self, token: str) -> dict[str, Any] | None:
        """Verify an email verification token and return user data if valid."""
        payload = self.verify_token(token)
        if not payload:
            return None

        # Verify it's an email verification token
        if payload.get("type") != "email_verification":
            logger.warning("Invalid token type for email verification")
            return None

        return payload

    async def update_user_password(
        self, user_id: UUID, new_password: str, session: AsyncSession
    ) -> bool:
        """Update user password."""
        try:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"User {user_id} not found for password update")
                return False

            # Hash the new password
            hashed_password = self.hash_password(new_password)
            user.hashed_password = hashed_password

            await session.commit()
            logger.info(f"Password updated for user {user_id}")
            return True

        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Failed to update password for user {user_id}: {e}")
            return False

    async def verify_user_email(self, user_id: UUID, session: AsyncSession) -> bool:
        """Mark user's email as verified."""
        try:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"User {user_id} not found for email verification")
                return False

            # Mark as verified
            user.is_verified = True

            await session.commit()
            logger.info(f"Email verified for user {user_id}")
            return True

        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Failed to verify email for user {user_id}: {e}")
            return False

    async def create_initial_super_admin(self, session: AsyncSession) -> None:
        """Create initial super admin user if it doesn't exist."""
        try:
            super_admin_email = getattr(
                settings, "SUPER_ADMIN_EMAIL", "admin@voting-platform.local"
            )
            super_admin_password = getattr(
                settings,
                "SUPER_ADMIN_PASSWORD",
                "super_admin_password_change_in_production",
            )

            # Check if super admin already exists
            result = await session.execute(
                select(User).where(User.email == super_admin_email)
            )
            existing_admin = result.scalar_one_or_none()

            if not existing_admin:
                # Create super admin user
                hashed_password = self.hash_password(super_admin_password)
                admin_user = User(
                    email=super_admin_email,
                    hashed_password=hashed_password,
                    first_name="Platform",
                    last_name="Administrator",
                    is_verified=True,
                    is_super_admin=True,
                )

                session.add(admin_user)
                await session.commit()
                logger.info(f"Created initial super admin user: {super_admin_email}")
            else:
                logger.info(f"Super admin user already exists: {super_admin_email}")

        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Failed to create initial super admin: {e}")
            # Don't raise - this is initialization, not critical for operation
