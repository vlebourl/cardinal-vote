"""FastAPI dependencies for the generalized voting platform."""

import logging
from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .auth_manager import GeneralizedAuthManager
from .database_manager import GeneralizedDatabaseManager
from .models import User
from .session_manager import session_manager

logger = logging.getLogger(__name__)

# OAuth2 scheme for JWT tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", scheme_name="JWT")

# Global manager instances (will be initialized in main.py)
generalized_auth_manager: GeneralizedAuthManager | None = None
generalized_db_manager: GeneralizedDatabaseManager | None = None


def get_auth_manager() -> GeneralizedAuthManager:
    """Dependency to get the generalized authentication manager."""
    if generalized_auth_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication manager not initialized",
        )
    return generalized_auth_manager


def get_generalized_db_manager() -> GeneralizedDatabaseManager:
    """Dependency to get the generalized database manager."""
    if generalized_db_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Generalized database manager not initialized",
        )
    return generalized_db_manager


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get an async database session."""
    db_manager = get_generalized_db_manager()
    async with db_manager.get_session() as session:
        yield session


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_manager: Annotated[GeneralizedAuthManager, Depends(get_auth_manager)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    Raises HTTPException if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify and decode the token
        payload = auth_manager.verify_token(token)
        if payload is None:
            raise credentials_exception

        # Extract user ID from token
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise credentials_exception from None

        # Get user from database
        user = await auth_manager.get_user_by_id(user_id, session)
        if user is None:
            raise credentials_exception

        # Set multi-tenant session context for Row-Level Security
        await session_manager.set_session_context(session, user)

        return user

    except Exception as e:
        logger.error(f"Error in get_current_user dependency: {e}")
        raise credentials_exception from e


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency to get the current active user.
    For now, just returns the user. Can be extended for user status checks.
    """
    # Future: add checks for user.is_active, is_verified, etc.
    return current_user


async def get_current_super_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Dependency to get the current user and verify they are a super admin.
    Raises HTTPException if user is not a super admin.
    """
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required"
        )
    return current_user


async def get_optional_current_user(
    auth_manager: Annotated[GeneralizedAuthManager, Depends(get_auth_manager)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token: str | None = Depends(oauth2_scheme),
) -> User | None:
    """
    Dependency to optionally get the current user.
    Returns None if no token or invalid token (does not raise exception).
    Useful for endpoints that work with or without authentication.
    """
    if token is None:
        return None

    try:
        # Verify and decode the token
        payload = auth_manager.verify_token(token)
        if payload is None:
            return None

        # Extract user ID from token
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None

        try:
            user_id = UUID(user_id_str)
        except ValueError:
            return None

        # Get user from database
        user = await auth_manager.get_user_by_id(user_id, session)
        if user is not None:
            # Set multi-tenant session context for Row-Level Security
            await session_manager.set_session_context(session, user)

        return user

    except Exception as e:
        logger.warning(f"Error in get_optional_current_user dependency: {e}")
        return None


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentSuperAdmin = Annotated[User, Depends(get_current_super_admin)]
OptionalCurrentUser = Annotated[User | None, Depends(get_optional_current_user)]
AsyncDatabaseSession = Annotated[AsyncSession, Depends(get_async_session)]
