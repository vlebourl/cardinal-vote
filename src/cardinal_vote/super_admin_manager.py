"""Super admin management functions for the generalized voting platform."""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select, text
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

            # User statistics
            total_users_result = await session.execute(select(func.count(User.id)))
            stats["total_users"] = total_users_result.scalar() or 0

            verified_users_result = await session.execute(
                select(func.count(User.id)).where(User.is_verified.is_(True))
            )
            stats["verified_users"] = verified_users_result.scalar() or 0

            unverified_users_result = await session.execute(
                select(func.count(User.id)).where(User.is_verified.is_(False))
            )
            stats["unverified_users"] = unverified_users_result.scalar() or 0

            super_admins_result = await session.execute(
                select(func.count(User.id)).where(User.is_super_admin.is_(True))
            )
            stats["super_admins"] = super_admins_result.scalar() or 0

            # Vote statistics
            total_votes_result = await session.execute(select(func.count(Vote.id)))
            stats["total_votes"] = total_votes_result.scalar() or 0

            draft_votes_result = await session.execute(
                select(func.count(Vote.id)).where(Vote.status == "draft")
            )
            stats["draft_votes"] = draft_votes_result.scalar() or 0

            active_votes_result = await session.execute(
                select(func.count(Vote.id)).where(Vote.status == "active")
            )
            stats["active_votes"] = active_votes_result.scalar() or 0

            closed_votes_result = await session.execute(
                select(func.count(Vote.id)).where(Vote.status == "closed")
            )
            stats["closed_votes"] = closed_votes_result.scalar() or 0

            # Response statistics
            total_responses_result = await session.execute(
                select(func.count(VoterResponse.id))
            )
            stats["total_responses"] = total_responses_result.scalar() or 0

            # Recent activity statistics (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)

            recent_users_result = await session.execute(
                select(func.count(User.id)).where(User.created_at >= seven_days_ago)
            )
            stats["recent_users"] = recent_users_result.scalar() or 0

            recent_votes_result = await session.execute(
                select(func.count(Vote.id)).where(Vote.created_at >= seven_days_ago)
            )
            stats["recent_votes"] = recent_votes_result.scalar() or 0

            recent_responses_result = await session.execute(
                select(func.count(VoterResponse.id)).where(
                    VoterResponse.submitted_at >= seven_days_ago
                )
            )
            stats["recent_responses"] = recent_responses_result.scalar() or 0

            # Today's statistics
            today_start = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            users_today_result = await session.execute(
                select(func.count(User.id)).where(User.created_at >= today_start)
            )
            stats["users_created_today"] = users_today_result.scalar() or 0

            votes_today_result = await session.execute(
                select(func.count(Vote.id)).where(Vote.created_at >= today_start)
            )
            stats["votes_created_today"] = votes_today_result.scalar() or 0

            responses_today_result = await session.execute(
                select(func.count(VoterResponse.id)).where(
                    VoterResponse.submitted_at >= today_start
                )
            )
            stats["responses_today"] = responses_today_result.scalar() or 0

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
            # Get recently created users
            result = await session.execute(
                select(User).order_by(desc(User.created_at)).limit(limit)
            )
            recent_users = result.scalars().all()

            activity = []
            for user in recent_users:
                # Get user's vote count
                vote_count_result = await session.execute(
                    select(func.count(Vote.id)).where(Vote.creator_id == user.id)
                )
                vote_count = vote_count_result.scalar() or 0

                activity.append(
                    {
                        "type": "user_registration",
                        "user_id": str(user.id),
                        "user_email": user.email,
                        "user_name": f"{user.first_name} {user.last_name}",
                        "is_verified": user.is_verified,
                        "is_super_admin": user.is_super_admin,
                        "vote_count": vote_count,
                        "created_at": user.created_at.isoformat()
                        if user.created_at
                        else None,
                        "last_login": user.last_login.isoformat()
                        if user.last_login
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
            summary = {}

            # Get users by verification status
            verified_users_result = await session.execute(
                select(User)
                .where(User.is_verified.is_(True))
                .order_by(desc(User.created_at))
            )
            verified_users = verified_users_result.scalars().all()

            unverified_users_result = await session.execute(
                select(User)
                .where(User.is_verified.is_(False))
                .order_by(desc(User.created_at))
            )
            unverified_users = unverified_users_result.scalars().all()

            # Get super admins
            super_admin_result = await session.execute(
                select(User)
                .where(User.is_super_admin.is_(True))
                .order_by(desc(User.created_at))
            )
            super_admins = super_admin_result.scalars().all()

            # Get most active users (by vote count)
            most_active_result = await session.execute(
                text("""
                    SELECT u.*, COUNT(v.id) as vote_count
                    FROM users u
                    LEFT JOIN votes v ON u.id = v.creator_id
                    GROUP BY u.id
                    ORDER BY vote_count DESC, u.created_at DESC
                    LIMIT 10
                """)
            )
            most_active_users = most_active_result.fetchall()

            summary = {
                "verified_users_count": len(verified_users),
                "unverified_users_count": len(unverified_users),
                "super_admins_count": len(super_admins),
                "most_active_users": [
                    {
                        "user_id": str(row[0]),  # id
                        "email": row[1],  # email
                        "first_name": row[2],  # first_name
                        "last_name": row[3],  # last_name
                        "vote_count": row[-1],  # vote_count (last column)
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
                    for user in (list(verified_users) + list(unverified_users))[:10]
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
                    for user in unverified_users[:10]
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
                # Bulk verify users
                result = await session.execute(
                    text(
                        "UPDATE users SET is_verified = true WHERE id = ANY(:user_ids)"
                    ),
                    {"user_ids": [str(uid) for uid in user_ids]},
                )
                await session.commit()

                affected_rows = getattr(result, "rowcount", 0) or 0
                logger.info(f"Bulk verified {affected_rows} users")

                return {
                    "success": True,
                    "message": f"Successfully verified {affected_rows} users",
                    "affected_count": affected_rows,
                }

            elif operation == "unverify_users":
                # Bulk unverify users
                result = await session.execute(
                    text(
                        "UPDATE users SET is_verified = false WHERE id = ANY(:user_ids)"
                    ),
                    {"user_ids": [str(uid) for uid in user_ids]},
                )
                await session.commit()

                affected_rows = getattr(result, "rowcount", 0) or 0
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
