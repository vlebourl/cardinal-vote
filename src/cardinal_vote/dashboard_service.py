"""Dashboard statistics service for the generalized voting platform."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .database_manager import GeneralizedDatabaseManager
from .models import (
    Dashboard,
    Notification,
    Statistics,
    User,
    UserActivity,
    Vote,
    VoteOption,
    VoterResponse,
)

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

    async def get_dashboard_overview(self, user: User) -> Dict[str, Any]:
        """
        Get complete dashboard overview for a user.
        This corresponds to the GET /api/dashboard endpoint.
        Returns data matching DashboardOverviewResponse model.
        """
        try:
            async with self.db_manager.get_session() as session:
                # Get user's vote counts by status for quick_stats
                my_votes_query = (
                    select(Vote.status, func.count(Vote.id).label("count"))
                    .where(Vote.creator_id == str(user.id))
                    .group_by(Vote.status)
                )
                my_votes_result = await session.execute(my_votes_query)
                vote_counts = {
                    row.status: row.count for row in my_votes_result.fetchall()
                }

                # Get user's participation data
                participation_query = select(func.count(VoterResponse.id)).where(
                    VoterResponse.user_id == user.id
                )
                participation_result = await session.execute(participation_query)
                votes_participated = participation_result.scalar() or 0

                # Get pending votes count
                participated_vote_ids_query = select(VoterResponse.vote_id).where(
                    VoterResponse.user_id == user.id
                )
                participated_vote_ids_result = await session.execute(
                    participated_vote_ids_query
                )
                participated_vote_ids = [
                    row[0] for row in participated_vote_ids_result.fetchall()
                ]

                pending_votes_query = select(func.count(Vote.id)).where(
                    and_(
                        Vote.status == "active",
                        Vote.creator_id != str(user.id),
                        ~Vote.id.in_(participated_vote_ids)
                        if participated_vote_ids
                        else True,
                    )
                )
                pending_votes_result = await session.execute(pending_votes_query)
                pending_votes = pending_votes_result.scalar() or 0

                # Get recent votes created by user (for recent_votes)
                recent_votes_query = (
                    select(Vote)
                    .where(Vote.creator_id == str(user.id))
                    .order_by(desc(Vote.created_at))
                    .limit(5)
                )
                recent_votes_result = await session.execute(recent_votes_query)
                recent_votes_data = recent_votes_result.scalars().all()

                recent_votes = []
                for vote in recent_votes_data:
                    # Get response count for each vote
                    response_count_query = select(func.count(VoterResponse.id)).where(
                        VoterResponse.vote_id == vote.id
                    )
                    response_count_result = await session.execute(response_count_query)
                    response_count = response_count_result.scalar() or 0

                    recent_votes.append(
                        {
                            "id": str(vote.id),
                            "title": vote.title,
                            "status": vote.status,
                            "created_at": vote.created_at.isoformat()
                            if vote.created_at
                            else None,
                            "response_count": response_count,
                        }
                    )

                # Get available votes (active votes user hasn't participated in)
                available_votes_query = (
                    select(Vote)
                    .where(
                        and_(
                            Vote.status == "active",
                            Vote.creator_id != str(user.id),
                            ~Vote.id.in_(participated_vote_ids)
                            if participated_vote_ids
                            else True,
                        )
                    )
                    .order_by(desc(Vote.created_at))
                    .limit(5)
                )
                available_votes_result = await session.execute(available_votes_query)
                available_votes_data = available_votes_result.scalars().all()

                available_votes = []
                for vote in available_votes_data:
                    available_votes.append(
                        {
                            "id": str(vote.id),
                            "title": vote.title,
                            "status": vote.status,
                            "created_at": vote.created_at.isoformat()
                            if vote.created_at
                            else None,
                            "creator_email": "Anonymous",  # Could be enhanced to show creator info
                        }
                    )

                # Return data matching DashboardOverviewResponse model
                return {
                    "quick_stats": {
                        "votes_created": sum(vote_counts.values()),
                        "active_votes": vote_counts.get("active", 0),
                        "draft_votes": vote_counts.get("draft", 0),
                        "closed_votes": vote_counts.get("closed", 0),
                        "votes_participated": votes_participated,
                        "pending_votes": pending_votes,
                    },
                    "recent_votes": recent_votes,
                    "available_votes": available_votes,
                    "notifications": [
                        {
                            "id": "welcome",
                            "type": "info",
                            "message": "Welcome to the Generalized Voting Platform!",
                            "created_at": datetime.utcnow().isoformat(),
                            "read": False,
                        }
                    ],  # Placeholder notifications
                    "user_activity": {
                        "last_login": datetime.utcnow().isoformat(),
                        "total_logins": 1,
                        "account_created": user.created_at.isoformat()
                        if user.created_at
                        else None,
                    },
                }

        except Exception as e:
            logger.error(f"Error getting dashboard overview for user {user.id}: {e}")
            raise DashboardStatsError(
                f"Unable to get dashboard overview: {str(e)}"
            ) from e

    async def get_dashboard_statistics_by_scope(
        self, user: User, scope: str = "user"
    ) -> Dict[str, Any]:
        """
        Get dashboard statistics for user or system scope.
        This corresponds to the GET /api/dashboard/stats endpoint.
        """
        try:
            async with self.db_manager.get_session() as session:
                if scope == "user":
                    return await self._get_user_statistics(user, session)
                elif scope == "system":
                    # Only super admins can access system statistics
                    user_role = getattr(user, "role", "user")
                    if not (user.is_super_admin or user_role == "super_admin"):
                        raise PermissionError(
                            "System statistics require admin privileges"
                        )

                    return await self._get_system_statistics(session)
                else:
                    raise ValueError(f"Invalid scope: {scope}")

        except Exception as e:
            logger.error(
                f"Error getting dashboard statistics for user {user.id}, scope {scope}: {e}"
            )
            raise DashboardStatsError(
                f"Unable to get dashboard statistics: {str(e)}"
            ) from e

    async def get_user_votes_list(
        self, user: User, status: str = "all", limit: int = 20, offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get user's votes with filtering and pagination.
        This corresponds to the GET /api/dashboard/votes endpoint.
        """
        try:
            async with self.db_manager.get_session() as session:
                # Build query for user's votes
                query = select(Vote).where(Vote.creator_id == str(user.id))

                # Apply status filter
                if status != "all":
                    query = query.where(Vote.status == status)

                # Apply ordering and pagination
                query = (
                    query.order_by(desc(Vote.updated_at)).limit(limit).offset(offset)
                )

                # Execute query with vote options loaded
                query = query.options(selectinload(Vote.options))
                result = await session.execute(query)
                votes = result.scalars().all()

                # Get response counts for each vote
                vote_data = []
                for vote in votes:
                    response_count_query = select(func.count(VoterResponse.id)).where(
                        VoterResponse.vote_id == vote.id
                    )
                    response_count_result = await session.execute(response_count_query)
                    response_count = response_count_result.scalar() or 0

                    vote_data.append(
                        {
                            "id": str(vote.id),
                            "title": vote.title,
                            "status": vote.status,
                            "created_at": vote.created_at.isoformat()
                            if vote.created_at
                            else None,
                            "response_count": response_count,
                            "is_owner": True,  # Always true for this endpoint
                        }
                    )

                # Get total count for pagination
                count_query = select(func.count(Vote.id)).where(
                    Vote.creator_id == str(user.id)
                )
                if status != "all":
                    count_query = count_query.where(Vote.status == status)

                total_result = await session.execute(count_query)
                total = total_result.scalar() or 0

                return {
                    "votes": vote_data,
                    "pagination": {
                        "total": total,
                        "has_more": (offset + len(votes)) < total,
                        "limit": limit,
                        "offset": offset,
                        "current_page": (offset // limit) + 1,
                        "total_pages": (total + limit - 1) // limit,
                    },
                }

        except Exception as e:
            logger.error(f"Error getting user votes for user {user.id}: {e}")
            raise DashboardStatsError(f"Unable to get user votes: {str(e)}") from e

    async def get_vote_details(self, vote_id: UUID, user: User) -> Dict[str, Any]:
        """
        Get detailed information about a specific vote.
        This corresponds to the GET /api/dashboard/votes/{vote_id} endpoint.
        """
        try:
            async with self.db_manager.get_session() as session:
                # Get vote with options
                query = (
                    select(Vote)
                    .where(Vote.id == vote_id)
                    .options(selectinload(Vote.options))
                )
                result = await session.execute(query)
                vote = result.scalar_one_or_none()

                if not vote:
                    raise ValueError(f"Vote {vote_id} not found")

                # Check if user has permission to view this vote
                user_role = getattr(user, "role", "user")
                is_admin = user.is_super_admin or user_role == "super_admin"

                if not (str(vote.creator_id) == str(user.id) or is_admin):
                    raise PermissionError("You don't have permission to view this vote")

                # Get vote statistics
                stats_query = select(func.count(VoterResponse.id)).where(
                    VoterResponse.vote_id == vote_id
                )
                stats_result = await session.execute(stats_query)
                total_responses = stats_result.scalar() or 0

                # Calculate completion rate (simplified)
                completion_rate = 100.0 if total_responses > 0 else 0.0

                return {
                    "id": str(vote.id),
                    "title": vote.title,
                    "description": vote.description,
                    "status": vote.status,
                    "created_at": vote.created_at.isoformat()
                    if vote.created_at
                    else None,
                    "updated_at": vote.updated_at.isoformat()
                    if vote.updated_at
                    else None,
                    "starts_at": vote.starts_at.isoformat() if vote.starts_at else None,
                    "ends_at": vote.ends_at.isoformat() if vote.ends_at else None,
                    "options": [
                        {
                            "id": str(option.id),
                            "title": option.title,
                            "content_type": option.option_type,
                            "display_order": option.display_order,
                        }
                        for option in sorted(
                            vote.options, key=lambda x: x.display_order
                        )
                    ],
                    "stats": {
                        "total_responses": total_responses,
                        "completion_rate": completion_rate,
                        "avg_rating": 0.0,  # Would need more complex calculation
                    },
                }

        except Exception as e:
            logger.error(
                f"Error getting vote details for vote {vote_id}, user {user.id}: {e}"
            )
            raise DashboardStatsError(f"Unable to get vote details: {str(e)}") from e

    async def get_available_votes(
        self, user: User, limit: int = 20, offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get votes available for user participation.
        This corresponds to the GET /api/dashboard/available-votes endpoint.
        """
        try:
            async with self.db_manager.get_session() as session:
                # Get votes user has already participated in
                participated_query = select(VoterResponse.vote_id).where(
                    VoterResponse.user_id == user.id
                )
                participated_result = await session.execute(participated_query)
                participated_vote_ids = [
                    row[0] for row in participated_result.fetchall()
                ]

                # Get active votes user hasn't participated in (excluding their own)
                query = (
                    select(Vote)
                    .where(
                        and_(
                            Vote.status == "active",
                            Vote.creator_id != str(user.id),
                            ~Vote.id.in_(participated_vote_ids)
                            if participated_vote_ids
                            else True,
                        )
                    )
                    .order_by(desc(Vote.created_at))
                    .limit(limit)
                    .offset(offset)
                )

                result = await session.execute(query)
                votes = result.scalars().all()

                vote_data = []
                for vote in votes:
                    vote_data.append(
                        {
                            "id": str(vote.id),
                            "title": vote.title,
                            "status": vote.status,
                            "created_at": vote.created_at.isoformat()
                            if vote.created_at
                            else None,
                            "response_count": 0,  # Could be calculated if needed
                            "is_owner": False,
                        }
                    )

                # Get total count for pagination
                count_query = select(func.count(Vote.id)).where(
                    and_(
                        Vote.status == "active",
                        Vote.creator_id != str(user.id),
                        ~Vote.id.in_(participated_vote_ids)
                        if participated_vote_ids
                        else True,
                    )
                )
                total_result = await session.execute(count_query)
                total = total_result.scalar() or 0

                return {
                    "votes": vote_data,
                    "pagination": {
                        "total": total,
                        "has_more": (offset + len(votes)) < total,
                        "limit": limit,
                        "offset": offset,
                        "current_page": (offset // limit) + 1,
                        "total_pages": (total + limit - 1) // limit,
                    },
                }

        except Exception as e:
            logger.error(f"Error getting available votes for user {user.id}: {e}")
            raise DashboardStatsError(f"Unable to get available votes: {str(e)}") from e

    async def _get_user_statistics(
        self, user: User, session: AsyncSession
    ) -> Dict[str, Any]:
        """Get statistics for a specific user."""
        # Get votes created by user
        votes_created_query = select(func.count(Vote.id)).where(
            Vote.creator_id == str(user.id)
        )
        votes_created_result = await session.execute(votes_created_query)
        votes_created = votes_created_result.scalar() or 0

        # Get votes user participated in
        votes_participated_query = select(func.count(VoterResponse.id)).where(
            VoterResponse.user_id == user.id
        )
        votes_participated_result = await session.execute(votes_participated_query)
        votes_participated = votes_participated_result.scalar() or 0

        # Get total responses to user's votes
        total_responses_query = (
            select(func.count(VoterResponse.id))
            .select_from(VoterResponse)
            .join(Vote, VoterResponse.vote_id == Vote.id)
            .where(Vote.creator_id == str(user.id))
        )
        total_responses_result = await session.execute(total_responses_query)
        total_responses = total_responses_result.scalar() or 0

        # Calculate average response rate (simplified)
        avg_response_rate = 0.0
        if votes_created > 0:
            avg_response_rate = (
                (total_responses / votes_created) if votes_created > 0 else 0.0
            )

        return {
            "votes_created": votes_created,
            "votes_participated": votes_participated,
            "total_responses": total_responses,
            "avg_response_rate": round(avg_response_rate, 2),
        }

    async def _get_system_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """Get system-wide statistics (admin only)."""
        # Get total users
        total_users_query = select(func.count(User.id))
        total_users_result = await session.execute(total_users_query)
        total_users = total_users_result.scalar() or 0

        # Get total votes
        total_votes_query = select(func.count(Vote.id))
        total_votes_result = await session.execute(total_votes_query)
        total_votes = total_votes_result.scalar() or 0

        # Get total responses
        total_responses_query = select(func.count(VoterResponse.id))
        total_responses_result = await session.execute(total_responses_query)
        total_responses = total_responses_result.scalar() or 0

        # Calculate system average response rate
        avg_response_rate = 0.0
        if total_votes > 0:
            avg_response_rate = (
                (total_responses / total_votes) if total_votes > 0 else 0.0
            )

        return {
            "votes_created": total_votes,
            "votes_participated": total_responses,  # Total participation events
            "total_responses": total_responses,
            "avg_response_rate": round(avg_response_rate, 2),
        }

    async def _get_recent_activity(
        self, user_id: UUID, session: AsyncSession, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent activity for a user."""
        try:
            # For now, return mock recent activity since UserActivity might not have data yet
            # In a full implementation, this would query the UserActivity table
            return [
                {
                    "type": "dashboard_viewed",
                    "description": "Viewed dashboard",
                    "created_at": datetime.utcnow().isoformat(),
                    "entity_id": None,
                }
            ]

        except Exception as e:
            logger.error(f"Error getting recent activity for user {user_id}: {e}")
            return []

    async def get_recent_activity(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent activity for a user (public method)."""
        try:
            async with self.db_manager.get_session() as session:
                return await self._get_recent_activity(UUID(user_id), session, limit)
        except Exception as e:
            logger.error(f"Error getting recent activity for user {user_id}: {e}")
            return []
