"""Super admin management functions for the generalized voting platform."""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, Vote, VoterResponse

logger = logging.getLogger(__name__)


class SuperAdminManager:
    """Manages super admin operations for user management and system statistics."""

    def __init__(self) -> None:
        """Initialize super admin manager."""
        pass

    async def get_comprehensive_system_stats(
        self, session: AsyncSession
    ) -> dict[str, Any]:
        """Get comprehensive system statistics for super admin dashboard."""
        try:
            stats: dict[str, Any] = {}

            # Calculate all statistics with efficient queries
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            today_start = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            # Single query for all user statistics using conditional aggregation
            user_stats_result = await session.execute(
                select(
                    func.count(User.id).label("total_users"),
                    func.count(func.case((User.is_verified.is_(True), 1))).label(
                        "verified_users"
                    ),
                    func.count(func.case((User.is_verified.is_(False), 1))).label(
                        "unverified_users"
                    ),
                    func.count(func.case((User.is_super_admin.is_(True), 1))).label(
                        "super_admins"
                    ),
                    func.count(func.case((User.created_at >= seven_days_ago, 1))).label(
                        "recent_users"
                    ),
                    func.count(func.case((User.created_at >= today_start, 1))).label(
                        "users_created_today"
                    ),
                )
            )
            user_stats = user_stats_result.fetchone()
            if user_stats:
                stats.update(
                    {
                        "total_users": user_stats.total_users or 0,
                        "verified_users": user_stats.verified_users or 0,
                        "unverified_users": user_stats.unverified_users or 0,
                        "super_admins": user_stats.super_admins or 0,
                        "recent_users": user_stats.recent_users or 0,
                        "users_created_today": user_stats.users_created_today or 0,
                    }
                )
            else:
                stats.update(
                    {
                        "total_users": 0,
                        "verified_users": 0,
                        "unverified_users": 0,
                        "super_admins": 0,
                        "recent_users": 0,
                        "users_created_today": 0,
                    }
                )

            # Single query for all vote statistics using conditional aggregation
            vote_stats_result = await session.execute(
                select(
                    func.count(Vote.id).label("total_votes"),
                    func.count(func.case((Vote.status == "draft", 1))).label(
                        "draft_votes"
                    ),
                    func.count(func.case((Vote.status == "active", 1))).label(
                        "active_votes"
                    ),
                    func.count(func.case((Vote.status == "closed", 1))).label(
                        "closed_votes"
                    ),
                    func.count(func.case((Vote.created_at >= seven_days_ago, 1))).label(
                        "recent_votes"
                    ),
                    func.count(func.case((Vote.created_at >= today_start, 1))).label(
                        "votes_created_today"
                    ),
                )
            )
            vote_stats = vote_stats_result.fetchone()
            if vote_stats:
                stats.update(
                    {
                        "total_votes": vote_stats.total_votes or 0,
                        "draft_votes": vote_stats.draft_votes or 0,
                        "active_votes": vote_stats.active_votes or 0,
                        "closed_votes": vote_stats.closed_votes or 0,
                        "recent_votes": vote_stats.recent_votes or 0,
                        "votes_created_today": vote_stats.votes_created_today or 0,
                    }
                )
            else:
                stats.update(
                    {
                        "total_votes": 0,
                        "draft_votes": 0,
                        "active_votes": 0,
                        "closed_votes": 0,
                        "recent_votes": 0,
                        "votes_created_today": 0,
                    }
                )

            # Single query for all response statistics using conditional aggregation
            response_stats_result = await session.execute(
                select(
                    func.count(VoterResponse.id).label("total_responses"),
                    func.count(
                        func.case((VoterResponse.submitted_at >= seven_days_ago, 1))
                    ).label("recent_responses"),
                    func.count(
                        func.case((VoterResponse.submitted_at >= today_start, 1))
                    ).label("responses_today"),
                )
            )
            response_stats = response_stats_result.fetchone()
            if response_stats:
                stats.update(
                    {
                        "total_responses": response_stats.total_responses or 0,
                        "recent_responses": response_stats.recent_responses or 0,
                        "responses_today": response_stats.responses_today or 0,
                    }
                )
            else:
                stats.update(
                    {
                        "total_responses": 0,
                        "recent_responses": 0,
                        "responses_today": 0,
                    }
                )

            # Platform health metrics
            platform_health = await self._calculate_platform_health(session, stats)
            stats["platform_health"] = platform_health

            # Add timestamp
            stats["timestamp"] = datetime.utcnow().isoformat()

            return stats

        except SQLAlchemyError as e:
            logger.error(f"Database error getting system stats: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting system stats: {e}")
            raise

    async def _calculate_platform_health(
        self, session: AsyncSession, stats: dict
    ) -> dict[str, Any]:
        """Calculate platform health metrics."""
        try:
            health: dict[str, Any] = {
                "status": "healthy",
                "score": 100,
                "warnings": [],
            }

            # Check user engagement
            if stats["total_users"] > 0:
                verification_rate = stats["verified_users"] / stats["total_users"]
                if verification_rate < 0.5:
                    health["warnings"].append("Low user verification rate")
                    health["score"] -= 10

            # Check vote activity
            if stats["total_votes"] > 0:
                active_rate = stats["active_votes"] / stats["total_votes"]
                if active_rate < 0.3:
                    health["warnings"].append("Many votes are not active")
                    health["score"] -= 5

            # Check recent activity
            if stats["recent_users"] == 0 and stats["total_users"] > 10:
                health["warnings"].append("No new users in the past 7 days")
                health["score"] -= 15

            if stats["recent_responses"] == 0 and stats["total_votes"] > 0:
                health["warnings"].append("No voting activity in the past 7 days")
                health["score"] -= 20

            # Determine overall status
            if health["score"] >= 80:
                health["status"] = "healthy"
            elif health["score"] >= 60:
                health["status"] = "warning"
            else:
                health["status"] = "critical"

            return health

        except Exception as e:
            logger.error(f"Error calculating platform health: {e}")
            return {
                "status": "unknown",
                "score": 0,
                "warnings": ["Unable to calculate health metrics"],
            }

    async def get_recent_user_activity(
        self, session: AsyncSession, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get recent user activity for monitoring."""
        try:
            # Get recently created users with their vote counts in a single query
            # Use LEFT JOIN to include users with zero votes
            result = await session.execute(
                select(
                    User.id,
                    User.email,
                    User.first_name,
                    User.last_name,
                    User.is_verified,
                    User.is_super_admin,
                    User.created_at,
                    User.last_login,
                    func.count(Vote.id).label("vote_count"),
                )
                .select_from(User)
                .outerjoin(Vote, User.id == Vote.creator_id)
                .group_by(
                    User.id,
                    User.email,
                    User.first_name,
                    User.last_name,
                    User.is_verified,
                    User.is_super_admin,
                    User.created_at,
                    User.last_login,
                )
                .order_by(desc(User.created_at))
                .limit(limit)
            )
            recent_users = result.fetchall()

            activity = []
            for user_row in recent_users:
                activity.append(
                    {
                        "type": "user_registration",
                        "user_id": str(user_row.id),
                        "user_email": user_row.email,
                        "user_name": f"{user_row.first_name} {user_row.last_name}",
                        "is_verified": user_row.is_verified,
                        "is_super_admin": user_row.is_super_admin,
                        "vote_count": user_row.vote_count or 0,
                        "created_at": user_row.created_at.isoformat()
                        if user_row.created_at
                        else None,
                        "last_login": user_row.last_login.isoformat()
                        if user_row.last_login
                        else None,
                    }
                )

            return activity

        except SQLAlchemyError as e:
            logger.error(f"Database error getting recent user activity: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting recent user activity: {e}")
            raise

    async def get_user_management_summary(
        self, session: AsyncSession
    ) -> dict[str, Any]:
        """Get summary information for user management dashboard."""
        try:
            # Use COUNT queries instead of loading all users into memory
            verified_count_result = await session.execute(
                select(func.count(User.id)).where(User.is_verified.is_(True))
            )
            verified_users_count = verified_count_result.scalar() or 0

            unverified_count_result = await session.execute(
                select(func.count(User.id)).where(User.is_verified.is_(False))
            )
            unverified_users_count = unverified_count_result.scalar() or 0

            super_admins_count_result = await session.execute(
                select(func.count(User.id)).where(User.is_super_admin.is_(True))
            )
            super_admins_count = super_admins_count_result.scalar() or 0

            # Get most active users (by vote count) using SQLAlchemy ORM
            most_active_result = await session.execute(
                select(
                    User.id,
                    User.email,
                    User.first_name,
                    User.last_name,
                    func.count(Vote.id).label("vote_count"),
                )
                .select_from(User)
                .outerjoin(Vote, User.id == Vote.creator_id)
                .group_by(User.id, User.email, User.first_name, User.last_name)
                .order_by(desc(func.count(Vote.id)), desc(User.created_at))
                .limit(10)
            )
            most_active_users = most_active_result.fetchall()

            # Get recent registrations (limit to 10 to avoid memory issues)
            recent_registrations_result = await session.execute(
                select(User).order_by(desc(User.created_at)).limit(10)
            )
            recent_registrations = recent_registrations_result.scalars().all()

            # Get pending verifications (unverified users, limit to 10)
            pending_verifications_result = await session.execute(
                select(User)
                .where(User.is_verified.is_(False))
                .order_by(desc(User.created_at))
                .limit(10)
            )
            pending_verifications = pending_verifications_result.scalars().all()

            summary = {
                "verified_users_count": verified_users_count,
                "unverified_users_count": unverified_users_count,
                "super_admins_count": super_admins_count,
                "most_active_users": [
                    {
                        "user_id": str(row.id),
                        "email": row.email,
                        "first_name": row.first_name,
                        "last_name": row.last_name,
                        "vote_count": row.vote_count,
                    }
                    for row in most_active_users[:5]  # Top 5 only
                ],
                "recent_registrations": [
                    {
                        "user_id": str(user.id),
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_verified": user.is_verified,
                        "created_at": user.created_at.isoformat()
                        if user.created_at
                        else None,
                    }
                    for user in recent_registrations
                ],
                "pending_verifications": [
                    {
                        "user_id": str(user.id),
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "created_at": user.created_at.isoformat()
                        if user.created_at
                        else None,
                    }
                    for user in pending_verifications
                ],
            }

            return summary

        except SQLAlchemyError as e:
            logger.error(f"Database error getting user management summary: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting user management summary: {e}")
            raise

    async def bulk_update_users(
        self, session: AsyncSession, user_ids: list[UUID], operation: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Perform bulk operations on multiple users."""
        try:
            if not user_ids:
                return {"success": False, "message": "No users specified"}

            if operation == "verify_users":
                # Bulk verify users using SQLAlchemy ORM
                result = await session.execute(
                    update(User).where(User.id.in_(user_ids)).values(is_verified=True)
                )
                await session.commit()

                affected_rows = result.rowcount or 0
                logger.info(f"Bulk verified {affected_rows} users")

                return {
                    "success": True,
                    "message": f"Successfully verified {affected_rows} users",
                    "affected_count": affected_rows,
                }

            elif operation == "unverify_users":
                # Bulk unverify users using SQLAlchemy ORM
                result = await session.execute(
                    update(User).where(User.id.in_(user_ids)).values(is_verified=False)
                )
                await session.commit()

                affected_rows = result.rowcount or 0
                logger.info(f"Bulk unverified {affected_rows} users")

                return {
                    "success": True,
                    "message": f"Successfully unverified {affected_rows} users",
                    "affected_count": affected_rows,
                }

            else:
                return {
                    "success": False,
                    "message": f"Unknown bulk operation: {operation}",
                }

        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error in bulk user update: {e}")
            return {
                "success": False,
                "message": "Database error during bulk operation",
                "error": str(e),
            }
        except Exception as e:
            await session.rollback()
            logger.error(f"Unexpected error in bulk user update: {e}")
            return {
                "success": False,
                "message": "Unexpected error during bulk operation",
                "error": str(e),
            }

    async def get_platform_audit_log(
        self, session: AsyncSession, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get platform audit log for super admin monitoring."""
        try:
            # This is a simplified audit log
            # In a real implementation, you'd have a dedicated audit_log table
            audit_events = []

            # Recent user registrations
            recent_users_result = await session.execute(
                select(User).order_by(desc(User.created_at)).limit(limit // 2)
            )
            recent_users = recent_users_result.scalars().all()

            for user in recent_users:
                audit_events.append(
                    {
                        "event_type": "user_registration",
                        "timestamp": user.created_at.isoformat()
                        if user.created_at
                        else None,
                        "user_email": user.email,
                        "details": f"New user registered: {user.first_name} {user.last_name}",
                        "is_verified": user.is_verified,
                    }
                )

            # Recent vote creations
            recent_votes_result = await session.execute(
                select(Vote, User)
                .join(User, Vote.creator_id == User.id)
                .order_by(desc(Vote.created_at))
                .limit(limit // 2)
            )
            recent_votes = recent_votes_result.all()

            for vote, user in recent_votes:
                audit_events.append(
                    {
                        "event_type": "vote_creation",
                        "timestamp": vote.created_at.isoformat()
                        if vote.created_at
                        else None,
                        "user_email": user.email,
                        "details": f"Vote created: {vote.title}",
                        "vote_slug": vote.slug,
                        "vote_status": vote.status,
                    }
                )

            # Sort all events by timestamp (most recent first)
            audit_events.sort(key=lambda x: x["timestamp"] or "", reverse=True)

            return audit_events[:limit]

        except SQLAlchemyError as e:
            logger.error(f"Database error getting audit log: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting audit log: {e}")
            raise
