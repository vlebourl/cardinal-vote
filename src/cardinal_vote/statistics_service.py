"""
Statistics Service for Cardinal Vote.

This service handles aggregation and calculation of various statistics
including vote metrics, user analytics, and system-wide statistics.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, func, distinct, and_, or_, desc, asc, case
from sqlalchemy.ext.asyncio import AsyncSession

from .database_manager import GeneralizedDatabaseManager
from .models import User, Vote, VoteOption, Statistics


class StatisticsService:
    """Service for calculating and aggregating various statistics."""

    def __init__(self, db_manager: GeneralizedDatabaseManager):
        self.db_manager = db_manager

    async def get_user_statistics(self, user: User) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a specific user.

        Args:
            user: The user to get statistics for

        Returns:
            Dictionary containing user statistics
        """
        async with self.db_manager.get_session() as session:
            # Votes created by user
            votes_created_query = select(func.count(Vote.id)).where(
                Vote.creator_id == str(user.id)
            )
            votes_created_result = await session.execute(votes_created_query)
            votes_created = votes_created_result.scalar() or 0

            # Votes participated in
            votes_participated_query = (
                select(func.count(distinct(VoteOption.vote_id)))
                .join(UserVoteChoice, VoteOption.id == UserVoteChoice.vote_option_id)
                .where(
                    and_(
                        UserVoteChoice.user_id == str(user.id),
                        VoteOption.vote_id.notin_(
                            select(Vote.id).where(Vote.creator_id == str(user.id))
                        ),
                    )
                )
            )
            votes_participated_result = await session.execute(votes_participated_query)
            votes_participated = votes_participated_result.scalar() or 0

            # Total responses given
            total_responses_query = select(func.count(UserVoteChoice.id)).where(
                UserVoteChoice.user_id == str(user.id)
            )
            total_responses_result = await session.execute(total_responses_query)
            total_responses = total_responses_result.scalar() or 0

            # Average response rate
            avg_response_rate = 0.0
            if votes_participated > 0:
                avg_response_rate = (total_responses / votes_participated) * 100

            # Votes by status (for created votes)
            votes_by_status_query = (
                select(Vote.status, func.count(Vote.id).label("count"))
                .where(Vote.creator_id == str(user.id))
                .group_by(Vote.status)
            )
            votes_by_status_result = await session.execute(votes_by_status_query)
            votes_by_status = {
                row.status.value: row.count for row in votes_by_status_result
            }

            # Response distribution (how user typically votes)
            response_distribution_query = (
                select(
                    UserVoteChoice.value, func.count(UserVoteChoice.id).label("count")
                )
                .where(UserVoteChoice.user_id == str(user.id))
                .group_by(UserVoteChoice.value)
            )
            response_distribution_result = await session.execute(
                response_distribution_query
            )
            response_distribution = {
                str(row.value): row.count for row in response_distribution_result
            }

            return {
                "user_id": str(user.id),
                "votes_created": votes_created,
                "votes_participated": votes_participated,
                "total_responses": total_responses,
                "avg_response_rate": round(avg_response_rate, 2),
                "votes_by_status": votes_by_status,
                "response_distribution": response_distribution,
                "calculated_at": datetime.utcnow().isoformat(),
            }

    async def get_system_statistics(self) -> Dict[str, Any]:
        """
        Get system-wide statistics for admin users.

        Returns:
            Dictionary containing system statistics
        """
        async with self.db_manager.get_session() as session:
            # Total users
            total_users_query = select(func.count(User.id))
            total_users_result = await session.execute(total_users_query)
            total_users = total_users_result.scalar() or 0

            # Active users (logged in within last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            active_users_query = select(func.count(distinct(User.id))).where(
                or_(
                    User.last_login >= thirty_days_ago,
                    User.created_at >= thirty_days_ago,
                )
            )
            active_users_result = await session.execute(active_users_query)
            active_users = active_users_result.scalar() or 0

            # Total votes created
            total_votes_query = select(func.count(Vote.id))
            total_votes_result = await session.execute(total_votes_query)
            total_votes = total_votes_result.scalar() or 0

            # Total votes by status
            votes_by_status_query = select(
                Vote.status, func.count(Vote.id).label("count")
            ).group_by(Vote.status)
            votes_by_status_result = await session.execute(votes_by_status_query)
            votes_by_status = {
                row.status.value: row.count for row in votes_by_status_result
            }

            # Total responses across all votes
            total_responses_query = select(func.count(UserVoteChoice.id))
            total_responses_result = await session.execute(total_responses_query)
            total_responses = total_responses_result.scalar() or 0

            # Average responses per vote
            avg_responses_per_vote = 0.0
            if total_votes > 0:
                avg_responses_per_vote = total_responses / total_votes

            # Most active users (top 10 by votes created)
            most_active_users_query = (
                select(User.username, func.count(Vote.id).label("votes_created"))
                .join(Vote, User.id == Vote.creator_id, isouter=True)
                .group_by(User.id, User.username)
                .order_by(desc(func.count(Vote.id)))
                .limit(10)
            )
            most_active_users_result = await session.execute(most_active_users_query)
            most_active_users = [
                {"username": row.username, "votes_created": row.votes_created}
                for row in most_active_users_result
            ]

            # Recent activity (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_votes_query = select(func.count(Vote.id)).where(
                Vote.created_at >= seven_days_ago
            )
            recent_votes_result = await session.execute(recent_votes_query)
            recent_votes = recent_votes_result.scalar() or 0

            recent_responses_query = select(func.count(UserVoteChoice.id)).where(
                UserVoteChoice.created_at >= seven_days_ago
            )
            recent_responses_result = await session.execute(recent_responses_query)
            recent_responses = recent_responses_result.scalar() or 0

            return {
                "total_users": total_users,
                "active_users": active_users,
                "user_activity_rate": round(
                    (active_users / total_users * 100) if total_users > 0 else 0, 2
                ),
                "total_votes": total_votes,
                "votes_by_status": votes_by_status,
                "total_responses": total_responses,
                "avg_responses_per_vote": round(avg_responses_per_vote, 2),
                "most_active_users": most_active_users,
                "recent_activity": {
                    "votes_created_7d": recent_votes,
                    "responses_given_7d": recent_responses,
                },
                "calculated_at": datetime.utcnow().isoformat(),
            }

    async def get_vote_statistics(self, vote: Vote) -> Dict[str, Any]:
        """
        Get statistics for a specific vote.

        Args:
            vote: The vote to get statistics for

        Returns:
            Dictionary containing vote statistics
        """
        async with self.db_manager.get_session() as session:
            # Total participants
            total_participants_query = (
                select(func.count(distinct(UserVoteChoice.user_id)))
                .join(VoteOption, UserVoteChoice.vote_option_id == VoteOption.id)
                .where(VoteOption.vote_id == vote.id)
            )
            total_participants_result = await session.execute(total_participants_query)
            total_participants = total_participants_result.scalar() or 0

            # Total responses
            total_responses_query = (
                select(func.count(UserVoteChoice.id))
                .join(VoteOption, UserVoteChoice.vote_option_id == VoteOption.id)
                .where(VoteOption.vote_id == vote.id)
            )
            total_responses_result = await session.execute(total_responses_query)
            total_responses = total_responses_result.scalar() or 0

            # Response distribution by value
            response_distribution_query = (
                select(
                    UserVoteChoice.value, func.count(UserVoteChoice.id).label("count")
                )
                .join(VoteOption, UserVoteChoice.vote_option_id == VoteOption.id)
                .where(VoteOption.vote_id == vote.id)
                .group_by(UserVoteChoice.value)
                .order_by(UserVoteChoice.value)
            )
            response_distribution_result = await session.execute(
                response_distribution_query
            )
            response_distribution = {
                str(row.value): row.count for row in response_distribution_result
            }

            # Participation by option
            option_participation_query = (
                select(
                    VoteOption.id,
                    VoteOption.content,
                    func.count(UserVoteChoice.id).label("response_count"),
                    func.avg(UserVoteChoice.value).label("avg_value"),
                )
                .outerjoin(
                    UserVoteChoice, VoteOption.id == UserVoteChoice.vote_option_id
                )
                .where(VoteOption.vote_id == vote.id)
                .group_by(VoteOption.id, VoteOption.content)
                .order_by(VoteOption.order_index)
            )
            option_participation_result = await session.execute(
                option_participation_query
            )
            option_participation = []
            for row in option_participation_result:
                option_participation.append(
                    {
                        "option_id": str(row.id),
                        "content": row.content,
                        "response_count": row.response_count,
                        "avg_value": float(row.avg_value) if row.avg_value else 0.0,
                    }
                )

            # Completion rate (if we track when users start vs complete)
            completion_rate = 100.0 if total_participants > 0 else 0.0

            return {
                "vote_id": str(vote.id),
                "vote_title": vote.title,
                "total_participants": total_participants,
                "total_responses": total_responses,
                "completion_rate": completion_rate,
                "response_distribution": response_distribution,
                "option_participation": option_participation,
                "avg_responses_per_participant": round(
                    total_responses / total_participants
                    if total_participants > 0
                    else 0,
                    2,
                ),
                "calculated_at": datetime.utcnow().isoformat(),
            }

    async def get_trending_votes(
        self, limit: int = 10, days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get trending votes based on recent activity.

        Args:
            limit: Maximum number of votes to return
            days_back: Number of days to look back for activity

        Returns:
            List of trending votes with activity metrics
        """
        async with self.db_manager.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Get votes with recent activity
            trending_query = (
                select(
                    Vote.id,
                    Vote.title,
                    Vote.created_at,
                    Vote.status,
                    func.count(UserVoteChoice.id).label("recent_responses"),
                    func.count(distinct(UserVoteChoice.user_id)).label(
                        "recent_participants"
                    ),
                )
                .join(VoteOption, Vote.id == VoteOption.vote_id)
                .join(UserVoteChoice, VoteOption.id == UserVoteChoice.vote_option_id)
                .where(
                    and_(
                        UserVoteChoice.created_at >= cutoff_date,
                        Vote.status == VoteStatus.ACTIVE,
                    )
                )
                .group_by(Vote.id, Vote.title, Vote.created_at, Vote.status)
                .order_by(desc(func.count(UserVoteChoice.id)))
                .limit(limit)
            )

            trending_result = await session.execute(trending_query)
            trending_votes = []

            for row in trending_result:
                trending_votes.append(
                    {
                        "vote_id": str(row.id),
                        "title": row.title,
                        "created_at": row.created_at.isoformat(),
                        "status": row.status.value,
                        "recent_responses": row.recent_responses,
                        "recent_participants": row.recent_participants,
                        "trend_score": row.recent_responses * row.recent_participants,
                    }
                )

            return trending_votes

    async def get_user_engagement_trends(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get user engagement trends over time.

        Args:
            days_back: Number of days to analyze

        Returns:
            Dictionary containing engagement trend data
        """
        async with self.db_manager.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Daily vote creation trend
            daily_votes_query = (
                select(
                    func.date(Vote.created_at).label("date"),
                    func.count(Vote.id).label("votes_created"),
                )
                .where(Vote.created_at >= cutoff_date)
                .group_by(func.date(Vote.created_at))
                .order_by(func.date(Vote.created_at))
            )
            daily_votes_result = await session.execute(daily_votes_query)
            daily_votes = [
                {"date": row.date.isoformat(), "votes_created": row.votes_created}
                for row in daily_votes_result
            ]

            # Daily response trend
            daily_responses_query = (
                select(
                    func.date(UserVoteChoice.created_at).label("date"),
                    func.count(UserVoteChoice.id).label("responses"),
                    func.count(distinct(UserVoteChoice.user_id)).label("active_users"),
                )
                .where(UserVoteChoice.created_at >= cutoff_date)
                .group_by(func.date(UserVoteChoice.created_at))
                .order_by(func.date(UserVoteChoice.created_at))
            )
            daily_responses_result = await session.execute(daily_responses_query)
            daily_responses = [
                {
                    "date": row.date.isoformat(),
                    "responses": row.responses,
                    "active_users": row.active_users,
                }
                for row in daily_responses_result
            ]

            return {
                "period_days": days_back,
                "daily_votes": daily_votes,
                "daily_responses": daily_responses,
                "calculated_at": datetime.utcnow().isoformat(),
            }

    async def get_comparative_statistics(self, user: User) -> Dict[str, Any]:
        """
        Get comparative statistics showing how user compares to system averages.

        Args:
            user: The user to compare

        Returns:
            Dictionary containing comparative statistics
        """
        async with self.db_manager.get_session() as session:
            # User's statistics
            user_stats = await self.get_user_statistics(user)

            # System averages
            avg_votes_per_user_query = (
                select(func.avg(func.count(Vote.id)))
                .join(User, Vote.creator_id == User.id)
                .group_by(User.id)
            )
            avg_votes_per_user_result = await session.execute(avg_votes_per_user_query)
            avg_votes_per_user = avg_votes_per_user_result.scalar() or 0

            avg_participation_per_user_query = (
                select(func.avg(func.count(distinct(VoteOption.vote_id))))
                .join(UserVoteChoice, VoteOption.id == UserVoteChoice.vote_option_id)
                .join(User, UserVoteChoice.user_id == User.id)
                .group_by(User.id)
            )
            avg_participation_per_user_result = await session.execute(
                avg_participation_per_user_query
            )
            avg_participation_per_user = avg_participation_per_user_result.scalar() or 0

            # Calculate percentiles
            user_votes_percentile = await self._calculate_user_percentile(
                session, user, "votes_created"
            )
            user_participation_percentile = await self._calculate_user_percentile(
                session, user, "votes_participated"
            )

            return {
                "user_stats": user_stats,
                "system_averages": {
                    "avg_votes_per_user": round(float(avg_votes_per_user), 2),
                    "avg_participation_per_user": round(
                        float(avg_participation_per_user), 2
                    ),
                },
                "user_percentiles": {
                    "votes_created_percentile": user_votes_percentile,
                    "votes_participated_percentile": user_participation_percentile,
                },
                "comparisons": {
                    "votes_vs_average": round(
                        (user_stats["votes_created"] / avg_votes_per_user * 100)
                        if avg_votes_per_user > 0
                        else 0,
                        1,
                    ),
                    "participation_vs_average": round(
                        (
                            user_stats["votes_participated"]
                            / avg_participation_per_user
                            * 100
                        )
                        if avg_participation_per_user > 0
                        else 0,
                        1,
                    ),
                },
                "calculated_at": datetime.utcnow().isoformat(),
            }

    async def _calculate_user_percentile(
        self, session: AsyncSession, user: User, metric: str
    ) -> float:
        """
        Calculate what percentile a user falls into for a given metric.

        Args:
            session: Database session
            user: The user to calculate percentile for
            metric: The metric to calculate ('votes_created' or 'votes_participated')

        Returns:
            Percentile value (0-100)
        """
        if metric == "votes_created":
            # Get user's vote count
            user_count_query = select(func.count(Vote.id)).where(
                Vote.creator_id == str(user.id)
            )
            user_count_result = await session.execute(user_count_query)
            user_count = user_count_result.scalar() or 0

            # Get count of users with fewer votes
            lower_users_query = (
                select(func.count(distinct(User.id)))
                .outerjoin(Vote, User.id == Vote.creator_id)
                .group_by(User.id)
                .having(func.count(Vote.id) < user_count)
            )
            lower_users_result = await session.execute(lower_users_query)
            lower_users_count = len(lower_users_result.fetchall())

            # Get total user count
            total_users_query = select(func.count(User.id))
            total_users_result = await session.execute(total_users_query)
            total_users = total_users_result.scalar() or 1

            return (lower_users_count / total_users) * 100

        elif metric == "votes_participated":
            # Similar logic for participation metric
            user_participation_query = (
                select(func.count(distinct(VoteOption.vote_id)))
                .join(UserVoteChoice, VoteOption.id == UserVoteChoice.vote_option_id)
                .where(UserVoteChoice.user_id == str(user.id))
            )
            user_participation_result = await session.execute(user_participation_query)
            user_participation = user_participation_result.scalar() or 0

            # This would need similar logic to votes_created
            # Simplified for now
            return 50.0  # Placeholder

        return 0.0
