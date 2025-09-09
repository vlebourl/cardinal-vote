"""Vote moderation manager for content oversight and policy enforcement."""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from .models import (
    Vote,
    VoteModerationAction,
    VoteModerationFlag,
    VoterResponse,
)

logger = logging.getLogger(__name__)


class VoteModerationManager:
    """Manager class for vote moderation and content oversight operations."""

    async def create_vote_flag(
        self,
        session: AsyncSession,
        vote_id: Any,
        flag_type: str,
        reason: str,
        flagger_id: Any | None = None,
    ) -> dict[str, Any]:
        """Create a new moderation flag for a vote."""
        try:
            # Check if vote exists
            vote_result = await session.execute(select(Vote).where(Vote.id == vote_id))
            vote = vote_result.scalar_one_or_none()

            if not vote:
                return {"success": False, "message": "Vote not found"}

            # Check for duplicate flags from the same user
            if flagger_id:
                existing_flag_result = await session.execute(
                    select(VoteModerationFlag).where(
                        VoteModerationFlag.vote_id == vote_id,
                        VoteModerationFlag.flagger_id == flagger_id,
                        VoteModerationFlag.flag_type == flag_type,
                        VoteModerationFlag.status == "pending",
                    )
                )
                existing_flag = existing_flag_result.scalar_one_or_none()

                if existing_flag:
                    return {
                        "success": False,
                        "message": "You have already flagged this vote for the same reason",
                    }

            # Create new flag
            flag = VoteModerationFlag(
                vote_id=vote_id,
                flagger_id=flagger_id,
                flag_type=flag_type,
                reason=reason,
                status="pending",
            )

            session.add(flag)
            await session.commit()

            logger.info(
                f"Vote {vote_id} flagged for {flag_type} by user {flagger_id or 'anonymous'}"
            )

            return {
                "success": True,
                "message": "Vote flagged successfully",
                "flag_id": str(flag.id),
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating vote flag: {e}")
            return {"success": False, "message": "Failed to create flag"}

    async def review_vote_flag(
        self,
        session: AsyncSession,
        flag_id: Any,
        reviewer_id: Any,
        status: str,
        review_notes: str,
    ) -> dict[str, Any]:
        """Review and update the status of a vote flag."""
        try:
            # Get flag with related data
            flag_result = await session.execute(
                select(VoteModerationFlag)
                .options(joinedload(VoteModerationFlag.vote))
                .where(VoteModerationFlag.id == flag_id)
            )
            flag = flag_result.scalar_one_or_none()

            if not flag:
                return {"success": False, "message": "Flag not found"}

            if flag.status != "pending":
                return {"success": False, "message": "Flag has already been reviewed"}

            # Update flag
            flag.status = status
            flag.reviewed_by = reviewer_id
            flag.reviewed_at = datetime.utcnow()
            flag.review_notes = review_notes

            await session.commit()

            logger.info(
                f"Flag {flag_id} reviewed by {reviewer_id} with status: {status}"
            )

            return {
                "success": True,
                "message": f"Flag {status} successfully",
                "flag_id": str(flag.id),
                "vote_id": str(flag.vote_id),
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"Error reviewing vote flag: {e}")
            return {"success": False, "message": "Failed to review flag"}

    async def take_moderation_action(
        self,
        session: AsyncSession,
        vote_id: Any,
        moderator_id: Any,
        action_type: str,
        reason: str,
        additional_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Take a moderation action on a vote."""
        try:
            # Get vote
            vote_result = await session.execute(select(Vote).where(Vote.id == vote_id))
            vote = vote_result.scalar_one_or_none()

            if not vote:
                return {"success": False, "message": "Vote not found"}

            previous_status = vote.status
            new_status = previous_status

            # Apply action based on type
            if action_type == "close_vote":
                if vote.status not in ["active"]:
                    return {"success": False, "message": "Can only close active votes"}
                vote.status = "closed"
                new_status = "closed"

            elif action_type == "disable_vote":
                if vote.status in ["disabled", "hidden"]:
                    return {
                        "success": False,
                        "message": "Vote is already disabled or hidden",
                    }
                vote.status = "disabled"
                new_status = "disabled"

            elif action_type == "hide_vote":
                if vote.status == "hidden":
                    return {"success": False, "message": "Vote is already hidden"}
                vote.status = "hidden"
                new_status = "hidden"

            elif action_type == "restore_vote":
                if vote.status not in ["disabled", "hidden"]:
                    return {
                        "success": False,
                        "message": "Can only restore disabled or hidden votes",
                    }
                # Restore to previous functional state - default to draft if created as disabled
                vote.status = (
                    "draft" if previous_status in ["disabled", "hidden"] else "active"
                )
                new_status = vote.status

            elif action_type == "delete_vote":
                # For delete action, we'll mark as hidden and add metadata
                vote.status = "hidden"
                new_status = "hidden"
                additional_data = {**(additional_data or {}), "deleted": True}

            # Record the moderation action
            action = VoteModerationAction(
                vote_id=vote_id,
                moderator_id=moderator_id,
                action_type=action_type,
                reason=reason,
                previous_status=previous_status,
                new_status=new_status,
                additional_data=additional_data,
            )

            session.add(action)
            await session.commit()

            logger.info(
                f"Moderation action '{action_type}' taken on vote {vote_id} by moderator {moderator_id}"
            )

            return {
                "success": True,
                "message": f"Action '{action_type}' applied successfully",
                "action_id": str(action.id),
                "vote_id": str(vote_id),
                "previous_status": previous_status,
                "new_status": new_status,
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"Error taking moderation action: {e}")
            return {"success": False, "message": "Failed to take moderation action"}

    async def bulk_moderation_action(
        self,
        session: AsyncSession,
        vote_ids: list[Any],
        moderator_id: Any,
        action_type: str,
        reason: str,
    ) -> dict[str, Any]:
        """Take bulk moderation actions on multiple votes."""
        try:
            if len(vote_ids) > 50:
                return {
                    "success": False,
                    "message": "Cannot process more than 50 votes at once",
                }

            results = []
            success_count = 0
            error_count = 0

            for vote_id in vote_ids:
                result = await self.take_moderation_action(
                    session, vote_id, moderator_id, action_type, reason
                )
                results.append(
                    {
                        "vote_id": str(vote_id),
                        "success": result["success"],
                        "message": result["message"],
                    }
                )

                if result["success"]:
                    success_count += 1
                else:
                    error_count += 1

            logger.info(
                f"Bulk moderation action '{action_type}' completed: {success_count} successful, {error_count} failed"
            )

            return {
                "success": True,
                "message": f"Bulk action completed: {success_count} successful, {error_count} failed",
                "success_count": success_count,
                "error_count": error_count,
                "results": results,
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"Error in bulk moderation action: {e}")
            return {"success": False, "message": "Failed to complete bulk action"}

    async def get_pending_flags(
        self, session: AsyncSession, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get pending moderation flags."""
        try:
            result = await session.execute(
                select(VoteModerationFlag)
                .options(
                    joinedload(VoteModerationFlag.vote).joinedload(Vote.creator),
                    joinedload(VoteModerationFlag.flagger),
                )
                .where(VoteModerationFlag.status == "pending")
                .order_by(desc(VoteModerationFlag.created_at))
                .limit(limit)
                .offset(offset)
            )
            flags = result.scalars().all()

            flag_data = []
            for flag in flags:
                flag_data.append(
                    {
                        "id": str(flag.id),
                        "vote_id": str(flag.vote_id),
                        "vote_title": flag.vote.title,
                        "vote_slug": flag.vote.slug,
                        "vote_status": flag.vote.status,
                        "creator_email": flag.vote.creator.email,
                        "flag_type": flag.flag_type,
                        "reason": flag.reason,
                        "flagger_email": flag.flagger.email
                        if flag.flagger
                        else "Anonymous",
                        "created_at": flag.created_at.isoformat()
                        if flag.created_at
                        else "",
                    }
                )

            return flag_data

        except Exception as e:
            logger.error(f"Error getting pending flags: {e}")
            return []

    async def get_vote_moderation_summary(
        self, session: AsyncSession, vote_id: Any
    ) -> dict[str, Any] | None:
        """Get comprehensive moderation summary for a vote."""
        try:
            # Get vote with creator info
            vote_result = await session.execute(
                select(Vote).options(joinedload(Vote.creator)).where(Vote.id == vote_id)
            )
            vote = vote_result.scalar_one_or_none()

            if not vote:
                return None

            # Get flags with related data
            flags_result = await session.execute(
                select(VoteModerationFlag)
                .options(
                    joinedload(VoteModerationFlag.flagger),
                    joinedload(VoteModerationFlag.reviewer),
                )
                .where(VoteModerationFlag.vote_id == vote_id)
                .order_by(desc(VoteModerationFlag.created_at))
            )
            flags = flags_result.scalars().all()

            # Get moderation actions
            actions_result = await session.execute(
                select(VoteModerationAction)
                .options(joinedload(VoteModerationAction.moderator))
                .where(VoteModerationAction.vote_id == vote_id)
                .order_by(desc(VoteModerationAction.created_at))
                .limit(10)
            )
            actions = actions_result.scalars().all()

            # Count flags by status
            flag_counts = {"pending": 0, "approved": 0, "rejected": 0, "resolved": 0}
            for flag in flags:
                if flag.status:
                    flag_counts[flag.status] = flag_counts.get(flag.status, 0) + 1

            return {
                "vote_id": str(vote.id),
                "vote_title": vote.title,
                "vote_slug": vote.slug,
                "vote_status": vote.status,
                "creator_email": vote.creator.email,
                "total_flags": len(flags),
                "pending_flags": flag_counts["pending"],
                "approved_flags": flag_counts["approved"],
                "rejected_flags": flag_counts["rejected"],
                "resolved_flags": flag_counts["resolved"],
                "recent_actions": [
                    {
                        "id": str(action.id),
                        "action_type": action.action_type,
                        "reason": action.reason,
                        "previous_status": action.previous_status,
                        "new_status": action.new_status,
                        "moderator_email": action.moderator.email,
                        "created_at": action.created_at.isoformat()
                        if action.created_at
                        else "",
                        "additional_data": action.additional_data,
                    }
                    for action in actions
                ],
                "flags": [
                    {
                        "id": str(flag.id),
                        "flag_type": flag.flag_type,
                        "reason": flag.reason,
                        "status": flag.status,
                        "flagger_email": flag.flagger.email
                        if flag.flagger
                        else "Anonymous",
                        "reviewer_email": flag.reviewer.email
                        if flag.reviewer
                        else None,
                        "reviewed_at": flag.reviewed_at.isoformat()
                        if flag.reviewed_at
                        else None,
                        "review_notes": flag.review_notes,
                        "created_at": flag.created_at.isoformat()
                        if flag.created_at
                        else "",
                    }
                    for flag in flags
                ],
            }

        except Exception as e:
            logger.error(f"Error getting vote moderation summary: {e}")
            return None

    async def get_moderation_dashboard_stats(
        self, session: AsyncSession
    ) -> dict[str, Any]:
        """Get moderation dashboard statistics."""
        try:
            # Total pending flags
            pending_flags_result = await session.execute(
                select(func.count(VoteModerationFlag.id)).where(
                    VoteModerationFlag.status == "pending"
                )
            )
            pending_flags = pending_flags_result.scalar() or 0

            # Flags by type in the last 7 days
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_flags_result = await session.execute(
                select(
                    VoteModerationFlag.flag_type,
                    func.count(VoteModerationFlag.id).label("count"),
                )
                .where(VoteModerationFlag.created_at >= week_ago)
                .group_by(VoteModerationFlag.flag_type)
            )
            recent_flags_by_type = {
                row.flag_type: row.count for row in recent_flags_result
            }

            # Moderation actions in the last 7 days
            recent_actions_result = await session.execute(
                select(
                    VoteModerationAction.action_type,
                    func.count(VoteModerationAction.id).label("count"),
                )
                .where(VoteModerationAction.created_at >= week_ago)
                .group_by(VoteModerationAction.action_type)
            )
            recent_actions_by_type = {
                row.action_type: row.count for row in recent_actions_result
            }

            # Votes by moderation status
            votes_by_status_result = await session.execute(
                select(Vote.status, func.count(Vote.id).label("count"))
                .where(Vote.status.in_(["disabled", "hidden", "closed"]))
                .group_by(Vote.status)
            )
            moderated_votes_by_status = {
                row.status: row.count for row in votes_by_status_result
            }

            return {
                "pending_flags": pending_flags,
                "recent_flags_by_type": recent_flags_by_type,
                "recent_actions_by_type": recent_actions_by_type,
                "moderated_votes_by_status": moderated_votes_by_status,
                "total_moderated_votes": sum(moderated_votes_by_status.values())
                if moderated_votes_by_status
                else 0,
            }

        except Exception as e:
            logger.error(f"Error getting moderation dashboard stats: {e}")
            return {
                "pending_flags": 0,
                "recent_flags_by_type": {},
                "recent_actions_by_type": {},
                "moderated_votes_by_status": {},
                "total_moderated_votes": 0,
            }

    async def get_flagged_votes(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        flag_status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get votes that have been flagged, with optional status filter."""
        try:
            # Build query for votes with flags
            query = (
                select(Vote)
                .options(joinedload(Vote.creator), selectinload(Vote.options))
                .join(VoteModerationFlag)
                .distinct()
            )

            if flag_status:
                query = query.where(VoteModerationFlag.status == flag_status)

            query = query.order_by(desc(Vote.created_at)).limit(limit).offset(offset)

            result = await session.execute(query)
            votes = result.scalars().all()

            vote_data = []
            for vote in votes:
                # Get flag summary for this vote
                flags_result = await session.execute(
                    select(
                        VoteModerationFlag.status,
                        func.count(VoteModerationFlag.id).label("count"),
                    )
                    .where(VoteModerationFlag.vote_id == vote.id)
                    .group_by(VoteModerationFlag.status)
                )
                flag_counts: dict[str, int] = {}
                for row in flags_result:
                    status = row[0] if row[0] else "unknown"
                    count = int(row[1]) if row[1] else 0
                    flag_counts[status] = count

                # Get total responses
                responses_result = await session.execute(
                    select(func.count(VoterResponse.id)).where(
                        VoterResponse.vote_id == vote.id
                    )
                )
                total_responses = responses_result.scalar() or 0

                vote_data.append(
                    {
                        "id": str(vote.id),
                        "title": vote.title,
                        "slug": vote.slug,
                        "status": vote.status,
                        "creator_email": vote.creator.email,
                        "created_at": vote.created_at.isoformat()
                        if vote.created_at
                        else "",
                        "total_options": len(vote.options),
                        "total_responses": total_responses,
                        "flag_counts": flag_counts,
                        "total_flags": sum(flag_counts.values()) if flag_counts else 0,
                    }
                )

            return vote_data

        except Exception as e:
            logger.error(f"Error getting flagged votes: {e}")
            return []
