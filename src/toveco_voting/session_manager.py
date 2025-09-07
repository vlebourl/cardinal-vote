"""Multi-tenant session management for the generalized voting platform."""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User

logger = logging.getLogger(__name__)


class MultiTenantSessionManager:
    """
    Manages multi-tenant sessions with PostgreSQL Row-Level Security integration.

    This class handles:
    - Setting PostgreSQL session context for RLS policies
    - Managing user sessions across requests
    - Integrating with JWT authentication
    - Providing multi-tenant isolation
    """

    def __init__(self):
        """Initialize the session manager."""
        self.session_contexts: dict[str, dict[str, Any]] = {}
        logger.info("Multi-tenant session manager initialized")

    async def set_session_context(self, session: AsyncSession, user: User) -> None:
        """
        Set PostgreSQL session context for RLS policies.

        This function calls the set_session_context() PostgreSQL function
        created in the database initialization script to set the current
        user context for Row-Level Security policies.

        Args:
            session: The database session
            user: The authenticated user
        """
        try:
            # Set the session context in PostgreSQL
            await session.execute(
                text("SELECT set_session_context(:user_id, :is_super_admin);"),
                {"user_id": str(user.id), "is_super_admin": user.is_super_admin},
            )
            logger.debug(
                f"Set session context for user {user.id} (super_admin: {user.is_super_admin})"
            )

        except Exception as e:
            logger.error(f"Failed to set session context for user {user.id}: {e}")
            raise

    async def clear_session_context(self, session: AsyncSession) -> None:
        """
        Clear PostgreSQL session context.

        This removes the user context from the PostgreSQL session,
        which will cause RLS policies to deny access to protected resources.

        Args:
            session: The database session
        """
        try:
            # Clear the session context in PostgreSQL
            await session.execute(text("SELECT set_session_context(NULL, FALSE);"))
            logger.debug("Cleared session context")

        except Exception as e:
            logger.error(f"Failed to clear session context: {e}")
            # Don't raise here as this is cleanup

    async def get_session_info(self, session: AsyncSession) -> dict[str, Any]:
        """
        Get current session information from PostgreSQL.

        Returns the current user context and session details
        that are active in the PostgreSQL session.

        Args:
            session: The database session

        Returns:
            Dictionary with session information
        """
        try:
            # Get current session context
            result = await session.execute(
                text("SELECT current_user_id(), is_super_admin();")
            )
            row = result.fetchone()

            if row:
                user_id_str, is_admin = row
                return {
                    "user_id": user_id_str,
                    "is_super_admin": is_admin,
                    "has_context": user_id_str is not None,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                return {
                    "user_id": None,
                    "is_super_admin": False,
                    "has_context": False,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return {
                "error": str(e),
                "has_context": False,
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def validate_session_context(
        self, session: AsyncSession, expected_user_id: uuid.UUID
    ) -> bool:
        """
        Validate that the current session context matches the expected user.

        This is a security check to ensure that the PostgreSQL session
        context is correctly set for the authenticated user.

        Args:
            session: The database session
            expected_user_id: The UUID of the expected user

        Returns:
            True if session context matches, False otherwise
        """
        try:
            session_info = await self.get_session_info(session)

            if not session_info.get("has_context"):
                logger.warning("Session context validation failed: no context set")
                return False

            current_user_id_str = session_info.get("user_id")
            if not current_user_id_str:
                logger.warning("Session context validation failed: no user ID")
                return False

            current_user_id = uuid.UUID(current_user_id_str)
            if current_user_id != expected_user_id:
                logger.warning(
                    f"Session context validation failed: expected {expected_user_id}, "
                    f"got {current_user_id}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Session context validation error: {e}")
            return False

    def create_session_token(self, user_id: uuid.UUID) -> str:
        """
        Create a session token for tracking user sessions.

        This is separate from JWT tokens and used for internal
        session management and context correlation.

        Args:
            user_id: The user's UUID

        Returns:
            A session token string
        """
        session_token = f"session_{uuid.uuid4().hex}"

        # Store session context info (in-memory for now)
        self.session_contexts[session_token] = {
            "user_id": str(user_id),
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
        }

        logger.debug(f"Created session token for user {user_id}")
        return session_token

    def get_session_context_info(self, session_token: str) -> dict[str, Any] | None:
        """
        Get session context information by token.

        Args:
            session_token: The session token

        Returns:
            Session context information or None if not found
        """
        context = self.session_contexts.get(session_token)
        if context:
            # Update last accessed time
            context["last_accessed"] = datetime.utcnow()

        return context

    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up expired session contexts.

        Args:
            max_age_hours: Maximum age in hours for session contexts

        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired_tokens = []

        for token, context in self.session_contexts.items():
            if context["last_accessed"] < cutoff_time:
                expired_tokens.append(token)

        for token in expired_tokens:
            del self.session_contexts[token]

        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired session contexts")

        return len(expired_tokens)

    async def test_rls_isolation(self, session: AsyncSession) -> dict[str, Any]:
        """
        Test Row-Level Security isolation for the current session.

        This method performs test queries to verify that RLS policies
        are working correctly for the current session context.

        Args:
            session: The database session

        Returns:
            Test results dictionary
        """
        try:
            results = {}

            # Test current session context
            session_info = await self.get_session_info(session)
            results["session_context"] = session_info

            # Test user table access
            try:
                result = await session.execute(text("SELECT COUNT(*) FROM users;"))
                user_count = result.scalar_one()
                results["users_accessible"] = user_count
            except Exception as e:
                results["users_error"] = str(e)

            # Test generalized_votes table access
            try:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM generalized_votes;")
                )
                votes_count = result.scalar_one()
                results["votes_accessible"] = votes_count
            except Exception as e:
                results["votes_error"] = str(e)

            # Test vote_options table access
            try:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM vote_options;")
                )
                options_count = result.scalar_one()
                results["options_accessible"] = options_count
            except Exception as e:
                results["options_error"] = str(e)

            # Test voter_responses table access
            try:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM voter_responses;")
                )
                responses_count = result.scalar_one()
                results["responses_accessible"] = responses_count
            except Exception as e:
                results["responses_error"] = str(e)

            results["test_completed"] = True
            results["timestamp"] = datetime.utcnow().isoformat()

            return results

        except Exception as e:
            logger.error(f"RLS isolation test failed: {e}")
            return {
                "test_completed": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# Global session manager instance
session_manager = MultiTenantSessionManager()
