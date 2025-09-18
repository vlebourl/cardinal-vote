"""Dashboard statistics service for the generalized voting platform."""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .database_manager import GeneralizedDatabaseManager
from .models import User, Vote, VoterResponse

logger = logging.getLogger(__name__)


class DashboardStatsError(Exception):
    """Exception raised when dashboard statistics calculation fails."""


class DashboardService:
    """Service for calculating dashboard statistics for authenticated users."""

    def __init__(self, db_manager: GeneralizedDatabaseManager) -> None:
        """Initialize dashboard service with database manager."""
        self.db_manager = db_manager

    async def get_user_dashboard_stats(self, user_id: str) -> dict[str, Any]:
        """
        Calculate comprehensive dashboard statistics for a specific user.

        Args:
            user_id: The UUID of the user to get stats for

        Returns:
            Dictionary containing dashboard statistics matching DashboardStats schema:
            - total_votes_created: Total number of votes created by user
            - active_votes_count: Number of active (published, not closed) votes
            - total_responses_received: Total responses across all user's votes
            - recent_activity_count: Activity in last 7 days

        Raises:
            DashboardStatsError: If statistics calculation fails
        """
        try:
            async with self.db_manager.get_session() as session:
                return await self._calculate_user_stats(session, user_id)
        except Exception as e:
            logger.error(
                f"Failed to calculate dashboard stats for user {user_id}: {str(e)}"
            )
            raise DashboardStatsError(
                f"Unable to calculate dashboard statistics: {str(e)}"
            ) from e

    async def _calculate_user_stats(
        self, session: AsyncSession, user_id: str
    ) -> dict[str, Any]:
        """Calculate statistics for a user within a database session."""
        # Define time boundary for recent activity (last 7 days)
        recent_cutoff = datetime.utcnow() - timedelta(days=7)

        # Query 1: Total votes created by user
        total_votes_query = select(func.count(Vote.id)).where(
            Vote.creator_id == user_id
        )
        total_votes_result = await session.execute(total_votes_query)
        total_votes_created = total_votes_result.scalar() or 0

        # Query 2: Active votes count (published and not closed)
        active_votes_query = select(func.count(Vote.id)).where(
            and_(
                Vote.creator_id == user_id,
                Vote.is_active == True,  # noqa: E712
                Vote.is_draft == False,  # noqa: E712
                Vote.closed_at.is_(None),
            )
        )
        active_votes_result = await session.execute(active_votes_query)
        active_votes_count = active_votes_result.scalar() or 0

        # Query 3: Total responses received across all user's votes
        responses_query = (
            select(func.count(VoterResponse.id))
            .join(Vote, VoterResponse.vote_id == Vote.id)
            .where(Vote.creator_id == user_id)
        )
        responses_result = await session.execute(responses_query)
        total_responses_received = responses_result.scalar() or 0

        # Query 4: Recent activity count (votes created + responses received in last 7 days)
        recent_votes_query = select(func.count(Vote.id)).where(
            and_(Vote.creator_id == user_id, Vote.created_at >= recent_cutoff)
        )
        recent_votes_result = await session.execute(recent_votes_query)
        recent_votes_count = recent_votes_result.scalar() or 0

        recent_responses_query = (
            select(func.count(VoterResponse.id))
            .join(Vote, VoterResponse.vote_id == Vote.id)
            .where(
                and_(
                    Vote.creator_id == user_id,
                    VoterResponse.submitted_at >= recent_cutoff,
                )
            )
        )
        recent_responses_result = await session.execute(recent_responses_query)
        recent_responses_count = recent_responses_result.scalar() or 0

        recent_activity_count = recent_votes_count + recent_responses_count

        return {
            "total_votes_created": total_votes_created,
            "active_votes_count": active_votes_count,
            "total_responses_received": total_responses_received,
            "recent_activity_count": recent_activity_count,
        }

    async def get_user_vote_summary(
        self, user_id: str, limit: int = 10
    ) -> dict[str, Any]:
        """
        Get a summary of user's recent votes for dashboard display.

        Args:
            user_id: The UUID of the user
            limit: Maximum number of recent votes to return

        Returns:
            Dictionary containing recent votes summary
        """
        try:
            async with self.db_manager.get_session() as session:
                # Get user's most recent votes with basic stats
                votes_query = (
                    select(
                        Vote.id,
                        Vote.title,
                        Vote.is_draft,
                        Vote.is_active,
                        Vote.created_at,
                        Vote.published_at,
                        Vote.closed_at,
                        func.count(VoterResponse.id).label("response_count"),
                    )
                    .outerjoin(VoterResponse, Vote.id == VoterResponse.vote_id)
                    .where(Vote.creator_id == user_id)
                    .group_by(Vote.id)
                    .order_by(Vote.created_at.desc())
                    .limit(limit)
                )

                result = await session.execute(votes_query)
                votes = result.fetchall()

                return {
                    "recent_votes": [
                        {
                            "id": str(vote.id),
                            "title": vote.title,
                            "is_draft": vote.is_draft,
                            "is_active": vote.is_active,
                            "created_at": vote.created_at.isoformat()
                            if vote.created_at
                            else None,
                            "published_at": vote.published_at.isoformat()
                            if vote.published_at
                            else None,
                            "closed_at": vote.closed_at.isoformat()
                            if vote.closed_at
                            else None,
                            "response_count": vote.response_count or 0,
                        }
                        for vote in votes
                    ]
                }
        except Exception as e:
            logger.error(f"Failed to get vote summary for user {user_id}: {str(e)}")
            raise DashboardStatsError(f"Unable to get vote summary: {str(e)}") from e

    async def get_platform_stats(self) -> dict[str, Any]:
        """
        Get platform-wide statistics (for super admin dashboard).

        Returns:
            Dictionary containing platform statistics
        """
        try:
            async with self.db_manager.get_session() as session:
                # Total users
                users_query = select(func.count(User.id))
                users_result = await session.execute(users_query)
                total_users = users_result.scalar() or 0

                # Total votes
                votes_query = select(func.count(Vote.id))
                votes_result = await session.execute(votes_query)
                total_votes = votes_result.scalar() or 0

                # Active votes
                active_votes_query = select(func.count(Vote.id)).where(
                    and_(
                        Vote.is_active == True,  # noqa: E712
                        Vote.is_draft == False,  # noqa: E712
                        Vote.closed_at.is_(None),
                    )
                )
                active_votes_result = await session.execute(active_votes_query)
                active_votes = active_votes_result.scalar() or 0

                # Total responses
                responses_query = select(func.count(VoterResponse.id))
                responses_result = await session.execute(responses_query)
                total_responses = responses_result.scalar() or 0

                return {
                    "total_users": total_users,
                    "total_votes": total_votes,
                    "active_votes": active_votes,
                    "total_responses": total_responses,
                }
        except Exception as e:
            logger.error(f"Failed to get platform stats: {str(e)}")
            raise DashboardStatsError(
                f"Unable to get platform statistics: {str(e)}"
            ) from e
