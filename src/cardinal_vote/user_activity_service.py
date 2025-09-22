"""
User Activity Service for Cardinal Vote.

This service handles tracking and managing user activities including
vote participation, statistics calculation, and activity history.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy import select, func, distinct, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from .database_manager import GeneralizedDatabaseManager
from .models import User, Vote, VoteOption, UserActivity


class UserActivityService:
    """Service for managing user activities and tracking engagement."""

    def __init__(self, db_manager: GeneralizedDatabaseManager):
        self.db_manager = db_manager

    async def track_user_login(self, user: User, session_info: Dict[str, Any]) -> None:
        """
        Track user login activity.

        Args:
            user: The user who logged in
            session_info: Session information (IP, user agent, etc.)
        """
        async with self.db_manager.get_session() as session:
            # Update user's last login time
            user.last_login = datetime.utcnow()

            # Create session record
            user_session = UserSession(
                user_id=str(user.id),
                session_token=session_info.get("session_token", ""),
                ip_address=session_info.get("ip_address", ""),
                user_agent=session_info.get("user_agent", ""),
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),  # 30-day session
                is_active=True,
            )

            session.add(user_session)
            await session.commit()

    async def track_vote_creation(self, user: User, vote: Vote) -> None:
        """
        Track when a user creates a vote.

        Args:
            user: The user who created the vote
            vote: The vote that was created
        """
        # This is automatically tracked by the Vote model's creator_id field
        # Additional tracking logic can be added here if needed
        pass

    async def track_vote_participation(
        self, user: User, vote: Vote, choices: List[Dict[str, Any]]
    ) -> None:
        """
        Track when a user participates in a vote.

        Args:
            user: The user who participated
            vote: The vote they participated in
            choices: The choices they made
        """
        async with self.db_manager.get_session() as session:
            # Record participation timestamp
            # This would typically be stored in the UserVoteChoice records
            for choice in choices:
                user_choice = UserVoteChoice(
                    user_id=str(user.id),
                    vote_option_id=choice["vote_option_id"],
                    value=choice["value"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(user_choice)

            await session.commit()

    async def get_user_activity_summary(
        self, user: User, days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get a summary of user activity over the specified time period.

        Args:
            user: The user to get activity for
            days_back: Number of days to look back

        Returns:
            Dictionary containing activity summary
        """
        async with self.db_manager.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Votes created in the period
            votes_created_query = select(func.count(Vote.id)).where(
                and_(Vote.creator_id == str(user.id), Vote.created_at >= cutoff_date)
            )
            votes_created_result = await session.execute(votes_created_query)
            votes_created = votes_created_result.scalar() or 0

            # Votes participated in during the period
            votes_participated_query = (
                select(func.count(distinct(UserVoteChoice.vote_option_id)))
                .join(VoteOption, UserVoteChoice.vote_option_id == VoteOption.id)
                .join(Vote, VoteOption.vote_id == Vote.id)
                .where(
                    and_(
                        UserVoteChoice.user_id == str(user.id),
                        UserVoteChoice.created_at >= cutoff_date,
                    )
                )
            )
            votes_participated_result = await session.execute(votes_participated_query)
            votes_participated = votes_participated_result.scalar() or 0

            # Login sessions in the period
            login_sessions_query = select(func.count(UserSession.id)).where(
                and_(
                    UserSession.user_id == str(user.id),
                    UserSession.created_at >= cutoff_date,
                )
            )
            login_sessions_result = await session.execute(login_sessions_query)
            login_sessions = login_sessions_result.scalar() or 0

            return {
                "period_days": days_back,
                "votes_created": votes_created,
                "votes_participated": votes_participated,
                "login_sessions": login_sessions,
                "last_activity": user.last_login.isoformat()
                if user.last_login
                else None,
                "summary_generated_at": datetime.utcnow().isoformat(),
            }

    async def get_user_vote_history(
        self, user: User, limit: int = 50, offset: int = 0, include_draft: bool = False
    ) -> Dict[str, Any]:
        """
        Get user's vote creation and participation history.

        Args:
            user: The user to get history for
            limit: Maximum number of records to return
            offset: Number of records to skip
            include_draft: Whether to include draft votes

        Returns:
            Dictionary containing vote history with pagination info
        """
        async with self.db_manager.get_session() as session:
            # Get votes created by user
            created_votes_query = (
                select(Vote)
                .where(Vote.creator_id == str(user.id))
                .order_by(desc(Vote.created_at))
            )

            if not include_draft:
                created_votes_query = created_votes_query.where(
                    Vote.status != VoteStatus.DRAFT
                )

            created_votes_result = await session.execute(
                created_votes_query.offset(offset).limit(limit)
            )
            created_votes = created_votes_result.scalars().all()

            # Get votes user participated in
            participated_query = (
                select(Vote)
                .join(VoteOption, Vote.id == VoteOption.vote_id)
                .join(UserVoteChoice, VoteOption.id == UserVoteChoice.vote_option_id)
                .where(
                    and_(
                        UserVoteChoice.user_id == str(user.id),
                        Vote.creator_id != str(user.id),  # Exclude own votes
                    )
                )
                .order_by(desc(UserVoteChoice.created_at))
                .distinct()
            )

            participated_result = await session.execute(
                participated_query.offset(offset).limit(limit)
            )
            participated_votes = participated_result.scalars().all()

            # Format created votes
            created_votes_data = []
            for vote in created_votes:
                created_votes_data.append(
                    {
                        "id": str(vote.id),
                        "title": vote.title,
                        "status": vote.status.value,
                        "created_at": vote.created_at.isoformat(),
                        "type": "created",
                    }
                )

            # Format participated votes
            participated_votes_data = []
            for vote in participated_votes:
                participated_votes_data.append(
                    {
                        "id": str(vote.id),
                        "title": vote.title,
                        "status": vote.status.value,
                        "created_at": vote.created_at.isoformat(),
                        "type": "participated",
                    }
                )

            # Combine and sort by date
            all_votes = created_votes_data + participated_votes_data
            all_votes.sort(key=lambda x: x["created_at"], reverse=True)

            # Apply limit to combined results
            paginated_votes = all_votes[offset : offset + limit]

            return {
                "votes": paginated_votes,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": len(all_votes),
                    "has_more": (offset + limit) < len(all_votes),
                },
            }

    async def get_user_engagement_metrics(self, user: User) -> Dict[str, Any]:
        """
        Calculate user engagement metrics.

        Args:
            user: The user to calculate metrics for

        Returns:
            Dictionary containing engagement metrics
        """
        async with self.db_manager.get_session() as session:
            # Total votes created
            votes_created_query = select(func.count(Vote.id)).where(
                Vote.creator_id == str(user.id)
            )
            votes_created_result = await session.execute(votes_created_query)
            total_votes_created = votes_created_result.scalar() or 0

            # Total votes participated in
            votes_participated_query = (
                select(func.count(distinct(VoteOption.vote_id)))
                .join(UserVoteChoice, VoteOption.id == UserVoteChoice.vote_option_id)
                .where(UserVoteChoice.user_id == str(user.id))
            )
            votes_participated_result = await session.execute(votes_participated_query)
            total_votes_participated = votes_participated_result.scalar() or 0

            # Total responses given
            total_responses_query = select(func.count(UserVoteChoice.id)).where(
                UserVoteChoice.user_id == str(user.id)
            )
            total_responses_result = await session.execute(total_responses_query)
            total_responses = total_responses_result.scalar() or 0

            # Average response rate (responses per vote participated)
            avg_response_rate = 0.0
            if total_votes_participated > 0:
                avg_response_rate = (total_responses / total_votes_participated) * 100

            # Days since joining
            days_since_joining = 0
            if user.created_at:
                days_since_joining = (datetime.utcnow() - user.created_at).days

            # Activity frequency (votes per month)
            votes_per_month = 0.0
            if days_since_joining > 0:
                votes_per_month = (total_votes_created * 30) / days_since_joining

            return {
                "total_votes_created": total_votes_created,
                "total_votes_participated": total_votes_participated,
                "total_responses": total_responses,
                "avg_response_rate": round(avg_response_rate, 2),
                "days_since_joining": days_since_joining,
                "votes_per_month": round(votes_per_month, 2),
                "engagement_level": self._calculate_engagement_level(
                    total_votes_created, total_votes_participated, days_since_joining
                ),
                "metrics_calculated_at": datetime.utcnow().isoformat(),
            }

    async def get_recent_activities(
        self, user: User, limit: int = 10, activity_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user's recent activities (votes created, participated, etc.).

        Args:
            user: The user to get activities for
            limit: Maximum number of activities to return
            activity_types: List of activity types to include

        Returns:
            List of recent activities
        """
        activities = []

        async with self.db_manager.get_session() as session:
            # Recent votes created
            if not activity_types or "vote_created" in activity_types:
                created_votes_query = (
                    select(Vote)
                    .where(Vote.creator_id == str(user.id))
                    .order_by(desc(Vote.created_at))
                    .limit(limit)
                )
                created_votes_result = await session.execute(created_votes_query)
                created_votes = created_votes_result.scalars().all()

                for vote in created_votes:
                    activities.append(
                        {
                            "type": "vote_created",
                            "timestamp": vote.created_at.isoformat(),
                            "data": {
                                "vote_id": str(vote.id),
                                "vote_title": vote.title,
                                "vote_status": vote.status.value,
                            },
                        }
                    )

            # Recent vote participations
            if not activity_types or "vote_participated" in activity_types:
                participation_query = (
                    select(UserVoteChoice, Vote)
                    .join(VoteOption, UserVoteChoice.vote_option_id == VoteOption.id)
                    .join(Vote, VoteOption.vote_id == Vote.id)
                    .where(UserVoteChoice.user_id == str(user.id))
                    .order_by(desc(UserVoteChoice.created_at))
                    .limit(limit)
                )
                participation_result = await session.execute(participation_query)
                participations = participation_result.all()

                for choice, vote in participations:
                    activities.append(
                        {
                            "type": "vote_participated",
                            "timestamp": choice.created_at.isoformat(),
                            "data": {
                                "vote_id": str(vote.id),
                                "vote_title": vote.title,
                                "response_value": choice.value,
                            },
                        }
                    )

            # Recent login sessions
            if not activity_types or "login" in activity_types:
                login_query = (
                    select(UserSession)
                    .where(UserSession.user_id == str(user.id))
                    .order_by(desc(UserSession.created_at))
                    .limit(limit)
                )
                login_result = await session.execute(login_query)
                logins = login_result.scalars().all()

                for login in logins:
                    activities.append(
                        {
                            "type": "login",
                            "timestamp": login.created_at.isoformat(),
                            "data": {
                                "ip_address": login.ip_address,
                                "session_duration": self._calculate_session_duration(
                                    login
                                ),
                            },
                        }
                    )

        # Sort all activities by timestamp (most recent first)
        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        # Return only the requested number of activities
        return activities[:limit]

    def _calculate_engagement_level(
        self, votes_created: int, votes_participated: int, days_since_joining: int
    ) -> str:
        """
        Calculate user engagement level based on activity metrics.

        Args:
            votes_created: Number of votes user has created
            votes_participated: Number of votes user has participated in
            days_since_joining: Number of days since user joined

        Returns:
            Engagement level string
        """
        if days_since_joining == 0:
            return "new"

        total_activity = votes_created + votes_participated
        activity_per_week = (total_activity * 7) / days_since_joining

        if activity_per_week >= 5:
            return "very_high"
        elif activity_per_week >= 2:
            return "high"
        elif activity_per_week >= 0.5:
            return "medium"
        elif activity_per_week > 0:
            return "low"
        else:
            return "inactive"

    def _calculate_session_duration(self, session: UserSession) -> Optional[str]:
        """
        Calculate session duration if session has ended.

        Args:
            session: The user session

        Returns:
            Session duration as string or None if still active
        """
        if session.is_active:
            return None

        # In a real implementation, we'd track session end time
        # For now, return estimated duration
        return "estimated_30min"

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired user sessions.

        Returns:
            Number of sessions cleaned up
        """
        async with self.db_manager.get_session() as session:
            current_time = datetime.utcnow()

            # Mark expired sessions as inactive
            expired_sessions_query = select(UserSession).where(
                and_(
                    UserSession.expires_at < current_time, UserSession.is_active == True
                )
            )
            expired_sessions_result = await session.execute(expired_sessions_query)
            expired_sessions = expired_sessions_result.scalars().all()

            cleanup_count = 0
            for expired_session in expired_sessions:
                expired_session.is_active = False
                cleanup_count += 1

            await session.commit()
            return cleanup_count
